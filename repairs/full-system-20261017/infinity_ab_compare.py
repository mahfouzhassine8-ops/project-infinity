#!/usr/bin/env python3
"""Compare signed Infinity TEST4 and newer TEST3, without promoting either.

Read-only summary of original Android process test evidence. Missing failures
remain reported; host fixtures never become a physical Fold or release pass.
"""
import argparse
import json
from pathlib import Path

SHA = {
    "test4-reference": "bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286",
    "test3-current": "6e28bfea7cdb5e497ee21601a714e738db7a57edc3c5c0d29a9c19d461031854",
}
SEED = "4ec1e3b2cabb595d228bc07bae2c6b3073c5af12822c8e40b1ec505b00865bf8"
CASES = ("fresh", "cold", "core-initialized", "loaded")
REPORTS = {"fresh": "ANDROID-PROCESS-PROBE.json", "cold": "OBSERVER-UPGRADE-PROBE.json",
           "core-initialized": "OBSERVER-UPGRADE-PROBE.json",
           "loaded": "OBSERVER-UPGRADE-PROBE.json"}
RESULT = ("passed", "failed", "missing-report", "invalid-identity")


def parse_case(folder, variant, case):
    expected = REPORTS[case]
    matches = list(folder.rglob(expected)) if folder.is_dir() else []
    # The output path for each action is unique. No other candidate receipts
    # may satisfy a scenario, even if their API result looks green.
    if len(matches) != 1:
        return dict(status="missing-report", observed_count=len(matches),
                    problem="Exact Android proof missing or ambiguous")
    try:
        raw = json.loads(matches[0].read_text())
    except (OSError, ValueError):
        return dict(status="invalid-identity", problem="Corrupt Android proof")
    key = "apk_sha256" if case == "fresh" else "candidate_apk_sha256"
    problems = []
    if raw.get(key) != SHA[variant]:
        problems.append("Candidate signed APK SHA did not match")
    if case != "fresh":
        if raw.get("baseline_apk_sha256") != SEED:
            problems.append("Different seed APK; scenarios not comparable")
        wanted = "loaded" if case == "loaded" else "early"
        if raw.get("scenario") != wanted:
            problems.append("Wrong scenario type")
        wanted_boundary = "core-initialized" if case == "core-initialized" else "owner"
        if raw.get("early_boundary") != wanted_boundary:
            problems.append("Wrong startup boundary")
    if raw.get("physical_fold_accepted") is not False:
        problems.append("Emulator claims phone acceptance")
    if problems:
        return dict(status="invalid-identity", problems=problems)
    return dict(status="passed" if raw.get("passed") is True else "failed",
                failure=str(raw.get("failure", ""))[:400],
                receipt=expected, tested_sha256=SHA[variant],
                controlled_fixture_only=True)


def compare(root):
    root = Path(root)
    entries = {}
    for variant in SHA:
        entries[variant] = {}
        for case in CASES:
            folder = root / ("Infinity-AB-" + variant + "-" + case)
            entries[variant][case] = parse_case(folder, variant, case)
    overall_green = all(x["status"] == "passed" for cases in entries.values()
                        for x in cases.values())
    result = dict(
        scope="Same original signed-Infinity Android emulator probes, same synthetic-service seed",
        compared={"test4_reference": SHA["test4-reference"], "test3_current": SHA["test3-current"]},
        seed_apk_sha256=SEED, candidates_not_modified=True,
        test3_improvements_preserved=True,
        test4_is_reference_only=True, version_reverted=False,
        actual_diggz_full_stack_verified=False, physical_fold_accepted=False,
        final_lock_authorized=False, every_scenario_passed=overall_green,
        results=entries,
    )
    return result


def write_report(result, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "INFINITY-TEST4-VS-TEST3.json").write_text(json.dumps(result, indent=2)+"\n")
    lines = [
        "# Infinity TEST4 reference versus improved TEST3 candidate",
        "",
        "**No rollback, no APK rebuild, no original signer change.**",
        "TEST4 is the reference for the physical-Fold working Close; TEST3 retains all newer features.",
        "Both candidates use the same earlier 2103377 TEST3 seed APK and unchanged "
        "Android process tests. The seed is not the comparison target.",
        "",
        "| Scenario | Signed TEST4 reference | Signed TEST3 current |",
        "|---|---|---|",
    ]
    for case in CASES:
        a = result["results"]["test4-reference"][case]["status"]
        b = result["results"]["test3-current"][case]["status"]
        lines.append(f"| {case} | {a} | {b} |")
    lines.extend([
        "",
        "A red result is an observation, not proof that the physically accepted TEST4 was broken.",
        "These controlled addon/Estuary tests are NOT a real installed Diggz/Fold clone.",
        "Use identical complete skin and component inputs in a separate full-stack comparison.",
        "Neither version may be promoted or locked from this comparison.",
        "",
    ])
    (out / "INFINITY-TEST4-VS-TEST3.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    write_report(compare(args.input), args.out)
