"""Functional acceptance: real tools, process boundaries, JSON and protected paths."""
import datetime
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fingerprint(path):
    if not path.exists():
        return "absent"
    rows = []
    for current, dirs, files in os.walk(path, followlinks=False):
        dirs.sort()
        for name in sorted(files):
            file = Path(current) / name
            try:
                stat = file.stat()
                rows.append((str(file.relative_to(path)), stat.st_size, stat.st_mtime_ns))
            except OSError:
                rows.append((str(file.relative_to(path)), "unreadable"))
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def main():
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    original_profile = Path(os.environ["USERPROFILE"])
    original_local = Path(os.environ["LOCALAPPDATA"])
    protected = [Path("<protected-root>/analysis/ghidra-projects"),
                 Path("<protected-root>/cache/ghidra-settings"), Path("<protected-root>/outputs")]
    protected += [original_profile / p for p in (".cargo", ".rustup", ".gradle")]
    protected += [original_local / p for p in ("flare/capa", "floss", "skylot")]
    before = {str(p): fingerprint(p) for p in protected}
    # Simulate an ordinary Windows machine with no developer tools on PATH.
    clean = dict(os.environ)
    clean["PATH"] = str(Path(os.environ["SYSTEMROOT"]) / "System32")
    clean["JAVA_HOME"] = "Z:/not-installed"
    clean["PYTHONPATH"] = "Z:/not-installed"
    results = []

    def run(name, tool, args, validator=lambda out: bool(out.strip()), expected_exit=0, stdin=None, timeout=90):
        start = time.monotonic()
        argv = [str(ROOT / "bin" / (tool + ".exe")), *map(str, args)]
        proc = subprocess.Popen(argv, cwd=ROOT, env=clean, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        try:
            stdout, stderr = proc.communicate(stdin, timeout=timeout)
            ok = proc.returncode == expected_exit and validator(stdout)
            error = None
        except subprocess.TimeoutExpired:
            subprocess.run([str(Path(os.environ["SYSTEMROOT"]) / "System32/taskkill.exe"), "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True)
            stdout, stderr = proc.communicate()
            ok, error = False, "timeout"
        except Exception as exc:
            stdout, stderr = "", str(exc)
            ok, error = False, str(exc)
        (logs / ("verify-" + name + ".stdout.txt")).write_text(stdout, encoding="utf-8")
        (logs / ("verify-" + name + ".stderr.txt")).write_text(stderr, encoding="utf-8")
        results.append(dict(name=name, ok=ok, exit_code=proc.returncode, error=error, seconds=round(time.monotonic()-start, 3)))
        print(("OK   " if ok else "FAIL ") + name, flush=True)

    values = ["", "a b", 'a"b', "last\\", "中文", "& | % ! $ ;"]
    code = "import json,sys; print(json.dumps(sys.argv[1:],ensure_ascii=False))"
    run("argv", "python", ["misc", "-c", code, *values], lambda out: json.loads(out) == values)
    run("stdin", "python", ["misc", "-"], lambda out: out.strip() == "stdin-ok", stdin='print("stdin-ok")\n')
    run("exit-status", "python", ["misc", "-c", "raise SystemExit(42)"], lambda out: out == "", expected_exit=42)
    run("bad-tool", "rekit", ["nonexistent-tool"], lambda out: out == "", expected_exit=3)
    sample = ROOT / "bin/rekit.exe"
    run("rizin-json", "rizin", ["-q", "-c", "iIj", "-c", "q", sample], lambda out: json.loads(out)["bits"] == 64)
    run("die-cli", "diec-db", [Path(os.environ.get("REKIT_SAMPLE_APK", "<authorized-sample-apk>"))], lambda out: "APK" in out)
    run("capa-json", "capa", ["-q", "--json", sample], lambda out: "rules" in json.loads(out), timeout=120)
    run("floss-json", "floss", ["--json", "--string-type", "static", "--", sample], lambda out: "strings" in json.loads(out), timeout=120)
    run("jadx", "jadx", ["--version"], lambda out: "dev" in out)
    project = "smoke-" + uuid.uuid4().hex[:8]
    run("ghidra-import", "ghidra-headless", [ROOT / "projects", project, "-import", sample, "-noanalysis",
                                             "-deleteProject", "-max-cpu", "2", "-log", logs / "ghidra-smoke.log",
                                             "-scriptlog", logs / "ghidra-smoke-script.log"],
        lambda out: "IMPORTING" in out or "Import succeeded" in out or "REPORT: Import succeeded" in out, timeout=120)
    if (ROOT / "scripts/render_entropy.py").is_file():
        png = logs / "entropy.png"
        def valid_png(out):
            data = png.read_bytes()
            return data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (2048, 1024)
        run("entropy-png", "binwalk", ["-E", "--png", png, sample], valid_png, timeout=60)
    after = {str(p): fingerprint(p) for p in protected}
    results.append(dict(name="protected-directories", ok=before == after))
    report = dict(time=datetime.datetime.now().astimezone().isoformat(), ok=all(row["ok"] for row in results),
                  checks=results, developer_path_removed=True, protected_before=before, protected_after=after)
    (logs / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print("PASS" if report["ok"] else "FAIL", flush=True)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
