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
CC='script.infinity.commandcenter';SKIN='skin.infinity.diggz';VERSION='0.3.5.61';SKIN_VERSION='1.0.5.268'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args,env=None):
 p=subprocess.run(list(map(str,args)),text=True,capture_output=True,env=env)
 if p.returncode:raise RuntimeError('Command failed: '+str(args[0])+'\n'+p.stdout[-3000:]+p.stderr[-3000:])
 return p.stdout
def save(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def preflight(apk,out):
 # Same owner-gated workflow and signing implementation; forward from the
 # authenticated physical-pass262 addon payload without repackaging APK462.
 from importlib.machinery import SourceFileLoader
 helper=SourceFileLoader('infinity_fold_preflight',str(HERE.parent/'fold-regressions/package_preflight.py')).load_module()
 return helper.prepare(sys.modules[__name__],apk,out)
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
  for aid,version,source_root,suffix in ((CC,VERSION,addons,'corrective'),(SKIN,SKIN_VERSION,addons,'corrective'),(CC,VERSION,out/'recovery-addons','recovery'),(SKIN,'1.0.5.269',out/'recovery-addons','recovery')):
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
 # Exercise the unchanged actual Java installer on disposable host profiles,
 # including partial-pair refusal and exact current-generation recovery.
 from importlib.machinery import SourceFileLoader
 recovery_audit=SourceFileLoader('infinity_fold_recovery_audit',str(HERE.parent/'fold-regressions/verify_recovery.py')).load_module()
 recovery_audit.audit(ROOT,Path(proof['seed_apk_path']),publish,out,out/'recovery-audit')
 # No key, temporary classes, extracted user data, or raw native engine enters artifacts.
 print('PASS original signatures and complete installable add-on ZIP structures; Android acceptance NOT RUN')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=('preflight','sign'));p.add_argument('--baseline',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 a.out=a.out.resolve()
 if a.operation=='preflight':preflight(a.baseline,a.out)
 else:sign(a.out)
