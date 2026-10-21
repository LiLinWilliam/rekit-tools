"""Read the package version without importing a runtime tool or its dependencies."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def _read_version() -> str:
    source = Path(__file__).resolve().parents[1] / "src" / "rekit_tools" / "__init__.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if any(isinstance(target, ast.Name) and target.id == "__version__" for target in targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, str):
                return value
    raise RuntimeError(f"__version__ is missing from {source}")


VERSION = _read_version()


def version_text(program: str) -> str:
    return f"{program} {VERSION}"


def add_version(parser) -> None:
    parser.add_argument("--version", action="version", version=version_text(parser.prog))


def version_only(argv=None) -> bool:
    values = list(sys.argv[1:] if argv is None else argv)
    if values != ["--version"]:
        return False
    return True


def print_version(program: str) -> None:
    print(version_text(program))
