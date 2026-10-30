"""Manual feature-only producer: exact431 inputs -> tested current owner ZIPs.

No APK assembly/signing, Android execution, registration, acceptance or shutdown.
The existing sole signer consumes the separately reviewed producer artifacts.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ISO = REPO / "repairs/dual-experience-isolation-2103420"
BRANCH = "work/cobra-only-from-2103427-20261028"
NS = "{http://maven.apache.org/POM/4.0.0}"
ET.register_namespace("", NS[1:-1])


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


def bootstrap_pom(out):
    """Resolve existing official host dependencies only; there are no tests."""
    root = ET.parse(ISO / "tests/pom.xml").getroot()
    deps = root.find(NS + "dependencies")
    systems = [dependency for dependency in deps if dependency.findtext(NS + "scope") == "system"]
    expected = {("local.review", "delta"): "${runtime.work}/changed-host.jar",
                ("local.review", "baseline"): "${baseline.dex}/application-host.jar"}
    actual = {(item.findtext(NS + "groupId"), item.findtext(NS + "artifactId")): item.findtext(NS + "systemPath") for item in systems}
    require(len(systems) == 2 and actual == expected, "Exactly the two existing baseline host system dependencies are required")
    for dependency in systems:
        deps.remove(dependency)
    for artifact, version, packaging, group in (
        ("nativeruntime", "4.14.1", None, "org.robolectric"),
        ("nativeruntime-dist-compat", "1.0.16", None, "org.robolectric"),
        ("android-all-instrumented", "15-robolectric-12650502-i7", None, "org.robolectric"),
    ):
        dependency = ET.SubElement(deps, NS + "dependency")
        for name, value in (("groupId", group), ("artifactId", artifact), ("version", version), ("scope", "test")):
            ET.SubElement(dependency, NS + name).text = value
        if packaging:
            ET.SubElement(dependency, NS + "type").text = packaging
    out.mkdir(parents=True)
    ET.ElementTree(root).write(out / "pom.xml", encoding="utf-8", xml_declaration=True)
    return out / "pom.xml"


def run(apk, bundles, jars, android, d8, dex2jar, maven, out, source, run_id):
    apk, bundles, jars, android, d8, dex2jar, maven, out = [p.resolve() for p in (apk, bundles, jars, android, d8, dex2jar, maven, out)]
    require(re.fullmatch("[0-9a-f]{40}", source) is not None and git("rev-parse", "HEAD") == source, "Exact producer commit required")
    require(git("branch", "--show-current") == BRANCH, "Existing authorized engineering branch required")
    require(os.environ.get("GITHUB_REPOSITORY") == "mahfouzhassine8-ops/project-infinity", "Expected GitHub repository required")
    require(os.environ.get("GITHUB_SHA") == source and os.environ.get("GITHUB_RUN_ID") == str(run_id) and run_id > 0, "Actual producer source/run binding required")
    require(not out.exists(), "Fresh producer directory required")
    baseline_info = read(HERE / "BASELINE.json")
    require(sha(apk) == baseline_info["APK_sha256"], "Exact accepted431 APK required")
    for name, pin in baseline_info["component_sha256"].items():
        require(sha(bundles / name) == pin, "Exact431 component required: " + name)
    require(sha(android) == "6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad", "Pinned Android compiler API required")
    require(sha(d8) == "305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5", "Pinned D8 required")
    require({p.name: sha(p) for p in jars.glob("*.jar")} == read(REPO / "repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json"), "Pinned owner tools required")
    require({p.name: sha(p) for p in (dex2jar / "lib").glob("*.jar")} == read(HERE / "DEX2JAR-LIB-PINS.json"), "Pinned dex2jar tools required")
    evidence = out / "evidence"
    evidence.mkdir(parents=True)
    steps = evidence / "steps"
    steps.mkdir()
    result = {"schema": 1, "status": "PRODUCER_IN_PROGRESS", "source": source, "run_id": run_id,
              "branch": BRANCH, "runtime_limits": "Host correctness/work counts only; physical Fold acceptance pending; no Android or shutdown tests"}

    def execute(name, command):
        command = [str(x) for x in command]
        save(steps / (name + "-COMMAND.json"), {"command": command, "source": source})
        with (steps / (name + ".txt")).open("w") as log:
            completed = subprocess.run(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT)
        save(steps / (name + "-RESULT.json"), {"exit_code": completed.returncode, "log_sha256": sha(steps / (name + ".txt"))})
        require(completed.returncode == 0, "Producer operation failed: " + name)

    try:
        from ci_host import local_repository
        repository = Path.home() / ".m2/repository"
        require(local_repository(maven) == repository.resolve(), "Use the standard shared Maven cache required by baseline AAR preparation")
        pom = bootstrap_pom(out / "bootstrap")
        execute("bootstrap-dependencies-no-tests", [maven, "-B", "-q", "-f", pom, "-Dmaven.repo.local=" + str(repository), "-DskipTests",
                "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:resolve"])
        baseline = out / "signed431-host"
        owner = out / "owner-build"
        trusted = out / "trusted-host"
        checks = out / "checks"
        components = out / "prepared-owners/components"
        execute("prepare-exact431-no-tests", [sys.executable, HERE / "qa/prepare_host.py", "--apk", apk, "--dex2jar", dex2jar, "--out", baseline])
        execute("compile-current-owner-no-apk", [sys.executable, HERE / "build.py", "--bundles", bundles, "--jars", jars,
                "--android", android, "--d8", d8, "--dex2jar", dex2jar, "--out", owner])
        execute("independent-current-owner-canonical", [sys.executable, HERE / "verify_owner_source.py", "--work", owner, "--bundles", bundles, "--jars", jars])
        execute("exact-current-owner-delta-from433", [sys.executable, HERE / "consolidated434/verify_from433.py",
                "--work", owner, "--out", owner / "EXACT433-DELTA.json"])
        execute("prepare-fresh-source-bound-host-no-tests", [sys.executable, HERE / "integrated-qa/prepare_release.py",
                "--apk", apk, "--baseline", baseline, "--build", owner, "--dex2jar", dex2jar, "--bundles", bundles,
                "--jars", jars, "--out", trusted, "--source", source])
        execute("selected-candidate-host-checks", [sys.executable, HERE / "ci_host.py", "--baseline", baseline,
                "--trusted-host", trusted, "--out", checks, "--maven", maven])
        host_result = read(checks / "HOST-RESULT.json")
        require(host_result["status"] == "PASS_FOCUSED_CANDIDATE_HOST_ONLY" and host_result["selected_JUnit_methods"] == 3
                and host_result["selected_groups"] == 1, "All3 current correction-specific actual-entry/guard checks must pass before packaging; retain prior bound visual/cache evidence")
        execute("package-tested-current-owners-no-apk", [sys.executable, HERE / "package_owners.py", "--bundles", bundles,
                "--work", owner, "--jars", jars, "--out", components, "--source", source])
        for src, name in ((owner / "BUILD.json", "BUILD.json"),
                          (owner / "EXACT433-DELTA.json", "EXACT433-DELTA.json"),
                          (owner / "PACKAGE-CANONICAL-RESULT.json", "PACKAGE-CANONICAL-RESULT.json"),
                          (components.parent / "CORRECTIVE-PRESERVATION.json", "CORRECTIVE-PRESERVATION.json"),
                          (trusted / "SOURCE-BINDINGS.json", "SOURCE-BINDINGS.json"),
                          (checks / "HOST-RESULT.json", "HOST-RESULT.json")):
            shutil.copyfile(src, evidence / name)
        selected = []
        test_sources = set()
        for group in host_result["groups"]:
            name = group["name"]
            src, dest = checks / name, evidence / "checks" / name
            dest.mkdir(parents=True)
            for item in src.iterdir():
                if item.is_file() and item.suffix in {".json", ".txt", ".xml"}:
                    shutil.copyfile(item, dest / item.name)
            for directory in ("measurements", "private-render", "target/surefire-reports"):
                if (src / directory).is_dir():
                    shutil.copytree(src / directory, dest / directory)
            inputs = read(src / "INPUTS.json")
            test_sources.update(inputs["test_sources"])
            reports = sorted((dest / "target/surefire-reports").glob("TEST-*.xml"))
            selected.append({"name": name, "status": "PASS", "selection_file": str((dest / "SELECTION.json").relative_to(evidence)),
                             "inputs_file": str((dest / "INPUTS.json").relative_to(evidence)),
                             "junit_files": [str(p.relative_to(evidence)) for p in reports]})
        sys.path.insert(0, str(HERE))
        import register_release
        tested = register_release.repository_source_files()
        paths = {HERE / name for name in ("run_producer.py", "ci_host.py", "CI-HOST-SCOPE.json", "PRODUCER-SCOPE.json",
            "qa/prepare_host.py", "cards-reuse/prepare_native.py", "cards-reuse/SCOPE.json", "layout-qa/prepare.py",
            "layout-qa/SCOPE.json", "render-qa/SCOPE.json", "settings-return/CobraSettingsReturnBaselineTest.java",
            "visual-closeout/qa/prepare.py", "visual-closeout/qa/SCOPE.json")}
        paths |= {REPO / name for name in test_sources}
        paths.add(HERE.parent / "tests/CobraLogoWorkTest.java")
        paths.add(ISO / "tests/pom.xml")
        paths |= set((HERE / "layout-qa/goldens/accepted431").glob("*.json"))
        paths |= set((HERE / "layout-qa/goldens/native431-theme-order").glob("*.json"))
        paths |= {HERE / name for name in ("presentation-qa/results/signed431-baseline/BASELINE.json",
                  "presentation-qa/results/signed431-bound-player-progress/BASELINE-PLAYER-PROGRESS.json")}
        paths |= set((HERE / "consolidated434/goldens433").glob("*"))
        paths |= {HERE / "consolidated434/SCOPE.json", HERE / "consolidated434/verify_from433.py"}
        tested.update({str(p.relative_to(REPO)): sha(p) for p in paths})
        for name, pin in tested.items():
            require(hashlib.sha256(subprocess.check_output(["git", "-C", str(REPO), "show", source + ":" + name])).hexdigest() == pin,
                    "Producer consumed uncommitted or changed source: " + name)
        result.update(status="PASS_CARDS_PREPARED_OWNERS", catalog_sha256=sha(components / "catalog.json"),
                      compiler_source_files=read(owner / "BUILD.json")["compiler_source_files"],
                      tested_source_files=tested, selected_checks=selected,
                      files={str(p.relative_to(evidence)): sha(p) for p in sorted(evidence.rglob("*")) if p.is_file()})
        save(evidence / "PRODUCER-RESULT.json", result)
        # Local protocol consumption checks source/DEX/package/selected JUnit;
        # successful GitHub-run/artifact-archive checks occur after upload.
        # This unapproved producer envelope intentionally retains immutable433
        # Infinity. It is not the current release authority and cannot be signed
        # or registered alone; the combined release validates current434 lineage
        # and merges the independently authenticated new Infinity owner.
        previous = register_release.signed432_authority()
        require(previous["candidate_versionCode"] == 2103433 and previous["generation"] == 18,
                "Exact immutable433 producer comparison required")
        register_release.validate_payload(previous, read(components / "catalog.json"), components)
        register_release.validate_ci(evidence, components / "catalog.json", run_id, source, previous)
    except Exception as error:
        result.update(status="FAILED_RECORDED_PRODUCER_OPERATION", error=str(error))
        (evidence / "ERROR.txt").write_text(traceback.format_exc())
        save(evidence / "PRODUCER-RESULT.json", result)
        # Preserve every available selected result even when no owners exist.
        if (out / "checks").is_dir() and not (evidence / "failed-checks").exists():
            failure_dir = evidence / "failed-checks"
            failure_dir.mkdir()
            for path in (out / "checks").rglob("*"):
                if path.is_file() and (path.suffix in {".json", ".xml", ".txt", ".png", ".dump", ".dumpstream"}) and "test-classes" not in path.parts:
                    dest = failure_dir / path.relative_to(out / "checks")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, dest)
        raise
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("apk", "bundles", "jars", "android", "d8", "dex2jar", "maven", "out"):
        parser.add_argument("--" + argument, type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    run(**vars(parser.parse_args()))
