"""Actual Kodi RPC and retained fixture settings; never a physical Otaku test."""
import hashlib
import json
from pathlib import Path
import sys
import traceback
import xbmc
import xbmcvfs

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "addon"))
import recovery


def require(value, message):
    if not value:
        raise RuntimeError(message)


profile = Path(xbmcvfs.translatePath("special://profile/"))
output = profile / "recovery-smoke-result.json"
result = {"passed": False, "real_kodi_api": True, "physical_fold_verified": False,
          "actual_otaku_tested": False, "scope": "Two disposable video fixtures; Linux Kodi API integration"}
try:
    ids = ["plugin.video.infinityrecoveryfixture1", "plugin.video.infinityrecoveryfixture2"]
    before = {addon_id: (profile / "addon_data" / addon_id / "settings.xml").read_bytes() for addon_id in ids}
    for addon_id in ids:
        require(recovery.rpc(xbmc.executeJSONRPC, "Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": False}) == "OK", "Fixture disable failed")
    rows = recovery.disabled(xbmc.executeJSONRPC)
    require(set(ids) <= {row["addonid"] for row in rows}, "Disabled installations were not listed")
    first = recovery.enable(xbmc.executeJSONRPC, ids[0])
    require(first["state"] == "enabled", "First enable failed")
    require(recovery.inventory(xbmc.executeJSONRPC)[ids[1]]["enabled"] is False, "Unselected fixture changed")
    second = recovery.enable(xbmc.executeJSONRPC, ids[1])
    require(second["state"] == "enabled", "Second enable failed")
    files = recovery.rpc(xbmc.executeJSONRPC, "Files.GetDirectory", {"directory": "addons://sources/video/", "media": "files"})
    paths = [str(item.get("file") or "") for item in files.get("files", [])]
    require(all(any(path.startswith("plugin://" + addon_id) for path in paths) for addon_id in ids), "Enabled fixtures did not reappear in Video Sources")
    require(all((profile / "addon_data" / addon_id / "settings.xml").read_bytes() == data for addon_id, data in before.items()), "Fixture settings changed")
    require(recovery.enable(xbmc.executeJSONRPC, ids[0])["state"] == "already-enabled", "Repeat enable was not idempotent")
    require(recovery.enable(xbmc.executeJSONRPC, "plugin.video.infinitymissingfixture")["state"] == "not-installed", "Missing installation was mislabeled")
    result.update(passed=True, disabled_list_verified=True, two_native_enables_verified=True,
                  video_sources_reappearance_verified=True, retained_settings_byte_identical=True,
                  unselected_addon_unchanged=True, idempotence_verified=True,
                  kodi_version=xbmc.getInfoLabel("System.BuildVersion"),
                  source_sha256=hashlib.sha256((HERE / "addon/recovery.py").read_bytes()).hexdigest())
except Exception:
    result["failure"] = traceback.format_exc()
finally:
    output.write_text(json.dumps(result, indent=2) + "\n")
