# SPDX-License-Identifier: GPL-2.0-or-later
"""Transactional in-place Infinity skin 1.0.5.181 -> 1.0.5.182 Resume Hub 2 upgrade.

The APK updates Command Center first. Command Center then upgrades only the approved
Home/menu data-source files in the already-installed Infinity skin. Player XML, geometry,
providers and native code are untouched.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET

import xbmc
import xbmcvfs

FROM_VERSION = "1.0.5.181"
TO_VERSION = "1.0.5.182"
COMMAND_VERSION = "0.3.5.19"
HOME_DIRS = (
    "16x9","20x9","6x5","5x6","portrait","fallback",
    "responsive/base","responsive/wide","responsive/ultrawide","responsive/landscape",
    "responsive/square","responsive/portrait","responsive/tall",
)
INCLUDE_DIRS = (
    "16x9","fallback","responsive/base","responsive/wide","responsive/ultrawide",
    "responsive/landscape","responsive/square","responsive/portrait","responsive/tall",
)

VARIABLES = r'''
  <!-- Infinity 1.0.5.182 / Resume Hub 2: Trakt and local Infinity sections reuse the same
       approved view-mode geometry. Only their data source changes. -->
  <variable name="InfinityMoviesPrimaryPath">
    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=movie&amp;bucket=watchlist&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>
    <value>plugin://plugin.video.umbrella/?action=movies&amp;url=traktwatchlist&amp;folderName=Trakt+Watchlist&amp;reload=$INFO[Window(Home).Property(widgetreload-movies)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>
  </variable>
  <variable name="InfinityMoviesSecondaryPath">
    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=movie&amp;bucket=collection&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>
    <value>plugin://plugin.video.umbrella/?action=movies&amp;url=traktcollection&amp;folderName=Collection&amp;reload=$INFO[Window(Home).Property(widgetreload-movies)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>
  </variable>
  <variable name="InfinityTVPrimaryPath">
    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=tv&amp;bucket=next&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>
    <value>plugin://plugin.video.umbrella/?action=calendar&amp;url=progress&amp;folderName=Progress+Episodes&amp;reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>
  </variable>
  <variable name="InfinityTVSecondaryPath">
    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=tv&amp;bucket=progress&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>
    <value>plugin://plugin.video.umbrella/?action=shows_progress&amp;url=progresstv&amp;folderName=Progress+Shows&amp;reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>
  </variable>
  <variable name="InfinityResumeHubWatchedState">
    <value condition="String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),true)">true</value>
    <value condition="Integer.IsGreater(ListItem.PlayCount,0)">true</value>
    <value>false</value>
  </variable>
'''

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _version(text: str) -> str:
    m = re.search(r'<addon\b[^>]*\bversion="([^"]+)"', text)
    return m.group(1) if m else ""

def _patch_home(text: str) -> str:
    if "<label>INFINITY MOVIES</label>" in text and "<label>INFINITY TV</label>" in text:
        return text

    trakt_movies = '''          <item>
            <label>TRAKT MOVIES</label>
            <property name="section">traktmovies</property>
            <property name="submenuVisibility">traktmovies</property>
            <property name="widgetName">Umbrella - Trakt Watchlist</property>
            <property name="widgetName.2">Umbrella - Collection</property>
            <onclick>ActivateWindow(Videos,"plugin://plugin.video.umbrella/?action=mymovieNavigator&amp;folderName=My+Movies",return)</onclick>
            <icon>infinity_ui/icons/trakt.png</icon>
          </item>'''
    trakt_movies_new = trakt_movies.replace(
        '<property name="submenuVisibility">traktmovies</property>',
        '<property name="submenuVisibility">traktmovies</property>\n            <property name="hubsource">trakt</property>',
    )
    if text.count(trakt_movies) != 1:
        raise RuntimeError("Unexpected Trakt Movies menu anchor")
    text = text.replace(trakt_movies, trakt_movies_new, 1)

    trakt_tv = '''          <item>
            <label>TRAKT TV</label>
            <property name="section">trakttv</property>
            <property name="submenuVisibility">trakttv</property>
            <property name="widgetName">Umbrella - Next Episodes</property>
            <property name="widgetName.2">Umbrella - Progress Shows</property>
            <onclick>ActivateWindow(Videos,"plugin://plugin.video.umbrella/?action=mytvNavigator&amp;folderName=My+TV+Shows",return)</onclick>
            <icon>infinity_ui/icons/trakt.png</icon>
          </item>'''
    trakt_tv_new = trakt_tv.replace(
        '<property name="submenuVisibility">trakttv</property>',
        '<property name="submenuVisibility">trakttv</property>\n            <property name="hubsource">trakt</property>',
    )
    infinity = '''          <item>
            <label>INFINITY MOVIES</label>
            <property name="section">traktmovies</property>
            <property name="submenuVisibility">infinitymovies</property>
            <property name="hubsource">infinity</property>
            <property name="widgetName">Infinity - Watchlist</property>
            <property name="widgetName.2">Infinity - Collection</property>
            <onclick>ActivateWindow(Videos,"plugin://script.infinity.commandcenter/?action=movies",return)</onclick>
            <icon>infinity_ui/icons/movie.png</icon>
          </item>
          <item>
            <label>INFINITY TV</label>
            <property name="section">trakttv</property>
            <property name="submenuVisibility">infinitytv</property>
            <property name="hubsource">infinity</property>
            <property name="widgetName">Infinity - Next Episodes</property>
            <property name="widgetName.2">Infinity - Progress Shows</property>
            <onclick>ActivateWindow(Videos,"plugin://script.infinity.commandcenter/?action=tv",return)</onclick>
            <icon>infinity_ui/icons/tv.png</icon>
          </item>'''
    if text.count(trakt_tv) != 1:
        raise RuntimeError("Unexpected Trakt TV menu anchor")
    text = text.replace(trakt_tv, trakt_tv_new + "\n" + infinity, 1)

    old = "String.IsEqual(ListItem.Property(section),Container(9000).ListItem.Property(section))"
    new = "[String.IsEqual(ListItem.Property(section),Container(9000).ListItem.Property(section)) + String.IsEqual(ListItem.Property(hubsource),Container(9000).ListItem.Property(hubsource))]"
    if text.count(old) < 2:
        raise RuntimeError("Missing nav selected-state anchors")
    text = text.replace(old, new)

    path_vars = {
        "traktwatchlist": "InfinityMoviesPrimaryPath",
        "traktcollection": "InfinityMoviesSecondaryPath",
        "url=progress": "InfinityTVPrimaryPath",
        "progresstv": "InfinityTVSecondaryPath",
    }
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        replaced = False
        if stripped.startswith("<content ") and "plugin://plugin.video.umbrella/" in line:
            for marker, var in path_vars.items():
                if marker in line:
                    prefix = line[: line.index(">") + 1]
                    lines.append(prefix + "$VAR[" + var + "]</content>")
                    replaced = True
                    break
        if replaced:
            continue
        if stripped.startswith("<onclick condition=") and "SetProperty(Infinity.BrowsePath,plugin://plugin.video.umbrella/" in line:
            mapping = None
            if "traktwatchlist" in line:
                mapping = ("traktmovies", "InfinityMoviesPrimaryPath")
            elif "traktcollection" in line:
                mapping = ("traktmovies", "InfinityMoviesSecondaryPath")
            elif "url=progress" in line and "calendar" in line:
                mapping = ("trakttv", "InfinityTVPrimaryPath")
            elif "progresstv" in line:
                mapping = ("trakttv", "InfinityTVSecondaryPath")
            if mapping:
                section, var = mapping
                indent = line[: len(line) - len(line.lstrip())]
                original = line.replace(
                    f"String.IsEqual(Container(9000).ListItem.Property(section),{section})",
                    f"[String.IsEqual(Container(9000).ListItem.Property(section),{section}) + String.IsEqual(Container(9000).ListItem.Property(hubsource),trakt)]",
                    1,
                )
                local = (
                    f'{indent}<onclick condition="[String.IsEqual(Container(9000).ListItem.Property(section),{section}) + '
                    f'String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)]">'
                    f"SetProperty(Infinity.BrowsePath,$VAR[{var}],Home)</onclick>"
                )
                lines.extend([original, local])
                continue
        lines.append(line)
    return "\n".join(lines) + "\n"

def _patch_includes(text: str) -> str:
    if "InfinityMoviesPrimaryPath" in text:
        return text
    marker = "  <!-- Infinity 1.0.5.115: compact-only Continue Watching media card. -->"
    if marker in text:
        return text.replace(marker, VARIABLES + "\n" + marker, 1)
    if "</includes>" not in text:
        raise RuntimeError("Missing unified include root close")
    return text.replace("</includes>", VARIABLES + "\n</includes>", 1)

def _atomic_write(path: Path, data: bytes) -> None:
    temp = path.with_name(path.name + ".rh3292.tmp")
    with temp.open("wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(temp), str(path))

def _backup(root: Path, files: dict[str, bytes]) -> None:
    profile = Path(xbmcvfs.translatePath("special://profile/addon_data/script.infinity.commandcenter"))
    backup = profile / "resume-hub2-skin181-backup"
    for rel in files:
        src = root / rel
        dst = backup / rel
        if src.is_file() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

def upgrade_installed_skin() -> tuple[bool, str]:
    root = Path(xbmcvfs.translatePath("special://home/addons/skin.infinity.diggz"))
    addon = root / "addon.xml"
    if not addon.is_file():
        return False, "skin-not-installed"
    current = _version(addon.read_text(encoding="utf-8", errors="replace"))
    if current == TO_VERSION:
        return False, "already-current"
    if current != FROM_VERSION:
        return False, "unexpected-parent-" + (current or "unknown")

    original: dict[str, bytes] = {}
    staged: dict[str, bytes] = {}

    for d in HOME_DIRS:
        rel = f"{d}/Home.xml"
        p = root / rel
        if not p.is_file():
            raise RuntimeError("Missing Home.xml: " + d)
        original[rel] = p.read_bytes()
        staged[rel] = _patch_home(original[rel].decode("utf-8")).encode("utf-8")

    for d in INCLUDE_DIRS:
        rel = f"{d}/Includes_InfinityHomeUnified.xml"
        p = root / rel
        if not p.is_file():
            raise RuntimeError("Missing unified include: " + d)
        original[rel] = p.read_bytes()
        staged[rel] = _patch_includes(original[rel].decode("utf-8")).encode("utf-8")

    for rel in ("addon.xml", "infinity-skin.json", "Infinity-Protected-Manifest.json"):
        p = root / rel
        if not p.is_file():
            raise RuntimeError("Missing skin metadata: " + rel)
        original[rel] = p.read_bytes()

    addon_text = original["addon.xml"].decode("utf-8")
    if f'version="{FROM_VERSION}"' not in addon_text:
        raise RuntimeError("Unexpected skin addon version")
    addon_text = addon_text.replace(f'version="{FROM_VERSION}"', f'version="{TO_VERSION}"', 1)
    addon_text = addon_text.replace(
        'addon="script.infinity.commandcenter" version="0.3.5.17"',
        f'addon="script.infinity.commandcenter" version="{COMMAND_VERSION}"',
        1,
    )
    addon_text = re.sub(
        r'(<description lang="en_GB">).*?(</description>)',
        r'\1Infinity Resume Hub 2 adds local Infinity Movies and Infinity TV beside the preserved Trakt sections. Resume Hub owns watched history, Watchlist, Collection, ratings and lists through Command Center 0.3.5.19 while preserving the approved 1.0.5.181 responsive geometry and player surfaces.\2',
        addon_text,
        flags=re.S,
    )
    staged["addon.xml"] = addon_text.encode("utf-8")

    release = {
        "baseline": FROM_VERSION,
        "title": "Infinity Resume Hub 2 RC1",
        "controller": COMMAND_VERSION,
        "requires_apk": 2103292,
        "native_changed": False,
        "runtime_tested": False,
        "status": "device_acceptance_pending",
        "scope": "Local Trakt-replacement menus/state plus watched/playcount skin bridge; existing responsive geometry and player surfaces preserved",
        "resume_hub_watched_contract": "Kodi playcount/overlay + Infinity.ResumeHub.Watched",
    }
    skin_data = json.loads(original["infinity-skin.json"])
    skin_data["previous_release_metadata"] = skin_data.get("current_release")
    skin_data["current_release"] = release
    skin_data.update(candidate=182, candidate_name="Infinity Resume Hub 2 RC1", skin_version=TO_VERSION, resume_hub_api="2.0")
    staged["infinity-skin.json"] = (json.dumps(skin_data, indent=2, sort_keys=True) + "\n").encode()

    manifest = json.loads(original["Infinity-Protected-Manifest.json"])
    manifest["previous_release_metadata"] = manifest.get("current_release")
    manifest["current_release"] = release
    manifest.update(skin_version=TO_VERSION, candidate="Infinity Resume Hub 2 1.0.5.182 RC1", resume_hub_api="2.0")
    protected = manifest.get("protected_files", {})
    for rel in list(protected):
        if rel in staged:
            protected[rel] = _sha(staged[rel])
        else:
            p = root / rel
            if p.is_file():
                protected[rel] = _sha(p.read_bytes())
    for rel, data in staged.items():
        if (root / rel).is_file():
            protected[rel] = _sha(data)
    manifest["protected_files"] = protected
    staged["Infinity-Protected-Manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()

    # Validate every transformed XML before any installed file is replaced.
    for rel, data in staged.items():
        if rel.endswith(".xml"):
            ET.fromstring(data)

    for d in HOME_DIRS:
        data = staged[f"{d}/Home.xml"].decode("utf-8")
        for token in ("<label>INFINITY MOVIES</label>", "<label>INFINITY TV</label>", '<property name="hubsource">infinity</property>'):
            if token not in data:
                raise RuntimeError(f"{d} missing {token}")
    for d in INCLUDE_DIRS:
        data = staged[f"{d}/Includes_InfinityHomeUnified.xml"].decode("utf-8")
        for token in ("InfinityMoviesPrimaryPath", "InfinityMoviesSecondaryPath", "InfinityTVPrimaryPath", "InfinityTVSecondaryPath", "InfinityResumeHubWatchedState"):
            if token not in data:
                raise RuntimeError(f"{d} missing {token}")

    _backup(root, original)

    # Stage every file to disk first. Publish addon.xml last so the version changes only
    # after the complete 1.0.5.182 file set is in place.
    for rel, data in staged.items():
        temp = (root / rel).with_name((root / rel).name + ".rh3292.stage")
        temp.parent.mkdir(parents=True, exist_ok=True)
        temp.write_bytes(data)
    order = [r for r in staged if r != "addon.xml"] + ["addon.xml"]
    for rel in order:
        target = root / rel
        temp = target.with_name(target.name + ".rh3292.stage")
        os.replace(str(temp), str(target))

    return True, "upgraded"

def apply_and_reload() -> str:
    try:
        changed, status = upgrade_installed_skin()
        xbmc.log("[Infinity Resume Hub] skin upgrade: " + status, xbmc.LOGINFO)
        if changed and xbmc.getSkinDir() == "skin.infinity.diggz":
            xbmc.executebuiltin("ReloadSkin()")
        return status
    except Exception as error:
        xbmc.log("[Infinity Resume Hub] skin upgrade failed: " + type(error).__name__ + ": " + str(error), xbmc.LOGERROR)
        return "failed-" + type(error).__name__
