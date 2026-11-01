"""Cards native playing-dot restoration and Pro expanded viewport; retain confirmed working Preview/Display fixes."""
import hashlib,json,subprocess,sys,os
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
 tools=Path(os.environ.get('CARDS_TOOLS_ROOT','/workspace/cobra-evidence/tools'));jars=tools/'receipt-evidence/tool-jars';android=tools/'receipt-evidence/android-34.jar';d8=tools/'d8.jar'
 assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
 assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(R/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
 bundle=Path(os.environ.get('CARDS_BASELINE_BUNDLE','/tmp/cards438/prepared/components/COBRA.zip'));assert file_sha(bundle)=='2229274553616f4febb7ef80925eddc23f6f2346bddf4eeabee18e819158399e'
 originals={};inputs=[]
 with ZipFile(bundle) as z:
  meta=json.loads(z.read('component.json'))
  for n in sorted(meta['dex']):
   p=out/Path(n).name;p.write_bytes(z.read(n));inputs.append(p)
   canonical=out/('original-'+p.stem)
   run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',p,'-o',canonical)
   for f in canonical.rglob('*.smali'):
    raw=f.read_text();name=raw.splitlines()[0].split()[-1];assert name not in originals;originals[name]=raw
  assert originals.keys()=={n[6:] for n in meta['payload'] if n.startswith('class:')}
  for n,raw in originals.items():assert digest(raw.encode())==meta['payload']['class:'+n]['sha256']
 source=R/'repairs/cobra-next-from-2103427/cards-from-2103431/runtime'
 sources=[source/(n+'.java') for n in ('CobraCardsLayout',)]
 sources+=[source/'CobraCardsTheme.java',source/'CobraCardsTiles.java']
 sources+=[R/'repairs/cobra-2103435-followups/drawer-only/runtime/CobraCardsDrawerViewport.java']
 classes=out/'classes';classes.mkdir()
 # Compile-only native signatures. No stub class enters cards.jar/DEX.
 stubs=out/'compile-only';stubs.mkdir()
 definitions={
 'CobraArrange':'public static Object ownedField(android.app.Activity a,String n){throw new AssertionError();} public static Object ownedCall(android.app.Activity a,String n,Class<?>[] types,Object... args){throw new AssertionError();}',
 'CobraCardsReuse':'public static void beforeLayout(android.app.Activity a,int width,int height,int columns){throw new AssertionError();} public static void columnsApplied(android.app.Activity a,android.widget.GridView v){throw new AssertionError();}',
 'CobraLogoRequests':'public static void clear(android.app.Activity a,android.widget.ImageView v){throw new AssertionError();} public static void request(android.app.Activity a,String url,android.widget.ImageView v){throw new AssertionError();}'}
 for name,body in definitions.items():(stubs/(name+'.java')).write_text('package com.projectinfinity.kodi; public final class '+name+'{'+body+'}')
 cp=str(android)
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',cp,'-d',classes,*sources,*stubs.glob('*.java'))
 roots=('CobraCardsLayout','CobraCardsTiles')
 with ZipFile(out/'cards.jar','w',ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):
   if p.stem.split('$')[0] in roots:z.write(p,p.relative_to(classes).as_posix())
 generated=out/'generated';generated.mkdir()
 run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',generated,out/'cards.jar')
 smali=out/'generated-smali';run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',generated/'classes.dex','-o',smali)
 changes={}
 for p in smali.rglob('*.smali'):
  raw=p.read_text();name=raw.splitlines()[0].split()[-1];assert any(name.startswith('Lcom/projectinfinity/kodi/'+n) for n in roots);changes[name]=raw
 # Merge selected methods only; retain every other signed438 method/field.
 budget=load(H/'METHOD-ALLOWLIST.json');merged={}
 for name in ('Lcom/projectinfinity/kodi/CobraCardsLayout;','Lcom/projectinfinity/kodi/CobraCardsTiles$Holder;'):
  original=originals[name];old=methods(original);new=methods(changes[name])
  for sig in budget[name]:
   assert sig in new
   if sig in old:original=original.replace(old[sig],new[sig])
   else:original+='\n'+new[sig]+'\n'
  merged[name]=original
 from patch_native import patch,patch_pro,APP,PRO
 merged[APP]=patch(originals[APP]);merged[PRO]=patch_pro(originals[PRO])
 sources+=[H/'patch_native.py']
 changes=merged
 for p in smali.rglob('*.smali'):p.unlink()
 for name,raw in changes.items():
  p=smali/(name[1:-1]+'.smali');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
 component='Lcom/projectinfinity/kodi/CobraComponent;'
 old=originals[component];require_old='"2103438.cobra.1"';assert old.count(require_old)==1
 changes[component]=old.replace(require_old,'"2103441.cobra.1"',1)
 cpfile=smali/'com/projectinfinity/kodi/CobraComponent.smali';cpfile.write_text(changes[component])
 run('java','-cp',jars/'*','org.jf.smali.Main','assemble',smali,'-o',out/'versioned-patch.dex')
 (out/'assignments.tsv').write_text(''.join(n+'\tCOBRA\n' for n in sorted(originals.keys()|changes.keys())))
 (out/'origins.tsv').write_text(''.join(n+'\t'+n+'\n' for n in sorted(changes.keys()&originals.keys())))
 empty=out/'empty';empty.mkdir();run('java','-cp',jars/'*','org.jf.smali.Main','assemble',empty,'-o',out/'empty.dex')
 writer=out/'writer';writer.mkdir();jc=':'.join(str(p) for p in sorted(jars.glob('*.jar')))
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',jc,'-d',writer,ISO/'ModuleDexWriter.java')
 run('java','-cp',str(writer)+':'+jc,'org.jf.dexlib2.writer.pool.ModuleDexWriter',out/'owner-dex',out/'assignments.tsv',out/'origins.tsv',out/'versioned-patch.dex',out/'empty.dex',*inputs)
 observed={}
 for dex in sorted((out/'owner-dex/COBRA').glob('*.dex')):
  target=out/('verify-'+dex.stem);run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',target)
  for p in target.rglob('*.smali'):
   raw=p.read_text();name=raw.splitlines()[0].split()[-1];assert name not in observed;observed[name]=raw
 assert observed.keys()==originals.keys()|changes.keys()
 altered=sorted(n for n in originals if originals[n]!=observed[n])
 assert all(n in changes for n in altered)
 assert observed[component]==changes[component]
 budget=load(H/'METHOD-ALLOWLIST.json');actual={}
 for name in altered:
  a,b=methods(originals[name]),methods(observed[name]);actual[name]=sorted(k for k in a.keys()|b.keys() if a.get(k)!=b.get(k))
 assert actual==budget,('UNREVIEWED_METHOD_DELTA',actual)
 save(out/'METHOD-DELTA.json',actual)
 save(out/'CLASS-HASHES.json',{name:digest(raw.encode()) for name,raw in observed.items()})
 save(out/'OWNER-BUILD.json',dict(status='PASS_CARDS_PLAYING_DOT_AND_PRO_VIEWPORT_METHOD_DELTA',changed=altered,added=sorted(observed.keys()-originals.keys()),unchanged=len(originals)-len(altered),sources={str(p.relative_to(R)):file_sha(p) for p in sources},dex={p.name:file_sha(p) for p in (out/'owner-dex/COBRA').glob('*.dex')}))
if __name__=='__main__':build(Path(sys.argv[1]))
