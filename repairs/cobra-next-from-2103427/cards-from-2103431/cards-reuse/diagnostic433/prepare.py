"""Prepare the one authorized reuse diagnostic; never compile or execute it."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
OWNER = HERE.parents[1]
REPO = OWNER.parents[2]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def prepare(baseline, out, maven):
    baseline, out, maven = (p.resolve() for p in (baseline, out, maven))
    scope = read(HERE / "SCOPE.json")
    selected = ["nativeReusePreservesScrollSelectionAndCurrentProgramme"]
    assert scope["selected_before_execution"] and scope["selected_methods"] == selected
    trusted = Path(scope["trusted_host"])
    binding = read(trusted / "SOURCE-BINDINGS.json")
    assert binding["source"] == scope["production_source"]
    assert binding["owner_DEX_sha256"] == scope["trusted_owner_DEX_sha256"]
    assert sha(Path(scope["official_CI_archive"])) == scope["official_CI_archive_sha256"]
    with zipfile.ZipFile(scope["official_CI_archive"]) as archive:
        actual_ci = json.loads(archive.read("failed-checks/reuse/INPUTS.json"))["source_binding"]
    assert actual_ci["source"] == scope["production_source"]
    assert actual_ci["owner_DEX_sha256"] == binding["owner_DEX_sha256"], "Diagnostic owner differs from actual failed CI owner"
    for name in ("production", "support"):
        assert sha(trusted / (name + ".jar")) == binding[name + "_jar_sha256"] == scope["trusted_" + name + "_sha256"]
    for name, pin in binding["compiler_source_files"].items():
        assert sha(REPO / name) == pin, "Frozen production input changed: " + name
    helper = module("reuse_diagnostic_native_prepare", OWNER / "cards-reuse/prepare_native.py")
    helper.prepare(baseline, trusted, "candidate", out)
    # Preserve the generic preparer's unexecuted five-case receipt. Replace the
    # active selector with the separately authorized exact one before execution.
    shutil.copyfile(out / "SELECTION.json", out / "GENERIC-SELECTION-NOT-EXECUTED.json")
    shutil.copyfile(out / "INPUTS.json", out / "GENERIC-INPUTS-NOT-EXECUTED.json")
    host = module("reuse_diagnostic_host_properties", OWNER / "ci_host.py")
    host.set_properties(out, {"reuse.output": str(out / "measurements")})
    native = host.verify_native_dependencies(maven, binding)
    selector = "CobraCardsReuseNativeTest#" + selected[0]
    common = [str(maven), "-B", "-q", "-f", str(out / "pom.xml"), "-Dmaven.repo.local=" + str(host.local_repository(maven))]
    selection = {"class": "CobraCardsReuseNativeTest", "methods": selected, "recorded_before_execution": True,
                 "command": common + ["-Dtest=" + selector, "test"],
                 "compile_only_command": common + ["-DskipTests", "test-compile"],
                 "compiled_only_fixture_classes": ["CobraSettingsReturnBaselineTest"],
                 "scope_sha256": sha(HERE / "SCOPE.json"), "production_source": scope["production_source"]}
    receipt = read(out / "INPUTS.json")
    receipt.update(phase="ONE_LOCAL_PREF_FIX_REUSE_PREASSERT_DIAGNOSTIC", selected_tests=selected,
                   scope_sha256=sha(HERE / "SCOPE.json"), diagnostic_prepare_sha256=sha(Path(__file__)),
                   diagnostic_test_sha256=sha(OWNER / "cards-reuse/CobraCardsReuseNativeTest.java"),
                   diagnostic_source_files={str(p.relative_to(REPO)): sha(p) for p in
                       (HERE / "SCOPE.json", Path(__file__), OWNER / "cards-reuse/CobraCardsReuseNativeTest.java")},
                   frozen_production_source=scope["production_source"], source_binding=binding,
                   resolved_native_dependencies=native, pom_sha256=sha(out / "pom.xml"), behavior="NOT_RUN")
    write(out / "SELECTION.json", selection)
    write(out / "INPUTS.json", receipt)
    print("Prepared exactly one existing diagnostic method; no compilation or execution")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "out", "maven"):
        parser.add_argument("--" + name, type=Path, required=True)
    prepare(**vars(parser.parse_args()))
