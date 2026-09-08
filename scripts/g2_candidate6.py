#!/usr/bin/env python3
"""G2 #6: compile one adapter and reuse the pinned, boot-tested G2 #5 APK.

No C++/Kodi build, no broad smali substitutions, no donor assets, no v3 ABI.
Only the DEX containing InfinityCoreBridge may change. Every other class in it
must disassemble identically, and every other APK member is copied byte-for-byte.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'mapping/g2-candidate6'
MAIN = 'Lcom/projectinfinity/kodi/Main;'
BRIDGE = 'Lcom/projectinfinity/kodi/InfinityCoreBridge;'
BRIDGE_PATH = 'com/projectinfinity/kodi/InfinityCoreBridge.smali'
NATIVE_METHODS = {
    'Main': {'_callNative(JJ)V', '_doFrame(J)V', '_onActivityResult(IILandroid/content/Intent;)V',
             '_onNewIntent(Landroid/content/Intent;)V', '_onVisibleBehindCanceled()V',
             '_infinityBridgeVersion()I', '_infinityHasActiveVideo()Z',
             '_infinitySyncDisplayState()V', '_infinitySystemThemeMode()I',
             '_infinityWindowWidth()I', '_infinityWindowHeight()I'},
    'XBMCMainView': {'_attach()V', '_surfaceChanged(Landroid/view/SurfaceHolder;III)V',
                     '_surfaceCreated(Landroid/view/SurfaceHolder;)V',
                     '_surfaceDestroyed(Landroid/view/SurfaceHolder;)V'},
    'XBMCSettingsContentObserver': {'_onVolumeChanged(I)V'},
    'XBMCInputDeviceListener': {'_onInputDeviceAdded(I)V', '_onInputDeviceChanged(I)V',
                               '_onInputDeviceRemoved(I)V'},
}
BRIDGE_METHODS = {name + '(' + MAIN + ')' + ret for name, ret in {
    'getBridgeVersion': 'I', 'hasActiveVideoPlayer': 'Z', 'syncDisplayState': 'V',
    'getSystemThemeMode': 'I', 'getNativeWindowWidth': 'I', 'getNativeWindowHeight': 'I',
    'updateInfinityPictureInPictureParams': 'V', 'enterInfinityPictureInPicture': 'Z',
}.items()}
CALLBACKS = {
    'onResume()V': ('updateInfinityPictureInPictureParams', 'V'),
    'onUserLeaveHint()V': ('enterInfinityPictureInPicture', 'Z'),
    'onConfigurationChanged(Landroid/content/res/Configuration;)V': ('syncDisplayState', 'V'),
    'onPictureInPictureModeChanged(ZLandroid/content/res/Configuration;)V': ('syncDisplayState', 'V'),
    'onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V': ('syncDisplayState', 'V'),
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def spec() -> dict:
    return json.loads((CONFIG / 'baseline.json').read_text())

def run(args: list[str]) -> None:
    subprocess.run(args, check=True)

def signature_member(name: str) -> bool:
    return bool(re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))', name, re.I))

def inventory(apk: Path) -> dict[str, str]:
    with zipfile.ZipFile(apk) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('Duplicate APK members')
        return {n: digest(archive.read(n)) for n in archive.namelist()
                if not archive.getinfo(n).is_dir() and not signature_member(n)}

def check_base(apk: Path) -> None:
    if digest(apk.read_bytes()) != spec()['apk_sha256']:
        raise ValueError('Not the exact G2 #5 APK: refusing a different run, engine or signature')
    inventory(apk)

def method_map(text: str) -> dict[str, tuple[str, str]]:
    """Exact complete method blocks; names in comments/calls never count as definitions."""
    result = {}
    active = None
    lines = []
    flags = ''
    for line in text.splitlines(keepends=True):
        if line.startswith('.method '):
            if active is not None:
                raise ValueError('Nested/unclosed method block')
            declaration = line.strip().split()
            active = declaration[-1]
            if '(' not in active or ')' not in active or active in result:
                raise ValueError('Invalid or duplicate method: ' + active)
            flags = ' '.join(declaration[1:-1])
            lines = [line]
        elif line.strip() == '.end method':
            if active is None:
                raise ValueError('Unmatched method end')
            lines.append(line)
            result[active] = (flags, ''.join(lines))
            active = None
        elif active is not None:
            lines.append(line)
    if active is not None:
        raise ValueError('Unclosed method')
    return result

def classes(decoded: Path) -> dict[str, Path]:
    result = {}
    for path in decoded.glob('smali*/**/*.smali'):
        text = path.read_text()
        match = [line.split()[-1] for line in text.splitlines() if line.startswith('.class ')]
        if len(match) != 1 or match[0] in result:
            raise ValueError('Missing/duplicate class descriptor: ' + str(path))
        result[match[0]] = path
    return result

def check_map(decoded: Path) -> tuple[Path, dict[str, Path]]:
    found = classes(decoded)
    for name, expected in NATIVE_METHODS.items():
        desc = 'Lcom/projectinfinity/kodi/' + name + ';'
        if desc not in found:
            raise ValueError('Missing JNI companion: ' + name)
        methods = method_map(found[desc].read_text())
        actual = {sig for sig, (flags, _) in methods.items() if 'native' in flags.split()}
        if actual != expected:
            raise ValueError('JNI declarations differ: ' + name)
        if any('static' in methods[sig][0].split() for sig in actual):
            raise ValueError('G2 JNI methods must remain instance methods')
    main = found[MAIN].read_text()
    if re.findall(r'^\.super (.+)$', main, re.M) != ['Landroid/app/NativeActivity;']:
        raise ValueError('Main does not directly extend NativeActivity')
    methods = method_map(main)
    for sig, (bridge_name, ret) in CALLBACKS.items():
        if sig not in methods:
            raise ValueError('Missing lifecycle definition: ' + sig)
        body = methods[sig][1]
        # Ignore debug information/comments. Check executable invocations, not tokens.
        calls = [line.strip() for line in body.splitlines() if line.strip().startswith('invoke-')]
        super_calls = [c for c in calls if c.startswith('invoke-super ') and
                       'Landroid/app/NativeActivity;->' + sig in c]
        target = BRIDGE + '->' + bridge_name + '(' + MAIN + ')' + ret
        bridge_calls = [c for c in calls if target in c]
        if len(super_calls) != 1 or len(bridge_calls) != 1:
            raise ValueError('Missing/duplicate lifecycle connection: ' + sig)
        if calls.index(super_calls[0]) > calls.index(bridge_calls[0]):
            raise ValueError('Bridge invoked before lifecycle supercall: ' + sig)
        if not bridge_calls[0].startswith('invoke-static {p0}, '):
            raise ValueError('Wrong bridge invocation/register mapping: ' + sig)
    if BRIDGE not in found:
        raise ValueError('Bridge class missing')
    bridge_methods = method_map(found[BRIDGE].read_text())
    exported = {sig for sig, (flags, _) in bridge_methods.items() if 'public' in flags.split()}
    if exported != BRIDGE_METHODS or any('static' not in bridge_methods[s][0].split() for s in exported):
        raise ValueError('Bridge public static descriptors changed')
    if any('native' in flags.split() for flags, _ in bridge_methods.values()):
        raise ValueError('Do not add native declarations to the adapter')
    native_calls = set(re.findall(re.escape(MAIN) + r'->(_infinity\w+\([^)]*\)[VZIFJ])', found[BRIDGE].read_text()))
    if native_calls != {s for s in NATIVE_METHODS['Main'] if s.startswith('_infinity')}:
        raise ValueError('Bridge calls do not match the six G2 native methods')
    root = ET.parse(decoded / 'AndroidManifest.xml').getroot()
    ns = '{http://schemas.android.com/apk/res/android}'
    if root.get('package') != 'com.projectinfinity.kodi':
        raise ValueError('Wrong Android package')
    activities = [a for a in root.iter('activity') if a.get(ns+'name') in ('.Main','com.projectinfinity.kodi.Main')]
    if len(activities) != 1:
        raise ValueError('Main manifest activity is ambiguous/missing')
    a = activities[0]
    if a.get(ns+'supportsPictureInPicture') != 'true' or a.get(ns+'resizeableActivity') != 'true':
        raise ValueError('Missing existing PiP/resize capability')
    native_names = [e.get(ns+'value') for e in a.findall('meta-data') if e.get(ns+'name') == 'android.app.lib_name']
    if native_names != ['kodi']:
        raise ValueError('Wrong native library in manifest')
    return found[BRIDGE], found

def compare_classes(before: dict[str, Path], after: dict[str, Path]) -> None:
    if set(before) != set(after):
        raise ValueError('Unexpected added/deleted class; compile-only stubs must never ship')
    for desc in before:
        if desc != BRIDGE and before[desc].read_bytes() != after[desc].read_bytes():
            raise ValueError('Protected class changed: ' + desc)

def install_bridge(decoded: Path, generated: Path) -> None:
    target, _ = check_map(decoded)
    original = target.read_bytes()
    replacement = generated.read_bytes()
    if original == replacement:
        return  # Idempotent: no duplicated callbacks, no unnecessary rewrite.
    if digest(original) != spec()['decoded_bridge_sha256']:
        raise ValueError('Unknown bridge preimage: refusing to overwrite another implementation')
    temporary = target.with_suffix('.smali.new')
    temporary.write_bytes(replacement)
    os.replace(temporary, target)
    try:
        check_map(decoded)
    except Exception:
        target.write_bytes(original)
        raise

def decode(apktool: Path, apk: Path, output: Path, no_res: bool = False) -> None:
    args = ['java', '-jar', str(apktool), 'd', '-f', str(apk), '-o', str(output)]
    if no_res:
        args.append('-r')
    run(args)

def compile_bridge(android_jar: Path, d8: Path, apktool: Path, apk: Path, work: Path) -> Path:
    src = work / 'java/com/projectinfinity/kodi'
    src.mkdir(parents=True)
    shutil.copyfile(CONFIG / 'InfinityCoreBridge.java', src / 'InfinityCoreBridge.java')
    ret = {'I':'int','Z':'boolean','V':'void'}
    natives = '\n'.join(' public native '+ret[s[-1]]+' '+s[:-3]+'();' for s in
                        sorted(NATIVE_METHODS['Main']) if s.startswith('_infinity'))
    (src / 'Main.java').write_text('package com.projectinfinity.kodi;\n'
            'public class Main extends android.app.NativeActivity {\n'+natives+'\n}\n')
    out = work / 'java-classes'
    out.mkdir()
    run(['javac', '-source','8','-target','8','-cp',str(android_jar),'-d',str(out),
         str(src / 'Main.java'),str(src / 'InfinityCoreBridge.java')])
    jar = work / 'bridge.jar'
    stubjar = work / 'compile-only.jar'
    with zipfile.ZipFile(jar, 'w') as z:
        compiled = sorted(out.rglob('InfinityCoreBridge*.class'))
        if len(compiled) != 1:
            raise ValueError('Expected one adapter class, no new companion classes')
        z.write(compiled[0], compiled[0].relative_to(out).as_posix())
    with zipfile.ZipFile(stubjar, 'w') as z:
        p = out/'com/projectinfinity/kodi/Main.class'
        z.write(p, p.relative_to(out).as_posix())
    dexdir = work/'bridge-dex'
    dexdir.mkdir()
    run([str(d8), '--lib',str(android_jar),'--classpath',str(stubjar),'--min-api','21',
         '--output',str(dexdir),str(jar)])
    mini = work/'bridge-compile-fixture.apk'
    with zipfile.ZipFile(apk) as base, zipfile.ZipFile(mini,'w') as z:
        z.writestr('AndroidManifest.xml',base.read('AndroidManifest.xml'))
        z.writestr('resources.arsc',base.read('resources.arsc'))
        z.write(dexdir/'classes.dex','classes.dex')
    decoded = work/'bridge-decoded'
    decode(apktool,mini,decoded,no_res=True)
    generated = classes(decoded)
    if set(generated) != {BRIDGE}:
        raise ValueError('Adapter DEX contains unexpected classes')
    return generated[BRIDGE]

def transplant(base: Path, rebuilt: Path, dex_name: str, output: Path) -> None:
    # zip copies unchanged compressed entries rather than recompressing libkodi.so.
    # Nothing from apktool's rebuilt resource table/assets/native set is imported.
    with zipfile.ZipFile(base) as original:
        removed = [n for n in original.namelist() if signature_member(n)]
    shutil.copyfile(base, output)
    run(['zip', '-q', '-d', str(output), dex_name] + removed)
    with tempfile.TemporaryDirectory(prefix='g2-dex-') as tmp:
        dex = Path(tmp)/dex_name
        with zipfile.ZipFile(rebuilt) as build:
            dex.write_bytes(build.read(dex_name))
        subprocess.run(['zip', '-q', '-1', str(output), dex_name], cwd=tmp, check=True)
    expected = inventory(base)
    actual = inventory(output)
    changed = {n for n in expected.keys() | actual.keys() if expected.get(n) != actual.get(n)}
    if changed != {dex_name}:
        raise ValueError('APK changed outside the one allowed DEX: '+repr(changed))

def build(base: Path, apktool: Path, sdk: Path, output: Path) -> None:
    base, apktool, sdk, output = (p.resolve() for p in (base, apktool, sdk, output))
    check_base(base)
    if digest(apktool.read_bytes()) != spec()['apktool_sha256']:
        raise ValueError('Apktool version/hash differs from the verified decoder')
    if base == output:
        raise ValueError('Do not overwrite #5')
    if output.exists():
        raise ValueError('Output already exists; use a new output path')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='g2-c6-') as tmp:
        work = Path(tmp)
        decoded = work/'baseline'
        decode(apktool,base,decoded)
        old_bridge, before = check_map(decoded)
        dex_dir = old_bridge.relative_to(decoded).parts[0]
        dex_name = 'classes.dex' if dex_dir == 'smali' else dex_dir[6:]+'.dex'
        if dex_name != spec()['bridge_dex']:
            raise ValueError('Unexpected original DEX ownership')
        stage = work/'staged'
        shutil.copytree(decoded,stage)
        generated = compile_bridge(sdk/'platforms/android-34/android.jar',
                                   sdk/'build-tools/34.0.0/d8',apktool,base,work)
        install_bridge(stage,generated)
        mapped = inventory_smali(stage)
        install_bridge(stage,generated)
        if inventory_smali(stage) != mapped:
            raise ValueError('Mapper not idempotent')
        compare_classes(before,classes(stage))
        rebuilt = work/'rebuilt.apk'
        run(['java','-jar',str(apktool),'b',str(stage),'-o',str(rebuilt)])
        candidate = work/'candidate-unsigned.apk'
        transplant(base,rebuilt,dex_name,candidate)
        final = work/'final'
        decode(apktool,candidate,final)
        final_bridge, final_classes = check_map(final)
        compare_classes(before,final_classes)
        # Also prove the compiler output is what shipped, after assembler round-trip.
        if final_bridge.read_bytes() != generated.read_bytes():
            raise ValueError('Compiled adapter changed during assembly')
        info = inventory(base)
        report = {**spec(), 'candidate':6, 'candidate_apk_sha256':digest(candidate.read_bytes()),
                  'signed':False, 'engine_rebuilt':False, 'native_libraries_unchanged':sum(n.endswith('.so') for n in info),
                  'dex_members':sum(bool(re.fullmatch(r'classes\d*\.dex',n)) for n in info),
                  'protected_classes_unchanged':len(before)-1,
                  'changed_apk_members':[dex_name], 'changed_class':BRIDGE,
                  'main_and_lifecycle_callbacks_unchanged':True,
                  'mapper_idempotent':True,'device_testing':'pending',
                  'source_java_sha256':digest((CONFIG/'InfinityCoreBridge.java').read_bytes())}
        # Atomic publication on the destination filesystem; never expose an unchecked APK.
        fd, pending = tempfile.mkstemp(prefix='.g2-c6-',dir=output.parent)
        os.close(fd)
        try:
            shutil.copyfile(candidate,pending)
            os.replace(pending,output)
        finally:
            if os.path.exists(pending): os.unlink(pending)
        output.with_suffix('.verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))

def inventory_smali(root: Path) -> dict[str,str]:
    return {p.relative_to(root).as_posix():digest(p.read_bytes()) for p in root.glob('smali*/**/*.smali')}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--apktool',type=Path,required=True)
    p.add_argument('--sdk',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    build(a.base,a.apktool,a.sdk,a.output)

if __name__ == '__main__': main()
