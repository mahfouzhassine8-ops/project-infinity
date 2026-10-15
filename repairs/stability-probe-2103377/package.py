"""Permanently sign an observational derivative of exact locked Rails RC02."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2]
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
PARENT='17e2458552b7dbb8f14dad307015eafc2497a5ec6ddc4f7bb1707d975f37b906'
NATIVE='7303a74822681464c23215bc6ddf10d3a4446770'
ENGINE='lib/arm64-v8a/libkodi.so'
SIGNATURE=re.compile(r'^META-INF/(?:MANIFEST.MF|[^/]+\.(?:SF|RSA|DSA|EC))$',re.I)
sha=lambda b:hashlib.sha256(b).hexdigest()
def run(*args):return subprocess.check_output([str(a) for a in args],text=True,stderr=subprocess.STDOUT)
def package(args):
    native=args.native/'checkpoint-build';proof=json.loads((native/'ENGINE-PROOF.json').read_text())
    delta=json.loads((native/'STABILITY-PROBE-DELTA.json').read_text())
    assert proof['stability_probe_source_commit']==NATIVE and delta['source_commit']==NATIVE
    assert proof['complete_native_engine_compiled'] and proof['observations_only'] and not proof['root_cause_fixed']
    assert delta['exact_delta_verified'] and not delta['required_save_gates_changed']
    assert json.loads((native/'stability-probe-host/PROBE-HOST-RESULT.json').read_text())['passed']
    assert sha((native/'libkodi.so').read_bytes())==proof['native_sha256']
    assert sha(args.parent.read_bytes())==PARENT
    smokes=list(args.smoke.rglob('rail-smoke-result.json'));assert len(smokes)==1
    smoke=json.loads(smokes[0].read_text());assert smoke['passed'] and smoke['open_action_runs_real_plugin'] and smoke['back_dismisses_and_clears_guard']
    args.out.mkdir(parents=True,exist_ok=True)
    ndk=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ['NDK_VER']/'toolchains/llvm/prebuilt/linux-x86_64/bin'
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    engine=args.out/'candidate-libkodi.so';shutil.copyfile(native/'libkodi.so',engine)
    run(ndk/'llvm-strip','--strip-unneeded',engine)
    module=ROOT/'repairs/critical-preview-2103376/manifest_patch.py'
    spec=importlib.util.spec_from_file_location('stability_manifest',module);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.PARENT_CODE=mod.CODE=2103377;mod.PARENT_NAME='1.0.9-Rails-Hold-Correction-RC02';mod.NAME='1.0.9-Stability-Evidence-RC01'
    unsigned=args.out/'stability-unsigned.apk';parent_engine=args.out/'parent-libkodi.so'
    with zipfile.ZipFile(args.parent) as src,zipfile.ZipFile(unsigned,'w') as dst:
        assert len(src.namelist())==len(set(src.namelist()));parent_engine.write_bytes(src.read(ENGINE))
        for info in src.infolist():
            if SIGNATURE.match(info.filename):continue
            data=src.read(info.filename)
            if info.filename==ENGINE:data=engine.read_bytes()
            elif info.filename=='AndroidManifest.xml':data,_=mod.patch(data)
            dst.writestr(info,data)
    def exports(file):return {p[-1].split('@')[0] for line in run('readelf','--dyn-syms','--wide',file).splitlines() if len(p:=line.split())>=8 and p[4:6]==['GLOBAL','DEFAULT'] and p[6]!='UND'}
    assert not exports(parent_engine)-exports(engine)
    needed=lambda p:sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]',run('readelf','-d','-W',p)))
    assert needed(parent_engine)==needed(engine)
    final=args.out/'Infinity-2103377-Stability-Evidence-RC1-TEST.apk'
    subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(final)],check=True)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final);assert CERT in cert.lower()
    for version in [2,3]:assert re.search(r'Verified using v'+str(version)+r' scheme[^\n]+true',cert)
    run(bt/'zipalign','-c','-p','4',final)
    assert "versionCode='2103377'" in run(bt/'aapt','dump','badging',final)
    with zipfile.ZipFile(args.parent) as old,zipfile.ZipFile(final) as new:
        assert set(old.namelist())==set(new.namelist())
        changed=sorted(n for n in old.namelist() if not SIGNATURE.match(n) and old.read(n)!=new.read(n))
        assert changed==['AndroidManifest.xml',ENGINE]
    helper=Path(__file__).resolve().parent/'helper';manifest=json.loads((helper.parent/'HELPER-025-HASHES.json').read_text())
    expected=set(manifest['files'])|{'resources/lib/stability_probe.py'}
    files={str(p.relative_to(helper)):p for p in helper.rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    assert set(files)==expected
    for n,p in files.items():
        if n not in ['addon.xml','resources/lib/runtime.py','resources/lib/stability_probe.py']:assert sha(p.read_bytes())==manifest['files'][n]
    helper_zip=args.out/'script.infinity.rails-0.2.6-Stability-Evidence-RC1-TEST.zip'
    with zipfile.ZipFile(helper_zip,'w',zipfile.ZIP_DEFLATED) as z:
        for n,p in sorted(files.items()):z.write(p,'script.infinity.rails/'+n)
    result=dict(source_commit=os.environ['GITHUB_SHA'],native_source_commit=NATIVE,apk_filename=final.name,apk_sha256=sha(final.read_bytes()),parent_sha256=PARENT,
        helper_filename=helper_zip.name,helper_sha256=sha(helper_zip.read_bytes()),signer_sha256=CERT,changed_payload=changed,
        dex_resources_assets_other_libraries_identical=True,skin_223_changed=False,save_gate_waivers=False,version_code=2103377,version_name=mod.NAME,
        observational_candidate=True,root_cause_fixed=False,physical_fold_accepted=False,locked=False,real_kodi_smoke=smoke,
        native_full_build=True,preserved_android_tests=274,fresh_android_tests=0,physical_capture_required=True)
    (args.out/'STABILITY-APK-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.out/'signing-verification.txt').write_text(cert)
    (args.out/'SHA256SUMS').write_text(result['apk_sha256']+'  '+final.name+'\n'+result['helper_sha256']+'  '+helper_zip.name+'\n')
    shutil.copyfile(Path(__file__).with_name('INSTALL-AND-CAPTURE.txt'),args.out/'INSTALL-AND-CAPTURE.txt')
    for p in [unsigned,engine,parent_engine]:p.unlink()
if __name__=='__main__':
    cli=argparse.ArgumentParser()
    for n in ['native','parent','smoke','out']:cli.add_argument('--'+n,type=Path,required=True)
    package(cli.parse_args())
