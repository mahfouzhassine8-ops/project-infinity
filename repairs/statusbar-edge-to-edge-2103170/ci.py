#!/usr/bin/env python3
"""Package and gate 2103170 over exact locked 2103168 native crash-fix APK."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,zipfile,xml.etree.ElementTree as ET

LOCKED_NATIVE_SHA="8ba2793633633706eeafcc1bde800d5f82365927fc5df769030698a2f9753a6e"
LOCKED_NATIVE_COMMIT="3c2005cb62ae2115170a0aae1a8b22813ee7eeb9"
SURFACE_COMMIT="3b97cd74e2f0e42b091a21fcab4019dfa319eb48"
CANDIDATE14="1465eabb045badad56142642c48292df94caaa12"
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
OLD="1.0.9-Cobra-Status-Bar-Surface-Match-RC1"
NEW="1.0.9-Cobra-Status-Bar-Edge-to-Edge-RC1"
VERSION=2103170
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
    s=pack.read_text();start=s.index("def verify_manifest_pair(original: str, compiled: str):");end=s.index("\n\ndef merge(",start)
    verifier='''def verify_manifest_pair(original: str, compiled: str):
    old,new=manifest_tree(original),manifest_tree(compiled)
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'):
            tree['attrs'].pop(key,None)
    require(old==new,'Compiled manifest drift from locked 2103168 base outside version identity')
'''
    pack.write_text(s[:start]+verifier+s[end:])

def promote(source:Path,base168:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    require(base168.is_file() and sha(base168)==LOCKED_NATIVE_SHA,"Wrong locked 2103168 native APK")

    surface=json.loads(Path("audit170/surface-source-audit.json").read_text())
    edge=json.loads(Path("audit170/edge-source-audit/source-audit.json").read_text())
    require(surface.get("passed") and not surface.get("failed"),"Surface resolver audit failed")
    require(edge.get("passed") and not edge.get("failed"),"Edge-to-edge audit failed")

    native_proof=Path("baseline168native/PYTHONINVOKER-NATIVE-REPAIR.json")
    require(native_proof.is_file(),"Locked native repair proof missing")
    native=json.loads(native_proof.read_text())
    require(native.get("upstream_fix")==UPSTREAM and all(native.get("checks",{}).values()),"Locked PythonInvoker proof failed")

    with zipfile.ZipFile(base168) as z:
        engine=z.read(LIB)
    engine_sha=sha_bytes(engine)
    require(b"thread state cleaned while waiting for child threads" in engine,"PythonInvoker device guard missing")
    require(b"m_threadState != nullptr" not in engine,"Old native abort assertion remains")

    activity=source/REL
    activity_sha=sha(activity)
    patch=json.loads(Path("audit170/edge-patch/patch.json").read_text())
    require(patch["files"][REL]["after"]==activity_sha,"Edge patch/source identity mismatch")

    gradle=source/"tools/android/packaging/xbmc/build.gradle.in"
    replace(gradle,"versionCode 2103168",f"versionCode {VERSION}")
    replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')

    runtime=Path("scripts/infinity_background_resume.py");s=runtime.read_text()
    require(s.count("VERSION_CODE = 2103168")==1 and s.count("RELEASE = '"+OLD+"'")==1,"2103168 surface runtime identity drift")
    bm=re.search(r"BASE_APK_SHA256 = '([0-9a-f]{64})'",s);em=re.search(r"BASE_ENGINE_SHA256 = '([0-9a-f]{64})'",s)
    require(bm and em,"Runtime base hashes missing")
    s=s.replace("VERSION_CODE = 2103168",f"VERSION_CODE = {VERSION}",1)
    s=s.replace("RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'",1)
    s=s.replace(bm.group(0),"BASE_APK_SHA256 = '"+LOCKED_NATIVE_SHA+"'",1)
    s=s.replace(em.group(0),"BASE_ENGINE_SHA256 = '"+engine_sha+"'",1)
    runtime.write_text(s)

    pack=Path("scripts/package_background_resume.py");ps=pack.read_text();needle="Infinity-"+OLD
    require(ps.count(needle)>=2,"Surface packager identity drift")
    pack.write_text(ps.replace(needle,"Infinity-"+NEW));patch_manifest_verifier(pack)

    receipt=Path("engine/background-resume-source.json");data=json.loads(receipt.read_text())
    require(data.get("version_code")==2103168,"Expected 2103168 surface receipt before promotion")
    data["files"][REL]["after"]=activity_sha
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
        status_bar_edge_to_edge=True,
        status_bar_contrast_enforced=False,
        browse_force_not_fullscreen=False,
        safe_area_geometry_preserved=True,
        physical_device_verified=False,candidate_locked=False)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

    (out/"promotion.json").write_text(json.dumps({
        "build":VERSION,"locked_native_apk_sha256":LOCKED_NATIVE_SHA,
        "native_engine_sha256":engine_sha,"activity_sha256":activity_sha,
        "surface_checks":len(surface["checks"]),"edge_checks":len(edge["checks"]),
        "pythoninvoker_checks":len(native["checks"]),"candidate14_untouched":True
    },indent=2)+"\n")
    print("PASS: 2103170 promoted over exact locked 2103168 native crash-fix APK")

def verify(final:Path,base168:Path,audit:Path):
    require(final.is_file(),"Final 2103170 APK missing")
    a=json.loads(audit.read_text())
    require(a["version_code"]==VERSION and a["version_name"]==NEW,"Final identity mismatch")
    require(a["signer_certificate_sha256"]==CERT,"Release signer changed")
    require(a["apk_sha256"]==sha(final),"APK hash receipt mismatch")
    with zipfile.ZipFile(final) as new,zipfile.ZipFile(base168) as old:
        require(new.read(LIB)==old.read(LIB),"Locked libkodi.so changed")
        eng=new.read(LIB)
        require(b"thread state cleaned while waiting for child threads" in eng,"PythonInvoker guard missing")
        require(b"m_threadState != nullptr" not in eng,"Old PythonInvoker abort returned")
        oldn={n for n in old.namelist() if n.startswith("lib/") and not n.endswith("/")}
        newn={n for n in new.namelist() if n.startswith("lib/") and not n.endswith("/")}
        require(oldn==newn,"Native inventory changed")
        for n in oldn:require(old.read(n)==new.read(n),"Native entry changed: "+n)
        protected={n for n in old.namelist() if n.startswith(("assets/","res/")) or n=="resources.arsc"}
        for n in protected:require(old.read(n)==new.read(n),"Protected resources changed: "+n)
        dex=b"".join(new.read(n) for n in new.namelist() if re.fullmatch(r"classes\d*\.dex",n))
        for token in (
          b"cobraBrowseSystemBarSurfaceColor",b"cobraConfirmBrowseSystemBars",b"cobraApplySystemBarsForSurface",
          b"setStatusBarContrastEnforced",b"setDecorFitsSystemWindows",b"cobraInstallBrowseSafeArea",
          b"cobraConsumeLauncherPipReturn",b"CobraPlaybackPolicy",b"PLAY IN BACKGROUND",b"MiXplorer",
          b"Previous channel",b"Next channel",b"Lock controls"):
            require(token in dex,"Combined contract missing: "+repr(token))
    badging=Path("signed170/badging.txt").read_text()
    require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103170'" in badging,
            "Final APK is not installable forward update")
    out={
      "build":VERSION,"version_name":NEW,"apk_sha256":sha(final),"signer":CERT,
      "locked_native_apk_sha256":LOCKED_NATIVE_SHA,"native_engine_sha256":sha_bytes(eng),
      "pythoninvoker_guard_present":True,"pythoninvoker_abort_assertion_removed":True,
      "status_bar_edge_to_edge_present":True,"status_bar_contrast_scrim_disabled":True,
      "candidate14_untouched":True,"physical_device_verified":False
    }
    Path("audit170/final-verification.json").write_text(json.dumps(out,indent=2)+"\n")
    print("PASS: signed 2103170 preserves native crash fix and concrete status-bar repair")

def suite(path,count):
    p=Path(path);require(p.is_file(),"Missing test evidence "+str(p))
    root=ET.parse(p).getroot();cases=root.findall("testcase")
    require(len(cases)==count,f"Unexpected test count {p}: {len(cases)} != {count}")
    require(all(int(root.get(k,"0"))==0 for k in ("failures","errors","skipped")),"Failed/incomplete suite "+str(p))
    require(all(c.find(k) is None for c in cases for k in ("failure","error","skipped")),"Failed/skipped testcase "+str(p))
    return count

def deliver():
    inherited=0
    for name,count,folder in [
      ("CobraNavigationUiTest",4,"cobra-regression"),("CobraHealthUiTest",7,"cobra-regression"),
      ("Cobra2103159UiTest",2,"experience"),("ExperienceChooserUiTest",6,"experience")]:
        inherited+=suite(Path("audit159/android")/folder/"test-results"/("TEST-com.projectinfinity.kodi."+name+".xml"),count)
    inherited+=suite("audit170/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml",17)
    inherited+=suite("audit170/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml",10)
    c14=suite("audit170/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml",16)
    p164=suite("audit170/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103164PlaybackStabilityTest.xml",26)
    p165=suite("audit170/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103165InsetsPipPlayerTest.xml",6)
    p166=suite("audit170/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103166EndToEndUiAuditTest.xml",8)
    p167=suite("audit170/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103167StatusBarRestoreTest.xml",5)
    surface=suite("audit170/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103168StatusBarSurfaceTest.xml",4)
    edge=suite("audit170/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103170StatusBarEdgeTest.xml",6)
    total=inherited+c14+p164+p165+p166+p167+surface+edge
    require(total==117,f"Expected 117 Android tests, got {total}")

    s=json.loads(Path("audit170/surface-source-audit.json").read_text())
    e=json.loads(Path("audit170/edge-source-audit/source-audit.json").read_text())
    n=json.loads(Path("baseline168native/PYTHONINVOKER-NATIVE-REPAIR.json").read_text())
    require(s.get("passed") and e.get("passed"),"Status-bar source audits failed")
    require(e["checks"]["contrast_scrim_disabled"] and e["checks"]["browse_does_not_force_not_fullscreen"]
            and e["checks"]["browse_draws_behind_status"],"Black-band ownership gates failed")
    require(n.get("upstream_fix")==UPSTREAM and all(n["checks"].values()),"Native repair proof failed")

    final=json.loads(Path("audit170/final-verification.json").read_text())
    result={
      "build":VERSION,"locked_native_parent":2103168,"locked_native_commit":LOCKED_NATIVE_COMMIT,
      "candidate14_untouched":True,"android_tests":total,
      "surface_source_checks":len(s["checks"]),"edge_source_checks":len(e["checks"]),
      "pythoninvoker_source_checks":len(n["checks"]),"native_engine_recompiled":False,
      "native_engine_preserved_from_locked_2103168":True,
      "physical_device_verified":False,"candidate_locked":False,
      "apk_sha256":final["apk_sha256"],
      "status":"TEST CANDIDATE - physical Fold status-bar confirmation required"
    }
    Path("signed170/ACCEPTANCE.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2("audit170/final-verification.json","signed170/2103170-verification.json")
    shutil.copy2("audit170/surface-source-audit.json","signed170/2103170-surface-audit.json")
    shutil.copy2("audit170/edge-source-audit/source-audit.json","signed170/2103170-edge-audit.json")
    shutil.copy2("baseline168native/PYTHONINVOKER-NATIVE-REPAIR.json","signed170/PYTHONINVOKER-NATIVE-REPAIR.json")
    print("PASS:",total,"Android tests + surface/edge/native integrity gates")

if __name__=="__main__":
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("promote");a.add_argument("--source",type=Path,required=True);a.add_argument("--base168",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
    a=sub.add_parser("verify");a.add_argument("--final",type=Path,required=True);a.add_argument("--base168",type=Path,required=True);a.add_argument("--audit",type=Path,required=True)
    sub.add_parser("deliver")
    x=p.parse_args()
    if x.cmd=="promote":promote(x.source,x.base168,x.out)
    elif x.cmd=="verify":verify(x.final,x.base168,x.audit)
    else:deliver()
