"""Public command-line entry point for the rekit-tools package."""

from __future__ import annotations

import argparse

from . import __version__

TOOLS = (
    "doctor",
    "environment-snapshot",
    "launcher",
    "migrate-after-move",
    "render-entropy",
    "restore",
    "retry-watchdog",
    "toolchain-installers",
    "venv-install-all",
    "verify",
    "verify-portability",
    "verify-review-fixes",
)


def main(argv: list[str] | None = None) -> int:
    """Print package metadata and the names of the repository tools."""
    parser = argparse.ArgumentParser(
        prog="rekit-tools",
        description="Auditable Windows helpers for a local rekit runtime",
    )
    parser.add_argument("--version", action="version", version=f"rekit-tools {__version__}")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("list",),
        help="list the repository tools (the default)",
    )
    args = parser.parse_args(argv)
    if args.command in (None, "list"):
        print(f"rekit-tools {__version__}")
        for name in TOOLS:
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
