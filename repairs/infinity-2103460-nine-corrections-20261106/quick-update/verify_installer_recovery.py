"""Original 2103460 Java installer with actual original-key module payloads.
Disposable host Android-filesystem adapter only; no app shutdown or user profile.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];FIRST=ROOT/'repairs/infinity-final-closure-2103407';sys.path.insert(0,str(FIRST))
import module_dex
IDS=('script.infinity.commandcenter','script.infinity.rails','script.infinity.uirepair','script.infinity.watchedbridge');CC=IDS[0]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(p):return {str(x.relative_to(p)):digest(x) for x in p.rglob('*') if x.is_file()}
def main(base,updates,out):
 out.mkdir(exist_ok=False,parents=True);results=[]
 with tempfile.TemporaryDirectory(prefix='infinity-quick-recovery-audit-') as temp:
  temp=Path(temp);assets=temp/'assets';addons=assets/'addons';addons.mkdir(parents=True)
  with ZipFile(base) as z:
   for n in z.namelist():
    if n.startswith(tuple('assets/addons/'+a+'/' for a in IDS)) and not n.endswith('/'):
     p=addons/n.removeprefix('assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
  src=temp/'InfinityInstalledCheckpointInstaller.java';src.write_text(module_dex.source());classes=temp/'classes';classes.mkdir()
  subprocess.run(['javac','--release','8','-g:none','-d',str(classes),str(src),*map(str,(FIRST/'host-java').rglob('*.java'))],check=True)
  recovery=next(updates.glob(CC+'-*-recovery.zip'))
  with ZipFile(recovery) as z: recovery_files={n:z.read(n) for n in z.namelist()}
  archive=next(updates.glob(CC+'-*-corrective.zip'))
  with ZipFile(archive) as z: candidate={n:z.read(n) for n in z.namelist()}
  def fixture(label):
   storage=temp/label;shutil.copytree(addons,storage/'.kodi/addons');sentinel=storage/'.kodi/userdata/unchanged-data';sentinel.parent.mkdir();sentinel.write_bytes(b'private profiles and databases are never inputs');return storage,sentinel
  def call(storage):return subprocess.run(['java','-cp',str(classes),'com.projectinfinity.kodi.Main',str(storage),str(assets)],text=True,capture_output=True)
  storage,sentinel=fixture('baseline');r=call(storage);assert r.returncode==0,r.stderr;results.append({'case':'original_complete_generation','result':'PASS','version':r.stdout.strip()})
  storage,sentinel=fixture('full-quick-update')
  for n,raw in candidate.items():(storage/'.kodi/addons'/n).write_bytes(raw)
  r=call(storage);assert r.returncode==0,r.stderr;results.append({'case':'complete_same_version_original_key_quick_update_cold_start','result':'PASS','version':r.stdout.strip()})
  def restore_zip_and_verify(storage,sentinel,label):
   saved=sentinel.read_bytes()
   # Filesystem transport fixture for the source-traced native ZIP installer;
   # this is not a claim of executing the Android GUI or C++ copy job.
   for n,raw in recovery_files.items():(storage/'.kodi/addons'/n).write_bytes(raw)
   r=call(storage);assert r.returncode==0,r.stderr;assert sentinel.read_bytes()==saved
   assert all((storage/'.kodi/addons'/n).read_bytes()==raw for n,raw in recovery_files.items())
   results.append({'case':label,'result':'PASS_HOST_ZIP_RESTORE_AND_REAL_JAVA_VERIFICATION','native_GUI_executed':False,'userdata_sentinel_preserved':True,'version':r.stdout.strip()})
  storage,sentinel=fixture('manifest-only-interruption');marker=storage/'.kodi/addons'/CC/'INFINITY-MODULES.v1';marker.write_bytes(candidate[CC+'/INFINITY-MODULES.v1']);before=snap(storage);r=call(storage)
  assert r.returncode!=0,'Unexpected partial pair accepted';assert snap(storage)==before,'Protected installer must not write unknown generation'
  results.append({'case':'interrupted_zip_new_manifest_old_signature_cold_start','result':'BLOCKED_AS_DESIGNED','error':r.stderr.strip(),'source_and_userdata_unchanged':True})
  restore_zip_and_verify(storage,sentinel,'native_GUI_transport_fixture_recovers_manifest_pair_interruption')
  storage,sentinel=fixture('code-only-interruption');(storage/'.kodi/addons'/CC/'default.py').write_bytes(candidate[CC+'/default.py']);before=snap(storage);r=call(storage)
  assert r.returncode!=0;assert snap(storage)==before
  results.append({'case':'interrupted_zip_new_code_old_manifest_cold_start','result':'BLOCKED_AS_DESIGNED','error':r.stderr.strip(),'source_and_userdata_unchanged':True})
  restore_zip_and_verify(storage,sentinel,'native_GUI_transport_fixture_recovers_code_only_interruption')
 report={'status':'PASS_HOST_RECOVERY_WITH_SOURCE_TRACED_NATIVE_GUI_ANDROID_PENDING','audit_completed':True,'tests':results,'keys_accessed':False,'baseline_version':2103460,'commandcenter_version':'0.3.5.61','physical_Android':'NOT_RUN','user_data_accessed':False,'production_installer_changed':False,'interpretation':'APK auto-repair correctly rejects partial standalone generations. Main caller records this refusal and continues native entry; native AddonBrowser recovery route is independent of Command Center. After recovery ZIP filesystem transport, the real unchanged Java installer accepts the restored original-signed generation and preserves the user-data sentinel. Android GUI/file-copy/service execution remain pending.'}
 (out/'INSTALLER-RECOVERY-AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'audit_completed':True,'compatibility':report['status'],'Android':'NOT_RUN'}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--updates',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.baseline.resolve(),a.updates.resolve(),a.out.resolve())
