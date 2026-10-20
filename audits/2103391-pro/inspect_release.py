#!/usr/bin/env python3
"""Read-only audit of pinned 2103391 APK and matching install-over ZIPs.

This is not a runtime or physical-Fold pass. Never changes the APK or addon code.
Outputs contain only first-party source and build metadata; no user diagnostics.
"""
from __future__ import annotations
import hashlib, json, re, subprocess, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'pro-audit-output'
OUT.mkdir(exist_ok=True)

def sha(data): return hashlib.sha256(data).hexdigest()
def one(root, pattern):
    hits=list(Path(root).rglob(pattern))
    if len(hits)!=1: raise RuntimeError(f'Expected exactly one {pattern}: {hits}')
    return hits[0]

def main():
    apk=one('audit-original','Infinity-2103391-All-In-One-Bugfix-EXPERIMENTAL.apk')
    receipt=json.loads(one('audit-original','INFINITY-2103391-SIGNED-EXPERIMENTAL.json').read_text())
    assert sha(apk.read_bytes())==receipt['apk_sha256'],'Original signed APK receipt mismatch'
    assert receipt['signed_permanently'] and receipt['signer_sha256']=='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
    report={'apk_sha256':receipt['apk_sha256'],'apk_bytes':apk.stat().st_size,'actual_fold_tested_by_this_audit':False,'runtime_code_modified':False,'final_lock':False}
    installed={}
    with zipfile.ZipFile(apk) as z:
        assert z.testzip() is None
        names=z.namelist(); assert len(names)==len(set(names))
        embedded={n[len('assets/addons/'):]:z.read(n) for n in names if n.startswith('assets/addons/') and not n.endswith('/')}
        report['apk_member_count']=len(names)
        report['largest_apk_members']=[{'path':i.filename,'bytes':i.file_size,'compressed':i.compress_size} for i in sorted(z.infolist(),key=lambda i:i.file_size,reverse=True)[:12]]
        native=z.read('lib/arm64-v8a/libkodi.so')
        report['native_sha256']=sha(native)
        lib=OUT/'original-libkodi.so';lib.write_bytes(native)
        for flag,label in [('-n','native-notes'),('-SW','native-sections')]:
            p=subprocess.run(['readelf',flag,str(lib)],capture_output=True,text=True,check=True)
            (OUT/(label+'.txt')).write_text(p.stdout)
        lib.unlink()
    for p in Path('audit-matching').rglob('*.zip'):
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            for n in z.namelist():
                if not n.endswith('/'):
                    assert n not in installed,f'Duplicate delivered path: {n}'
                    installed[n]=z.read(n)
    assert installed,'No matching standalone ZIPs found'
    def manifests(payload):
        return {ET.fromstring(v).get('id'):ET.fromstring(v).get('version') for n,v in payload.items() if n.count('/')==1 and n.endswith('/addon.xml')}
    report['embedded_versions']=manifests(embedded)
    report['standalone_versions']=manifests(installed)
    contract=ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
    pairs=sorted(set(re.findall(r'\{\s*"([^"]+/[^"]+)"\s*,\s*"([0-9a-f]{64})"\s*\}',contract.read_text())))
    assert pairs,'Could not parse native pinned contracts'
    comparisons=[]
    for path,expected in pairs:
        for label,payload in [('embedded',embedded),('standalone',installed)]:
            if path in payload:
                actual=sha(payload[path])
                comparisons.append({'payload':label,'path':path,'expected':expected,'actual':actual,'match':actual==expected,'pin_present_in_native_binary':expected.encode() in native})
    report['native_contract_comparisons']=comparisons
    report['native_contract_mismatches']=[v for v in comparisons if not v['match']]
    report['standalone_member_changes']=[{'path':n,'embedded_sha256':sha(embedded[n]) if n in embedded else None,'standalone_sha256':sha(v)} for n,v in installed.items() if embedded.get(n)!=v]
    excerpts=[]
    for label,payload in [('embedded',embedded),('standalone',installed)]:
        for n,data in sorted(payload.items()):
            if 'CONTROLLER-PREIMAGES.json' in n:
                excerpts.append('\n### '+label+' '+n+'\n'+data.decode())
            if n.endswith('.py') and n.split('/')[0] in ('script.infinity.commandcenter','script.infinity.watchedbridge','script.infinity.uirepair'):
                text=data.decode('utf-8',errors='replace');lines=text.splitlines();interesting=set()
                for i,line in enumerate(lines):
                    if any(term in line for term in ('0.3.5.20','0.3.5.21','CONTROLLER-PREIMAGES','expected_version','addon_version','preimage','VERSION','version mismatch')):
                        interesting.update(range(max(0,i-4),min(len(lines),i+6)))
                if interesting:
                    excerpts.append('\n### '+label+' '+n+'\n'+'\n'.join(f'{i+1}: {lines[i]}' for i in sorted(interesting)))
    (OUT/'first-party-contract-excerpts.txt').write_text('\n'.join(excerpts))
    source_hits=[]
    for base in ('repairs/android-checkpoint-shutdown','repairs/four-repair-20261018','repairs/2103390-bugfixes'):
        for p in (ROOT/base).rglob('*'):
            if p.is_file() and p.suffix in ('.py','.cpp','.h','.java','.smali','.json') and p.stat().st_size<2_000_000:
                for i,line in enumerate(p.read_text(errors='replace').splitlines()):
                    if any(term in line for term in ('legacy_or_unknown','exactly_one_canonical_resident_required','command_center_applied','0.3.5.20')):
                        source_hits.append(f'{p.relative_to(ROOT)}:{i+1}: {line[:500]}')
    (OUT/'startup-source-hits.txt').write_text('\n'.join(source_hits)+'\n')
    (OUT/'release-coherence.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('=== RELEASE COHERENCE SUMMARY ===')
    print(json.dumps({k:v for k,v in report.items() if k not in ('embedded_versions','native_contract_comparisons')},indent=2))
    for label,name in [('NATIVE ELF SECTIONS','native-sections.txt'),('FIRST-PARTY GUARDS','first-party-contract-excerpts.txt'),('STARTUP ROUTING GUARDS','startup-source-hits.txt')]:
        print('\n=== '+label+' ===\n'+(OUT/name).read_text())
    print('=== EXISTING GROUP TEST FILES ===')
    for p in sorted((ROOT/'repairs/2103390-bugfixes').glob('group*/test*.py')):print(p.relative_to(ROOT))
    if report['native_contract_mismatches']:
        print('AUDIT FAIL: exact runtime contract mismatches found; no APK changed.')
        return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
