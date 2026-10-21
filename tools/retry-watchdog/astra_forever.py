#!/usr/bin/env python3
"""astra_forever.py - 用 astra + ultra 死磕一个会话，直到 turn 成功完成。

前提：Codex 桌面端已关闭（否则 thread 写锁被占，exec resume 会报 active writer）。
失败（容量不足 / 断流）自动指数退避重试；写锁被占时等待，不强行抢。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_VERSION_ROOT = Path(__file__).resolve().parents[1]
if str(_VERSION_ROOT) not in sys.path:
    sys.path.insert(0, str(_VERSION_ROOT))
from _version import add_version  # noqa: E402

CREATE_NO_WINDOW = 0x08000000

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def find_codex():
    env = os.environ.get("CODEX_EXE")
    if env and Path(env).exists():
        return env
    w = shutil.which("codex.exe") or shutil.which("codex")
    if w:
        return w
    local = os.environ.get("LOCALAPPDATA")
    if local:
        base = Path(local) / "OpenAI" / "Codex" / "bin"
        if base.is_dir():
            cands = []
            for d in base.iterdir():
                for n in ("codex.exe", "codex.cmd"):
                    p = d / n
                    if p.is_file():
                        cands.append(p)
            if cands:
                cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return str(cands[0])
    raise SystemExit("找不到 codex.exe，用 --codex-exe 指定")

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

def run_once(codex, thread, prompt, model, effort, tier, cwd, out_dir):
    cmd = [codex, "exec", "resume", thread, prompt, "--json",
           "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
           "-m", model]
    if effort:
        cmd += ["-c", 'model_reasoning_effort="%s"' % effort]
    if tier:
        cmd += ["-c", 'service_tier="%s"' % tier]
    print("[cmd] " + " ".join(cmd), flush=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    jl = Path(out_dir) / ("exec-%s.jsonl" % stamp)
    res = {"completed": False, "failed": False, "error": None, "last_msg": None,
           "exit_code": None, "events": 0, "jsonl": str(jl)}
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                             errors="replace", bufsize=1,
                             creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0)
    except OSError as e:
        res["error"] = "spawn failed: %s" % e
        return res
    last_msg = None
    err_msg = None
    with open(jl, "w", encoding="utf-8") as fh:
        assert p.stdout is not None
        for line in p.stdout:
            fh.write(line); fh.flush()
            s = line.strip()
            if not s.startswith("{"):
                continue
            try:
                ev = json.loads(s)
            except json.JSONDecodeError:
                continue
            res["events"] += 1
            low = str(ev.get("type", "")).lower()
            if low == "turn.failed":
                res["failed"] = True
                err = ev.get("error") or {}
                err_msg = err.get("message") if isinstance(err, dict) else str(err)
            elif low in ("error",):
                msg = str(ev.get("message") or "")
                if msg and "capacity" in msg.lower():
                    err_msg = msg
            elif low == "turn.completed":
                res["completed"] = True
            elif low == "item.completed":
                item = ev.get("item") or {}
                if item.get("type") in ("agent_message", "assistant_message", "message"):
                    t = item.get("text") or item.get("content") or ""
                    if isinstance(t, str) and t.strip():
                        last_msg = t.strip()[-800:]
    res["exit_code"] = p.wait()
    res["error"] = err_msg
    res["last_msg"] = last_msg
    if res["exit_code"] != 0 and not res["error"]:
        res["error"] = "exit %s" % res["exit_code"]
    return res

def main(argv):
    ap = argparse.ArgumentParser()
    add_version(ap)
    ap.add_argument("--thread", required=True)
    ap.add_argument("--model", default="gpt-6-astra")
    ap.add_argument("--effort", default="ultra")
    ap.add_argument("--tier", default="priority")
    ap.add_argument("--cwd", default="D:\\ruanzhu")
    ap.add_argument("--prompt", default="继续")
    ap.add_argument("--prompt-file", default=None, help="从 UTF-8 文件读取 prompt（避免编码问题）")
    ap.add_argument("--max-attempts", type=int, default=0)
    ap.add_argument("--backoff-base", type=float, default=20)
    ap.add_argument("--backoff-max", type=float, default=300)
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--codex-exe", default=None)
    args = ap.parse_args(argv)

    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    log_dir = Path(args.log_dir) if args.log_dir else (Path(__file__).resolve().parent / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_dir / "astra_retry.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = Tee(sys.__stdout__, log_fh)
    sys.stderr = Tee(sys.__stderr__, log_fh)

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    codex = args.codex_exe or find_codex()
    print("=" * 70, flush=True)
    print("[%s] 启动死磕：thread=%s model=%s effort=%s tier=%s cwd=%s" % (
        now(), args.thread, args.model, args.effort, args.tier, args.cwd), flush=True)
    print("[%s] codex=%s" % (now(), codex), flush=True)

    attempt = 0
    backoff = args.backoff_base
    while True:
        attempt += 1
        print("[%s] === 第 %d 次尝试（%s + %s）===" % (now(), attempt, args.model, args.effort), flush=True)
        r = run_once(codex, args.thread, prompt, args.model, args.effort,
                     args.tier, args.cwd, str(log_dir))
        print("[%s] 结果 completed=%s failed=%s exit=%s events=%s err=%r" % (
            now(), r["completed"], r["failed"], r["exit_code"], r["events"], r["error"]), flush=True)
        if r["last_msg"]:
            print("[%s] 最后输出: %r" % (now(), r["last_msg"][-400:]), flush=True)
        if r["completed"]:
            print("[%s] *** 成功完成，退出 ***" % now(), flush=True)
            return 0
        low = (r["error"] or "").lower()
        if "active writer" in low or "thread-store conflict" in low:
            wait = 60
            print("[%s] 写锁被占（Codex 可能被打开了），等 %ss 再试" % (now(), wait), flush=True)
            time.sleep(wait)
            continue
        if args.max_attempts and attempt >= args.max_attempts:
            print("[%s] 达到最大尝试次数 %d，退出" % (now(), args.max_attempts), flush=True)
            return 1
        print("[%s] 退避 %.0fs 后重试" % (now(), backoff), flush=True)
        time.sleep(backoff)
        backoff = min(backoff * 2, args.backoff_max)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
