# -*- coding: utf-8 -*-
"""Infinity Authorization Manager 0.1.0.

Boundary: status/orchestration only. Never reads, copies, exports, logs or stores
OAuth access/refresh tokens. Authentication remains owned by each installed add-on.
"""
import hashlib
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()\nVERSION = "0.1.1"
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
STATE = os.path.join(PROFILE, "authorization-state.json")
ACCT = "script.module.acctmgr"
SERVICES = [
    ("Trakt", "trakt", "traktAuth", "traktReSync", "traktViewer"),
    ("Real-Debrid", "realdebrid", "realdebridAuth", "realdebridReSync", "realdebridViewer"),
    ("Premiumize", "premiumize", "premiumizeAuth", "premiumizeReSync", "premiumizeViewer"),
    ("All-Debrid", "alldebrid", "alldebridAuth", "alldebridReSync", "alldebridViewer"),
    ("TorBox", "torbox", "torboxAuth", "torboxReSync", "torboxViewer"),
    ("OffCloud", "offcloud", "offcloudAuth", "offcloudReSync", "offcloudViewer"),
    ("Easynews", "easynews", "easynewsAuth", "easynewsReSync", "easynewsViewer"),
    ("MDBList", "mdblist", "mdblistAuth", "mdblistReSync", "mdblistViewer"),
]
TOKEN_KEYS = {
    "trakt": ("trakt.token", "trakt.refresh"),
    "realdebrid": ("realdebrid.token", "realdebrid.refresh"),
    "premiumize": ("premiumize.token",),
    "alldebrid": ("alldebrid.token",),
    "torbox": ("torbox.token",),
    "offcloud": ("offcloud.token",),
    "easynews": ("easynews.password",),
    "mdblist": ("mdblist.apikey",),
}
ERROR_PATTERNS = {
    "trakt": ("invalid_grant", "session not found", "re-authorize your trakt"),
    "realdebrid": ("real-debrid", "bad_token"),
    "premiumize": ("premiumize", "unauthorized"),
    "alldebrid": ("all-debrid", "unauthorized"),
    "torbox": ("torbox", "unauthorized"),
}
SUCCESS_PATTERNS = {
    "trakt": ("trakt token refresh succeeded", "background trakt refresh succeeded", "successfully authorized"),
    "realdebrid": ("real-debrid token refresh succeeded", "real-debrid auth"),
}


def has_addon(addon_id):
    return xbmc.getCondVisibility("System.HasAddon(%s)" % addon_id)


def safe_setting_presence(addon_id, keys):
    """Return only booleans. Raw values never leave this stack frame."""
    try:
        a = xbmcaddon.Addon(addon_id)
        present = []
        for key in keys:
            try:
                present.append(bool(a.getSetting(key)))
            except Exception:
                present.append(False)
        return any(present), all(present)
    except Exception:
        return False, False


def tail_log(limit=800000):
    path = xbmcvfs.translatePath("special://logpath/kodi.log")
    try:
        with xbmcvfs.File(path, "r") as f:
            data = f.read()
        return data[-limit:].lower()
    except Exception:
        return ""


def log_state(service_key, log_text):
    """Classify by the newest matching marker, not mere presence anywhere in kodi.log."""
    failure_hits = [(log_text.rfind(p), p) for p in ERROR_PATTERNS.get(service_key, ()) if p in log_text]
    success_hits = [(log_text.rfind(p), p) for p in SUCCESS_PATTERNS.get(service_key, ()) if p in log_text]
    newest_failure = max((x[0] for x in failure_hits), default=-1)
    newest_success = max((x[0] for x in success_hits), default=-1)
    failed = newest_failure >= 0 and newest_failure > newest_success
    succeeded = newest_success >= 0 and newest_success > newest_failure
    return failed, succeeded


