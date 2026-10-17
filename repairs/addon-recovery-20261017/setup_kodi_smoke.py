"""Create an isolated runner profile and two harmless video add-on fixtures."""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
profile = Path.home() / ".kodi/userdata"
addons = profile.parent / "addons"
profile.mkdir(parents=True, exist_ok=True)
addons.mkdir(exist_ok=True)
shutil.copytree(HERE / "addon", addons / "script.infinity.addonrecovery", dirs_exist_ok=True)
for number in (1, 2):
    addon_id = "plugin.video.infinityrecoveryfixture" + str(number)
    folder = addons / addon_id
    folder.mkdir(exist_ok=True)
    (folder / "addon.xml").write_text('<addon id="' + addon_id + '" name="Recovery Fixture ' + str(number) + '" version="1.0.0" provider-name="Infinity CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.pluginsource" library="default.py"><provides>video</provides></extension><extension point="xbmc.addon.metadata"><summary lang="en_GB">Offline enable-state fixture</summary><description lang="en_GB">Disposable fixture only</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (folder / "default.py").write_text("import sys,xbmcplugin\nxbmcplugin.endOfDirectory(int(sys.argv[1]))\n")
    data = profile / "addon_data" / addon_id
    data.mkdir(parents=True, exist_ok=True)
    (data / "settings.xml").write_text('<settings><setting id="retained">fixture-' + str(number) + '</setting></settings>\n')
keymaps = profile / "keymaps"
keymaps.mkdir(exist_ok=True)
root = ET.Element("keymap")
keyboard = ET.SubElement(ET.SubElement(root, "global"), "keyboard")
ET.SubElement(keyboard, "f12").text = "RunScript(" + str(HERE / "kodi_smoke.py") + ")"
ET.ElementTree(root).write(keymaps / "recovery-smoke.xml", encoding="unicode")
