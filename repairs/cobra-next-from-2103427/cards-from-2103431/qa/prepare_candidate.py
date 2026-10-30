"""Host-only Activity prototype overlay on freshly pinned signed431 dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
APK_SHA='3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
SOURCE='9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
PROTOTYPE_SHA='f3fe97407023881be8457c60d61da8189c93b0546010fb8dc34787869aa88dd1'
ACTIVITY='com/projectinfinity/kodi/InfinityLiveActivity.class'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def methods(source):
    return {m[1]:m[0]+'\n' for m in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method',source,re.M|re.S)}


def classes(path):
    with ZipFile(path) as jar:return {n:jar.read(n) for n in jar.namelist() if n.endswith('.class')}


def prepare(baseline,prototype,baseline_smali,prototype_smali,dex2jar,jars,out):
    baseline=baseline.resolve();out=out.resolve();prototype=prototype.resolve();dex2jar=dex2jar.resolve()
    receipt=json.loads((baseline/'INPUTS.json').read_text())
    assert receipt['source']==SOURCE and receipt['APK_sha256']==APK_SHA and receipt['versionCode']==2103431
    for name,pin in receipt['DEX_sha256'].items():assert sha(baseline/name)==pin,name
    for name,pin in receipt['translated_jar_SHA256'].items():assert sha(baseline/(Path(name).stem+'-translated.jar'))==pin,name
    assert sha(prototype)==PROTOTYPE_SHA,'Only reviewed assembled Activity prototype admitted'
    budget_path=HERE.parent/'PROJECTION-SOURCE-BUDGET.json';budget=json.loads(budget_path.read_text())
    assert budget['baseline_signed_source']==SOURCE
    jars=jars.resolve()
    tool_pins={'baksmali-2.5.2.jar':'1ed236266d7dc4907aade0b19a34f77efac25342b63c8ace52e579039941b389',
               'dexlib2-2.5.2.jar':'5a5c8982d8bd7d6e3bb1a0713049e3c78b719ec32b20f6b619885cec30a0dd61'}
    for name,pin in tool_pins.items():assert sha(jars/name)==pin,name
    # Bind canonical source to fresh disassembly of the exact accepted APK DEX,
    # not the older pre-assembly source (whose labels/formatting normalize).
    with tempfile.TemporaryDirectory(prefix='accepted431-source-proof-',dir=out.parent) as scratch:
        subprocess.run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble',
          '--sequential-labels','--classes','Lcom/projectinfinity/kodi/InfinityLiveActivity;',
          str(baseline/'classes4.dex'),'-o',scratch],check=True)
        fresh=Path(scratch)/'com/projectinfinity/kodi/InfinityLiveActivity.smali'
        assert sha(fresh)==sha(baseline_smali),'Canonical baseline source does not match accepted431 DEX'
        before_text=fresh.read_text()
        fresh_source_sha=sha(fresh)
    after_text=prototype_smali.read_text()
    before=methods(before_text);after=methods(after_text)
    assert set(before)==set(after),'No method additions/deletions permitted'
    changed=sorted(k for k in before if before[k]!=after[k])
    assert changed==sorted(budget['changed_methods'])
    for signature,pin in {**budget['selected_method_preimages'],**budget['read_only_assumption_preimages']}.items():
        assert hashlib.sha256(before[signature].encode()).hexdigest()==pin,signature
    strip=lambda s:re.sub(r'^\.method [^\n]+\n.*?^\.end method','',s,flags=re.M|re.S)
    assert strip(before_text)==strip(after_text),'Fields/class metadata must be unchanged'
    original_test=HERE/'results/signed431-baseline/CobraProjectionBenchmarkTest-BASELINE.java'
    assert sha(original_test)==receipt['test_SHA256'],'Original tested baseline Java source must remain exact'
    current_test=HERE/'CobraProjectionBenchmarkTest.java'
    semantic=lambda p:p.read_text().split('  @Test public void nextProjectionReflectsFiltersHiddenFavoritesRecentsInventoryAndProfile()',1)[1]
    assert semantic(original_test)==semantic(current_test),'Same semantic test scenarios required'
    out.mkdir(parents=True,exist_ok=False)
    errors=out/'translation-errors';errors.mkdir()
    translated=out/'prototype-Activity.jar'
    subprocess.run(['java','-cp',str(dex2jar/'lib/*'),'com.googlecode.dex2jar.tools.Dex2jarCmd',str(prototype),'-o',str(translated),'-e',str(errors/'prototype.zip')],check=True)
    assert not list(errors.iterdir()),'Activity prototype translation errors refused'
    overlay=classes(translated);assert set(overlay)=={ACTIVITY},'Only Activity class may be translated from prototype'
    base=classes(baseline/'production.jar');assert ACTIVITY in base
    with ZipFile(out/'production.jar','w',ZIP_DEFLATED) as merged:
        for name,content in base.items():merged.writestr(name,overlay.get(name,content))
    actual=classes(out/'production.jar');assert set(actual)==set(base)
    changed_classes=[name for name in base if actual[name]!=base[name]]
    assert changed_classes==[ACTIVITY],'All other production class bytes must be identical'
    for name in ('support.jar',):shutil.copyfile(baseline/name,out/name);assert sha(out/name)==sha(baseline/name)
    shutil.copytree(baseline/'android-test-libs',out/'android-test-libs')
    for p in (baseline/'android-test-libs').iterdir():assert sha(out/'android-test-libs'/p.name)==sha(p)
    target=out/'src/test/java/com/projectinfinity/kodi';target.mkdir(parents=True)
    shutil.copyfile(current_test,target/current_test.name)
    # Dependencies/protocol stay exact; only paths, phase and explicitly selected work-count expectations differ.
    pom=(baseline/'pom.xml').read_text().replace(str(baseline),str(out))
    pom=pom.replace('<projection.output>','<projection.phase>UNSIGNED_SINGLE_ACTIVITY_PROTOTYPE_V2_NO_APK</projection.phase><projection.expected.hidden.reads>1</projection.expected.hidden.reads><projection.expected.default.sets>1</projection.expected.default.sets><projection.output>')
    (out/'pom.xml').write_text(pom)
    record={'phase':'UNSIGNED_SINGLE_ACTIVITY_PROTOTYPE_V2_NO_APK','baseline_signed_source':SOURCE,'baseline_APK_sha256':APK_SHA,
      'baseline_INPUTS_sha256':sha(baseline/'INPUTS.json'),'baseline_DEX_sha256':receipt['DEX_sha256'],
      'prototype_DEX_sha256':sha(prototype),'prototype_smali_sha256':sha(prototype_smali),'baseline_smali_sha256':sha(baseline_smali),'fresh_accepted_DEX_disassembly_sha256':fresh_source_sha,'baksmali_tool_sha256':tool_pins,
      'patch_source_sha256':sha(HERE.parent/'projection_patch.py'),'method_budget_sha256':sha(budget_path),
      'changed_methods':changed,'method_count':len(before),'all_other_method_and_class_metadata_identical':True,
      'changed_translated_classes':changed_classes,'all_other_translated_production_class_bytes_identical':True,
      'unchanged_translated_class_count':len(base)-1,'support_jar_exact':sha(out/'support.jar'),
      'original_baseline_test_sha256':sha(original_test),'test_sha256':sha(current_test),'semantic_scenarios_unchanged':True,
      'additional_non_timed_assertion':'Input inventory size, order and object identities unchanged after each semantic projection',
      'expected_hidden_reads':1,'expected_default_sets':1,'warmups_per_entry':2,'timed_samples_per_entry':7,
      'application_APK':'NOT_BUILT_OR_MODIFIED','physical_Fold':'NOT_RUN','shutdown':'NOT_RUN'}
    (out/'INPUTS.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('baseline','prototype','baseline-smali','prototype-smali','dex2jar','jars','out'):
        parser.add_argument('--'+name,type=Path,required=True)
    prepare(**vars(parser.parse_args()))
