"""Extract .xz archives in place; bsdtar on Windows does not decode xz reliably."""
import lzma
import pathlib
import sys
from pathlib import Path

_VERSION_ROOT = Path(__file__).resolve().parents[1]
if str(_VERSION_ROOT) not in sys.path:
    sys.path.insert(0, str(_VERSION_ROOT))
from _version import print_version, version_only  # noqa: E402


def main():
    if version_only():
        print_version("launcher/extract_xz")
        return 0
    target = pathlib.Path(sys.argv[1])
    failed = 0
    for archive in sorted(target.glob("*.xz")):
        out = archive.with_suffix("")
        if out.is_file() and out.stat().st_size:
            print("keep  " + out.name)
            continue
        with lzma.open(archive, "rb") as src, open(out, "wb") as dst:
            while True:
                block = src.read(1 << 20)
                if not block:
                    break
                dst.write(block)
        print("wrote " + out.name + " " + str(out.stat().st_size))
    return failed


if __name__ == "__main__":
    sys.exit(main())
