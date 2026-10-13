"""Sign a clearly labeled native diagnostic with the exact locked Java/assets.

The lifecycle candidate is preserved separately and is not claimed deployed by
this diagnostic. Only libkodi.so and the manifest's version fields may differ.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
PARENT_SHA='8e8e139929592daedb63e0e41040258d655f132fd025b236de7dee1e88b47649'
SIGNER='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
ENGINE='lib/arm64-v8a/libkodi.so'
NAME='1.0.9-Wide-VFS-Diagnostic-RC1'
SIGNATURE=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:RSA|DSA|EC|SF))')

def sha(data):return hashlib.sha256(data).hexdigest()
def command(*argv):return subprocess.check_output([str(x) for x in argv],text=True,stderr=subprocess.STDOUT)
def exports(text):
    return {p[-1].split('@',1)[0] for line in text.splitlines()
            if len(p:=line.split())>=8 and p[4:6]==['GLOBAL','DEFAULT'] and p[6]!='UND'}

def package(a):
    assert sha(a.parent.read_bytes())==PARENT_SHA,'Not locked 2103376 APK'
    for n in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        assert os.environ.get(n),'Existing permanent signing setting unavailable: '+n
    proof=json.loads((a.evidence/'ENGINE-PROOF.json').read_text())
    assert proof['complete_native_engine_compiled'] and proof['vfs_trace_compiled'] and proof['observation_only']
    assert not proof['shutdown_corrected'] and not proof['final_2103377_repair']
    tests=json.loads((a.evidence/'vfs-trace-tests/VFS-TRACE-TESTS.json').read_text());assert tests['passed'] and all(tests['capabilities'].values())
    assert json.loads((a.evidence/'vfs-source-tests/VFS-SOURCE-CAPABILITIES.json').read_text())['passed']
    preserved=json.loads((a.evidence/'SAVED-274-CANDIDATE-PRESERVATION.json').read_text());assert preserved['exact_hashes_preserved']
    a.out.mkdir(parents=True,exist_ok=True)
    assert sha(a.engine.read_bytes())==proof['native_sha256']
    engine=a.out/'libkodi.so';shutil.copyfile(a.engine,engine)
    ndk=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ['NDK_VER']/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    subprocess.run([str(ndk),'--strip-unneeded',str(engine)],check=True)
    for token in [b'operation_start_monotonic_ns',b'vfs.shutdown.request',b'infinityPrepareNativeTask']:
        assert token in engine.read_bytes(),token
    oldengine=a.out/'parent-libkodi.so'
    spec=importlib.util.spec_from_file_location('version_fields',ROOT/'repairs/critical-preview-2103376/manifest_patch.py')
    patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    patch.PARENT_CODE=2103376;patch.CODE=2103377
    patch.PARENT_NAME='1.0.9-File-Preview-Repair-RC1';patch.NAME=NAME
    unsigned=a.out/'vfs-diagnostic-unsigned.apk'
    with zipfile.ZipFile(a.parent) as parent,zipfile.ZipFile(unsigned,'w') as target:
        assert parent.testzip() is None and len(parent.namelist())==len(set(parent.namelist()))
        manifest,edits=patch.patch(parent.read('AndroidManifest.xml'))
        oldengine.write_bytes(parent.read(ENGINE))
        for info in parent.infolist():
            if SIGNATURE.fullmatch(info.filename):continue
            data=manifest if info.filename=='AndroidManifest.xml' else engine.read_bytes() if info.filename==ENGINE else parent.read(info.filename)
            target.writestr(info,data)
    before_symbols=command('readelf','--dyn-syms','--wide',oldengine)
    after_symbols=command('readelf','--dyn-syms','--wide',engine)
    assert not exports(before_symbols)-exports(after_symbols),'Existing native export lost'
    needed=lambda s:sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]',s))
    assert needed(command('readelf','-d','-W',oldengine))==needed(command('readelf','-d','-W',engine))
    final=a.out/'Infinity-2103377-Shutdown-Wide-Diagnostic-RC1.apk'
    subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(final)],check=True)
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    for label,file in [('parent',a.parent),('diagnostic',final)]:
        text=command(bt/'apksigner','verify','--verbose','--print-certs',file)
        (a.out/(label+'-signature.txt')).write_text(text)
        assert SIGNER in text.lower()
        assert all(re.search(r'Verified using v'+str(n)+r' scheme[^\n]+true',text) for n in (2,3))
    badging=command(bt/'aapt','dump','badging',final)
    assert f"package: name='com.projectinfinity.kodi' versionCode='2103377' versionName='{NAME}'" in badging
    assert 'application-debuggable' not in badging
    (a.out/'diagnostic-badging.txt').write_text(badging)
    (a.out/'alignment.txt').write_text(command(bt/'zipalign','-c','-p','4',final))
    protected={}
    with zipfile.ZipFile(a.parent) as parent,zipfile.ZipFile(final) as candidate:
        names=lambda z:{n for n in z.namelist() if not SIGNATURE.fullmatch(n)}
        assert names(parent)==names(candidate)
        assert candidate.testzip() is None and len(candidate.namelist())==len(set(candidate.namelist()))
        for n in names(parent)-{ENGINE,'AndroidManifest.xml'}:
            assert parent.read(n)==candidate.read(n),'Protected entry changed: '+n
            protected[n]=sha(candidate.read(n))
        assert candidate.read('AndroidManifest.xml')==manifest and candidate.read(ENGINE)==engine.read_bytes()
        assert all(parent.read(n)==candidate.read(n) for n in names(parent) if re.fullmatch(r'classes\d*\.dex',n))
    receipt={'source_commit':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'file':final.name,'sha256':sha(final.read_bytes()),'bytes':final.stat().st_size,
        'version_code':2103377,'version_name':NAME,'package':'com.projectinfinity.kodi',
        'permanent_signer_sha256':SIGNER,'parent_apk_sha256':PARENT_SHA,
        'unstripped_engine_sha256':proof['native_sha256'],'packaged_engine_sha256':sha(engine.read_bytes()),
        'protected_payload_entries':protected,'all_locked_dex_byte_identical':True,
        'all_resources_assets_and_other_native_libraries_byte_identical':True,
        'native_exports_preserved':True,'native_dependencies_preserved':True,'manifest_edits':edits,
        'observation_only':True,'shutdown_corrected':False,'final_2103377_repair':False,
        'saved_274_lifecycle_candidate_preserved_but_not_deployed_in_diagnostic':True,
        'physical_device_verified':False,'locked':False,'promoted':False}
    (a.out/'DIAGNOSTIC-DELIVERY.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    (a.out/'SCOPE.txt').write_text('EVIDENCE COLLECTION APK ONLY. ACTUAL SHUTDOWN CORRECTION UNRESOLVED. LOCKED 2103376 JAVA/DATA/FEATURE PAYLOAD RETAINED. SAVED 274-TEST LIFECYCLE CANDIDATE IS PRESERVED FOR THE FINAL REPAIR, NOT CLAIMED DEPLOYED HERE. NO DEVICE ACCEPTANCE, PROMOTION OR LOCK.\n')
    unsigned.unlink();oldengine.unlink();engine.unlink()
    print(json.dumps({k:receipt[k] for k in ('file','sha256','version_name','shutdown_corrected')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','engine','evidence','out'):p.add_argument('--'+n,type=Path,required=True)
    package(p.parse_args())
