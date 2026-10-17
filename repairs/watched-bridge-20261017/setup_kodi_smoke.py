"""Disposable Linux Kodi profile with actual CC code and projected row controls."""
from pathlib import Path
import copy
import importlib.util
import shutil
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
profile = Path.home() / ".kodi/userdata"
addons = profile.parent / "addons"
profile.mkdir(parents=True, exist_ok=True); addons.mkdir(exist_ok=True)
source = HERE.parent / "android-checkpoint-shutdown/installed/build.py"
spec = importlib.util.spec_from_file_location("verified_cc_fixture", source)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
_, verified = module.sources("script.infinity.commandcenter")
cc = addons / "script.infinity.commandcenter"; cc.mkdir(exist_ok=True)
for name, data in verified.items():
    (cc / name).write_bytes(data)
shutil.copytree(HERE / "addon", addons / "script.infinity.watchedbridge", dirs_exist_ok=True)
fixture = profile / "watched-render-fixture"
with zipfile.ZipFile(HERE / "fixtures/skin-row-projection.zip") as archive:
    assert archive.testzip() is None
    archive.extractall(fixture)
estuary = Path("/usr/share/kodi/addons/skin.estuary")
if not estuary.is_dir():
    raise RuntimeError("Native Estuary fixture base unavailable")
for version in ("before", "after"):
    addon_id = "skin.infinity.rowverify." + version
    root = addons / addon_id
    # Dereference valid distro links so relocating the test skin preserves its
    # fonts. The production row faces below are always the exact source files.
    shutil.copytree(estuary, root, dirs_exist_ok=True, ignore_dangling_symlinks=True)
    tree = ET.parse(root / "addon.xml")
    manifest = tree.getroot(); manifest.set("id", addon_id); manifest.set("name", "Infinity Row Verification " + version)
    manifest.set("version", "1.0.0")
    tree.write(root / "addon.xml", encoding="utf-8", xml_declaration=True)
    xml = root / manifest.find("./extension[@point='xbmc.gui.skin']/res").get("folder")
    shutil.copyfile(fixture / version / "InfinityFixture.xml", xml / "InfinityFixture.xml")
    includes = ET.parse(xml / "Includes.xml"); ET.SubElement(includes.getroot(), "include", file="InfinityFixture.xml")
    includes.write(xml / "Includes.xml", encoding="utf-8", xml_declaration=True)
    fonts = ET.parse(xml / "Font.xml")
    for fontset in fonts.getroot().findall("fontset"):
        for font in ET.parse(fixture / version / "Fonts.xml").getroot():
            fontset.append(copy.deepcopy(font))
    fonts.write(xml / "Font.xml", encoding="utf-8", xml_declaration=True)
    for font in (fixture / "fonts").iterdir():
        target = root / "fonts" / font.name
        if target.is_symlink(): target.unlink()
        shutil.copyfile(font, target)
    shutil.copytree(fixture / version / "media", root / "media", dirs_exist_ok=True)
    (xml / "Home.xml").write_text('''<?xml version="1.0" encoding="UTF-8"?>
<window><defaultcontrol always="true">50</defaultcontrol><controls>
<control type="image"><left>0</left><top>0</top><width>1920</width><height>1080</height><texture colordiffuse="$VAR[InfinityLegacyBase]">infinity_ui/contract_white.png</texture></control>
<include condition="!String.IsEqual(Skin.String(Infinity.HomeView),regular)">InfinityPluginDirectoryCompact</include>
<include condition="String.IsEqual(Skin.String(Infinity.HomeView),regular)">InfinityPluginDirectoryRegular</include>
</controls></window>''')
keymaps = profile / "keymaps"; keymaps.mkdir(exist_ok=True)
root = ET.Element("keymap"); keyboard = ET.SubElement(ET.SubElement(root, "global"), "keyboard")
ET.SubElement(keyboard, "f12").text = "RunScript(" + str(HERE / "kodi_smoke.py") + ")"
ET.ElementTree(root).write(keymaps / "watched-verification.xml", encoding="unicode")
