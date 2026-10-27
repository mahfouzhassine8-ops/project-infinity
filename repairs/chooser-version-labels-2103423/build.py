"""Build an unsigned chooser-only owner from exact signed 2103423; never signs."""
import argparse, copy, hashlib, json, re, subprocess, sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
HERE=Path(__file__).resolve().parent
ISO=HERE.parent/'dual-experience-isolation-2103420'
sys.path.insert(0,str(ISO))
from inventory import APP,canonical,digest,file_sha,load,save
from component_bundles import read_bundle,record
from release_gate import component_digest,require

SIGNED_SHA='4cbbf963be72904de962f434d00ee5f9d5080de6b6b9fd4b3e31ab1d6ac01aff'
SHELL_ZIP_SHA='d57912e7a7020b0fbc441a067f09e3e6512501f450072c6c6cf71135aab13952'
OLD_DEX_SHA='f2cc8dc2484ea388c2e4a981decf25099be32b2f28c415bcef649197e0f58a2f'
VERSION='2103420.container.2.labels.1'
MEMBER='assets/experience-component-updates.properties'
SOURCE=HERE/'runtime/ChooserReleaseMetadata.smali'

def run(*args):
 subprocess.run(list(map(str,args)),check=True)

def change(path,pattern,anchor,added):
 s=path.read_text()
 match=re.search(r'^\.method '+pattern+r'\n.*?^\.end method',s,re.M|re.S)
 require(match is not None,'EXPECTED_METHOD_NOT_FOUND:'+path.name)
 method=match[0]
 require(method.count(anchor)==1,'EXPECTED_ANCHOR_NOT_FOUND:'+path.name)
 path.write_text(s[:match.start()]+method.replace(anchor,anchor+added,1)+s[match.end():])

def patch(smali):
 base=smali/'com/projectinfinity/kodi'
 card=base/'InfinityGlassChooser$Card.smali'
 stage=base/'InfinityGlassChooser$Stage.smali'
 change(card,r'constructor <init>\(Landroid/content/Context;ZZLcom/projectinfinity/kodi/InfinityGlassChooser\$Actions;\)V',
 '    invoke-virtual {v15, v1}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->setVisibility(I)V',
 '''
    invoke-static {v8, v10}, Lcom/projectinfinity/kodi/ChooserReleaseMetadata;->updated(Landroid/content/Context;Z)Ljava/lang/String;
    move-result-object v1
    invoke-virtual {v15, v1}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->setText(Ljava/lang/CharSequence;)V
    const/4 v1, 0x0
    invoke-virtual {v15, v1}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->setVisibility(I)V''')
 change(stage,r'constructor <init>\(Landroid/content/Context;ZLcom/projectinfinity/kodi/InfinityGlassChooser\$Actions;\)V',
 '    invoke-direct {p0}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->updateClock()V',
 '''
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->getContext()Landroid/content/Context;
    move-result-object v0
    invoke-static {v0}, Lcom/projectinfinity/kodi/ChooserReleaseMetadata;->installed(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v1
    iget-object v2, p0, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->hmCopy:Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;
    invoke-virtual {v2, v1}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->setText(Ljava/lang/CharSequence;)V
    const/4 v1, 0x0
    invoke-virtual {v2, v1}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->setVisibility(I)V''')
 change(stage,r'protected onMeasure\(II\)V',
 '    invoke-virtual {p0, p1, p2}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->setMeasuredDimension(II)V',
 '''
    iget-object v1, p0, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->hmCopy:Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->getContext()Landroid/content/Context;
    move-result-object v3
    const/high16 v4, 0x41c00000
    invoke-static {v3, v4}, Lcom/projectinfinity/kodi/InfinityGlassChooser;->access$000(Landroid/content/Context;F)I
    move-result v3
    sub-int v2, p1, v3
    sub-int/2addr v2, v3
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->getContext()Landroid/content/Context;
    move-result-object v3
    const/high16 v4, 0x41800000
    invoke-static {v3, v4}, Lcom/projectinfinity/kodi/InfinityGlassChooser;->access$000(Landroid/content/Context;F)I
    move-result v3
    invoke-direct {p0, v1, v2, v3}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->measure(Landroid/view/View;II)V''')
 change(stage,r'protected onLayout\(ZIIII\)V',
 '    invoke-direct {p0, p1, p3, p2}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->place(Landroid/view/View;II)V',
 '''
    iget-object p1, p0, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->hmCopy:Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;
    invoke-virtual {p0}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->getMeasuredWidth()I
    move-result p3
    invoke-virtual {p1}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->getMeasuredWidth()I
    move-result p4
    sub-int/2addr p3, p4
    div-int/lit8 p3, p3, 0x2
    iget-object p4, p0, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->footer:Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;
    invoke-virtual {p4}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->getTop()I
    move-result p4
    invoke-virtual {p1}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Label;->getMeasuredHeight()I
    move-result p5
    sub-int/2addr p4, p5
    iget-object p5, p0, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->infinity:Lcom/projectinfinity/kodi/InfinityGlassChooser$Card;
    invoke-virtual {p5}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Card;->getBottom()I
    move-result p5
    invoke-static {p4, p5}, Ljava/lang/Math;->max(II)I
    move-result p4
    invoke-direct {p0, p1, p3, p4}, Lcom/projectinfinity/kodi/InfinityGlassChooser$Stage;->place(Landroid/view/View;II)V''')
 (base/'ChooserReleaseMetadata.smali').write_bytes(SOURCE.read_bytes())

