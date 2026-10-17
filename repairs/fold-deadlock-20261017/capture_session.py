"""Bounded, user-started evidence; never reads provider settings or databases."""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

ARM_FILE = "infinity-foldcapture-arm.json"
MAX_FILE = 1024 * 1024
OWNED = {
    "skin.infinity.diggz": ("addon.xml", "unified/Custom_1193_InfinityBrowse.xml",
                            "16x9/Custom_1193_InfinityBrowse.xml"),
    "script.infinity.commandcenter": ("addon.xml", "default.py", "service.py", "plugin.py", "context.py",
                                      "resume_hub.py", "experience.py", "common.py", "checkpoint_runtime.py",
                                      "persistence_participant.py", "runtime_visibility.py", "skin_upgrade.py",
                                      "view_mode.py", "resources/settings.xml"),
    "script.infinity.rails": ("addon.xml", "default.py", "plugin.py", "context_add.py", "resources/lib/runtime.py",
                              "resources/lib/mocha.py", "resources/lib/catalog.py", "resources/lib/store.py",
                              "resources/lib/dialog.py", "resources/lib/stability_probe.py", "resources/lib/input_status.py",
                              "resources/lib/__init__.py", "resources/defaults.xml",
                              "resources/language/resource.language.en_gb/strings.po"),
    "plugin.video.umbrella": ("addon.xml",),
    "plugin.video.pov": ("addon.xml",),
    "plugin.video.otaku": ("addon.xml",),
    "plugin.video.watchnixtoons2": ("addon.xml",),
}


def save_arm(temp, receipt):
    row = dict(receipt, pid=os.getpid(), armed_epoch_ms=int(time.time() * 1000))
    target = Path(temp) / ARM_FILE
    temporary = target.with_suffix(".pending")
    with temporary.open("w") as stream:
        json.dump(row, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)


def arm_record(temp):
    try:
        with (Path(temp) / ARM_FILE).open("rb") as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            return {"available": False, "reason": "size limit"}
        value = json.loads(raw)
        if not (isinstance(value, dict) and type(value.get("pid")) is int and value["pid"] > 0 and
                re.fullmatch("[0-9a-f]{64}", str(value.get("native_sha256", ""))) and
                all(type(value.get(k)) is int for k in ("armed_epoch_ms", "armed_until_monotonic_ms", "window_seconds"))):
            return {"available": False, "reason": "invalid receipt"}
        return {"available": True, **{key: value[key] for key in (
            "pid", "native_sha256", "armed_epoch_ms", "armed_until_monotonic_ms", "window_seconds")}}
    except (OSError, ValueError, TypeError):
        return {"available": False, "reason": "not available"}


def installed(addons_root, enabled=None):
    result = {}
    for addon_id, names in OWNED.items():
        row = {"version": "unavailable", "enabled": None, "code_sha256": {}}
        root = Path(addons_root) / addon_id
        for name in names:
            try:
                with (root / name).open("rb") as stream:
                    data = stream.read(MAX_FILE + 1)
                if len(data) > MAX_FILE:
                    continue
                row["code_sha256"][name] = hashlib.sha256(data).hexdigest()
                if name == "addon.xml":
                    manifest = ET.fromstring(data)
                    if manifest.get("id") == addon_id:
                        row["version"] = manifest.get("version", "unavailable")
            except (OSError, ET.ParseError):
                continue
        if enabled is not None:
            try:
                value = enabled(addon_id)
                if type(value) is bool:
                    row["enabled"] = value
            except (ValueError, RuntimeError, TypeError, KeyError, AttributeError):
                pass
        result[addon_id] = row
    return result
