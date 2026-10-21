#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_models.py - 并行探测各模型当前容量是否可用（小请求，独立会话，不碰原会话锁）。"""
import os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000
MODELS = [
    ("gpt-6-astra", "ultra"), ("gpt-6-astra", "xhigh"),
    ("gpt-6.1-sol", "max"), ("gpt-6.1-sol", "xhigh"),
    ("gpt-reserve", "xhigh"), ("gpt-6-luna", "xhigh"),
    ("gpt-6-sol", "xhigh"), ("gpt-5.6-sol", "xhigh"),
    ("gpt-5.6-terra", "xhigh"), ("gpt-5.6-luna", "xhigh"),
]

def now(): return datetime.now().strftime("%H:%M:%S")

def find_codex():
    env = os.environ.get("CODEX_EXE")
    if env and Path(env).exists(): return env
    w = shutil.which("codex.exe") or shutil.which("codex")
    if w: return w
    local = os.environ.get("LOCALAPPDATA")
    base = Path(local)/"OpenAI"/"Codex"/"bin"
    c = []
    if base.is_dir():
        for d in base.iterdir():
            for n in ("codex.exe","codex.cmd"):
                p = d/n
                if p.is_file(): c.append(p)
    if c:
        c.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return str(c[0])
    raise SystemExit("找不到 codex.exe")

def test(codex, model, effort, timeout=100):
    cmd = [codex,"exec","--ephemeral","--skip-git-repo-check","-s","read-only",
           "-m", model, "-c", 'model_reasoning_effort="%s"' % effort,
           "Reply with exactly: OK"]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout,
                           creationflags=CREATE_NO_WINDOW if os.name=="nt" else 0)
        out = (p.stdout or "") + (p.stderr or "")
        ok = "OK" in out and "capacity" not in out.lower() and p.returncode == 0
        err = ""
        if not ok:
            for line in out.splitlines():
                if "capacity" in line.lower() or "ERROR" in line:
                    err = line.strip()[:120]; break
        return model, effort, ok, round(time.time()-t0,1), err
    except subprocess.TimeoutExpired:
        return model, effort, False, timeout, "timeout"

def main():
    for st in (sys.stdout, sys.stderr):
        try: st.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass
    here = Path(__file__).resolve().parent
    log_dir = here/"logs"; log_dir.mkdir(exist_ok=True)
    fh = open(log_dir/"probe.log","a",encoding="utf-8",buffering=1)
    class T:
        def write(self,s):
            try: sys.__stdout__.write(s)
            except Exception: pass
            fh.write(s)
        def flush(self):
            try: sys.__stdout__.flush()
            except Exception: pass
            fh.flush()
    sys.stdout = T()
    codex = find_codex()
    print("="*70, flush=True)
    print("[%s] 模型容量并行探测器启动（%d 组）" % (now(), len(MODELS)), flush=True)
    round_no = 0
    while True:
        round_no += 1
        print("[%s] ---- 第 %d 轮探测 ----" % (now(), round_no), flush=True)
        with ThreadPoolExecutor(max_workers=len(MODELS)) as ex:
            futs = [ex.submit(test, codex, m, e) for m, e in MODELS]
            results = [f.result() for f in futs]
        avail = []
        for model, effort, ok, dur, err in results:
            print("  %-14s %-6s %-6s %5.1fs  %s" % (model, effort, "可用" if ok else "失败", dur, err), flush=True)
            if ok: avail.append("%s:%s" % (model, effort))
        print("[%s] 本轮可用: %s" % (now(), ", ".join(avail) if avail else "无（全部容量不足）"), flush=True)
        time.sleep(60)
        continue

if __name__ == "__main__":
    raise SystemExit(main())
