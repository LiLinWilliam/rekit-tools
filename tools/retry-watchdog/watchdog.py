#!/usr/bin/env python3
"""
Codex 自动重试守护 (watchdog)
=================================
不碰前端 UI，纯接口/数据面：

  1) 只读 ~/.codex/*.sqlite 判断目标会话的 turn 状态
     (logs_2.sqlite / thread_history_1.sqlite / state_5.sqlite / queue_1.sqlite)
  2) 检测到"失败后停摆"（服务端容量不足、断流、崩溃等），用官方交互桥
     codex queue --thread <id> --message <续跑指令>
     把消息排进该会话，桌面端 app-server 会在秒级内消费并重新起 turn。
     （不抢 thread 写锁，不需要前端操作，不重启 Codex）
  3) 失败则指数退避后再次排队，直到该 turn 正常完成 -> 退出并汇报。
     若桌面端已关闭、队列没人消费，则自动回退到 codex exec resume。

安全设计：
  * 桌面端仍在运行时（有 inProgress turn 或最近有日志活动）不抢跑
  * 单实例锁，防止多个守护进程同时操作同一会话
  * 只读打开 sqlite（WAL 模式），不会阻塞 Codex 自身写入
  * 每轮执行都落 logs/ 目录，可审计

用法示例：
  python watchdog.py --thread <thread-uuid> --once --dry-run
  python watchdog.py --thread <thread-id-prefix>-... --interval 15 --stall-seconds 120
  powershell -File start.ps1 -Thread <thread-id-prefix>-...
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------- 基础工具

def now_ts() -> float:
    return time.time()

def fmt_ts(ts) -> str:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%H:%M:%S")
    except Exception:
        return "-"

def log(msg: str) -> None:
    print("[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg), flush=True)

def setup_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass

def find_codex_exe() -> str:
    env = os.environ.get("CODEX_EXE")
    if env and Path(env).exists():
        return env
    w = shutil.which("codex.exe") or shutil.which("codex")
    if w:
        return w
    bases = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        bases.append(Path(local) / "OpenAI" / "Codex" / "bin")
    pf = os.environ.get("PROGRAMFILES")
    if pf:
        bases.append(Path(pf) / "OpenAI" / "Codex" / "bin")
    found = []
    for base in bases:
        if not base.is_dir():
            continue
        for d in base.iterdir():
            for name in ("codex.exe", "codex.cmd"):
                p = d / name
                if p.is_file():
                    found.append(p)
    if not found:
        raise SystemExit("找不到 codex.exe，请用 --codex-exe 指定路径")
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return str(found[0])

def open_ro(db_path: Path):
    """只读打开 sqlite；失败时复制快照再读。"""
    if not db_path.exists():
        return None
    try:
        uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=3)
        con.execute("select 1").fetchone()
        return con
    except sqlite3.Error:
        pass
    try:
        snap_dir = Path(os.environ.get("TEMP", ".")) / "codex-watchdog-snap"
        snap_dir.mkdir(parents=True, exist_ok=True)
        for suf in ("", "-wal", "-shm"):
            src = Path(str(db_path) + suf)
            if src.exists():
                shutil.copy2(src, snap_dir / (db_path.name + suf))
        uri = "file:" + str(snap_dir / db_path.name).replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=3)
        con.execute("select 1").fetchone()
        return con
    except Exception as exc:  # noqa: BLE001
        log("[warn] 无法读取 %s: %s" % (db_path.name, exc))
        return None

# ---------------------------------------------------------------- 状态读取

TURN_ID_RE = re.compile(r'turn\.id="([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"')
SUBMIT_ID_RE = re.compile(r'submission\.id="([0-9a-f-]{20,})"')
MODEL_RE = re.compile(r'\bmodel=([A-Za-z0-9][\w.\-]*)\b')
EFFORT_RE = re.compile(r'reasoning_effort=([a-z]+)')
ERROR_MARKERS = ("turn error:", "selected model is at capacity", "serveroverloaded",
                 "at capacity", "stream disconnected", "connection closed", "overloaded")

class CodexState:
    def __init__(self, codex_home: Path):
        self.home = codex_home
        self.logs_db = codex_home / "logs_2.sqlite"
        self.hist_db = codex_home / "thread_history_1.sqlite"
        self.state_db = codex_home / "state_5.sqlite"
        self.logs_watermark = -1
        self.recent_rows = []
        self.max_cache = 6000

    def poll_logs(self) -> int:
        con = open_ro(self.logs_db)
        if con is None:
            return 0
        try:
            row = con.execute("select coalesce(max(id),0) from logs").fetchone()
            cur_max = int(row[0] or 0)
            if self.logs_watermark < 0:
                rows = con.execute(
                    "select id,ts,level,target,thread_id,feedback_log_body "
                    "from logs order by id desc limit 4000").fetchall()
                new_rows = list(reversed(rows))
            elif cur_max > self.logs_watermark:
                new_rows = con.execute(
                    "select id,ts,level,target,thread_id,feedback_log_body "
                    "from logs where id > ? order by id", (self.logs_watermark,)).fetchall()
            else:
                new_rows = []
            self.logs_watermark = max(self.logs_watermark, cur_max)
            for r in new_rows:
                self.recent_rows.append({
                    "id": r[0], "ts": r[1], "level": r[2], "target": r[3] or "",
                    "thread_id": r[4] or "", "body": r[5] or "",
                })
            if len(self.recent_rows) > self.max_cache:
                self.recent_rows = self.recent_rows[-self.max_cache:]
            return len(new_rows)
        finally:
            con.close()

    def thread_rows(self, thread_id: str):
        rows = []
        for r in self.recent_rows:
            if r["thread_id"] == thread_id or (not r["thread_id"] and thread_id in r["body"]):
                rows.append(r)
        return rows

    def thread_meta(self, thread_id: str) -> dict:
        meta = {"id": thread_id, "cwd": None, "model": None, "sandbox_policy": None,
                "approval_mode": None, "title": None, "rollout_path": None}
        con = open_ro(self.state_db)
        if con is not None:
            try:
                row = con.execute(
                    "select cwd,model,sandbox_policy,approval_mode,title,rollout_path "
                    "from threads where id=?", (thread_id,)).fetchone()
                if row:
                    meta.update(cwd=row[0], model=row[1], sandbox_policy=row[2],
                                approval_mode=row[3], title=row[4], rollout_path=row[5])
            except sqlite3.Error:
                pass
            finally:
                con.close()
        return meta

    def turn_status(self, turn_id: str):
        con = open_ro(self.hist_db)
        if con is None:
            return None
        try:
            row = con.execute(
                "select thread_id,status,error_json,started_at,completed_at,duration_ms "
                "from thread_turns where turn_id=?", (turn_id,)).fetchone()
            if not row:
                return None
            return {"row_thread_id": row[0], "status": row[1], "error": row[2],
                    "started_at": row[3], "completed_at": row[4], "duration_ms": row[5]}
        except sqlite3.Error:
            return None
        finally:
            con.close()

    def queued_ids(self, thread_id: str) -> list:
        con = open_ro(self.home / "queue_1.sqlite")
        if con is None:
            return []
        try:
            rows = con.execute("select id from queued_items where thread_id like ?",
                               (thread_id + "%",)).fetchall()
            return [r[0] for r in rows]
        except sqlite3.Error:
            return []
        finally:
            con.close()

    def judge(self, thread_id: str, stall_seconds: float, max_turn_age: float) -> dict:
        ts_now = now_ts()
        self.poll_logs()
        recent = self.thread_rows(thread_id)
        if not recent:
            return {"verdict": "unknown", "idle_seconds": None, "last_turn": None,
                    "turn_status": None, "error": None, "model": None, "effort": None}
        recent.sort(key=lambda r: r["id"])
        last = recent[-1]
        last_ts = float(last["ts"])
        last_turn = None
        for r in reversed(recent):
            m = TURN_ID_RE.search(r["body"])
            if m:
                last_turn = m.group(1)
                break
        err = None
        for r in reversed(recent[-400:]):
            b = r["body"]
            low = b.lower()
            if any(k in low for k in ERROR_MARKERS):
                err = {"ts": r["ts"], "level": r["level"], "text": b[-320:].strip()}
                break
        status = self.turn_status(last_turn) if last_turn else None
        model = None
        effort = None
        for r in reversed(recent[-600:]):
            if model is None:
                mm = MODEL_RE.search(r["body"])
                if mm:
                    model = mm.group(1)
            if effort is None:
                em = EFFORT_RE.search(r["body"])
                if em:
                    effort = em.group(1)
            if model and effort:
                break
        idle = ts_now - last_ts
        st = (status or {}).get("status")
        started = (status or {}).get("started_at")
        if st == "inProgress" and started and (ts_now - float(started)) < max_turn_age:
            verdict = "running"
            reason = "turn in progress"
        elif st == "completed" and started and (ts_now - float(started)) < max_turn_age:
            verdict = "completed"
            reason = "turn completed"
        elif st in ("failed", "interrupted"):
            # 无视桌面端的自动重试节奏：失败即接管，立刻补一条重试
            verdict = "stalled"
            reason = "turn %s (ignore desktop auto-retry)" % st
        elif idle <= stall_seconds:
            verdict = "running"
            reason = "recent activity"
        else:
            verdict = "stalled"
            reason = "idle %.0fs" % idle
        return {"verdict": verdict, "reason": reason, "idle_seconds": round(idle, 1),
                "last_turn": last_turn, "turn_status": status, "error": err,
                "model": model, "effort": effort, "last_activity": last_ts}

    def newest_turn_id(self, thread_id: str) -> str | None:
        self.poll_logs()
        recent = self.thread_rows(thread_id)
        recent.sort(key=lambda r: r["id"])
        for r in reversed(recent):
            m = TURN_ID_RE.search(r["body"])
            if m:
                return m.group(1)
        return None

# ---------------------------------------------------------------- 执行器

CREATE_NO_WINDOW = 0x08000000

class Runner:
    def __init__(self, codex_exe: str, log_dir: Path):
        self.codex_exe = codex_exe
        self.log_dir = log_dir

    def _run_cmd(self, cmd, timeout: float) -> dict:
        log("[cmd] " + " ".join(cmd))
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout,
                               creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0)
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "stderr": "timeout", "rc": None}
        except OSError as exc:
            return {"ok": False, "stdout": "", "stderr": "spawn failed: %s" % exc, "rc": None}
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        if out:
            log("[out] " + out[-600:].replace("\n", " | "))
        if err:
            log("[err] " + err[-600:].replace("\n", " | "))
        return {"ok": p.returncode == 0, "stdout": out, "stderr": err, "rc": p.returncode}

    def queue_message(self, thread_id: str, prompt: str, timeout: float = 60) -> dict:
        """官方交互桥：把消息排进已有会话，由桌面端 app-server 消费。"""
        cmd = [self.codex_exe, "queue", "--thread", thread_id, "--message", prompt]
        return self._run_cmd(cmd, timeout)

    def exec_resume(self, thread_id: str, prompt: str, meta: dict, model, effort,
                    turn_timeout: float) -> dict:
        """兜底：桌面端关闭/队列无人消费时，独立进程续跑（会被 thread 写锁挡住）。"""
        cmd = [self.codex_exe, "exec", "resume", thread_id, prompt,
               "--json", "--skip-git-repo-check",
               "--dangerously-bypass-approvals-and-sandbox"]
        if model:
            cmd += ["-m", model]
        if effort:
            cmd += ["-c", 'model_reasoning_effort="%s"' % effort]
        cwd = meta.get("cwd") or None
        if cwd and cwd.startswith("\\\\?\\"):
            cwd = cwd[4:]
        log("[exec] " + " ".join(cmd))
        out_path = self.log_dir / ("exec-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".jsonl")
        result = {"ok": False, "completed": False, "error": None, "last_message": None,
                  "exit_code": None, "events": 0, "log_file": str(out_path)}
        try:
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0)
        except OSError as exc:
            result["error"] = "启动失败: %s" % exc
            return result
        killed = {"flag": False}

        def _kill():
            killed["flag"] = True
            try:
                proc.kill()
            except Exception:
                pass

        timer = threading.Timer(turn_timeout, _kill)
        timer.daemon = True
        timer.start()
        last_msg = None
        err_msg = None
        completed = False
        rc = None
        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                assert proc.stdout is not None
                for line in proc.stdout:
                    fh.write(line)
                    fh.flush()
                    if killed["flag"]:
                        break
                    s = line.strip()
                    if not s.startswith("{"):
                        continue
                    try:
                        ev = json.loads(s)
                    except json.JSONDecodeError:
                        continue
                    result["events"] += 1
                    low = str(ev.get("type", "")).lower()
                    if "failed" in low or low in ("error",):
                        err_msg = json.dumps(ev.get("error") or ev, ensure_ascii=False)[:800]
                    elif "completed" in low:
                        completed = True
                    if low in ("item.completed", "item_completed"):
                        item = ev.get("item") or {}
                        if item.get("type") in ("agent_message", "assistant_message", "message"):
                            txt = item.get("text") or item.get("content") or ""
                            if isinstance(txt, str) and txt.strip():
                                last_msg = txt.strip()[-1500:]
            try:
                rc = proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait(timeout=10)
        finally:
            timer.cancel()
        if killed["flag"]:
            result["error"] = "超时被终止（>%ds）" % int(turn_timeout)
        elif rc != 0:
            result["error"] = err_msg or ("codex 退出码 %s" % rc)
        else:
            result["ok"] = True
            if not completed:
                result["error"] = err_msg
        result["exit_code"] = rc
        result["completed"] = completed and rc == 0
        result["last_message"] = last_msg
        return result

# ---------------------------------------------------------------- 锁/进程

def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                                 capture_output=True, text=True, timeout=10)
            return str(pid) in (out.stdout or "")
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def acquire_lock(lock_path: Path) -> bool:
    if lock_path.exists():
        try:
            old = int(lock_path.read_text(encoding="utf-8").strip() or "0")
        except Exception:
            old = 0
        if old and pid_alive(old):
            return False
        log("[lock] 清理过期锁 pid=%s" % old)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    return True

# ---------------------------------------------------------------- 主循环

def main(argv) -> int:
    setup_stdout()
    ap = argparse.ArgumentParser(
        description="Codex 会话自动重试守护：codex queue 交互桥 + 失败退避，直到 turn 完成")
    ap.add_argument("--thread", required=True, help="目标会话 UUID")
    ap.add_argument("--codex-home", default=None, help="CODEX_HOME，默认 ~/.codex")
    ap.add_argument("--codex-exe", default=None, help="codex.exe 路径，默认自动探测")
    ap.add_argument("--interval", type=float, default=15, help="轮询间隔秒（默认 15）")
    ap.add_argument("--stall-seconds", type=float, default=120,
                    help="无 inProgress turn 且静默多久算停摆（默认 120）")
    ap.add_argument("--max-turn-age", type=float, default=7200,
                    help="inProgress turn 的最大合理时长，超过视为卡死（默认 7200）")
    ap.add_argument("--consume-timeout", type=float, default=90,
                    help="queue 后等待被桌面端消费的秒数（默认 90）")
    ap.add_argument("--turn-timeout", type=float, default=3600,
                    help="等待单轮结束的最长秒数（默认 3600）")
    ap.add_argument("--max-attempts", type=int, default=0, help="最多接管次数，0=不限")
    ap.add_argument("--backoff-base", type=float, default=10, help="失败退避起始秒（默认 10）")
    ap.add_argument("--backoff-max", type=float, default=300, help="失败退避上限秒（默认 300）")
    ap.add_argument("--prompt", default=" ",
                    help="续跑时排队的消息内容。默认单个空格 = 纯空输入重试，"
                         "效果等同 Codex 自己的自动重试（user_input_count=0），不向会话注入任何文案")
    ap.add_argument("--model", default=None, help="exec 兜底时覆盖模型")
    ap.add_argument("--effort", default=None, help="exec 兜底时覆盖 reasoning effort")
    ap.add_argument("--exec-fallback", action="store_true",
                    help="queue 未被消费时回退到 codex exec resume")
    ap.add_argument("--log-dir", default=None, help="日志目录，默认脚本同级 logs/")
    ap.add_argument("--dry-run", action="store_true", help="只判定不执行")
    ap.add_argument("--once", action="store_true", help="只跑一个 tick 后退出")
    ap.add_argument("--no-lock", action="store_true", help="不加单实例锁")
    args = ap.parse_args(argv)

    codex_home = Path(args.codex_home) if args.codex_home else Path(
        os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    if not codex_home.exists():
        log("[fatal] CODEX_HOME 不存在: %s" % codex_home)
        return 2
    log_dir = Path(args.log_dir) if args.log_dir else (Path(__file__).resolve().parent / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "watchdog.log"

    class Tee:
        def __init__(self, *streams):
            self.streams = streams
        def write(self, s):
            for st in self.streams:
                try:
                    st.write(s)
                except Exception:
                    pass
        def flush(self):
            for st in self.streams:
                try:
                    st.flush()
                except Exception:
                    pass

    log_fh = open(log_file, "a", encoding="utf-8", buffering=1)
    sys.stdout = Tee(sys.__stdout__, log_fh)
    sys.stderr = Tee(sys.__stderr__, log_fh)

    if not args.no_lock:
        lock_path = log_dir / "watchdog.lock"
        if not acquire_lock(lock_path):
            log("[fatal] 已有守护进程在运行（锁 %s），退出" % lock_path)
            return 3

    codex_exe = args.codex_exe or find_codex_exe()
    log("=" * 72)
    log("启动守护 thread=%s" % args.thread)
    log("codex=%s" % codex_exe)
    log("codex_home=%s" % codex_home)
    log("interval=%ss stall=%ss dry_run=%s" % (args.interval, args.stall_seconds, args.dry_run))
    st = CodexState(codex_home)
    meta = st.thread_meta(args.thread)
    log("会话标题=%r cwd=%r model=%r" % (meta.get("title"), meta.get("cwd"), meta.get("model")))
    runner = Runner(codex_exe, log_dir)

    attempts = 0
    fail_streak = 0
    started = now_ts()

    def wait_for_consume(before_turn, wait_seconds):
        """等待桌面端消费队列消息：出现新 turn / 新活动。"""
        t0 = now_ts()
        while now_ts() - t0 < wait_seconds:
            time.sleep(3)
            j = st.judge(args.thread, args.stall_seconds, args.max_turn_age)
            nt = j.get("last_turn")
            if nt and nt != before_turn:
                log("       [consume] 队列消息已被消费，新 turn=%s" % nt[:14])
                return True, j
            if j.get("idle_seconds") is not None and j["idle_seconds"] < 10:
                log("       [consume] 检测到新活动（turn 变化滞后）")
                return True, j
        return False, st.judge(args.thread, args.stall_seconds, args.max_turn_age)

    def track_turn(turn_id, timeout):
        """跟踪指定 turn 直到 completed/failed/interrupted；自动重试产生新 turn 时切换跟踪。"""
        t0 = now_ts()
        cur = turn_id
        while now_ts() - t0 < timeout:
            time.sleep(max(5.0, args.interval))
            j = st.judge(args.thread, args.stall_seconds, args.max_turn_age)
            nt = j.get("last_turn")
            if nt and nt != cur:
                log("       [track] 出现新 turn=%s（跟进）" % nt[:14])
                cur = nt
            info = st.turn_status(cur)
            if info:
                s = info.get("status")
                if s in ("completed", "failed", "interrupted"):
                    return s, info, cur
            if j.get("verdict") == "stalled":
                return "stalled", None, cur
        return "timeout", None, cur

    try:
        while True:
            j = st.judge(args.thread, args.stall_seconds, args.max_turn_age)
            v = j["verdict"]
            stt = (j.get("turn_status") or {}).get("status")
            log("[tick] verdict=%s reason=%s idle=%ss turn=%s status=%s model=%s effort=%s" % (
                v, j.get("reason"), j.get("idle_seconds"), str(j.get("last_turn"))[:14],
                stt, j.get("model"), j.get("effort")))
            if j.get("error"):
                log("       最近错误: %r" % j["error"]["text"][-240:])

            if v == "completed":
                # turn 已完成：再观察一个 grace 周期，确认没有新的失败重试
                log("       最后 turn 已完成，等待 %ss 确认无新失败..." % int(args.interval * 2))
                if args.once:
                    return 0
                time.sleep(args.interval * 2)
                j2 = st.judge(args.thread, args.stall_seconds, args.max_turn_age)
                if j2["verdict"] == "completed":
                    log("       任务完成（turn completed，无新失败）")
                    break
                continue

            if v == "running":
                log("       会话仍在运行/自动重试，本轮不接管（%s）" % j.get("reason"))
                if args.once:
                    return 0
                time.sleep(args.interval)
                continue

            if v == "unknown":
                log("       日志中尚无该会话记录，等待")
                if args.once:
                    return 0
                time.sleep(args.interval)
                continue

            if args.max_attempts and attempts >= args.max_attempts:
                log("       达到最大接管次数 %s，退出" % args.max_attempts)
                break

            if args.once:
                log("       [once] 会话已停摆，执行一次接管")
            if args.dry_run:
                log("       [dry-run] 本应 codex queue 续跑消息，跳过")
                return 0

            attempts += 1
            backoff = min(args.backoff_base * (2 ** max(0, fail_streak - 1)), args.backoff_max) if fail_streak else 0
            if backoff:
                log("       退避 %.0fs（连续失败 %d 次）" % (backoff, fail_streak))
                time.sleep(backoff)

            before = st.newest_turn_id(args.thread)
            log("[queue] 第 %d 次接管（before_turn=%s）" % (attempts, str(before)[:14]))
            qres = runner.queue_message(args.thread, args.prompt)
            if not qres["ok"]:
                log("       queue 失败: %r" % (qres["stderr"][-300:] or qres["stdout"][-300:]))
                fail_streak += 1
                if args.once:
                    return 0
                time.sleep(max(5.0, args.interval))
                continue

            consumed, jj = wait_for_consume(before, args.consume_timeout)
            if not consumed:
                log("       queue 消息 %ss 内未被消费" % int(args.consume_timeout))
                if args.exec_fallback:
                    model = args.model or j.get("model") or meta.get("model")
                    effort = args.effort or j.get("effort")
                    log("[exec] 回退 exec resume model=%s effort=%s" % (model, effort))
                    res = runner.exec_resume(args.thread, args.prompt, meta, model, effort,
                                              args.turn_timeout)
                    log("[exec] ok=%s completed=%s err=%r" % (res["ok"], res["completed"], res["error"]))
                    if res["completed"]:
                        fail_streak = 0
                        log("       本轮 turn 正常完成")
                        break
                fail_streak += 1
                if args.once:
                    return 0
                time.sleep(max(5.0, args.interval))
                continue

            turn_id = jj.get("last_turn")
            log("[track] 跟踪 turn=%s" % str(turn_id)[:14])
            outcome, info, final_turn = track_turn(turn_id, args.turn_timeout)
            log("[track] 结果=%s turn=%s" % (outcome, str(final_turn)[:14]))
            if info and info.get("error"):
                log("       错误: %r" % str(info["error"])[-260:])
            if outcome == "completed":
                fail_streak = 0
                log("       本轮 turn 正常完成")
                break
            if outcome in ("failed", "interrupted"):
                fail_streak += 1
                log("       本轮失败（第 %d 次连续失败）" % fail_streak)
            elif outcome in ("stalled", "timeout"):
                fail_streak += 1
                log("       本轮停摆/超时（第 %d 次连续失败）" % fail_streak)
            if args.once:
                return 0

        elapsed = now_ts() - started
        log("守护结束：运行 %.0fs，接管 %d 次" % (elapsed, attempts))
        return 0
    except KeyboardInterrupt:
        log("收到中断，退出")
        return 130
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            log_fh.close()
        except Exception:
            pass

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
