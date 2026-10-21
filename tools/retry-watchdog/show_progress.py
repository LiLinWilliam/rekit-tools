#!/usr/bin/env python3
"""查看某个 Codex 会话的最新进展（读 rollout，不碰任何运行中的东西）。

用法:
  python show_progress.py                    # 列出最近 10 个会话
  python show_progress.py <thread-id>        # 看某会话最近 20 条事件
  python show_progress.py <thread-id> -n 50
"""
import datetime
import json
import os
import sqlite3
import sys
from pathlib import Path

HOME = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))

def conn(name):
    p = HOME / name
    return sqlite3.connect("file:" + str(p).replace("\\", "/") + "?mode=ro", uri=True)

def list_threads(limit=10):
    c = conn("state_5.sqlite")
    rows = c.execute(
        "select id,title,model,reasoning_effort,cwd,updated_at,source,rollout_path "
        "from threads order by updated_at desc limit ?", (limit,)).fetchall()
    print("%-38s %-14s %-6s %-20s %s" % ("ID", "MODEL", "EFFORT", "UPDATED", "TITLE"))
    for r in rows:
        upd = datetime.datetime.fromtimestamp(r[5]).strftime("%m-%d %H:%M") if r[5] else "-"
        print("%-38s %-14s %-6s %-20s %s" % (r[0], r[2] or "-", r[3] or "-", upd, (r[1] or "")[:50]))

def show(thread_id, n=20):
    c = conn("state_5.sqlite")
    r = c.execute("select title,model,reasoning_effort,cwd,rollout_path from threads where id=?",
                  (thread_id,)).fetchone()
    if not r:
        print("找不到会话:", thread_id); return 1
    title, model, effort, cwd, rollout = r
    print("会话: %s" % thread_id)
    print("标题: %s" % (title or ""))
    print("模型: %s / %s   目录: %s" % (model, effort, cwd))
    p = (rollout or "").replace("\\\\?\\", "")
    if not p or not os.path.exists(p):
        print("rollout 不存在:", p); return 2
    lines = Path(p).read_text(encoding="utf-8", errors="replace").splitlines()
    print("rollout: %s (%d 条事件, %.1f KB)" % (p, len(lines), os.path.getsize(p)/1024))
    print("-" * 70)
    shown = 0
    for ln in reversed(lines):
        if shown >= n: break
        try:
            d = json.loads(ln)
        except Exception:
            continue
        t = d.get("type"); pl = d.get("payload") or {}
        pt = pl.get("type") if isinstance(pl, dict) else None
        ts = d.get("timestamp")
        brief = None
        if pt == "agent_message":
            brief = (pl.get("message") or pl.get("text") or "")[:500]
        elif pt == "reasoning":
            s = pl.get("summary")
            if s: brief = str(s)[:300]
        elif pt in ("function_call", "custom_tool_call"):
            brief = str(pl.get("name")) + " " + str(pl.get("arguments") or pl.get("input") or "")[:300]
        elif pt in ("exec_command_begin", "command_execution"):
            brief = str(pl.get("command"))[:300]
        elif pt == "task_complete":
            brief = "task_complete error=%s last_msg=%s" % (
                (pl.get("error") or {}).get("message"), str(pl.get("last_agent_message"))[:200])
        if brief:
            print("[%s] %s/%s\n  %s" % (ts or "", t, pt, brief.replace("\n", "\n  ")))
            shown += 1
    return 0

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:]]
    n = 20
    if "-n" in args:
        i = args.index("-n"); n = int(args[i+1]); del args[i:i+2]
    if not args:
        list_threads()
    else:
        sys.exit(show(args[0], n))
