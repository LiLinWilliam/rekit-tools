from conftest import load_tool


snapshot = load_tool(
    "tools/environment-snapshot/02-snapshot-environments.py", "environment_snapshot"
)


def test_parse_freeze_output_keeps_pinned_requirements(tmp_path):
    pins, sources = snapshot.parse_freeze_output("Pillow==12.2.0\npytest==8.0.0\n", tmp_path)
    assert pins == ["Pillow==12.2.0", "pytest==8.0.0"]
    assert sources == []


def test_parse_freeze_output_rejects_unpinned_requirement(tmp_path):
    try:
        snapshot.parse_freeze_output("requests\n", tmp_path)
    except ValueError as exc:
        assert str(exc) == "Unpinned requirement: requests"
    else:
        raise AssertionError("unpinned requirements must be rejected")

