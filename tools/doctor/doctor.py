"""Health checks with JSON evidence and a nonzero failure exit code."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
from _environment import ROOT, VENVS, create_directories, environment, python_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    env = environment()
    create_directories(env)
    checks = []

    def check(name, argv, expected=None, codes=(0,)):
        start = time.monotonic()
        try:
            result = subprocess.run([str(a) for a in argv], env=env, cwd=ROOT, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=90)
            output, error = result.stdout.strip(), result.stderr.strip()
            ok = result.returncode in codes and (expected is None or expected in output + error)
            row = dict(name=name, ok=ok, exit_code=result.returncode, stdout=output, stderr=error)
        except (OSError, subprocess.TimeoutExpired) as exc:
            row = dict(name=name, ok=False, exit_code=None, stdout="", stderr=str(exc))
        row["seconds"] = round(time.monotonic() - start, 3)
        checks.append(row)
        if not args.json:
            print(("OK   " if row["ok"] else "FAIL ") + name, flush=True)

    for tool, flag, expected in (("binwalk", "--version", "3.1.1"), ("rizin", "-v", "rizin"),
                                  ("jadx", "--version", "dev"), ("capa", "--version", "9.4.0"),
                                  ("floss", "--version", "3.1.1"), ("diec-db", os.environ.get("REKIT_SAMPLE_APK", "<authorized-sample-apk>"), "APK"),
                                  ("uv", "--version", "uv"), ("frida", "--version", "17.")):
        check(tool, [ROOT / "bin" / (tool + ".exe"), flag], expected)
    modules = {"buildtools": "import cmake,mesonbuild", "misc": "import lief,pefile,elftools",
               "angr": "import angr,unicorn", "capa": "import capa.main", "qiling": "import qiling,unicorn,capstone,keystone",
               "floss": "import floss.main,binary2strings,platformdirs",
               "render": "import PIL; assert PIL.__version__ == '10.4.0'",
               "frida": "import frida,objection,frida_tools;print('import ok')"}
    for name in VENVS:
        py = ROOT / "venv" / name / "Scripts/python.exe"
        check("import:" + name, [py, "-I", "-B", "-c", modules[name] + ";print('import ok')"], "import ok")
        check("dependencies:" + name, [env["REKIT_UV"], "pip", "check", "--python", py])
    check("java", [Path(env["JAVA_HOME"]) / "bin/java.exe", "-version"], "25.")
    check("ghidra-headless", [ROOT / "bin/ghidra-headless.exe"], "Usage", codes=(0, 1))
    sample_args = ["", "space here", 'quote"inside', "trailing\\", "中文 & % !"]
    probe = "import json,sys;print(json.dumps(sys.argv[1:],ensure_ascii=False))"
    check("native-argv", [ROOT / "bin/python.exe", "misc", "-c", probe, *sample_args], json.dumps(sample_args, ensure_ascii=False))
    for label, path in (("capa-rules", ROOT / "capa/rules"), ("qiling-linux", ROOT / "qiling/examples/rootfs/x8664_linux"),
                        ("qiling-windows", ROOT / "qiling/examples/rootfs/x8664_windows"),
                        ("local-uv", ROOT / "toolchain/uv/uv.exe"), ("local-python", python_runtime() / "python.exe")):
        checks.append(dict(name=label, ok=path.exists(), path=str(path)))
    frida_servers = sorted((ROOT / "tooling/frida").glob("frida-server-*"))
    checks.append(dict(name="frida-server", ok=len(frida_servers) >= 2,
                       path=", ".join(p.name for p in frida_servers)))
    ok = all(c["ok"] for c in checks)
    report = dict(time=datetime.datetime.now().astimezone().isoformat(), root=str(ROOT), ok=ok, checks=checks,
                  optional_build_dependency=dict(name="MSVC + Windows SDK",
                  available=(ROOT / "toolchain/vs/VC/Auxiliary/Build/vcvars64.bat").is_file()))
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if not args.no_write:
        (ROOT / "logs/doctor.json").write_text(text + "\n", encoding="utf-8")
        lines = [report["time"], "PASS" if ok else "FAIL"]
        for row in checks:
            lines.append(("OK   " if row["ok"] else "FAIL ") + row["name"])
            if not row["ok"]:
                lines.append(row.get("stdout", "") + "\n" + row.get("stderr", ""))
        (ROOT / "logs/doctor.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if args.json:
        print(text)
    else:
        print(f"{'PASS' if ok else 'FAIL'}: {sum(c['ok'] for c in checks)}/{len(checks)} checks; logs/doctor.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
