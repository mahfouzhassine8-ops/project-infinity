"""Prepare a reviewed parsed-data host prototype. No APK or test execution."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
APK_SHA='3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
ACTIVITY='com/projectinfinity/kodi/InfinityLiveActivity.class'
FEATURE='com/projectinfinity/kodi/InfinityCobraFeatureRuntime.class'
HELPER_CLASSES={'com/projectinfinity/kodi/CobraProfileDataReuse.class','com/projectinfinity/kodi/CobraProfileDataReuse$Entry.class'}
ANDROID_SHA='6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad'
D8_SHA='305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5'
V2='f3fe97407023881be8457c60d61da8189c93b0546010fb8dc34787869aa88dd1'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def classes(path):
    with ZipFile(path) as archive:return {n:archive.read(n) for n in archive.namelist() if n.endswith('.class')}


def run(command):subprocess.run(list(map(str,command)),check=True)


def prepare(baseline,projection,android,d8,jars,dex2jar,out):
    baseline=baseline.resolve();projection=projection.resolve();out=out.resolve()
    budget=json.loads((HERE/'SOURCE-BUDGET.json').read_text())
    b=json.loads((baseline/'INPUTS.json').read_text());v2=json.loads((projection/'INPUTS.json').read_text())
    assert b['APK_sha256']==budget['baseline_APK_sha256']==APK_SHA
    assert v2['baseline_APK_sha256']==APK_SHA and v2['prototype_DEX_sha256']==V2
    for name,pin in b['DEX_sha256'].items():assert sha(baseline/name)==pin
    assert sha(android)==ANDROID_SHA and sha(d8)==D8_SHA,'Pinned Android compiler inputs required'
    before=classes(baseline/'production.jar');projected=classes(projection/'production.jar')
    assert set(before)==set(projected)
    assert [name for name in before if before[name]!=projected[name]]==[ACTIVITY]
    assert sha(baseline/'support.jar')==sha(projection/'support.jar')
    out.mkdir(parents=True,exist_ok=False)
    smali=out/'baseline-canonical'
    run(['java','-cp',jars/'*','org.jf.baksmali.Main','disassemble','--sequential-labels',
      '--classes','Lcom/projectinfinity/kodi/InfinityCobraFeatureRuntime;',baseline/'classes4.dex','-o',smali])
    original=smali/'com/projectinfinity/kodi/InfinityCobraFeatureRuntime.smali'
    assert sha(original)==budget['feature_class_sha256']
    assert original.read_text().startswith('.class public final '),'Subclass profiles override must remain impossible'
    spec=importlib.util.spec_from_file_location('profile_data_patch',HERE/'patch_feature.py');patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    changed_text=patch.patch(original.read_text())
    target=out/'feature-smali/com/projectinfinity/kodi/InfinityCobraFeatureRuntime.smali';target.parent.mkdir(parents=True);target.write_text(changed_text)
    run(['java','-cp',jars/'*','org.jf.smali.Main','assemble',out/'feature-smali','-o',out/'feature.dex'])
    compiled=out/'helper-classes';compiled.mkdir()
    source=HERE/'runtime/CobraProfileDataReuse.java'
    compiler=[shutil.which('javac')] if shutil.which('javac') else ['java','-m','jdk.compiler/com.sun.tools.javac.Main']
    run(compiler+['-source','8','-target','8','-cp',android,'-d',compiled,source])
    actual={str(p.relative_to(compiled)) for p in compiled.rglob('*.class')}
    assert actual==HELPER_CLASSES,'Only two admitted helper class files are permitted'
    helper_jar=out/'helper-classes.jar'
    with ZipFile(helper_jar,'w',ZIP_DEFLATED) as archive:
        for p in compiled.rglob('*.class'):archive.write(p,p.relative_to(compiled))
    helper_dex=out/'helper-dex';helper_dex.mkdir()
    run(['java','-cp',d8,'com.android.tools.r8.D8','--min-api','23','--lib',android,'--output',helper_dex,helper_jar])
    assert {p.name for p in helper_dex.iterdir()}=={'classes.dex'}
    errors=out/'translation-errors';errors.mkdir()
    translated={}
    for name,dex in [('feature',out/'feature.dex'),('helper',helper_dex/'classes.dex')]:
        path=out/(name+'-translated.jar')
        run(['java','-cp',dex2jar/'lib/*','com.googlecode.dex2jar.tools.Dex2jarCmd',dex,'-o',path,'-e',errors/(name+'.zip')])
        translated[name]=path
    assert not list(errors.iterdir()),'Prototype translation errors refused'
    feature_classes=classes(translated['feature']);helper_classes=classes(translated['helper'])
    assert set(feature_classes)=={FEATURE} and set(helper_classes)==HELPER_CLASSES
    assert not (set(helper_classes)&set(before)),'No helper may replace an existing class'
    merged=dict(projected);merged.update(feature_classes);merged.update(helper_classes)
    assert set(merged)-set(before)==HELPER_CLASSES
    changed_existing=sorted(n for n in before if merged[n]!=before[n])
    assert changed_existing==sorted([ACTIVITY,FEATURE]),'Only the two admitted existing classes may differ'
    with ZipFile(out/'production.jar','w',ZIP_DEFLATED) as archive:
        for name,raw in merged.items():archive.writestr(name,raw)
    for name in ('support.jar',):shutil.copyfile(baseline/name,out/name);assert sha(out/name)==sha(baseline/name)
    shutil.copytree(baseline/'android-test-libs',out/'android-test-libs')
    test_folder=out/'src/test/java/com/projectinfinity/kodi';test_folder.mkdir(parents=True)
    tests=[HERE/'tests/CobraProfileDataReuseTest.java',HERE.parent/'qa/CobraProjectionBenchmarkTest.java']
    for test in tests:shutil.copyfile(test,test_folder/test.name)
    pom=(baseline/'pom.xml').read_text().replace(str(baseline),str(out))
    properties='<projection.phase>UNSIGNED_PROFILE_DATA_REUSE_PROTOTYPE_NO_APK</projection.phase><projection.expected.hidden.reads>1</projection.expected.hidden.reads><projection.expected.default.sets>1</projection.expected.default.sets><profile.helper.expected>true</profile.helper.expected>'
    (out/'pom.xml').write_text(pom.replace('<systemPropertyVariables>','<systemPropertyVariables>'+properties))
    # Prepare baseline classpath for the same six new API/data-parity tests; do not execute it.
    parity=out/'baseline-parity';parity.mkdir()
    for name in ('production.jar','support.jar'):shutil.copyfile(baseline/name,parity/name)
    shutil.copytree(baseline/'android-test-libs',parity/'android-test-libs')
    dest=parity/'src/test/java/com/projectinfinity/kodi';dest.mkdir(parents=True)
    shutil.copyfile(tests[0],dest/tests[0].name)
    (parity/'pom.xml').write_text((baseline/'pom.xml').read_text().replace(str(baseline),str(parity)))
    old_methods=patch.methods(original.read_text());new_methods=patch.methods(changed_text)
    record={'phase':'HOST_ONLY_UNSIGNED_PARSED_PROFILE_DATA_REUSE_PROTOTYPE','baseline_source':budget['baseline_signed_source'],
      'baseline_APK_sha256':APK_SHA,'baseline_DEX_sha256':b['DEX_sha256'],'projection_V2_DEX_sha256':V2,
      'Feature_class_canonical_sha256':sha(original),'Feature_final_modifier_verified':True,
      'Feature_method_count':len(old_methods),'Feature_changed_methods':[k for k in old_methods if old_methods[k]!=new_methods[k]],
      'Feature_all_other_methods_fields_annotations_exact':True,'public_profiles_method_exact':True,
      'feature_DEX_sha256':sha(out/'feature.dex'),'helper_DEX_sha256':sha(helper_dex/'classes.dex'),
      'helper_source_sha256':sha(source),'helper_classes':sorted(helper_classes),
      'changed_existing_translated_classes':changed_existing,'all_other_existing_class_bytes_exact':True,
      'unchanged_existing_class_count':len(before)-len(changed_existing),'new_classes':sorted(helper_classes),
      'runtime_policy':'Fresh activeProfileId then fresh profiles raw preference on EVERY call; private parsed data only; no policy boolean cache',
      'compiler_inputs':{'android_jar_sha256':sha(android),'D8_jar_sha256':sha(d8)},
      'test_sources_sha256':{p.name:sha(p) for p in tests},
      'application_APK':'NOT_BUILT_OR_MODIFIED','tests':'NOT_RUN_AWAITING_PEER_REVIEW','physical_Fold':'NOT_RUN','shutdown':'NOT_RUN'}
    (out/'INPUTS.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('baseline','projection','android','d8','jars','dex2jar','out'):parser.add_argument('--'+name,type=Path,required=True)
    prepare(**vars(parser.parse_args()))
