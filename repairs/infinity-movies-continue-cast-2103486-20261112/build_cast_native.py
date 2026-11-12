"""Restore the exact accepted86 native source; add only isolated Cast commands.

Reuse frozen 9ce build/dependency tools in a separate detached build worktree.
Never replace the authoritative signed86 APK with an older application payload.
"""
from pathlib import Path
import hashlib, importlib.util, json, os, re, shutil, subprocess, sys
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'cast-native-output'
TOOLS=ROOT/'cast-native-frozen-tools'
REFERENCE='9ce852ebb044a82853ef93af24e34a07ed96daff'
LOCK='e1ef672a6f24aed6c19a14ab96d2df6fe3380460'
BRANCH='work/infinity-movies-continue-cast-2103486-20261112'
OLD='repairs/infinity-essential-only-shutdown-2103483-20261112'
APK86='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
ENGINE86='b75747363c83a548d61463c2fd434be909f27c07d4872fa9d9c61642a3757635'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
CPP='xbmc/platform/android/activity/InfinityCastNative.cpp'
CMAKE='xbmc/platform/android/activity/CMakeLists.txt'

def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def save(name,obj):
    OUT.mkdir(exist_ok=True);(OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')

def gate():
    assert os.environ.get('GITHUB_ACTIONS')=='true'
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/'+BRANCH
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==os.environ['GITHUB_SHA']
    changed=subprocess.check_output(['git','diff','--name-only',LOCK,'HEAD'],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith(str(HERE.relative_to(ROOT))+'/') or n in (
        '.github/workflows/infinity-core-outcomes-qa-native.yml',
        '.github/workflows/infinity-saved-navigation-android.yml') for n in changed),changed
    assert json.loads((HERE/'SCOPE.json').read_text())['native_protected_changes'] is False

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(path.parent))
    try:spec.loader.exec_module(m)
    finally:sys.path.pop(0)
    return m

def retained():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=TOOLS,text=True).strip()==REFERENCE
    path=TOOLS/OLD/'build_native.py'
    assert path.read_bytes()==subprocess.check_output(['git','show',REFERENCE+':'+OLD+'/build_native.py'],cwd=ROOT)
    m=load(path,'frozen_actual86_native_builder');m.scope=gate;m.OUT=OUT
    return m

def prepare():
    gate();assert not TOOLS.exists()
    subprocess.run(['git','worktree','add','--detach','--no-checkout',str(TOOLS),REFERENCE],cwd=ROOT,check=True)
    subprocess.run(['git','sparse-checkout','init','--no-cone'],cwd=TOOLS,check=True)
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',REFERENCE],cwd=ROOT,text=True).splitlines()
    suffixes={'.py','.sh','.json','.java','.in','.h','.hpp','.cpp','.c','.txt','.patch','.xml','.pem','.sig','.v1','.cmake','.yml','.md'}
    selected=[n for n in names if Path(n).suffix in suffixes or Path(n).name=='CMakeLists.txt']
    subprocess.run(['git','sparse-checkout','set','--no-cone','--stdin'],input=''.join('/'+n+'\n' for n in selected),cwd=TOOLS,text=True,check=True)
    subprocess.run(['git','checkout'],cwd=TOOLS,check=True)
    for name in ('verified-inputs','previous-review','exact464','signed80'):
        (TOOLS/name).symlink_to(ROOT/name,target_is_directory=True)
    retained().prepare()
    native=TOOLS/'kodi';before=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    original=json.loads((TOOLS/OLD/'BASE83-NATIVE-SOURCE-MAP.json').read_text())
    expected86=dict(original)
    for name in json.loads((TOOLS/OLD/'BASELINE-SOURCE.json').read_text()):
        expected86[name]=sha(TOOLS/OLD/'native/overlay'/name)
    assert before==expected86 and len(before)==9412
    cmake=(HERE/'native/overlay'/CMAKE).read_bytes()
    assert cmake.replace(b'\n            InfinityCastNative.cpp',b'',1)==(native/CMAKE).read_bytes()
    after=dict(before)
    for name in (CMAKE,CPP):
        data=(HERE/'native/overlay'/name).read_bytes();(native/name).write_bytes(data)
        after[name]=hashlib.sha256(data).hexdigest()
    assert CPP not in before and len(after)==9413
    hasher=load(TOOLS/'repairs/infinity-native-touch-2103451-20261105/compile_only.py','frozen_native_source_hasher')
    assert hasher.hashes(native)==after
    save('NATIVE-SOURCE-MAP.json',after)
    save('CAST-SOURCE-PRESERVATION.json',dict(status='PASS_EXACT86_PLUS_CAST_ONLY_CPP_AND_CMAKE_ENTRY',
        source=os.environ['GITHUB_SHA'],baseline86_engine_sha256=ENGINE86,baseline86_reference_source=REFERENCE,
        unchanged86_native_files=9411,added={CPP:after[CPP]},changed={CMAKE:dict(before=before[CMAKE],after=after[CMAKE])},
        shutdown_changed=False,persistence_protections_changed=False,Cobra_changed=False,
        Python_startup_changed=False,providers_changed=False,old_API_changed=False,Android='NOT_RUN'))
    apk=ROOT/'signed86/Infinity-2103486-Combined-Original-Signer.apk';assert sha(apk)==APK86
    sdk=Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0'
    signature=subprocess.check_output([sdk/'apksigner','verify','--verbose','--print-certs',apk],text=True)
    assert re.findall(r'certificate SHA-256 digest: ([a-f0-9]+)',signature)==[CERT]
    assert all(any(line.startswith('Verified using '+v+' scheme') and line.endswith(': true')
                   for line in signature.splitlines()) for v in ('v1','v2','v3'))
    with ZipFile(apk) as z,z.open('lib/arm64-v8a/libkodi.so') as src,(OUT/'baseline86-libkodi.so').open('wb') as dst:
        shutil.copyfileobj(src,dst,1024*1024)
    assert sha(OUT/'baseline86-libkodi.so')==ENGINE86

