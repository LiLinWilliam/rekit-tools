from conftest import load_tool

entropy = load_tool("tools/render-entropy/render_entropy.py", "render_entropy")


def test_clamp_entropy_bounds_values():
    assert entropy.clamp_entropy(-1) == 0.0
    assert entropy.clamp_entropy(3.5) == 3.5
    assert entropy.clamp_entropy(99) == 8.0


def test_block_points_clamps_and_preserves_block_edges():
    points = entropy.block_points([{"start": 0, "end": 10, "entropy": 9}], 10,
                                  left=0, right=100, top=0, bottom=80)
    assert points == [(0.0, 0.0), (100.0, 0.0)]


def test_block_points_returns_no_points_for_empty_input():
    assert entropy.block_points([], 1) == []


def test_render_writes_expected_png(tmp_path):
    output = tmp_path / "entropy.data"
    assert entropy.render({"blocks": [{"start": 0, "end": 8, "entropy": 4}]}, output) == 0
    png = output.with_suffix(".png")
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_writes_a_valid_png_for_empty_blocks(tmp_path):
    output = tmp_path / "empty.json"
    assert entropy.render({"blocks": []}, output) == 0
    assert output.with_suffix(".png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
