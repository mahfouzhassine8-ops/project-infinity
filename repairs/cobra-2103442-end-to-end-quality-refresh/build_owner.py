"""Cobra-only, exact signed442 input; untouched second DEX and original class fields."""
import json,os,re,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
H=Path(__file__).resolve().parent;R=H.parents[1];ISO=R/'repairs/dual-experience-isolation-2103420'
sys.path[:0]=[str(ISO),str(H),str(R/'repairs/cobra-next-from-2103427/cards-from-2103431')]
from inventory import file_sha,load,save,digest
from compile_runtime import ANDROID_SHA,D8_SHA
from projection_patch import methods
from patch_native import APP,patch,CHANNEL,HELPER
VERSION=2103443
BASELINE_SHA='9435546ad399b7d464340ca54b3208f8db15a7c3f63bc5dee0bdb2c99989ee7e'
def run(*args):subprocess.run(list(map(str,args)),check=True)
def header(raw):
 raw=re.sub(r'^\.method [^\n]+\n.*?^\.end method\n?','',raw,flags=re.M|re.S)
 return re.sub(r'\n{3,}','\n\n',raw).strip()
def read_classes(directory):
 return {p.read_text().splitlines()[0].split()[-1]:p.read_text() for p in directory.rglob('*.smali')}
def build(out):
 out=out.resolve();out.mkdir()
 tools=Path(os.environ.get('CARDS_TOOLS_ROOT','/workspace/cobra-evidence/tools'));jars=tools/'receipt-evidence/tool-jars';android=tools/'receipt-evidence/android-34.jar';d8=tools/'d8.jar'
 assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
 assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(R/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
 bundle=Path(os.environ.get('CARDS_BASELINE_BUNDLE','/tmp/approved442/components442/COBRA.zip'));assert file_sha(bundle)==BASELINE_SHA
 originals={};inputs=[]
 with ZipFile(bundle) as z:
  meta=json.loads(z.read('component.json'))
  for n in sorted(meta['dex']):
   p=out/Path(n).name;p.write_bytes(z.read(n));inputs.append(p);target=out/('original-'+p.stem)
   run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',p,'-o',target)
   for name,raw in read_classes(target).items():assert name not in originals;originals[name]=raw
  assert originals.keys()=={n[6:] for n in meta['payload'] if n.startswith('class:')}
  for name,raw in originals.items():assert digest(raw.encode())==meta['payload']['class:'+name]['sha256']
 classes=out/'classes';classes.mkdir();stubs=out/'compile-only';stubs.mkdir()
 (stubs/'CobraArrange.java').write_text('package com.projectinfinity.kodi; public final class CobraArrange{public static Object ownedCall(android.app.Activity a,String n,Class<?>[] t,Object...args){throw new AssertionError();}}')
 source=H/'runtime/CobraGuidePresentation.java'
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',android,'-d',classes,source,*stubs.glob('*.java'))
 with ZipFile(out/'presentation.jar','w',ZIP_DEFLATED) as z:
  for p in classes.rglob('CobraGuidePresentation*.class'):z.write(p,p.relative_to(classes).as_posix())
 generated=out/'generated';generated.mkdir();run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',generated,out/'presentation.jar')
 smali=out/'generated-smali';run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',generated/'classes.dex','-o',smali)
 changes=read_classes(smali)
 expected={HELPER[:-1]+suffix+';' for suffix in ('','$ClockFormat','$State','$Pair','$ProgramFields','$Snapshot','$Entry')}
 assert set(changes)==expected and not expected&originals.keys(),set(changes)
 changes[APP]=patch(originals[APP]);component='Lcom/projectinfinity/kodi/CobraComponent;'
 old=originals[component];assert old.count('"2103442.cobra.1"')==1
 changes[component]=old.replace('"2103442.cobra.1"','"'+str(VERSION)+'.cobra.1"',1)
 for name,raw in changes.items():
  p=smali/(name[1:-1]+'.smali');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
 run('java','-cp',jars/'*','org.jf.smali.Main','assemble',smali,'-o',out/'patch.dex')
 writer=out/'writer';writer.mkdir();jc=':'.join(str(p) for p in sorted(jars.glob('*.jar')))
 writer_source=H/'PreserveCobraDexPartition.java'
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',jc,'-d',writer,ISO/'ModuleDexWriter.java',writer_source)
 run('java','-cp',str(writer)+':'+jc,'org.jf.dexlib2.writer.pool.PreserveCobraDexPartition',out/'owner-dex/COBRA',out/'patch.dex',*inputs)
 assert file_sha(out/'owner-dex/COBRA/part-1.dex')==file_sha(inputs[1]),'UNTOUCHED_SECOND_DEX'
 observed={}
 for dex in sorted((out/'owner-dex/COBRA').glob('*.dex')):
  target=out/('verify-'+dex.stem);run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',target)
  observed.update(read_classes(target))
 assert observed.keys()==originals.keys()|changes.keys()
 actual={}
 for name,raw in originals.items():
  assert header(raw)==header(observed[name]),('ORIGINAL_FIELDS_ANNOTATIONS',name)
  if raw==observed[name]:continue
  before,after=methods(raw),methods(observed[name]);actual[name]=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
 budget={APP:sorted(['private formatTime(J)Ljava/lang/String;','private cobraNextProgram('+CHANNEL+')'+APP[:-1]+'$GuideProgram;','private cobraNextProgramList('+CHANNEL+')Ljava/util/ArrayList;']),component:['public static version()Ljava/lang/String;']}
 assert actual==budget,('UNREVIEWED_METHOD_DELTA',actual)
 added={name:sorted(methods(observed[name])) for name in observed.keys()-originals.keys()}
 save(out/'METHOD-DELTA.json',actual);save(out/'NEW-CLASS-METHODS.json',added)
 save(out/'CLASS-HASHES.json',{name:digest(raw.encode()) for name,raw in observed.items()})
 sources=[source,H/'patch_native.py',H/'build_owner.py',writer_source,ISO/'ModuleDexWriter.java']
 save(out/'OWNER-BUILD.json',dict(status='PASS_COBRA_QUALITY_EXACT442_METHOD_DELTA',baseline_component_sha256=BASELINE_SHA,changed=sorted(actual),added=sorted(added),unchanged=len(originals)-len(actual),sources={str(p.relative_to(R)):file_sha(p) for p in sources},dex={p.name:file_sha(p) for p in (out/'owner-dex/COBRA').glob('*.dex')}))
if __name__=='__main__':build(Path(sys.argv[1]))
