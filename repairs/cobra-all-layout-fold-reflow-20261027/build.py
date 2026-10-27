"""Cobra-only delta from the exact signed 2103421 owner DEX; never signs."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
ISO=HERE.parent/'dual-experience-isolation-2103420';sys.path.insert(0,str(ISO))
from inventory import load,save,file_sha,digest,APP
BASE_SHA='a1ea9442cd8ff82be09c34cc7c84887178fb162b8397005bba656ff6e28f5637'
VERSION='bundled-2103420.isolation.1.fold-reflow.1'
def run(args):subprocess.run(list(map(str,args)),check=True)
def build(apk,baseline,jars,android,d8,out):
 assert file_sha(apk)==BASE_SHA
 with ZipFile(apk) as z:
  for name in ['classes4.dex','classes5.dex']:assert digest(z.read(name))==file_sha(baseline/name)
 from compile_runtime import ANDROID_SHA,D8_SHA
 assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
 assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(ISO.parent/'universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
 authority=load(ISO/'release-authority.json');sources={}
 for p in baseline.glob('*-smali/**/*.smali'):
  name=p.read_text().splitlines()[0].split()[-1];sources[name]=p.read_text()
 assert all(digest(s.encode())==authority['payload']['class:'+n]['sha256'] for n,s in sources.items())
 out.mkdir();changed=out/'changed/com/projectinfinity/kodi';changed.mkdir(parents=True)
 activity=sources[APP+'InfinityLiveActivity;']
 activity=activity.replace('.super Landroid/app/Activity;', '.super Landroid/app/Activity;\n.implements '+APP+'CobraWindowReflow$Owner;',1)
 anchor='    invoke-direct {p0}, '+APP+'InfinityLiveActivity;->buildShell()V'
 creation=re.search(r'^\.method protected onCreate\(Landroid/os/Bundle;\)V\n.*?^\.end method',activity,re.M|re.S).group()
 assert creation.count(anchor)==1
 revised=creation.replace(anchor,anchor+'\n\n    invoke-static {p0}, '+APP+'CobraWindowReflow;->install(Landroid/app/Activity;)V',1)
 activity=activity.replace(creation,revised,1)
 activity+='''
.method public cobraReflowSurface()Landroid/view/View;
    .registers 2
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mMultiOverlay:Landroid/widget/FrameLayout;
    if-nez v0, :ready
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mPlayerOverlay:Landroid/widget/FrameLayout;
    if-nez v0, :ready
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideShell:Landroid/widget/FrameLayout;
    :ready
    return-object v0
.end method

.method public cobraReflowMeasuredWindow()V
    .registers 2
    invoke-direct {p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraLayoutPlayerPanels()V
    invoke-direct {p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraLayoutMultiTiles()V
    iget-object v0, p0, Lcom/projectinfinity/kodi/InfinityLiveActivity;->mCobraGuideShell:Landroid/widget/FrameLayout;
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/widget/FrameLayout;->isAttachedToWindow()Z
    move-result v0
    if-eqz v0, :done
    invoke-direct {p0}, Lcom/projectinfinity/kodi/InfinityLiveActivity;->cobraLayoutGuide()V
    :done
    return-void
.end method
'''
 (changed/'InfinityLiveActivity.smali').write_text(activity)
 version=sources[APP+'CobraComponent;'];assert version.count('"bundled-2103420.isolation.1"')==1
 (changed/'CobraComponent.smali').write_text(version.replace('"bundled-2103420.isolation.1"','"'+VERSION+'"'))
 classes=out/'compiled';classes.mkdir();helper=out/'helpers';helper.mkdir()
 run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',android,'-d',classes,HERE/'runtime/CobraWindowReflow.java'])
 with ZipFile(out/'helper.jar','w') as z:
  for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes).as_posix())
 run(['java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',helper,out/'helper.jar'])
 run(['java','-cp',str(jars/'*'),'org.jf.smali.Main','assemble','--api','21',out/'changed','-o',out/'changed.dex'])
 run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',helper/'classes.dex','-o',out/'helper-smali'])
 owned={n for n in sources if authority['payload']['class:'+n]['owner']=='COBRA'}
 owned.update(p.read_text().splitlines()[0].split()[-1] for p in (out/'helper-smali').rglob('*.smali'))
 (out/'assignments.tsv').write_text(''.join(n+'\tCOBRA\n' for n in sorted(owned)))
 (out/'origins.tsv').write_text(''.join(APP+n+';\t'+APP+n+';\n' for n in ['InfinityLiveActivity','CobraComponent']))
 host=out/'host';host.mkdir();cp=':'.join(map(str,sorted(jars.glob('*.jar'))))
 run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',cp,'-d',host,ISO/'ModuleDexWriter.java'])
 inputs=sorted(p for p in baseline.glob('classes*.dex') if p.name in ['classes4.dex','classes5.dex'])
 run(['java','-cp',str(host)+':'+cp,'org.jf.dexlib2.writer.pool.ModuleDexWriter',out/'owner-dex',out/'assignments.tsv',out/'origins.tsv',out/'changed.dex',helper/'classes.dex',*inputs])
 save(out/'BUILD.json',{'status':'COMPILED_UNSIGNED_PENDING_GEOMETRY_TESTS','baseline_apk_sha256':BASE_SHA,'component_version':VERSION,'changed_original_classes':['InfinityLiveActivity','CobraComponent'],'new_java_sha256':file_sha(HERE/'runtime/CobraWindowReflow.java')})
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['apk','baseline','jars','android','d8','out']:p.add_argument('--'+n,type=Path,required=True)
 build(**vars(p.parse_args()))
