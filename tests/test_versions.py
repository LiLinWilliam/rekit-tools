import subprocess
import sys
from pathlib import Path

import pytest
from conftest import load_tool

from rekit_tools import __version__

ROOT = Path(__file__).parents[1]
version_helpers = load_tool("tools/_version.py", "version_helpers")
VERSION_TOOLS = [
    "tools/doctor/doctor.py",
    "tools/environment-snapshot/02-snapshot-environments.py",
    "tools/launcher/extract_xz.py",
    "tools/render-entropy/render_entropy.py",
    "tools/restore/restore.py",
    "tools/verify/verify.py",
    "tools/verify-portability/verify-portability.py",
    "tools/verify-review-fixes/verify-review-fixes.py",
    "tools/retry-watchdog/probe_models.py",
    "tools/retry-watchdog/show_progress.py",
    "tools/retry-watchdog/astra_forever.py",
    "tools/retry-watchdog/multi_retry.py",
    "tools/retry-watchdog/watchdog.py",
]


@pytest.mark.parametrize("relative_path", VERSION_TOOLS)
def test_version_flag_is_safe_and_consistent(relative_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / relative_path), "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith(f" {__version__}"), result.stdout


def test_version_text_uses_the_single_source_version():
    assert version_helpers.version_text("demo") == f"demo {__version__}"


@pytest.mark.parametrize("argv, expected", [([], False), (["--help"], False), (["--version"], True)])
def test_version_only_accepts_only_the_version_flag(argv, expected):
    assert version_helpers.version_only(argv) is expected


def test_print_version_writes_one_line(capsys):
    version_helpers.print_version("demo")
    assert capsys.readouterr().out == f"demo {__version__}\n"