def snapshot():
    log_text = tail_log()
    acct_installed = has_addon(ACCT)
    rows = []
    for label, key, auth, sync, viewer in SERVICES:
        any_present = all_present = False
        if acct_installed:
            any_present, all_present = safe_setting_presence(ACCT, TOKEN_KEYS.get(key, ()))
        failed, succeeded = log_state(key, log_text)
        if not acct_installed:
            status = "Owner unavailable"
        elif failed and not succeeded:
            status = "Reauthorization required"
        elif all_present and failed:
            status = "Credentials present - refresh failed"
        elif key == "trakt" and all_present and acct_installed:
            # AM Lite 1.1.6's own master credential pair exists. We intentionally
            # do not claim downstream add-ons are healthy until their owner sync/refresh
            # has been observed; AM Lite remains the credential owner in RC1.
            status = "Connected (owner)"
        elif all_present:
            status = "Connected"
        elif any_present:
            status = "Partial credentials"
        else:
            status = "Not configured"
        rows.append({
            "service": label, "key": key, "status": status,
            "owner": "Account Manager Lite" if acct_installed else "Not installed",
            "credential_fields_present": bool(any_present),
            "credential_set_complete": bool(all_present),
            "refresh_failure_seen": bool(failed),
            "success_marker_seen": bool(succeeded),
            "actions": {"authorize": auth, "resync": sync, "viewer": viewer},
        })
    return {"schema": 1, "generated_at": int(time.time()), "credential_values_stored": False, "services": rows}


def publish(snap):
    w = xbmcgui.Window(10000)
    w.setProperty("Infinity.AuthManager.Ready", "true")
    w.setProperty("Infinity.AuthManager.OwnerInstalled", "true" if has_addon(ACCT) else "false")
    for row in snap["services"]:
        k = row["key"]
        w.setProperty("Infinity.Auth.%s.Status" % k, row["status"])
        w.setProperty("Infinity.Auth.%s.Owner" % k, row["owner"])
        w.setProperty("Infinity.Auth.%s.Configured" % k, "true" if row["credential_fields_present"] else "false")


def persist_safe(snap):
    xbmcvfs.mkdirs(PROFILE)
    # Only status booleans/labels/timestamps are persisted. No credential material.
    safe = {"schema": 1, "generated_at": snap["generated_at"], "credential_values_stored": False,
            "services": [{k:v for k,v in row.items() if k not in ("actions",)} for row in snap["services"]]}
    with xbmcvfs.File(STATE, "w") as f:
        f.write(json.dumps(safe, indent=2, sort_keys=True))


def run_owner(action):
    if not has_addon(ACCT):
        xbmcgui.Dialog().ok("Infinity Authorization Manager", "Account Manager Lite is not installed/enabled.")
        return
    xbmc.executebuiltin("RunScript(%s, action=%s)" % (ACCT, action))


def choose_service():
    snap = snapshot(); publish(snap); persist_safe(snap)
    labels = ["%s  -  %s" % (r["service"], r["status"]) for r in snap["services"]]
    idx = xbmcgui.Dialog().select("Infinity Authorization Manager", labels)
    if idx < 0: return
    row = snap["services"][idx]
    options = ["Authorize / Reauthorize", "ReSync installed add-ons", "View authorizations", "Refresh status"]
    pick = xbmcgui.Dialog().select(row["service"], options)
    if pick == 0: run_owner(row["actions"]["authorize"])
    elif pick == 1: run_owner(row["actions"]["resync"])
    elif pick == 2: run_owner(row["actions"]["viewer"])
    elif pick == 3:
        snap = snapshot(); publish(snap); persist_safe(snap)
        xbmcgui.Dialog().notification("Infinity Authorization Manager", "%s: %s" % (row["service"], snap["services"][idx]["status"]), time=4000)


def main():
    params = {}
    for raw in sys.argv[1:]:
        if "=" in raw:
            k,v=raw.split("=",1); params[k.lstrip("-")] = v
    action=params.get("action","")
    service=params.get("service","")
    snap=snapshot(); publish(snap); persist_safe(snap)
    if action in ("authorize","resync","viewer") and service:
        for row in snap["services"]:
            if row["key"] == service:
                run_owner(row["actions"][{"authorize":"authorize","resync":"resync","viewer":"viewer"}[action]])
                return
    choose_service()

if __name__ == "__main__":
    main()
