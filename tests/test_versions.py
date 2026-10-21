import subprocess
import sys
from pathlib import Path

import pytest

from rekit_tools import __version__

ROOT = Path(__file__).parents[1]
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
