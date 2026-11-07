"""Actual unchanged Java installer, original-signed ZIPs, disposable host files.

No Android GUI execution, application shutdown, user profile or signing keys.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

def audit(root,seed,publish,previous,out):
    first=root/'repairs/infinity-final-closure-2103407'
    sys.path.insert(0,str(first))
    import module_dex
    ids=('script.infinity.commandcenter','script.infinity.rails','script.infinity.uirepair','script.infinity.watchedbridge')
    cc=ids[0];out.mkdir(exist_ok=False)
    # Only the Info skin changed after run42281237899. Reuse its real Java
    # cases only when BOTH complete module payloads and every Java source are
    # identical. Skin hashes/forward version and RSA are checked afresh elsewhere.
    reference_path=Path(__file__).with_name('CC-AUDIT-REFERENCE.json')
    if reference_path.is_file():
        reference=json.loads(reference_path.read_text())
        assert reference['run_id']==42281237899 and reference['artifact_id']==13535786340
        with Path(seed).open('rb') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==reference['seed_apk_sha256']
        assert hashlib.sha256(module_dex.source().encode()).hexdigest()==reference['java_source_sha256']
        assert {str(f.relative_to(first)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (first/'host-java').rglob('*.java')}==reference['host_java_sha256']
        def payload_hashes(path):
            with ZipFile(path) as z:return {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
        # The 268 Search repair changes authenticated CC code. Its 266 Java
        # host evidence MUST NOT be reused; rerun the six actual Java checks.
        unchanged_candidate = payload_hashes(next(publish.glob(cc+'-*-corrective.zip')))==reference['candidate']
        unchanged_recovery = payload_hashes(next(publish.glob(cc+'-*-recovery.zip')))==reference['recovery']
        if unchanged_candidate and unchanged_recovery:
            report=reference['report']
            report['evidence_reused']=dict(run_id=reference['run_id'],artifact_id=reference['artifact_id'],
                artifact_sha256=reference['artifact_sha256'],CC_payloads_and_Java_sources='EXACTLY_IDENTICAL',tests_rerun=False)
            (out/'RECOVERY-VERIFIED.json').write_text(json.dumps(report,indent=2)+'\n')
            shutil.copyfile(out/'RECOVERY-VERIFIED.json',publish/'RECOVERY-VERIFIED.json')
            print('REUSE six real-Java recovery cases: both CC payloads and all Java sources exactly identical')
            return
        print('CHANGED authenticated Command Center payload: six real-Java installer/recovery checks required')
    rows=[]
    with tempfile.TemporaryDirectory(dir=out) as temp:
        temp=Path(temp);assets=temp/'assets';addons=assets/'addons';addons.mkdir(parents=True)
        with ZipFile(seed) as z:
            for n in z.namelist():
                if n.startswith(tuple('assets/addons/'+a+'/' for a in ids)) and not n.endswith('/'):
                    p=addons/n.removeprefix('assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
        source=temp/'InfinityInstalledCheckpointInstaller.java';source.write_text(module_dex.source())
        classes=temp/'classes';classes.mkdir()
        subprocess.run(['javac','--release','8','-g:none','-d',str(classes),str(source),*map(str,(first/'host-java').rglob('*.java'))],check=True)
        def files(path):
            with ZipFile(path) as z:return {n:z.read(n) for n in z.namelist() if not n.endswith('/')}
        baseline=files(previous/(cc+'-0.3.5.61-2103460-corrective.zip'))
        candidate=files(next(publish.glob(cc+'-*-corrective.zip')))
        recovery=files(next(publish.glob(cc+'-*-recovery.zip')))
        assert baseline==recovery,'RECOVERY_MUST_RESTORE_EXACT_PHYSICAL_PASS_CC_PAYLOAD'
        def put(directory,content):
            for n,raw in content.items():(directory/n).write_bytes(raw)
        def fixture(label):
            storage=temp/label;shutil.copytree(addons,storage/'.kodi/addons')
            put(storage/'.kodi/addons',baseline)
            sentinel=storage/'.kodi/userdata/unchanged-data';sentinel.parent.mkdir();sentinel.write_bytes(b'host-only profile sentinel')
            return storage,sentinel
        def call(storage):
            return subprocess.run(['java','-cp',str(classes),'com.projectinfinity.kodi.Main',str(storage),str(assets)],capture_output=True,text=True)
        def snap(storage):
            return {str(p.relative_to(storage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in storage.rglob('*') if p.is_file()}
        for label,content in [('authenticated_current262_generation',baseline),('complete_fold_corrective_generation',candidate)]:
            storage,sentinel=fixture(label);put(storage/'.kodi/addons',content);before=sentinel.read_bytes()
            result=call(storage);assert result.returncode==0,result.stderr
            assert sentinel.read_bytes()==before
            rows.append(dict(case=label,status='PASS_HOST_REAL_JAVA_INSTALLER',user_data_sentinel_unchanged=True))
        for label,leaf in [('manifest_pair_interruption','INFINITY-MODULES.v1'),('source_pair_interruption','context.py')]:
            storage,sentinel=fixture(label)
            assert candidate[cc+'/'+leaf]!=baseline[cc+'/'+leaf]
            (storage/'.kodi/addons'/cc/leaf).write_bytes(candidate[cc+'/'+leaf])
            before=snap(storage);result=call(storage)
            assert result.returncode!=0,'PARTIAL_GENERATION_MUST_BE_REJECTED'
            assert snap(storage)==before,'REFUSAL_MUST_PRESERVE_UNKNOWN_SOURCE_AND_DATA'
            rows.append(dict(case=label,status='REFUSED_AS_REQUIRED',files_and_data_unchanged=True))
            saved=sentinel.read_bytes();put(storage/'.kodi/addons',recovery)
            result=call(storage);assert result.returncode==0,result.stderr
            assert sentinel.read_bytes()==saved
            assert all((storage/'.kodi/addons'/n).read_bytes()==raw for n,raw in baseline.items())
            rows.append(dict(case=label+'_forward_recovery',status='PASS_HOST_ZIP_TRANSPORT_AND_REAL_JAVA',
                             exact_CC262_function_restored=True,user_data_sentinel_unchanged=True))
    report=dict(status='PASS_SIX_HOST_INSTALLER_AND_RECOVERY_CASES',tests=rows,
        actual_Android_GUI='NOT_RUN',physical_Fold='NOT_RUN',shutdown_tests='NOT_RUN',
        original_production_installer_changed=False,keys_accessed=False,
        recovery_reference='authenticated currently installed CC61/skin262, not original460 functionality')
    (out/'RECOVERY-VERIFIED.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(out/'RECOVERY-VERIFIED.json',publish/'RECOVERY-VERIFIED.json')
    print('PASS six focused host checks with real unchanged Java installer and exact previous CC recovery; Android NOT RUN')
