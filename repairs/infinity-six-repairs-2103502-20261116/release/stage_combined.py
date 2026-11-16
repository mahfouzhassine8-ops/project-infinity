"""Preservation-checked combined QA staging. Unsigned; never owner-installable.

Reuse exact502 APK, verified Kodi/DEX/Cast artifacts and original-signed menu
modules. No compile, signing key, user profile, registry or behavioral test.
"""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib, importlib.util, json, os, shutil, subprocess, sys, urllib.request

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
ROOT=TASK.parents[1]
BASE='f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
CC='assets/addons/script.infinity.commandcenter/'
WORK=ROOT/'six502-qa-stage'

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def zipsha(archive,name):
    with archive.open(name) as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def input_paths():
    fixed=['release/stage_combined.py','release/MODULE-REQUEST.json','release/MODULE-REVIEW.json',
           'OWNER-CONSOLIDATED-QA-UPDATE.json','PRESERVATION.json','BASELINE.json',
           'lock/application/stage.py','lock/application/NATIVE.json',
           'lock/verified-classes3.zip','lock/verified-classes7.zip',
           'lock/DEX-CLASSES3-PRESERVATION.json','lock/DEX-BUILD-DIALOG-RETIREMENT.json',
           'lock/patch_main.py','lock/build_dex.py','lock/DEX-BUILD-SELECTION.json',
           'cast/native/InfinityCastRemux.cpp','cast/CAST-PTL-ARM64.json','cast/ASTRA-ELF-REVIEW.json']
    paths={str((TASK/name).relative_to(ROOT)) for name in fixed}
    for directory in ('overlay','lock/java','lock/smali','lock/native','crashes/native'):
        paths.update(str(p.relative_to(ROOT)) for p in (TASK/directory).rglob('*') if p.is_file())
    paths.update(('.github/workflows/infinity-502-combined-stage.yml',
        'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem',
        'repairs/infinity-consolidated-2103500-20261115/stage_fast_qa.py',
        'repairs/dual-experience-isolation-2103420/inventory.py',
        'repairs/dual-experience-isolation-2103420/assemble_modules.py',
        'repairs/dual-experience-isolation-2103420/release_gate.py',
        'repairs/dual-experience-isolation-2103420/component_bundles.py',
        'repairs/infinity-final-closure-2103407/p0/manifest.py'))
    return paths

