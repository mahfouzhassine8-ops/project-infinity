"""Reuse the verified signed-package install-over driver; no application launch.

Only the selected baseline/version/request location changes. Original allowed
ADB commands, certificate checks and UID/dataDir/first-install checks remain.
"""
from pathlib import Path
import hashlib, json, os, subprocess, sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REFERENCE='21616dfa94bf7ca9ec52e40119edf95df5e64073'
DRIVER='repairs/infinity-consolidated-2103500-20261115/verify_fastqa_install.py'

def main():
    assert len(sys.argv)==2 and sys.argv[1] in ('prepare','run')
    assert os.environ['GITHUB_ACTIONS']=='true'
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103502-six-repairs-20261116'
    request=json.loads((HERE/'QA-SIGNED-INSTALL-REQUEST.json').read_bytes())
    review_raw=(HERE/'INSTALL-REVIEW.json').read_bytes()
    assert hashlib.sha256(review_raw).hexdigest()==request['review_sha256']
    review=json.loads(review_raw)
    assert review['reviewer']=='Astra' and review['status']=='PASS_SELECTED_PACKAGE_INSTALL_SOURCE'
    canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical(request['inputs'])).hexdigest()==review['signed_inputs_sha256']
    assert request['application_startup'] is False and request['shutdown'] is False
    assert request['baseline']==2103502 and request['versions']=={'candidate':2103504,'recovery':2103505}
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==review['driver_sha256']
    assert hashlib.sha256((ROOT/'.github/workflows/infinity-502-combined-stage.yml').read_bytes()).hexdigest()==review['workflow_sha256']
    raw=subprocess.check_output(['git','show',REFERENCE+':'+DRIVER],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()=='dc4f2de26406eac4e29cfc7dae11de7c1df0f644de95c9c345d1d2ffe4bce34b'
    original="version={'baseline':2103500,**VERSIONS}[kind]"
    assert raw.count(original.encode())==1
    source=raw.decode().replace(original,"version={'baseline':2103502,**VERSIONS}[kind]")
    helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py'
    assert (ROOT/helper).read_bytes()==subprocess.check_output(['git','show',REFERENCE+':'+helper],cwd=ROOT),'UNCHANGED_IMPORTED_INSTALL_TRANSPORT'
    if sys.argv[1]=='run':
        assert subprocess.check_output(['adb','shell','getprop','ro.kernel.qemu'],text=True,timeout=15).strip()=='1','DISPOSABLE_EMULATOR_ONLY'
    scope={'__file__':str(ROOT/DRIVER),'__name__':'_retained_install_package_driver'}
    exec(compile(source,str(ROOT/DRIVER),'exec'),scope)
    scope.update(HERE=HERE,VERSIONS={'candidate':2103504,'recovery':2103505})
    scope[sys.argv[1]]()

if __name__=='__main__':main()
