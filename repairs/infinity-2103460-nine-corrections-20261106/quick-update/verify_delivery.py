"""Verify downloaded genuine add-on ZIPs against exact signed2103460 payloads."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as E
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];FIRST=ROOT/'repairs/infinity-final-closure-2103407'
base=Path(sys.argv[1]);delivery=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(exist_ok=False,parents=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(base)=='226911966c1d27d1246cd0ecfcd864c722df48f9be07167bd4b15ad1e73560af'
assert (delivery/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_bytes()==(FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_bytes()
key=serialization.load_pem_public_key((delivery/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_bytes());key.verify((delivery/'INFINITY-QUICK-UPDATE.v1.sig').read_bytes(),(delivery/'INFINITY-QUICK-UPDATE.v1').read_bytes(),padding.PKCS1v15(),hashes.SHA256())
proof=json.loads((delivery/'BUILD-RECEIPT.json').read_text());assert proof['commandcenter_version']=='0.3.5.61';assert not proof['native_changed']
lines=(delivery/'INFINITY-QUICK-UPDATE.v1').read_text().splitlines();assert lines[:4]==['INFINITY-QUICK-UPDATE/1','base\t2103460','commandcenter\t0.3.5.61','skin\t1.0.5.260']
bound={x.split('\t')[2]:x.split('\t')[1] for x in lines[4:]};assert bound==proof['artifacts']
CC='script.infinity.commandcenter';SKIN='skin.infinity.diggz';ids=(CC,'script.infinity.rails','script.infinity.uirepair','script.infinity.watchedbridge')
with ZipFile(base) as z:
 reference={n.removeprefix('assets/addons/'):hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith(tuple('assets/addons/'+a+'/' for a in (*ids,SKIN))) and not n.endswith('/')}
 result=[]
 for name,want in bound.items():
  path=delivery/name;assert sha(path)==want;is_skin=name.startswith(SKIN);aid=SKIN if is_skin else CC;recover='-recovery.zip' in name
  with ZipFile(path) as zip:
   assert zip.testzip() is None;assert len(zip.namelist())==len(set(zip.namelist()));assert {n.split('/')[0] for n in zip.namelist()}=={aid}
   actual={n:hashlib.sha256(zip.read(n)).hexdigest() for n in zip.namelist()}
   expected={n:h for n,h in reference.items() if n.startswith(aid+'/')};assert set(actual)==set(expected),'NO_EXTRA_OR_MISSING_ADDON_FILES'
   changed=[n for n in actual if actual[n]!=expected[n]]
   permitted=({SKIN+'/addon.xml',SKIN+'/infinity-skin.json',SKIN+'/Infinity-Protected-Manifest.json'} if recover and is_skin else set() if recover else {n for n in proof['changes'] if n.startswith(aid+'/')}|({CC+'/INFINITY-MODULES.v1.sig'} if not is_skin else set()))
   assert set(changed)==permitted,(name,set(changed)^permitted)
   if is_skin:
    manifest=json.loads(zip.read(aid+'/Infinity-Protected-Manifest.json'))
    for rel,h in manifest['protected_files'].items():assert actual[aid+'/'+rel]==h,(name,rel)
    assert len(manifest['protected_files'])==948
   else:
    with tempfile.TemporaryDirectory(dir=out) as temp:
     root=Path(temp)
     for n in z.namelist():
      if n.startswith(tuple('assets/addons/'+a+'/' for a in ids)) and not n.endswith('/'):
       p=root/n.removeprefix('assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
     for n in zip.namelist():
      p=root/n;assert '..' not in p.parts;p.write_bytes(zip.read(n))
     verify=subprocess.run(['/dev/shm/infinity2103460-quick-verifier',str(root.resolve()),str((FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').resolve())],text=True,capture_output=True);assert verify.returncode==0,verify.stderr
   result.append({'file':name,'sha256':want,'addon_id':aid,'version':E.fromstring(zip.read(aid+'/addon.xml')).get('version'),'member_count':len(actual),'protected_unchanged':len(actual)-len(changed),'changed':changed,'skin_948_integrity_hashes':'PASS' if is_skin else None,'native_original_key_module_verifier':'PASS' if not is_skin else None})
report={'status':'PASS_DOWNLOADED_ORIGINAL_KEY_INSTALLER_ZIPS','artifacts':result,'signed_envelope':'PASS_ORIGINAL_PUBLIC_KEY','base_APK_and_native_changed':False,'Cobra_changed':False,'Preview_changed':False,'device_installation':'NOT_RUN','all_nine_complete':False}
(out/'VERIFIED-DOWNLOAD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'artifacts':len(result),'physical_Android':'NOT_RUN'}))
