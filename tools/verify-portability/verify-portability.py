"""Verify a relocated bootstrap, an offline Python restore, and portable rizin."""
import datetime
import json
import os
import shutil
import struct
import subprocess
import sys
import uuid
from pathlib import Path

_VERSION_ROOT = Path(__file__).resolve().parents[1]
if str(_VERSION_ROOT) not in sys.path:
    sys.path.insert(0, str(_VERSION_ROOT))
from _version import print_version, version_only  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    if version_only():
        print_version("verify-portability")
        return 0
    target = ROOT / "temp" / ("portable path-" + uuid.uuid4().hex[:8])
    target.mkdir(parents=True)
    env = dict(os.environ)
    env["PATH"] = str(Path(os.environ["SYSTEMROOT"]) / "System32")
    env["JAVA_HOME"] = "Z:/not-installed"
    env["PYTHONPATH"] = "Z:/not-installed"
    for key in tuple(env):
        if key.startswith("REKIT_"):
            env.pop(key)
    checks = []
    log_dir = ROOT / "logs"

    def run(name, argv, valid):
        result = subprocess.run([str(x) for x in argv], cwd=target, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=180)
        (log_dir / ("portability-" + name + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
        (log_dir / ("portability-" + name + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
        ok = result.returncode == 0 and valid(result.stdout)
        checks.append(dict(name=name, ok=ok, exit_code=result.returncode))
        print(("OK   " if ok else "FAIL ") + name, flush=True)
        if not ok:
            raise RuntimeError(name + " failed")

    try:
        print("Copying private runtime and cache into a directory containing spaces...", flush=True)
        paths = ["bin", "scripts", "requirements", "toolchain/uv", "toolchain/vcredist", "toolchain/jdk",
                 "toolchain/python/cpython-3.12.14-windows-x86_64-none", "cache/uv", "pefile", "pyelftools",
                 "rizin/rizin-install", "build/cargo-target/release/binwalk.exe"]
        for relative in paths:
            if (ROOT / relative).is_file():
                (target / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target / relative)
            else:
                shutil.copytree(ROOT / relative, target / relative,
                                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.obj"))
        run("offline-restore", [target / "bin/repair.exe", "--venv", "misc", "--venv", "render"], lambda out: "Restore verified" in out)
        for file in (target / "logs").glob("restore-*.log"):
            shutil.copy2(file, log_dir / "portability-restore-detail.log")
        code = "import sys,json,lief,pefile,elftools;print(json.dumps(dict(python=sys.executable,pefile=pefile.__file__,elftools=elftools.__file__,lief=lief.__file__)))"
        def local_imports(out):
            values = json.loads(out)
            return all(Path(value).resolve().is_relative_to(target.resolve()) for value in values.values())
        run("relocated-python", [target / "bin/python.exe", "misc", "-I", "-c", code], local_imports)
        render_code = "import sys,json,PIL;print(json.dumps(dict(python=sys.executable,pillow=PIL.__file__)))"
        run("relocated-render", [target / "bin/python.exe", "render", "-I", "-c", render_code], local_imports)
        prefix = "RZ_PREFIX=" + str(target / "rizin/rizin-install")
        run("relocated-rizin", [target / "bin/rizin.exe", "-H"], lambda out: prefix in out and "RZ_IS_PORTABLE=1" in out)
        output = target / "logs/relocated-entropy.png"
        def png_without_qiling(out):
            data = output.read_bytes()
            return (not (target / "venv/qiling").exists() and not (target / "qiling").exists()
                    and data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (2048, 1024))
        run("relocated-bare-entropy", [target / "build/cargo-target/release/binwalk.exe", "-E", "--png", output,
                                      target / "bin/rekit.exe"], png_without_qiling)
    except Exception as exc:
        checks.append(dict(name="completion", ok=False, error=str(exc)))
        print(str(exc), file=sys.stderr)
    finally:
        ok = bool(checks) and all(row["ok"] for row in checks)
        report = dict(time=datetime.datetime.now().astimezone().isoformat(), ok=ok, checks=checks,
                      copied_root=str(target), system_developer_path_removed=True,
                      scope="Relocated native bootstrap, offline misc/render restore/imports, portable rizin, and raw binwalk PNG without qiling; not a full clone of every tool.")
        (log_dir / "portability.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        resolved = target.resolve()
        if resolved != ROOT and resolved.is_relative_to((ROOT / "temp").resolve()) and not target.is_junction():
            shutil.rmtree(target)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
