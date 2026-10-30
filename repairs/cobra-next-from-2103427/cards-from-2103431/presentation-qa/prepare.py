"""Prepare only the selected actual-431 host fixture; never run Maven or an APK."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
EXPECTED_DEX = {
    "classes.dex": "07b94bfde6dbc3e3a6bfc8436ea65e6a67bdef5ca868379809e20f2fb7ce8efb",
    "classes2.dex": "2e8fa1ae27e670db0525d31a655e93d861893fa20316d5c54a4c6283a97ca304",
    "classes3.dex": "7e18d8092de33a4d44e299305965e9b9eb943372a9643452f6f78afe209fb215",
    "classes4.dex": "9f82b0420b32ad8bdda7ef042e44bb975c8c01663f66506eaf33d22123f49b82",
    "classes5.dex": "af03db41f53209de52f5d8609e411da49fee106d0fe544d6ea6e5d8230d88363",
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(baseline, out, selection=None):
    baseline, out = baseline.resolve(), out.resolve()
    if out.exists():
        raise RuntimeError("Fresh output required; no reuse or deletion")
    scope_path = selection.resolve() if selection is not None else HERE / "SCOPE.json"
    scope = json.loads(scope_path.read_text())
    receipt = json.loads((baseline / "INPUTS.json").read_text())
    if (receipt["source"] != scope["baseline_source"] or
            receipt["APK_sha256"] != scope["baseline_APK_sha256"] or
            receipt["DEX_sha256"] != EXPECTED_DEX):
        raise RuntimeError("Exact signed-431 baseline receipt required")
    for name, expected in EXPECTED_DEX.items():
        if sha(baseline / name) != expected:
            raise RuntimeError("Original signed-431 DEX changed: " + name)
        translated = baseline / (name.removesuffix(".dex") + "-translated.jar")
        if sha(translated) != receipt["translated_jar_SHA256"][name]:
            raise RuntimeError("Bound translation changed: " + name)
    out.mkdir(parents=True)
    test = HERE / "CobraProgrammePresentationBaselineTest.java"
    dest = out / "src/test/java/com/projectinfinity/kodi" / test.name
    dest.parent.mkdir(parents=True)
    shutil.copyfile(test, dest)
    # Reuse the existing complete host harness/dependencies, changing only this
    # selected test's input paths and output property. Never edit its baseline.
    for name in ("production.jar", "support.jar"):
        (out / name).symlink_to(baseline / name)
    (out / "android-test-libs").symlink_to(baseline / "android-test-libs", target_is_directory=True)
    pom = (baseline / "pom.xml").read_text()
    pom = pom.replace(escape(str(baseline)), escape(str(out)))
    pom = pom.replace("<projection.output>", "<presentation.output>")
    pom = pom.replace("</projection.output>", "</presentation.output>")
    if "projection.output" in pom or str(baseline) in pom:
        raise RuntimeError("Harness output paths not isolated")
    (out / "pom.xml").write_text(pom)
    inputs = {
        "status": "PREPARED_ONLY_NOT_EXECUTED",
        "scope": scope,
        "scope_sha256": sha(scope_path),
        "original_baseline_receipt": receipt,
        "baseline_receipt_sha256": sha(baseline / "INPUTS.json"),
        "DEX_sha256": EXPECTED_DEX,
        "test_sha256": sha(test),
        "prepare_sha256": sha(HERE / "prepare.py"),
        "production_jar_sha256": sha(baseline / "production.jar"),
        "support_jar_sha256": sha(baseline / "support.jar"),
        "pom_sha256": sha(out / "pom.xml"),
        "shutdown": "NOT_RUN",
        "production_changes": "NONE",
    }
    (out / "INPUTS.json").write_text(json.dumps(inputs, indent=2) + "\n")
    print("Prepared selected native-view write-count fixture; no execution")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    prepare(**vars(parser.parse_args()))
