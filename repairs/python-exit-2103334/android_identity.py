#!/usr/bin/env python3
"""Bind exactly the 3333 Android source to the new engine; no UI/lifecycle changes."""
import argparse
import hashlib
import json
from pathlib import Path
import re

PARENT_MAP = 'e845dd7bf29b929856b0cd6a07c3bbe646a354273c3ac9d4af9128cf59b6b40e'
OLD_NATIVE = '22f56ef1836c53930f7b2c9fa89d1a3658482db9444c088bdc175c5a641b477d'
OLD_TAG = 'infinity-shutdown-2103330-v1'
NEW_TAG = 'infinity-shutdown-2103334-v1'
SRC = 'tools/android/packaging/xbmc/src/'
PREIMAGES = {
    SRC+'InfinityHealthExport.java.in': 'ede79dcb038e949e0d9a0f1178ffc4de43a6bc8b830d033c911cbd8f270f0970',
    SRC+'InfinityExitDiagnostics.java.in': '156921b8a5c8530c1c11f974c69f1e3b72f067f45446174c7fd20ba047de0896',
    SRC+'InfinityCloseProgress.java.in': 'b959d92b8c4a757189f6d918e6c6233ab4a7402536ba402016040ffef173c4e3',
}
COUNTS = {
    SRC+'InfinityHealthExport.java.in': (1,1),
    SRC+'InfinityExitDiagnostics.java.in': (1,0),
    SRC+'InfinityCloseProgress.java.in': (0,1),
}

def sha(data): return hashlib.sha256(data).hexdigest()
def digest(mapping): return sha(json.dumps(mapping,sort_keys=True,separators=(',',':')).encode())
def snapshot(root):
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*')
            if p.is_file() and '.git' not in p.relative_to(root).parts}
def require(ok,message):
    if not ok: raise ValueError(message)

def transform(name,text,native_sha):
    require(name in PREIMAGES,'Unapproved Android target')
    require(re.fullmatch(r'[0-9a-f]{64}',native_sha) is not None and native_sha!=OLD_NATIVE,
            'Actual new packaged native hash required')
    require((text.count(OLD_NATIVE),text.count(OLD_TAG))==COUNTS[name],
            'Native identity counts differ: '+name)
    return text.replace(OLD_NATIVE,native_sha).replace(OLD_TAG,NEW_TAG)

def apply(source,proof,receipt,native_sha):
    parent=json.loads(proof.read_text())
    # The version-only 3333 repack legitimately retains the 3330 source receipt.
    require(parent['candidate']==2103330,'Wrong current source receipt lineage')
    before=snapshot(source)
    require(before==parent['after'] and digest(before)==PARENT_MAP,
            'Not the exact Android source installed in 3333')
    require({n:before[n] for n in PREIMAGES}==PREIMAGES,'Android preimage mismatch')
    for name in PREIMAGES:
        p=source/name;p.write_text(transform(name,p.read_text(),native_sha))
    after=snapshot(source)
    changed={n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}
    require(before.keys()==after.keys() and changed==set(PREIMAGES),
            'Unapproved Android file/behavior delta')
    result=dict(candidate=2103334,apk_parent=2103333,source_parent=2103330,
                before=before,after=after,changed=sorted(changed),native_sha256=native_sha,
                engine_tag=NEW_TAG,identity_only=True,physical_device_verified=False,locked=False)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

def verify(source,receipt):
    r=json.loads(receipt.read_text())
    require(r['candidate']==2103334 and r['changed']==sorted(PREIMAGES), 'Wrong identity receipt')
    require(digest(r['before'])==PARENT_MAP and snapshot(source)==r['after'],
            'Android changed after tests')
    for name in PREIMAGES:
        text=(source/name).read_text()
        # Invert only the declared string substitutions to prove exact parent bytes.
        require(sha(text.replace(r['native_sha256'],OLD_NATIVE).replace(NEW_TAG,OLD_TAG).encode())
                ==PREIMAGES[name], 'Android change beyond identity: '+name)
    require(all(r['before'][n]==r['after'][n] for n in r['before'] if n not in PREIMAGES),
            'Unrelated Android source changed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['apply','verify'])
    p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--proof',type=Path);p.add_argument('--native-sha');a=p.parse_args()
    if a.mode=='apply':apply(a.source,a.proof,a.receipt,a.native_sha)
    else:verify(a.source,a.receipt)
    print('PASS: exact 3333 Android source; only three engine identity strings updated')
