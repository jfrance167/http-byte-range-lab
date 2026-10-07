"""Repeat reviewed local checks into a fresh evidence directory.

Usage: python tools/verify.py --output NEW_DIRECTORY. Requires installed Bandit.
Temporarily mutates only own model.py; always restores exact original bytes.
No input-derived commands, network, package installation or project publication.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
# Commands below are fixed reviewed local Python checks; never shell/case content.
import subprocess  # nosec B404
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(arguments, output, name, expected=0):
    result = subprocess.run([sys.executable]+arguments,cwd=ROOT,capture_output=True,
                            timeout=60,check=False)  # nosec B603
    (output/(name+".stdout.txt")).write_bytes(result.stdout)
    (output/(name+".stderr.txt")).write_bytes(result.stderr)
    passed = result.returncode == expected
    if expected == 1:
        # A crash/import error is not evidence that the fixture caught this regression.
        log = result.stderr.decode("utf-8", "replace")
        passed = passed and bool(re.search(r"FAILED \(failures=[1-9][0-9]*\)", log)) and "FAIL: test_frozen_labels" in log
    return {"name":name,"arguments":arguments,"exit_code":result.returncode,
            "expected_exit":expected,"passed":passed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT) or output == ROOT:
        parser.error("evidence output must be a new directory inside this project")
    output.mkdir(parents=True,exist_ok=False)
    checks = []
    checks.append(run(["-m","unittest","discover","-s","tests","-v"],output,"tests-normal"))
    checks.append(run(["-O","-m","unittest","discover","-s","tests","-v"],output,"tests-optimized"))
    checks.append(run(["-m","compileall","-q","rangelab","tests","tools"],output,"compile"))
    checks.append(run(["-m","bandit","-r","rangelab","tests","tools","-f","json"],output,"bandit"))
    model = ROOT/"rangelab/model.py"
    original = model.read_bytes()
    mutations = [
        ("omit-inclusive-count", b'last - first + 1', b'last - first'),
        ("omit-suffix-clamp", b'max(0, length - suffix)', b'length - suffix'),
        ("wrong-first-boundary", b'if first >= length:', b'if first > length:'),
        ("ignore-baseline-gate", b'if baseline != 200:', b'if False and baseline != 200:')]
    try:
        for name, before, after in mutations:
            if original.count(before) != 1:
                raise RuntimeError("mutation target changed")
            model.write_bytes(original.replace(before,after))
            checks.append(run(["-B","-m","unittest","discover","-s","tests","-v"],output,name,1))
            model.write_bytes(original)
    finally:
        model.write_bytes(original)
    restored = model.read_bytes() == original
    checks.append(run(["-B","-m","unittest","discover","-s","tests","-v"],output,"tests-restored"))
    # Deleting no files: fresh output artifacts and all earlier evidence are retained.
    for format_name in ("json","markdown"):
        target = output/("demo."+("json" if format_name=="json" else "md"))
        checks.append(run(["-m","rangelab","fixtures/cases.json","--format",format_name,
                           "--output",str(target)],output,"demo-"+format_name,2))
    files = [*ROOT.joinpath("rangelab").glob("*.py"), ROOT/"tests/test_lab.py",
             ROOT/"tools/verify.py", ROOT/"fixtures/cases.json",ROOT/"fixtures/expected.json",ROOT/"CONTRACT.md"]
    receipt = {"runtime":sys.version,"checks":checks,"model_restored":restored,
               "hashes":{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in files},"passed":restored and all(item["passed"] for item in checks)}
    (output/"results.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"passed":receipt["passed"],"checks":len(checks),"restored":restored}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

