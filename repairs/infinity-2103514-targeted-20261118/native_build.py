"""Build the authorized startup trace overlay from the frozen 2103514 engine."""
import hashlib
import json
import mmap
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = "dea5df6063b49d65099c7958722f2b9f33895600"
REVIEW = ROOT / "native-retained/repairs/infinity-six-repairs-2103502-20261116/lock"
EXACT = ROOT / "baseline514-native"
SCOPE = json.loads((HERE / "SCOPE.json").read_bytes())
BASE = SCOPE["baseline"]
BRANCH = "work/infinity-2103514-targeted-20261118"
TASK = "repairs/infinity-2103514-targeted-20261118"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def retained():
    import importlib.util

    path = REVIEW / "native_build502.py"
    reference = ROOT / "native-retained"
    require(subprocess.check_output(["git", "-C", str(reference), "rev-parse", "HEAD"]).decode().strip() == PRIOR,
            "Wrong frozen producer checkout")
    require(path.read_bytes() == subprocess.check_output([
        "git", "-C", str(reference), "show", PRIOR + ":" + str(path.relative_to(reference))]),
            "Reviewed native producer changed")
    spec = importlib.util.spec_from_file_location("retained_native", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = ROOT / "native502-lock-output"
    return module


def gate(old):
    require(os.environ.get("GITHUB_ACTIONS") == "true" and
            os.environ["GITHUB_REPOSITORY"] == old.REPOSITORY and
            os.environ["GITHUB_REF"] == "refs/heads/" + BRANCH and
            os.environ["GITHUB_EVENT_NAME"] == "push" and
            git("rev-parse", "HEAD").decode().strip() == os.environ["GITHUB_SHA"],
            "Wrong Infinity diagnostic build request")
    paths = [f"{TASK}/CI-NATIVE.json", f"{TASK}/native_build.py",
             f"{TASK}/SCOPE.json", f"{TASK}/startup-boundary.patch",
             ".github/workflows/infinity-514-startup-boundary.yml"]
    require(not git("diff", "--name-only", "HEAD", "--", *paths), "Diagnostic inputs changed")
    request = json.loads((HERE / "CI-NATIVE.json").read_bytes())
    require(request["operation"] == "compile_exact_2103514_startup_diagnostic_arm64" and
            request["baseline"] == BASE and request["selected"] ==
            "Full ARM64 compile/link, startup markers, exact 2103514 exported ABI and dependencies" and
            request["apk_packaging"] is False and request["signing"] is False,
            "Unrecognized native-only authorization or test selection")
    for path in paths[1:]:
        require(sha(ROOT / path) == request["inputs"][path], "Diagnostic input hash: " + path)
    for name in ("SCOPE.json", "startup-boundary.patch"):
        require((HERE / name).read_bytes() == git("show", "301a6cd0:" + TASK + "/" + name),
                "Host-tested startup patch or source pins differ")
    legacy, scope = (json.loads(path.read_bytes()) for path in (old.REQUEST, old.SCOPE))
    require(old.sha(old.REQUEST) == "ef12b91795833060319a25d8dc5feed77a5083bf8b2ac7cadd0a0d48f50448d2" and
            legacy["reviewed_files"] == old.source_hashes(), "Retained historical request or reviewed files changed")
    for name in ("build_native.py", "verify_scope.py", "prepare_ci_tooling.sh"):
        path = old.PRODUCER_PATH + "/" + name
        require(old.blob(PRIOR, path) == old.blob(old.FROZEN, path),
                "Retained reconstruction script changed: " + path)
    return legacy, scope


def preflight(old):
    _, scope = gate(old)
    inputs = [*scope["input_artifacts"], dict(id=14226277189, run_id=43861331996,
              source_commit=PRIOR, name="Infinity502-Lock-Native-ARM64-43861331996-NO-INSTALLER",
              size_in_bytes=203463683,
              digest="sha256:7bfe4e92d9f1253da590a997369fcc79bd9234263ed6d43ba0dc71cad36325f5")]
    for expected in inputs:
        actual = json.loads(subprocess.check_output(["gh", "api",
            f"repos/{old.REPOSITORY}/actions/artifacts/{expected['id']}"]))
        require(actual["expired"] is False and
                all(actual[key] == expected[key] for key in ("id", "name", "size_in_bytes", "digest")) and
                actual["workflow_run"]["id"] == expected["run_id"] and
                actual["workflow_run"]["head_sha"] == expected["source_commit"],
                "Retained input artifact identity differs: " + str(expected["id"]))
    old.save("INPUT-514-AUTHENTICATION.json", inputs)


def baseline_map():
    library = EXACT / "libkodi.so"
    source_map = EXACT / "NATIVE-SOURCE-MAP.json"
    require(sha(library) == BASE["engine_sha256"] and sha(source_map) == BASE["engine_source_map_sha256"],
            "Retained 2103514 original engine or source map differs")
    receipt = json.loads((EXACT / "ARM64.json").read_bytes())
    require(receipt["native_sha256"] == BASE["engine_sha256"] and receipt["source"] == PRIOR and
            receipt["status"] == "PASS_FULL_ARM64_LINK_AND_EXACT502_ABI", "Wrong verified build receipt")
    source = json.loads(source_map.read_bytes())
    require(len(source) == 9418, "Incomplete 2103514 source map")
    return source


def maps():
    before = baseline_map()
    after = dict(before)
    for name, pins in SCOPE["source_allowlist"].items():
        require(before[name] == pins["before_sha256"], "Wrong frozen preimage: " + name)
        after[name] = pins["after_sha256"]
    return before, after


def prepare(old):
    before, after = maps()
    for name in ("verified-inputs", "previous-review", "exact464", "signed80",
                 "baseline500-native", "baseline502-native"):
        require((ROOT / name).is_dir(), "Missing retained input: " + name)
        (old.ROOT / name).symlink_to(ROOT / name, target_is_directory=True)
    old.prepare()
    require(old.hasher().hashes(old.NATIVE) == before,
            "Historical source reconstruction does not match all 2103514 source bytes")
    patch = HERE / "startup-boundary.patch"
    command = ["patch", "--batch", "--forward", "--fuzz=0", "-p1", "-i", str(patch)]
    subprocess.run(command + ["--dry-run"], cwd=old.NATIVE, check=True)
    subprocess.run(command, cwd=old.NATIVE, check=True)
    require(old.hasher().hashes(old.NATIVE) == after, "Unexpected diagnostic source change")
    old.save("NATIVE-SOURCE-MAP.json", after)
    old.save("SOURCE-PRESERVATION-514.json", dict(
        baseline=BASE, unchanged_files=len(after)-len(SCOPE["source_allowlist"]),
        changes=SCOPE["source_allowlist"], build_source=os.environ["GITHUB_SHA"]))


def compile_engine(old):
    _, expected = maps()
    path = old.TOOLS / "repairs/universal-persistence-2103401/build.py"
    require(path.read_bytes() == old.blob(old.RECONSTRUCTION, "repairs/universal-persistence-2103401/build.py"),
            "Verified compiler wrapper differs")
    compiler = old.load(path, "retained_arm64_compiler")
    compiler.OUT = old.OUT
    checked_sources = compiler.checked_sources

    def check_sources(root, pins, allow_generated=False):
        require(root == old.NATIVE and pins == expected, "Wrong diagnostic compiler source map")
        extras = checked_sources(root, pins, allow_generated=True)
        if not allow_generated:
            require(all(name.startswith("tools/depends/") for name in extras), "Unexpected dependency source")
        return extras

    compiler.checked_sources = check_sources
    proof = old.with_tools(compiler.compile_engine)
    engine = old.OUT / "libkodi.so"
    require(proof["complete_native_engine_compiled"] and proof["reviewed_file_count"] == len(expected) and
            sha(engine) == proof["native_sha256"], "Full ARM64 compile/link receipt failed")
    with engine.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as binary:
        for marker in (b"interpreter.returned", b"tracked={} addon={}", b"trace.overflow",
                       b"bytecode.cancelled_before_entry"):
            require(binary.find(marker) >= 0, "Diagnostic marker absent from linked engine")

    tools = Path(os.environ["ANDROID_HOME"]) / "ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin"
    def abi(path):
        def read(option):
            return subprocess.check_output([tools / "llvm-readelf", option, "--wide", path], text=True)
        header = read("-h")
        require(all(value in header for value in ("ELF64", "AArch64", "DYN")), "Invalid ARM64 shared object")
        symbols = {tuple(row[i] for i in (7, 3, 4, 5)) for line in read("--dyn-syms").splitlines()
                   if len(row := line.split()) >= 8 and row[4] in ("GLOBAL", "WEAK")
                   and row[5] in ("DEFAULT", "PROTECTED") and row[6] != "UND"}
        return symbols, set(re.findall(r"Shared library: \[([^\]]+)\]", read("-d"))), tuple(
            re.findall(r"Rev:\s*\d+[^\n]*?Name:\s*(\S+)", read("--version-info")))

    previous, current = abi(EXACT / "libkodi.so"), abi(engine)
    old.save("ABI-514.json", dict(removed=sorted(previous[0] - current[0]),
        added=sorted(current[0] - previous[0]), needed_before=sorted(previous[1]),
        needed_after=sorted(current[1]), versions_before=previous[2], versions_after=current[2]))
    require(previous == current, "Exact 2103514 exported ABI or runtime dependencies differ")
    old.save("ARM64-514.json", dict(status="PASS_FULL_ARM64_LINK_AND_EXACT_2103514_ABI", **proof,
                                  android_execution="NOT_RUN",
                                  apk_packaging=False, signing=False))


if __name__ == "__main__":
    old = retained()
    gate(old)
    old.gate = lambda: gate(old)
    stage = sys.argv[1]
    if stage == "gate":
        preflight(old)
    elif stage == "prepare":
        prepare(old)
    elif stage == "tooling":
        old.tooling()
    elif stage == "dependencies":
        old.candidate_map = maps
        old.dependencies()
    elif stage == "compile":
        compile_engine(old)
    else:
        raise ValueError("Unknown stage")
