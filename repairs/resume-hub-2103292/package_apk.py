#!/usr/bin/env python3
"""Inject the checksummed Resume Hub controller asset without touching native payloads."""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import re
import zipfile

ASSET = "assets/infinity/resume-hub-controller.zip"
SIGNING = re.compile(r"META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))", re.I)

def H(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build(parent: Path, compiled: Path, controller: Path, unsigned: Path) -> dict:
    controller_bytes = controller.read_bytes()
    with zipfile.ZipFile(parent) as p, zipfile.ZipFile(compiled) as c:
        if p.testzip() is not None or c.testzip() is not None:
            raise RuntimeError("APK CRC failure")
        parent_native = p.read("lib/arm64-v8a/libkodi.so")
        compiled_native = c.read("lib/arm64-v8a/libkodi.so")
        if parent_native != compiled_native:
            raise RuntimeError("2103292 native engine changed")
        parent_assets = {n: p.read(n) for n in p.namelist() if n.startswith("assets/") and not n.endswith("/")}
        for n, data in parent_assets.items():
            if c.read(n) != data:
                raise RuntimeError("protected parent asset changed: " + n)

        with zipfile.ZipFile(unsigned, "w", allowZip64=True) as out:
            for info in c.infolist():
                if SIGNING.fullmatch(info.filename) or info.filename == ASSET:
                    continue
                out.writestr(info, c.read(info.filename))
            out.writestr(ASSET, controller_bytes, compress_type=zipfile.ZIP_STORED)

    with zipfile.ZipFile(unsigned) as z:
        if z.testzip() is not None:
            raise RuntimeError("unsigned APK CRC failure")
        if z.read(ASSET) != controller_bytes:
            raise RuntimeError("controller asset mismatch")
        if z.read("lib/arm64-v8a/libkodi.so") != parent_native:
            raise RuntimeError("native changed after asset injection")
    return {
        "parent_apk_sha256": H(parent.read_bytes()),
        "compiled_apk_sha256": H(compiled.read_bytes()),
        "controller_asset_sha256": H(controller_bytes),
        "native_engine_sha256": H(parent_native),
        "asset_path": ASSET,
        "native_changed": False,
    }

def verify(parent: Path, final: Path, controller: Path) -> dict:
    cb = controller.read_bytes()
    with zipfile.ZipFile(parent) as p, zipfile.ZipFile(final) as f:
        if p.testzip() is not None or f.testzip() is not None:
            raise RuntimeError("final APK CRC failure")
        if f.read("lib/arm64-v8a/libkodi.so") != p.read("lib/arm64-v8a/libkodi.so"):
            raise RuntimeError("final native engine changed")
        if f.read(ASSET) != cb:
            raise RuntimeError("final Resume Hub asset mismatch")
        for n in p.namelist():
            if n.startswith("assets/") and not n.endswith("/"):
                if f.read(n) != p.read(n):
                    raise RuntimeError("final parent asset changed: " + n)
    return {
        "final_apk_sha256": H(final.read_bytes()),
        "parent_apk_sha256": H(parent.read_bytes()),
        "controller_asset_sha256": H(cb),
        "native_engine_sha256": H(zipfile.ZipFile(final).read("lib/arm64-v8a/libkodi.so")),
        "native_changed": False,
        "parent_assets_preserved": True,
    }

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    b=sub.add_parser("build")
    b.add_argument("--parent",type=Path,required=True)
    b.add_argument("--compiled",type=Path,required=True)
    b.add_argument("--controller",type=Path,required=True)
    b.add_argument("--unsigned",type=Path,required=True)
    v=sub.add_parser("verify")
    v.add_argument("--parent",type=Path,required=True)
    v.add_argument("--final",type=Path,required=True)
    v.add_argument("--controller",type=Path,required=True)
    a=ap.parse_args()
    if a.cmd=="build":
        print(build(a.parent,a.compiled,a.controller,a.unsigned))
    else:
        print(verify(a.parent,a.final,a.controller))

if __name__=="__main__":
    main()
