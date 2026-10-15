#!/usr/bin/env python3
"""Exact 2103324 Android diagnostic delta; no shutdown route or data migration."""
from pathlib import Path
import hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
PARENT_MAP='8ce33bd0159e0650e0e62034b90382a58599f15440e19fdc7a2aabfff6cfa809'
ALLOWED=sorted('tools/android/packaging/xbmc/src/'+n+'.java.in' for n in ('InfinityExitCompletion','Main','InfinityHealthExport','InfinityExitDiagnostics'))
PATCH_SHA='8f43e89333e9dbd065033bb4690ff942d83374eaf4233b7f9bc0998d935e8472'
OLD_IDENTITY='c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'
def sha(data):return hashlib.sha256(data).hexdigest()
def snapshot(root):
    if any(p.is_symlink() for p in root.rglob('*')):raise ValueError('Symlink in protected shell')
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def apply(source,proof,native_sha):
    if not re.fullmatch('[0-9a-f]{64}',native_sha):raise ValueError('Missing packaged native identity')
    expected=json.loads(proof.read_text())['after']
    if sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())!=PARENT_MAP:raise ValueError('Wrong 2103324 source receipt')
    before=snapshot(source)
    if before!=expected:raise ValueError('Source differs from locked 2103324')
    patch=HERE/'android.patch'
    if sha(patch.read_bytes())!=PATCH_SHA:raise ValueError('Android diagnostic patch integrity mismatch')
    subprocess.run(['git','apply','--check',str(patch)],cwd=source,check=True)
    subprocess.run(['git','apply',str(patch)],cwd=source,check=True)
    identity=source/'tools/android/packaging/xbmc/src/InfinityExitDiagnostics.java.in'
    text=identity.read_text()
    if text.count(OLD_IDENTITY)!=1:raise ValueError('Unexpected native identity preimage')
    identity.write_text(text.replace(OLD_IDENTITY,native_sha))
    exporter=source/'tools/android/packaging/xbmc/src/InfinityHealthExport.java.in'
    text=exporter.read_text();anchor='      manifest.put("shutdown_trace_engine", "infinity-shutdown-2103325-v1");'
    if text.count(anchor)!=1:raise ValueError('Missing shutdown export contract')
    exporter.write_text(text.replace(anchor,anchor+'\n      manifest.put("shutdown_packaged_native_sha256", "'+native_sha+'");'))
    after=snapshot(source)
    changed=sorted(n for n in before.keys()|after.keys() if before.get(n)!=after.get(n))
    if changed!=ALLOWED or before.keys()!=after.keys():raise ValueError('Undeclared Android source change')
    return {'before':before,'after':after,'changed':changed,'base':2103324,'candidate':2103325,
            'base_source_commit':'9f621f34e3ded845e1c3e9c2a49d98158b6e31b3',
            'native_engine_sha256':native_sha,'diagnostics_only':True,'shutdown_behavior_changed':False}
