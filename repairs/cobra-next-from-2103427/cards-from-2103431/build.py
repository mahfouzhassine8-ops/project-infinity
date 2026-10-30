"""Compile the Cards/performance delta from exact signed431 Cobra-owned DEX.

The established owner writer, compiler pins and original component architecture
are retained. This emits owner DEX only; no APK, signing or app execution.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ISO=REPO/'repairs/dual-experience-isolation-2103420'
sys.path.insert(0,str(ISO))
from inventory import load,save,file_sha,APP
from component_bundles import read_bundle
from compile_runtime import ANDROID_SHA,D8_SHA
import cards_patch
import projection_patch
import presentation_patch

VERSION='2103432.cobra.1'
BASE_SOURCE='9ccc4c362a65118eeba38a8e7e4b0de5723c69af'


def run(args): subprocess.run(list(map(str,args)),check=True)
def sha(raw): return hashlib.sha256(raw).hexdigest()


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded)
    return loaded


def classes(path):
    with ZipFile(path) as z:return {n:z.read(n) for n in z.namelist() if n.endswith('.class')}


def compiler_sources():
    files=[HERE/'build.py',HERE/'cards_patch.py',HERE/'projection_patch.py',HERE/'presentation_patch.py',
      HERE/'CARDS-SOURCE-BUDGET.json',HERE/'PROJECTION-SOURCE-BUDGET.json',HERE/'DEX2JAR-LIB-PINS.json',
      HERE/'BASELINE.json',HERE/'SCOPE.json',HERE/'logo-clear/patch.py',HERE/'logo-clear/SOURCE-BUDGET.json',
      HERE/'profile-reads/patch_feature.py',HERE/'profile-reads/SOURCE-BUDGET.json',
      HERE/'profile-reads/runtime/CobraProfileDataReuse.java',HERE/'cards-reuse/patch.py',HERE/'cards-reuse/SOURCE-BUDGET.json',
      HERE/'cards-reuse/runtime/CobraCardsReuse.java',ISO/'ModuleDexWriter.java']
    return sorted(set(files+list((HERE/'runtime').glob('*.java'))))


def build(bundles,jars,android,d8,dex2jar,out):
    bundles,jars,android,d8,dex2jar,out=(p.resolve() for p in (bundles,jars,android,d8,dex2jar,out))
    assert not out.exists();out.mkdir()
    source_files={str(p.relative_to(REPO)):file_sha(p) for p in compiler_sources()}
    for relative,pin in source_files.items():
        frozen=out/'compiler-source-snapshot'/relative
        frozen.parent.mkdir(parents=True,exist_ok=True);frozen.write_bytes((REPO/relative).read_bytes())
        assert file_sha(frozen)==pin,'Exact immutable compiler input snapshot required'
    assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
    assert {p.name:file_sha(p) for p in jars.glob('*.jar')}==load(REPO/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
    assert {p.name:file_sha(p) for p in (dex2jar/'lib').glob('*.jar')}==load(HERE/'DEX2JAR-LIB-PINS.json')
    authority=json.loads(subprocess.check_output(['git','-C',str(REPO),'show',BASE_SOURCE+':repairs/dual-experience-isolation-2103420/release-authority.json']))
    assert authority['generation']==16 and authority['candidate_versionCode']==2103431
    catalog=load(bundles/'catalog.json');assert catalog==authority['bundle_catalog']
    recovery=load(HERE/'BASELINE.json')
    for owner,row in catalog['bundles'].items():
        assert file_sha(bundles/row['file'])==recovery['component_sha256'][row['file']]
        read_bundle(bundles/row['file'],row)
    row=catalog['bundles']['COBRA'];meta=read_bundle(bundles/row['file'],row)
    baseline=out/'baseline/COBRA';baseline.mkdir(parents=True)
    sources={};inputs=[]
    with ZipFile(bundles/row['file']) as z:
        for leaf in sorted(meta['dex']):
            dex=baseline/Path(leaf).name;dex.write_bytes(z.read(leaf));inputs.append(dex)
            assert file_sha(dex)==meta['dex'][leaf]
            dest=baseline/(dex.stem+'-smali')
            run(['java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',dest])
            for p in dest.rglob('*.smali'):
                raw=p.read_text();name=raw.splitlines()[0].split()[-1]
                assert name not in sources and sha(raw.encode())==meta['payload']['class:'+name]['sha256']
                sources[name]=raw
    activity=APP+'InfinityLiveActivity;';card=APP+'InfinityLiveActivity$CobraPosterChannelCard;'
    feature=APP+'InfinityCobraFeatureRuntime;';logo=APP+'CobraLogoRequests;';component=APP+'CobraComponent;'
    revised={}
    projected=projection_patch.patch_activity(sources[activity])
    presented=presentation_patch.patch_activity(projected)
    staged=cards_patch.patch_activity(presented)
    revised[activity]=module('cards_reuse_patch',HERE/'cards-reuse/patch.py').patch_activity(staged)
    revised[card]=cards_patch.patch_card(sources[card])
    revised[feature]=module('cards_profile_patch',HERE/'profile-reads/patch_feature.py').patch(sources[feature])
    revised[logo]=module('cards_logo_clear_patch',HERE/'logo-clear/patch.py').patch(sources[logo])
    assert sources[component].count('"2103431.cobra.1"')==1
    revised[component]=sources[component].replace('"2103431.cobra.1"','"'+VERSION+'"',1)
    changed=out/'changed';changed.mkdir()
    for name,raw in revised.items():
        target=changed/(name[1:-1]+'.smali');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(raw)
    run(['java','-cp',jars/'*','org.jf.smali.Main','assemble','--api','21',changed,'-o',out/'changed.dex'])
    # Compile against actual accepted Cobra classes plus its add-only clear API.
    # No fake Java classes or recompiled old helpers replace the baseline.
    api_smali=out/'api-smali/com/projectinfinity/kodi/CobraLogoRequests.smali';api_smali.parent.mkdir(parents=True)
    api_smali.write_text(revised[logo])
    run(['java','-cp',jars/'*','org.jf.smali.Main','assemble',out/'api-smali','-o',out/'api-clear.dex'])
    api={};translation=out/'translation';translation.mkdir()
    for i,dex in enumerate([*inputs,out/'api-clear.dex']):
        target=translation/('api-'+str(i)+'.jar');errors=translation/('errors-'+str(i)+'.zip')
        run(['java','-cp',dex2jar/'lib/*','com.googlecode.dex2jar.tools.Dex2jarCmd',dex,'-o',target,'-e',errors])
        assert not errors.exists(),'Actual Cobra compile-ABI translation must be complete'
        new=classes(target)
        if dex==out/'api-clear.dex':assert set(new)=={'com/projectinfinity/kodi/CobraLogoRequests.class'}
        else:assert not set(new)&set(api)
        api.update(new)
    api_jar=out/'compile-api.jar'
    with ZipFile(api_jar,'w',ZIP_DEFLATED) as z:
        for name,raw in api.items():z.writestr(name,raw)
    helpers=[HERE/'runtime/CobraCardsTiles.java',HERE/'runtime/CobraCardsLayout.java',HERE/'profile-reads/runtime/CobraProfileDataReuse.java',HERE/'cards-reuse/runtime/CobraCardsReuse.java']
    assert all(p.is_file() for p in helpers),'No substitute for incomplete approved Cards implementation'
    helper_sources={str(p.relative_to(REPO)):file_sha(p) for p in helpers}
    compiled=out/'compiled';compiled.mkdir()
    run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:all,-options,-deprecation',
         '-cp',str(android)+':'+str(api_jar),'-d',compiled,*helpers])
    roots={'CobraCardsTiles','CobraCardsLayout','CobraProfileDataReuse','CobraCardsReuse'}
    assert all(p.stem.split('$')[0] in roots for p in compiled.rglob('*.class'))
    with ZipFile(out/'helpers.jar','w',ZIP_DEFLATED) as z:
        for p in compiled.rglob('*.class'):z.write(p,p.relative_to(compiled).as_posix())
    helper_dex=out/'helper-dex';helper_dex.mkdir()
    run(['java','-cp',d8,'com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',helper_dex,out/'helpers.jar'])
    assert helper_sources=={str(p.relative_to(REPO)):file_sha(p) for p in helpers},'Source mutation during compilation refused'
    assert {p.name for p in helper_dex.iterdir()}=={'classes.dex'}
    helper_smali=out/'helper-smali'
    run(['java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',helper_dex/'classes.dex','-o',helper_smali])
    layout_methods=projection_patch.methods((helper_smali/'com/projectinfinity/kodi/CobraCardsLayout.smali').read_text())
    assert {'public static beforeShell(Landroid/app/Activity;)V','public static layout(Landroid/app/Activity;Ljava/lang/Object;)V',
        'public static afterRender(Landroid/app/Activity;)V','public static refreshDetails(Landroid/app/Activity;)Z',
        'public static refreshPreview(Landroid/app/Activity;)V',
        'public static ambientSurface(Landroid/app/Activity;Landroid/view/View;IIIZ)Z'}<=set(layout_methods),'Exact Cards native hook API required'
    assignments={name:'COBRA' for name in sources}
    for p in helper_smali.rglob('*.smali'):
        name=p.read_text().splitlines()[0].split()[-1];assert name not in assignments;assignments[name]='COBRA'
    (out/'assignments.tsv').write_text(''.join(n+'\t'+o+'\n' for n,o in sorted(assignments.items())))
    (out/'origins.tsv').write_text(''.join(n+'\t'+n+'\n' for n in sorted(revised)))
    host=out/'host';host.mkdir();cp=':'.join(map(str,sorted(jars.glob('*.jar'))))
    run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-Xlint:-options','-cp',cp,'-d',host,ISO/'ModuleDexWriter.java'])
    run(['java','-cp',str(host)+':'+cp,'org.jf.dexlib2.writer.pool.ModuleDexWriter',out/'owner-dex',out/'assignments.tsv',out/'origins.tsv',out/'changed.dex',helper_dex/'classes.dex',*inputs])
    method_changes={}
    for name,raw in revised.items():
        old_methods=projection_patch.methods(sources[name]);new_methods=projection_patch.methods(raw)
        method_changes[name]=sorted(s for s in old_methods if old_methods[s]!=new_methods.get(s))
    assert source_files=={str(p.relative_to(REPO)):file_sha(p) for p in compiler_sources()},'Source mutation during owner compilation refused'
    save(out/'BUILD.json',dict(status='COMPILED_UNSIGNED_COBRA_OWNER_ONLY',baseline_signed_source=BASE_SOURCE,baseline_components=catalog,
         candidate_component_version=VERSION,changed_classes=sorted(revised),source_method_changes=method_changes,
         new_classes=sorted(set(assignments)-set(sources)),helper_sources=helper_sources,compiler_source_files=source_files,
         compile_API_jar_sha256=file_sha(api_jar),Infinity='FROZEN_ZIP',minimal_Android='FROZEN_ZIP',chooser='NO_CODE_OR_DEX_CHANGE; later genuine-version metadata only',shutdown='FROZEN_NOT_RUN',APK='NOT_BUILT'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('bundles','jars','android','d8','dex2jar','out'):parser.add_argument('--'+name,type=Path,required=True)
    build(**vars(parser.parse_args()))
