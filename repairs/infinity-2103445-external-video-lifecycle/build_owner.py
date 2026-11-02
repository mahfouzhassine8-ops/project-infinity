"""Compile a test-only Infinity owner DEX from exact signed445; not an APK release."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
H=Path(__file__).resolve().parent;R=H.parents[1];ISO=R/'repairs/dual-experience-isolation-2103420'
sys.path[:0]=[str(H),str(ISO),str(R/'repairs/cobra-next-from-2103427/cards-from-2103431')]
from inventory import file_sha,save,digest
from compile_runtime import ANDROID_SHA,D8_SHA
from projection_patch import methods
from patch_external_intents import MAIN,POLICY,patch_main,patch_delayed

def run(*args):subprocess.run(list(map(str,args)),check=True)
def classes(p):return {f.read_text().splitlines()[0].split()[-1]:f.read_text() for f in p.rglob('*.smali')}
def header(s):return re.sub(r'\n{3,}','\n\n',re.sub(r'^\.method [^\n]+\n.*?^\.end method\n?','',s,flags=re.M|re.S)).strip()
def build(out):
 out.mkdir();tools=Path('/workspace/cobra-evidence/tools');jars=tools/'receipt-evidence/tool-jars';android=tools/'receipt-evidence/android-34.jar';d8=tools/'d8.jar'
 assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
 assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==json.loads((R/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
 bundle=Path('/tmp/cobra445-prepared/components/INFINITY.zip');assert file_sha(bundle)=='d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d'
 with ZipFile(bundle) as z:
  meta=json.loads(z.read('component.json'));assert set(meta['dex'])=={'dex/part-0.dex'}
  (out/'baseline.dex').write_bytes(z.read('dex/part-0.dex'))
 run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',out/'baseline.dex','-o',out/'original')
 before=classes(out/'original')
 for name,raw in before.items():assert digest(raw.encode())==meta['payload']['class:'+name]['sha256']
 compiled=out/'classes';compiled.mkdir();stub=out/'Main.java';stub.write_text('package com.projectinfinity.kodi; public class Main extends android.app.NativeActivity { native void _onNewIntent(android.content.Intent i); }')
 source=H/'runtime/InfinityExternalVideoIntents.java'
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',android,'-d',compiled,source,stub)
 with ZipFile(out/'policy.jar','w',ZIP_DEFLATED) as z:
  for p in compiled.rglob('InfinityExternalVideoIntents*.class'):z.write(p,p.relative_to(compiled))
 generated=out/'generated';generated.mkdir();run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',generated,out/'policy.jar')
 smali=out/'patch-smali';run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',generated/'classes.dex','-o',smali)
 changed=classes(smali);assert set(changed)=={POLICY,POLICY[:-1]+'$State;'}
 changed[MAIN]=patch_main(before[MAIN]);changed[MAIN[:-1]+'$3;']=patch_delayed(before[MAIN[:-1]+'$3;'])
 for name,raw in changed.items():
  p=smali/(name[1:-1]+'.smali');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
 run('java','-cp',jars/'*','org.jf.smali.Main','assemble',smali,'-o',out/'patch.dex')
 writer=out/'writer';writer.mkdir();cp=':'.join(str(p) for p in sorted(jars.glob('*.jar')))
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-g:none','-cp',cp,'-d',writer,ISO/'ModuleDexWriter.java',H/'PreserveInfinityExternalDex.java')
 run('java','-cp',str(writer)+':'+cp,'org.jf.dexlib2.writer.pool.PreserveInfinityExternalDex',out/'candidate.dex',out/'patch.dex',out/'baseline.dex')
 run('java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',out/'candidate.dex','-o',out/'verified')
 after=classes(out/'verified');assert after.keys()==before.keys()|changed.keys();delta={}
 for name,raw in before.items():
  assert header(raw)==header(after[name]),name
  a,b=methods(raw),methods(after[name]);diff=sorted(k for k in a.keys()|b.keys() if a.get(k)!=b.get(k))
  if diff:delta[name]=diff
 expected={MAIN:['protected onNewIntent(Landroid/content/Intent;)V','public onCreate(Landroid/os/Bundle;)V'],MAIN[:-1]+'$3;':['public run()V']}
 assert delta==expected,delta
 save(out/'OWNER-PRESERVATION.json',dict(status='PASS_EXACT445_EXTERNAL_INTENT_ONLY_DEX_DELTA',baseline_dex_sha256=file_sha(out/'baseline.dex'),candidate_dex_sha256=file_sha(out/'candidate.dex'),unchanged_classes=len(before)-2,changed_methods=delta,new_classes=sorted(after.keys()-before.keys()),original_fields_annotations='EXACT',onResume_onPause_onStop_onDestroy_other_methods='EXACT',native_Cobra_chooser_shared_shutdown='NOT_MODIFIED_NOT_TESTED',APK='NOT_BUILT',sources={str(p.relative_to(R)):file_sha(p) for p in [source,H/'patch_external_intents.py',H/'build_owner.py',H/'PreserveInfinityExternalDex.java']}))
 print('PASS_EXACT445_EXTERNAL_INTENT_ONLY_DEX_DELTA')
if __name__=='__main__':build(Path(sys.argv[1]))
