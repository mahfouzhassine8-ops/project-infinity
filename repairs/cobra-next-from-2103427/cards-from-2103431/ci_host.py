"""Source-bound, candidate-only essential host producer. No APK or Android run.

Dependencies and the exact431 baseline/trusted owner must already be prepared.
Each selected class runs in its own fresh Maven folder. Unselected fixture tests
are compiled only; an exact JUnit method-set check rejects accidental expansion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import traceback
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = "9ccc4c362a65118eeba38a8e7e4b0de5723c69af"
APK = "3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471"
NS = "{http://maven.apache.org/POM/4.0.0}"
ET.register_namespace("", NS[1:-1])
PROFILE = ["currentRawAndActiveIdAreReadFreshInOriginalOrder", "publicProfilesRemainIndependentMutableCopies",
           "malformedWrongTypeAndNullableDataRecoverOnNextCall", "firstMatchOptBooleanMissingIdsAndNullActiveIdMatchOriginalLoop",
           "validOversizeIsEvaluatedUncachedAndAdmissionIsBounded", "privateDataSnapshotsAreSeparatePerThread"]
PROJECTION = ["actualProjectionCounts20226WithoutTiming", "nextProjectionReflectsFiltersHiddenFavoritesRecentsInventoryAndProfile"]
PRESENTATION = ["actualCandidateFinalStateParityAndBoundPlayerProgress"]
LOGO = ["clearWithoutOwnerCreatesNoServiceOrWork", "clearedBlankViewRejectsOldCompletionAndDoesNotRequeueOnAttach",
        "clearThenRebindPublishesOnlyTheCurrentLogo", "clearingOneViewPreservesSharedFlightAndOtherWaiter"]
NATIVE = ["nativeCardRecycleAndCurrentProgramme", "nativeCardDimensionsAndCornerTouch", "nativeCardLogoRecycle"]
REUSE = ["nativeReusePreservesScrollSelectionAndCurrentProgramme", "nativeImmediateSecondRenderPreservesPendingPosition",
         "nativeSelectiveCollectionsAndFreshDirectory", "nativePolicyTypesAndContextInvalidation", "revisionHooksAllowBackgroundAndModeExitDisposes"]
LAYOUT = ["actualCardsRenderAtReferenceViewport", "cardsRestoresSharedNativeViewsInOtherModes",
          "truthfulLiveBadgeUsesNativeStatusAndPreservesActualPipPress", "activeAmbientPreservesNativeEffectsAndRecordsWrapping"]
THEME = ["nativeCandidateColdAndWarmThemeCardsMobileControl"]
CLOSEOUT = ["nativeWrappedMissingScheduleAndLivePeersShareMeasuredRows",
            "nativeRowRecyclingAndContentChangesPreserveAnchors",
            "nativeMoreAndRowTargetsKeepTheirCurrentChannelAfterGrowth",
            "cardsHeaderAndRowsLeaveFourNativeModesUnchanged"]
CLOSEOUT_HEADER_WEIGHT = 500
GROUPS = [
    ("profile", "CobraProfileDataReuseTest", PROFILE, ["profile-reads/tests/CobraProfileDataReuseTest.java"]),
    ("projection", "CobraProjectionCorrectnessTest", PROJECTION, ["profile-reads/tests/CobraProjectionCorrectnessTest.java"]),
    ("presentation", "CobraProgrammePresentationBaselineTest", PRESENTATION, ["presentation-qa/CobraProgrammePresentationBaselineTest.java"]),
    ("logo", "CobraCardsLogoUnbindTest", LOGO, ["logo-clear/CobraCardsLogoUnbindTest.java"]),
    ("native-cards", "CobraCardsNativeRenderTest", NATIVE, ["render-qa/CobraCardsNativeRenderTest.java"]),
    ("reuse", "CobraCardsReuseNativeTest", REUSE, ["cards-reuse/CobraCardsReuseNativeTest.java"]),
    ("layout", "CobraCardsLayoutTest", LAYOUT, ["layout-qa/CobraCardsLayoutTest.java"]),
    ("theme-publication", "CobraCardsThemeOrderControlTest", THEME,
     ["layout-qa/CobraCardsThemeOrderControlTest.java"]),
    ("visual-closeout", "CobraCardsVisualCloseoutTest", CLOSEOUT,
     ["visual-closeout/qa/CobraCardsVisualCloseoutTest.java"]),
]
REFERENCES = {
    "presentation-qa/results/signed431-baseline/BASELINE.json": "afe37ff8ed00a442ee240efe425413df0cc9d57acb397993939844c16bab763d",
    "presentation-qa/results/signed431-bound-player-progress/BASELINE-PLAYER-PROGRESS.json": "600cf86ba8958517a16f0519bf8a6040348acbb1984ce1f714fc2ec7c65eb383",
}
THEME_REFERENCE = "layout-qa/goldens/native431-theme-order/NATIVE431-COLD-WARM-THEME.json"
THEME_REFERENCE_SHA = "c435dcc449c4aec8b783a973698621cd4f30c822c5b58a34c6ba045693a46691"


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def inventory(folder):
    return {str(path.relative_to(folder)): sha(path) for path in sorted(folder.rglob("*")) if path.is_file()}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def bindings(baseline, trusted):
    original = read(baseline / "INPUTS.json")
    require(original["source"] == SOURCE and original["APK_sha256"] == APK, "Exact signed431 baseline required")
    for name, pin in original["DEX_sha256"].items():
        require(sha(baseline / name) == pin, "Baseline DEX changed: " + name)
    for name, pin in original["translated_jar_SHA256"].items():
        require(sha(baseline / (Path(name).stem + "-translated.jar")) == pin, "Baseline translation changed: " + name)
    manifest = read(trusted / "SOURCE-BINDINGS.json")
    require(sha(trusted / "pom.xml") == manifest["pom_sha256"], "Trusted portable POM changed")
    require(manifest["baseline_signed_source"] == SOURCE and manifest["baseline_APK_sha256"] == APK, "Trusted owner baseline differs")
    require(sha(trusted / "production.jar") == manifest["production_jar_sha256"], "Trusted production changed")
    require(sha(trusted / "support.jar") == manifest["support_jar_sha256"] == sha(baseline / "support.jar"), "Support differs from431")
    require(sha(trusted / "OWNER-BUILD.json") == manifest["owner_BUILD_sha256"], "Owner build receipt changed")
    require(read(trusted / "OWNER-BUILD.json") == manifest["owner_BUILD"], "Owner receipt differs from source binding")
    require(sha(trusted / "INDEPENDENT-CANONICAL-RESULT.json") == manifest["canonical_chain"]["independent_proof_sha256"], "Canonical proof changed")
    require("PASS" in read(trusted / "INDEPENDENT-CANONICAL-RESULT.json")["status"], "Canonical proof is not passing")
    require(sha(trusted / "ACTUAL-CANONICAL-CLASS-HASHES.json") == manifest["canonical_class_hash_inventory_sha256"], "Canonical inventory changed")
    require(sha(trusted / "HOST-OVERLAY-CLASS-HASHES.json") == manifest["host_overlay_class_hash_inventory_sha256"], "Host inventory changed")
    require(manifest["canonical_chain"]["accepted_COBRA_ZIP_sha256"] == "98583b7a935103c8d13744fc624a6005f0566b1e3d26a47f240295cafd21cae7", "Accepted Cobra identity differs")
    require(sorted(manifest["changed_existing_classes"]) == sorted(manifest["allowed_changed_existing_classes"]), "Existing class budget differs")
    require(sorted(manifest["new_helper_classes"]) == sorted(manifest["expected_new_helper_classes"]), "Helper class budget differs")
    for name, pin in manifest["compiler_source_files"].items():
        require(sha(REPO / name) == pin, "Trusted owner is stale for source: " + name)
    require(sha(HERE / "verify_owner_source.py") == manifest["verifier_source_sha256"], "Canonical verifier source changed")
    require(inventory(trusted / "android-test-libs") == inventory(baseline / "android-test-libs"), "Official Android host support libraries differ")
    return manifest


def properties(trusted, manifest):
    """Keep the prepared portable resolver policy and exact dependency versions."""
    pom = ET.parse(trusted / "pom.xml")
    dependencies = pom.findall("./" + NS + "dependencies/" + NS + "dependency")
    for name, info in manifest["native_graphics_dependencies"].items():
        matches = [item for item in dependencies
                   if item.findtext(NS + "groupId") == "org.robolectric"
                   and item.findtext(NS + "artifactId") == name]
        require(len(matches) == 1 and matches[0].findtext(NS + "version") == info["version"],
                "Prepared native graphics coordinate differs: " + name)
    return {}



def local_repository(maven):
    # Match standard Maven precedence without adding a resolver plugin or a
    # developer-specific path. The selected CLI has no extra -s/-Dmaven flags.
    value = None
    for path in (maven.parent.parent / "conf/settings.xml", Path.home() / ".m2/settings.xml"):
        if path.is_file():
            root = ET.parse(path).getroot()
            found = root.findtext("{http://maven.apache.org/SETTINGS/1.2.0}localRepository")
            if found is None:
                found = next((node.text for node in root if node.tag.rsplit("}", 1)[-1] == "localRepository"), None)
            if found:
                value = found
    for variable in ("JAVA_TOOL_OPTIONS", "MAVEN_OPTS", "MAVEN_ARGS"):
        for token in shlex.split(os.environ.get(variable, "")):
            if token.startswith("-Dmaven.repo.local="):
                value = token.split("=", 1)[1]
    value = value or str(Path.home() / ".m2/repository")
    value = value.replace("${user.home}", str(Path.home()))
    require("${" not in value, "Unresolved Maven localRepository expression")
    return Path(value).expanduser().resolve()


def verify_native_dependencies(maven, manifest):
    repository = local_repository(maven)
    verified = {}
    expected = {
        "nativeruntime": ("4.14.1", "c07b66d315aec3272a7c64aa5f154b4194be2cc6030a733d16f2ee87330232a8"),
        "nativeruntime-dist-compat": ("1.0.16", "2f4e879b00eed634d0e43353ecff80db4d5ce24b3b213d1e6053cb21b0ced10f"),
    }
    for name, (version, pin) in expected.items():
        info = manifest["native_graphics_dependencies"][name]
        require(info["version"] == version and info.get("expected_jar_sha256", info.get("jar_sha256")) == pin,
                "Prepared native graphics identity differs: " + name)
        path = repository / "org/robolectric" / name / version / (name + "-" + version + ".jar")
        require(sha(path) == pin, "Resolved native graphics JAR differs: " + str(path))
        verified[name] = {"file": str(path), "version": version, "sha256": pin}
    return verified


def prepare_plain(trusted, folder, sources):
    folder.mkdir(parents=True)
    for name in ("production.jar", "support.jar"):
        shutil.copyfile(trusted / name, folder / name)
    shutil.copytree(trusted / "android-test-libs", folder / "android-test-libs")
    target = folder / "src/test/java/com/projectinfinity/kodi"
    target.mkdir(parents=True)
    for source in sources:
        shutil.copyfile(source, target / source.name)
    pom = (trusted / "pom.xml").read_text().replace(str(trusted), str(folder))
    (folder / "pom.xml").write_text(pom)


def set_properties(folder, values):
    tree = ET.parse(folder / "pom.xml")
    nodes = tree.findall(".//" + NS + "systemPropertyVariables")
    require(len(nodes) == 1, "Exactly one reviewed Surefire property block required")
    target = nodes[0]
    for old in list(target):
        if old.tag.removeprefix(NS) in values:
            target.remove(old)
    for key, value in values.items():
        ET.SubElement(target, NS + key).text = str(value)
    tree.write(folder / "pom.xml", encoding="utf-8", xml_declaration=True)


def junit(folder, class_name, methods):
    reports = sorted((folder / "target/surefire-reports").glob("TEST-*.xml"))
    require(bool(reports), "No actual JUnit XML produced")
    expected_class = "com.projectinfinity.kodi." + class_name
    observed = []
    for path in reports:
        suite = ET.parse(path).getroot()
        require(suite.tag == "testsuite" and suite.get("name") == expected_class, "Unselected JUnit suite: " + str(path))
        require(all(int(suite.get(key, "-1")) == 0 for key in ("failures", "errors", "skipped")), "JUnit failed/errored/skipped: " + str(path))
        cases = suite.findall("testcase")
        require(int(suite.get("tests", "-1")) == len(cases), "JUnit suite count differs from cases")
        for case in cases:
            require(case.get("classname") == expected_class, "Unselected testcase class")
            require(not any(case.find(key) is not None for key in ("failure", "error", "skipped")), "Non-passing testcase")
            observed.append(case.get("name"))
    require(len(observed) == len(methods) and sorted(observed) == sorted(methods), "Actual JUnit methods differ from exact selection: " + repr(observed))
    return {"class": expected_class, "methods": observed, "tests": len(observed), "failures": 0, "errors": 0, "skipped": 0,
            "reports": {str(path.relative_to(folder)): sha(path) for path in reports}}


def run(baseline, trusted_host, out, maven):
    baseline, trusted, out, maven = (path.resolve() for path in (baseline, trusted_host, out, maven))
    require(not out.exists(), "Fresh producer output required; historical evidence is never deleted")
    require(maven.is_file(), "Prepared Maven executable required")
    manifest = bindings(baseline, trusted)
    sdk_properties = properties(trusted, manifest)
    source_binding = sha(trusted / "SOURCE-BINDINGS.json")
    source_pins = dict(manifest["compiler_source_files"])
    source_pins[str(Path(__file__).resolve().relative_to(REPO))] = sha(Path(__file__))
    for relative in ("cards-reuse/prepare_native.py", "cards-reuse/SCOPE.json", "layout-qa/prepare.py", "layout-qa/SCOPE.json",
                     "visual-closeout/qa/prepare.py", "visual-closeout/qa/SCOPE.json"):
        source_pins[str((HERE / relative).relative_to(REPO))] = sha(HERE / relative)
    golden_dir = HERE / "layout-qa/goldens/accepted431"
    golden_binding = read(golden_dir / "SOURCE-BINDING.json")
    require(golden_binding["baseline_binding"]["source_binding"]["source"] == SOURCE, "Layout goldens must bind signed431")
    require(golden_binding["baseline_binding"]["source_binding"]["APK_sha256"] == APK, "Layout golden APK differs")
    for name, pin in golden_binding["files"].items():
        require(sha(golden_dir / name) == pin, "Layout golden changed: " + name)
        source_pins[str((golden_dir / name).relative_to(REPO))] = pin
    for name, pin in REFERENCES.items():
        require(sha(HERE / name) == pin, "Frozen presentation reference changed: " + name)
        source_pins[str((HERE / name).relative_to(REPO))] = pin
    require(sha(HERE / THEME_REFERENCE) == THEME_REFERENCE_SHA, "Independent native431 theme-order reference changed")
    source_pins[str((HERE / THEME_REFERENCE).relative_to(REPO))] = THEME_REFERENCE_SHA
    out.mkdir(parents=True)
    result = {"status": "RUNNING_FOCUSED_CANDIDATE_HOST_ONLY", "source_binding_sha256": source_binding,
              "baseline_signed_source": SOURCE, "baseline_APK_sha256": APK, "groups": [],
              "timing_benchmarks": "NOT_RUN", "Android": "NOT_RUN", "physical_Fold": "NOT_RUN", "APK": "NOT_BUILT", "shutdown": "NOT_RUN"}
    try:
        for name, class_name, methods, relative_sources in GROUPS:
            bindings(baseline, trusted)
            sources = [HERE / rel for rel in relative_sources]
            folder = out / name
            auxiliary = []
            if name == "reuse":
                module("cards_ci_reuse_prepare", HERE / "cards-reuse/prepare_native.py").prepare(baseline, trusted, "candidate", folder)
                auxiliary = [trusted / "fixtures-not-selected/CobraSettingsReturnBaselineTest.java"]
                require(read(folder / "SELECTION.json")["methods"] == methods, "Reuse selection changed")
            elif name == "layout":
                module("cards_ci_layout_prepare", HERE / "layout-qa/prepare.py").prepare(trusted, folder, True, golden_dir)
            elif name == "visual-closeout":
                module("cards_ci_closeout_prepare", HERE / "visual-closeout/qa/prepare.py").prepare(
                    trusted, golden_dir, folder, CLOSEOUT_HEADER_WEIGHT)
                auxiliary = [HERE / "layout-qa/CobraCardsLayoutTest.java"]
                require(read(folder / "SELECTION.json")["methods"] == methods, "Visual closeout selection changed")
            else:
                if name == "logo":
                    auxiliary = [HERE.parent / "tests/CobraLogoWorkTest.java"]
                elif name == "theme-publication":
                    auxiliary = [HERE / "layout-qa/CobraCardsLayoutTest.java"]
                prepare_plain(trusted, folder, sources + auxiliary)
            props = dict(sdk_properties)
            output = folder / "measurements"
            props.update({"projection.output": str(output), "presentation.output": str(output), "reuse.output": str(output),
                          "cards.render.output": str(output), "cards.layout.output": str(output),
                          "cards.closeout.output": str(output),
                          "profile.helper.expected": "true", "projection.expected.hidden.reads": "1",
                          "projection.phase": "FINAL_CURRENT_OWNER_CANDIDATE_CORRECTNESS_NO_TIMING",
                          "cards.render.phase": "CARDS_TILE_PROTOTYPE", "cards.candidate": "true",
                          "cards.layout.baseline": str(golden_dir),
                          "cards.theme.baseline": str(HERE / THEME_REFERENCE),
                          "presentation.reference.baseline": str(HERE / next(iter(REFERENCES))),
                          "presentation.reference.player": str(HERE / list(REFERENCES)[1])})
            set_properties(folder, props)
            input_path = folder / "INPUTS.json"
            preparation = read(input_path) if input_path.exists() else None
            inputs = {"phase": "FINAL_CURRENT_OWNER_FOCUSED_HOST_CANDIDATE", "source_binding_sha256": source_binding,
                      "source_binding": manifest, "classpath": {n: sha(folder / n) for n in ("production.jar", "support.jar")},
                      "test_sha256": sha(sources[0]), "test_sources": {str(p.relative_to(REPO)): sha(p) for p in sources},
                      "compiled_fixture_only": {p.name: sha(p) for p in auxiliary}, "prepare_receipt": preparation,
                      "golden_binding_sha256": sha(golden_dir / "SOURCE-BINDING.json"),
                      "presentation_reference_sha256": REFERENCES, "pom_sha256": sha(folder / "pom.xml"),
                      "producer_source_sha256": sha(Path(__file__)), "selected_methods": methods,
                      "behavior": "NOT_RUN_AT_INPUT_RECORDING", "APK": "NOT_BUILT", "shutdown": "NOT_RUN"}
            for jar, pin in inputs["classpath"].items():
                require(pin == sha(trusted / jar), "Prepared group classpath differs from trusted owner")
            write(input_path, inputs)
            selector = class_name + "#" + "+".join(methods)
            repository_option = "-Dmaven.repo.local=" + str(local_repository(maven))
            command = [str(maven), "-B", "-q", "-f", str(folder / "pom.xml"), repository_option, "-Dtest=" + selector, "test"]
            compile_command = [str(maven), "-B", "-q", "-f", str(folder / "pom.xml"), repository_option, "-DskipTests", "test-compile"]
            write(folder / "SELECTION.json", {"class": class_name, "methods": methods, "recorded_before_execution": True,
                  "command": command, "compile_only_command": compile_command,
                  "compiled_only_fixture_classes": [p.stem for p in auxiliary], "baseline_or_timing_tests": "NONE"})
            source_pins.update({str(p.relative_to(REPO)): sha(p) for p in sources + auxiliary if p.is_relative_to(REPO)})
            with (folder / "COMPILE-OUTPUT.txt").open("w") as log:
                compilation = subprocess.run(compile_command, cwd=folder, stdout=log, stderr=subprocess.STDOUT)
            write(folder / "COMPILE-RESULT.json", {"exit_code": compilation.returncode,
                  "command": compile_command, "log_sha256": sha(folder / "COMPILE-OUTPUT.txt"), "behavioral_tests": "NOT_RUN"})
            require(compilation.returncode == 0, "Selected fixture compilation failed: " + name)
            resolved_native = verify_native_dependencies(maven, manifest)
            write(folder / "RESOLVED-NATIVE-DEPENDENCIES.json", resolved_native)
            for rel, pin in source_pins.items():
                require(sha(REPO / rel) == pin, "Source changed before selected execution: " + rel)
            with (folder / "TEST-OUTPUT.txt").open("w") as log:
                completed = subprocess.run(command, cwd=folder, stdout=log, stderr=subprocess.STDOUT)
            group = {"name": name, "class": class_name, "methods": methods, "maven_exit_code": completed.returncode,
                     "inputs_sha256": sha(input_path), "selection_sha256": sha(folder / "SELECTION.json"),
                     "raw_log_sha256": sha(folder / "TEST-OUTPUT.txt"), "resolved_native_dependencies": resolved_native}
            result["groups"].append(group)
            require(completed.returncode == 0, "Selected Maven group failed: " + name)
            group["JUnit"] = junit(folder, class_name, methods)
            if name == "presentation":
                report = read(output / "CANDIDATE.json")
                require(report["case_count"] == 15 and len(report["comparisons"]) == 15, "All15 frozen-reference parity cases required")
                group["internal_parity_cases"] = 15
            for rel, pin in source_pins.items():
                require(sha(REPO / rel) == pin, "Source changed during selected execution: " + rel)
            write(folder / "RESULT.json", {"status": "PASS_EXACT_SELECTED_HOST_METHODS", **group})
        bindings(baseline, trusted)
        require(sha(trusted / "SOURCE-BINDINGS.json") == source_binding, "Trusted source binding changed during execution")
        result.update(status="PASS_FOCUSED_CANDIDATE_HOST_ONLY", selected_JUnit_methods=sum(len(g[2]) for g in GROUPS),
                      selected_groups=len(GROUPS), internal_presentation_parity_cases=15)
    except Exception as error:
        result.update(status="FAILED_AT_RECORDED_SELECTED_HOST_GROUP", error=str(error))
        (out / "ERROR.txt").write_text(traceback.format_exc())
        raise
    finally:
        write(out / "HOST-RESULT.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("baseline", "trusted-host", "out", "maven"):
        parser.add_argument("--" + argument, type=Path, required=True)
    run(**vars(parser.parse_args()))
