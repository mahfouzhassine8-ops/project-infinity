"""Original-key add-on installers for exact signed2103460; never an APK producer."""
import argparse,base64,hashlib,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
FIRST=ROOT/'repairs/infinity-final-closure-2103407';sys.path.insert(0,str(FIRST))
import module_bundle
BASE='226911966c1d27d1246cd0ecfcd864c722df48f9be07167bd4b15ad1e73560af'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
CC='script.infinity.commandcenter';SKIN='skin.infinity.diggz';VERSION='0.3.5.61';SKIN_VERSION='1.0.5.262'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args,env=None):
 p=subprocess.run(list(map(str,args)),text=True,capture_output=True,env=env)
 if p.returncode:raise RuntimeError('Command failed: '+str(args[0])+'\n'+p.stdout[-3000:]+p.stderr[-3000:])
 return p.stdout
def save(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def preflight(apk,out):
 assert sha(apk)==BASE,'EXACT_SIGNED2103460_REQUIRED'
 branch=run('git','branch','--show-current').strip();assert branch=='work/infinity-2103460-nine-corrections-20261106'
 changed=run('git','diff','--name-only','ed5f797618b570e837d83668ba355a4396a8d4a8','HEAD').splitlines()
 assert all(n.startswith('repairs/infinity-2103460-nine-corrections-20261106/') or n in ('.github/workflows/infinity-combined-release.yml','.github/workflows/infinity-six-navigation-arm64.yml','repairs/dual-experience-isolation-2103420/signer-policy.json','repairs/dual-experience-isolation-2103420/release_gate.py') or n in json.loads((HERE.parent/'SOURCE-INVENTORY.json').read_text())['changed_source_files'] for n in changed),'UNRELATED_SOURCE_CHANGE'
 assert run('git','status','--porcelain','--untracked-files=no').strip()=='','COMMITTED_REVIEWED_SOURCE_REQUIRED'
 assert not out.exists(),'fresh output required'
 out.mkdir(parents=True);addons=out/'addons';addons.mkdir();inventory=json.loads((HERE.parent/'SOURCE-INVENTORY.json').read_text());changes={};protected={}
 with ZipFile(apk) as z:
  assert len(z.namelist())==len(set(z.namelist()))
  for n in z.namelist():
   if n.startswith(tuple('assets/addons/'+a+'/' for a in (*module_bundle.IDS,SKIN))) and not n.endswith('/'):
    raw=z.read(n);p=addons/n.removeprefix('assets/addons/');assert '..' not in p.parts;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);protected[n.removeprefix('assets/addons/')]=hashlib.sha256(raw).hexdigest()
  recovery=out/'recovery-addons';recovery.mkdir()
  for aid in (CC,SKIN):shutil.copytree(addons/aid,recovery/aid)
  for source,row in inventory['changed_source_files'].items():
   rel=source.split('/overlay/assets/addons/',1)[1];assert rel.startswith((CC+'/',SKIN+'/'))
   assert protected[rel]==row['before_sha256'],rel
   assert sha(ROOT/source)==row['candidate_sha256'],source
   (addons/rel).write_bytes((ROOT/source).read_bytes());changes[rel]=row['candidate_sha256']
 assert len(changes)==14 and inventory['Command_Center_version']=='0.3.5.61 unchanged'
 assert ET.parse(addons/CC/'addon.xml').getroot().get('version')==VERSION
 # Only skin release/integrity metadata changes; Command Center identity remains exact.
 xml=addons/SKIN/'addon.xml';raw=xml.read_bytes();assert b'version="1.0.5.258"' in raw
 xml.write_bytes(raw.replace(b'version="1.0.5.258"',b'version="1.0.5.262"',1));changes[SKIN+'/addon.xml']=sha(xml)
 for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
  f=addons/SKIN/leaf;d=json.loads(f.read_text());d['candidate']=262;d['candidate_locked']=False
  if 'physical_device_verified' in d:d['physical_device_verified']=False
  for k in ('version','candidate_version','skin_version'):
   if k in d:d[k]=SKIN_VERSION
  if 'protected_files' in d:
   for name,value in changes.items():
    if name.startswith(SKIN+'/'):d['protected_files'][name[len(SKIN)+1:]]=value
   assert len(d['protected_files'])==948
  save(f,d);changes[SKIN+'/'+leaf]=sha(f)
 # Forward skin recovery: original functional payload, higher skin version.
 recovery_xml=recovery/SKIN/'addon.xml';recovery_xml.write_bytes(recovery_xml.read_bytes().replace(b'version="1.0.5.258"',b'version="1.0.5.263"',1))
 for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
  f=recovery/SKIN/leaf;d=json.loads(f.read_text());d['candidate']=263;d['candidate_locked']=False
  for k in ('version','candidate_version','skin_version'):
   if k in d:d[k]='1.0.5.263'
  if 'physical_device_verified' in d:d['physical_device_verified']=False
  if 'protected_files' in d:
   d['protected_files']['addon.xml']=sha(recovery_xml)
   d['protected_files']['infinity-skin.json']=sha(recovery/SKIN/'infinity-skin.json')
  save(f,d)
 for skin_root in (addons/SKIN,recovery/SKIN):
  protected_skin=json.loads((skin_root/'Infinity-Protected-Manifest.json').read_text())['protected_files']
  assert len(protected_skin)==948
  for rel,want in protected_skin.items():assert sha(skin_root/rel)==want,'SKIN_INTEGRITY_BEFORE_KEYS:'+rel
 old_marker=(addons/CC/module_bundle.MANIFEST).read_bytes();payload,files=module_bundle.build(addons_for_build(addons,out))
 assert len(files)==78 and payload.startswith(('INFINITY-MODULES/1\npackage\t'+VERSION+'\n').encode())
 marker=addons/CC/module_bundle.MANIFEST;marker.write_bytes(payload);Path(str(marker)+'.sig').unlink();changes[CC+'/'+module_bundle.MANIFEST]=sha(marker)
 for rel,want in protected.items():
  if rel.startswith((CC+'/',SKIN+'/')) and rel not in {SKIN+'/addon.xml',SKIN+'/infinity-skin.json',SKIN+'/Infinity-Protected-Manifest.json'}:
   assert sha(recovery/rel)==want,'RECOVERY_FUNCTIONAL_DIFFERENCE:'+rel
 # Full reference inventory; every unrelated existing add-on byte must match.
 for rel,want in protected.items():
  if rel not in changes and rel!=CC+'/'+module_bundle.MANIFEST+'.sig':assert sha(addons/rel)==want,rel
 for path in (addons/SKIN).rglob('*.xml'):ET.parse(path)
 for leaf in ('default.py','library_navigation.py'):compile((addons/CC/leaf).read_bytes(),leaf,'exec')
 save(out/'PREFLIGHT.json',dict(status='PASS_EXACT2103460_ADDON_SOURCE_AND_METADATA',baseline_sha256=BASE,commandcenter_version=VERSION,skin_version=SKIN_VERSION,source=run('git','rev-parse','HEAD').strip(),changes=changes,protected=protected,module_file_count=78,old_module_manifest_sha256=hashlib.sha256(old_marker).hexdigest(),Android='NOT_RUN',all_nine_complete=False,Downloads_native_required_sha256=json.loads((HERE.parent/'native-packaging/ENGINE-INPUT.json').read_text())['native_sha256']))
 print('PASS exact signed2103460, 14 authorized source changes, original CC identity and complete module source set')
