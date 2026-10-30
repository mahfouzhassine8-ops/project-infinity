"""Strict one-Activity host overlay; no APK, original431 file or app mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
from prepare import prepare, sha

HERE = Path(__file__).resolve().parent
ACTIVITY = "com/projectinfinity/kodi/InfinityLiveActivity.class"
TICK = "private cobraRefreshProgrammeLabels()V"
FINAL = "private cobraRefreshModeDetails()V"
DEX_SHA = "6354ea6cdc1dfde1745b4463d1e8b17e714ac3a6b52119f597b32c18deab746d"


def methods(text):
    return {m[1]:m[0] + "\n" for m in re.finditer(r"^\.method ([^\n]+)\n.*?^\.end method", text, re.M | re.S)}


def classes(path):
    with ZipFile(path) as jar:
        return {n:jar.read(n) for n in jar.namelist() if n.endswith(".class")}


def candidate(baseline, prototype, prototype_smali, jars, dex2jar, reference, reference_player, out):
    baseline, prototype, prototype_smali, jars, dex2jar, out = (
        p.resolve() for p in (baseline, prototype, prototype_smali, jars, dex2jar, out))
    reference, reference_player = reference.resolve(), reference_player.resolve()
    selection = json.loads((HERE / "CANDIDATE-SCOPE.json").read_text())
    if sha(prototype) != DEX_SHA:
        raise RuntimeError("Only root-reviewed single-method prototype admitted")
    tool_pins = {
        "baksmali-2.5.2.jar":"1ed236266d7dc4907aade0b19a34f77efac25342b63c8ace52e579039941b389",
        "dexlib2-2.5.2.jar":"5a5c8982d8bd7d6e3bb1a0713049e3c78b719ec32b20f6b619885cec30a0dd61",
    }
    for name, pin in tool_pins.items():
        if sha(jars / name) != pin:
            raise RuntimeError("Trusted tool changed: " + name)
    prepare(baseline, out, HERE / "CANDIDATE-SCOPE.json")
    accepted = out / "accepted-smali"
    subprocess.run(["java", "-cp", str(jars / "*"), "org.jf.baksmali.Main", "disassemble",
                    "--sequential-labels", "--classes", "Lcom/projectinfinity/kodi/InfinityLiveActivity;",
                    str(baseline / "classes4.dex"), "-o", str(accepted)], check=True)
    original_path = accepted / "com/projectinfinity/kodi/InfinityLiveActivity.smali"
    before_text, after_text = original_path.read_text(), prototype_smali.read_text()
    before, after = methods(before_text), methods(after_text)
    if set(before) != set(after) or {n for n in before if before[n] != after[n]} != {TICK}:
        raise RuntimeError("Only exact selected tick may change")
    strip = lambda s:re.sub(r"^\.method [^\n]+\n.*?^\.end method", "", s, flags=re.M | re.S)
    if strip(before_text) != strip(after_text):
        raise RuntimeError("Class metadata/fields changed")
    if hashlib.sha256(before[TICK].encode()).hexdigest() != selection["original_method_sha256"]:
        raise RuntimeError("Original tick preimage changed")
    if hashlib.sha256(before[FINAL].encode()).hexdigest() != selection["frozen_final_writer_sha256"]:
        raise RuntimeError("Final writer preimage changed")
    errors = out / "translation-errors"
    errors.mkdir()
    translated = out / "prototype-Activity.jar"
    subprocess.run(["java", "-cp", str(dex2jar / "lib/*"), "com.googlecode.dex2jar.tools.Dex2jarCmd",
                    str(prototype), "-o", str(translated), "-e", str(errors / "prototype.zip")], check=True)
    if list(errors.iterdir()):
        raise RuntimeError("Actual prototype translation errors refused")
    overlay = classes(translated)
    if set(overlay) != {ACTIVITY}:
        raise RuntimeError("Prototype must contain only Activity class")
    original = classes(baseline / "production.jar")
    (out / "production.jar").unlink()  # Remove only our fresh baseline symlink.
    with ZipFile(out / "production.jar", "w", ZIP_DEFLATED) as merged:
        for name, data in original.items():
            merged.writestr(name, overlay.get(name, data))
    revised = classes(out / "production.jar")
    changed = sorted(n for n in original if original[n] != revised[n])
    if set(original) != set(revised) or changed != [ACTIVITY]:
        raise RuntimeError("All other translated production classes must stay byte-exact")
    if sha(out / "support.jar") != sha(baseline / "support.jar"):
        raise RuntimeError("Original support JAR changed")
    # Require genuine accepted full-tick references, not a candidate result or
    # the direct-details reference whose player labels were intentionally idle.
    base_report = json.loads(reference.read_text())
    player_report = json.loads(reference_player.read_text())
    if base_report["status"] != "PASS_ACTUAL_NATIVE_WRITE_COUNTS_AND_FINAL_STATE" or base_report["case_count"] != 12:
        raise RuntimeError("Original accepted431 twelve-case reference required")
    if player_report["status"] != "PASS_ACTUAL_SIGNED431_BOUND_PLAYER_PROGRESS_BASELINE" or player_report["case_count"] != 3:
        raise RuntimeError("Genuine accepted431 bound-progress reference required")
    pom = (out / "pom.xml").read_text()
    props = ("<presentation.reference.baseline>" + escape(str(reference)) + "</presentation.reference.baseline>"
             "<presentation.reference.player>" + escape(str(reference_player)) + "</presentation.reference.player>")
    (out / "pom.xml").write_text(pom.replace("</systemPropertyVariables>", props + "</systemPropertyVariables>"))
    record = json.loads((out / "INPUTS.json").read_text())
    record.update({
        "phase":"UNSIGNED_SINGLE_METHOD_PRESENTATION_PROTOTYPE_NO_APK",
        "prototype_DEX_sha256":sha(prototype),
        "prototype_smali_sha256":sha(prototype_smali),
        "fresh_accepted_smali_sha256":sha(original_path),
        "changed_methods":[TICK],
        "method_count":len(before),
        "all_other_canonical_method_bodies_and_class_metadata":"EXACT",
        "selected_original_method_sha256":selection["original_method_sha256"],
        "selected_revised_method_sha256":hashlib.sha256(after[TICK].encode()).hexdigest(),
        "frozen_final_writer_sha256":selection["frozen_final_writer_sha256"],
        "register_review_sha256":sha(HERE / "REGISTER-LIVENESS-REVIEW.md"),
        "candidate_prepare_sha256":sha(HERE / "prepare_candidate.py"),
        "parent_patch_source_sha256":sha(HERE.parent / "presentation_patch.py"),
        "tool_pins":tool_pins,
        "dex2jar_libraries":{p.name:sha(p) for p in sorted((dex2jar / "lib").glob("*.jar"))},
        "changed_translated_classes":changed,
        "unchanged_translated_class_count":len(original)-1,
        "candidate_production_jar_sha256":sha(out / "production.jar"),
        "support_jar_unchanged":True,
        "accepted431_full_tick_reference_sha256":sha(reference),
        "accepted431_bound_progress_reference_sha256":sha(reference_player),
        "pom_sha256":sha(out / "pom.xml"),
        "application_APK":"NOT_BUILT_OR_INSTALLED",
        "shutdown":"NOT_RUN",
    })
    (out / "INPUTS.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Prepared strict single-Activity presentation overlay; no test or APK run")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("baseline", "prototype", "prototype-smali", "jars", "dex2jar", "reference", "reference-player", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    candidate(**vars(parser.parse_args()))
