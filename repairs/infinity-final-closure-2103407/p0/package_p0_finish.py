"""Original-key P0 integration/signing; no application or shutdown test runner."""
import argparse, base64, copy, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

HERE=Path(__file__).parent.resolve();ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
import module_bundle
import patch_p0_finish as correction
import manifest

PREFIX='assets/addons/'
CERTIFICATE='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
PARENT_SHA='0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a'
APK_NAME='Infinity-2103420-P0-Corrective-SIGNED.apk'
SIGNATURE={'META-INF/INFINITY.SF','META-INF/INFINITY.RSA','META-INF/MANIFEST.MF'}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for raw in iter(lambda:stream.read(4*1024*1024),b''):h.update(raw)
    return h.hexdigest()

def member_sha(archive,name):
    h=hashlib.sha256()
    with archive.open(name) as stream:
        for raw in iter(lambda:stream.read(4*1024*1024),b''):h.update(raw)
    return h.hexdigest()

def only(root,name):
    paths=list(Path(root).rglob(name))
    if len(paths)!=1:raise ValueError('Exactly one '+name+' required')
    return paths[0]

def run(args,env=None):
    result=subprocess.run(list(map(str,args)),env=env,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    return result.stdout

def read_addon(archive,aid):
    base=PREFIX+aid+'/'
    return {n[len(base):]:archive.read(n) for n in archive.namelist() if n.startswith(base) and not n.endswith('/')}

def write_sources(root,files):
    for name,raw in files.items():
        file=root/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)

def compare(original,candidate,changes):
    old=original.namelist();new=candidate.namelist()
    if len(set(old))!=len(old) or len(set(new))!=len(new):raise ValueError('Duplicate APK member')
    if (set(new)-SIGNATURE)!=(set(old)-SIGNATURE)|{'classes4.dex'}:
        raise ValueError('Unowned APK member addition/removal')
    differences={};preserved=0
    for name in sorted(set(old)-SIGNATURE):
        a=member_sha(original,name);b=member_sha(candidate,name)
        if a==b:preserved+=1;continue
        if name not in changes or b!=correction.digest(changes[name]):raise ValueError('Unexplained APK difference: '+name)
        differences[name]=dict(before=a,after=b)
    if set(differences)!=set(changes)-{'classes4.dex'}:raise ValueError('Declared change budget differs')
    if member_sha(candidate,'classes4.dex')!=correction.digest(changes['classes4.dex']):raise ValueError('New preference helper differs')
    if any(name.endswith('.so') or re.fullmatch(r'classes[0-9]*\.dex',name) for name in differences):
        raise ValueError('Frozen original native/DEX member changed')
    if any('cobra' in name.lower() for name in differences):raise ValueError('Cobra member changed')
    return dict(preserved_parent_members=preserved,explained_differences=differences,
        added_members={'classes4.dex':member_sha(candidate,'classes4.dex')},unexpected_differences=[],
        all_original_native_and_DEX_members_byte_identical=True,all_shutdown_implementation_members_byte_identical=True,
        chooser_and_Cobra_members_changed=[],all_existing_Power_Close_Force_nodes_identical=True,
        user_data_modified=False,shutdown_tests='NOT_SELECTED_NOT_RUN')

def compile_preference(sdk,android,out):
    if sha(android)!='6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad':
        raise ValueError('Existing pinned Android34 signature jar required')
    d8=sdk/'lib/d8.jar'
    if sha(d8)!='305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5':
        raise ValueError('Existing pinned build-tools35 compiler required')
    java=Path(os.environ['JAVA_HOME'])/'bin/java'
    classes=out/'preference-classes';classes.mkdir()
    run([java,'-m','jdk.compiler/com.sun.tools.javac.Main','--release','8','-g:none',
        '-Xlint:all,-options','-Werror','-cp',android,'-d',classes,
        HERE/'InfinityAskEveryTimeActivity.java',HERE/'InfinityJavaPersistence.java'])
    expected={'InfinityAskEveryTimeActivity.class','InfinityJavaPersistence.class'}
    if {p.name for p in classes.rglob('*.class')}!=expected:raise ValueError('Unexpected preference class inventory')
    dex=out/'preference-dex';dex.mkdir()
    # Input ONLY the new Activity. The compile-only stub can never enter DEX.
    run([java,'-cp',d8,'com.android.tools.r8.D8','--release','--min-api','21','--lib',android,
        '--classpath',classes,'--output',dex,classes/'com/projectinfinity/kodi/InfinityAskEveryTimeActivity.class'])
    result=(dex/'classes.dex').read_bytes()
    if len(list(dex.iterdir()))!=1:raise ValueError('Unexpected isolated DEX output')
    return result

