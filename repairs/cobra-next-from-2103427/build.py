"""Build Cobra presentation delta from exact signed2103427 owned DEX only.

No whole-Activity reconstruction, library rebuild, app install or signing.
All non-selected methods and class definitions are preserved by exact pins.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
sys.path.insert(0,str(ISO))
from inventory import load,file_sha,save,APP
from component_bundles import read_bundle
from compile_runtime import ANDROID_SHA,D8_SHA

VERSION='2103431.cobra.1'
HELPER=APP+'CobraArrange;'
PRESENT=APP+'CobraPresentation;'
ACTIVITY=APP+'InfinityLiveActivity;'


def run(args):subprocess.run(list(map(str,args)),check=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def methods(text):return {m[1]:m[0]+'\n' for m in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method',text,re.M|re.S)}


def patch_activity(text):
    budget=load(HERE/'SOURCE-BUDGET.json')
    assert sha(text.encode())==budget['activity_class_sha256']
    before=methods(text);changed={}
    def update(name,edit):
        signature=next(s for s in before if s.split('(')[0].split()[-1]==name)
        old=before[signature];assert sha(old.encode())==budget['selected_method_preimages'][signature]
        revised=edit(old);assert revised!=old
        changed[signature]=revised
    def layout(s):
        assert '.registers 24' in s;s=s.replace('.registers 24','.registers 32',1)
        anchor='    invoke-static/range {v8 .. v13}, '+APP+'InfinityLiveActivity$CobraMultiLayoutPolicy;->rect(IIIIIZ)[I\n\n    move-result-object v0'
        assert s.count(anchor)==1
        descriptor='(Landroid/app/Activity;[I'+'I'*5+'Z)[I'
        s=s.replace(anchor,anchor+'''

    move-object/from16 v23, v6
    move-object/from16 v24, v0
    move/from16 v25, v4
    move/from16 v26, v9
    move/from16 v27, v19
    move/from16 v28, v20
    move/from16 v29, v14
    move/from16 v30, v15
    invoke-static/range {v23 .. v30}, '''+HELPER+'->rect'+descriptor+'''
    move-result-object v0''',1)
        return s.replace('    return-void','    invoke-static/range {p0 .. p0}, '+HELPER+'->afterLayout(Landroid/app/Activity;)V\n\n    return-void')
    update('cobraLayoutMultiTiles',layout)
    update('cobraShowMultiLayoutChooser',lambda s:s.replace('    return-void','    invoke-static {p0, v8}, '+HELPER+'->addLayouts(Landroid/app/Activity;Landroid/widget/LinearLayout;)V\n\n    return-void'))
    def actions(s):
        anchor='    invoke-direct {p0, v2, p1, v3}, '+ACTIVITY+'->cobraOpenSheet(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Landroid/widget/LinearLayout;\n\n    move-result-object p1'
        assert s.count(anchor)==1
        return s.replace(anchor,anchor+'\n\n    invoke-static {p0, p1, v0}, '+HELPER+'->addActions(Landroid/app/Activity;Landroid/widget/LinearLayout;Ljava/lang/String;)V',1)
    update('showCobraMultiTileActions',actions)
    def preview(s):
        full='    move-result-object v9\n\n    .line 2286'
        assert s.count(full)==1
        s=s.replace(full,'    move-result-object v9\n\n    const-string v10, "cobra_preview_fullscreen"\n\n    invoke-virtual {v9, v10}, Landroid/view/View;->setTag(Ljava/lang/Object;)V\n\n    .line 2286',1)
        anchor='    invoke-virtual {v0, p2, p1}, '+APP+'InfinityLiveActivity$CobraSix;->previewButton(Landroid/widget/LinearLayout;Landroid/widget/FrameLayout;)V'
        assert s.count(anchor)==1
        s=s.replace(anchor,anchor+'\n\n    invoke-static {p0, p2}, '+PRESENT+'->moreLast(Landroid/app/Activity;Landroid/widget/LinearLayout;)V',1)
        assert s.count('    return-object p1')==2
        return s.replace('    return-object p1','    invoke-static {p0, p1}, '+PRESENT+'->previewReused(Landroid/app/Activity;Landroid/widget/FrameLayout;)V\n\n    return-object p1')
    update('cobraPreviewPanel',preview)
    def pro_control(s):
        anchor='    invoke-virtual {v1, p1}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;\n\n    move-result-object p1'
        assert s.count(anchor)==1
        return s.replace(anchor,'    invoke-static {v1, p1}, '+PRESENT+'->proTarget(Landroid/view/ViewGroup;I)Landroid/view/View;\n\n    move-result-object p1\n\n    if-eqz p1, :cond_a',1)
    update('cobraProControl',pro_control)
    def position(s):
        head=s.split('\n',1)[0]
        return head+'''
    .registers 8
    invoke-static/range {p1 .. p5}, '''+PRESENT+'''->position(Landroid/view/View;IIII)V
    return-void
.end method
'''
    update('cobraPosition',position)
    def logo_request(s):
        return s.split('\n',1)[0]+"\n    .registers 3\n    invoke-static {p0, p1, p2}, "+APP+"CobraLogoRequests;->request(Landroid/app/Activity;Ljava/lang/String;Landroid/widget/ImageView;)V\n    return-void\n.end method\n"
    def logo_deliver(s):
        return s.split('\n',1)[0]+"\n    .registers 4\n    invoke-static {p0, p1, p2, p3}, "+APP+"CobraLogoRequests;->deliver(Landroid/app/Activity;Ljava/lang/String;Landroid/graphics/Bitmap;Landroid/widget/ImageView;)V\n    return-void\n.end method\n"
    update('cobraSportsLoadLogo',logo_request)
    update('lambda$cobraSportsLoadLogo$481$com-projectinfinity-kodi-InfinityLiveActivity',logo_deliver)
    def back(s):
        anchor='    .registers 7\n';assert s.count(anchor)==1
        return s.replace(anchor,anchor+'''
    invoke-static {p0}, '''+HELPER+'''->cancelActive(Landroid/app/Activity;)Z
    move-result v0
    if-eqz v0, :cobra_arrange_back_continue
    return-void
    :cobra_arrange_back_continue
''',1)
    update('onBackPressed',back)
    for signature,revised in changed.items():text=text.replace(before[signature],revised,1)
    # Preserve the exact Activity field set. The helper uses weak, UI-owned
    # references and view listener lifetimes rather than weakening DEX guards.
    after=methods(text)
    assert set(after)==set(before)
    assert {s for s in before if before[s]!=after[s]}==set(changed)
    return text,sorted(changed)


def build(bundles,jars,android,d8,out):
    bundles,jars,android,d8,out=(p.resolve() for p in (bundles,jars,android,d8,out))
    assert not out.exists();out.mkdir()
    scope=load(HERE/'SCOPE.json')
    authority=json.loads(subprocess.check_output(['git','-C',str(REPO),'show',scope['baseline_source']+':repairs/dual-experience-isolation-2103420/release-authority.json']))
    assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
    assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(REPO/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
    catalog=load(bundles/'catalog.json');source={};inputs=[]
    for owner in ('COBRA','CHOOSER_SHELL'):
        row=authority['bundle_catalog']['bundles'][owner]
        assert catalog['bundles'][owner]==row
        meta=read_bundle(bundles/row['file'],row)
        dest=out/'baseline'/owner;dest.mkdir(parents=True)
        with ZipFile(bundles/row['file']) as z:
            for leaf in meta['dex']:
                p=dest/Path(leaf).name;p.write_bytes(z.read(leaf));inputs.append(p)
                smali=dest/(p.stem+'-smali')
                run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',p,'-o',smali])
                for f in smali.rglob('*.smali'):
                    raw=f.read_text();name=raw.splitlines()[0].split()[-1]
                    assert sha(raw.encode())==meta['payload']['class:'+name]['sha256'],name
                    source[name]=raw
    changed=out/'changed/com/projectinfinity/kodi';changed.mkdir(parents=True)
    revised,selected=patch_activity(source[ACTIVITY]);(changed/'InfinityLiveActivity.smali').write_text(revised)
    component=source[APP+'CobraComponent;'];old='"bundled-2103420.isolation.1.fold-reflow.2"';assert component.count(old)==1
    (changed/'CobraComponent.smali').write_text(component.replace(old,'"'+VERSION+'"'))
    chooser=source[APP+'ChooserReleaseMetadata;'];assert chooser.count('"Last updated in "')==1
    (changed/'ChooserReleaseMetadata.smali').write_text(chooser.replace('"Last updated in "','"Version "',1))
    classes=out/'compiled';classes.mkdir()
    run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:all,-options,-deprecation',
         '-cp',android,'-d',classes,*sorted((HERE/'runtime').glob('*.java'))])
    with ZipFile(out/'helpers.jar','w') as z:
        for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes).as_posix())
    helper=out/'helper-dex';helper.mkdir()
    run(['java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',helper,out/'helpers.jar'])
    run(['java','-cp',str(jars/'*'),'org.jf.smali.Main','assemble','--api','21',out/'changed','-o',out/'changed.dex'])
    run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',helper/'classes.dex','-o',out/'helper-smali'])
    assignments={name:authority['payload']['class:'+name]['owner'] for name in source}
    for f in (out/'helper-smali').rglob('*.smali'):assignments[f.read_text().splitlines()[0].split()[-1]]='COBRA'
    (out/'assignments.tsv').write_text(''.join(n+'\t'+o+'\n' for n,o in sorted(assignments.items())))
    (out/'origins.tsv').write_text(''.join(APP+n+';\t'+APP+n+';\n' for n in ('InfinityLiveActivity','CobraComponent','ChooserReleaseMetadata')))
    host=out/'host';host.mkdir();cp=':'.join(map(str,sorted(jars.glob('*.jar'))))
    run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',cp,'-d',host,ISO/'ModuleDexWriter.java'])
    run(['java','-cp',str(host)+':'+cp,'org.jf.dexlib2.writer.pool.ModuleDexWriter',out/'owner-dex',out/'assignments.tsv',out/'origins.tsv',out/'changed.dex',helper/'classes.dex',*inputs])
    save(out/'BUILD.json',dict(status='COMPILED_UNSIGNED_COBRA_AND_NARROW_CHOOSER_ONLY',selected_activity_methods=selected,unchanged_activity_methods=len(methods(source[ACTIVITY]))-len(selected),baseline_class_count=len(source),Cobra_version=VERSION,runtime_source_sha256={p.name:file_sha(p) for p in sorted((HERE/'runtime').glob('*.java'))},source_budget_sha256=file_sha(HERE/'SOURCE-BUDGET.json'),Infinity='EXACT_FROZEN_BUNDLE',shutdown='NOT_RUN_FROZEN',user_data_modified=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('bundles','jars','android','d8','out'):parser.add_argument('--'+name,type=Path,required=True)
    build(**vars(parser.parse_args()))
