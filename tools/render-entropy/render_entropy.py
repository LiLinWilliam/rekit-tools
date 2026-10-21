"""Render binwalk entropy blocks using Pillow."""
import json
import sys
from pathlib import Path

_VERSION_ROOT = Path(__file__).resolve().parents[1]
if str(_VERSION_ROOT) not in sys.path:
    sys.path.insert(0, str(_VERSION_ROOT))
from _version import print_version, version_only  # noqa: E402

if version_only():
    print_version("render-entropy")
    raise SystemExit(0)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    repair = Path(__file__).resolve().parent.parent / "bin/repair.exe"
    print(f"rekit entropy PNG: Pillow is unavailable in {sys.executable}: {exc}\n"
          f'Restore the dedicated renderer with: "{repair}" --venv render', file=sys.stderr)
    sys.exit(3)


def clamp_entropy(value) -> float:
    """Convert an entropy value to the graph's supported 0..8 range."""
    return max(0.0, min(8.0, float(value)))


def block_points(blocks, size: int, left=130, right=1978, top=100, bottom=914):
    """Return line points for entropy blocks without drawing or filesystem I/O."""
    points = []
    for block in blocks:
        entropy = clamp_entropy(block["entropy"])
        y = bottom - (bottom - top) * entropy / 8
        points.extend(((left + (right - left) * block["start"] / size, y),
                       (left + (right - left) * block["end"] / size, y)))
    return points


def render(data, output):
    """Render a decoded entropy payload to a PNG path."""
    output = Path(output).with_suffix(".png")
    width, height = 2048, 1024
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=23)
    heading = ImageFont.load_default(size=32)
    left, top, right, bottom = 130, 100, width - 70, height - 110
    blocks = data["blocks"]
    size = blocks[-1]["end"] if blocks else 1
    size = max(1, size)
    draw.text((left, 28), "Entropy Graph", font=heading, fill="#172b4d")
    for value in range(9):
        y = bottom - (bottom - top) * value / 8
        draw.line((left, y, right, y), fill="#e3e9ef", width=1)
        draw.text((left - 40, y - 13), str(value), font=font, fill="#334155")
    for tick in range(6):
        offset = round(size * tick / 5)
        x = left + (right - left) * offset / size
        draw.line((x, top, x, bottom), fill="#eef2f6", width=1)
        draw.text((x, bottom + 15), f"{offset:,}", font=font, fill="#334155", anchor="mt")
    draw.line((left, top, left, bottom, right, bottom), fill="#334155", width=2)
    points = block_points(blocks, size, left, right, top, bottom)
    if len(points) >= 2:
        draw.line(points, fill="#2563eb", width=2)
    draw.text(((left + right) / 2, height - 40), "File Offset (bytes)",
              font=font, fill="#334155", anchor="mm")
    draw.text((left, 70), "Shannon entropy (bits per byte)", font=font, fill="#334155")
    temporary = output.with_name(output.name + ".tmp")
    try:
        image.save(temporary, format="PNG")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return 0


def main():
    if version_only():
        print_version("render-entropy")
        return 0
    data = json.load(sys.stdin.buffer)
    return render(data, sys.argv[1])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"rekit entropy PNG: {exc}", file=sys.stderr)
        sys.exit(2)
