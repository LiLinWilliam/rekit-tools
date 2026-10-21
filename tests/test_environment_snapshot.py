import pytest

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


def test_parse_freeze_output_records_editable_source_revision(tmp_path):
    root = tmp_path / "rekit"
    source = root / "src" / "demo"
    source.mkdir(parents=True)

    pins, sources = snapshot.parse_freeze_output(
        "\n-e " + source.as_uri() + "\nPillow==12.2.0\n",
        root,
        revision_resolver=lambda path: "deadbeef",
    )

    assert pins == ["-e ./src/demo", "Pillow==12.2.0"]
    assert sources == [{"path": "src/demo", "commit": "deadbeef"}]


def test_parse_freeze_output_rejects_editable_source_outside_root(tmp_path):
    root = tmp_path / "rekit"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    with pytest.raises(ValueError):
        snapshot.parse_freeze_output("-e " + outside.as_uri(), root,
                                     revision_resolver=lambda path: "ignored")


def test_parse_freeze_output_accepts_multiple_pinned_lines(tmp_path):
    pins, sources = snapshot.parse_freeze_output(
        "Pillow==12.2.0\npytest==9.1.1\n", tmp_path
    )
    assert pins == ["Pillow==12.2.0", "pytest==9.1.1"]
    assert sources == []
