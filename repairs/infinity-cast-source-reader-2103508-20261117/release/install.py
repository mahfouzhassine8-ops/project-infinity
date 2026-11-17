"""Retained signed PackageManager-only install-over driver; no app launch or data reset."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REF='21616dfa94bf7ca9ec52e40119edf95df5e64073'
DRIVER='repairs/infinity-consolidated-2103500-20261115/verify_fastqa_install.py'
def main():
 assert len(sys.argv)==2 and sys.argv[1] in ('prepare','run')
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103508-cast-source-reader-20261117'
 r=json.loads((HERE/'INSTALL-REQUEST.json').read_bytes());raw_review=(HERE/'INSTALL-REVIEW.json').read_bytes();assert hashlib.sha256(raw_review).hexdigest()==r['review_sha256']
 review=json.loads(raw_review);assert review['reviewer']=='Astra' and review['status']=='PASS_SELECTED_PACKAGE_INSTALL_SOURCE'
 fixed={k:r[k] for k in ('baseline','versions','inputs','application_startup','shutdown')}
 assert hashlib.sha256(json.dumps(fixed,sort_keys=True,separators=(',',':')).encode()).hexdigest()==review['request_sha256']
 assert r['baseline']==2103508 and r['versions']['recovery']>r['versions']['candidate']>2103509 and r['application_startup'] is False and r['shutdown'] is False
 assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==review['driver_sha256']
 assert hashlib.sha256((ROOT/'.github/workflows/infinity-506-cast-hardware-stage.yml').read_bytes()).hexdigest()==review['workflow_sha256']
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py';raw=subprocess.check_output(['git','show',REF+':'+helper])
 module=types.ModuleType('common_release');module.__file__=str(ROOT/helper);exec(compile(raw,module.__file__,'exec'),module.__dict__);sys.modules['common_release']=module
 raw=subprocess.check_output(['git','show',REF+':'+DRIVER]);assert hashlib.sha256(raw).hexdigest()=='dc4f2de26406eac4e29cfc7dae11de7c1df0f644de95c9c345d1d2ffe4bce34b'
 source=raw.decode().replace("version={'baseline':2103500,**VERSIONS}[kind]","version={'baseline':2103508,**VERSIONS}[kind]").replace("HERE/'QA-SIGNED-INSTALL-REQUEST.json'","HERE/'INSTALL-REQUEST.json'")
 scope={'__file__':str(ROOT/DRIVER),'__name__':'_retained_install_driver'};exec(compile(source,str(ROOT/DRIVER),'exec'),scope);scope.update(HERE=HERE,VERSIONS=r['versions'])
 if sys.argv[1]=='run':assert subprocess.check_output(['adb','shell','getprop','ro.kernel.qemu'],text=True,timeout=15).strip()=='1','DISPOSABLE_EMULATOR_ONLY'
 scope[sys.argv[1]]()
if __name__=='__main__':main()
