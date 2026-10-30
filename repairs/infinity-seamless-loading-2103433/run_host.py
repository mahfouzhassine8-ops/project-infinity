"""Source-bound focused Infinity loading producer. No APK/signing/native launch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def sources():
    return sorted(p for p in HERE.rglob('*') if p.is_file() and not set(p.relative_to(HERE).parts)&{'__pycache__','results'} and p.suffix in {'.py','.java','.cpp','.json','.md','.xml'})

def run(baseline,out,selection='original'):
    baseline,out=baseline.resolve(),out.resolve()
    assert not out.exists(),'Fresh evidence directory required';out.mkdir(parents=True)
    branch=subprocess.check_output(['git','-C',str(REPO),'branch','--show-current'],text=True).strip()
    source=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
    scope=json.loads((HERE/'SCOPE.json').read_text());assert branch==scope['branch'],'Exact Infinity owner branch required'
    if os.environ.get('GITHUB_ACTIONS')=='true':
        assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
        assert os.environ['GITHUB_SHA']==source
    pins={str(p.relative_to(REPO)):sha(p) for p in sources()}
    for relative,pin in pins.items():
        assert hashlib.sha256(subprocess.check_output(['git','-C',str(REPO),'show',source+':'+relative])).hexdigest()==pin,'Uncommitted selected source: '+relative
    from stage import generate
    generate(baseline,out/'stage')
    os.environ['INFINITY_STAGED']=str(out/'stage')
    os.environ['INFINITY_HOST_MEASUREMENTS']=str(out/'measurements')
    sys.path.insert(0,str(HERE/'tests'))
    if selection=='current-window':
        row=scope['rejected434_current_window_correction'];assert row['recorded_before_execution'] is True
        selected=['test_current_window.'+row['class']+'.'+name for name in row['methods']]
        selected.extend('test_integration.'+row['retained_integration_class']+'.'+name for name in row['retained_integration_methods'])
        expected=7
    else:
        selected=['test_loading.'+name for name in scope['exact_host_methods']]
        for file,key in [('test_integration','integration_test_selection'),('test_monitor','monitor_integration_selected_before_execution')]:
            row=scope[key];assert row['selected_before_execution'] is True
            selected.extend(file+'.'+row['class']+'.'+name for name in row['methods'])
        expected=24
    assert len(selected)==len(set(selected))==expected,'Exact selected loading methods required'
    selection=dict(recorded_before_execution=True,source=source,branch=branch,methods=selected,tested_source_files=pins,
                   baseline_component_sha256=sha(baseline),stage_sha256=sha(out/'stage/STAGE.json'),
                   source_plan_sha256=sha(out/'stage/SOURCE-PLAN.json'),APK='NOT_BUILT',shutdown='NOT_RUN')
    (out/'SELECTION.json').write_text(json.dumps(selection,indent=2)+'\n')
    suite=unittest.defaultTestLoader.loadTestsFromNames(selected)
    with (out/'TEST-OUTPUT.txt').open('w') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    assert all(sha(REPO/relative)==pin for relative,pin in pins.items()),'Source mutated during focused tests'
    success=result.wasSuccessful() and result.testsRun==expected and not result.skipped
    record=dict(status='PASS_FOCUSED_INFINITY_LOADING_HOST_ONLY' if success else 'FAIL_FOCUSED_INFINITY_LOADING_HOST_ONLY',
                source=source,branch=branch,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
                tested_source_files=pins,selected_methods=selected,selection_sha256=sha(out/'SELECTION.json'),
                stage_sha256=sha(out/'stage/STAGE.json'),source_plan_sha256=sha(out/'stage/SOURCE-PLAN.json'),
                module_manifest_sha256=sha(out/'stage/candidate-addons/script.infinity.commandcenter/INFINITY-MODULES.v1'),
                original_module_signature='VERIFIED_ON_BASELINE; NEW_MANIFEST_REQUIRES_ORIGINAL_KEY',
                Android_Kodi_Python='BLOCKED_EXISTING_NATIVE_CONSTRUCTOR; NOT_RUN',physical_Fold='PENDING',APK='NOT_BUILT',shutdown='NOT_CHANGED_NOT_RUN')
    (out/'HOST-RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('tested_source_files','selected_methods')},indent=2))
    if not success:raise SystemExit('Focused Infinity loading tests failed; retain evidence')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--selection',choices=['original','current-window'],default='original')
    run(**vars(parser.parse_args()))