def classes(directory):
 return {p.relative_to(directory).as_posix():p.read_bytes() for p in directory.rglob('*.smali')}

def build(apk,bundles,jars,out,source):
 require(file_sha(apk)==SIGNED_SHA,'SIGNED_2103423_REQUIRED')
 require(file_sha(bundles/'CHOOSER_SHELL.zip')==SHELL_ZIP_SHA,'EXACT_SHELL_REQUIRED')
 catalog=load(bundles/'catalog.json')
 meta=copy.deepcopy(read_bundle(bundles/'CHOOSER_SHELL.zip',catalog['bundles']['CHOOSER_SHELL']))
 with ZipFile(apk) as z:
  old=z.read('classes.dex')
 require(digest(old)==OLD_DEX_SHA,'EXACT_DEX_PREIMAGE_REQUIRED')
 require(not out.exists(),'FRESH_OUTPUT_REQUIRED')
 out.mkdir();(out/'old.dex').write_bytes(old)
 oldsmali=out/'old-smali';newsmali=out/'new-smali'
 run('java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',out/'old.dex','-o',oldsmali)
 import shutil
 shutil.copytree(oldsmali,newsmali)
 # Introspect only the actual signed 2103423 layout, not historical previews.
 stage_inspect=(newsmali/'com/projectinfinity/kodi/InfinityGlassChooser$Stage.smali').read_text()
 print('CHOOSER_ACTUAL_STAGE_FIELDS', '\\n'.join(x for x in stage_inspect.splitlines() if x.startswith('.field') or x.startswith('.super')))
 import re as re_inspect
 for kind,sig in [('constructor',r'constructor <init>\\(Landroid/content/Context;ZLcom/projectinfinity/kodi/InfinityGlassChooser\\$Actions;\\)V'),('measure',r'protected onMeasure\\(II\\)V'),('layout',r'protected onLayout\\(ZIIII\\)V')]:
  mm=re_inspect.search(r'^\\.method '+sig+r'\\n.*?^\\.end method',stage_inspect,re_inspect.M|re_inspect.S)
  if mm:
   print('CHOOSER_ACTUAL_'+kind.upper(), '\\n'.join(mm[0].splitlines()[:150]))
 patch(newsmali)
 run('java','-cp',str(jars/'*'),'org.jf.smali.Main','assemble','--api','21',newsmali,'-o',out/'new.dex')
 verify_smali=out/'verify-smali'
 run('java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',out/'new.dex','-o',verify_smali)
 a,b=classes(oldsmali),classes(verify_smali)
 expected={'com/projectinfinity/kodi/InfinityGlassChooser$Card.smali','com/projectinfinity/kodi/InfinityGlassChooser$Stage.smali'}
 new={'com/projectinfinity/kodi/ChooserReleaseMetadata.smali'}
 require(set(b)-set(a)==new and set(a)-set(b)==set(),'UNEXPECTED_CLASS_SET')
 require({k for k in a if a[k]!=b[k]}==expected,'UNRELATED_SHELL_CLASS_MUTATION')
 require(len(a)==150 and len(b)==151,'INCOMPLETE_SHELL_CLASSES')
 payload={k:v for k,v in meta['payload'].items() if not k.startswith('class:')}
 for path,data in b.items():
  descriptor=data.decode().splitlines()[0].split()[-1]
  payload['class:'+descriptor]={'owner':'CHOOSER_SHELL','sha256':digest(data)}
 require(len(payload)==151,'UNEXPECTED_SHELL_MEMBER_COUNT')
 history=b'infinity.last_updated_in=2103421\ncobra.last_updated_in=2103423\n'
 member={'owner':'CHOOSER_SHELL','sha256':digest(history)}
 payload['member:'+MEMBER]=member
 meta['payload']=payload
 meta['members'][MEMBER]={'sha256':digest(history),'compress_type':ZIP_DEFLATED,'external_attr':0o100644<<16}
 meta['dex']={'dex/part-0.dex':file_sha(out/'new.dex')}
 meta['version']=VERSION
 meta['approved_source']=source
 meta['digest']=component_digest(payload,'CHOOSER_SHELL')
 target=out/'CHOOSER_SHELL.zip'
 with ZipFile(target,'w') as z:
  z.writestr(record('dex/part-0.dex'),(out/'new.dex').read_bytes())
  z.writestr(record('payload/'+MEMBER),history)
  z.writestr(record('component.json'),canonical(meta))
 row={key:meta[key] for key in ('version','digest','settings_schema','approved_source')}
 row.update(file='CHOOSER_SHELL.zip',sha256=file_sha(target))
 read_bundle(target,row)
 save(out/'catalog-row.json',row)
 save(out/'component.json',meta)
 save(out/'PRESERVATION.json',{
  'status':'PASS_TARGETED_SHELL_ONLY',
  'signed_base_sha256':SIGNED_SHA,
  'old_shell_class_count':len(a),'new_shell_class_count':len(b),
  'modified_original_classes':sorted(expected),'added_class':sorted(new),
  'exact_unchanged_shell_classes':len(a)-len(expected),
  'offline_component_history':{'INFINITY':2103421,'COBRA':2103423},
  'app_version_source':'Android package manager actual manifest versionCode',
  'all_other_owner_bundles_unchanged':True})
 return row

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ('apk','bundles','jars','out'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--source',required=True)
 print(json.dumps(build(**vars(p.parse_args())),indent=2))
