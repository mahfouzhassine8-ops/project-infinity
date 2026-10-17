# SPDX-License-Identifier: GPL-2.0-or-later
"""Manual, exact-binary access to the existing observational TEST4 recorder.

The only native call is Arm(int), whose symbol and body are verified in TEST4.
It changes recorder timing/counters, never a lock or shutdown authority.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import time
import zipfile

EXPECTED_NATIVE_SHA256 = "2f1597ecc4f8a0ee09f24e399aa738b96a876c7760eaec0ee0ad1a18bafd6929"
ARM_SYMBOL = "_ZN22InfinityStabilityProbe3ArmEi"
UNTIL_SYMBOL = "_ZN22InfinityStabilityProbe5untilE"
WRITTEN_SYMBOL = "_ZN22InfinityStabilityProbe7writtenE"
CONFIGURED_SYMBOL = "_ZN22InfinityStabilityProbe10configuredE"
CAPTURE_SECONDS = 7200
MAX_LOG_BYTES = 512 * 1024
LOG_NAMES = ("infinity-stability-probe.jsonl", "infinity-stability-probe.jsonl.previous")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mapped_native_paths(maps_text):
    paths = set()
    for line in maps_text.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) != 6:
            continue
        name = fields[5]
        if name.startswith("/data/app/") and name.endswith("/libkodi.so"):
            paths.add(name)
    return sorted(paths)


def find_exact_native():
    paths = mapped_native_paths(Path("/proc/self/maps").read_text())
    if len(paths) != 1:
        raise RuntimeError("The expected loaded Infinity library is unavailable. Capture was not armed.")
    path = Path(paths[0])
    if sha256_file(path) != EXPECTED_NATIVE_SHA256:
        raise RuntimeError("This helper requires the locked 2103377 TEST4 engine. Capture was not armed.")
    return path


def arm_exact_library(path):
    """Hash first, then use the fixed ABI; never load the global process handle."""
    if sha256_file(path) != EXPECTED_NATIVE_SHA256:
        raise RuntimeError("Native engine identity differs from TEST4. Capture was not armed.")
    library = ctypes.CDLL(str(path))
    if not ctypes.c_bool.in_dll(library, CONFIGURED_SYMBOL).value:
        raise RuntimeError("The existing recorder is not ready. Let Infinity finish loading, then retry.")
    written = ctypes.c_uint.in_dll(library, WRITTEN_SYMBOL).value
    if written > MAX_LOG_BYTES - 128 * 1024:
        raise RuntimeError("Capture space is low for this session. Close Infinity normally, reopen, then arm capture.")
    arm = getattr(library, ARM_SYMBOL)
    arm.argtypes = [ctypes.c_int]
    arm.restype = None
    before_ms = int(time.monotonic() * 1000)
    arm(CAPTURE_SECONDS)
    until_ms = ctypes.c_int64.in_dll(library, UNTIL_SYMBOL).value
    after_ms = int(time.monotonic() * 1000)
    if not before_ms + CAPTURE_SECONDS * 1000 <= until_ms <= after_ms + CAPTURE_SECONDS * 1000 + 100:
        raise RuntimeError("The recorder did not acknowledge the requested capture window.")
    return {"native_sha256": EXPECTED_NATIVE_SHA256, "window_seconds": CAPTURE_SECONDS,
            "armed_until_monotonic_ms": until_ms, "observational_only": True}


def collect(destination, temp_dir, versions=None):
    """Copy only the two recorder files; no settings, databases or general logs."""
    manifest = {"schema": 1, "helper_version": "1.0.0", "export_pid": os.getpid(),
                "export_epoch_ms": int(time.time() * 1000), "versions": versions or {},
                "expected_test4_native_sha256": EXPECTED_NATIVE_SHA256,
                "observational_only": True, "is_repair": False,
                "files": {}, "unavailable": []}
    files = {}
    for name in LOG_NAMES:
        try:
            with (Path(temp_dir) / name).open("rb") as stream:
                data = stream.read(MAX_LOG_BYTES + 1)
            if len(data) > MAX_LOG_BYTES:
                manifest["unavailable"].append({"name": name, "reason": "exceeds recorder cap"})
                continue
            pids = set()
            rows = 0
            malformed = 0
            for line in data.splitlines():
                if not line:
                    continue
                try:
                    value = json.loads(line)
                    if value.get("kind") == "stability_probe":
                        rows += 1
                        if type(value.get("pid")) is int:
                            pids.add(value["pid"])
                except (ValueError, AttributeError):
                    malformed += 1
            files["native/" + name] = data
            manifest["files"][name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                         "probe_rows": rows, "malformed_rows": malformed,
                                         "producer_pids": sorted(pids)}
        except OSError:
            manifest["unavailable"].append({"name": name, "reason": "not available"})
    if not any(info["probe_rows"] for info in manifest["files"].values()):
        raise RuntimeError("No lock snapshots are available yet. Arm capture, reproduce the freeze, then export.")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
    return manifest
