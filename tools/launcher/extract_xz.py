"""Extract .xz archives in place; bsdtar on Windows does not decode xz reliably."""
import lzma
import pathlib
import sys


def main():
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
