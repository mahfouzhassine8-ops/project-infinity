#!/usr/bin/env python3
"""One chooser presentation delta over proven 2103295. No native compilation or skin mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

VC=2103296
REL='1.0.9-Cosmic-Chooser-RC1'
PARENT='dba26141addbacd64f334bcc32633669ffcc3c4677961e7ce3e23f01684416a0'
NATIVE='b3f32d5c5a3c346b7c0b15e382d0b43e0d6e795edabadb9e6b4175209043cf61'
COMMIT='c562d7d1b0a5cb71df90484dc56a3fae6bf17001'
JAVA=Path('tools/android/packaging/xbmc/src')
HERE=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def once(s,old,new):
    assert s.count(old)==1,('Unexpected source preimage',old[:120],s.count(old))
    return s.replace(old,new,1)

def apply(root,base,out):
    assert H(base)==PARENT,'Not the verified signed 2103295 APK'
    src=root/'shell-kodi'
    assert H(src/JAVA/'InfinityGlassChooser.java.in')=='36f25bc517cae1ca07876643f2eaa1ce2ce4493a90064fab8495c57814a65031'
    assert H(src/JAVA/'Splash.java.in')=='0f3a7919c67a29f7de13ea0441f9cd1b736438d5c3ea18e11bca4afd0df5d255'
    # Complete the already-inherited 3291 trace-only baseline before defining this UI delta.
    trace=src/JAVA/'InfinityResponsiveTrace.java.in';t=trace.read_text()
    if 'Infinity in-place responsive reflow:' not in t:
        t=once(t,'        line.contains("Infinity responsive window:") ||',
               '        line.contains("Infinity responsive window:") ||\n        line.contains("Infinity in-place responsive reflow:") ||')
        trace.write_text(t)
    before={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    for name in ('InfinityGlassChooser.java.in','InfinityCosmicArt.java.in','InfinityChooserWeather.java.in'):
        shutil.copy2(HERE/name,src/JAVA/name)
    install=src/'cmake/scripts/android/Install.cmake'
    install.write_text(once(install.read_text(),'                  src/InfinityGlassChooser.java',
                       '                  src/InfinityGlassChooser.java\n                  src/InfinityCosmicArt.java\n                  src/InfinityChooserWeather.java'))
    gradle=src/'tools/android/packaging/xbmc/build.gradle.in';t=gradle.read_text()
    t=once(t,'versionCode 2103290',f'versionCode {VC}')
    t=once(t,'versionName "1.0.9-Native-Responsive-Layout-RC1"',f'versionName "{REL}"');gradle.write_text(t)
    t=once(t,'    ndkPath "@NDKROOT@"\n','')
    gradle.write_text(t)  # Java-only donor compilation has no NDK/toolchain dependency.
    after={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    changed=[p for p in sorted(before) if before[p]!=after.get(p)]
    added=sorted(set(after)-set(before))
    assert changed==sorted(['cmake/scripts/android/Install.cmake',str(JAVA/'InfinityGlassChooser.java.in'),'tools/android/packaging/xbmc/build.gradle.in']),changed
    assert added==[str(JAVA/'InfinityChooserWeather.java.in'),str(JAVA/'InfinityCosmicArt.java.in')],added
    assert not (set(before)-set(after))
    with zipfile.ZipFile(base) as z:
        assert hashlib.sha256(z.read('lib/arm64-v8a/libkodi.so')).hexdigest()==NATIVE
        # Use the parent bytes of every non-Kodi native library, never rebuild observer/crash code.
        for name in ('libinfinityambient.so','libinfinitycrash.so'):
            (root/'engine'/name).write_bytes(z.read('lib/arm64-v8a/'+name))
    metadata=root/'scripts/infinity_background_resume.py';t=metadata.read_text()
    for old,new in [
        ('VERSION_CODE = 2103288',f'VERSION_CODE = {VC}'),
        ("RELEASE = '1.0.9-Evidence-First-Health-RC1'",f"RELEASE = '{REL}'"),
        ("BASE_COMMIT = 'c0c150b30008cee17df39e2a79a0c07e9a91f72a'",f"BASE_COMMIT = '{COMMIT}'"),
        ("BASE_APK_SHA256 = '64ed5ce79096a3e09d02907cf72d3a5c4ad20186da231898c92db83e540d266b'",f"BASE_APK_SHA256 = '{PARENT}'"),
        ("BASE_ENGINE_SHA256 = 'f6eb05f091bfe7a624105a0a83744a292e229b385d39c1b6a23f8bf954a2522a'",f"BASE_ENGINE_SHA256 = '{NATIVE}'")]:
        t=once(t,old,new)
    metadata.write_text(t)
    receipt={'schema':1,'base_source_commit':COMMIT,'base_apk_sha256':PARENT,'native_engine_sha256':NATIVE,
             'version_code':VC,'release':REL,'candidate_locked':False,'physical_device_verified':False,
             'files':{p:{'before':before.get(p),'after':h} for p,h in after.items()}}
    (root/'engine/background-resume-source.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    # Keep the proven assembler, stable resource IDs, permanent signer and manifest verifier.
    # Tighten its old observer exception to exact pre-existing JNI/native-byte equality.
    pkg=root/'scripts/package_background_resume.py';t=pkg.read_text()
    old="original_native | {('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'requestToken', '()J'), ('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'surfaceAvailable', '(Z)V'), ('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'publish', '(J[III)V'), ('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'failure', '(JI)V')}"
    t=once(t,old,'original_native')
    old="dex_contract(a)[0] | {('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'requestToken', '()J'), ('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'surfaceAvailable', '(Z)V'), ('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'publish', '(J[III)V'), ('Lcom/projectinfinity/kodi/InfinityKodiSurfaceSampler;', 'failure', '(JI)V')}"
    t=once(t,old,'dex_contract(a)[0]')
    t=t.replace('Infinity-2103288-Evidence-First-Health-RC1',f'Infinity-{VC}-Cosmic-Chooser-RC1')
    t=once(t,"'base_run':36933314038","'base_run':37092252001")
    t=once(t,"'updated_presentation_library':'libinfinityambient.so'","'updated_presentation_library':None")
    t=once(t,"shutil.copy2(ROOT/'repairs/evidence-health-2103288/DEVICE-TEST.md',out/'DEVICE-TEST.md')",
             "shutil.copy2(ROOT/'repairs/cosmic-chooser-2103296/DEVICE-TEST.txt',out/'DEVICE-TEST.txt')")
    t=once(t,"        native,_=dex_contract(b)",
             "        for name in an:\n            if name.startswith('lib/') and not name.endswith('/'):\n                require(a.read(name)==b.read(name),'Native library changed: '+name)\n        native,_=dex_contract(b)")
    t=once(t,"    print('PASS: Kodi video Surface repair over exact 2103282; native engine/assets/resources preserved; permanent signer verified')",
             "    print('PASS: chooser-only 2103296 over exact signed 2103295; all native libraries/assets/resources preserved; permanent signer verified')")
    pkg.write_text(t)
    for name in ('sign-infinity71.sh','validate_candidate2_compiled_manifest.py'):
        origin=HERE.parents[1]/'scripts'/name
        if origin.exists():shutil.copy2(origin,root/'scripts'/name)
    device=root/'repairs/cosmic-chooser-2103296/DEVICE-TEST.txt';device.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(HERE/'DEVICE-TEST.txt',device)
    out.mkdir(parents=True,exist_ok=True)
    rows=[{'path':p,'before':before.get(p),'after':after.get(p),'status':'added' if p in added else 'changed' if p in changed else 'protected unchanged'} for p in sorted(set(before)|set(after))]
    (out/'CHOOSER-BYTE-MANIFEST.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'CHOOSER-SOURCE-AUDIT.json').write_text(json.dumps({'version_code':VC,'version_name':REL,'base_apk_sha256':PARENT,
        'native_sha256':NATIVE,'changed_source_files':changed,'added_source_files':added,'unexpected_source_changes':0,
        'native_rebuilt':False,'skin_modified':False,'main_splash_cobra_player_provider_sources_modified':False,
        'live_time_date':True,'weather_before_cold_kodi':'real last-known reading or unavailable; not fresh without running Kodi',
        'physical_verified':False,'locked':False},indent=2)+'\n')
    print('PASS: exact chooser-only source delta; Main/Splash/Cobra/player/skin unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    apply(a.root.resolve(),a.base.resolve(),a.out.resolve())