def addons_for_build(addons,out):
 root=out/'module-root'
 if root.exists():shutil.rmtree(root)
 root.mkdir()
 for aid in module_bundle.IDS:shutil.copytree(addons/aid,root/aid)
 return root

def sign(out):
 proof=json.loads((out/'PREFLIGHT.json').read_text());assert proof['status']=='PASS_EXACT2103460_ADDON_SOURCE_AND_METADATA'
 assert proof['source']==run('git','rev-parse','HEAD').strip(),'SOURCE_CHANGED'
 addons=out/'addons';module_root=addons_for_build(addons,out)
 marker=addons/CC/module_bundle.MANIFEST;assert module_bundle.build(module_root)[0]==marker.read_bytes()
 # Full source/hash gate again immediately before key access.
 for rel,want in proof['protected'].items():
  if rel==CC+'/'+module_bundle.MANIFEST+'.sig':continue
  assert sha(addons/rel)==proof['changes'].get(rel,want),rel
 verifier=out/'verify-modules';run('g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',FIRST/'verify_module_bundle.cpp',FIRST/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier)
 from importlib.machinery import SourceFileLoader
 # Preserve the existing sole-original-key policy; do not create/enable a new workflow.
 sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
 from signer_policy import check
 check(json.loads((ROOT/'repairs/dual-experience-isolation-2103420/signer-policy.json').read_text()))
 env={n:os.environ[n] for n in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
 publish=out/'publish';publish.mkdir()
 with tempfile.TemporaryDirectory(prefix='infinity-quick-original-key-') as temp:
  temp=Path(temp);key=temp/'original.jks';key.touch(mode=0o600);key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));classes=temp/'classes';classes.mkdir()
  run('javac','--release','8','-g:none','-d',classes,FIRST/'SignInfinityModules.java',HERE/'SignInfinityQuickUpdate.java')
  text=run('java','-cp',classes,'SignInfinityModules',key,marker,env=env)
  shutil.copyfile(Path(str(marker)+'.sig'),module_root/CC/(module_bundle.MANIFEST+'.sig'))
  text+=run(verifier,module_root,FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem');(publish/'MODULE-AUTHENTICATION.txt').write_text(text)
  # Normal Kodi add-on ZIP shape: exactly one addon root, complete existing resources.
  ziprows=[]
  for aid,version,source_root,suffix in ((CC,VERSION,addons,'corrective'),(SKIN,SKIN_VERSION,addons,'corrective'),(CC,VERSION,out/'recovery-addons','recovery'),(SKIN,'1.0.5.263',out/'recovery-addons','recovery')):
   name=aid+'-'+version+'-2103460-'+suffix+'.zip';dest=publish/name
   with ZipFile(dest,'w',compression=ZIP_DEFLATED,compresslevel=9) as z:
    for f in sorted((source_root/aid).rglob('*')):
     if f.is_file():z.write(f,str(f.relative_to(source_root)))
   with ZipFile(dest) as z:
    assert z.testzip() is None
    assert {n.split('/')[0] for n in z.namelist()}=={aid}
    assert ET.fromstring(z.read(aid+'/addon.xml')).get('version')==version
   ziprows.append((name,sha(dest)))
  envelope=('INFINITY-QUICK-UPDATE/1\nbase\t2103460\ncommandcenter\t'+VERSION+'\nskin\t'+SKIN_VERSION+'\n'+''.join('artifact\t'+h+'\t'+n+'\n' for n,h in ziprows)).encode('ascii')
  signed=publish/'INFINITY-QUICK-UPDATE.v1';signed.write_bytes(envelope)
  text=run('java','-cp',classes,'SignInfinityQuickUpdate',key,signed,env=env);(publish/'ENVELOPE-AUTHENTICATION.txt').write_text(text)
 run('openssl','dgst','-sha256','-verify',FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',str(signed)+'.sig',signed)
 shutil.copyfile(FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem',publish/'ORIGINAL-INFINITY-PUBLIC-KEY.pem')
 (publish/'SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in ziprows))
 proof['status']='PASS_ORIGINAL_KEY_COMPLETE_ADDON_INSTALLER_ZIPS';proof['artifacts']={n:h for n,h in ziprows};proof['certificate_sha256']=CERT;proof['native_changed']=False;proof['all_nine_complete']=False;proof['Android_install_and_service_restart']='NOT_RUN'
 save(publish/'BUILD-RECEIPT.json',proof)
 # No key, temporary classes, extracted user data, or raw native engine enters artifacts.
 print('PASS original signatures and complete installable add-on ZIP structures; Android acceptance NOT RUN')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=('preflight','sign'));p.add_argument('--baseline',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 a.out=a.out.resolve()
 if a.operation=='preflight':preflight(a.baseline,a.out)
 else:sign(a.out)
