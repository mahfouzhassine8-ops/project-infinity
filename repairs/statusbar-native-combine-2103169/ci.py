#!/usr/bin/env python3
"""Combine the proven status-bar surface repair with locked 2103168 native crash fix."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

LOCKED_NATIVE_SHA="8ba2793633633706eeafcc1bde800d5f82365927fc5df769030698a2f9753a6e"
LOCKED_NATIVE_COMMIT="3c2005cb62ae2115170a0aae1a8b22813ee7eeb9"
SURFACE_COMMIT="3b97cd74e2f0e42b091a21fcab4019dfa319eb48"
SURFACE_ACTIVITY_SHA="8797019d960d0861937d3a93ef4e93b94c3e9034179b429b7cd55d8cfb586831"
CANDIDATE14="1465eabb045badad56142642c48292df94caaa12"
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
OLD_SURFACE="1.0.9-Cobra-Status-Bar-Surface-Match-RC1"
OLD_NATIVE="1.0.9-Cobra-Status-Bar-PythonInvoker-Stability-RC1"
NEW="1.0.9-Cobra-Status-Bar-Native-Stability-RC1"
VERSION=2103169
LIB="lib/arm64-v8a/libkodi.so"
REL="tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in"
UPSTREAM="0186f895271d4ce7d240b4e9f40da03b4833539d"

def sha_bytes(v):return hashlib.sha256(v).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(v,msg):
    if not v:raise RuntimeError(msg)
def replace(path,old,new,count=1):
    p=Path(path);s=p.read_text();require(s.count(old)==count,f"anchor drift: {path} :: {old} count={s.count(old)}")
    p.write_text(s.replace(old,new,count))

def patch_manifest_verifier(pack:Path):
    s=pack.read_text()
    start=s.index("def verify_manifest_pair(original: str, compiled: str):")
    end=s.index("\n\ndef merge(",start)
    verifier='''def verify_manifest_pair(original: str, compiled: str):
    old,new=manifest_tree(original),manifest_tree(compiled)
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'):
            tree['attrs'].pop(key,None)
    # 2103169 changes Java presentation only and reuses the exact locked 2103168
    # native-crash-fix APK as its protected base. No manifest delta is allowed.
    require(old==new,'Compiled manifest drift from locked 2103168 base outside version identity')
'''
    pack.write_text(s[:start]+verifier+s[end:])

def promote(source:Path,base168:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    require(base168.is_file(),"Locked 2103168 APK missing")
    require(sha(base168)==LOCKED_NATIVE_SHA,"Wrong locked 2103168 native-crash-fix APK")
    activity=source/REL
    require(activity.is_file() and sha(activity)==SURFACE_ACTIVITY_SHA,
            "Status-bar surface repair source identity mismatch")

    receipt=Path("engine/background-resume-source.json")
    data=json.loads(receipt.read_text())
    require(data.get("version_code")==2103168,"Expected successful status-surface 2103168 source receipt")
    require(data.get("status_bar_surface_matches_visual_theme") is True,
            "Status surface repair receipt missing")
    require(data.get("native_engine_unchanged") is True,
            "Status surface branch unexpectedly changed native engine")

    with zipfile.ZipFile(base168) as z:
        native=z.read(LIB)
    engine_sha=sha_bytes(native)
    require(b"thread state cleaned while waiting for child threads" in native,
            "Locked base does not contain PythonInvoker device crash guard")
    require(b"m_threadState != nullptr" not in native,
            "Locked base still contains old PythonInvoker abort assertion")

    native_proof=Path("baseline168native/PYTHONINVOKER-NATIVE-REPAIR.json")
    require(native_proof.is_file(),"Locked native source proof missing")
    proof=json.loads(native_proof.read_text())
    require(proof.get("upstream_fix")==UPSTREAM and all(proof.get("checks",{}).values()),
            "Locked PythonInvoker source proof failed")

    gradle=source/"tools/android/packaging/xbmc/build.gradle.in"
    replace(gradle,"versionCode 2103168",f"versionCode {VERSION}")
    replace(gradle,'versionName "'+OLD_SURFACE+'"','versionName "'+NEW+'"')

    runtime=Path("scripts/infinity_background_resume.py");s=runtime.read_text()
    require(s.count("VERSION_CODE = 2103168")==1 and s.count("RELEASE = '"+OLD_SURFACE+"'")==1,
            "Status-surface runtime identity drift")
    base_match=re.search(r"BASE_APK_SHA256 = '([0-9a-f]{64})'",s)
    engine_match=re.search(r"BASE_ENGINE_SHA256 = '([0-9a-f]{64})'",s)
    require(base_match and engine_match,"Runtime base hash constants missing")
    s=s.replace("VERSION_CODE = 2103168",f"VERSION_CODE = {VERSION}",1)
    s=s.replace("RELEASE = '"+OLD_SURFACE+"'","RELEASE = '"+NEW+"'",1)
    s=s.replace(base_match.group(0),"BASE_APK_SHA256 = '"+LOCKED_NATIVE_SHA+"'",1)
    s=s.replace(engine_match.group(0),"BASE_ENGINE_SHA256 = '"+engine_sha+"'",1)
    runtime.write_text(s)

    pack=Path("scripts/package_background_resume.py");ptext=pack.read_text()
    needle="Infinity-"+OLD_SURFACE
    require(ptext.count(needle)>=2,"Status-surface packager identity drift")
    pack.write_text(ptext.replace(needle,"Infinity-"+NEW))
    patch_manifest_verifier(pack)

    data["files"][REL]["after"]=sha(activity)
    data["files"]["tools/android/packaging/xbmc/build.gradle.in"]["after"]=sha(gradle)
    data.update(
        version_code=VERSION,version_name=NEW,
        source_parent=2103168,source_parent_locked=True,
        locked_native_parent_commit=LOCKED_NATIVE_COMMIT,
        status_surface_parent_commit=SURFACE_COMMIT,
        protected_candidate14=CANDIDATE14,candidate14_preserved=True,
        pythoninvoker_native_crash_fix_preserved=True,
        pythoninvoker_upstream_fix=UPSTREAM,
        native_engine_sha256=engine_sha,native_engine_recompiled=False,
        status_bar_surface_matches_visual_theme=True,
        transparent_status_bar_over_safe_area=True,
        status_bar_surface_resolver_persisted_theme_aware=True,
        status_bar_surface_source_sha256=SURFACE_ACTIVITY_SHA,
        physical_device_verified=False,candidate_locked=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

    report={
        "build":VERSION,"locked_native_apk_sha256":LOCKED_NATIVE_SHA,
        "locked_native_commit":LOCKED_NATIVE_COMMIT,
        "status_surface_commit":SURFACE_COMMIT,
        "status_surface_activity_sha256":sha(activity),
        "native_engine_sha256":engine_sha,
        "pythoninvoker_guard_present":True,
        "pythoninvoker_abort_assertion_removed":True,
        "candidate14_untouched":True
    }
    (out/"promotion.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: locked 2103168 native fix + proven status-bar surface repair promoted to 2103169")

def verify(final:Path,base168:Path,audit:Path):
    require(final.is_file(),"Signed 2103169 APK missing")
    a=json.loads(audit.read_text())
    require(a["version_code"]==VERSION and a["version_name"]==NEW,"2103169 identity mismatch")
    require(a["signer_certificate_sha256"]==CERT,"Infinity signer changed")
    require(a["apk_sha256"]==sha(final),"APK hash receipt mismatch")

    with zipfile.ZipFile(final) as new,zipfile.ZipFile(base168) as old:
        require(new.read(LIB)==old.read(LIB),"Locked native crash-fix libkodi.so changed")
        native=new.read(LIB)
        require(b"thread state cleaned while waiting for child threads" in native,
                "PythonInvoker crash guard missing from final APK")
        require(b"m_threadState != nullptr" not in native,
                "Old PythonInvoker abort assertion returned")

        old_native={n for n in old.namelist() if n.startswith("lib/") and not n.endswith("/")}
        new_native={n for n in new.namelist() if n.startswith("lib/") and not n.endswith("/")}
        require(old_native==new_native,"Native library inventory changed")
        for n in old_native:require(old.read(n)==new.read(n),"Native entry changed: "+n)

        protected={n for n in old.namelist() if n.startswith(("assets/","res/")) or n=="resources.arsc"}
        for n in protected:require(old.read(n)==new.read(n),"Protected resource/asset changed: "+n)

        dex=b"".join(new.read(n) for n in new.namelist() if re.fullmatch(r"classes\d*\.dex",n))
        for token in (
            b"cobraBrowseSystemBarSurfaceColor",b"cobraConfirmBrowseSystemBars",
            b"cobraApplySystemBarsForSurface",b"cobraInstallBrowseSafeArea",
            b"cobraConsumeLauncherPipReturn",b"CobraPlaybackPolicy",
            b"PLAY IN BACKGROUND",b"MiXplorer",b"Previous channel",b"Next channel",b"Lock controls"):
            require(token in dex,"Required combined contract missing: "+repr(token))

    badging=Path("signed169/badging.txt").read_text()
    require("package: name='com.projectinfinity.kodi'" in badging,"Package name changed")
    require("versionCode='2103169'" in badging,"Final APK is not a forward update")

    result={
        "build":VERSION,"version_name":NEW,"apk_sha256":sha(final),"signer":CERT,
        "locked_native_apk_sha256":LOCKED_NATIVE_SHA,
        "native_engine_sha256":sha_bytes(native),
        "pythoninvoker_guard_present":True,
        "pythoninvoker_abort_assertion_removed":True,
        "status_bar_surface_repair_present":True,
        "status_bar_surface_activity_sha256":SURFACE_ACTIVITY_SHA,
        "candidate14_untouched":True,"physical_device_verified":False
    }
    Path("audit169/final-verification.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PASS: installable 2103169 preserves locked native crash fix and status-bar surface repair")

def suite(path,count):
    p=Path(path);require(p.is_file(),"Missing Android test evidence "+str(p))
    root=ET.parse(p).getroot();cases=root.findall("testcase")
    require(len(cases)==count,"Unexpected test count "+str(p)+" "+str(len(cases)))
    require(all(int(root.get(k,"0"))==0 for k in ("failures","errors","skipped")),
            "Incomplete/failed suite "+str(p))
    require(all(c.find(k) is None for c in cases for k in ("failure","error","skipped")),
            "Failed/skipped testcase "+str(p))
    return count

def deliver():
    inherited=0
    for name,count,folder in [
        ("CobraNavigationUiTest",4,"cobra-regression"),("CobraHealthUiTest",7,"cobra-regression"),
        ("Cobra2103159UiTest",2,"experience"),("ExperienceChooserUiTest",6,"experience")]:
        inherited+=suite(Path("audit159/android")/folder/"test-results"/("TEST-com.projectinfinity.kodi."+name+".xml"),count)
    inherited+=suite("audit169/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml",17)
    inherited+=suite("audit169/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml",10)
    c14=suite("audit169/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml",16)
    p164=suite("audit169/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103164PlaybackStabilityTest.xml",26)
    p165=suite("audit169/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103165InsetsPipPlayerTest.xml",6)
    p166=suite("audit169/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103166EndToEndUiAuditTest.xml",8)
    p167=suite("audit169/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103167StatusBarRestoreTest.xml",5)
    surface=suite("audit169/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103168StatusBarSurfaceTest.xml",4)
    total=inherited+c14+p164+p165+p166+p167+surface
    require(total==111,"Expected 111 Android regression tests, got "+str(total))

    source=json.loads(Path("audit169/surface-source-audit.json").read_text())
    require(source.get("passed") and source.get("failed")==[],"Status-bar source audit failed")
    require(source.get("checks",{}).get("persistent_theme_pointer"),"Persistent theme status-bar resolver absent")
    require(source.get("checks",{}).get("root_band_matches_bar"),"Safe-area surface matching absent")

    native=json.loads(Path("baseline168native/PYTHONINVOKER-NATIVE-REPAIR.json").read_text())
    require(native.get("upstream_fix")==UPSTREAM and all(native["checks"].values()),"Native repair proof failed")

    final=json.loads(Path("audit169/final-verification.json").read_text())
    report={
        "build":VERSION,"locked_native_parent":2103168,
        "locked_native_commit":LOCKED_NATIVE_COMMIT,"status_surface_commit":SURFACE_COMMIT,
        "candidate14_untouched":True,"android_tests":total,
        "status_surface_source_checks":len(source["checks"]),
        "pythoninvoker_source_checks":len(native["checks"]),
        "native_engine_recompiled":False,
        "native_engine_preserved_from_locked_2103168":True,
        "physical_device_verified":False,"candidate_locked":False,
        "apk_sha256":final["apk_sha256"],
        "status":"TEST CANDIDATE - physical Fold status-bar surface confirmation required"
    }
    Path("signed169/ACCEPTANCE.json").write_text(json.dumps(report,indent=2)+"\n")
    shutil.copy2("audit169/final-verification.json","signed169/2103169-verification.json")
    shutil.copy2("audit169/surface-source-audit.json","signed169/2103169-status-surface-audit.json")
    shutil.copy2("baseline168native/PYTHONINVOKER-NATIVE-REPAIR.json","signed169/PYTHONINVOKER-NATIVE-REPAIR.json")
    print("PASS:",total,"Android tests + status-surface + locked native crash-repair gates")

if __name__=="__main__":
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("promote");a.add_argument("--source",type=Path,required=True);a.add_argument("--base168",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
    a=sub.add_parser("verify");a.add_argument("--final",type=Path,required=True);a.add_argument("--base168",type=Path,required=True);a.add_argument("--audit",type=Path,required=True)
    sub.add_parser("deliver")
    args=p.parse_args()
    if args.cmd=="promote":promote(args.source,args.base168,args.out)
    elif args.cmd=="verify":verify(args.final,args.base168,args.audit)
    else:deliver()