def dependencies():
    gate()
    # Frozen dependency scripts explicitly cd to GITHUB_WORKSPACE. Their
    # source is unchanged; execute them in the verified detached tools tree.
    previous=os.environ.get('GITHUB_WORKSPACE')
    os.environ['GITHUB_WORKSPACE']=str(TOOLS)
    try:retained().dependencies()
    finally:
        if previous is None:os.environ.pop('GITHUB_WORKSPACE',None)
        else:os.environ['GITHUB_WORKSPACE']=previous

def compile_native():
    gate();expected=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text());assert len(expected)==9413
    compiler=load(TOOLS/'repairs/universal-persistence-2103401/build.py','frozen_actual_arm64_compiler')
    compiler.OUT=OUT;original=compiler.checked_sources
    def checked(root,pins,allow_generated=False):
        extra=original(root,pins,allow_generated=True)
        if not allow_generated:
            assert Path(root)==TOOLS/'kodi' and pins==expected
            assert all(n.startswith('tools/depends/') for n in extra),extra
        return extra
    compiler.checked_sources=checked
    previous=os.environ.get('GITHUB_WORKSPACE')
    os.environ['GITHUB_WORKSPACE']=str(TOOLS)
    try:proof=compiler.compile_engine()
    finally:
        if previous is None:os.environ.pop('GITHUB_WORKSPACE',None)
        else:os.environ['GITHUB_WORKSPACE']=previous
    assert proof['complete_native_engine_compiled'] and proof['reviewed_file_count']==9413
    library=OUT/'libkodi.so';assert sha(library)==proof['native_sha256']
    readelf=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    def abi(p):
        head=subprocess.check_output([readelf,'-h',p],text=True);assert all(n in head for n in ('ELF64','AArch64','DYN'))
        dyn=subprocess.check_output([readelf,'-d',p],text=True)
        rows=subprocess.check_output([readelf,'--dyn-syms','--wide',p],text=True).splitlines();exports=set()
        for line in rows:
            f=line.split()
            if len(f)>=8 and f[4]=='GLOBAL' and f[5] in ('DEFAULT','PROTECTED') and f[6]!='UND':exports.add(f[7])
        return exports,set(re.findall(r'Shared library: \[([^\]]+)\]',dyn))
    before,after=abi(OUT/'baseline86-libkodi.so'),abi(library)
    assert before[0]<=after[0] and before[1]==after[1]
    new={'Java_com_projectinfinity_kodi_InfinityCastNative_'+n for n in ('request','poll','cancel')}
    assert new<=after[0]-before[0]
    save('CAST-ARM64.json',dict(status='PASS_FULL_REAL_ARM64_LINK_AND_BASELINE86_ABI',source=os.environ['GITHUB_SHA'],
        native_sha256=sha(library),baseline86_native_sha256=ENGINE86,preserved_exports=len(before[0]),
        Cast_JNI=sorted(new),new_exports=sorted(after[0]-before[0]),dependencies=sorted(after[1]),
        shutdown_source_changed=False,Cobra_changed=False,Android='NOT_RUN',signed=False))

if __name__=='__main__':
    assert len(sys.argv)==2
    {'prepare':prepare,'dependencies':dependencies,'compile':compile_native}[sys.argv[1]]()
