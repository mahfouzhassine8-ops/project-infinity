#!/usr/bin/env python3
"""Package/gate 2103179 buffer resilience over exact passed/tested 2103178 without rebuilding native."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
BASE_COMMIT="56792d4e44b381cff2c900e7b86ed99265b55d04"
OLD="1.0.9-Cobra-Timeshift-Mini-Player-Repair-RC1"
NEW="1.0.9-Cobra-Buffer-Resilience-RC1"
VERSION=2103179
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
 require(data.get("version_code")==2103178 and data.get("version_name")==OLD,"Expected exact passed 2103178 source receipt")
 for rel,row in data.get("files",{}).items():
  require(sha(Path("kodi")/rel)==row["after"],"2103178 source receipt drift: "+rel)

 run("python3",ROOT/"apply.py","--source","kodi","--receipt",receipt,"--out","audit179/patch")
 patch=json.loads(Path("audit179/patch/patch.json").read_text())
 data["files"][ACT]["after"]=patch["files"][ACT]["after"]

 gradle=Path("kodi/tools/android/packaging/xbmc/build.gradle.in")
 replace(gradle,"versionCode 2103178",f"versionCode {VERSION}")
 replace(gradle,'versionName "'+OLD+'"','versionName "'+NEW+'"')

 runtime=Path("scripts/infinity_background_resume.py")
 replace(runtime,"VERSION_CODE = 2103178",f"VERSION_CODE = {VERSION}")
 replace(runtime,"RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'")

 pack=Path("scripts/package_background_resume.py");s=pack.read_text();needle="Infinity-"+OLD
 require(s.count(needle)>=2,"2103178 packager identity drift");pack.write_text(s.replace(needle,"Infinity-"+NEW))

 data["files"]["tools/android/packaging/xbmc/build.gradle.in"]["after"]=sha(gradle)
 data.update(
   version_code=VERSION,version_name=NEW,
   source_parent=2103178,source_parent_locked=True,locked_parent_commit=BASE_COMMIT,candidate_locked=False,
   diagnostics_evidence="Cobra-Diagnostics-20260919-084842-UTC.zip",
   live_reserve_seconds=9,provider_connect_timeout_ms=7000,provider_read_timeout_ms=5000,
   reconnect_backoff_initial_ms=250,reconnect_backoff_max_ms=1500,
   partial_segment_preservation=True,visible_rebuffer_threshold_ms=750,
   rewind_contract_preserved=True,timeshift_transport_repaired=True,
   mini_preview_same_player_handoff=True,display_performance_preserved=True,
   provider_catchup_preserved=True,last_channel_preserved=True,
   normal_single_load_control="Media3 default",stall_watchdog_reprepare=False,
   native_engine_recompiled=False,theme_zip_changed=False,physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

 for rel,row in data["files"].items():
  require(sha(Path("kodi")/rel)==row["after"],"Final 2103179 source receipt drift: "+rel)

 run("python3",ROOT/"source_audit.py","--source","kodi","--patch","audit179/patch/patch.json","--out","audit179/source-audit")
 with Path("audit179/native-after.patch").open("wb") as out:
  subprocess.run(["git","-C","kodi","diff","--binary","--","xbmc"],stdout=out,check=True)
 require(Path("audit179/native-after.patch").read_bytes()==Path("engine/native-before.patch").read_bytes(),"Native source changed")
 print("PASS: exact 2103178 -> 2103179 buffer resilience; rewind ownership and native tree preserved")

def verify():
 base=Path("baseline178/Infinity-"+OLD+".apk")
 final=Path("signed179/Infinity-"+NEW+".apk")
 require(base.is_file() and final.is_file(),"Baseline/final APK missing")
 base_verify=Path("baseline178/2103178-verification.json")
 require(base_verify.is_file(),"2103178 verification receipt missing")
 bv=json.loads(base_verify.read_text());require(bv["apk_sha256"]==sha(base),"Wrong exact passed 2103178 APK")
 audit=json.loads(Path("signed179/background-resume-apk-audit.json").read_text())
 require(audit["version_code"]==VERSION and audit["version_name"]==NEW,"Final 2103179 identity mismatch")
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
  for token in (
    b"CobraTimeshiftTransportPolicy",b"TIME-OFFSET=-9.0",b"buffering_transitions",b"rebuffer_duration_ms",
    b"mini_preview_direct",b"timeshift_http_failures",b"preview-timeshift-fullscreen",
    b"timeshift-transport-fallback",b"Capture diagnostics",b"preview_timeshift_starts",
    b"surface_attach_calls",b"last_prepare_reason",b"cobra_display_performance",
    b"preferredDisplayModeId",b"cobra_performance_proof_overlay",b"CobraLocalTimeshiftSession",
    b"cobra_live_timeshift_seek",b"cobra_last_channel",b"network_transport",
    b"buffer_observed_no_restart",b"cobra_live_rewind_enabled",b"cobra-browse-background",
    b"experience-safe-content"):
   require(token in dex,"Combined 2103179 contract missing: "+repr(token))
  require(b"Cobra2103178TimeshiftMiniPlayerTest" not in dex,"2103178 test code packaged in release APK")
  require(b"Cobra2103179BufferResilienceTest" not in dex,"2103179 test code packaged in release APK")

 badging=Path("signed179/badging.txt").read_text()
 require("package: name='com.projectinfinity.kodi'" in badging and "versionCode='2103179'" in badging,
         "Final APK is not installable forward update")
 result={
  "build":VERSION,"base_build":2103178,"base_commit":BASE_COMMIT,
  "base_apk_sha256":sha(base),"apk_sha256":sha(final),"signer":CERT,
  "native_entries":len(old_native),"protected_resource_entries":len(protected),
  "native_engine_recompiled":False,"theme_zip_changed":False,
  "rewind_contract_preserved":True,"live_reserve_seconds":9,
  "partial_segment_preservation":True,"provider_connect_timeout_ms":7000,
  "provider_read_timeout_ms":5000,"reconnect_backoff_max_ms":1500,
  "visible_rebuffer_threshold_ms":750,"physical_device_verified":False}
 Path("audit179/final-verification.json").write_text(json.dumps(result,indent=2)+"\n")
 print("PASS: signed 2103179 preserves exact 2103178 native/resources/signer and rewind contract")

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
 inherited+=suite("audit179/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml",17)
 inherited+=suite("audit179/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml",10)
 targeted=0
 for name,count in [
  ("Cobra2103162ThemeRotationTest",15),("Cobra2103164PlaybackStabilityTest",26),
  ("Cobra2103165InsetsPipPlayerTest",6),("Cobra2103166EndToEndUiAuditTest",8),
  ("Cobra2103170StatusBarRestoreSupersessionTest",5),("Cobra2103170StatusBarEdgeTest",7),
  ("Cobra2103175FullscreenBackgroundTest",12),("Cobra2103176LiveRewindTest",5),
  ("Cobra2103177FinalFeatureFreezeTest",10),("Cobra2103178TimeshiftMiniPlayerTest",10),
  ("Cobra2103179BufferResilienceTest",7)]:
  targeted+=suite(Path("audit179/targeted/test-results")/("TEST-com.projectinfinity.kodi."+name+".xml"),count)
 total=inherited+targeted
 require(total==157,f"Expected 157 Android tests, got {total}")
 source=json.loads(Path("audit179/source-audit/source-audit.json").read_text())
 final=json.loads(Path("audit179/final-verification.json").read_text())
 require(source.get("passed") and not source.get("failed"),"2103179 source audit failed")
 result={
  "build":VERSION,"locked_parent":2103178,"locked_parent_commit":BASE_COMMIT,
  "android_tests":total,"new_buffer_resilience_tests":7,
  "rewind_contract_preserved":True,"live_reserve_seconds":9,
  "partial_segment_preservation":True,"provider_connect_timeout_ms":7000,
  "provider_read_timeout_ms":5000,"reconnect_backoff_initial_ms":250,
  "reconnect_backoff_max_ms":1500,"visible_rebuffer_threshold_ms":750,
  "timeshift_direct_fallback":True,"mini_preview_same_player_handoff":True,
  "display_performance_preserved":True,"provider_catchup_preserved":True,
  "last_channel_preserved":True,"normal_single_load_control":"Media3 default",
  "stall_watchdog_reprepare":False,"native_engine_recompiled":False,"theme_zip_changed":False,
  "apk_sha256":final["apk_sha256"],"physical_device_verified":False,"candidate_locked":False,
  "status":"TEST CANDIDATE - physical channel-switch / buffering / rewind comparison required before lock"}
 Path("signed179/ACCEPTANCE.json").write_text(json.dumps(result,indent=2)+"\n")
 shutil.copy2("audit179/final-verification.json","signed179/2103179-verification.json")
 shutil.copy2("audit179/source-audit/source-audit.json","signed179/2103179-source-audit.json")
 print("PASS:",total,"Android tests + 2103179 integrity gates")

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("phase",choices=["upgrade","verify","deliver"]);a=p.parse_args();globals()[a.phase]()
