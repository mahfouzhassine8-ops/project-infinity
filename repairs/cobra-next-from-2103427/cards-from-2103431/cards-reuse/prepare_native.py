"""Prepare selected native-view tests using exact431 or a trusted actual owner.

This script does not build an APK, rewrite production, run Maven or synthesize
an unverified host overlay. The integrated host must already pass its complete
actual-owner/canonical preservation preparation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = "9ccc4c362a65118eeba38a8e7e4b0de5723c69af"
APK = "3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471"
FIXTURE = "CobraSettingsReturnBaselineTest.java"
TEST = "CobraCardsReuseNativeTest.java"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(baseline431, trusted_host, phase, out):
    baseline431, trusted_host, out = (p.resolve() for p in (baseline431, trusted_host, out))
    baseline = json.loads((baseline431 / "INPUTS.json").read_text())
    assert baseline["source"] == SOURCE and baseline["APK_sha256"] == APK
    for name, pin in baseline["DEX_sha256"].items():
        assert sha(baseline431 / name) == pin, name
    for name, pin in baseline["translated_jar_SHA256"].items():
        assert sha(baseline431 / (Path(name).stem + "-translated.jar")) == pin, name
    binding_path = trusted_host / "SOURCE-BINDINGS.json"
    bindings = json.loads(binding_path.read_text())
    assert bindings["baseline_signed_source"] == SOURCE and bindings["baseline_APK_sha256"] == APK
    assert sha(trusted_host / "production.jar") == bindings["production_jar_sha256"]
    assert sha(trusted_host / "support.jar") == bindings["support_jar_sha256"] == sha(baseline431 / "support.jar")
    assert sha(trusted_host / "OWNER-BUILD.json") == bindings["owner_BUILD_sha256"]
    assert sha(trusted_host / "INDEPENDENT-CANONICAL-RESULT.json") == bindings["canonical_chain"]["independent_proof_sha256"]
    assert bindings["canonical_chain"]["accepted_COBRA_ZIP_sha256"] == "98583b7a935103c8d13744fc624a6005f0566b1e3d26a47f240295cafd21cae7"
    assert sha(trusted_host / "ACTUAL-CANONICAL-CLASS-HASHES.json") == bindings["canonical_class_hash_inventory_sha256"]
    fixture = trusted_host / "fixtures-not-selected" / FIXTURE
    assert sha(fixture) == bindings["fixture_source"]["sha256"]
    scope = json.loads((HERE / "SCOPE.json").read_text())
    selected = scope["selected_native_tests"][phase]
    if phase == "candidate":
        build = bindings["owner_BUILD"]
        assert "com/projectinfinity/kodi/CobraCardsReuse.class" in bindings["new_helper_classes"]
        runtime = HERE / "runtime/CobraCardsReuse.java"
        recorded = build["helper_sources"][str(runtime.relative_to(ROOT))]
        assert sha(runtime) == recorded, "Actual owner must compile the current reviewed helper"
        for name in ("patch.py", "SOURCE-BUDGET.json"):
            path = HERE / name
            assert build["compiler_source_files"][str(path.relative_to(ROOT))] == sha(path), name
        changes = set(build["source_method_changes"]["Lcom/projectinfinity/kodi/InfinityLiveActivity;"])
        budget = json.loads((HERE / "SOURCE-BUDGET.json").read_text())
        assert set(budget["allowed_changed_methods"]) <= changes
    assert not out.exists(), "Fresh output required; no deletion/reuse"
    out.mkdir(parents=True)
    owner = baseline431 if phase == "accepted431" else trusted_host
    for name in ("production.jar", "support.jar"):
        shutil.copyfile(owner / name, out / name)
    shutil.copytree(owner / "android-test-libs", out / "android-test-libs")
    target = out / "src/test/java/com/projectinfinity/kodi"
    target.mkdir(parents=True)
    shutil.copyfile(fixture, target / FIXTURE)
    shutil.copyfile(HERE / TEST, target / TEST)
    # Shared fixture tests are compiled for their real native setup only; their
    # unrelated test methods are not selected by the Maven command.
    pom = (owner / "pom.xml").read_text().replace(str(owner), str(out))
    pom = pom.replace("projection.output", "reuse.output").replace("integrated.output", "reuse.output")
    (out / "pom.xml").write_text(pom)
    record = {
        "phase":phase,
        "baseline_signed_source":SOURCE,
        "baseline_APK_sha256":APK,
        "baseline_DEX_sha256":baseline["DEX_sha256"],
        "trusted_source_bindings_sha256":sha(binding_path),
        "trusted_actual_owner_BUILD_sha256":bindings["owner_BUILD_sha256"],
        "trusted_owner_DEX_sha256":bindings["owner_DEX_sha256"],
        "production_jar_sha256":sha(out / "production.jar"),
        "support_jar_sha256":sha(out / "support.jar"),
        "fixture_sha256":sha(fixture),
        "test_sha256":sha(HERE / TEST),
        "scope_sha256":sha(HERE / "SCOPE.json"),
        "prepare_sha256":sha(HERE / "prepare_native.py"),
        "selected_tests":selected,
        "core_method_stubs":"NONE; actual native buildShell/ShowGuideShell/Layout/Render/projection/auth",
        "provider_workers":"ADMISSIONS_RECORDED; WORKER_BODIES_NOT_EXECUTED",
        "Activity_lifecycle":"NOT_CALLED; native visible/measure fixture only",
        "application_APK":"NOT_BUILT_OR_INSTALLED",
        "timing_FPS":"NOT_MEASURED",
        "physical_Fold":"NOT_RUN",
        "shutdown":"NOT_RUN",
    }
    (out / "INPUTS.json").write_text(json.dumps(record, indent=2) + "\n")
    (out / "SELECTION.json").write_text(json.dumps({"class":"CobraCardsReuseNativeTest", "methods":selected,
                                                    "scope":"SCOPE.json", "recorded_before_execution":True}, indent=2) + "\n")
    print("Prepared selected real-native cache cases, phase " + phase + "; no test executed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline431", type=Path, required=True)
    parser.add_argument("--trusted-host", type=Path, required=True)
    parser.add_argument("--phase", choices=("accepted431", "candidate"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    prepare(**vars(parser.parse_args()))
