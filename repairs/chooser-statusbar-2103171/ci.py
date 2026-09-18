#!/usr/bin/env python3
"""Package/gate 2103171 over exact passed 2103170 without rebuilding native Kodi."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT="6046c0ac64c7ef83a65550d53ffd4211c6cb5bef"
OLD="1.0.9-Cobra-Status-Bar-Edge-to-Edge-RC1"
NEW="1.0.9-Cobra-Chooser-Status-Bar-Surface-RC1"
VERSION=2103171
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
SPLASH="tools/android/packaging/xbmc/src/Splash.java.in"

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def replace(path,old,new,count=1):
 p=Path(path);s=p.read_text();require(s.count(old)==count,f"identity anchor drift {path}: {old} count={s.count(old)}")
 p.write_text(s.replace(old,new,count) if count==1 else s.replace(old,new))
def run(*args):subprocess.run(list(map(str,args)),check=True)

def upgrade():
 receipt=Path("engine/background-resume-source.json");data=json.loads(receipt.read_text())
 require(data.get("version_code")==2103170 and data.get("version_name")==OLD,"Expected exact promoted 2103170 source receipt")
 for rel,row in data.get("files",{}).items():
  require(sha(Path("kodi")/rel)==row["after"],"2103170 source receipt drift: "+rel)

 run("python3",ROOT/"apply.py","--source","kodi","--receipt",receipt,"--out","audit171/patch")
 patch=json.loads(Path("audit171/patch/patch.json").read_text())
 data["files"][SPLASH]["after"]=patch["files"][SPLASH]["after"]

 gradle=Path("kodi/tools/android/packaging/xbmc/build.gradle.in")
 replace(gradle,"versionCode 2103170",f"versionCode {VERSION}")
 replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')

 runtime=Path("scripts/infinity_background_resume.py")
 replace(runtime,"VERSION_CODE = 2103170",f"VERSION_CODE = {VERSION}")
 replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")

 pack=Path("scripts/package_background_resume.py");s=pack.read_text();needle="Infinity-"+OLD
 require(s.count(needle)>=2,"2103170 packager identity drift");pack.write_text(s.replace(needle,"Infinity-"+NEW))

 data["files"]["tools/android/packaging/xbmc/build.gradle.in"]["after"]=sha(gradle)
 data.update(
   version_code=VERSION,version_name=NEW,
   source_parent=2103170,source_parent_locked=True,
   locked_parent_commit=BASE_COMMIT,candidate_locked=False,
   chooser_status_bar_surface_fixed=True,
   chooser_status_bar_edge_to_edge=True,
   chooser_status_bar_contrast_enforced=False,
   chooser_status_icon_contrast_from_theme=True,
   chooser_safe_area_transient_zero_stabilized=True,
   cobra_runtime_activity_unchanged=True,
   native_engine_recompiled=False,
   physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

 for rel,row in data["files"].items():
  require(sha(Path("kodi")/rel)==row["after"],"Final 2103171 source receipt drift: "+rel)

 run("python3",ROOT/"source_audit.py","--source","kodi","--patch","audit171/patch/patch.json","--receipt",receipt,"--out","audit171/source-audit")

 with Path("audit171/native-after.patch").open("wb") as out:
  subprocess.run(["git","-C","kodi","diff","--binary","--","xbmc"],stdout=out,check=True)
 require(Path("audit171/native-after.patch").read_bytes()==Path("engine/native-before.patch").read_bytes(),"Native source changed")
 print("PASS: exact 2103170 -> 2103171 chooser-only status-bar repair; native tree unchanged")

def verify():
 base=Path("baseline170/Infinity-"+OLD+".apk")
 final=Path("signed171/Infinity-"+NEW+".apk")
 require(base.is_file() and final.is_file(),"Baseline/final APK missing")
 base_verify=Path("baseline170/2103170-verification.json")
 require(base_verify.is_file(),"2103170 verification receipt missing")
 bv=json.loads(base_verify.read_text());require(bv["apk_sha256"]==sha(base),"Wrong exact passed 2103170 APK")
 audit=json.loads(Path("signed171/background-resume-apk-audit.json").read_text())
 require(audit["version_code"]==VERSION and audit["version_name"]==NEW,"Final 2103171 identity mismatch")
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
  for token in (b"cobraPrepareExperienceSystemBars",b"cobraChooserDarkStatusIcons",
                b"APPEARANCE_LIGHT_STATUS_BARS",b"experience-themed-root",
                b"cobraApplySystemBarsForSurface",b"setStatusBarContrastEnforced"):
   require(token in dex,"Combined contract missing: "+repr(token))
  require(b"Cobra2103171ChooserStatusBarTest" not in dex,"Test code packaged in release APK")

 result={
  "build":VERSION,"base_build":2103170,"base_commit":BASE_COMMIT,
  "base_apk_sha256":sha(base),"apk_sha256":sha(final),"signer":CERT,
  "native_entries":len(old_native),"protected_resource_entries":len(protected),
  "native_engine_recompiled":False,"chooser_only_android_delta":True,
  "physical_device_verified":False}
 Path("audit171/final-verification.json").write_text(json.dumps(result,indent=2)+"\n")
 print("PASS: signed 2103171 preserves exact 2103170 native/resources and release signer")

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
 inherited+=suite("audit171/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml",17)
 inherited+=suite("audit171/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml",10)
 c14=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml",16)
 p164=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103164PlaybackStabilityTest.xml",26)
 p165=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103165InsetsPipPlayerTest.xml",6)
 p166=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103166EndToEndUiAuditTest.xml",8)
 p167=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103170StatusBarRestoreSupersessionTest.xml",5)
 surface=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103168StatusBarSurfaceTest.xml",4)
 edge=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103170StatusBarEdgeTest.xml",7)
 chooser=suite("audit171/targeted/test-results/TEST-com.projectinfinity.kodi.Cobra2103171ChooserStatusBarTest.xml",7)
 total=inherited+c14+p164+p165+p166+p167+surface+edge+chooser
 require(total==125,f"Expected 125 Android tests, got {total}")

 source=json.loads(Path("audit171/source-audit/source-audit.json").read_text())
 final=json.loads(Path("audit171/final-verification.json").read_text())
 require(source.get("passed") and not source.get("failed"),"Chooser source audit failed")
 result={
  "build":VERSION,"locked_parent":2103170,"locked_parent_commit":BASE_COMMIT,
  "android_tests":total,"new_chooser_tests":chooser,
  "chooser_status_bar_black_band_fixed":True,
  "light_dark_oled_icon_contrast_gated":True,
  "transient_zero_insets_gated":True,
  "legacy_fallback_preserved":True,
  "cobra_activity_unchanged":True,"native_engine_recompiled":False,
  "apk_sha256":final["apk_sha256"],"physical_device_verified":False,
  "candidate_locked":False,
  "status":"TEST CANDIDATE - physical Fold chooser confirmation required"}
 Path("signed171/ACCEPTANCE.json").write_text(json.dumps(result,indent=2)+"\n")
 shutil.copy2("audit171/final-verification.json","signed171/2103171-verification.json")
 shutil.copy2("audit171/source-audit/source-audit.json","signed171/2103171-source-audit.json")
 print("PASS:",total,"Android tests + chooser source/native/resource integrity gates")

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("phase",choices=["upgrade","verify","deliver"]);a=p.parse_args()
 globals()[a.phase]()
