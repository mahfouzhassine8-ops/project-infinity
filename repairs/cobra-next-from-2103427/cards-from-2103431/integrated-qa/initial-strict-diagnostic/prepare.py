"""Strict actual-owner-DEX host preparation. No behavioral execution or APK build.

All original class bytes must match the exact accepted431 translations except
five explicitly admitted classes. No translation difference is normalized away.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
SIGNED_SOURCE='9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
SIGNED_APK='3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
BASE_DEX={
 'classes.dex':'07b94bfde6dbc3e3a6bfc8436ea65e6a67bdef5ca868379809e20f2fb7ce8efb',
 'classes2.dex':'2e8fa1ae27e670db0525d31a655e93d861893fa20316d5c54a4c6283a97ca304',
 'classes3.dex':'7e18d8092de33a4d44e299305965e9b9eb943372a9643452f6f78afe209fb215',
 'classes4.dex':'9f82b0420b32ad8bdda7ef042e44bb975c8c01663f66506eaf33d22123f49b82',
 'classes5.dex':'af03db41f53209de52f5d8609e411da49fee106d0fe544d6ea6e5d8230d88363'}
OWNER_DEX={
 'part-0.dex':'1454943187ff782b48908bfa5aaf1c240b6db1fa99396f4ee0ed86e5215c0230',
 'part-1.dex':'be8e25e898a95a42a552b161ae52f399cb562c3cbcf7273ed4a10f7ad7e1acae'}
CHANGED={
 'com/projectinfinity/kodi/InfinityLiveActivity.class',
 'com/projectinfinity/kodi/InfinityLiveActivity$CobraPosterChannelCard.class',
 'com/projectinfinity/kodi/InfinityCobraFeatureRuntime.class',
 'com/projectinfinity/kodi/CobraLogoRequests.class',
 'com/projectinfinity/kodi/CobraComponent.class'}
HELPER_ROOTS={'com/projectinfinity/kodi/CobraCardsLayout',
              'com/projectinfinity/kodi/CobraCardsTiles',
              'com/projectinfinity/kodi/CobraProfileDataReuse'}
EXCLUDED=('com/google/common/','com/google/thirdparty/')
NATIVE_DEPS={
 'nativeruntime':('4.14.1','nativeruntime-4.14.1.jar'),
 'nativeruntime-dist-compat':('1.0.16','nativeruntime-dist-compat-1.0.16.jar')}


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def digest(raw):return hashlib.sha256(raw).hexdigest()


def class_name(descriptor):
    assert descriptor.startswith('Lcom/projectinfinity/kodi/') and descriptor.endswith(';')
    return descriptor[1:-1]+'.class'


def read_classes(paths):
    result={}
    for path in paths:
        with ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith('.class'):continue
                raw=archive.read(name)
                assert name not in result,'Duplicate translated class: '+name
                result[name]=raw
    return result


def prepare(baseline,build,dex2jar,out):
    baseline=baseline.resolve();build=build.resolve();dex2jar=dex2jar.resolve();out=out.resolve()
    baseline_receipt=json.loads((baseline/'INPUTS.json').read_text())
    build_receipt=json.loads((build/'BUILD.json').read_text())
    assert baseline_receipt['source']==build_receipt['baseline_signed_source']==SIGNED_SOURCE
    assert baseline_receipt['APK_sha256']==SIGNED_APK and baseline_receipt['DEX_sha256']==BASE_DEX
    assert baseline_receipt['versionCode']==2103431
    assert build_receipt['status']=='COMPILED_UNSIGNED_COBRA_OWNER_ONLY' and build_receipt['APK']=='NOT_BUILT'
    assert {class_name(n) for n in build_receipt['changed_classes']}==CHANGED
    new_expected={class_name(n) for n in build_receipt['new_classes']}
    assert len(new_expected)==16
    assert {n[:-6].split('$',1)[0] for n in new_expected}==HELPER_ROOTS
    for name,pin in BASE_DEX.items():assert sha(baseline/name)==pin,name
    for name,pin in baseline_receipt['translated_jar_SHA256'].items():
        assert sha(baseline/(Path(name).stem+'-translated.jar'))==pin,name
    for name,pin in OWNER_DEX.items():assert sha(build/'owner-dex/COBRA'/name)==pin,name
    helper_sources={}
    for name,pin in build_receipt['helper_sources'].items():
        assert sha(REPO/name)==pin,'Source changed after owner build: '+name
        helper_sources[name]=pin
    full_original=read_classes([baseline/'classes4-translated.jar',baseline/'classes5-translated.jar'])
    original={n:raw for n,raw in full_original.items() if not n.startswith(EXCLUDED)}
    assert read_classes([baseline/'production.jar'])==original,'Baseline production must remain exact accepted431'
    support={}
    for part in ('classes-translated.jar','classes2-translated.jar','classes3-translated.jar'):
        with ZipFile(baseline/part) as archive:
            for n in archive.namelist():
                if (n.endswith('.class') and n.startswith(('com/projectinfinity/kodi/','androidx/'))
                        and not n.startswith(EXCLUDED)):
                    support.setdefault(n,archive.read(n))
    assert read_classes([baseline/'support.jar'])==support,'Baseline shared/Infinity support changed'
    out.mkdir(parents=True,exist_ok=False)
    binding={'status':'PREPARING_ACTUAL_OWNER_DEX_CLASSPATH','phase':'UNSIGNED_COBRA_OWNER_PROTOTYPE_V2_NO_APK',
      'baseline_signed_source':SIGNED_SOURCE,'baseline_APK_sha256':SIGNED_APK,
      'baseline_DEX_sha256':BASE_DEX,'owner_DEX_sha256':OWNER_DEX,
      'owner_BUILD_sha256':sha(build/'BUILD.json'),'owner_BUILD':build_receipt,
      'helper_source_sha256':helper_sources,'allowed_changed_existing_classes':sorted(CHANGED),
      'expected_new_helper_classes':sorted(new_expected),'behavioral_execution':'NOT_RUN',
      'application_APK':'NOT_BUILT_OR_MODIFIED','CI':'NOT_RUN','physical_Fold':'NOT_RUN','shutdown':'NOT_RUN'}
    def save():
        (out/'SOURCE-BINDINGS.json').write_text(json.dumps(binding,indent=2)+'\n')
    save();shutil.copyfile(build/'BUILD.json',out/'OWNER-BUILD.json')
    try:
        errors=out/'translation-errors';errors.mkdir();translated=[]
        for name in ('part-0.dex','part-1.dex'):
            source=build/'owner-dex/COBRA'/name
            target=out/(Path(name).stem+'-translated.jar');translated.append(target)
            with (out/(Path(name).stem+'-D2J.txt')).open('w') as log:
                completed=subprocess.run(['java','-cp',str(dex2jar/'lib/*'),
                  'com.googlecode.dex2jar.tools.Dex2jarCmd',str(source),'-o',str(target),'-e',str(errors/(name+'.zip'))],
                  stdout=log,stderr=subprocess.STDOUT)
            assert completed.returncode==0,'Actual owner DEX translation failed: '+name
        assert not list(errors.iterdir()),'Actual owner translation-error archives refused'
        full_candidate=read_classes(translated)
        new_detected=set(full_candidate)-set(full_original)
        missing=set(full_original)-set(full_candidate)
        actual_changed=sorted(n for n in full_original if n in full_candidate and full_original[n]!=full_candidate[n])
        unexpected=sorted(set(actual_changed)-CHANGED)
        diff={'baseline_full_class_count':len(full_original),'candidate_full_class_count':len(full_candidate),
          'changed_existing_classes':actual_changed,'unexpected_changed_existing_classes':unexpected,
          'new_classes':sorted(new_detected),'missing_classes':sorted(missing),
          'changed_class_sha256':{n:{'accepted431':digest(full_original[n]),'owner_v2':digest(full_candidate[n])} for n in actual_changed}}
        (out/'ACTUAL-CLASS-DIFF.json').write_text(json.dumps(diff,indent=2)+'\n')
        assert not missing,'Existing class disappeared from actual owner DEX'
        assert new_detected==new_expected,'Unexpected new helper class definitions'
        assert not unexpected,'Unselected class translation bytes differ: '+','.join(unexpected[:10])
        assert set(actual_changed)==CHANGED,'Five selected classes must be the exact changed set'
        candidate={n:raw for n,raw in full_candidate.items() if not n.startswith(EXCLUDED)}
        merged=dict(original)
        for n in CHANGED|new_expected:merged[n]=candidate[n]
        assert merged==candidate,'Overlay must exactly represent actual owner DEX class bytes'
        assert all(merged[n]==original[n] for n in original if n not in CHANGED)
        with ZipFile(out/'production.jar','w',ZIP_DEFLATED) as archive:
            for n,raw in merged.items():archive.writestr(n,raw)
        shutil.copyfile(baseline/'support.jar',out/'support.jar')
        assert sha(out/'support.jar')==sha(baseline/'support.jar')
        shutil.copytree(baseline/'android-test-libs',out/'android-test-libs')
        native={}
        for artifact,(version,name) in NATIVE_DEPS.items():
            jar=Path.home()/'.m2/repository/org/robolectric'/artifact/version/name
            assert jar.is_file(),'Official cached Robolectric native dependency missing: '+artifact
            native[artifact]={'version':version,'jar_sha256':sha(jar),'source':'Official org.robolectric Maven artifact; cached dependency, no APK inclusion'}
        # Explicit native-graphics dependencies reuse the accepted Robolectric4.14.1 platform.
        # No behavior is run here; future selected fixtures opt in with @GraphicsMode(NATIVE).
        pom=(baseline/'pom.xml').read_text().replace(str(baseline),str(out))
        deps=''.join('<dependency><groupId>org.robolectric</groupId><artifactId>'+a+'</artifactId><version>'+v+'</version><scope>test</scope></dependency>' for a,(v,_) in NATIVE_DEPS.items())
        pom=pom.replace('</dependencies>',deps+'</dependencies>')
        pom=pom.replace('projection.output','integrated.output')
        (out/'pom.xml').write_text(pom)
        (out/'src/test/java/com/projectinfinity/kodi').mkdir(parents=True)
        fixtures=out/'fixtures-not-selected';fixtures.mkdir()
        fixture_source=HERE.parent/'settings-return/CobraSettingsReturnBaselineTest.java'
        shutil.copyfile(fixture_source,fixtures/fixture_source.name)
        binding.update(status='PASS_STRICT_ACTUAL_OWNER_DEX_CLASSPATH_PREPARED_NO_TESTS',
          changed_existing_classes=actual_changed,new_helper_classes=sorted(new_detected),
          unchanged_baseline_host_class_count=len(original)-len(CHANGED),
          unchanged_full_owner_translated_class_count=len(full_original)-len(CHANGED),
          production_jar_sha256=sha(out/'production.jar'),support_jar_sha256=sha(out/'support.jar'),
          translated_owner_jar_sha256={p.name:sha(p) for p in translated},
          native_graphics_dependencies=native,pom_sha256=sha(out/'pom.xml'),
          fixture_source={'path':str(fixture_source),'sha256':sha(fixture_source),'copied_to':'fixtures-not-selected/'+fixture_source.name,
                          'execution':'NOT_SELECTED_OR_RUN; shared actual native buildShell/ShowGuideShell foundation'},
          prepare_source_sha256=sha(Path(__file__)))
        save();print(json.dumps({k:v for k,v in binding.items() if k!='owner_BUILD'},indent=2))
    except Exception as failure:
        binding['status']='FAILED_CLOSED_ACTUAL_DEX_PREPARATION';binding['error']=str(failure);save();raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('baseline','build','dex2jar','out'):parser.add_argument('--'+name,type=Path,required=True)
    prepare(**vars(parser.parse_args()))
