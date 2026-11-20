"""Reproduce the selected CPython startup observations with reviewed source."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent


def run(source, cpython, sqlite_include, out):
    receipt = json.loads((HERE / "RECEIPT.json").read_bytes())
    for name, digest in receipt["native_source_sha256"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Wrong authenticated native input: " + name)
    if subprocess.check_output([cpython / "python", "-V"], text=True).strip() != "Python 3.11.7":
        raise ValueError("CPython 3.11.7 host build required")
    out.mkdir()
    invoker = (source / "xbmc/interfaces/python/PythonInvoker.cpp").read_text()
    begin = invoker.index("      m_mainThreadState = PyThreadState_New(owner->interp);")
    last = "      newInterp = true;"
    end = invoker.index(last, begin) + len(last)
    adapter = "      PyThreadState* owner = CServiceBroker::GetXBPython().GetMainThreadState();\n"
    compiled = out / "startup-harness.cpp"
    template = (HERE / "startup-harness.cpp.in").read_text()
    compiled.write_text(template.replace("@@CALL_SITE@@", adapter + invoker[begin:end]))
    binary = out / "startup-harness"
    subprocess.run(["g++", "-std=c++20", "-O1", "-g", "-no-pie", "-fno-omit-frame-pointer",
                    "-Wno-deprecated-declarations", "-Wl,--wrap=pthread_mutex_lock",
                    "-pthread", "-rdynamic", "-I", cpython / "Include", "-I", cpython,
                    "-I", source / "xbmc", "-I", sqlite_include,
                    compiled, cpython / "libpython3.11.a", "-lm", "-ldl", "-lexpat",
                    "-l:libcrypto.so.3", "-l:libsqlite3.so.0", "-o", binary], check=True)
    for mode in ("stock", "hooked", "ledger_hold"):
        result = subprocess.run([binary, mode, cpython / "Lib"], check=True, text=True,
                                capture_output=True, timeout=35)
        proof = json.loads(result.stdout)
        result_path = out / (mode + ".json")
        result_path.write_text(json.dumps(proof, indent=2) + "\n")
        if mode == "ledger_hold":
            addresses = re.findall(r"(?m)^fixture-mutex-stack (0x[0-9a-f]+)$", result.stderr)
            stack = subprocess.check_output(
                ["addr2line", "-f", "-i", "-C", "-e", binary, *addresses], text=True)
            for name in ("BeginProtectedOperation", "RawInitialize", "create_stdio", "Py_NewInterpreter"):
                if name not in stack:
                    raise ValueError("Missing expected host lock stack frame: " + name)
            (out / "ledger-stack.txt").write_text(stack)
        print(json.dumps(proof), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("source", "cpython", "sqlite-include", "out"):
        parser.add_argument("--" + option, type=Path, required=True)
    run(**{key: val.resolve() for key, val in vars(parser.parse_args()).items()})
