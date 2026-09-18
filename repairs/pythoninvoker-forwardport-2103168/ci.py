#!/usr/bin/env python3
"""Forward-port proven PythonInvoker native repair onto exact successful 2103167 shell."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

BASE167_SHA="e44b1c884292fbbf75ab8ce3bf58ea273e783ff3f818cceeb8d1956e888b541a"
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
OLD="1.0.9-Cobra-Status-Bar-Restore-RC1"
NEW="1.0.9-Cobra-Status-Bar-PythonInvoker-Stability-RC1"
VERSION=2103168
LIB="lib/arm64-v8a/libkodi.so"
UPSTREAM="0186f895271d4ce7d240b4e9f40da03b4833539d"

def sha_bytes(v):return hashlib.sha256(v).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(v,msg):
    if not v:raise RuntimeError(msg)
def replace(path,old,new,count=1):
    p=Path(path);s=p.read_text();require(s.count(old)==count,f"anchor drift {path}: {old} count={s.count(old)}")
    p.write_text(s.replace(old,new,count))

def controlled_base(base167:Path,native_apk:Path,out:Path):
    require(sha(base167)==BASE167_SHA,"Wrong 2103167 signed baseline")
    with zipfile.ZipFile(base167) as old,zipfile.ZipFile(native_apk) as native:
        patched=native.read(LIB);before=old.read(LIB)
        require(patched!=before,"Native repair did not change libkodi.so vs 2103167")
        require(b"thread state cleaned while waiting for child threads" in patched,"Native crash guard missing")
        require(b"m_threadState != nullptr" not in patched,"Old PythonInvoker abort assertion remains")
        with zipfile.ZipFile(out,"w") as z:
            for info in old.infolist():
                z.writestr(info,patched if info.filename==LIB else old.read(info.filename))
    with zipfile.ZipFile(out) as new,zipfile.ZipFile(base167) as old:
        require(set(new.namelist())==set(old.namelist()),"Controlled-base inventory drift")
        changed=[n for n in old.namelist() if old.read(n)!=new.read(n)]
        require(changed==[LIB],"Controlled base changed more than libkodi.so: "+repr(changed))
    return sha_bytes(patched),sha_bytes(before)

def patch_packager_for_protected_base(pack:Path):
    s=pack.read_text()
    start=s.index("def verify_manifest_pair(original: str, compiled: str):")
    end=s.index("\n\ndef merge(",start)
    verifier='''def verify_manifest_pair(original: str, compiled: str):
    old,new=manifest_tree(original),manifest_tree(compiled)
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'): tree['attrs'].pop(key,None)
    def validate(tree):
        names=[n['attrs'].get('android:name','') for n in tree['children'] if n['tag']=='uses-permission']
        for permission in (
            'android.permission.FOREGROUND_SERVICE_SPECIAL_USE',
            'android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK',
            'android.permission.WAKE_LOCK'):
            require(sum(permission in name for name in names)==1,'Expected one manifest permission: '+permission)
        app=next(n for n in tree['children'] if n['tag']=='application')
        services=[n for n in app['children'] if n['tag']=='service' and
                  'InfinityExtendedBackgroundService' in n['attrs'].get('android:name','')]
        require(len(services)==1,'Exactly one background service component required')
        svc=services[0]
        require(svc['attrs'].get('android:exported','').endswith('0x0'),'Background service must not be exported')
        require(svc['attrs'].get('android:foregroundServiceType','').endswith('0x40000002'),
                'Expected specialUse|mediaPlayback foreground service type')
        controls=[n for n in app['children'] if n['tag']=='activity' and
                  'InfinityBackgroundControlActivity' in n['attrs'].get('android:name','')]
        require(len(controls)==1,'Exactly one Infinity background control Activity required')
    validate(old);validate(new)
    require(old==new,'Compiled manifest drift from protected 2103167 base outside version identity')
'''
    pack.write_text(s[:start]+verifier+s[end:])

def promote(shell:Path,base167:Path,native_apk:Path,outdir:Path):
    outdir.mkdir(parents=True,exist_ok=True)
    controlled=outdir/"Infinity-2103167-PythonInvoker-Patched-Base.apk"
    new_engine,old_engine=controlled_base(base167,native_apk,controlled)

    gradle=shell/"tools/android/packaging/xbmc/build.gradle.in"
    replace(gradle,"versionCode 2103167",f"versionCode {VERSION}")
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')

    runtime=Path("scripts/infinity_background_resume.py");s=runtime.read_text()
    require(s.count("VERSION_CODE = 2103167")==1 and s.count("RELEASE = '"+OLD+"'")==1,"2103167 runtime identity drift")
    base=re.search(r"BASE_APK_SHA256 = '([0-9a-f]{64})'",s);eng=re.search(r"BASE_ENGINE_SHA256 = '([0-9a-f]{64})'",s)
    require(base and eng,"Runtime base hashes missing")
    s=s.replace("VERSION_CODE = 2103167",f"VERSION_CODE = {VERSION}",1)
    s=s.replace("RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'",1)
    s=s.replace(base.group(0),"BASE_APK_SHA256 = '"+sha(controlled)+"'",1)
    s=s.replace(eng.group(0),"BASE_ENGINE_SHA256 = '"+new_engine+"'",1)
    runtime.write_text(s)

    pack=Path("scripts/package_background_resume.py");ptext=pack.read_text();needle="Infinity-"+OLD
    require(ptext.count(needle)>=2,"2103167 packager identity drift")
    pack.write_text(ptext.replace(needle,"Infinity-"+NEW))
    patch_packager_for_protected_base(pack)

    receipt=Path("engine/background-resume-source.json");data=json.loads(receipt.read_text())
    require(data.get("version_code")==2103167,"Expected exact 2103167 source receipt")
    rel="tools/android/packaging/xbmc/build.gradle.in";require(rel in data["files"],"Gradle absent from receipt")
    data["files"][rel]["after"]=sha(gradle)
    data.update(
        version_code=VERSION,version_name=NEW,source_parent=2103167,source_parent_locked=True,
        source_parent_commit="2d72c733998d3c535a16d354058344007c5f7921",
        candidate_locked=False,candidate14_preserved=True,
        status_bar_2103167_preserved=True,ui_lifecycle_2103166_preserved=True,
        inset_pip_2103165_preserved=True,playback_stability_2103164_preserved=True,
        pythoninvoker_threadstate_repair=True,pythoninvoker_upstream_fix=UPSTREAM,
        pythoninvoker_device_abort_guard=True,native_engine_unchanged=False,
        native_engine_rebuilt=True,previous_native_engine_sha256=old_engine,
        native_engine_sha256=new_engine,physical_device_verified=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

    (outdir/"promotion.json").write_text(json.dumps({
        "build":VERSION,"base167_apk_sha256":BASE167_SHA,"controlled_base_sha256":sha(controlled),
        "previous_native_engine_sha256":old_engine,"native_engine_sha256":new_engine,
        "only_baseline_entry_changed_before_shell_compile":LIB,"upstream_fix":UPSTREAM,
        "candidate14_modified":False
    },indent=2)+"\n")
    print("PASS: exact 2103167 shell promoted to installable 2103168 native repair")

def verify(final:Path,base167:Path,native_apk:Path,audit:Path):
    require(final.is_file() and base167.is_file(),"Final/baseline APK missing")
    a=json.loads(audit.read_text())
    require(a["version_code"]==VERSION and a["version_name"]==NEW,"Final identity mismatch")
    require(a["signer_certificate_sha256"]==CERT,"Release signer changed")
    require(a["apk_sha256"]==sha(final),"Final hash receipt mismatch")

    with zipfile.ZipFile(final) as new,zipfile.ZipFile(base167) as old,zipfile.ZipFile(native_apk) as native:
        require(new.read(LIB)==native.read(LIB),"Final libkodi.so differs from proven repaired engine")
        require(b"thread state cleaned while waiting for child threads" in new.read(LIB),"Crash guard absent from final APK")
        require(b"m_threadState != nullptr" not in new.read(LIB),"Old abort assertion remains in final APK")
        natives={n for n in old.namelist() if n.startswith("lib/") and not n.endswith("/")}
        require(natives=={n for n in new.namelist() if n.startswith("lib/") and not n.endswith("/")},"Native inventory changed")
        for n in natives-{LIB}:require(new.read(n)==old.read(n),"Non-target native changed: "+n)
        protected={n for n in old.namelist() if n.startswith(("assets/","res/")) or n=="resources.arsc"}
        for n in protected:require(new.read(n)==old.read(n),"Protected assets/resources changed: "+n)
        dex=b"".join(new.read(n) for n in new.namelist() if re.fullmatch(r"classes\d*\.dex",n))
        for token in (
            b"cobraConfirmBrowseSystemBars",b"cobraApplySystemBarsForSurface",b"cobraInstallBrowseSafeArea",
            b"CobraPlaybackPolicy",b"PLAY IN BACKGROUND",b"MiXplorer",b"Previous channel",b"Lock controls"):
            require(token in dex,"Latest shell contract lost: "+repr(token))

    manifest=Path("signed168/manifest.txt").read_text()
    require("com.projectinfinity.kodi.InfinityLiveActivity" in manifest,"InfinityLiveActivity missing")
    badging=Path("signed168/badging.txt").read_text()
    require("versionCode='2103168'" in badging and "package: name='com.projectinfinity.kodi'" in badging,"Badging identity mismatch")

    result={
        "version_code":VERSION,"version_name":NEW,"apk_sha256":sha(final),"signer":CERT,
        "base_2103167_sha256":BASE167_SHA,"pythoninvoker_upstream_fix":UPSTREAM,
        "pythoninvoker_abort_assertion_removed":True,"pythoninvoker_guard_present":True,
        "status_bar_2103167_preserved":True,"candidate14_untouched":True,
        "physical_device_verified":False
    }
    Path("audit168/final-verification.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PASS: 2103168 APK is a forward update over 2103167 with native crash repair")

def suite(path,count):
    p=Path(path);require(p.is_file(),"Missing test suite "+str(p))
    root=ET.parse(p).getroot();cases=root.findall("testcase")
    require(len(cases)==count and all(int(root.get(k,"0"))==0 for k in ("failures","errors","skipped")),"Suite failed/incomplete "+str(p))
    return count

def deliver():
    inherited=0
    for name,count,folder in [
        ("CobraNavigationUiTest",4,"cobra-regression"),("CobraHealthUiTest",7,"cobra-regression"),
        ("Cobra2103159UiTest",2,"experience"),("ExperienceChooserUiTest",6,"experience")]:
        inherited+=suite(Path("audit159/android")/folder/"test-results"/("TEST-com.projectinfinity.kodi."+name+".xml"),count)
    inherited+=suite("audit168/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml",17)
    inherited+=suite("audit168/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml",10)
    c14=suite("audit168/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml",16)
    p164=suite("audit168/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103164PlaybackStabilityTest.xml",26)
    p165=suite("audit168/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103165InsetsPipPlayerTest.xml",6)
    p166=suite("audit168/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103166EndToEndUiAuditTest.xml",8)
    p167=suite("audit168/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103167StatusBarRestoreTest.xml",5)
    native=json.loads(Path("engine/pythoninvoker-threadstate-source.json").read_text())
    require(native.get("upstream_fix")==UPSTREAM and all(native["checks"].values()),"Native source proof failed")
    total=inherited+c14+p164+p165+p166+p167
    require(total==107,"Expected 107 inherited/latest Android tests, got "+str(total))
    result={
        "build":VERSION,"base":2103167,"candidate14_untouched":True,"total_android_tests":total,
        "pythoninvoker_source_checks":len(native["checks"]),"native_engine_rebuilt":True,
        "upstream_fix":UPSTREAM,"candidate_locked":False,"physical_device_verified":False,
        "status":"TEST CANDIDATE - install and crash-reproduction acceptance required"
    }
    Path("signed168/ACCEPTANCE.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2("engine/pythoninvoker-threadstate-source.json","signed168/PYTHONINVOKER-NATIVE-REPAIR.json")
    shutil.copy2("audit168/final-verification.json","signed168/2103168-verification.json")
    print("PASS:",total,"latest Android tests + native repair gates")

if __name__=="__main__":
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("promote");a.add_argument("--shell",type=Path,required=True);a.add_argument("--base167",type=Path,required=True);a.add_argument("--native-apk",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
    a=sub.add_parser("verify");a.add_argument("--final",type=Path,required=True);a.add_argument("--base167",type=Path,required=True);a.add_argument("--native-apk",type=Path,required=True);a.add_argument("--audit",type=Path,required=True)
    sub.add_parser("deliver")
    args=p.parse_args()
    if args.cmd=="promote":promote(args.shell,args.base167,args.native_apk,args.out)
    elif args.cmd=="verify":verify(args.final,args.base167,args.native_apk,args.audit)
    else:deliver()
