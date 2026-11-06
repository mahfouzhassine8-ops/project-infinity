"""Read-only actual signed APK verifier: official SDK35 and streaming full-member comparison."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
from inventory import SIGNATURE,validate_names
from release_gate import normalize_manifest
BASE='226911966c1d27d1246cd0ecfcd864c722df48f9be07167bd4b15ad1e73560af';CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def member(z,n):
 with z.open(n) as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(base,candidate,plan,jar,out):
 out.mkdir(exist_ok=False,parents=True);p=json.loads(plan.read_text());version=p['versionCode'];assert version in (2103462,2103463) and sha(base)==BASE
 assert sha(jar)==json.loads((HERE/'VERIFIER-TOOL.json').read_text())['jar_sha256']
 r=subprocess.run(['java','-jar',str(jar),'verify','--verbose','--print-certs',str(candidate)],capture_output=True,text=True);(out/'SIGNATURE.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
 assert re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',r.stdout)==[CERT];assert 'Number of signers: 1' in r.stdout
 for scheme in ('v1','v2','v3'):assert re.search(r'Verified using '+scheme+r' scheme .*: true',r.stdout)
 expected=p['expected_members'];allowed={'AndroidManifest.xml','assets/experience-component-updates.properties'}|({'lib/arm64-v8a/libkodi.so'} if version==2103462 else set());changed=[];signatures=[];hashes={}
 with ZipFile(base) as a,ZipFile(candidate) as b:
  old=set(validate_names(a));new=set(validate_names(b));assert old-SIGNATURE==new-SIGNATURE and old&SIGNATURE==new&SIGNATURE
  for n in sorted(old|new):
   x,y=member(a,n),member(b,n);hashes[n]={'before':x,'after':y}
   if x==y:continue
   if n in SIGNATURE:signatures.append(n);continue
   assert n in allowed,'UNAUTHORIZED_MEMBER:'+n
   if n=='AndroidManifest.xml':assert normalize_manifest(b.read(n))==(normalize_manifest(a.read(n))[0],version)
   else:assert y==expected[n],'EXPECTED_EXACT_PAYLOAD:'+n
   changed.append(n)
  assert set(changed)==allowed
  dex=[n for n in old if re.fullmatch(r'classes\d*\.dex',n)];assert len(dex)==5 and all(hashes[n]['before']==hashes[n]['after'] for n in dex)
  libs=[n for n in old if n.startswith('lib/') and n.endswith('.so')]
 report={'status':'PASS_DOWNLOADED_ACTUAL_APK_ORIGINAL_CERT_AND_EXACT_PAYLOAD','versionCode':version,'apk_sha256':sha(candidate),'apk_bytes':candidate.stat().st_size,'certificate_sha256':CERT,'package':'com.projectinfinity.kodi unchanged: all manifest bytes except typed versionCode identical','signature_schemes':['v1','v2','v3'],'changed_payload_members':changed,'regenerated_signature_members':signatures,'protected_existing_payload_members':len(old-SIGNATURE)-len(changed),'all_five_DEX_unchanged':True,'native_libraries_total':len(libs),'native_libraries_unchanged':len(libs)-(1 if version==2103462 else 0),'all_addons_and_skin_unchanged_in_APK':True,'Cobra_and_Preview_unchanged':True,'all_nine_complete':False,'Android_installation_and_runtime':'NOT_RUN','physical_Fold':'PENDING','user_data_accessed':False}
 (out/'VERIFIED-SIGNED-APK.json').write_text(json.dumps(report,indent=2)+'\n');(out/'ALL-APK-MEMBER-HASHES.json').write_text(json.dumps(hashes,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('base','candidate','plan','jar','out'):p.add_argument('--'+n,type=Path,required=True)
 main(**vars(p.parse_args()))
