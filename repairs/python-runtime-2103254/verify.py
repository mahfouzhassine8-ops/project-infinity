#!/usr/bin/env python3
"""Verify 2103254 against the exact locked 2103229 APK and captured native repair contract."""
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path

VERSION=2103254
NAME="1.0.9-Python-Runtime-Native-Repair-RC1"
PARENT_SHA="3a80480e300bafc6071aed7f494cc6b3a96a79f7e1e4dcb9ae87fe36c9a707f5"
OLD_ENGINE="db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375"
SIGNER="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
LIB="lib/arm64-v8a/libkodi.so"
REC="lib/arm64-v8a/libinfinitycrash.so"
DEX=re.compile(r"classes\d*\.dex$")
SIG=re.compile(r"META-INF/[^/]+\.(?:RSA|DSA|EC|SF|MF)$",re.I)

def hb(b):return hashlib.sha256(b).hexdigest()
def sha(p):return hb(p.read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--audit",type=Path,required=True)
    p.add_argument("--native-proof",type=Path,required=True)
    p.add_argument("--base-proof",type=Path,required=True)
    p.add_argument("--recorder",type=Path,required=True)
    p.add_argument("--signing",type=Path,required=True)
    p.add_argument("--badging",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)

    req(sha(a.parent)==PARENT_SHA,"wrong locked 2103229 parent")
    audit=json.loads(a.audit.read_text())
    native=json.loads(a.native_proof.read_text())
    base=json.loads(a.base_proof.read_text())
    new_engine=native["rebuilt_native_engine_sha256"]
    req(new_engine==base["rebuilt_native_engine_sha256"],"native proof mismatch")
    req(new_engine!=OLD_ENGINE,"native engine was not rebuilt")
    req(all(native["checks"].values()),"native source repair checks not all green")
    req(native.get("schema")==3,"wrong native repair proof schema")

    req(audit.get("version_code")==VERSION,"versionCode mismatch")
    req(audit.get("version_name")==NAME,"versionName mismatch")
    req(audit.get("native_engine_sha256")==new_engine,"packager engine receipt mismatch")
    req(audit.get("native_recompiled") is True,"packager must mark native recompile")
    req(audit.get("signer_certificate_sha256")==SIGNER,"signer changed")
    req(audit.get("apk_sha256")==sha(a.candidate),"candidate SHA receipt mismatch")

    with zipfile.ZipFile(a.parent) as old, zipfile.ZipFile(a.candidate) as new:
        req(old.testzip() is None and new.testzip() is None,"APK CRC failure")
        on=set(old.namelist()); nn=set(new.namelist())
        req(REC not in on and REC in nn,"diagnostic recorder inventory contract failed")
        req(nn-on=={REC},"unexpected APK member additions: "+repr(sorted(nn-on)))
        req(on-nn==set(),"APK members removed")
        req(hb(old.read(LIB))==OLD_ENGINE,"parent engine identity drift")
        req(hb(new.read(LIB))==new_engine,"candidate rebuilt engine identity mismatch")
        req(hb(new.read(REC))==sha(a.recorder),"recorder payload mismatch")

        changed=[n for n in sorted(on) if old.read(n)!=new.read(n)]
        allowed=lambda n: n==LIB or n=="AndroidManifest.xml" or bool(DEX.fullmatch(n)) or bool(SIG.fullmatch(n))
        unexpected=[n for n in changed if not allowed(n)]
        req(not unexpected,"protected payload changed: "+repr(unexpected[:20]))
        for n in on:
            if n.startswith("lib/") and not n.endswith("/") and n!=LIB:
                req(old.read(n)==new.read(n),"unrelated native library changed: "+n)
            if (n.startswith("assets/") or n.startswith("res/")) and not n.endswith("/"):
                req(old.read(n)==new.read(n),"asset/resource changed: "+n)
        req(old.read("resources.arsc")==new.read("resources.arsc"),"resources.arsc changed")
        joined=b"".join(new.read(n) for n in nn if DEX.fullmatch(n))
        for token in (b"nativeCrashRecorder.loaded.afterKodiOnCreate",b"trace_request_attempted",b"process_state_summary"):
            req(token in joined,"diagnostic Android token missing: "+repr(token))

    badging=a.badging.read_text(errors="replace")
    req(f"versionCode='{VERSION}'" in badging and f"versionName='{NAME}'" in badging,"badging identity mismatch")
    signing=a.signing.read_text(errors="replace").lower()
    req(SIGNER in signing,"permanent signing certificate missing")

    result={
      "schema":1,"build":VERSION,"version_name":NAME,"parent":2103229,
      "parent_apk_sha256":PARENT_SHA,"candidate_apk_sha256":sha(a.candidate),
      "parent_native_engine_sha256":OLD_ENGINE,"rebuilt_native_engine_sha256":new_engine,
      "native_engine_rebuilt":True,"python_runtime_repair_checks":native["checks"],
      "upstream_teardown_commit":native["upstream_teardown_commit"],
      "diagnostic_recorder_preserved":True,"assets_resources_preserved":True,
      "unrelated_native_libraries_preserved":True,"signer_sha256":SIGNER,
      "physical_device_verified":False,
      "status":"TEST CANDIDATE — actual native Python runtime repair; device verification required",
    }
    (a.out/"verification.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("PASS: 2103254 actual native repair preserves locked 2103229 outside authorized engine/diagnostic delta")

if __name__=="__main__":main()
