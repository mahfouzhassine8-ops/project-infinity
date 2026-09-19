#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, re, zipfile

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "visual-theme.json"
ZIP_ROOT = "script.infinity.cobra.theme/resources/visual-theme.json"
PACKAGE = "Cobra-Liquid-Glass-HM-SAFE-v1.1.0.zip"
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
TOP = {"schema","scope","minimum_runtime","minimum_build","id","name","assets","base","variants"}
LAYER = {"colors","dimensions","numbers","copy","styles","images","scenes","guide_layouts"}
STYLE_FIELDS = {
    "fill","fill_end","stroke","stroke_width_dp","radius_dp","image","image_fit",
    "text","text_size_sp","font_family","font_asset","font_style","letter_spacing",
    "padding_dp","min_height_dp","elevation_dp","focus","pressed","selected",
    "width_dp","height_dp","margin_dp","margin_left_dp","margin_top_dp","margin_right_dp",
    "margin_bottom_dp","padding_left_dp","padding_top_dp","padding_right_dp","padding_bottom_dp",
    "weight","orientation","gravity","max_lines","alpha"
}
SAFE_STYLE_KEYS = {
    "screen","screen.header","screen.status","rail",
    "drawer.panel","drawer.header","drawer.items","drawer.power",
    "drawer.item.search","drawer.item.tv","drawer.item.movies","drawer.item.shows",
    "drawer.item.recordings","drawer.item.my_list","drawer.item.settings","drawer.item.view",
    "settings","sheet.row","sheet.detail","dialog.panel","dialog.button",
    "guide.shell","guide.directory","guide.details","guide.browser",
    "player.chrome","player.channels","chooser","chooser.card.infinity","chooser.card.cobra"
}
COPY_KEYS = {
    "chooser.label.brand","chooser.label.brand_tagline","chooser.label.title","chooser.label.personalization",
    "chooser.label.infinity_title","chooser.label.infinity_subtitle","chooser.label.cobra_title",
    "chooser.label.cobra_subtitle","chooser.label.footer_brand","chooser.label.footer_tagline","chooser.label.initials"
}
GEOMETRY_FIELDS = {
    "width_dp","height_dp","min_height_dp","margin_dp","margin_left_dp","margin_top_dp","margin_right_dp",
    "margin_bottom_dp","padding_dp","padding_left_dp","padding_top_dp","padding_right_dp","padding_bottom_dp",
    "weight","orientation","gravity","max_lines"
}

def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)

