from conftest import load_tool


watchdog = load_tool("tools/retry-watchdog/watchdog.py", "watchdog")


def test_fmt_ts_returns_placeholder_for_invalid_values():
    assert watchdog.fmt_ts("not-a-timestamp") == "-"


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

