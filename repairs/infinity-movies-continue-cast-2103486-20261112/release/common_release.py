"""Frozen-input helpers; no signing key handling or installation."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,os,re,stat,subprocess,sys,urllib.request

HERE=Path(__file__).resolve().parent;TASK=HERE.parent;ROOT=TASK.parents[1]
CORE=ROOT/'repairs/dual-experience-isolation-2103420'
REPO='mahfouzhassine8-ops/project-infinity'
CANONICAL='work/infinity-2103460-nine-corrections-20261106'
BRANCH='work/infinity-movies-continue-cast-2103486-20261112'
BASE='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
NATIVE='dc9e734655546f02c9a060b50bda1643f189e2756dd159c4f5b14169e6bb6716'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
AUTHORITY='repairs/dual-experience-isolation-2103420/release-authority.json'
WORKFLOW='.github/workflows/infinity-combined-release.yml'
VERSIONS={'candidate':2103488,'recovery':2103489}
GENERATIONS={'candidate':73,'recovery':74}
def require(value,label):
    if not value:raise RuntimeError(label)
def load(path):return json.loads(Path(path).read_bytes())
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/'+path],timeout=60))
def tools():
    for name in ('assemble.py','component_bundles.py','release_gate.py','inventory.py','review_ownership.py','signer_policy.py'):
        path='repairs/dual-experience-isolation-2103420/'+name
        require((ROOT/path).read_bytes()==git('show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:'+path),'UNCHANGED_ORIGINAL_TOOL:'+name)
    for path in ('repairs/infinity-final-closure-2103407/p0/manifest.py',
                 'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                 'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json'):
        require((ROOT/path).read_bytes()==git('show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:'+path),'UNCHANGED_ORIGINAL_TOOL_INPUT:'+path)
    sys.path.insert(0,str(CORE))
    import inventory,component_bundles,release_authority,release_gate,review_ownership
    return inventory,component_bundles,release_authority,release_gate,review_ownership
def context(canonical=False):
    require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')==REPO,'AUTHORIZED_CI_REPOSITORY')
    require(os.environ.get('GITHUB_REF')=='refs/heads/'+(CANONICAL if canonical else BRANCH),'EXACT_QA_BRANCH')
    require(git('rev-parse','HEAD').decode().strip()==os.environ['GITHUB_SHA'] and not git('status','--porcelain','--untracked-files=no').strip(),'CLEAN_EXACT_CI_SOURCE')
    run=api('actions/runs/'+os.environ['GITHUB_RUN_ID']);require(run['workflow_id']==397702717 and run['head_sha']==os.environ['GITHUB_SHA'],'SOLE_EXISTING_ORIGINAL_WORKFLOW')
    lock=subprocess.check_output(['git','ls-remote','origin','refs/heads/locks/infinity-2103486-fold-accepted-20261112'],text=True).split()
    require(lock==['e1ef672a6f24aed6c19a14ab96d2df6fe3380460','refs/heads/locks/infinity-2103486-fold-accepted-20261112'],'OWNER_ACCEPTED86_LOCK_MOVED')
def producer(row):
    run=api('actions/runs/'+str(row['run']))
    require(run['status']=='completed' and run['conclusion']=='success' and run['workflow_id']==row['workflow_id'] and run['head_sha']==row['source'],'FROZEN_SUCCESSFUL_PRODUCER')
    a=api('actions/artifacts/'+str(row['id']))
    require(not a['expired'] and a['workflow_run']['id']==row['run'] and all(a[k]==row[k] for k in ('id','name','digest','size_in_bytes')),'EXACT_LIVE_ARTIFACT')
def obtain(row,role):
    producer(row);folder=ROOT/('movies-cast-input-'+role);folder.mkdir(exist_ok=True);archive=folder/'authenticated.zip';out=folder/'files'
    if not archive.exists():
        with archive.open('xb') as target:subprocess.run(['gh','api','repos/'+REPO+'/actions/artifacts/'+str(row['id'])+'/zip'],stdout=target,check=True,timeout=900)
    require('sha256:'+sha(archive)==row['digest'] and archive.stat().st_size==row['size_in_bytes'],'ACTUAL_ARCHIVE_DIGEST:'+role)
    with ZipFile(archive) as z:
        names=z.namelist();require(len(names)==len(set(names)) and len(names)<100000 and sum(i.file_size for i in z.infolist())<8*1024**3,'BOUNDED_UNIQUE_ARCHIVE')
        for item in z.infolist():
            p=Path(item.filename);require(not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and not stat.S_ISLNK(item.external_attr>>16),'SAFE_ARCHIVE_MEMBER')
        if not out.exists():out.mkdir();z.extractall(out)
        require({p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}=={i.filename for i in z.infolist() if not i.is_dir()},'CACHED_MEMBER_VECTOR')
        for item in z.infolist():
            if not item.is_dir():
                with z.open(item) as stream:require(hashlib.file_digest(stream,'sha256').hexdigest()==sha(out/item.filename),'CACHED_AUTHENTICATED_BYTES')
    return out
def unique(root,name):
    found=[p for p in Path(root).rglob(name) if p.is_file()];require(len(found)==1,'ONE_EXACT_INPUT:'+name);return found[0]
def signature(apk):
    sdk=Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0'
    text=subprocess.check_output([sdk/'apksigner','verify','--verbose','--print-certs',apk],text=True)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',text)==[CERT],'PERMANENT_CERTIFICATE')
    require(all(any(x.startswith('Verified using '+v+' scheme') and x.endswith(': true') for x in text.splitlines()) for v in ('v1','v2','v3')),'ORIGINAL_V1_V2_V3_SIGNATURES')
    return text
def jars():
    path='repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json'
    require((ROOT/path).read_bytes()==git('show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:'+path),'ORIGINAL_DEX_TOOL_PINS')
    pins=load(ROOT/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json');out=ROOT/'movies-cast-original-dex-tools';out.mkdir(exist_ok=True)
    coordinates={
      'ST4-4.0.8.jar':'org/antlr/ST4/4.0.8', 'antlr-2.7.7.jar':'antlr/antlr/2.7.7',
      'antlr-3.5.2.jar':'org/antlr/antlr/3.5.2','antlr-runtime-3.5.2.jar':'org/antlr/antlr-runtime/3.5.2',
      'animal-sniffer-annotations-1.17.jar':'org/codehaus/mojo/animal-sniffer-annotations/1.17',
      'checker-compat-qual-2.5.2.jar':'org/checkerframework/checker-compat-qual/2.5.2',
      'error_prone_annotations-2.2.0.jar':'com/google/errorprone/error_prone_annotations/2.2.0',
      'failureaccess-1.0.1.jar':'com/google/guava/failureaccess/1.0.1','guava-27.1-android.jar':'com/google/guava/guava/27.1-android',
      'j2objc-annotations-1.1.jar':'com/google/j2objc/j2objc-annotations/1.1',
      'jcommander-1.64.jar':'com/beust/jcommander/1.64','jsr305-3.0.2.jar':'com/google/code/findbugs/jsr305/3.0.2',
      'listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar':'com/google/guava/listenablefuture/9999.0-empty-to-avoid-conflict-with-guava',
      'stringtemplate-3.2.1.jar':'org/antlr/stringtemplate/3.2.1'}
    for artifact in ('baksmali','dexlib2','smali','util'):coordinates[artifact+'-2.5.2.jar']='org/smali/'+artifact+'/2.5.2'
    require(set(coordinates)==set(pins),'UNCHANGED_ORIGINAL_DEX_TOOL_VECTOR')
    for name,wanted in pins.items():
        p=out/name
        if not p.exists():
            with urllib.request.urlopen('https://repo.maven.apache.org/maven2/'+coordinates[name]+'/'+name,timeout=60) as stream:p.write_bytes(stream.read())
        require(sha(p)==wanted,'PINNED_ORIGINAL_DEX_TOOL:'+name)
    return out
