#!/usr/bin/env python3
"""Package and verify 2103164 from exact successful 2103163 shell + rebuilt PythonInvoker native engine."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,zipfile,xml.etree.ElementTree as ET

RUN6_SHA="5991bdd239c0c26c67a6535d9d08671ef865a48e88a3691a5d7f8993d4b67be9"
CERT="d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7"
OLD="1.0.9-Cobra-Candidate14-Five-Fixes-RC1"
NEW="1.0.9-Cobra-PythonInvoker-Stability-RC1"
VERSION=2103164
LIB="lib/arm64-v8a/libkodi.so"

def sha_bytes(v):return hashlib.sha256(v).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(v,msg):
 if not v:raise RuntimeError(msg)
def run(*args,output=None,cwd=None):
 r=subprocess.run(list(map(str,args)),cwd=cwd,check=True,stdout=subprocess.PIPE if output else None,stderr=subprocess.STDOUT if output else None,text=True)
 if output:Path(output).write_text(r.stdout);return r.stdout
 return ""

def controlled_base(run6:Path,native_apk:Path,out:Path):
 require(sha(run6)==RUN6_SHA,"Wrong 2103163 run-6 APK")
 with zipfile.ZipFile(run6) as old,zipfile.ZipFile(native_apk) as native:
  require(LIB in native.namelist(),"Rebuilt engine APK has no libkodi.so")
  patched=native.read(LIB);before=old.read(LIB)
  require(patched!=before,"Python repair did not change libkodi.so")
  require(b"thread state cleaned while waiting for child threads" in patched,"Patched native binary missing device-abort guard")
  require(b'm_threadState != nullptr' not in patched,"Old PythonInvoker line-412 assertion remains in native binary")
  with zipfile.ZipFile(out,"w") as z:
   for info in old.infolist():
    data=patched if info.filename==LIB else old.read(info.filename)
    z.writestr(info,data)
 with zipfile.ZipFile(out) as new,zipfile.ZipFile(run6) as old:
  require(set(new.namelist())==set(old.namelist()),"Controlled base inventory changed")
  changed=[]
  for name in old.namelist():
   if old.read(name)!=new.read(name):changed.append(name)
  require(changed==[LIB],"Controlled base changed more than libkodi.so: "+repr(changed))
 return sha_bytes(patched),sha_bytes(before)

def promote(shell:Path,run6:Path,native_apk:Path,outdir:Path):
 outdir.mkdir(parents=True,exist_ok=True)
 base=outdir/"Infinity-2103163-PythonInvoker-Patched-Base.apk"
 new_engine,old_engine=controlled_base(run6,native_apk,base)
 require(new_engine!=old_engine,"Native hash unchanged")
 # Promote only shell identity + expected protected base/native hashes.
 gradle=shell/"tools/android/packaging/xbmc/build.gradle.in"
 s=gradle.read_text();require(s.count("versionCode 2103163")==1,"Shell versionCode drift");require(s.count('versionName "'+OLD+'"')==1,"Shell versionName drift")
 gradle.write_text(s.replace("versionCode 2103163",f"versionCode {VERSION}",1).replace('versionName "'+OLD+'"','versionName "'+NEW+'"',1))
 runtime=Path("scripts/infinity_background_resume.py");s=runtime.read_text()
 require(s.count("VERSION_CODE = 2103163")==1 and s.count("RELEASE = '"+OLD+"'")==1,"Runtime identity drift")
 old_base=re.search(r"BASE_APK_SHA256 = '([0-9a-f]{64})'",s);old_engine_match=re.search(r"BASE_ENGINE_SHA256 = '([0-9a-f]{64})'",s)
 require(old_base and old_engine_match,"Runtime base hash constants missing")
 s=s.replace("VERSION_CODE = 2103163",f"VERSION_CODE = {VERSION}",1).replace("RELEASE = '"+OLD+"'","RELEASE = '"+NEW+"'",1)
 s=s.replace(old_base.group(0),"BASE_APK_SHA256 = '"+sha(base)+"'",1)
 s=s.replace(old_engine_match.group(0),"BASE_ENGINE_SHA256 = '"+new_engine+"'",1)
 runtime.write_text(s)
 pack=Path("scripts/package_background_resume.py");s=pack.read_text();needle="Infinity-"+OLD
 require(s.count(needle)>=2,"Packager 2103163 identity drift");s=s.replace(needle,"Infinity-"+NEW)
 # 2103163 is now the protected base APK. Its manifest already contains the approved
 # foreground service/control bridge/permissions. The old packager verifier was designed
 # for run-40 as the base and therefore stripped those nodes only from the newly compiled
 # manifest, which creates a false mismatch when both old and new legitimately contain them.
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
    require(old==new,'Compiled manifest drift from protected 2103163 base outside version identity')
'''
 s=s[:start]+verifier+s[end:]
 pack.write_text(s)
 receipt=Path("engine/background-resume-source.json");data=json.loads(receipt.read_text());require(data["version_code"]==2103163,"Wrong shell source receipt")
 rel="tools/android/packaging/xbmc/build.gradle.in";require(rel in data["files"],"Gradle missing from source receipt")
 data["files"][rel]["after"]=sha(gradle)
 data.update(version_code=VERSION,version_name=NEW,source_parent=2103163,locked_parent=2103162,candidate_locked=False,
   pythoninvoker_threadstate_repair=True,pythoninvoker_upstream_fix="0186f895271d4ce7d240b4e9f40da03b4833539d",
   pythoninvoker_device_abort_guard=True,native_engine_unchanged=False,native_engine_rebuilt=True,
   previous_native_engine_sha256=old_engine,native_engine_sha256=new_engine,physical_device_verified=False)
 receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
 report={"build":VERSION,"run6_apk_sha256":RUN6_SHA,"controlled_base_sha256":sha(base),
   "previous_native_engine_sha256":old_engine,"native_engine_sha256":new_engine,
   "only_controlled_base_entry_changed":LIB,"candidate14_modified":False}
 (outdir/"promotion.json").write_text(json.dumps(report,indent=2)+"\n")
 print("PASS: exact 2103163 shell promoted to 2103164; controlled base differs only by rebuilt libkodi.so")

def suite(path,count):
 root=ET.parse(path).getroot();cases=root.findall("testcase")
 require(len(cases)==count and all(int(root.get(k,"0"))==0 for k in ("failures","errors","skipped")),"Suite incomplete: "+str(path))
 require(all(c.find(k) is None for c in cases for k in ("failure","error","skipped")),"Suite testcase failed/skipped: "+str(path))
 return len(cases)

def verify(final:Path,run6:Path,native_apk:Path,audit:Path):
 require(final.is_file(),"Final APK missing");require(run6.is_file(),"Run6 APK missing")
 report=json.loads(audit.read_text());require(report["version_code"]==VERSION,"Wrong final versionCode");require(report["version_name"]==NEW,"Wrong final versionName")
 require(report["signer_certificate_sha256"]==CERT,"Permanent signer changed");require(report["apk_sha256"]==sha(final),"Final APK hash mismatch")
 with zipfile.ZipFile(final) as new,zipfile.ZipFile(run6) as old,zipfile.ZipFile(native_apk) as native:
  protected={n for n in old.namelist() if (n.startswith(("assets/","res/")) or n=="resources.arsc")}
  for name in protected:require(new.read(name)==old.read(name),"Protected asset/resource changed: "+name)
  native_names={n for n in old.namelist() if n.startswith("lib/") and not n.endswith("/")}
  require(native_names=={n for n in new.namelist() if n.startswith("lib/") and not n.endswith("/")},"Native inventory changed")
  for name in native_names-{LIB}:require(new.read(name)==old.read(name),"Non-target native library changed: "+name)
  rebuilt=native.read(LIB);require(new.read(LIB)==rebuilt,"Final libkodi.so differs from rebuilt native engine")
  require(b"thread state cleaned while waiting for child threads" in rebuilt,"Native guard string missing")
  require(b"m_threadState != nullptr" not in rebuilt,"Old abort assertion still compiled")
  dex=b"".join(new.read(n) for n in new.namelist() if re.fullmatch(r"classes\d*\.dex",n))
  for token in (b"PLAY IN BACKGROUND",b"MiXplorer",b"MINI_BACKGROUND_START",b"cobra_mini_background_playback",b"CobraVisualTheme"):
   require(token in dex,"2103163 shell contract lost: "+repr(token))
  changed_native=sha_bytes(new.read(LIB))
 result={"build":VERSION,"apk_sha256":sha(final),"signer":CERT,"native_engine_sha256":changed_native,
  "pythoninvoker_assert_removed":True,"pythoninvoker_guard_present":True,"candidate14_untouched":True,
  "run6_assets_resources_preserved":len(protected),"non_target_native_libraries_preserved":len(native_names)-1,
  "physical_device_verified":False}
 Path("audit164/final-verification.json").write_text(json.dumps(result,indent=2)+"\n")
 print("PASS: 2103164 final APK signer/shell/resources/native repair verified")

def deliver():
 inherited=0
 for name,count,folder in [("CobraNavigationUiTest",4,"cobra-regression"),("CobraHealthUiTest",7,"cobra-regression"),("Cobra2103159UiTest",2,"experience"),("ExperienceChooserUiTest",6,"experience")]:
  inherited+=suite(Path("audit159/android")/folder/"test-results"/("TEST-com.projectinfinity.kodi."+name+".xml"),count)
 inherited+=suite("audit164/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualRuntimeTest.xml",17)
 inherited+=suite("audit164/android/runtime/test-results/TEST-com.projectinfinity.kodi.CobraVisualLayoutTest.xml",10)
 targeted=suite("audit164/theme-rotation/test-results/TEST-com.projectinfinity.kodi.Cobra2103162ThemeRotationTest.xml",16)
 behavior=suite("audit164/behavior/test-results/TEST-com.projectinfinity.kodi.Cobra2103163AuditTest.xml",29)
 native=json.loads(Path("engine/pythoninvoker-threadstate-source.json").read_text());require(all(native["checks"].values()),"Native source gate failed")
 final=json.loads(Path("audit164/final-verification.json").read_text())
 result={"build":VERSION,"source_parent":2103163,"locked_baseline":2103162,"candidate14_untouched":True,
  "inherited_android_tests":inherited,"theme_rotation_tests":targeted,"behavioral_tests":behavior,
  "pythoninvoker_source_checks":len(native["checks"]),"native_engine_rebuilt":True,
  "native_fix_upstream":"Kodi PR #27320 / merge 0186f895271d4ce7d240b4e9f40da03b4833539d",
  "device_crash_guard":"CPythonInvoker execute child-thread cleanup recheck",
  "apk_sha256":final["apk_sha256"],"candidate_locked":False,"physical_device_verified":False,
  "status":"TEST CANDIDATE - device crash reproduction/acceptance required"}
 Path("signed164/ACCEPTANCE.json").write_text(json.dumps(result,indent=2)+"\n")
 shutil.copy2("engine/pythoninvoker-threadstate-source.json","signed164/PYTHONINVOKER-NATIVE-REPAIR.json")
 shutil.copy2("audit164/final-verification.json","signed164/2103164-verification.json")
 print("PASS:",inherited+targeted+behavior,"Android tests plus native PythonInvoker gates; 2103164 ready for device acceptance")

if __name__=="__main__":
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
 a=sub.add_parser("promote");a.add_argument("--shell",type=Path,required=True);a.add_argument("--run6",type=Path,required=True);a.add_argument("--native-apk",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
 a=sub.add_parser("verify");a.add_argument("--final",type=Path,required=True);a.add_argument("--run6",type=Path,required=True);a.add_argument("--native-apk",type=Path,required=True);a.add_argument("--audit",type=Path,required=True)
 sub.add_parser("deliver")
 args=p.parse_args()
 if args.cmd=="promote":promote(args.shell,args.run6,args.native_apk,args.out)
 elif args.cmd=="verify":verify(args.final,args.run6,args.native_apk,args.audit)
 else:deliver()
