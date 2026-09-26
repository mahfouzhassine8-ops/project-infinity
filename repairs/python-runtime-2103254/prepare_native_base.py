#!/usr/bin/env python3
"""Prepare the exact 2103229 packaging base with only the rebuilt 2103254 libkodi.so."""
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path

OLD_BASE_SHA="9bda7a49c38dcfd7c67b548ed38c661ddb44ca7434fbb2c69ce48dd7554dab7f"
OLD_ENGINE_SHA="db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375"
LIB="lib/arm64-v8a/libkodi.so"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def req(v,m):
    if not v: raise RuntimeError(m)

def once(t,o,n,label):
    c=t.count(o); req(c==1,f"{label}: expected one anchor, got {c}")
    return t.replace(o,n,1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--engine-apk",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    root=a.root.resolve()
    req(sha(a.base.read_bytes())==OLD_BASE_SHA,"wrong exact 2103229 packaging base")
    with zipfile.ZipFile(a.base) as b, zipfile.ZipFile(a.engine_apk) as e:
        req(b.testzip() is None and e.testzip() is None,"input APK CRC failure")
        old=b.read(LIB); new=e.read(LIB)
        req(sha(old)==OLD_ENGINE_SHA,"2103229 packaging base engine drift")
        newsha=sha(new)
        req(newsha!=OLD_ENGINE_SHA,"2103254 rebuilt engine did not change")
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(a.out,"w") as z:
            for info in b.infolist():
                data=new if info.filename==LIB else b.read(info.filename)
                z.writestr(info,data)
    newbase=sha(a.out.read_bytes())

    runtime=root/"scripts/infinity_background_resume.py"
    t=runtime.read_text()
    m=re.search(r"BASE_APK_SHA256 = '([0-9a-f]{64})'",t); req(m,"BASE_APK_SHA256 missing")
    t=once(t,m.group(0),f"BASE_APK_SHA256 = '{newbase}'","base apk sha")
    m=re.search(r"BASE_ENGINE_SHA256 = '([0-9a-f]{64})'",t); req(m,"BASE_ENGINE_SHA256 missing")
    t=once(t,m.group(0),f"BASE_ENGINE_SHA256 = '{newsha}'","engine sha")
    runtime.write_text(t)

    pack=root/"scripts/package_background_resume.py"
    q=pack.read_text()
    q=q.replace("'native_recompiled':False","'native_recompiled':True")
    pack.write_text(q)

    src_receipt=root/"engine/background-resume-source.json"
    data=json.loads(src_receipt.read_text())
    data["native_engine_parent_sha256"]=OLD_ENGINE_SHA
    data["native_engine_sha256"]=newsha
    data["native_engine_rebuilt"]=True
    data["native_engine_reused_from_2103209"]=False
    data["python_runtime_native_repair"]=True
    src_receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

    proof={
      "schema":1,"parent_packaging_base_sha256":OLD_BASE_SHA,
      "patched_packaging_base_sha256":newbase,
      "parent_native_engine_sha256":OLD_ENGINE_SHA,
      "rebuilt_native_engine_sha256":newsha,
      "only_packaging_base_member_replaced":LIB,
    }
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n")
    print("PASS: exact 2103229 packaging base prepared with only rebuilt 2103254 libkodi.so")

if __name__=="__main__":main()
