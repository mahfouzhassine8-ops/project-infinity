"""Fixed four-run host comparison after the preserved V1 timing regression."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
V2='f3fe97407023881be8457c60d61da8189c93b0546010fb8dc34787869aa88dd1'
ORDER=('B431','C2','C2','B431')
ENTRIES=('cobraChannelsForCurrentView','cobraGuideChannels')


def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def classes(p):
    with ZipFile(p) as z:return {n:z.read(n) for n in z.namelist() if n.endswith('.class')}


def stats(values):
    x=sorted(values);n=len(x)
    return {'N':n,'p50_ms':x[n//2] if n%2 else (x[n//2-1]+x[n//2])/2,
            'p95_ms':x[math.ceil(n*0.95)-1],'minimum_ms':x[0],'maximum_ms':x[-1]}


def run(baseline,candidate,maven,out):
    baseline=baseline.resolve();candidate=candidate.resolve();out=out.resolve()
    selected=json.loads((HERE/'ABBA-MEASUREMENT-SCOPE.json').read_text())
    assert selected['selected_before_execution'] and selected['fixed_run_order']==list(ORDER)
    assert selected['warmups_per_entry_per_run']==selected['samples_per_entry_per_run']==21
    b=json.loads((baseline/'INPUTS.json').read_text());c=json.loads((candidate/'INPUTS.json').read_text())
    assert b['source']=='9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
    assert b['APK_sha256']==c['baseline_APK_sha256']=='3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
    assert c['prototype_DEX_sha256']==V2
    for name,pin in b['DEX_sha256'].items():assert sha(baseline/name)==pin
    before=classes(baseline/'production.jar');after=classes(candidate/'production.jar')
    assert set(before)==set(after)
    assert [n for n in before if before[n]!=after[n]]==['com/projectinfinity/kodi/InfinityLiveActivity.class']
    assert sha(baseline/'support.jar')==sha(candidate/'support.jar')
    test=HERE/'CobraProjectionBenchmarkTest.java';testsha=sha(test)
    assert sha(candidate/'src/test/java/com/projectinfinity/kodi'/test.name)==testsha
    out.mkdir(parents=True,exist_ok=False)
    report={'scope':'FIXED_ABBA_HOST_COMPARISON_AFTER_V1_REGRESSION','status':'IN_PROGRESS',
      'test_SHA256':testsha,'warmups_per_entry_per_run':21,'samples_per_entry_per_run':21,
      'run_order':list(ORDER),'aggregate_N_per_entry_per_variant':42,
      'percentile_method':'p50 midpoint for even N; p95 nearest rank',
      'baseline_APK_sha256':b['APK_sha256'],'candidate_prototype_DEX_sha256':V2,
      'application_APK':'NO_CANDIDATE_APK_BUILT_OR_SIGNED','physical_Fold':'NOT_RUN','shutdown':'NOT_RUN',
      'runs':[]}
    (out/'SELECTION.json').write_text(json.dumps(selected,indent=2)+'\n')
    (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    for index,label in enumerate(ORDER,1):
        source=baseline if label=='B431' else candidate
        folder=out/('%02d-%s'%(index,label));folder.mkdir()
        for name in ('production.jar','support.jar'):shutil.copyfile(source/name,folder/name);assert sha(source/name)==sha(folder/name)
        shutil.copytree(baseline/'android-test-libs',folder/'android-test-libs')
        for lib in (baseline/'android-test-libs').iterdir():assert sha(lib)==sha(folder/'android-test-libs'/lib.name)
        target=folder/'src/test/java/com/projectinfinity/kodi';target.mkdir(parents=True)
        shutil.copyfile(test,target/test.name);assert sha(target/test.name)==testsha
        count='20226' if label=='B431' else '1'
        phase='SIGNED431_BASELINE' if label=='B431' else 'UNSIGNED_SINGLE_ACTIVITY_PROTOTYPE_V2_NO_APK'
        properties='<projection.warmups>21</projection.warmups><projection.samples>21</projection.samples><projection.phase>'+phase+'</projection.phase><projection.expected.hidden.reads>'+count+'</projection.expected.hidden.reads><projection.expected.default.sets>'+count+'</projection.expected.default.sets>'
        pom=(baseline/'pom.xml').read_text().replace(str(baseline),str(folder)).replace('<systemPropertyVariables>','<systemPropertyVariables>'+properties)
        (folder/'pom.xml').write_text(pom)
        record={'order':index,'variant':label,'phase':phase,'test_SHA256':testsha,
          'production_jar_SHA256':sha(folder/'production.jar'),'support_jar_SHA256':sha(folder/'support.jar'),
          'prepared_source_INPUTS_SHA256':sha(source/'INPUTS.json'),'effective_warmups':21,'effective_samples':21,
          'expected_hidden_reads_and_default_sets':int(count),'expected_profile_JSON_and_active_profile_reads':40452}
        (folder/'INPUTS.json').write_text(json.dumps(record,indent=2)+'\n')
        print('Starting fixed run %d/4 %s (21 warmups +21 samples per entry)'%(index,label),flush=True)
        with (folder/'TEST-OUTPUT.txt').open('w') as output:
            completed=subprocess.run([str(maven),'-B','-q','-f',str(folder/'pom.xml'),'-Dtest=CobraProjectionBenchmarkTest','test'],stdout=output,stderr=subprocess.STDOUT)
        record['exit_code']=completed.returncode
        report['runs'].append(record)
        (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
        if completed.returncode:
            report['status']='FAILED_SELECTED_TEST; REMAINING_RUNS_NOT_EXECUTED'
            (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
            raise RuntimeError('Selected host test failed at run%d %s; evidence preserved'%(index,label))
        name='BASELINE' if label=='B431' else 'PROTOTYPE'
        measurement=json.loads((folder/'measurements'/(name+'.json')).read_text())
        assert measurement['warmups_per_entry']==measurement['samples_per_entry']==21
        for entry in ENTRIES:
            assert len(measurement[entry]['samples_ms'])==21
            assert measurement[entry]['hidden_preference_reads_separate_count_call']==int(count)
            assert measurement[entry]['distinct_hidden_default_sets_separate_count_call']==int(count)
            assert measurement[entry]['feature_profiles_JSON_reads_separate_count_call']==40452
            assert measurement[entry]['feature_active_profile_reads_separate_count_call']==40452
        record['measurement']=measurement
        (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
        print('Completed fixed run%d %s: %s'%(index,label,{e:stats(measurement[e]['samples_ms']) for e in ENTRIES}),flush=True)
    report['aggregates']={}
    for entry in ENTRIES:
        report['aggregates'][entry]={}
        for variant in ('B431','C2'):
            values=[sample for row in report['runs'] if row['variant']==variant for sample in row['measurement'][entry]['samples_ms']]
            assert len(values)==42
            report['aggregates'][entry][variant]={**stats(values),'samples_ms':values}
        base=report['aggregates'][entry]['B431'];new=report['aggregates'][entry]['C2']
        report['aggregates'][entry]['observed_p50_change_percent']=(new['p50_ms']/base['p50_ms']-1)*100
        report['aggregates'][entry]['observed_p95_change_percent']=(new['p95_ms']/base['p95_ms']-1)*100
    report['status']='COMPLETED_FIXED_ABBA; SELECTED_CORRECTNESS_AND_COUNTS_PASS'
    report['limitations']='Finite host-only samples with JIT/GC/order variation; raw runs retained. No Android frame/startup, physical Fold, memory/battery/thermal or signed-candidate acceptance claim.'
    (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'aggregates':report['aggregates']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('baseline','candidate','maven','out'):parser.add_argument('--'+name,type=Path,required=True)
    run(**vars(parser.parse_args()))
