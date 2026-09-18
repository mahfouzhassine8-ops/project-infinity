#!/usr/bin/env python3
"""Package/gate 2103173 buffering stability over exact locked 2103171."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT="59cf1958e5d911ede8df9b04c200025f4b39026e"
OLD="1.0.9-Cobra-Chooser-Status-Bar-Surface-RC1"
NEW="1.0.9-Cobra-Buffering-Stability-RC1"
VERSION=2103173
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
ACT="tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in"

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def replace(path,old,new,count=1):
 p=Path(path);s=p.read_text();require(s.count(old)==count,f"identity anchor drift {path}: {old} count={s.count(old)}")
 p.write_text(s.replace(old,new,count) if count==1 else s.replace(old,new))
def run(*args):subprocess.run(list(map(str,args)),check=True)

def upgrade():
 receipt=Path("engine/background-resume-source.json");data=json.loads(receipt.read_text())
 require(data.get("version_code")==2103171 and data.get("version_name")==OLD,"Expected exact locked 2103171 source receipt")
 for rel,row in data.get("files",{}).items():
  require(sha(Path("kodi")/rel)==row["after"],"2103171 source receipt drift: "+rel)

 run("python3",ROOT/"apply.py","--source","kodi","--receipt",receipt,"--out","audit173/patch")
 patch=json.loads(Path("audit173/patch/patch.json").read_text())
 data["files"][ACT]["after"]=patch["files"][ACT]["after"]

 gradle=Path("kodi/tools/android/packaging/xbmc/build.gradle.in")
 replace(gradle,"versionCode 2103171",f"versionCode {VERSION}")
 replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')

 runtime=Path("scripts/infinity_background_resume.py")
 replace(runtime,"VERSION_CODE = 2103171",f"VERSION_CODE = {VERSION}")
 replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")

 pack=Path("scripts/package_background_resume.py");s=pack.read_text();needle="Infinity-"+OLD
 require(s.count(needle)>=2,"2103171 packager identity drift");pack.write_text(s.replace(needle,"Infinity-"+NEW))

 data["files"]["tools/android/packaging/xbmc/build.gradle.in"]["after"]=sha(gradle)
 data.update(
   version_code=VERSION,version_name=NEW,
   source_parent=2103171,source_parent_locked=True,
   locked_parent_commit=BASE_COMMIT,candidate_locked=False,
   buffering_watchdog_reprepare_removed=True,
   single_view_buffer_headroom=True,
   preview_fullscreen_session_reuse_preserved=True,
   multi_view_buffer_limits_preserved=True,
   http_timeouts_preserved=True,
   cobra_statusbar_2103171_preserved=True,
   native_engine_recompiled=False,
   physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

 for rel,row in data["files"].items():
  require(sha(Path("kodi")/rel)==row["after"],"Final 2103173 source receipt drift: "+rel)

 run("python3",ROOT/"source_audit.py","--source","kodi","--patch","audit173/patch/patch.json","--out","audit173/source-audit")

 with Path("audit173/native-after.patch").open("wb") as out:
  subprocess.run(["git","-C","kodi","diff","--binary","--","xbmc"],stdout=out,check=True)
 require(Path("audit173/native-after.patch").read_bytes()==Path("engine/native-before.patch").read_bytes(),"Native source changed")
 print("PASS: exact 2103171 -> 2103173 buffering stability; native tree unchanged")

def verify():
 base=Path("baseline171/Infinity-"+OLD+".apk")
 final=Path("signed173/Infinity-"+NEW+".apk")
 require(base.is_file() and final.is_file(),"Baseline/final APK missing")
 base_verify=Path("baseline171/2103171-verification.json")
 require(base_verify.is_file(),"2103171 verification receipt missing")
 bv=json.loads(base_verify.read_text());require(bv["apk_sha256"]==sha(base),"Wrong exact locked 2103171 APK")
 audit=json.loads(Path("signed173/background-resume-apk-audit.json").read_text())
 require(audit["version_code"]==VERSION and audit["version_name"]==NEW,"Final 2103173 identity mismatch")
 require(audit["signer_certificate_sha256"]==CERT and audit["apk_sha256"]==sha(final),"Signer/hash mismatch")
 require(not audit["native_recompiled"],"Native engine was rebuilt")

 with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
  old_native={n for n in old.namelist() if n.startswith("lib/") and not n.endswith("/")}
  new_native={n for n in new.namelist() if n.startswith("lib/") and not n.endswith("/")}
  require(old_native==new_native,"Native inventory changed")
  for n in old_native:require(old.read(n)==new.read(n),"Native entry changed: "+n)
  protected={n for n in old.namelist() if n.startswith(("assets/","res/")) or n=="resources.arsc"}
  require(protected=={n for n in new.namelist() if n.startswith(("assets/","res/")) or n=="resources.arsc"},"Protected resource inventory changed")
  for n in protected:require(old.read(n)==new.read(n),"Protected resource changed: "+n)
  dex=b"".join(new.read(n) for n in new.namelist() if re.fullmatch(r"classes\d*\.dex",n))
  for token in (b"buffer_wait_network",b"same_session=true",b"CobraBufferingPolicy",
                b"promoteCobraPreviewToFullscreen",b"cobraPrepareExperienceSystemBars",
                b"cobraApplySystemBarsForSurface"):
   require(token in dex,"Combined 2103173 contract missing: "+repr(token))
  require(b"Cobra2103173BufferingStabilityTest" not in dex,"Test code packaged in release APK")

 badging=Path("signed173/badging.txt").read_text()
 require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103173'" in badging,
         "Final APK is not installable forward update")

 result={
  "build":VERSION,"base_build":2103171,"base_commit":BASE_COMMIT,
  "base_apk_sha256":sha(base),"apk_sha256":sha(final),"signer":CERT,
  "native_entries":len(old_native),"protected_resource_entries":len(protected),
  "native_engine_recompiled":False,"buffering_android_delta_only":True,
  "physical_device_verified":False}
 Path("audit173/final-verification.json").write_text(json.dumps(result,indent=2)+"\n")
 print("PASS: signed 2103173 preserves exact 2103171 native/resources and release signer")

def suite(path,count):
 p=Path(path);require(p.is_file(),"Missing test evidence "+str(p));root=ET.parse(p).getroot();cases=root.findall("testcase")
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
 inherited+=suite("audit173/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml",17)
 inherited+=suite("audit173/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml",10)
 targeted=0
 for name,count in [
  ("Cobra2103162ThemeRotationTest",16),("Cobra2103164PlaybackStabilityTest",26),
  ("Cobra2103165InsetsPipPlayerTest",6),("Cobra2103166EndToEndUiAuditTest",8),
  ("Cobra2103170StatusBarRestoreSupersessionTest",5),("Cobra2103168StatusBarSurfaceTest",4),
  ("Cobra2103170StatusBarEdgeTest",7),("Cobra2103171ChooserStatusBarTest",7),
  ("Cobra2103173BufferingStabilityTest",4)]:
  targeted+=suite(Path("audit173/targeted/test-results")/("TEST-com.projectinfinity.kodi."+name+".xml"),count)
 total=inherited+targeted
 require(total==129,f"Expected 129 Android tests, got {total}")

 source=json.loads(Path("audit173/source-audit/source-audit.json").read_text())
 final=json.loads(Path("audit173/final-verification.json").read_text())
 require(source.get("passed") and not source.get("failed"),"Buffering source audit failed")
 result={
  "build":VERSION,"locked_parent":2103171,"locked_parent_commit":BASE_COMMIT,
  "android_tests":total,"new_buffering_tests":4,
  "watchdog_reprepare_removed":True,
  "single_view_headroom":"15s min / 60s max / 48 MiB target / 5s rebuffer",
  "multi_view_profile_preserved":True,
  "preview_fullscreen_session_reuse_preserved":True,
  "http_timeouts_preserved":True,
  "native_engine_recompiled":False,
  "apk_sha256":final["apk_sha256"],"physical_device_verified":False,
  "candidate_locked":False,
  "status":"TEST CANDIDATE - physical stream buffering confirmation required"}
 Path("signed173/ACCEPTANCE.json").write_text(json.dumps(result,indent=2)+"\n")
 shutil.copy2("audit173/final-verification.json","signed173/2103173-verification.json")
 shutil.copy2("audit173/source-audit/source-audit.json","signed173/2103173-source-audit.json")
 print("PASS:",total,"Android tests + buffering/session/native/resource integrity gates")

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("phase",choices=["upgrade","verify","deliver"]);a=p.parse_args()
 globals()[a.phase]()