def main():
    r=load(HERE/'QA-STAGE-REQUEST.json')
    assert r['operation']=='unsigned_combined502_QA_staging' and r['signing'] is False
    assert r['baseline']==2103502 and r['ContinuePlaying']=='DEFERRED_UNCHANGED'
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103502-six-repairs-20261116'
    changed=subprocess.check_output(['git','diff','--name-only',r['source_commit'],os.environ['GITHUB_SHA']],cwd=ROOT,text=True).splitlines()
    assert changed==[str((HERE/'QA-STAGE-REQUEST.json').relative_to(ROOT))]
    assert set(r['inputs'])==input_paths(),'EXACT_SOURCE_INPUT_SET_REQUIRED'
    for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
    review=load(HERE/'STAGE-REVIEW.json')
    assert sha(HERE/'STAGE-REVIEW.json')==r['review_sha256']
    assert review['status']=='PASS_EXACT_UNSIGNED_COMBINED_SCOPE' and review['reviewer']=='Astra'
    canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    assert digest(canonical(r['inputs']))==review['inputs_sha256']
    assert digest(canonical(r['allowed_members']))==review['allowed_members_sha256']
    assert digest(canonical({'modules':r['modules'],'cast':r['cast']}))==review['artifact_bindings_sha256']
    assert r['provisional_versionCode']==2103504 and r['version_reserved'] is False
    WORK.mkdir();evidence=WORK/'evidence';evidence.mkdir()
    stage=module('retained_stage',TASK/'lock/application/stage.py')
    # Retained native verifier writes its three independently checked receipts
    # to this fixed path. Keep it unchanged and capture those real outputs.
    native_evidence=ROOT/'lock-app-work/evidence'
    native_evidence.mkdir(parents=True,exist_ok=False)
    baseline,binding=stage.artifact(WORK,'baseline');engine,native=stage.artifact(WORK,'native')
    for name in ('ARM64.json','SOURCE-PRESERVATION.json','ABI-COMPARISON.json'):
        shutil.copyfile(native_evidence/name,evidence/name)
    assert sha(baseline)==BASE
    def obtain(row,label):
        api=lambda path:json.loads(subprocess.check_output(['gh','api','repos/'+os.environ['GITHUB_REPOSITORY']+'/'+path]))
        a=api('actions/artifacts/'+str(row['artifact']));run=api('actions/runs/'+str(row['run']))
        assert not a['expired'] and a['digest']=='sha256:'+row['archive_sha256']
        assert a['workflow_run']['id']==row['run'] and run['conclusion']=='success' and run['head_sha']==row['source']
        archive=WORK/(label+'.zip')
        req=urllib.request.Request(a['archive_download_url'],headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'})
        with urllib.request.build_opener(stage.SafeRedirect()).open(req,timeout=90) as src,archive.open('wb') as dst:shutil.copyfileobj(src,dst,2*1024*1024)
        assert sha(archive)==row['archive_sha256']
        out=WORK/label;out.mkdir()
        with ZipFile(archive) as z:
            for info in z.infolist():
                path=Path(info.filename)
                assert not path.is_absolute() and '..' not in path.parts and info.file_size<16*1024*1024
                assert (info.external_attr>>16)&0o170000!=0o120000
                z.extract(info,out)
        archive.unlink();return out
    menus=obtain(r['modules'],'menus');cast=obtain(r['cast'],'cast')
    proof=load(menus/'ORIGINAL-SIGNATURE-VERIFICATION.json');root=menus/'modules'
    assert proof['status']=='PASS_ORIGINAL_SIGNED_MODULES_ONLY' and proof['module_version']=='0.3.5.84'
    assert {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}==proof['modules']
    unsigned=dict(proof['modules']);assert unsigned.pop('script.infinity.commandcenter/INFINITY-MODULES.v1.sig')
    assert unsigned==load(HERE/'MODULE-REQUEST.json')['expected_modules'],'REVIEWED_MENU_GENERATION_REQUIRED'
    public=ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'
    assert sha(public)=='bc883be4515d328935b1f3e28294bfc0fe0f2614083274db63b1d24d4da172e8'
    subprocess.run(['openssl','dgst','-sha256','-verify',str(public),'-signature',str(root/'script.infinity.commandcenter/INFINITY-MODULES.v1.sig'),str(root/'script.infinity.commandcenter/INFINITY-MODULES.v1')],check=True,capture_output=True)
    library=cast/'native/libinfinitycastremux.so'
    assert sha(library)=='86a34a4976813f24280345561170b1dee47e96fb9c3b34642190ced2c2fe9ffd'
    assert load(cast/'CAST-PTL-ARM64.json')['source_hashes']['repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp']==sha(TASK/'cast/native/InfinityCastRemux.cpp')
    # Original source-bound DEX artifacts, no Java/D8 build.
    receipt=stage.retained_classes3();dex=Path(load(receipt)['output'])
    with ZipFile(TASK/'lock/verified-classes7.zip') as z:
        assert z.namelist()==['classes7.dex'];(dex/'classes7.dex').write_bytes(z.read('classes7.dex'))
    expected=load(TASK/'lock/DEX-BUILD-DIALOG-RETIREMENT.json')
    for name,h in expected['input_sha256'].items():assert sha(TASK/'lock'/name)==h,name
    for name in ('classes3.dex','classes7.dex'):assert sha(dex/name)==expected['outputs_sha256'][name]
    sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
    from component_bundles import set_version
    from inventory import SIGNATURE,validate_names
    stream=module('existing_stream_writer',ROOT/'repairs/infinity-consolidated-2103500-20261115/stage_fast_qa.py')
    sdk=Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0'
    signature=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(baseline)],text=True)
    assert 'certificate SHA-256 digest: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' in signature
    assert all(any(line.startswith('Verified using v'+str(v)+' scheme') and line.endswith(': true') for line in signature.splitlines()) for v in (1,2,3))
    updates={'lib/arm64-v8a/libkodi.so':engine,'lib/arm64-v8a/libinfinitycastremux.so':library,
             'classes3.dex':dex/'classes3.dex','classes7.dex':dex/'classes7.dex'}
    ledger=load(TASK/'PRESERVATION.json')
    for entry in ledger['authorized_source_overlays']:
        if entry['path'].startswith('overlay/'):
            source=TASK/entry['path'];assert sha(source)==entry['candidate_source_sha256'];updates[entry['APK_member']]=source
    with ZipFile(baseline) as old:
        original=set(validate_names(old))-SIGNATURE
        for rel,wanted in proof['modules'].items():
            target='assets/addons/'+rel
            assert target in original
            if zipsha(old,target)!=wanted:
                assert target in {CC+n for n in ('addon.xml','context.py','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig')}
                updates[target]=root/rel
        updates['AndroidManifest.xml']=set_version(old.read('AndroidManifest.xml'),r['provisional_versionCode'])
        label='assets/experience-component-updates.properties'
        assert old.read(label)==b'infinity.last_updated_in=2103502\ncobra.last_updated_in=2103445\n'
        updates[label]=b'infinity.last_updated_in=2103504\ncobra.last_updated_in=2103445\n'
        assert set(updates)==set(r['allowed_members']),'EXACT_MEMBER_ALLOWLIST_REQUIRED'
        assert 'classes7.dex' not in original
        output=WORK/'Infinity-2103504-Combined-QA-UNSIGNED-NOT-INSTALLABLE.apk'
        with ZipFile(output,'w',allowZip64=True) as out:
            for info in old.infolist():
                if info.filename not in SIGNATURE:stream.write_zip_member(out,info,old,updates.get(info.filename))
            info=ZipInfo('classes7.dex');info.compress_type=ZIP_DEFLATED
            stream.write_zip_member(out,info,old,updates['classes7.dex'])
        with ZipFile(output) as new:
            assert set(validate_names(new))==original|{'classes7.dex'}
            differences={}
            for name in sorted(original|{'classes7.dex'}):
                before=zipsha(old,name) if name in original else None;after=zipsha(new,name)
                value=updates.get(name)
                wanted=sha(value) if isinstance(value,Path) else digest(value) if isinstance(value,bytes) else before
                assert after==wanted,name
                if before!=after:differences[name]={'before':before,'after':after}
            assert set(differences)==set(updates)
    report=dict(status='PASS_UNSIGNED_COMBINED_QA_PRESERVATION_NOT_INSTALLABLE',source=os.environ['GITHUB_SHA'],
        baseline=binding,native=native,modules=r['modules'],cast=r['cast'],changes=differences,
        unchanged_members=len(original)-len(updates)+1,APK_sha256=sha(output),
        package='com.projectinfinity.kodi',provisional_versionCode=2103504,version_reserved=False,
        original_signing='PENDING_EXISTING_OWNER_AUTHORITY_GATES',ContinuePlaying='DEFERRED_NOT_FIXED_UNCHANGED',
        Cobra='UNCHANGED',native_build=False,DEX_build=False,owner_data='NOT_ACCESSED',
        physical_acceptance='PENDING_OWNER',known_limitations=load(TASK/'OWNER-CONSOLIDATED-QA-UPDATE.json')['unresolved_disclosure'])
    (evidence/'COMBINED-QA-STAGING.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'])

if __name__=='__main__':main()
