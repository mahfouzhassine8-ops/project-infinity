"""Focused, read-only contract checks for source work based on signed 2103460.

Does not compile the Android native engine, run providers, or claim a signed APK.
Run on an actual checkout: python3 repairs/infinity-2103460-skin-script-20261106/test_source_contract.py
"""
from pathlib import Path
import ast
import importlib.util
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SKIN = ROOT / "repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz"
CC = ROOT / "repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter"
NATIVE = ROOT / "repairs/infinity-2103458-six-corrections-20261105/integration-048/native/xbmc/video/windows/GUIWindowVideoNav.cpp"


def check(name, ok):
    if not ok:
        raise AssertionError(name)
    print("PASS " + name)


def main():
    for path in (CC / "library_navigation.py", CC / "infinity_search.py",
                 CC / "default.py", SKIN / "resources/lib/infinity_library_navigation.py"):
        ast.parse(path.read_text(encoding="utf8"), filename=str(path))
    for path in (SKIN / "unified/Custom_1198_InfinityNav.xml",
                 SKIN / "unified/DialogVideoInfo.xml",
                 SKIN / "unified/Includes_InfinityMediaLists.xml"):
        ET.parse(path)
    check("4 Python source parses; 3 XML files parse", True)

    helper = (CC / "library_navigation.py").read_text(encoding="utf8")
    duplicate = (SKIN / "resources/lib/infinity_library_navigation.py").read_text(encoding="utf8")
    check("Command Center helper and skin helper identical", helper == duplicate)
    check("no automatic Android Downloads access warning", "Downloads access" not in helper
          and "infinity-downloads-only" in helper)
    check("only exact Home-menu URI targets", all(s in helper for s in (
        "plugin://script.infinity.commandcenter/?action=movies",
        "plugin://script.infinity.commandcenter/?action=tv")))

    spec = importlib.util.spec_from_file_location("scoped_helper", CC / "library_navigation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    class Kodi:
        def __init__(self):
            self.requests = []
        def executeJSONRPC(self, text):
            query = json.loads(text)
            self.requests.append(query)
            return json.dumps({"result": "OK"})
    class GUI:
        def Dialog(self):
            return self
        def ok(self, *unused):
            raise AssertionError("Unexpected GUI error")
    for action, params in (
        ("library-movies", ["plugin://script.infinity.commandcenter/?action=movies", "return"]),
        ("library-tv", ["plugin://script.infinity.commandcenter/?action=tv", "return"]),
        ("downloads", ["files", "return", "infinity-downloads-only"]),
    ):
        k = Kodi()
        check("Kodi dispatch " + action,
              module.run(action, k, GUI()) is True
              and len(k.requests) == 1
              and k.requests[0]["method"] == "GUI.ActivateWindow"
              and k.requests[0]["params"]["parameters"] == params)

    drawer = (SKIN / "unified/Custom_1198_InfinityNav.xml").read_text(encoding="utf8")
    check("Power below Explore, Discover and Refresh",
          drawer.index("<label>Power</label>") > drawer.index("<label>Discover</label>")
          and drawer.index("<label>Power</label>") > drawer.index("<label>Max</label>"))
    shared = ET.parse(SKIN / "unified/Includes_InfinityMediaLists.xml").getroot()
    guide = shared.find(".//include[@name='InfinityMedia_TouchGuide']/definition/control")
    check("shared instruction footer hidden", guide is not None and guide.findtext("visible") == "false")
    info = ET.parse(SKIN / "unified/DialogVideoInfo.xml").getroot()
    check("Info action IDs unchanged", all(len(info.findall(".//control[@id='%s']" % n)) == 1
                                          for n in ("8", "9012", "5", "106")))
    detail = (SKIN / "unified/DialogVideoInfo.xml").read_text(encoding="utf8")
    check("native Trailer and first-party More fallbacks are scoped",
          "PlayMedia($ESCINFO[ListItem.Trailer])" in detail
          and "RunScript(script.infinity.commandcenter,media-details)" in detail
          and "RunScript(script.extendedinfo" in detail)
    search = (CC / "infinity_search.py").read_text(encoding="utf8")
    check("Search result guard remains and fallback label corrected",
          "return provider,'state_changed',{},path" in search
          and "'Open provider search' if status=='state_changed'" in search)
    native = NATIVE.read_text(encoding="utf8")
    check("native filtering is Android/Infinity/Downloads-root gated",
          all(part in native for part in (
              "infinity-downloads-only", 'g_SkinInfo->ID() == "skin.infinity.diggz"',
              'GetProperty("Infinity.DownloadsOnly").asBoolean()',
              'URIUtils::PathEquals(items.GetPath(), "sources://video/")',
              'items.Remove(i);', '"infinity-library-direct"')))
    check("legacy source labels match reported 2103460 rows",
          all('StringUtils::EqualsNoCase(label, "' + name + '")' in native for name in (
              "The Crew Movies", "The Crew TVShows", "Download",
              "FREE99 Movies", "FREE99 TVShows",
              "Homelander Movies", "Homelander TV Shows",
              "Netflix Movies", "Netflix shows", "Scrubs Movies",
              "Scrubs TV Shows", "TMDBH Movies", "TMDBH TV Shows")))
    print("SOURCE CONTRACT PASS; ARM64 BUILD / FOLD / SIGNING NOT RUN")


if __name__ == "__main__":
    main()
