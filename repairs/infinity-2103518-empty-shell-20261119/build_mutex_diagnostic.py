"""Reconstruct the signed 2103518 engine and build the selected mutex probe."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BRANCH = "work/infinity-2103518-empty-shell-investigation-20261119"
BASE_TOOL = ROOT / "repairs/infinity-2103514-targeted-20261118/native_build.py"
REVIEWED_TOOL = "827dc2abdb042ed59ba3c1ab8bddd17f277c0737"
PRIOR = ROOT / "signed518-native"
REQUEST = json.loads((HERE / "MUTEX-NATIVE-REQUEST.json").read_bytes())


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", ROOT, *args])


def load_native():
    receipt_names = (
        "native_build.py", "CI-NATIVE.json", "STARTUP-ABI-SCOPE.json",
        "STARTUP-ABI-HOST.json", "startup-boundary-abi.patch",
    )
    for name in receipt_names:
        path = BASE_TOOL.with_name(name)
        require(path.read_bytes() == git("show", REVIEWED_TOOL + ":" + str(path.relative_to(ROOT))),
                "Reviewed native input differs: " + name)
    spec = importlib.util.spec_from_file_location("reused_native", BASE_TOOL)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    return native


def check_artifact(row):
    value = json.loads(subprocess.check_output([
        "gh", "api", f"repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{row['id']}",
    ]))
    require(not value["expired"] and all(value[key] == row[key] for key in
            ("id", "name", "size_in_bytes", "digest")) and
            value["workflow_run"]["id"] == row["run"] and
            value["workflow_run"]["head_sha"] == row["source"], "Wrong linked signed518 engine artifact")
    run = json.loads(subprocess.check_output([
        "gh", "api", f"repos/mahfouzhassine8-ops/project-infinity/actions/runs/{row['run']}",
    ]))
    require(run["conclusion"] == "success", "Previous native link did not pass")


def gate(old):
    require(os.environ.get("GITHUB_ACTIONS") == "true" and
            os.environ["GITHUB_REPOSITORY"] == old.REPOSITORY and
            os.environ["GITHUB_REF"] == "refs/heads/" + BRANCH and
            os.environ["GITHUB_EVENT_NAME"] == "push" and
            git("rev-parse", "HEAD").decode().strip() == os.environ["GITHUB_SHA"],
            "Wrong mutex-only native build request")
    for name, digest in REQUEST["inputs"].items():
        require(sha(ROOT / name) == digest, "Scoped input hash differs: " + name)
    host = json.loads((HERE / "MUTEX-HOST.json").read_bytes())
    require(host["result"] == "PASS" and all(host[key] is True for key in
            ("owner_and_waiter_bound", "timestamps_checked", "loss_checked", "disabled_path_checked")),
            "Missing focused probe verification")
    legacy, scope = (json.loads(path.read_bytes()) for path in (old.REQUEST, old.SCOPE))
    require(old.sha(old.REQUEST) == "ef12b91795833060319a25d8dc5feed77a5083bf8b2ac7cadd0a0d48f50448d2"
            and legacy["reviewed_files"] == old.source_hashes(),
            "Historical producer request or sources differ")
    for name in ("build_native.py", "verify_scope.py", "prepare_ci_tooling.sh"):
        path = old.PRODUCER_PATH + "/" + name
        require(old.blob(old.FROZEN, path) == old.blob(REVIEWED_502_PRODUCER, path),
                "Reviewed reconstruction helper changed")
    return legacy, scope


REVIEWED_502_PRODUCER = "dea5df6063b49d65099c7958722f2b9f33895600"


def maps():
    original = json.loads((PRIOR / "NATIVE-SOURCE-MAP.json").read_bytes())
    artifact = REQUEST["retained_engine"]
    receipt = json.loads((PRIOR / "ARM64-514.json").read_bytes())
    release_authority = json.loads(git(
        "show", "41dcaca27396fca320097b6a53d1ba5f3d7dfee6:"
        "repairs/dual-experience-isolation-2103420/release-authority.json"))
    engine_digest = release_authority["payload"]["member:lib/arm64-v8a/libkodi.so"]["sha256"]
    require(release_authority["candidate_versionCode"] == 2103518 and
            engine_digest == REQUEST["baseline_engine_sha256"] ==
            sha(PRIOR / "libkodi.so") == receipt["native_sha256"] and
            receipt["source_commit"] == artifact["source"] and
            receipt["status"] == "PASS_FULL_ARM64_LINK_AND_EXACT_2103514_ABI" and
            len(original) == receipt["reviewed_file_count"] == 9418,
            "The source map does not bind the actual signed 2103518 engine")
    revised = dict(original)
    for name, pins in REQUEST["source_allowlist"].items():
        require(original.get(name) == pins["before"], "Wrong signed518 preimage: " + name)
        revised[name] = pins["after"]
    require(len(revised) == 9419, "Unexpected extra sources")
    return original, revised


def prepare(native, old):
    native.prepare(old)
    original, revised = maps()
    installed = old.hasher().hashes(old.NATIVE)
    require(installed == original, "Reconstructed 2103518 source map differs")
    command = ["patch", "--batch", "--forward", "--fuzz=0", "-p1", "-i",
               str(HERE / "persistence-mutex.patch")]
    subprocess.run(command + ["--dry-run"], cwd=old.NATIVE, check=True)
    subprocess.run(command, cwd=old.NATIVE, check=True)
    require(old.hasher().hashes(old.NATIVE) == revised, "Unexpected native source delta")
    # State::mutex remains a std::mutex. The only external access to its
    # ledger is in the Python observer. Detect drift before a build.
    ledger_access = re.compile(rb"InfinityScriptPersistence\s*::\s*Get\s*\(")
    access = [name for name in revised if name.startswith("xbmc/") and
              Path(name).suffix in (".h", ".cpp", ".c", ".hpp", ".inl") and
              ledger_access.search((old.NATIVE / name).read_bytes())]
    require(access == ["xbmc/interfaces/python/InfinityPythonPersistence.h"],
            "An uninstrumented direct persistence mutex caller exists")
    old.save("NATIVE-SOURCE-MAP.json", revised)
    old.save("MUTEX-SOURCE-PRESERVATION.json", dict(
        status="PASS_EXACT_2103518_SOURCE_MAP", baseline_engine_sha256=REQUEST["baseline_engine_sha256"],
        source=os.environ["GITHUB_SHA"], native_delta=REQUEST["source_allowlist"],
        unchanged_sources=sum(original[name] == revised[name] for name in original)))


def compile_engine(native, old):
    native.maps = maps
    # The retained signed518 artifact is the ELF comparison input. Keep the
    # existing exact dependencies, exports and startup storage ABI checks.
    native.EXACT = PRIOR
    native.compile_engine(old)
    engine = old.OUT / "libkodi.so"
    import mmap

    with engine.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as image:
        for marker in (b"InfinityPersistenceMutex", b"phase=waiting ticket=", b"phase=completed ticket=",
                       b"phase=loss wait_slots=", b"interpreter.returned"):
            require(image.find(marker) >= 0, "Linked diagnostic marker missing")
    proof = json.loads((old.OUT / "ARM64-514.json").read_bytes())
    old.save("MUTEX-ARM64.json", dict(
        status="PASS_FULL_ARM64_LINK_AND_EXACT_2103518_ABI", engine_sha256=sha(engine),
        baseline_engine_sha256=REQUEST["baseline_engine_sha256"], source=os.environ["GITHUB_SHA"],
        native_source_count=proof["reviewed_file_count"], full_arm64_link=True, diagnostic_only=True))


if __name__ == "__main__":
    native = load_native()
    old = native.retained()
    native.gate = gate
    old.gate = lambda: gate(old)
    gate(old)
    stage = sys.argv[1]
    if stage == "gate":
        check_artifact(REQUEST["retained_engine"])
        native.preflight(old)
    elif stage == "prepare":
        prepare(native, old)
    elif stage == "tooling":
        old.tooling()
    elif stage == "dependencies":
        old.candidate_map = maps
        old.dependencies()
    elif stage == "compile":
        compile_engine(native, old)
    else:
        raise ValueError("Unknown stage")
