#!/usr/bin/env python3
"""Fast, read-only Infinity whole-stack stability audit.

This intentionally does not build Kodi or mutate product source. It inventories the
repo, compares first-party add-on source against the stability baseline, checks for
legacy mutation contracts, and can verify the externally locked skin ZIP when supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
import tempfile
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "stability" / "infinity-stability-baseline.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def issue(bucket, severity, code, detail, **extra):
    item = {"severity": severity, "code": code, "detail": detail}
    item.update(extra)
    bucket.append(item)


def parse_addon_manifests(root: Path, issues):
    addons = {}
    addons_root = root / "addons"
    if not addons_root.exists():
        issue(issues, "error", "ADDONS_DIR_MISSING", "Repository addons/ directory is missing")
        return addons
    for manifest in sorted(addons_root.glob("*/addon.xml")):
        try:
            node = ET.parse(manifest).getroot()
        except ET.ParseError as exc:
            issue(issues, "error", "ADDON_XML_PARSE", f"{manifest.relative_to(root)}: {exc}")
            continue
        addon_id = node.attrib.get("id", "")
        version = node.attrib.get("version", "")
        if not addon_id:
            issue(issues, "error", "ADDON_ID_MISSING", str(manifest.relative_to(root)))
            continue
        if addon_id in addons:
            issue(issues, "error", "DUPLICATE_ADDON_ID", addon_id)
        service_entries = [e for e in node.findall("extension") if e.attrib.get("point") == "xbmc.service"]
        addons[addon_id] = {
            "version": version,
            "path": str(manifest.parent.relative_to(root)),
            "service_entries": len(service_entries),
        }
    return addons


def compile_addon_python(root: Path, issues):
    checked = 0
    for path in sorted((root / "addons").glob("**/*.py")):
        if "__pycache__" in path.parts:
            continue
        checked += 1
        try:
            py_compile.compile(
                str(path),
                doraise=True,
                cfile=str(Path(tempfile.gettempdir()) / (path.name + ".pyc")),
            )
        except py_compile.PyCompileError as exc:
            issue(issues, "error", "PYTHON_COMPILE", f"{path.relative_to(root)}: {exc.msg}")
    return checked


def scan_tracked_tree(root: Path, issues):
    tracked_cache = [str(p.relative_to(root)) for p in root.glob("addons/**/__pycache__/*")]
    tracked_cache += [str(p.relative_to(root)) for p in root.glob("addons/**/*.pyc")]
    if tracked_cache:
        issue(
            issues,
            "error",
            "PYTHON_CACHE_SHIPPED",
            "Python cache artifacts found under addons/",
            files=tracked_cache[:50],
        )

    active_legacy = []
    for path in sorted((root / "addons").glob("**/*")):
        if not path.is_file() or path.suffix.lower() not in {".py", ".xml", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "skin.xenon2" in text:
            active_legacy.append(str(path.relative_to(root)))
    if active_legacy:
        issue(
            issues,
            "blocker",
            "FOREIGN_SKIN_ACTIVE_REFERENCE",
            "Active first-party add-on source still references skin.xenon2",
            files=active_legacy,
        )


def compare_companions(baseline, addons, issues):
    for target in baseline["companions"]:
        addon_id = target["addon_id"]
        expected = target["target_version"]
        actual = addons.get(addon_id)
        required = bool(target.get("repo_source_required"))
        if actual is None:
            severity = "blocker" if required else "info"
            issue(
                issues,
                severity,
                "COMPANION_SOURCE_MISSING" if required else "EXTERNAL_COMPANION",
                f"{addon_id} {expected} is not present as repository source",
                addon_id=addon_id,
                expected=expected,
            )
            continue
        if actual["version"] != expected:
            issue(
                issues,
                "blocker",
                "COMPANION_SOURCE_DRIFT",
                f"{addon_id}: repo={actual['version']} target={expected}",
                addon_id=addon_id,
                actual=actual["version"],
                expected=expected,
            )

        if addon_id == "service.infinity.compat":
            contract = target.get("contract", {})
            if contract.get("single_startup_service") and actual["service_entries"] != 1:
                issue(
                    issues,
                    "blocker",
                    "COMPAT_SERVICE_TOPOLOGY_DRIFT",
                    f"Compatibility Guard declares {actual['service_entries']} xbmc.service entries; target contract requires exactly 1",
                )


def scan_legacy_contracts(root: Path, issues):
    compat_dir = root / "addons" / "service.infinity.compat"
    mutation_tokens = {
        "ensure_player_files(": "legacy player-file reassertion",
        "ensure_theme_files(": "legacy theme-file reassertion",
    }
    for path in sorted(compat_dir.glob("**/*.py")) if compat_dir.exists() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token, label in mutation_tokens.items():
            if token in text:
                issue(
                    issues,
                    "blocker",
                    "COMPAT_MUTATION_CONTRACT",
                    f"{path.relative_to(root)} contains {label} token {token!r}",
                )

    legacy_test = root / "tests" / "infinity_compat" / "test_candidate_107.py"
    if legacy_test.exists():
        text = legacy_test.read_text(encoding="utf-8", errors="ignore")
        if "compat_runtime.ensure_player_files(" in text or "compat_runtime.ensure_theme_files(" in text:
            issue(
                issues,
                "blocker",
                "LEGACY_TEST_EXPECTATION",
                "tests/infinity_compat/test_candidate_107.py still invokes legacy file-mutation behavior that conflicts with the clean-core Compat contract",
            )

    support_test = root / "tests" / "infinity_compat" / "test_support.py"
    if support_test.exists() and "skin.xenon2" in support_test.read_text(encoding="utf-8", errors="ignore"):
        issue(
            issues,
            "warning",
            "SUPPORT_TEST_LEGACY_FIXTURE",
            "Support Exporter tests still use skin.xenon2 fixtures; current-skin 0.3.1 coverage is required",
        )


def verify_provider_inventory(root: Path, baseline, issues):
    addons_txt = root / "kodi-config" / "addons.txt"
    if addons_txt.exists():
        active = [
            line.strip()
            for line in addons_txt.read_text(errors="ignore").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not active:
            issue(
                issues,
                "warning",
                "PROVIDER_INSTALL_MANIFEST_EMPTY",
                "kodi-config/addons.txt contains no active add-on entries; provider certification relies on the explicit stability inventory",
            )
    else:
        issue(issues, "warning", "PROVIDER_INSTALL_MANIFEST_MISSING", "kodi-config/addons.txt is missing")
    if len(baseline.get("providers", [])) < 1:
        issue(issues, "error", "PROVIDER_BASELINE_EMPTY", "No providers declared in stability baseline")


def verify_skin_zip(path: Path, baseline, issues):
    expected = baseline["locked_skin"]
    result = {"path": str(path), "expected_sha256": expected["sha256"]}
    if not path.exists():
        issue(issues, "error", "SKIN_ZIP_MISSING", str(path))
        result["verified"] = False
        return result
    actual_hash = sha256_file(path)
    result["actual_sha256"] = actual_hash
    if actual_hash != expected["sha256"]:
        issue(issues, "error", "SKIN_SHA_MISMATCH", f"locked skin SHA mismatch: {actual_hash}")
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad:
            issue(issues, "error", "SKIN_ZIP_CRC", f"corrupt member: {bad}")
        names = zf.namelist()
        roots = sorted({n.split("/", 1)[0] for n in names if "/" in n})
        if len(roots) != 1:
            issue(issues, "error", "SKIN_ROOT_LAYOUT", f"expected one skin root, found {roots}")
            root_name = roots[0] if roots else ""
        else:
            root_name = roots[0]
        addon_name = f"{root_name}/addon.xml"
        if addon_name not in names:
            issue(issues, "error", "SKIN_ADDON_XML_MISSING", addon_name)
        else:
            addon = ET.fromstring(zf.read(addon_name))
            if addon.attrib.get("id") != expected["addon_id"] or addon.attrib.get("version") != expected["version"]:
                issue(
                    issues,
                    "error",
                    "SKIN_IDENTITY_MISMATCH",
                    f"zip id/version={addon.attrib.get('id')}/{addon.attrib.get('version')} expected={expected['addon_id']}/{expected['version']}",
                )
        xml_names = [n for n in names if n.startswith(root_name + "/") and n.endswith(".xml")]
        parse_errors = []
        for name in xml_names:
            try:
                ET.fromstring(zf.read(name))
            except ET.ParseError as exc:
                parse_errors.append({"file": name, "error": str(exc)})
        if parse_errors:
            issue(
                issues,
                "error",
                "SKIN_XML_PARSE",
                f"{len(parse_errors)} skin XML parse errors",
                samples=parse_errors[:20],
            )
        if len(xml_names) != expected["xml_count"]:
            issue(
                issues,
                "warning",
                "SKIN_XML_COUNT_DRIFT",
                f"skin XML count={len(xml_names)} expected={expected['xml_count']}",
            )
        blob = b"\n".join(
            zf.read(n)
            for n in names
            if n.endswith((".xml", ".json", ".txt")) and zf.getinfo(n).file_size < 2_000_000
        )
        text = blob.decode("utf-8", errors="ignore")
        missing_providers = [p for p in baseline["providers"] if p not in text]
        if missing_providers:
            issue(
                issues,
                "blocker",
                "SKIN_PROVIDER_REFERENCE_MISSING",
                "locked skin does not reference every provider in the stability inventory",
                providers=missing_providers,
            )
        for profile in expected["profiles"]:
            for rel in (
                "Custom_1191_InfinitySystemHub.xml",
                "Custom_1198_InfinityNav.xml",
                "Home.xml",
                "VideoOSD.xml",
                "AddonBrowser.xml",
                "FileBrowser.xml",
            ):
                member = f"{root_name}/{profile}/{rel}"
                if member not in names:
                    issue(issues, "error", "SKIN_PROFILE_CONTRACT_MISSING", member)
        result.update(
            {
                "verified": actual_hash == expected["sha256"] and not bad and not parse_errors,
                "xml_count": len(xml_names),
                "root": root_name,
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--skin-zip", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "stability-report.json")
    parser.add_argument("--strict", action="store_true", help="Return non-zero while blockers remain")
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text())
    issues = []
    addons = parse_addon_manifests(ROOT, issues)
    python_files = compile_addon_python(ROOT, issues)
    scan_tracked_tree(ROOT, issues)
    compare_companions(baseline, addons, issues)
    scan_legacy_contracts(ROOT, issues)
    verify_provider_inventory(ROOT, baseline, issues)

    skin = None
    if args.skin_zip:
        skin = verify_skin_zip(args.skin_zip, baseline, issues)
    else:
        issue(
            issues,
            "info",
            "EXTERNAL_SKIN_NOT_SUPPLIED",
            "Locked skin ZIP not supplied to this run; hash/XML/provider verification skipped",
        )

    counts = {
        level: sum(i["severity"] == level for i in issues)
        for level in ("error", "blocker", "warning", "info")
    }
    try:
        baseline_label = str(args.baseline.relative_to(ROOT))
    except ValueError:
        baseline_label = str(args.baseline)
    report = {
        "schema": 1,
        "baseline": baseline_label,
        "git_base": baseline["git_base"],
        "repo_addons": addons,
        "compiled_addon_python_files": python_files,
        "provider_count": len(baseline.get("providers", [])),
        "locked_skin": skin,
        "counts": counts,
        "certifiable": counts["error"] == 0 and counts["blocker"] == 0,
        "issues": issues,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"certifiable": report["certifiable"], "counts": counts}, sort_keys=True))
    for item in issues:
        print(f"[{item['severity'].upper()}] {item['code']}: {item['detail']}")

    if counts["error"]:
        return 2
    if args.strict and counts["blocker"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
