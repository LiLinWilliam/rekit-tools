import re
import sqlite3
import sys

from conftest import load_tool

watchdog = load_tool("tools/retry-watchdog/watchdog.py", "watchdog")


def test_fmt_ts_returns_placeholder_for_invalid_values():
    assert watchdog.fmt_ts("not-a-timestamp") == "-"


def test_fmt_ts_formats_numeric_timestamp():
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", watchdog.fmt_ts(0))


def test_thread_rows_matches_thread_id_and_body():
    state = watchdog.CodexState(__import__("pathlib").Path("."))
    state.recent_rows = [
        {"thread_id": "abc", "body": "direct"},
        {"thread_id": "", "body": "contains abc"},
        {"thread_id": "other", "body": "abc"},
    ]
    rows = state.thread_rows("abc")
    assert [row["body"] for row in rows] == ["direct", "contains abc"]


def test_acquire_lock_rejects_live_process_and_reclaims_stale(tmp_path):
    lock = tmp_path / "watchdog.lock"
    assert watchdog.acquire_lock(lock) is True
    lock.write_text(str(__import__("os").getpid()), encoding="utf-8")
    assert watchdog.acquire_lock(lock) is False
    lock.write_text("not-a-pid", encoding="utf-8")
    assert watchdog.acquire_lock(lock) is True


def test_open_ro_returns_none_for_missing_database(tmp_path):
    assert watchdog.open_ro(tmp_path / "missing.sqlite") is None


def test_open_ro_reads_sqlite_database(tmp_path):
    db = tmp_path / "state.sqlite"
    con = sqlite3.connect(db)
    con.execute("create table values_table (value text)")
    con.execute("insert into values_table values ('ok')")
    con.commit()
    con.close()

    read_only = watchdog.open_ro(db)
    assert read_only is not None
    try:
        assert read_only.execute("select value from values_table").fetchone() == ("ok",)
    finally:
        read_only.close()


def test_find_codex_exe_prefers_existing_environment_path(tmp_path, monkeypatch):
    exe = tmp_path / "codex.exe"
    exe.write_text("placeholder", encoding="ascii")
    monkeypatch.setenv("CODEX_EXE", str(exe))
    assert watchdog.find_codex_exe() == str(exe)


def test_codex_state_reads_thread_metadata(tmp_path):
    db = tmp_path / "state.sqlite"
    con = sqlite3.connect(db)
    con.execute("create table threads (id text, cwd text, model text, sandbox_policy text, "
                "approval_mode text, title text, rollout_path text)")
    con.execute("insert into threads values (?, ?, ?, ?, ?, ?, ?)",
                ("thread-a", "C:/work", "gpt", "workspace", "never", "title", "rollout"))
    con.commit()
    con.close()

    state = watchdog.CodexState(tmp_path)
    state.state_db = db
    assert state.thread_meta("thread-a") == {
        "id": "thread-a", "cwd": "C:/work", "model": "gpt",
        "sandbox_policy": "workspace", "approval_mode": "never",
        "title": "title", "rollout_path": "rollout",
    }


def test_codex_state_reads_turn_status_and_queue_ids(tmp_path):
    hist = tmp_path / "history.sqlite"
    con = sqlite3.connect(hist)
    con.execute("create table thread_turns (thread_id text, status text, error_json text, "
                "started_at real, completed_at real, duration_ms integer, turn_id text)")
    con.execute("insert into thread_turns values (?, ?, ?, ?, ?, ?, ?)",
                ("thread-a", "completed", None, 1.0, 2.0, 1000, "turn-a"))
    con.commit()
    con.close()
    queue = tmp_path / "queue_1.sqlite"
    con = sqlite3.connect(queue)
    con.execute("create table queued_items (id text, thread_id text)")
    con.executemany("insert into queued_items values (?, ?)",
                    [("q1", "thread-a"), ("q2", "thread-ab")])
    con.commit()
    con.close()

    state = watchdog.CodexState(tmp_path)
    state.hist_db = hist
    assert state.turn_status("turn-a")["status"] == "completed"
    assert state.queued_ids("thread-a") == ["q1", "q2"]


def test_judge_returns_unknown_without_recent_rows(tmp_path):
    state = watchdog.CodexState(tmp_path)
    result = state.judge("thread-a", stall_seconds=30, max_turn_age=120)
    assert result["verdict"] == "unknown"
    assert result["last_turn"] is None


def test_judge_marks_recent_activity_running(tmp_path, monkeypatch):
    monkeypatch.setattr(watchdog, "now_ts", lambda: 100.0)
    state = watchdog.CodexState(tmp_path)
    state.recent_rows = [{
        "id": 1, "ts": 95.0, "level": "info", "target": "",
        "thread_id": "thread-a", "body": "model=gpt reasoning_effort=high",
    }]
    result = state.judge("thread-a", stall_seconds=30, max_turn_age=120)
    assert result["verdict"] == "running"
    assert result["model"] == "gpt"
    assert result["effort"] == "high"


def test_runner_run_cmd_captures_success_and_failure(tmp_path):
    runner = watchdog.Runner(sys.executable, tmp_path)
    success = runner._run_cmd([sys.executable, "-c", "print('ok')"], timeout=5)
    failure = runner._run_cmd([sys.executable, "-c", "raise SystemExit(7)"], timeout=5)
    assert success["ok"] is True
    assert success["stdout"] == "ok"
    assert failure["ok"] is False
    assert failure["rc"] == 7
