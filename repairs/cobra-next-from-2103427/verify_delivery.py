"""Final APK/owner identity and original-key install-over verification only."""
import argparse,hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'dual-experience-isolation-2103420'))
from inventory import file_sha,canonical,digest,load,save,SIGNATURE,CERT_SHA,validate_names
from component_bundles import read_bundle
from release_gate import normalize_manifest,require
REPO=HERE.parents[1];ISO=HERE.parent/'dual-experience-isolation-2103420'
def run(args):return subprocess.check_output(list(map(str,args)),text=True)
def verify(baseline,signed,bundles,sdk):
 scope=load(HERE/'SCOPE.json');receipt=load(signed/'BUILD-RECEIPT.json');authority=load(signed/'release-authority.json')
 require(authority==load(ISO/'release-authority.json'),'EXACT_AUTHORITY')
 require(receipt['registry_sha256']==digest(canonical(authority)),'AUTHORITY_BINDING')
 require(receipt['versionCode']==2103428 and receipt['source']==os.environ.get('GITHUB_SHA',receipt['source']),'SOURCE_VERSION')
 require(file_sha(baseline)==scope['baseline_apk_sha256'],'EXACT_BASELINE')
 apk=signed/'Infinity-2103428-Combined-Original-Signer.apk';require(file_sha(apk)==receipt['signed_apk_sha256'],'SIGNED_HASH')
 signature=run([sdk/'apksigner','verify','--verbose','--print-certs',apk]);(signed/'ORIGINAL-SIGNATURE.txt').write_text(signature)
 require(re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)',signature)==[CERT_SHA],'ORIGINAL_CERTIFICATE')
 for scheme in ('v1','v2','v3'):require(re.search('Verified using '+scheme+r' scheme.*: true',signature)!=None,'SIGNATURE:'+scheme)
 run([sdk/'zipalign','-c','-P','16','4',apk])
 changed=set();native={};dex={};component_sha={}
 metadata='assets/experience-component-updates.properties'
 with ZipFile(baseline) as old,ZipFile(apk) as new:
  require(set(validate_names(old))-SIGNATURE==set(validate_names(new))-SIGNATURE,'EXACT_APK_MEMBER_SET')
  normalized,previous=normalize_manifest(old.read('AndroidManifest.xml'))
  require(previous==2103427 and normalize_manifest(new.read('AndroidManifest.xml'))==(normalized,2103428),'MANIFEST_VERSION_ONLY')
  for name in sorted(set(new.namelist())-SIGNATURE-{'AndroidManifest.xml'}):
   with old.open(name) as a,new.open(name) as b:before,after=hashlib.file_digest(a,'sha256').hexdigest(),hashlib.file_digest(b,'sha256').hexdigest()
   if before!=after:require(name in {'classes.dex','classes4.dex','classes5.dex',metadata},'FROZEN_APK_MEMBER:'+name);changed.add(name)
   if name.endswith('.so'):native[name]=after
   if re.fullmatch(r'classes\d*\.dex',name):dex[name]=after
  require({'classes.dex','classes4.dex',metadata}<=changed,'REQUIRED_CHANGES_PRESENT')
  require(new.read(metadata)==b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103428\n','VERSION_LABELS')
  bundle_dex=set()
  for owner,row in authority['bundle_catalog']['bundles'].items():
   meta=read_bundle(bundles/row['file'],row);component_sha[row['file']]=row['sha256']
   with ZipFile(bundles/row['file']) as bundle:
    for name in meta['members']:
     a,b=bundle.read('payload/'+name),new.read(name)
     if name=='AndroidManifest.xml':a,b=normalize_manifest(a)[0],normalize_manifest(b)[0]
     require(a==b,'COMPONENT_APK_MISMATCH:'+name)
    bundle_dex.update(meta['dex'].values())
  require(set(dex.values())==bundle_dex and len(dex)==len(bundle_dex),'EXACT_COMPONENT_DEX')
  # The frozen authenticated Infinity manifest and its detached signature are
  # unchanged, and the original-key signature still verifies independently.
  with tempfile.TemporaryDirectory() as temporary:
   temp=Path(temporary)
   for leaf in ('INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig'):
    name='assets/addons/script.infinity.commandcenter/'+leaf;require(old.read(name)==new.read(name),'FROZEN_AUTHENTICATED_INFINITY')
    (temp/leaf).write_bytes(new.read(name))
   run(['openssl','dgst','-sha256','-verify',REPO/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',temp/'INFINITY-MODULES.v1.sig',temp/'INFINITY-MODULES.v1'])
 original=json.loads(run(['git','show',scope['baseline_source']+':repairs/dual-experience-isolation-2103420/release-authority.json']))
 for owner in ('INFINITY','MINIMAL_ANDROID_CONTRACT'):
  row=authority['bundle_catalog']['bundles'][owner];require(row==original['bundle_catalog']['bundles'][owner],'FROZEN_OWNER_VECTOR:'+owner)
  require(row['sha256']==scope['frozen_owner_zips'][owner],'FROZEN_ZIP:'+owner)
 require(authority['protected_contract']==original['protected_contract'],'FROZEN_PROTECTED_CONTRACT')
 report=dict(status='SIGNED_INSTALL_OVER_CANDIDATE_VERIFIED',versionCode=2103428,source=receipt['source'],build_run=os.environ.get('GITHUB_RUN_ID'),
  package='com.projectinfinity.kodi',certificate_sha256=CERT_SHA,signature_schemes=['v1','v2','v3'],apk_sha256=file_sha(apk),apk_bytes=apk.stat().st_size,
  component_sha256=component_sha,changed_APK_members=sorted(changed),manifest_change='versionCode only',unchanged_native_libraries=len(native),
  Infinity='EXACT_2103427_COMPONENT_ZIP',shared_contract='EXACT_ORIGINAL_COMPONENT_ZIP',chooser='ONE_LITERAL_AND_AUTHENTICATED_COBRA_VERSION_METADATA',
  shutdown_sources_and_binaries='UNCHANGED',shutdown_tests='NOT_RUN',actual_device_install='NOT_RUN',physical_Fold='USER_ACCEPTANCE_PENDING',accepted_pointer_updated=False)
 save(signed/'DELIVERY-VERIFICATION.json',report)
 (signed/'SHA256SUMS').write_text(file_sha(apk)+'  '+apk.name+'\n')
 (bundles/'SHA256SUMS').write_text(''.join(pin+'  '+name+'\n' for name,pin in sorted(component_sha.items())))
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('baseline','signed','bundles','sdk'):p.add_argument('--'+n,type=Path,required=True)
 verify(**vars(p.parse_args()))
