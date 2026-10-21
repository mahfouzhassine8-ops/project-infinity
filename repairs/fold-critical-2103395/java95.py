"""Only additive hooks in three original classes; every other definition retained."""
import json,os,re,subprocess,shutil
from pathlib import Path
import components95 as c
PREFIX='com/projectinfinity/kodi/'
EDITOR=PREFIX+'InfinityAndroidKeyboard$Editor.smali';EVIDENCE=PREFIX+'InfinityInstalledCodeEvidence.smali';STARTUP=PREFIX+'InfinityInstalledCheckpointInstaller.smali'
TARGETS={EDITOR,EVIDENCE,STARTUP}
CTOR='<init>(Landroid/app/Activity;JLjava/lang/String;Ljava/lang/String;ZZILcom/projectinfinity/kodi/InfinityAndroidKeyboard$Sink;)V'
COLLECT='collect(Landroid/content/Context;)Lorg/json/JSONObject;'
STUB='''package com.projectinfinity.kodi;
import android.app.*;import android.widget.*;
final class InfinityAndroidKeyboard {
 interface Sink {void change(long t,String s,boolean f,boolean a);}
 static final class Editor {
 Activity owner; Dialog dialog; EditText input; int kind;
 void finish(boolean b) {} int dp(float f){return 0;}
 }
}'''

def build_and_patch(original,modified,work,android,tools,cp,api):
 import dex95 as d
 sources=work/'ui-java';sources.mkdir();classes=work/'ui-classes';classes.mkdir()
 (sources/'InfinityAndroidKeyboard.java').write_text(STUB)
 for name in ('InfinitySearch95.java','InfinityEvidence95.java'):shutil.copyfile(c.HERE/name,sources/name)
 subprocess.run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-cp',str(android),'-d',str(classes)]+[str(p) for p in sources.glob('*.java')],check=True)
 produced=[p for p in classes.rglob('*.class') if p.name.startswith(('InfinitySearch95','InfinityEvidence95'))]
 helper=work/'ui-dex';helper.mkdir();subprocess.run([str(tools/'d8'),'--release','--min-api',str(api),'--lib',str(android),'--output',str(helper)]+[str(p) for p in produced],check=True)
 decoded=work/'ui-smali';subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(helper/'classes.dex'),'-o',str(decoded)],check=True)
 added={p.relative_to(decoded).as_posix() for p in decoded.rglob('*.smali')}
 c.require(added and not added&set(original) and all(n.startswith((PREFIX+'InfinitySearch95',PREFIX+'InfinityEvidence95')) for n in added),'unapproved new class')
 for name in added:target=modified/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(decoded/name,target)
 methods=d.previous().methods;report={}
 for name,method,anchor,hook in [(EDITOR,CTOR,'    return-void\n',
  '    move-object/from16 v0, p0\n    move-object/from16 v1, p5\n    move/from16 v2, p6\n    move/from16 v3, p7\n    invoke-static {v0, v1, v2, v3}, Lcom/projectinfinity/kodi/InfinitySearch95;->decorate(Lcom/projectinfinity/kodi/InfinityAndroidKeyboard$Editor;Ljava/lang/String;ZZ)V\n'),
 (EVIDENCE,COLLECT,'    return-object v6\n',
  '    move-object/from16 v0, p0\n    invoke-static {v0, v6}, Lcom/projectinfinity/kodi/InfinityEvidence95;->append(Landroid/content/Context;Lorg/json/JSONObject;)V\n')]:
  block=methods(original[name])[method];c.require(block.count(anchor)==1,'hook return differs')
  patched=block.replace(anchor,hook+anchor,1);result=original[name].replace(block,patched,1)
  c.require(result.replace(patched,block,1)==original[name] and patched.replace(hook,'',1)==block,'original instructions altered')
  (modified/name).write_text(result);report[name]={'method':method,'original_sha256':c.sha(original[name].encode()),'new_sha256':c.sha(result.encode()),'additive_hook_reversal_exact':True}
 return added,report

def preserve_fields(original,assembled,work,api,cp):
 classes=work/'field-preservation95';classes.mkdir();adapter=c.HERE/'PreserveDexFields95.java'
 subprocess.run(['javac','--release','8','-g:none','-cp',cp,'-d',str(classes),str(adapter)],check=True)
 intermediate=work/'assembler-output.dex';os.rename(assembled,intermediate)
 result=subprocess.run(['java','-cp',str(classes)+os.pathsep+cp,'org.jf.dexlib2.writer.pool.PreserveDexFields95',str(original),str(intermediate),str(assembled),str(api)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);print(result.stdout,flush=True)
 c.require(result.returncode==0,'original encoded field preservation failed')
 count=re.search(r'VERIFIED_EXACT_FIELD_DEFINITIONS=(\d+)',result.stdout);protected=re.search(r'PRESERVED_CLASSES=(\d+)',result.stdout)
 c.require(count and protected and int(count[1])==25870 and int(protected[1])==7852,'protected definition count differs')
 return dict(build_only_adapter_sha256=c.digest(adapter),exact_field_definitions_verified=int(count[1]),protected_class_definitions_from_original=int(protected[1]),encoded_values_and_presence_preserved=True,field_normalization_or_exemption_added=False,protected_runtime_classes_recompiled=False,adapter_packaged_into_app=False)

def verify_class_maps(before,after,added):
 c.require(set(after)==set(before)|set(added),'class inventory drift')
 changed={n for n in before if before[n]!=after[n]};c.require(changed==TARGETS,'unapproved changed original classes')
 return {'changed_classes':sorted(changed),'protected_classes':len(before)-len(TARGETS),'added_classes':sorted(added)}
