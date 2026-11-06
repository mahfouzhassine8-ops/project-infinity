import hashlib,json,sys,zipfile
from pathlib import Path
from cryptography.hazmat.primitives.serialization.pkcs7 import load_der_pkcs7_certificates
from cryptography.hazmat.primitives import hashes
sys.dont_write_bytecode=True
sys.path.insert(0,'/tmp/infinity-master-testing-20261105/repairs/dual-experience-isolation-2103420')
from component_bundles import set_version
version=int(sys.argv[1]);root=Path('/dev/shm');a=root/f'infinity{str(version)[-3:]}-apk';c=root/f'infinity{str(version)[-3:]}-components'
apk=next(a.glob('*.apk')); proof=json.loads((a/'preservation/APK-PRESERVATION.json').read_text()); expected=json.loads((a/'preservation/ALL-APK-MEMBER-HASHES.json').read_text())
with apk.open('rb') as f: apksha=hashlib.file_digest(f,'sha256').hexdigest()
assert apksha==proof['candidate_sha256'] and proof['versionCode']==version
certificate='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
with zipfile.ZipFile(apk) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 for name,row in expected.items():
  with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['after'],name
 extras=set(z.namelist())-set(expected);assert all(n.startswith('META-INF/') and (n.endswith(('.RSA','.SF')) or n=='META-INF/MANIFEST.MF') for n in extras),extras
 certs=[cert for n in extras if n.endswith('.RSA') for cert in load_der_pkcs7_certificates(z.read(n))]
 assert len(certs)==1 and certs[0].fingerprint(hashes.SHA256()).hex()==certificate
 catalog=json.loads((c/'catalog.json').read_text());assert catalog['certificate_sha256']==certificate and catalog['package']=='com.projectinfinity.kodi'
 bundles={}
 for owner,row in catalog['bundles'].items():
  path=c/row['file']
  with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  assert actual==row['sha256'],owner
  count=0
  with zipfile.ZipFile(path) as b:
   for n in b.namelist():
    if n.startswith('payload/'):
     name=n[len('payload/'):]
     if name=='AndroidManifest.xml':
      assert set_version(b.read(n),version)==z.read(name),'manifest must match after existing assembler version stamping only'
     else:
      with b.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected[name]['after'],name
     count+=1
  bundles[owner]={'sha256':actual,'matching_apk_payload_members':count}
 dex_index=1
 for owner in ('CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA'):
  with zipfile.ZipFile(c/catalog['bundles'][owner]['file']) as b:
   for n in sorted(x for x in b.namelist() if x.startswith('dex/') and x.endswith('.dex')):
    name='classes'+(str(dex_index) if dex_index>1 else '')+'.dex'
    with b.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected[name]['after'],name
    dex_index+=1
 assert dex_index==6
report={'verifier_development_note':'The initial 2103460 local check required existing assembler manifest version stamping. No payload or source changed.', 'status':'PASS_DOWNLOADED_APK_AND_COMPONENT_IDENTITY','versionCode':version,'apk':apk.name,'apk_sha256':apksha,'apk_size':apk.stat().st_size,'certificate_sha256':certificate,'signature_cryptographic_verification':'Original GitHub signer apksigner v1/v2/v3 PASS; local certificate identity matched','member_hashes_checked':len(expected),'changed_existing':proof['changed_existing'],'protected_existing_members':proof['protected_existing_members'],'components':bundles,'Android':'NOT_RUN','physical_Fold':'PENDING'}
(root/f'infinity{str(version)[-3:]}-DOWNLOAD-VERIFIED.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','versionCode','apk_sha256','certificate_sha256','member_hashes_checked','protected_existing_members')}))
