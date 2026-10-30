"""Prepare exactly five selected post-fix checks against a newly admitted owner.

No application compilation or execution occurs here. The pre-fix diagnostic
preparer and all historical inputs/results remain unchanged.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
OWNER = HERE.parents[1]
REPO = OWNER.parents[2]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def prepare(baseline, trusted_host, out, maven, source, production_sha256):
    baseline, trusted, out, maven = (p.resolve() for p in (baseline, trusted_host, out, maven))
    scope = read(HERE / "SCOPE.json")
    assert scope["selected_before_execution"] and scope["selected_methods"] == 5
    assert re.fullmatch("[0-9a-f]{40}", source) and source != "30f840bab7eb21eee8255ff349d3f7eb61fc8202"
    assert re.fullmatch("[0-9a-f]{64}", production_sha256)
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip() == source
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip() == scope["branch"]
    host = module("postfix433_host_gates", OWNER / "ci_host.py")
    binding = host.bindings(baseline, trusted)
    assert binding["status"] == "PASS_FRESH_SOURCE_BOUND_EXACT_FIVE_CLASS_HOST_OVERLAY_NO_BEHAVIOR"
    assert binding["source"] == source
    assert sha(trusted / "production.jar") == binding["production_jar_sha256"] == production_sha256
    assert sha(trusted / "pom.xml") == binding["pom_sha256"]
    native = host.verify_native_dependencies(maven, binding)
    assert scope["groups"]["CobraCardsReuseNativeTest"] == ["nativeReusePreservesScrollSelectionAndCurrentProgramme"]
    assert scope["groups"]["CobraCardsVisualCloseoutTest"] == host.CLOSEOUT
    admitted_sources = [Path(__file__), HERE / "SCOPE.json", OWNER / "ci_host.py",
                        OWNER / "cards-reuse/prepare_native.py", OWNER / "cards-reuse/CobraCardsReuseNativeTest.java",
                        OWNER / "visual-closeout/qa/prepare.py", OWNER / "visual-closeout/qa/SCOPE.json",
                        OWNER / "visual-closeout/qa/CobraCardsVisualCloseoutTest.java",
                        OWNER / "layout-qa/CobraCardsLayoutTest.java", OWNER / "settings-return/CobraSettingsReturnBaselineTest.java"]
    for path in admitted_sources:
        relative = str(path.relative_to(REPO))
        committed = subprocess.check_output(["git", "show", source + ":" + relative], cwd=REPO)
        assert hashlib.sha256(committed).hexdigest() == sha(path), "Uncommitted QA input: " + relative
    assert not out.exists(), "Fresh output required; historical evidence remains intact"
    out.mkdir(parents=True)
    groups = []
    source_files = {str(p.relative_to(REPO)): sha(p) for p in admitted_sources}
    for name, class_name, fixture in (
        ("reuse", "CobraCardsReuseNativeTest", "CobraSettingsReturnBaselineTest"),
        ("visual-closeout", "CobraCardsVisualCloseoutTest", "CobraCardsLayoutTest"),
    ):
        folder = out / name
        methods = scope["groups"][class_name]
        if name == "reuse":
            module("postfix433_native_prepare", OWNER / "cards-reuse/prepare_native.py").prepare(baseline, trusted, "candidate", folder)
            shutil.copyfile(folder / "SELECTION.json", folder / "GENERIC-SELECTION-NOT-EXECUTED.json")
            shutil.copyfile(folder / "INPUTS.json", folder / "GENERIC-INPUTS-NOT-EXECUTED.json")
            host.set_properties(folder, {"reuse.output": str(folder / "measurements")})
            test_source = OWNER / "cards-reuse/CobraCardsReuseNativeTest.java"
            fixture_source = OWNER / "settings-return/CobraSettingsReturnBaselineTest.java"
        else:
            module("postfix433_visual_prepare", OWNER / "visual-closeout/qa/prepare.py").prepare(
                trusted, OWNER / "layout-qa/goldens/accepted431", folder, 500)
            assert read(folder / "SELECTION.json")["methods"] == methods
            test_source = OWNER / "visual-closeout/qa/CobraCardsVisualCloseoutTest.java"
            fixture_source = OWNER / "layout-qa/CobraCardsLayoutTest.java"
        copied_sources = folder / "src/test/java/com/projectinfinity/kodi"
        for path in (test_source, fixture_source):
            assert sha(copied_sources / path.name) == sha(path), "Compiled QA input differs from committed source: " + path.name
        common = [str(maven), "-B", "-q", "-f", str(folder / "pom.xml"), "-Dmaven.repo.local=" + str(host.local_repository(maven))]
        selection = {"class": class_name, "methods": methods, "recorded_before_execution": True,
                     "command": common + ["-Dtest=" + class_name + "#" + "+".join(methods), "test"],
                     "compile_only_command": common + ["-DskipTests", "test-compile"],
                     "compiled_only_fixture_classes": [fixture], "scope_sha256": sha(HERE / "SCOPE.json")}
        receipt = read(folder / "INPUTS.json")
        receipt.update(phase="EXACT_FIVE_LOCAL_POST_FIX_METHODS_NO_EXECUTION", selected_tests=methods,
                       source=source, source_binding=binding, root_admitted_production_sha256=production_sha256,
                       postfix_scope_sha256=sha(HERE / "SCOPE.json"), postfix_prepare_sha256=sha(Path(__file__)),
                       actual_test_sha256=sha(test_source), source_files={**source_files, str(test_source.relative_to(REPO)): sha(test_source)},
                       resolved_native_dependencies=native, pom_sha256=sha(folder / "pom.xml"), behavior="NOT_RUN")
        for jar, key in (("production.jar", "production_jar_sha256"), ("support.jar", "support_jar_sha256")):
            assert sha(folder / jar) == binding[key]
        write(folder / "INPUTS.json", receipt)
        write(folder / "SELECTION.json", selection)
        groups.append({"name": name, "class": class_name, "methods": methods, "inputs_sha256": sha(folder / "INPUTS.json"),
                       "selection_sha256": sha(folder / "SELECTION.json")})
    write(out / "PREPARED-RESULT.json", {"status": "EXACT_FIVE_POST_FIX_METHODS_PREPARED_NOT_EXECUTED", "source": source,
          "source_binding_sha256": sha(trusted / "SOURCE-BINDINGS.json"), "production_jar_sha256": production_sha256,
          "groups": groups, "selected_methods": sum(len(g["methods"]) for g in groups),
          "scope_sha256": sha(HERE / "SCOPE.json"), "prepare_sha256": sha(Path(__file__)), "behavior": "NOT_RUN",
          "Android": "NOT_RUN", "shutdown": "NOT_RUN"})
    print("Prepared exactly five post-fix methods; no compilation or application execution")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "trusted-host", "out", "maven"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--production-sha256", required=True)
    prepare(**vars(parser.parse_args()))
