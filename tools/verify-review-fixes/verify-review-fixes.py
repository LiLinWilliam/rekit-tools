"""Regression checks for renderer independence, raw invocation and JVM configuration."""
import datetime
import json
import os
import re
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
        print_version("verify-review-fixes")
        return 0
    scratch = ROOT / "temp" / ("review-check-" + uuid.uuid4().hex[:8])
    scratch.mkdir(parents=True)
    logs = ROOT / "logs"
    results = []
    clean = {k: v for k, v in os.environ.items() if not k.startswith("REKIT_")}
    clean["PATH"] = str(Path(os.environ["SYSTEMROOT"]) / "System32")
    clean["VIRTUAL_ENV"] = str(scratch / "nonexistent-qiling")
    raw = ROOT / "build/cargo-target/release/binwalk.exe"
    sample = ROOT / "bin/rekit.exe"

    def run(name, argv, valid, env=None, timeout=90):
        proc = subprocess.Popen([str(v) for v in argv], cwd=scratch, env=env or clean,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace")
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            ok = valid(proc.returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            subprocess.run([str(Path(os.environ["SYSTEMROOT"]) / "System32/taskkill.exe"),
                            "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            stdout, stderr = proc.communicate()
            ok = False
        (logs / ("review-" + name + ".stdout.txt")).write_text(stdout, encoding="utf-8")
        (logs / ("review-" + name + ".stderr.txt")).write_text(stderr, encoding="utf-8")
        results.append(dict(name=name, ok=ok, exit_code=proc.returncode))
        print(("OK   " if ok else "FAIL ") + name, flush=True)
        return stdout

    def png(path):
        data = path.read_bytes()
        return data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (2048, 1024)

    try:
        bare_png, wrapped_png = scratch / "bare.png", scratch / "wrapped.png"
        run("bare-entropy", [raw, "-E", "--png", bare_png, sample], lambda code, out, err: code == 0 and png(bare_png))
        run("wrapped-entropy", [ROOT / "bin/binwalk.exe", "-E", "--png", wrapped_png, sample],
            lambda code, out, err: code == 0 and png(wrapped_png) and wrapped_png.read_bytes() == bare_png.read_bytes())

        no_pillow = scratch / "no-pillow"
        base = next((ROOT / "toolchain/python").glob("cpython-3.12.*-windows-x86_64-none")) / "python.exe"
        subprocess.run([str(base), "-I", "-B", "-m", "venv", "--without-pip", str(no_pillow)], check=True, env=clean)
        broken = dict(clean, REKIT_ENTROPY_PYTHON=str(no_pillow / "Scripts/python.exe"),
                      REKIT_ENTROPY_SCRIPT=str(ROOT / "scripts/render_entropy.py"))
        run("missing-pillow", [raw, "-E", "--png", scratch / "missing.png", sample],
            lambda code, out, err: code != 0 and "Pillow is unavailable" in err and "--venv render" in err
            and "panicked" not in err and not (scratch / "missing.png").exists(), env=broken)

        configured = dict(clean, REKIT_JAVA_XMX="512M")
        run("jadx-heap", [ROOT / "bin/jadx.exe", "--version"], lambda code, out, err: code == 0 and "dev" in out,
            env=configured)
        invalid = dict(clean, REKIT_JAVA_XMX="wrong")
        for tool in ("jadx", "ghidra-headless"):
            run(tool + "-invalid-heap", [ROOT / "bin" / (tool + ".exe"), "--version"],
                lambda code, out, err: code == 3 and "REKIT_JAVA_XMX" in err, env=invalid)
        too_small = dict(clean, REKIT_JAVA_XMX="64M")
        run("too-small-heap", [ROOT / "bin/jadx.exe", "--version"],
            lambda code, out, err: code == 3 and "at least 128M" in err, env=too_small)

        script = scratch / "RekitHeapProbe.java"
        script.write_text('import ghidra.app.script.GhidraScript;\n'
                          'public class RekitHeapProbe extends GhidraScript {\n'
                          '  public void run() { println("REKIT_MAX_HEAP=" + Runtime.getRuntime().maxMemory()); }\n'
                          '}\n', encoding="ascii")
        def heap_is_configured(code, out, err):
            values = re.findall(r"REKIT_MAX_HEAP=(\d+)", out + err)
            return code == 0 and values and abs(int(values[-1]) - 512 * 1024**2) <= 1024**2
        run("ghidra-actual-heap", [ROOT / "bin/ghidra-headless.exe", ROOT / "projects", "heap-" + uuid.uuid4().hex[:8],
                                  "-import", sample, "-noanalysis", "-deleteProject", "-max-cpu", "2",
                                  "-scriptPath", scratch, "-postScript", "RekitHeapProbe.java",
                                  "-log", logs / "review-ghidra.log"], heap_is_configured, env=configured, timeout=120)
        run("cmd-warning", [ROOT / "bin/binwalk.cmd", "--version"],
            lambda code, out, err: code == 0 and "binwalk 3.1.1" in out and "deprecated" in err and "deprecated" not in out)
        catalog = json.loads((ROOT / "bin/tools.json").read_text(encoding="utf-8"))
        results.append(dict(name="native-tool-catalog", ok=all(value.endswith(".exe") and (ROOT / "bin" / value).is_file()
                            for value in catalog["tools"].values()) and catalog["compatibility_cmd"]["for_automation"] is False))
    except Exception as exc:
        results.append(dict(name="completion", ok=False, error=str(exc)))
    finally:
        report = dict(time=datetime.datetime.now().astimezone().isoformat(), ok=all(row["ok"] for row in results), checks=results)
        (logs / "review-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        resolved = scratch.resolve()
        if resolved.is_relative_to((ROOT / "temp").resolve()) and not scratch.is_junction():
            shutil.rmtree(scratch)
    print("PASS" if report["ok"] else "FAIL", flush=True)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
