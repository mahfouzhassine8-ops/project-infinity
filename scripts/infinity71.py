#!/usr/bin/env python3
"""Pinned source preparation and byte-preserving presentation packaging for Infinity 7.1.

Only the engine job changes Java/native code. Presentation overlays can change four
allowlisted skin assets; every other APK member must remain byte-identical.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[1]
PATCHES = REPO / 'patches/infinity-7.1-audited'
ASSETS = REPO / 'assets/infinity-7.1'
PACKAGE = 'com.projectinfinity.kodi'
ICON_SOURCE = 'tools/android/packaging/xbmc/res/drawable-nodpi/project_infinity_icon.png'
SKIN = 'assets/addons/skin.estuary/'
LOCK_FILES = {
    'Custom_1199_InfinityVideoLock.xml': SKIN + 'xml/Custom_1199_InfinityVideoLock.xml',
    'infinity-lock.png': SKIN + 'media/osd/fullscreen/buttons/infinity-lock.png',
    'infinity-unlock.png': SKIN + 'media/osd/fullscreen/buttons/infinity-unlock.png',
}
OVERLAY_ALLOWLIST = set(LOCK_FILES.values()) | {SKIN + 'xml/VideoOSD.xml'}
LOCK_BUTTON = '''<control type="radiobutton" id="7999">
                        <include content="OSDButton">
                            <param name="texture" value="osd/fullscreen/buttons/infinity-lock.png"/>
                        </include>
                        <label>Lock screen</label>
                        <onclick>Dialog.Close(VideoOSD)</onclick>
                        <onclick>ActivateWindow(1199)</onclick>
                        <visible>Player.HasVideo</visible>
                    </control>
                    '''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def contract() -> dict:
    return json.loads((PATCHES / 'contract.json').read_text())


def asset_check() -> None:
    provenance = json.loads((ASSETS / 'provenance.json').read_text())
    if provenance['donor_artifact'] != 10037657045:
        raise ValueError('Wrong donor: the approved lock comes from the actual 7.0 artifact')
    for name, meta in provenance['files'].items():
        if sha((ASSETS / name).read_bytes()) != meta['sha256']:
            raise ValueError('Preserved asset hash mismatch: ' + name)


def prepare_source(source: Path) -> None:
    source = source.resolve()
    asset_check()
    spec = contract()
    current = {name: sha((source/name).read_bytes()) if (source/name).exists() else None
               for name in spec['files']}
    icon = source / ICON_SOURCE
    icon_data = (ASSETS / 'project_infinity_icon.png').read_bytes()
    if all(current[p] == h['after'] for p, h in spec['files'].items()):
        if not icon.exists() or icon.read_bytes() != icon_data:
            raise ValueError('Source patch exists but the expected branding asset differs/missing')
        print('Source already matches the complete audited contract (idempotent).')
        return
    mismatch = [p for p, h in spec['files'].items() if current[p] != h['before']]
    if mismatch:
        raise ValueError('Refusing mixed/unpinned source: ' + ', '.join(mismatch))
    if icon.exists():
        raise ValueError('Unexpected pre-existing branding asset: ' + str(icon))
    patch = str(PATCHES / 'source.patch')
    # Exact preimage hashes plus a dry run prevent fuzzy or partial-version patching.
    subprocess.run(['patch', '--dry-run', '--batch', '--fuzz=0', '-p1', '-i', patch],
                   cwd=source, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', patch],
                   cwd=source, check=True, stdout=subprocess.DEVNULL)
    icon.parent.mkdir(parents=True, exist_ok=True)
    icon.write_bytes(icon_data)
    for name, h in spec['files'].items():
        if sha((source/name).read_bytes()) != h['after']:
            raise ValueError('Postimage mismatch: ' + name)
    print('Applied the exact Kodi 21.3 / Infinity bridge v3 source set.')


def uleb(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 35, 7):
        b = data[pos]; pos += 1
        value |= (b & 0x7f) << shift
        if b < 128:
            return value, pos
    raise ValueError('Malformed DEX uleb128')


def dex_native_methods(data: bytes, class_name: str) -> dict[str, str] | None:
    """Read the actual class_data native flags and prototypes, not string occurrences."""
    if data[:4] != b'dex\n' or len(data) < 112:
        raise ValueError('Not a standard DEX file')
    def word(at): return struct.unpack_from('<I', data, at)[0]
    strings=[]
    for i in range(word(56)):
        pos=word(word(60)+4*i); _,pos=uleb(data,pos)
        strings.append(data[pos:data.index(b'\0',pos)].decode('utf-8','replace'))
    types=[strings[word(word(68)+4*i)] for i in range(word(64))]
    protos=[]
    for i in range(word(72)):
        _,ret,params=struct.unpack_from('<III',data,word(76)+12*i)
        args=[] if not params else [types[struct.unpack_from('<H',data,params+4+2*j)[0]] for j in range(word(params))]
        protos.append('('+''.join(args)+')'+types[ret])
    methods=[]
    for i in range(word(88)):
        cls,proto,name=struct.unpack_from('<HHI',data,word(92)+8*i)
        methods.append((types[cls],strings[name],protos[proto]))
    for i in range(word(96)):
        entry=word(100)+32*i
        if types[word(entry)] != class_name: continue
        pos=word(entry+24)
        if not pos: return {}
        counts=[]
        for _ in range(4): n,pos=uleb(data,pos);counts.append(n)
        for _ in range(counts[0]+counts[1]):
            _,pos=uleb(data,pos);_,pos=uleb(data,pos)
        natives={}
        for count in counts[2:]:
            index=0
            for _ in range(count):
                delta,pos=uleb(data,pos);index+=delta
                flags,pos=uleb(data,pos);_,pos=uleb(data,pos)
                owner,name,proto=methods[index]
                if flags & 0x100:
                    if name in natives: raise ValueError('Duplicate/overloaded native method: '+name)
                    natives[name]=proto
        return natives
    return None


def apk_hashes(apk: Path) -> dict[str,str]:
    with zipfile.ZipFile(apk) as z:
        if len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Duplicate ZIP members are not allowed')
        return {n:sha(z.read(n)) for n in z.namelist() if not z.getinfo(n).is_dir() and not signing_member(n)}


def signing_member(name: str) -> bool:
    return bool(re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:RSA|DSA|EC|SF))',name,re.I))


def check_apk_contract(apk: Path) -> None:
    expected = {
        '_onNewIntent':'(Landroid/content/Intent;)V',
        '_onActivityResult':'(IILandroid/content/Intent;)V',
        '_doFrame':'(J)V', '_callNative':'(JJ)V', '_onVisibleBehindCanceled':'()V',
        **contract()['jni'],
    }
    found=[]
    from infinity71_axml import package_name
    with zipfile.ZipFile(apk) as z:
        if package_name(z.read('AndroidManifest.xml')) != PACKAGE:
            raise ValueError('APK would install under the wrong Android package')
        for n in z.namelist():
            if re.fullmatch(r'classes\d*\.dex',n):
                methods=dex_native_methods(z.read(n),'Lcom/projectinfinity/kodi/Main;')
                if methods is not None: found.append(methods)
        if len(found)!=1 or found[0]!=expected:
            raise ValueError('Final DEX native declarations do not equal the compiled JNI contract: '+repr(found))
        if 'lib/arm64-v8a/libkodi.so' not in z.namelist():
            raise ValueError('Matched ARM64 Kodi engine missing')


def record_engine(apk: Path, output: Path, source_commit: str) -> None:
    check_apk_contract(apk)
    hashes=apk_hashes(apk)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({
        'schema':1,'bridge_version':contract()['bridge_version'],
        'kodi_sha':contract()['kodi_sha'],'source_commit':source_commit,
        'source_patch_sha256':sha((PATCHES/'source.patch').read_bytes()),
        'base_apk_sha256':sha(apk.read_bytes()),'package':PACKAGE,
        'files':hashes,
        'native_libraries':{n:h for n,h in hashes.items() if n.endswith('.so')},
        'dex':{n:h for n,h in hashes.items() if re.fullmatch(r'classes\d*\.dex',n)},
    },indent=2,sort_keys=True)+'\n')
    print('Recorded independently reusable matched engine, DEX and complete APK inventory.')


def check_engine(apk: Path, manifest: Path) -> dict:
    engine=json.loads(manifest.read_text())
    if engine['package']!=PACKAGE or engine['bridge_version']!=contract()['bridge_version'] or engine['kodi_sha']!=contract()['kodi_sha']:
        raise ValueError('Wrong engine identity/version')
    if engine['source_patch_sha256']!=sha((PATCHES/'source.patch').read_bytes()):
        raise ValueError('Engine does not match this pinned source patch')
    if sha(apk.read_bytes())!=engine['base_apk_sha256'] or apk_hashes(apk)!=engine['files']:
        raise ValueError('Base APK integrity mismatch')
    check_apk_contract(apk)
    return engine


def overlay(apk: Path, manifest: Path, output: Path) -> None:
    asset_check(); engine=check_engine(apk,manifest)
    if apk.resolve()==output.resolve(): raise ValueError('Keep the reusable base unchanged')
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(apk) as src:
        osd=src.read(SKIN+'xml/VideoOSD.xml').decode('utf-8')
        marker='<control type="radiobutton" id="804">'
        if 'id="7999"' in osd: raise ValueError('Base already contains an unknown lock overlay')
        if osd.count(marker)!=1: raise ValueError('Exact Kodi 21.3 OSD insertion point missing')
        osd=osd.replace(marker,LOCK_BUTTON+marker,1)
        ET.fromstring(osd)
        ET.fromstring((ASSETS/'Custom_1199_InfinityVideoLock.xml').read_bytes())
        additions={target:(ASSETS/name).read_bytes() for name,target in LOCK_FILES.items()}
        additions[SKIN+'xml/VideoOSD.xml']=osd.encode('utf-8')
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'w',allowZip64=True) as dst:
            for item in src.infolist():
                if signing_member(item.filename) or item.filename in additions: continue
                dst.writestr(item,src.read(item.filename))
            for name,data in additions.items():
                dst.writestr(name,data,compress_type=zipfile.ZIP_DEFLATED)
    verify_overlay(output,manifest)
    print('Preserved original 7.0 lock and all engine/DEX/stock assets. Output is unsigned.')


def verify_overlay(apk: Path, manifest: Path) -> None:
    engine=json.loads(manifest.read_text()); hashes=apk_hashes(apk)
    before=engine['files']
    changed={n for n in before.keys() | hashes.keys() if before.get(n)!=hashes.get(n)}
    if not changed.issubset(OVERLAY_ALLOWLIST):
        raise ValueError('Presentation changed protected engine files: '+repr(sorted(changed-OVERLAY_ALLOWLIST)))
    for name,target in LOCK_FILES.items():
        if hashes.get(target)!=sha((ASSETS/name).read_bytes()):
            raise ValueError('Lock not preserved: '+target)
    check_apk_contract(apk)
    print('Verified byte-identical native libraries, DEX, manifest, resources, resume code and all other protected members.')


def native_compile_check(build_dir: Path) -> None:
    entries=json.loads((build_dir/'compile_commands.json').read_text())
    targets=['xbmc/platform/android/activity/JNIMainActivity.cpp',
             'xbmc/platform/android/activity/XBMCApp.cpp',
             'xbmc/windowing/android/WinSystemAndroid.cpp']
    import shlex
    for target in targets:
        matches=[e for e in entries if e['file'].endswith('/'+target)]
        if len(matches)!=1: raise ValueError('Missing/ambiguous real compile command: '+target)
        e=matches[0]; args=e.get('arguments') or shlex.split(e['command'])
        filtered=[];i=0
        while i<len(args):
            if args[i] in ('-o','-MF','-MT','-MQ'): i+=2;continue
            if args[i] in ('-c','-MD','-MMD','-MP'): i+=1;continue
            filtered.append(args[i]);i+=1
        filtered.append('-fsyntax-only')
        print('Early native compiler gate: '+target,flush=True)
        subprocess.run(filtered,cwd=e['directory'],check=True)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__); subs=p.add_subparsers(dest='cmd',required=True)
    s=subs.add_parser('source');s.add_argument('--source',required=True,type=Path)
    s=subs.add_parser('record-engine');s.add_argument('--apk',required=True,type=Path);s.add_argument('--output',required=True,type=Path);s.add_argument('--source-commit',required=True)
    for cmd in ['overlay','verify-overlay']:
        s=subs.add_parser(cmd);s.add_argument('--apk',required=True,type=Path);s.add_argument('--manifest',required=True,type=Path)
        if cmd=='overlay':s.add_argument('--output',required=True,type=Path)
    s=subs.add_parser('native-check');s.add_argument('--build-dir',required=True,type=Path)
    a=p.parse_args()
    if a.cmd=='source':prepare_source(a.source)
    elif a.cmd=='record-engine':record_engine(a.apk,a.output,a.source_commit)
    elif a.cmd=='overlay':overlay(a.apk,a.manifest,a.output)
    elif a.cmd=='verify-overlay':verify_overlay(a.apk,a.manifest)
    elif a.cmd=='native-check':native_compile_check(a.build_dir)

if __name__=='__main__':main()
