"""Kodi-managed enable only. This module has no filesystem or disable API."""
import json
import re

OTAKU = "plugin.video.otaku"
ID = re.compile(r"[A-Za-z0-9_.-]{1,160}\Z")


class RecoveryError(RuntimeError):
    pass


def rpc(execute, method, params):
    try:
        value = json.loads(execute(json.dumps({"jsonrpc": "2.0", "id": 1,
                                               "method": method, "params": params})))
    except (TypeError, ValueError, RuntimeError) as error:
        raise RecoveryError("Kodi's add-on manager could not be queried.") from error
    if not isinstance(value, dict) or "error" in value or "result" not in value:
        raise RecoveryError("Kodi did not accept this add-on manager request.")
    return value["result"]


def inventory(execute):
    result = rpc(execute, "Addons.GetAddons", {"enabled": "all", "properties": ["name", "version", "enabled"]})
    if not isinstance(result, dict) or not isinstance(result.get("addons"), list):
        raise RecoveryError("Kodi returned an unavailable add-on inventory.")
    rows = {}
    for item in result["addons"]:
        if not isinstance(item, dict):
            continue
        addon_id = item.get("addonid")
        if isinstance(addon_id, str) and ID.fullmatch(addon_id):
            if addon_id in rows:
                raise RecoveryError("Kodi returned duplicate add-on identities; no change was made.")
            rows[addon_id] = dict(addonid=addon_id, name=str(item.get("name") or addon_id),
                                  version=str(item.get("version") or "unknown"),
                                  enabled=item.get("enabled") if type(item.get("enabled")) is bool else None)
    return rows


def disabled(execute):
    return sorted((item for item in inventory(execute).values() if item["enabled"] is False),
                  key=lambda item: (item["name"].casefold(), item["addonid"]))


def enable(execute, addon_id):
    if not isinstance(addon_id, str) or not ID.fullmatch(addon_id):
        raise RecoveryError("Invalid add-on identity; no change was made.")
    # Query the current state immediately before mutation, including the version.
    before = inventory(execute).get(addon_id)
    if before is None:
        return {"state": "not-installed", "addonid": addon_id}
    if before["enabled"] is True:
        return {"state": "already-enabled", **before}
    if before["enabled"] is not False:
        raise RecoveryError("Kodi could not establish whether this add-on is disabled. No change was made.")
    result = rpc(execute, "Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": True})
    if result != "OK":
        raise RecoveryError("Kodi did not confirm the enable request. Open Add-on Information for dependency details.")
    after = inventory(execute).get(addon_id)
    if after is None or after["enabled"] is not True:
        raise RecoveryError("Kodi has not confirmed this add-on as enabled. Check Add-on Information.")
    return {"state": "enabled", **after, "previous_version": before["version"]}
