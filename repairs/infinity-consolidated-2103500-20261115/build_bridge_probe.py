#!/usr/bin/env python3
"""Package an actual-engine bridge fixture; distinct identity/key, never an installer."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FROZEN='9ce852ebb044a82853ef93af24e34a07ed96daff'
OLD='repairs/infinity-essential-only-shutdown-2103483-20261112/native/overlay/'
BASE_APK='224d5f808587ce4004a96a003331abe7c71cbe7bd08ec6b1d3ec288c6c75cf40'
BASE_ENGINE='3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75'
LEDGER='12e26e9ee008ec65b3def04e7dc0919ff66a0d1a2d1f22cc220d83c393f7c67e'
PROTECTED='bcd235ab97e38cd09c768a47488a14106208ff9ba1ac5da550864f2aaaa757ac'
CASES={'closed_binary':'ClosedBinary','closed_text':'ClosedText','closed_layered':'ClosedLayered',
       'flush_error':'FlushError','dirty_buffer':'DirtyBuffer','sqlite_pending':'SqlitePending',
       'durability_denied':'DurabilityDenied','late_write':'LateWrite'}


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def run(command):
    subprocess.run([str(s) for s in command],check=True)


def build(apk,native,work):
    assert sha(apk)==BASE_APK
    selected=json.loads((HERE/'CI-BRIDGE.json').read_text())
    variant=selected['variant']
    assert variant in ('baseline','candidate')
    if variant=='candidate':
        proof=json.loads((native/'ARM64.json').read_text())
        assert proof['status']=='PASS_FULL_ARM64_LINK_AND_EXACT500_ABI'
        assert proof['baseline_native_sha256']==BASE_ENGINE
        assert sha(native/'libkodi.so')==proof['native_sha256']
        preservation=json.loads((native/'SOURCE-PRESERVATION.json').read_text())
        observer='xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
        assert set(preservation['changed'])=={observer}
        assert preservation['source']==proof['source']==selected['native_source']
        row=next(r for r in json.loads((HERE/'SCOPE.json').read_text())['production_allowlist'] if r.get('native_path')==observer)
        assert preservation['changed'][observer]==dict(before=row['baseline_sha256'],after=sha(HERE/'native/overlay'/observer))
        assert preservation['unchanged_native_files']==9412
    else:
        # Execute the single causal control while the full corrected engine
        # compiles. Never mislabel this unchanged engine as a corrected build.
        baseline=json.loads((HERE/'BASELINE.json').read_text())
        assert selected['native_source']==baseline['native_producer']['source']
        proof=dict(source=selected['native_source'],native_sha256=BASE_ENGINE)
    work.mkdir(parents=True,exist_ok=True)
    if variant=='baseline':
        native=work/'baseline-engine';native.mkdir(exist_ok=True)
        with ZipFile(apk) as original:
            with original.open('lib/arm64-v8a/libkodi.so') as src,(native/'libkodi.so').open('wb') as dst:
                import shutil
                shutil.copyfileobj(src,dst,1024*1024)
        assert sha(native/'libkodi.so')==BASE_ENGINE
    # Only exact ABI data structures are copied. No ledger functions, state,
    # observer source, mock callbacks or persistence macros are compiled here.
    raw=subprocess.check_output(['git','show',FROZEN+':'+OLD+'xbmc/platform/android/activity/InfinityScriptPersistence.h'],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()==LEDGER
    text=raw.decode()
    spans=[text[text.index('struct '+name+'\n'):text.index(end,text.index('struct '+name+'\n'))]
           for name,end in [('InitializationStep','struct Writer'),('Blocker','struct Namespace'),('Evidence','inline Evidence Snapshot()')]]
    protection=subprocess.check_output(['git','show',FROZEN+':'+OLD+'xbmc/platform/android/activity/InfinityProtectedWrites.h'],cwd=ROOT)
    assert hashlib.sha256(protection).hexdigest()==PROTECTED
    ptext=protection.decode()
    spans.append(ptext[ptext.index('struct EssentialWriteProof\n'):ptext.index('inline std::string ResourceOwnerLocked')])
    (work/'bridge_types.h').write_text('#include <cstdint>\n#include <string>\n#include <vector>\nnamespace InfinityScriptPersistence {\n'+''.join(spans)+'}\n')
    sdk=Path(os.environ['ANDROID_HOME']);tools=sdk/'build-tools/35.0.0'
    ndk=sdk/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin'
    symbols=subprocess.check_output([ndk/'llvm-nm','--dynamic','--defined-only',native/'libkodi.so'],text=True).splitlines()
    names=[line.split()[-1] for line in symbols]
    demangled=subprocess.check_output([ndk/'llvm-cxxfilt'],input='\n'.join(names)+'\n',text=True).splitlines()
    stems={
        'VFS':'PythonBindings::PyInit_Module_xbmcvfs()',
        'SNAPSHOT':'InfinityScriptPersistence::Snapshot()',
        'ADMIT':'InfinityScriptPersistence::Admit(',
        'START':'InfinityPythonPersistence::Start(',
        'FINISH':'InfinityPythonPersistence::Finish(',
        'END':'InfinityPythonPersistence::End(',
        'BEGIN':'InfinityScriptPersistence::BeginWriteProtection(',
        'CLOSE':'InfinityScriptPersistence::CloseParticipantWrites(',
        'SEAL':'InfinityScriptPersistence::SealEssentialWrites(',
        'AUTHORIZED':'InfinityScriptPersistence::EssentialWritesAuthorized(',
        'ACTIVE':'InfinityScriptPersistence::ActiveProtectedResources()',
        'PROOF':'InfinityScriptPersistence::EssentialWrites()',
    }
    bindings={}
    for key,stem in stems.items():
        found=[name for name,desc in zip(names,demangled) if desc.startswith(stem) and ')::' not in desc]
        assert len(found)==1,(key,found)
        bindings[key]=found[0]
    (work/'bridge_symbols.h').write_text(''.join('#define SYM_'+k+' '+json.dumps(v)+'\n' for k,v in bindings.items()))
    library=work/'libinfinityobserverqa.so'
    run([ndk/'aarch64-linux-android21-clang++','-std=c++17','-shared','-fPIC','-O1',
         '-I'+str(work),HERE/'android/observer_bridge.cpp','-ldl','-llog',
         '-Wl,-z,max-page-size=16384','-o',library])
    dynamic=subprocess.check_output([ndk/'llvm-readelf','-d',library],text=True)
    assert 'libc++_shared.so' in dynamic,'Fixture must share the exact engine libc++ ABI'
    classes=work/'classes';classes.mkdir(exist_ok=True)
    run(['javac','-source','8','-target','8','-bootclasspath',os.pathsep.join(str(p) for p in (sdk/'platforms/android-34/android.jar',tools/'core-lambda-stubs.jar')),
         '-d',classes,HERE/'android/ProbeActivity.java'])
    with ZipFile(work/'fixture.jar','w',ZIP_DEFLATED) as z:
        for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes).as_posix())
    dex=work/'dex';dex.mkdir(exist_ok=True)
    run(['java','-cp',tools/'lib/d8.jar','com.android.tools.r8.D8','--min-api','30','--lib',sdk/'platforms/android-34/android.jar',
         '--output',dex,work/'fixture.jar'])
    spec=importlib.util.spec_from_file_location('bridge_case_inputs',HERE/'android/bridge_cases.py')
    cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)
    receipts={}
    key=work/'fixture-only.jks'
    run(['keytool','-genkeypair','-keystore',key,'-storepass','fixture-only','-keypass','fixture-only','-alias','fixture',
         '-dname','CN=Disposable Embedded Bridge Fixture','-keyalg','RSA','-keysize','2048','-validity','2','-noprompt'])
    with ZipFile(apk) as baseline:
        assert hashlib.sha256(baseline.read('lib/arm64-v8a/libkodi.so')).hexdigest()==BASE_ENGINE
        for variant in (variant,):
            manifest=work/(variant+'.xml')
            activity=''.join('<activity android:name="com.projectinfinity.observerqa.ProbeActivity$'+name+'" android:exported="true" android:process=":'+case+'"/>' for case,name in CASES.items())
            manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.observerqa.'+variant+'" android:versionCode="1" android:versionName="CI-only"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="35"/><application android:extractNativeLibs="true" android:label="Embedded bridge CI" android:theme="@android:style/Theme.Material.NoActionBar">'+activity+'</application></manifest>')
            shell=work/(variant+'-shell.apk')
            run([tools/'aapt2','link','--manifest',manifest,'-I',sdk/'platforms/android-34/android.jar','-o',shell])
            unsigned=work/(variant+'-unsigned.apk')
            with ZipFile(unsigned,'w',ZIP_DEFLATED) as out,ZipFile(shell) as stub:
                for n in stub.namelist():out.writestr(n,stub.read(n))
                out.write(dex/'classes.dex','classes.dex')
                for n in ('libc++_shared.so','libshairplay.so'):
                    path='lib/arm64-v8a/'+n;out.writestr(path,baseline.read(path))
                if variant=='baseline':out.writestr('lib/arm64-v8a/libkodi.so',baseline.read('lib/arm64-v8a/libkodi.so'))
                else:out.write(native/'libkodi.so','lib/arm64-v8a/libkodi.so')
                out.write(library,'lib/arm64-v8a/libinfinityobserverqa.so')
                for n in baseline.namelist():
                    prefix='assets/python3.11/lib/python3.11/'
                    if n.startswith(prefix) and not n.endswith('/'):
                        out.writestr('assets/python3.11/'+n[len(prefix):],baseline.read(n))
                for name,code in cases.CASES.items():out.writestr('assets/cases/'+name+'.py',code)
            aligned=work/(variant+'-aligned.apk');signed=work/(variant+'-CI-ONLY.apk')
            run([tools/'zipalign','-f','4',unsigned,aligned])
            run([tools/'apksigner','sign','--ks',key,'--ks-pass','pass:fixture-only','--out',signed,aligned])
            receipts[variant]={'APK_sha256':sha(signed),'engine_sha256':BASE_ENGINE if variant=='baseline' else proof['native_sha256']}
            unsigned.unlink();aligned.unlink()
    result={'status':'FIXTURES_BUILT_NOT_EXECUTED','baseline_APK':BASE_APK,'native_source':proof['source'],'variant':variant,
            'symbols':bindings,'types_source_sha256':LEDGER,'packages':receipts,'cases':CASES,
            'production_installer':False,'original_signer_used':False,'full_application_acceptance':False}
    (work/'BUILD.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('native',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();build(a.apk.resolve(),a.native.resolve(),a.out.resolve())