def validate_layer(layer: dict, where: str) -> None:
    if not isinstance(layer, dict):
        fail(where + " must be an object")
    unknown = set(layer) - LAYER
    if unknown:
        fail(where + " has unsupported groups: " + ", ".join(sorted(unknown)))
    for forbidden in ("dimensions","images","scenes","guide_layouts"):
        if layer.get(forbidden):
            fail(where + "/" + forbidden + " is forbidden in SAFE v1.1")

    colors = layer.get("colors", {})
    if not isinstance(colors, dict):
        fail(where + "/colors must be an object")
    for key, value in colors.items():
        if not isinstance(value, str) or not COLOR.fullmatch(value):
            fail(where + "/colors/" + key + " invalid")

    copy = layer.get("copy", {})
    if not isinstance(copy, dict):
        fail(where + "/copy must be an object")
    for key, value in copy.items():
        if key not in COPY_KEYS:
            fail(where + "/copy/" + key + " is not a wired chooser slot")
        if not isinstance(value, str) or not value.strip() or len(value) > 240 or "\x00" in value:
            fail(where + "/copy/" + key + " invalid")
        low = value.lower()
        if key.endswith("_subtitle") and ("live tv" in low or "2-in-1" in low or "2 in 1" in low):
            fail("legacy chooser wording is forbidden")
    if "chooser.label.initials" in copy and not re.fullmatch(r"[A-Za-z]{1,3}", copy["chooser.label.initials"]):
        fail("initials must be 1-3 letters")

    styles = layer.get("styles", {})
    if not isinstance(styles, dict):
        fail(where + "/styles must be an object")
    for key, style in styles.items():
        if key not in SAFE_STYLE_KEYS:
            fail(where + "/styles/" + key + " is not an explicitly scoped SAFE surface")
        if not isinstance(style, dict):
            fail(where + "/styles/" + key + " must be an object")
        unknown_style = set(style) - STYLE_FIELDS
        if unknown_style:
            fail(where + "/styles/" + key + " unsupported fields: " + ", ".join(sorted(unknown_style)))
        if set(style) & GEOMETRY_FIELDS:
            fail(where + "/styles/" + key + " may not change layout/touch geometry")
        if "image" in style or "font_asset" in style:
            fail(where + "/styles/" + key + " may not attach binary assets")
        for c in ("fill","fill_end","stroke","text","focus","pressed","selected"):
            if c in style and (not isinstance(style[c], str) or not COLOR.fullmatch(style[c])):
                fail(where + "/styles/" + key + "/" + c + " invalid")
        if "radius_dp" in style and not 0 <= float(style["radius_dp"]) <= 64:
            fail(where + "/styles/" + key + "/radius_dp out of range")
        if "stroke_width_dp" in style and not 0 <= float(style["stroke_width_dp"]) <= 3:
            fail(where + "/styles/" + key + "/stroke_width_dp out of range")
        if "elevation_dp" in style and not 0 <= float(style["elevation_dp"]) <= 6:
            fail(where + "/styles/" + key + "/elevation_dp out of range")

    numbers = layer.get("numbers", {})
    if not isinstance(numbers, dict):
        fail(where + "/numbers must be an object")
    for key, value in numbers.items():
        if key != "chooser.layout.motion_ms" or not isinstance(value,(int,float)) or not 0 <= value <= 250:
            fail(where + "/numbers/" + key + " invalid")

def load() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if set(data) - TOP:
        fail("unsupported top-level fields")
    if data.get("schema") != 2 or data.get("scope") != "cobra-presentation":
        fail("wrong Cobra visual schema/scope")
    if data.get("minimum_runtime") != 2 or int(data.get("minimum_build", 9999999)) > 2103160:
        fail("unsupported runtime requirement")
    if data.get("id") != "cobra.liquid-glass.hm.safe.v1":
        fail("SAFE theme id mismatch")
    if data.get("assets") != {}:
        fail("SAFE v1.1 must contain zero binary assets")
    variants = data.get("variants", {})
    if set(variants) != {"light","dark","oled"}:
        fail("SAFE v1.1 supports exactly light/dark/oled appearance variants")
    validate_layer(data["base"], "base")
    for name, layer in variants.items():
        validate_layer(layer, "variant:" + name)
    return data

def build(out: Path) -> None:
    data = load()
    out.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    package = out / PACKAGE
    info = zipfile.ZipInfo(ZIP_ROOT, date_time=(2026,9,19,0,0,0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(package, "w") as zf:
        zf.writestr(info, raw)
    with zipfile.ZipFile(package, "r") as zf:
        if zf.namelist() != [ZIP_ROOT]:
            fail("ZIP must contain only the data manifest")
        if json.loads(zf.read(ZIP_ROOT).decode("utf-8")) != data:
            fail("ZIP manifest round-trip mismatch")
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    report = {
        "theme": data["id"],
        "name": data["name"],
        "version": "1.1.0-safe",
        "sha256": digest,
        "zip": package.name,
        "base_commit": "0560b18c497e9861864126d96f9b784e488ebe32",
        "data_only": True,
        "scoped_styles_only": True,
        "global_styles_forbidden": True,
        "layout_geometry_changed": False,
        "binary_assets": 0,
        "native_engine_changed": False,
        "player_ownership_changed": False,
        "timeshift_rewind_changed": False,
        "pip_changed": False
    }
    (out/"build-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    (out/"SHA256SUMS").write_text(digest+"  "+package.name+"\n",encoding="utf-8")
    print("PASS:", package)
    print("SHA-256:", digest)

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=ROOT/"dist")
    build(p.parse_args().out)
