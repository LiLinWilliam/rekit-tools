#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multi_retry.py - 同一会话上轮换多个模型/档位死磕，直到某个模型能跑完 turn。

同一 thread 同一时刻只能有一个 writer，所以这里是"轮换"而不是并发撞锁：
每次失败后换下一组 (model, effort)，无限循环，直到 turn.completed。
"""
import argparse, json, os, shutil, subprocess, sys, time
from datetime import datetime
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def find_codex():
    env = os.environ.get("CODEX_EXE")
    if env and Path(env).exists(): return env
    w = shutil.which("codex.exe") or shutil.which("codex")
    if w: return w
    local = os.environ.get("LOCALAPPDATA")
    if local:
        base = Path(local) / "OpenAI" / "Codex" / "bin"
        if base.is_dir():
            c = []
            for d in base.iterdir():
                for n in ("codex.exe","codex.cmd"):
                    p = d/n
                    if p.is_file(): c.append(p)
            if c:
                c.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return str(c[0])
    raise SystemExit("找不到 codex.exe")

class Tee:
    def __init__(self,*s): self.s=s
    def write(self,x):
        for st in self.s:
            try: st.write(x)
            except Exception: pass
    def flush(self):
        for st in self.s:
            try: st.flush()
            except Exception: pass

def run_once(codex, thread, prompt, model, effort, tier, cwd, out_dir):
    cmd = [codex,"exec","resume",thread,prompt,"--json","--skip-git-repo-check",
           "--dangerously-bypass-approvals-and-sandbox","-m",model]
    if effort: cmd += ["-c", 'model_reasoning_effort="%s"' % effort]
    if tier: cmd += ["-c", 'service_tier="%s"' % tier]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    jl = Path(out_dir)/("multi-%s-%s.jsonl" % (model, stamp))
    print("[%s] [cmd] %s | model=%s effort=%s" % (now(), " ".join(cmd[:6]), model, effort), flush=True)
    res = {"completed": False, "error": None, "last_msg": None, "events": 0, "jsonl": str(jl)}
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", bufsize=1,
                             creationflags=CREATE_NO_WINDOW if os.name=="nt" else 0)
    except OSError as e:
        res["error"] = "spawn failed: %s" % e; return res
    err = None; last = None
    with open(jl,"w",encoding="utf-8") as fh:
        for line in p.stdout:
            fh.write(line); fh.flush()
            s = line.strip()
            if not s.startswith("{"): continue
            try: ev = json.loads(s)
            except Exception: continue
            res["events"] += 1
            low = str(ev.get("type","")).lower()
            if low == "turn.failed":
                e = ev.get("error") or {}
                err = e.get("message") if isinstance(e,dict) else str(e)
            elif low == "error":
                m = str(ev.get("message") or "")
                if m: err = m
            elif low == "turn.completed":
                res["completed"] = True
            elif low == "item.completed":
                it = ev.get("item") or {}
                if it.get("type") in ("agent_message","assistant_message","message"):
                    t = it.get("text") or it.get("content") or ""
                    if isinstance(t,str) and t.strip(): last = t.strip()[-800:]
    rc = p.wait()
    res["error"] = err or ("exit %s" % rc if rc != 0 else None)
    res["last_msg"] = last
    return res

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--thread", required=True)
    ap.add_argument("--models", default="gpt-6-astra:ultra,gpt-6.1-sol:max,gpt-reserve:xhigh,gpt-6-luna:xhigh,gpt-6.1-sol:xhigh,gpt-5.6-sol:xhigh")
    ap.add_argument("--tier", default="priority")
    ap.add_argument("--cwd", default="D:\\ruanzhu")
    ap.add_argument("--prompt", default="继续")
    ap.add_argument("--round-sleep", type=float, default=15)
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--codex-exe", default=None)
    args = ap.parse_args(argv)
    for st in (sys.stdout,sys.stderr):
        try: st.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass
    log_dir = Path(args.log_dir) if args.log_dir else (Path(__file__).resolve().parent/"logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = open(log_dir/"multi_retry.log","a",encoding="utf-8",buffering=1)
    sys.stdout = Tee(sys.__stdout__, fh); sys.stderr = Tee(sys.__stderr__, fh)
    codex = args.codex_exe or find_codex()
    pairs = []
    for item in args.models.split(","):
        item = item.strip()
        if not item: continue
        if ":" in item:
            m,e = item.split(":",1)
        else:
            m,e = item,""
        pairs.append((m.strip(), e.strip()))
    print("="*72, flush=True)
    print("[%s] 多模型轮换死磕 thread=%s" % (now(), args.thread), flush=True)
    print("[%s] 轮换顺序: %s" % (now(), " -> ".join("%s/%s" % p for p in pairs)), flush=True)
    i = 0
    attempt = 0
    while True:
        model, effort = pairs[i % len(pairs)]
        i += 1
        attempt += 1
        print("[%s] === 第 %d 次：%s + %s ===" % (now(), attempt, model, effort), flush=True)
        r = run_once(codex, args.thread, args.prompt, model, effort, args.tier, args.cwd, str(log_dir))
        print("[%s] completed=%s events=%s err=%r" % (now(), r["completed"], r["events"], r["error"]), flush=True)
        if r["last_msg"]:
            print("[%s] 最后输出: %r" % (now(), r["last_msg"][-300:]), flush=True)
        if r["completed"]:
            print("[%s] *** %s 成功完成，退出 ***" % (now(), model), flush=True)
            return 0
        low = (r["error"] or "").lower()
        if "active writer" in low or "thread-store conflict" in low:
            print("[%s] 写锁被占（Codex 被打开了？），等 60s" % now(), flush=True)
            time.sleep(60)
            continue
        time.sleep(args.round_sleep)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
