"""Selected Android emulator-only external ACTION_VIEW/Stop/Back QA.
No shutdown exercise, device/user data, developer-signed release or source changes.
"""
import argparse,hashlib,json,os,re,subprocess,time,zipfile
from pathlib import Path
BASE_SHA="b7e78393ade7e52d8653823a0ad72ae99614a5a8e0b6cdedf5d5d15a9e643400"
PACKAGE="com.projectinfinity.kodi"
SIGNATURE=re.compile(r"^META-INF/(?:MANIFEST\.MF|.*\.(?:RSA|SF|DSA))$")
def sha(p):
 with open(p,"rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def run(cmd,timeout=90,check=True,binary=False):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=not binary,timeout=timeout)
 if check and r.returncode:raise RuntimeError(" ".join(map(str,cmd[:3]))+": "+str(r.stderr)[-1700:])
 return r
def adb(*args,timeout=60,check=True):
 return run(["adb",*args],timeout=timeout,check=check)
def save(path,data):
 Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
def pack(args):
 src=Path(args.baseline); dex=Path(args.dex); out=Path(args.out)
 assert sha(src)==BASE_SHA,"Exact signed 2103445 baseline mismatch"
 assert dex.is_file() and dex.stat().st_size>1000,"Corrected owner DEX missing"
 out.mkdir(parents=True,exist_ok=False)
 unsigned=out/"qa-unsigned.apk"
 with zipfile.ZipFile(src) as old,zipfile.ZipFile(unsigned,"w",allowZip64=True) as new:
  existing={i.filename:i for i in old.infolist()}
  assert "classes3.dex" in existing
  seen=set()
  for info in old.infolist():
   n=info.filename
   if n.startswith("META-INF/") and (SIGNATURE.match(n) or n.startswith("META-INF/com/android")):continue
   assert n not in seen;seen.add(n)
   copy=zipfile.ZipInfo(n,info.date_time)
   copy.compress_type=info.compress_type;copy.external_attr=info.external_attr
   with new.open(copy,"w",force_zip64=info.file_size>=2**31) as w:
    if n=="classes3.dex":w.write(dex.read_bytes())
    else:
     with old.open(info) as reader:
      while True:
       chunk=reader.read(4*1024*1024)
       if not chunk:break
       w.write(chunk)
 with zipfile.ZipFile(src) as old,zipfile.ZipFile(unsigned) as new:
  orig=set(old.namelist());changed=[]
  for n in orig:
   if n not in new.namelist():
    assert n.startswith("META-INF/"),("Unexpected deleted member",n)
    continue
   if hashlib.sha256(old.read(n)).digest()!=hashlib.sha256(new.read(n)).digest():changed.append(n)
  assert changed==["classes3.dex"],("Unauthorized payload changes",changed)
  assert new.read("classes3.dex")==dex.read_bytes()
 key=out/"qa-only.keystore"
 run(["keytool","-genkeypair","-noprompt","-keyalg","RSA","-keysize","2048",
      "-alias","qa-only","-keystore",key,"-storepass","qa-only-pass","-keypass","qa-only-pass",
      "-dname","CN=Disposable emulator QA only","-validity","2"],timeout=45)
 aligned=out/"qa-aligned.apk";signed=out/"qa-DISCARD-DO-NOT-INSTALL-ON-PHONE.apk"
 sdk=Path(args.sdk)
 run([sdk/"zipalign","-P","16","-f","4",unsigned,aligned],timeout=100)
 run([sdk/"apksigner","sign","--ks",key,"--ks-key-alias","qa-only",
      "--ks-pass","pass:qa-only-pass","--key-pass","pass:qa-only-pass",
      "--out",signed,aligned],timeout=100)
 sig=run([sdk/"apksigner","verify","--verbose","--print-certs",signed]).stdout
 assert "Verified using v2 scheme (APK Signature Scheme v2): true" in sig
 assert "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7" not in sig
 save(out/"QA-PACK.json",{"status":"PASS_DISPOSABLE_ONLY","release_candidate":False,
       "original_signed_baseline":BASE_SHA,"corrected_classes3_sha256":sha(dex),
       "qa_apk_sha256":sha(signed),"changed_nonsignature_members":["classes3.dex"],
       "signer":"EPHEMERAL_DEBUG_QA_NOT_ORIGINAL","user_install":"PROHIBITED",
       "no_release_or_locked_pointer_update":True})
 print(signed)
def dump(out,name,report):
 p=out/name;p.mkdir(exist_ok=True)
 for tag,cmd in [
  ("media_session",["shell","dumpsys","media_session"]),
  ("activity",["shell","dumpsys","activity","activities"]),
  ("top",["shell","dumpsys","window","windows"])]:
  r=adb(*cmd,timeout=45,check=False);(p/(tag+".txt")).write_text(r.stdout+r.stderr)
 r=run(["adb","exec-out","screencap","-p"],timeout=25,check=False,binary=True)
 if r.returncode==0 and r.stdout.startswith(b"\x89PNG"): (p/"screen.png").write_bytes(r.stdout)
 ui=adb("shell","uiautomator","dump","/sdcard/infinity-external-qa.xml",timeout=25,check=False)
 xml=adb("shell","cat","/sdcard/infinity-external-qa.xml",timeout=25,check=False).stdout
 (p/"ui.xml").write_text(xml)
 report.setdefault("observations",{})[name]={"screenshot":(p/"screen.png").is_file(),
         "media_session_contains_synthetic_name":bool(re.search(r"(?:QA_A|QA_B)\.mp4",(p/"media_session.txt").read_text(),re.I)),
         "ui_contains_loading":bool(re.search("Loading",xml,re.I))}
def intent(file,out,report):
 uri="file:///sdcard/Movies/"+file
 args=["shell","am","start","-W","-a","android.intent.action.VIEW",
       "-d",uri,"-t","video/mp4","-p",PACKAGE,
       "--grant-read-uri-permission"]
 r=adb(*args,timeout=40,check=False)
 if r.returncode or "Error:" in r.stdout+r.stderr:
  report.setdefault("errors",[]).append({"route":"implicit","file":file,"result":r.stdout+r.stderr})
  args=["shell","am","start","-W","-n",PACKAGE+"/.Splash",
        "-a","android.intent.action.VIEW","-d",uri,"-t","video/mp4",
        "--grant-read-uri-permission"]
  r=adb(*args,timeout=40,check=False)
 report.setdefault("intent_routes",[]).append({"file":file,"output":(r.stdout+r.stderr)[-2500:],"returncode":r.returncode})
 return r.returncode==0 and "Error:" not in (r.stdout+r.stderr)
def play(args):
 out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
 r={"phase":args.phase,"scope":"Selected external local file ACTION_VIEW only; NOT shutdown",
    "real_fold":False,"real_miXplorer_uri":False,"android_runtime_test":True,
    "exact_production_signer":args.phase=="baseline","result":"BLOCKED_UNTIL_ACTUAL_PLAYBACK_OBSERVED"}
 try:
  assert adb("shell","getprop","ro.kernel.qemu").stdout.strip()=="1","Emulator required"
  assert adb("shell","getprop","ro.build.version.sdk").stdout.strip()=="37","API37 required"
  apk=Path(args.apk)
  if args.phase=="baseline":assert sha(apk)==BASE_SHA
  assert not adb("shell","pm","path",PACKAGE,check=False).stdout.strip(),"Requires empty disposable emulator app state"
  r["apk_sha256"]=sha(apk)
  install=adb("install","--no-incremental",apk,timeout=210,check=False)
  (out/"INSTALL.txt").write_text(install.stdout+install.stderr)
  assert install.returncode==0,"Fresh QA install blocked; not a candidate failure"
  adb("shell","mkdir","-p","/sdcard/Movies")
  for f in ["QA_A.mp4","QA_B.mp4"]:
   x=adb("push",str(Path(args.media)/f),"/sdcard/Movies/"+f,timeout=45,check=False)
   assert x.returncode==0,x.stderr
  adb("logcat","-c",check=False)
  assert intent("QA_A.mp4",out,r),"First ACTION_VIEW activity could not launch"
  time.sleep(1)
  assert intent("QA_B.mp4",out,r),"Second ACTION_VIEW activity could not launch"
  time.sleep(15)
  dump(out,"after-rapid-A-B",r)
  r["stop_delivery"]="KEYCODE_MEDIA_STOP (not UI tap)"
  x=adb("shell","input","keyevent","KEYCODE_MEDIA_STOP",timeout=15,check=False)
  r["stop_input_returncode"]=x.returncode
  time.sleep(2);dump(out,"after-stop",r)
  x=adb("shell","input","keyevent","KEYCODE_BACK",timeout=15,check=False)
  r["back_input_returncode"]=x.returncode
  time.sleep(2);dump(out,"after-back",r)
  assert intent("QA_B.mp4",out,r),"Reopen ACTION_VIEW failed"
  time.sleep(10);dump(out,"after-reopen-B",r)
  r["result"]="OBSERVATIONS_CAPTURED_NOT_AUTOMATIC_PLAYBACK_PASS"
 except Exception as e:
  r["result"]="BLOCKED_OR_FAILED_NOT_PASS";r["error"]=str(e)
 finally:
  try:
   r["android_pid"]=adb("shell","pidof",PACKAGE,check=False).stdout.strip()
   l=adb("logcat","-d","-v","threadtime",timeout=60,check=False)
   (out/"LOGCAT.txt").write_text(l.stdout[-2000000:])
   r["fatal_strings"]=len(re.findall(r"FATAL EXCEPTION|Fatal signal|ANR in "+re.escape(PACKAGE),l.stdout,re.I))
  except Exception as e:r["logcat_error"]=str(e)
  save(out/"RESULT.json",r)
 if r["result"].startswith("BLOCKED"):raise SystemExit(1)
if __name__=="__main__":
 p=argparse.ArgumentParser()
 s=p.add_subparsers(dest="mode",required=True)
 b=s.add_parser("pack")
 for k in ("baseline","dex","sdk","out"):b.add_argument("--"+k,required=True)
 x=s.add_parser("play")
 for k in ("apk","media","out"):x.add_argument("--"+k,required=True)
 x.add_argument("--phase",choices=("baseline","candidate"),required=True)
 a=p.parse_args()
 (pack if a.mode=="pack" else play)(a)
