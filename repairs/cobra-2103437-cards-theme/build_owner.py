"""Compile Cards theme classes only, preserving every non-Cards DEX class."""
import hashlib,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
H=Path(__file__).resolve().parent;R=H.parents[1];ISO=R/'repairs/dual-experience-isolation-2103420'
sys.path[:0]=[str(ISO),str(R/'repairs/cobra-next-from-2103427/cards-from-2103431')];
from projection_patch import methods
from inventory import file_sha,load,save,digest
from compile_runtime import ANDROID_SHA,D8_SHA

def run(*args):subprocess.run(list(map(str,args)),check=True)
def build(out):
 out=out.resolve();out.mkdir()
 tools=Path('/workspace/cobra-evidence/tools');jars=tools/'receipt-evidence/tool-jars';android=tools/'receipt-evidence/android-34.jar';d8=tools/'d8.jar'
 assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
 assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(R/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
 bundle=Path('/tmp/infinity437-prepared/components/COBRA.zip');assert file_sha(bundle)=='41d812863992d9200bbd7708cc03c4a4c048354ccb67cc4ff73ec8c5fb6bb0cb'
 originals={}
 for folder in ('canonical0','canonical1'):
  for p in (Path('/tmp/cards438')/folder).rglob('*.smali'):
   raw=p.read_text();name=raw.splitlines()[0].split()[-1];assert name not in originals;originals[name]=raw
 with ZipFile(bundle) as z:
  meta=json.loads(z.read('component.json'));inputs=[]
  assert {n for n in originals}=={n[6:] for n in meta['payload'] if n.startswith('class:')}
  for n,raw in originals.items():assert digest(raw.encode())==meta['payload']['class:'+n]['sha256']
  for n in sorted(meta['dex']):
   p=out/Path(n).name;p.write_bytes(z.read(n));inputs.append(p)
 source=R/'repairs/cobra-next-from-2103427/cards-from-2103431/runtime'
 sources=[source/(n+'.java') for n in ('CobraCardsLayout','CobraCardsTiles','CobraCardsTheme')]
 sources+=[R/'repairs/cobra-2103435-followups/drawer-only/runtime/CobraCardsDrawerViewport.java']
 classes=out/'classes';classes.mkdir()
 cp=str(android)+':/workspace/cobra-evidence/drawer435-candidate-host-v2/production.jar:/workspace/cobra-evidence/drawer435-candidate-host-v2/support.jar'
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',cp,'-d',classes,*sources)
 roots=('CobraCardsLayout','CobraCardsTiles','CobraCardsTheme')
 with ZipFile(out/'cards.jar','w',ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):
   if p.stem.split('$')[0] in roots:z.write(p,p.relative_to(classes).as_posix())
 generated=out/'generated';generated.mkdir()
 run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',generated,out/'cards.jar')
 smali=out/'generated-smali';run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',generated/'classes.dex','-o',smali)
 changes={}
 for p in smali.rglob('*.smali'):
  raw=p.read_text();name=raw.splitlines()[0].split()[-1];assert any(name.startswith('Lcom/projectinfinity/kodi/'+n) for n in roots);changes[name]=raw
 assert all(n in changes for n in originals if any(n.startswith('Lcom/projectinfinity/kodi/'+root) for root in roots[:2]))
 # Signed436 applied the drawer fix directly to DEX. Recompiling identical
 # Java renumbers registers in physicalLayout: retain its exact original body.
 state='Lcom/projectinfinity/kodi/CobraCardsLayout$State;'
 signature='physicalLayout(Landroid/app/Activity;Ljava/lang/Object;)V'
 generated_body=methods(changes[state])[signature];original_body=methods(originals[state])[signature]
 changes[state]=changes[state].replace(generated_body,original_body)
 (smali/'com/projectinfinity/kodi/CobraCardsLayout$State.smali').write_text(changes[state])
 run('java','-cp',jars/'*','org.jf.smali.Main','assemble',smali,'-o',out/'patch.dex')
 (out/'assignments.tsv').write_text(''.join(n+'\tCOBRA\n' for n in sorted(originals.keys()|changes.keys())))
 (out/'origins.tsv').write_text(''.join(n+'\t'+n+'\n' for n in sorted(changes.keys()&originals.keys())))
 empty=out/'empty';empty.mkdir();run('java','-cp',jars/'*','org.jf.smali.Main','assemble',empty,'-o',out/'empty.dex')
 writer=out/'writer';writer.mkdir();jc=':'.join(str(p) for p in sorted(jars.glob('*.jar')))
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',jc,'-d',writer,H/'ModuleDexWriter.java')
 run('java','-cp',str(writer)+':'+jc,'org.jf.dexlib2.writer.pool.ModuleDexWriter',out/'owner-dex',out/'assignments.tsv',out/'origins.tsv',out/'patch.dex',out/'empty.dex',*inputs)
 observed={}
 for dex in sorted((out/'owner-dex/COBRA').glob('*.dex')):
  target=out/('verify-'+dex.stem);run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',target)
  for p in target.rglob('*.smali'):
   raw=p.read_text();name=raw.splitlines()[0].split()[-1];assert name not in observed;observed[name]=raw
 assert observed.keys()==originals.keys()|changes.keys()
 altered=[n for n in originals if originals[n]!=observed[n]]
 assert all(n in changes for n in altered)
 assert methods(observed[state])[signature]==methods(originals[state])[signature]
 save(out/'OWNER-BUILD.json',dict(status='CARDS_ONLY_CLASS_DELTA_COMPILED_METHOD_REVIEW_PENDING',changed=altered,added=sorted(observed.keys()-originals.keys()),unchanged=len(originals)-len(altered),sources={str(p.relative_to(R)):file_sha(p) for p in sources},dex={p.name:file_sha(p) for p in (out/'owner-dex/COBRA').glob('*.dex')}))
if __name__=='__main__':build(Path(sys.argv[1]))
