#!/usr/bin/env python3
"""Additional RC2-to-RC3 preservation gates; never relax the existing run-40 gates."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from infinity_cobra_async_lifecycle import LIVE, GRADLE, PREIMAGE, transform


def sha(data):return hashlib.sha256(data).hexdigest()

def inventory(root):
    files=list((root/'tools/android/packaging/xbmc').rglob('*'))+[root/'cmake/scripts/android/Install.cmake']
    return {str(p.relative_to(root)):p.read_bytes() for p in files if p.is_file()}

def source(before,after,out):
    old,new=inventory(before),inventory(after)
    changed={n for n in old.keys()|new.keys() if old.get(n)!=new.get(n)}
    assert changed=={str(LIVE),str(GRADLE)},changed
    assert sha(old[str(LIVE)])==PREIMAGE
    assert new[str(LIVE)].decode()==transform(old[str(LIVE)].decode())
    restored=new[str(GRADLE)].decode().replace('versionCode 2103138','versionCode 2103137').replace('1.0.9-Infinity-Lifecycle-Repair-RC3','1.0.9-Infinity-Background-Control-RC2')
    assert restored.encode()==old[str(GRADLE)],'Gradle drift beyond identity'
    report={'source_changed_files':sorted(changed),'all_other_android_source_files_byte_identical':len(old)-2,
            'main_service_background_control_manifest_and_resources_unchanged':True,
            'device_tested':False}
    out.write_text(json.dumps(report,indent=2)+'\n');print('PASS: only Cobra Activity and version identity changed from exact RC2')

def apk(base,candidate,base_manifest,manifest,out):
    from package_background_resume import verify_bytes,manifest_tree,DEX
    assert sha(base.read_bytes())=='d709c9dbf7224a9cfe4198cffb3adf523449fdc34af8c373f1c4463cdb494930'
    old,new=manifest_tree(base_manifest.read_text()),manifest_tree(manifest.read_text())
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'):tree['attrs'].pop(key,None)
    assert old==new,'Compiled manifest differs from RC2 beyond version'
    report=verify_bytes(base,candidate)
    with zipfile.ZipFile(candidate) as z:
        dex=b''.join(z.read(n) for n in z.namelist() if DEX.fullmatch(n))
    for token in (b'mCobraAsyncDestroyed',b'submitCobraIo',b'publishCobraUi',b'closeCobraAsyncWork'):
        assert token in dex,token
    report.update(apk_sha256=sha(candidate.read_bytes()),rc2_payload_preserved=True,
      rc2_compiled_manifest_preserved_except_version=True,async_guard_in_final_dex=True,device_tested=False)
    out.write_text(json.dumps(report,indent=2)+'\n');print('PASS: final RC3 matches RC2 native/assets/resources/manifest and includes compiled lifecycle guard')

if __name__=='__main__':
    p=argparse.ArgumentParser();subs=p.add_subparsers(dest='mode',required=True)
    s=subs.add_parser('source');s.add_argument('--before',type=Path,required=True);s.add_argument('--after',type=Path,required=True);s.add_argument('--out',type=Path,required=True)
    s=subs.add_parser('apk')
    for name in ('base','candidate','base-manifest','manifest','out'):s.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.mode=='source':source(a.before,a.after,a.out)
    else:apk(a.base,a.candidate,a.base_manifest,a.manifest,a.out)
