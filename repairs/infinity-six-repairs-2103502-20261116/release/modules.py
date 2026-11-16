"""Exact502 two-file menu correction: prepare/readback original-signed modules.

No APK, registry mutation, native build, profile or provider execution.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse, hashlib, importlib.util, json, os, subprocess

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
ROOT=TASK.parents[1]
CC='script.infinity.commandcenter'
IDS=(CC,'script.infinity.rails','script.infinity.uirepair','script.infinity.watchedbridge')
MANIFEST=CC+'/INFINITY-MODULES.v1'
SIGNATURE=MANIFEST+'.sig'
BASE='f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
WORK=ROOT/'six502-module-work'
WORKFLOW='.github/workflows/infinity-combined-release.yml'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(Path(path).read_bytes())
def hashes(root): return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)

def gate():
    r=load(HERE/'MODULE-REQUEST.json')
    assert r['operation']=='prepare-six502-modules' and r['APK'] is False
    assert r['registry_mutation'] is False and r['owner_data']=='NOT_ACCESSED'
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103502-six-repairs-20261116'
    run=json.loads(subprocess.check_output(['gh','api','repos/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID']]))
    assert run['workflow_id']==397702717 and run['head_sha']==os.environ['GITHUB_SHA']
    assert not git('status','--porcelain','--untracked-files=no').strip()
    assert git('diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']).decode().splitlines()==[
        str((HERE/'MODULE-REQUEST.json').relative_to(ROOT))],'UNREVIEWED_SOURCE_AFTER_REQUEST'
    names=[str((TASK/name).relative_to(ROOT)) for name in (
        'release/modules.py','WATCHLIST-SCOPE.json','WATCHLIST-REVIEW.json','test_watchlist_menu.py',
        'overlay/script.infinity.commandcenter/addon.xml','overlay/script.infinity.commandcenter/context.py',
        'lock/application/stage.py','lock/application/NATIVE.json')]
    names.extend((WORKFLOW,'repairs/infinity-final-closure-2103407/SignInfinityModules.java',
                  'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'))
    assert set(r['inputs'])==set(names),'EXACT_REVIEWED_INPUT_SET_REQUIRED'
    review_raw=(HERE/'MODULE-REVIEW.json').read_bytes()
    assert sha(review_raw)==r['independent_review_sha256']
    review=json.loads(review_raw)
    canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    assert review['status']=='PASS_EXACT_MODULE_SIGNING_SCOPE' and review['reviewer']=='Astra'
    assert review['inputs_sha256']==sha(canonical(r['inputs']))
    assert review['expected_modules_sha256']==sha(canonical(r['expected_modules']))
    for name,expected in r['inputs'].items(): assert sha((ROOT/name).read_bytes())==expected,name
    before=git('show',r['workflow_before_commit']+':'+WORKFLOW).decode()
    expected=before.replace('sign-cast98-hls]','sign-cast98-hls, prepare-six502-modules]',1)
    assert (ROOT/WORKFLOW).read_text().split('\n  prepare-six502-modules:\n')[0].rstrip()==expected.rstrip(),'EXISTING_SIGNER_JOBS_CHANGED'
    signer='repairs/infinity-final-closure-2103407/SignInfinityModules.java'
    assert (ROOT/signer).read_bytes()==git('show',r['workflow_before_commit']+':'+signer)
    return r

def prepare():
    r=gate();WORK.mkdir()
    path=TASK/'lock/application/stage.py'
    spec=importlib.util.spec_from_file_location('existing_artifact_reader',path)
    stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
    apk,binding=stage.artifact(WORK,'baseline');assert stage.digest(apk)==BASE
    baseline={}
    with ZipFile(apk) as z:
        for info in z.infolist():
            name=info.filename
            if any(name.startswith('assets/addons/'+aid+'/') for aid in IDS) and not name.endswith('/'):
                relative=name[len('assets/addons/'):]
                assert '..' not in Path(relative).parts and not Path(relative).is_absolute()
                baseline[relative]=z.read(info)
    assert MANIFEST in baseline and SIGNATURE in baseline
    candidate=dict(baseline)
    scope=load(TASK/'WATCHLIST-SCOPE.json')
    assert set(scope['allowlist'])=={'addon.xml','context.py'}
    assert scope['baseline']==2103502 and scope['module_version']=='0.3.5.84'
    for name,row in scope['allowlist'].items():
        key=CC+'/'+name;raw=(TASK/'overlay'/key).read_bytes()
        assert sha(baseline[key])==row['before'] and sha(raw)==row['after']
        candidate[key]=raw
    original=baseline[MANIFEST].decode('ascii').splitlines()
    assert original[:3]==['INFINITY-MODULES/1','package\t0.3.5.83','protocol\t1']
    lines=[]
    for line in original:
        if line.startswith('package\t'):line='package\t0.3.5.84'
        elif line.startswith('file\t'):
            _,digest,name=line.split('\t');assert sha(baseline[name])==digest
            line='file\t'+sha(candidate[name])+'\t'+name
        lines.append(line)
    candidate[MANIFEST]=('\n'.join(lines)+'\n').encode('ascii')
    del candidate[SIGNATURE]
    assert {n for n in candidate if candidate[n]!=baseline[n]}=={CC+'/addon.xml',CC+'/context.py',MANIFEST}
    assert {n:sha(raw) for n,raw in candidate.items()}==r['expected_modules']
    modules=WORK/'modules'
    for n,raw in candidate.items():
        out=modules/n;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
    (WORK/'PREPARATION.json').write_text(json.dumps(dict(baseline=2103502,baseline_artifact=binding,
        source=os.environ['GITHUB_SHA'],modules=hashes(modules),modified_sources=scope['allowlist'],
        original_key_signature='PENDING',APK=False,registry_mutated=False,owner_data='NOT_ACCESSED'),indent=2)+'\n')
    print('PASS_EXACT502_MENU_MODULE_PREPARATION_ONLY')

def readback(signed=False):
    r=gate();root=WORK/'modules';actual=hashes(root)
    if signed: assert actual.pop(SIGNATURE,None)
    assert actual==r['expected_modules'],'PREPARED_SOURCE_CHANGED'
    if signed:
        public=ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'
        assert sha(public.read_bytes())=='bc883be4515d328935b1f3e28294bfc0fe0f2614083274db63b1d24d4da172e8'
        subprocess.run(['openssl','dgst','-sha256','-verify',str(public),'-signature',str(root/SIGNATURE),str(root/MANIFEST)],check=True,capture_output=True)
        (WORK/'ORIGINAL-SIGNATURE-VERIFICATION.json').write_text(json.dumps(dict(
            status='PASS_ORIGINAL_SIGNED_MODULES_ONLY',source=os.environ['GITHUB_SHA'],baseline=2103502,
            module_version='0.3.5.84',modules=hashes(root),APK=False,Android='NOT_RUN',owner_acceptance=False),indent=2)+'\n')
    print('PASS_EXACT_MODULE_'+('ORIGINAL_SIGNATURE' if signed else 'READBACK'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['prepare','readback','verify'])
    op=parser.parse_args().operation
    prepare() if op=='prepare' else readback(op=='verify')