def archive_extra(root,aid,version,out):
    file=out/(aid+'-'+version+'.zip')
    with ZipFile(file,'w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
        for source in sorted((root/aid).rglob('*')):
            if not source.is_file():continue
            info=ZipInfo(source.relative_to(root).as_posix(),date_time=(2026,10,26,0,0,0))
            info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,source.read_bytes())
    return file

def build(parent_root,sdk,android,out):
    parent_root=Path(parent_root).resolve();sdk=Path(sdk).resolve();out=Path(out).absolute()
    parent=only(parent_root,'Infinity-2103419-Home-Playlist-Corrective-VERIFICATION.apk')
    if sha(parent)!=PARENT_SHA:raise ValueError('Exact signed419 parent required')
    prior=json.loads(only(parent_root,'APK-PRESERVATION.json').read_text())
    if (prior.get('candidate_APK_sha256')!=PARENT_SHA or prior.get('source_commit')!='a24db78554da7bc40a2a0b658ba441793f1c1605'
        or str(prior.get('build'))!='40396544415' or prior.get('unexpected_differences')!=[]
        or prior.get('original_certificate_sha256')!=CERTIFICATE):raise ValueError('Exact419 source/build binding required')
    for name,pin in prior['component_sha256'].items():
        if sha(only(parent_root,name))!=pin:raise ValueError('Parent component digest differs')
    cert=re.compile(r'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]{64})')
    signature=run([sdk/'apksigner','verify','--verbose','--print-certs',parent])
    if cert.search(signature)[1].lower()!=CERTIFICATE:raise ValueError('Parent permanent signer differs')
    out.mkdir(parents=True,exist_ok=False)
    addons=out/'assets/addons';addons.mkdir(parents=True)
    with ZipFile(parent) as archive:
        before={aid+'/'+n:raw for aid in module_bundle.IDS for n,raw in read_addon(archive,aid).items()}
        revised=correction.firstparty(before);write_sources(addons,revised)
        payload,_=module_bundle.build(addons)
        # First authenticate the untouched parent generation, not a new claim.
        parent_addons=out/'parent-authentication';write_sources(parent_addons,before)
        old_payload,_=module_bundle.build(parent_addons)
        if old_payload!=before[correction.CC+'/'+module_bundle.MANIFEST]:raise ValueError('Parent inventory differs')
        run(['openssl','dgst','-sha256','-verify',ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
            '-signature',parent_addons/correction.CC/(module_bundle.MANIFEST+'.sig'),
            parent_addons/correction.CC/module_bundle.MANIFEST])
        for leaf in (module_bundle.MANIFEST,module_bundle.MANIFEST+'.sig'):(addons/correction.CC/leaf).unlink()
        module_bundle.prepare(addons)
        for aid,fun in ((correction.HC,correction.health),(correction.SKIN,correction.skin)):
            result=fun(read_addon(archive,aid))
            if isinstance(result,tuple):
                result,proof=result;(out/'SKIN-P0-PRESERVATION.json').write_text(json.dumps(proof,indent=2)+'\n')
            write_sources(out/'presentation'/aid,result)
    java=Path(os.environ['JAVA_HOME'])/'bin/java'
    with tempfile.TemporaryDirectory(prefix='infinity420-original-key-') as temp:
        work=Path(temp);key=work/'original.jks';key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));key.chmod(0o600)
        classes=work/'classes';classes.mkdir()
        run([java,'-m','jdk.compiler/com.sun.tools.javac.Main','--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,ROOT/'SignInfinityModules.java'])
        env={k:os.environ[k] for k in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')}
        (out/'ORIGINAL-MODULE-SIGNATURE.txt').write_text(run([java,'-cp',classes,'SignInfinityModules',key,addons/correction.CC/module_bundle.MANIFEST],env))
    verifier=out/'verify-native-bundle'
    run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',ROOT/'verify_module_bundle.cpp',
        ROOT/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',verifier])
    (out/'MODULE-NATIVE-AUTHENTICATION.txt').write_text(run([verifier,addons,ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem']))
    components=out/'components';module_bundle.archive(addons,components)
    for file in list(components.iterdir()):file.rename(components/file.name.replace('-2103409-QA.zip','-2103420.zip'))
    archive_extra(out/'presentation',correction.SKIN,'1.0.5.247',components)
    archive_extra(out/'presentation',correction.HC,'2.5.27',components)
    new_dex=compile_preference(sdk,Path(android).resolve(),out)
    plan=json.loads(correction.PLAN.read_text());owned={PREFIX+n for n in plan['source_preimages']}
    owned.update((PREFIX+correction.CC+'/'+module_bundle.MANIFEST,PREFIX+correction.CC+'/'+module_bundle.MANIFEST+'.sig'))
    changes={}
    with ZipFile(parent) as original:
        for name in owned:
            relative=name[len(PREFIX):]
            root=addons if relative.split('/')[0] in module_bundle.IDS else out/'presentation'
            raw=(root/relative).read_bytes()
            if raw==original.read(name):raise ValueError('Unnecessary declared P0 modification: '+name)
            changes[name]=raw
        changes['AndroidManifest.xml']=manifest.patch(original.read('AndroidManifest.xml'))
        changes['classes4.dex']=new_dex
        unsigned=out/'unsigned.apk'
        with ZipFile(unsigned,'w',allowZip64=True) as writer:
            for info in original.infolist():
                if info.filename in SIGNATURE:continue
                with writer.open(copy.copy(info),'w',force_zip64=info.file_size>=2**31) as target:
                    if info.filename in changes:target.write(changes[info.filename])
                    else:
                        with original.open(info) as source:shutil.copyfileobj(source,target,4*1024*1024)
            writer.writestr('classes4.dex',new_dex,compress_type=ZIP_DEFLATED)
        with ZipFile(unsigned) as candidate:compare(original,candidate,changes)
    aligned=out/'aligned.apk';run([sdk/'zipalign','-P','16','-f','4',unsigned,aligned])
    final=out/APK_NAME
    with tempfile.TemporaryDirectory(prefix='infinity420-apk-sign-') as temp:
        key=Path(temp)/'original.jks';key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'],validate=True));key.chmod(0o600)
        env={k:os.environ[k] for k in ('PATH','JAVA_HOME','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD')}
        run([sdk/'apksigner','sign','--ks',key,'--ks-key-alias',os.environ['INFINITY_KEY_ALIAS'],
            '--ks-pass','env:INFINITY_STORE_PASSWORD','--key-pass','env:INFINITY_KEY_PASSWORD',
            '--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true',
            '--out',final,aligned],env)
    signed=run([sdk/'apksigner','verify','--verbose','--print-certs',final])
    if cert.search(signed)[1].lower()!=CERTIFICATE:raise ValueError('Permanent signer changed')
    run([sdk/'zipalign','-c','-P','16','4',final])
    badging=run([sdk/'aapt','dump','badging',final])
    if not re.search(r"^package: name='com.projectinfinity.kodi' versionCode='2103420'",badging,re.M) or "native-code: 'arm64-v8a'" not in badging:
        raise ValueError('Install-over package/ABI differs')
    xml=run([sdk/'aapt','dump','xmltree',final,'AndroidManifest.xml'])
    if xml.count(manifest.CLASS)!=1:raise ValueError('Private preference activity absent/duplicated')
    with ZipFile(parent) as original,ZipFile(final) as candidate:
        report=compare(original,candidate,changes)
        for file in components.glob('*.zip'):
            with ZipFile(file) as component:
                for name in component.namelist():
                    if not name.endswith('/') and correction.digest(component.read(name))!=member_sha(candidate,PREFIX+name):
                        raise ValueError('Component/APK member mismatch: '+name)
    report.update(source_commit=os.environ.get('GITHUB_SHA'),build=os.environ.get('GITHUB_RUN_ID'),
        baseline_APK_sha256=PARENT_SHA,candidate_APK_sha256=sha(final),original_certificate_sha256=CERTIFICATE,
        ARM64=True,zip_page_alignment=16384,native_ELF_page_alignment='UNCHANGED_PARENT_4K_LIMITATION',
        component_sha256={p.name:sha(p) for p in components.iterdir()},
        runtime_verification='NOT RUN IN PACKAGING',physical_Fold='USER_FINAL_ACCEPTANCE_PENDING',final_lock=False)
    (out/'APK-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'ORIGINAL-SIGNATURE.txt').write_text(signature);(out/'NEW-SIGNATURE.txt').write_text(signed)
    (out/'MANIFEST.txt').write_text(xml)
    (out/'SHA256SUMS').write_text(sha(final)+'  '+final.name+'\n'+''.join(sha(p)+'  components/'+p.name+'\n' for p in sorted(components.iterdir())))
    for name in ('INSTALLATION.txt','REQUIREMENT-LEDGER.md'):
        shutil.copyfile(HERE/name,out/name)
    unsigned.unlink();aligned.unlink()
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('parent_root','sdk','android','out'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    result=build(**vars(parser.parse_args()))
    print(json.dumps({k:v for k,v in result.items() if k!='explained_differences'},indent=2))
