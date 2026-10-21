"""Record package versions and local source revisions without upgrades."""
import datetime
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def parse_freeze_output(stdout, root, revision_resolver=None):
    """Parse ``pip freeze`` output into pinned requirements and source metadata."""
    pins, sources = [], []
    root = Path(root).resolve()

    def resolve_revision(path):
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    for line in stdout.splitlines():
        if line.startswith("-e file://"):
            parsed = urlparse(line[3:])
            path = Path(unquote(parsed.path).lstrip("/"))
            relative = path.resolve().relative_to(root).as_posix()
            pins.append("-e ./" + relative)
            revision = (revision_resolver or resolve_revision)(path)
            sources.append({"path": relative, "commit": revision})
        elif line.strip():
            if "==" not in line:
                raise ValueError("Unpinned requirement: " + line)
            pins.append(line)
    return pins, sources


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
    from _environment import ROOT, VENVS, environment

    env = environment()
    target = ROOT / "requirements"
    target.mkdir(exist_ok=True)
    manifest = {"created": datetime.datetime.now().astimezone().isoformat(), "environments": {}}
    for name in VENVS:
        py = ROOT / "venv" / name / "Scripts/python.exe"
        result = subprocess.run([env["REKIT_UV"], "pip", "freeze", "--python", str(py)],
                                capture_output=True, text=True, encoding="utf-8", check=True, env=env, cwd=ROOT)
        pins, sources = parse_freeze_output(result.stdout, ROOT)
        (target / (name + ".txt")).write_text(
            "# Installed snapshot; resolve relative paths from the rekit root.\n" +
            "\n".join(pins) + "\n", encoding="utf-8")
        manifest["environments"][name] = {"requirements": len(pins), "editable_sources": sources}
        print(name + ": " + str(len(pins)) + " pinned entries")
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
