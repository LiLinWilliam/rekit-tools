"""Run the examples that are safe to exercise from a clean checkout.

This script creates only temporary synthetic data. It never reads a real sample,
Codex session database, device, or rekit runtime.
"""

from __future__ import annotations

import json
import lzma
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from rekit_tools import __version__

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def check_cli() -> None:
    result = run([sys.executable, "-m", "rekit_tools.cli", "list"])
    lines = result.stdout.splitlines()
    assert lines[0] == f"rekit-tools {__version__}", lines
    assert "render-entropy" in lines and "verify" in lines, lines
    print("CLI: version and tool list passed")


def check_entropy_renderer(temp: Path) -> None:
    output = temp / "entropy.png"
    payload = json.dumps(
        {"blocks": [{"start": 0, "end": 512, "entropy": 1.2}, {"start": 512, "end": 1024, "entropy": 7.6}]}
    )
    run([sys.executable, "tools/render-entropy/render_entropy.py", str(output)], input_text=payload)
    assert output.exists() and output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", output.read_bytes()[16:24])
    assert (width, height) == (2048, 1024)
    print(f"render-entropy: wrote {output.name} ({width}x{height} PNG)")


def check_xz_extractor(temp: Path) -> None:
    archive = temp / "synthetic.bin.xz"
    expected = b"rekit-tools example\n"
    archive.write_bytes(lzma.compress(expected))
    result = run([sys.executable, "tools/launcher/extract_xz.py", str(temp)])
    extracted = temp / "synthetic.bin"
    assert extracted.read_bytes() == expected
    assert "wrote synthetic.bin" in result.stdout
    print("launcher/extract_xz: extracted synthetic.bin")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rekit-tools-example-") as directory:
        temp = Path(directory)
        check_cli()
        check_entropy_renderer(temp)
        check_xz_extractor(temp)
    print("safe examples passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
