#!/usr/bin/env python3
"""Repair crash-recorder SIGABRT ownership without altering Kodi executable code.

NARROW SCOPE: stage ONLY the reviewed libinfinitycrash signal-source change.
Android's debuggerd should see the *original* FORTIFY abort stack, rather
than only infinitycrash.restore_and_reraise. This is a diagnostics integrity
repair, NOT a claim that a native destroyed-mutex failure has been fixed.

The original signed 2103405 libinfinitycrash.so stays the rollback reference.
Any install-over APK must independently match exact C source and native build ID.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_REL = "repairs/infinity-2103402-final/native-overlay/infinity_crash_recorder.c"
ORIGINAL_GIT_BLOB_SHA1 = "fc7be4f72c7e19606b718d4ef04487756a17a901"
BEFORE = "static const int g_signals[] = { SIGSEGV, SIGABRT, SIGBUS, SIGILL, SIGFPE };"
AFTER = "static const int g_signals[] = { SIGSEGV, SIGBUS, SIGILL, SIGFPE };"

def git_blob_sha1(contents: bytes) -> str:
    header = ("blob " + str(len(contents)) + "\x00").encode("ascii")
    return hashlib.sha1(header + contents).hexdigest()

def apply(source: bytes) -> bytes:
    if git_blob_sha1(source) != ORIGINAL_GIT_BLOB_SHA1:
        raise RuntimeError("Recorder source does not match audited baseline Git object")
    old, new = BEFORE.encode("ascii"), AFTER.encode("ascii")
    if source.count(old) != 1:
        raise RuntimeError("SIGABRT source anchor is not unique")
    modified = source.replace(old, new, 1)
    if modified.replace(new, old, 1) != source:
        raise RuntimeError("Unexpected recorder source modification")
    if b"SIGABRT" not in source or b"SIGABRT" in modified.split(b"static const int g_signals[]",1)[1].split(b";",1)[0]:
        raise RuntimeError("SIGABRT interception was not disabled")
    for token in (
        b"static void crash_handler(int sig, siginfo_t* info, void* opaque)",
        b"static void forward_original_signal(int sig, pid_t tid, siginfo_t* info, void* opaque)",
        b"static void rearm_sigsegv_if_needed(void)",
        b"native-crash-last.txt",
        b"native-maps-%d.txt",
    ):
        if token not in modified:
            raise RuntimeError("Existing signal/memory-map diagnostic owner disappeared")
    return modified

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    before = args.source.read_bytes()
    after = apply(before)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    if args.destination.exists():
        raise RuntimeError("Refusing to overwrite an existing candidate")
    args.destination.write_bytes(after)
    print("PATCHED_DIAGNOSTIC_SOURCE_SHA256="+hashlib.sha256(after).hexdigest())
    print("WHAT_CHANGED: SIGABRT interception disabled, nothing else")
    print("NOT_A_SEARCH_CRASH_FIX: native object lifetime is still under investigation")

if __name__ == "__main__":
    main()
