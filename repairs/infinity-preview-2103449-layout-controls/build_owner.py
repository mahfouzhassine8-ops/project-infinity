"""Compile Preview presentation only over exact signed449 component definitions."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
H=Path(__file__).resolve().parent;R=H.parents[1];OLD=R/'repairs/infinity-2103445-standalone-external-player'
sys.path[:0]=[str(R/'repairs/dual-experience-isolation-2103420'),str(OLD)]
from inventory import file_sha,save,load
from compile_runtime import ANDROID_SHA,D8_SHA
from build_owner import classes,methods
BASE='dd7bd790e7adc3cfadccb9743c9b38b49e8e7b11'
FAMILIES=('InfinityExternalPlayerActivity','InfinityPreviewChrome')
def allowed(name):return any(name.startswith('Lcom/projectinfinity/kodi/'+n+'$') or name=='Lcom/projectinfinity/kodi/'+n+';' for n in FAMILIES)
def run(*a):subprocess.run(list(map(str,a)),check=True)
def build(out,bundles):
 out=out.resolve();out.mkdir(parents=True)
 tools=Path(os.environ.get('CARDS_TOOLS_ROOT','/workspace/cobra-evidence/tools'));jars=tools/'receipt-evidence/tool-jars';android=tools/'receipt-evidence/android-34.jar';d8=tools/'d8.jar'
 assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
 assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(R/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
 authority=json.loads(subprocess.check_output(['git','show',BASE+':repairs/dual-experience-isolation-2103420/release-authority.json']))
 for owner,row in authority['bundle_catalog']['bundles'].items():assert file_sha(bundles/row['file'])==row['sha256']
 with ZipFile(bundles/'INFINITY.zip') as z:
  metadata=json.loads(z.read('component.json'));(out/'original.dex').write_bytes(z.read('dex/part-0.dex'))
 run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',out/'original.dex','-o',out/'original')
 original=classes(out/'original');before={n:p.read_text() for n,p in original.items()}
 assert set(original)=={n[6:] for n in metadata['payload'] if n.startswith('class:')}
 for n,p in original.items():assert file_sha(p)==metadata['payload']['class:'+n]['sha256']
 compiled=out/'compiled';compiled.mkdir();sources=sorted((OLD/'runtime').glob('*.java'))
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',android,'-d',compiled,*sources)
 with ZipFile(out/'feature.jar','w',ZIP_DEFLATED) as z:
  for p in sorted(compiled.rglob('*.class')):z.write(p,p.relative_to(compiled))
 generated=out/'generated';generated.mkdir()
 run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',generated,out/'feature.jar')
 run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',generated/'classes.dex','-o',out/'new-smali')
 additions=classes(out/'new-smali');edited=out/'edited';shutil.copytree(out/'original',edited)
 for n in original:
  if allowed(n):(edited/(n[1:-1]+'.smali')).unlink()
 for n,p in additions.items():
  if allowed(n):
   dest=edited/(n[1:-1]+'.smali');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 run('java','-cp',jars/'*','org.jf.smali.Main','assemble','--api','21','--jobs','1',edited,'-o',out/'INFINITY-new.dex')
 run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',out/'INFINITY-new.dex','-o',out/'verify')
 current=classes(out/'verify');changed=[];removed=sorted(set(before)-set(current));added=sorted(set(current)-set(before))
 assert all(allowed(n) for n in removed+added)
 for n,raw in before.items():
  if n not in current:continue
  if raw!=current[n].read_text():assert allowed(n),n;changed.append(n)
 save(out/'CLASS-HASHES.json',{'INFINITY':{n:file_sha(p) for n,p in current.items()}})
 save(out/'OWNER-BUILD.json',dict(baseline=BASE,sources={str(p.relative_to(R)):file_sha(p) for p in sources},
  changed=sorted(changed),added=added,removed=removed,unchanged=len(before)-len(changed)-len(removed),
  dex_sha256=file_sha(out/'INFINITY-new.dex'),Cobra_shared_Splash_and_Kodi='UNCHANGED'))
 print(json.dumps(load(out/'OWNER-BUILD.json'),indent=2))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--bundles',type=Path,required=True);a=p.parse_args();build(a.out,a.bundles)
