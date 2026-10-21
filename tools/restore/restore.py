"""Restore exact installed versions offline, with rollback on failure."""
import argparse
import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
from _environment import ROOT, VENVS, create_directories, environment, python_runtime

IMPORTS = {
    "buildtools": "import cmake,mesonbuild; print('buildtools ok')",
    "misc": "import lief,pefile,elftools; print('misc ok')",
    "angr": "import angr,unicorn; print('angr ok')",
    "capa": "import capa.main; print('capa ok')",
    "qiling": "import qiling,unicorn,keystone,capstone; print('qiling ok')",
    "floss": "import floss.main,binary2strings,platformdirs; print('floss ok')",
    "render": "import PIL; assert PIL.__version__ == '10.4.0'; print('render Pillow', PIL.__version__)",
    "frida": "import frida,objection,frida_tools; print('frida', frida.__version__)",
}


def contained(path):
    resolved = path.resolve()
    if resolved == ROOT or not resolved.is_relative_to(ROOT):
        raise ValueError("Refusing filesystem operation outside rekit: " + str(path))
    if path.is_junction() or path.is_symlink():
        raise ValueError("Refusing to replace linked environment: " + str(path))
    return path


def run(argv, env, log):
    result = subprocess.run([str(a) for a in argv], cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    log.write(result.stdout)
    log.flush()
    if result.returncode:
        raise RuntimeError(f"command exited {result.returncode}: {argv[0]}\n{result.stdout[-4000:]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", choices=VENVS, action="append")
    parser.add_argument("--online", action="store_true", help="explicitly permit index access; default is offline")
    parser.add_argument("--check-only", action="store_true", help="verify fresh temporary venvs without replacing installed ones")
    args = parser.parse_args()
    env = environment()
    create_directories(env)
    for key in tuple(env):
        if key.startswith(("PIP_", "UV_INDEX", "UV_DEFAULT_INDEX", "UV_EXTRA_INDEX")) and key != "PIP_CACHE_DIR":
            env.pop(key, None)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    backup = ROOT / "backups" / ("restore-" + stamp)
    scratch = ROOT / "temp" / ("restore-check-" + stamp)
    changed = []
    log_path = ROOT / "logs" / ("restore-" + stamp + ".log")
    try:
        with log_path.open("w", encoding="utf-8") as log:
            for name in args.venv or VENVS:
                target = scratch / name if args.check_only else ROOT / "venv" / name
                pins = ROOT / "requirements" / (name + ".txt")
                if not pins.is_file():
                    raise FileNotFoundError(pins)
                if not args.check_only:
                    old = backup / name
                    contained(target)
                    contained(old)
                    if target.exists():
                        backup.mkdir(parents=True, exist_ok=True)
                        target.rename(old)
                    changed.append((target, old))
                target.parent.mkdir(parents=True, exist_ok=True)
                print("Restoring " + name + (" (offline)" if not args.online else " (online)"), flush=True)
                run([python_runtime() / "python.exe", "-I", "-B", "-m", "venv", "--without-pip", target], env, log)
                py = target / "Scripts/python.exe"
                install = [env["REKIT_UV"], "pip", "install", "--python", py, "--no-deps", "-r", pins]
                if not args.online:
                    install.append("--offline")
                run(install, env, log)
                for dll in (ROOT / "toolchain/vcredist").glob("*.dll"):
                    shutil.copy2(dll, target / "Scripts" / dll.name)
                run([env["REKIT_UV"], "pip", "check", "--python", py], env, log)
                run([py, "-I", "-B", "-c", IMPORTS[name]], env, log)
        print("Restore verified. Log: " + str(log_path))
        if any(old.exists() for _, old in changed):
            print("Previous environments retained at: " + str(backup))
        return 0
    except Exception as exc:
        for target, old in reversed(changed):
            if target.exists():
                shutil.rmtree(contained(target))
            if old.exists():
                old.rename(target)
        print("Restore failed; original environments restored: " + str(exc), file=sys.stderr)
        return 1
    finally:
        if scratch.exists():
            shutil.rmtree(contained(scratch))


if __name__ == "__main__":
    sys.exit(main())
