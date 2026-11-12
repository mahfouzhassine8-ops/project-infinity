"""Module-only input/readback gate for the existing sole original-key workflow.

No APK signing, installer, release registry mutation or acceptance assertion.
The original SignInfinityModules/public key and every pre-existing job are fixed.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess

HERE=Path(__file__).resolve().parent;TASK=HERE.parent;ROOT=TASK.parents[1]
LOCK='e1ef672a6f24aed6c19a14ab96d2df6fe3380460'
REPO='mahfouzhassine8-ops/project-infinity'
BRANCH='work/infinity-movies-continue-cast-2103486-20261112'
WORKFLOW='.github/workflows/infinity-combined-release.yml'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def load(path):return json.loads(Path(path).read_bytes())
def gate():
    request=load(HERE/'MODULE-PREPARE-REQUEST.json')
    assert request['operation']=='prepare-original86-movies-cast-modules' and request['APK'] is False
    assert request['registry_mutation'] is False and request['owner_installer'] is False
    assert request['baseline_APK_sha256']=='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
    assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')==REPO
    assert os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH
    assert git('rev-parse','HEAD').decode().strip()==os.environ['GITHUB_SHA']
    assert not git('status','--porcelain','--untracked-files=no').strip(),'Frozen checked-out inputs only'
    run=json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/actions/runs/'+os.environ['GITHUB_RUN_ID']]))
    assert run['workflow_id']==397702717 and run['head_sha']==os.environ['GITHUB_SHA'],'Sole existing original signer workflow required'
    before=git('show',LOCK+':'+WORKFLOW).decode().rstrip()
    expected=before.replace('sign-essential-recovery]','sign-essential-recovery, prepare-movies-cast-modules]',1)
    current=(ROOT/WORKFLOW).read_text()
    assert current.split('\n  prepare-movies-cast-modules:\n')[0].rstrip()==expected,'Pre-existing signer jobs changed'
    assert sha(current.encode())==request['workflow_sha256']
    signer='repairs/infinity-final-closure-2103407/SignInfinityModules.java'
    assert (ROOT/signer).read_bytes()==git('show',LOCK+':'+signer),'Original signer changed'
    for name,wanted in request['source_bindings'].items():
        p=Path(name);assert not p.is_absolute() and '..' not in p.parts
        assert sha((ROOT/p).read_bytes())==wanted,'Input changed: '+name
    return request
def preparation():
    spec=importlib.util.spec_from_file_location('frozen86_module_stage',HERE/'prepare_modules.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def readback(request,out,signed=False):
    prepared=load(out/'PREPARATION.json');module=preparation()
    assert prepared['registry_mutated'] is False and prepared['APK'] is False
    for label in ('candidate','recovery'):
        root=out/label;record=load(root/'INPUTS.json')
        assert sha((root/'INPUTS.json').read_bytes())==prepared['inputs'][label]
        assert record['source_commit']==os.environ['GITHUB_SHA']
        assert record['modules']==request['expected_modules'][label]
        actual=module.hashes(root/'modules');signature='script.infinity.commandcenter/INFINITY-MODULES.v1.sig'
        if signed:assert actual.pop(signature,None) is not None
        assert actual==record['modules'],'Staged generation changed'
        if signed:
            subprocess.run(['openssl','dgst','-sha256','-verify',str(ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                '-signature',str(root/'modules'/signature),str(root/'modules/script.infinity.commandcenter/INFINITY-MODULES.v1')],check=True,capture_output=True)
    if signed:
        result=dict(status='PASS_COMPLETE_ORIGINAL_SIGNED_MODULES_ONLY',baseline=2103486,
            candidate_sources=81,recovery_sources=80,original_signer='UNCHANGED_SignInfinityModules.java',
            original_public_key_sha256='bc883be4515d328935b1f3e28294bfc0fe0f2614083274db63b1d24d4da172e8',
            APK=False,owner_installable=False,Android_integration='NOT_YET_TESTED',registry_mutated=False)
        (out/'ORIGINAL-SIGNATURE-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS_ORIGINAL_MODULE_'+('SIGNATURES' if signed else 'FROZEN_SOURCE_READBACK')+'_NOT_AN_INSTALLER')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['preflight','readback','verify']);parser.add_argument('--out',type=Path,default=Path('movies-cast-module-prepared'))
    args=parser.parse_args();request=gate()
    if args.operation!='preflight':readback(request,args.out,args.operation=='verify')
