"""Original signed generations on disposable host adapters; never Android PASS."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import release_controlled as r
import module_dex


def snapshot(root):
    return {p.relative_to(root).as_posix():r.file_sha(p) for p in root.rglob('*') if p.is_file()}


def verify_recovery(baseline,out,verifier):
    results=[]
    def check(name,condition):
        r.require(condition,'RECOVERY:'+name);results.append(dict(check=name,result='PASS'))
    with tempfile.TemporaryDirectory(prefix='infinity-ui-recovery-host-') as tmp:
        root=Path(tmp);storage=root/'storage';addons=storage/'.kodi/addons';addons.mkdir(parents=True)
        assets={v:out/str(v)/'modules' for v in r.VERSIONS}
        with ZipFile(baseline) as z:
            for n in z.namelist():
                if n.startswith('assets/addons/') and n.split('/')[2] in r.module_bundle.IDS:
                    p=addons/n.removeprefix('assets/addons/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
        userdata=storage/'.kodi/userdata';userdata.mkdir()
        sentinel=userdata/'unchanged-profile-database-sentinel';sentinel.write_bytes(b'Existing settings and watched data are never migration inputs.')
        sentinel_hash=r.file_sha(sentinel)
        original=module_dex.source();src=root/'InfinityInstalledCheckpointInstaller.java';src.write_text(original)
        classes=root/'classes';classes.mkdir()
        r.cmd('javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,src,*sorted((r.FIRST/'host-java').rglob('*.java')))
        def call(v,fail=None):
            env=dict(os.environ)
            if fail is not None:env['INFINITY_HOST_FAIL_RENAME']=str(fail)
            asset_root=root/('assets-'+str(v));asset_root.mkdir(exist_ok=True)
            link=asset_root/'addons'
            if not link.exists():link.symlink_to(assets[v].resolve(),target_is_directory=True)
            return subprocess.run(['java','-cp',str(classes),'com.projectinfinity.kodi.Main',str(storage),str(asset_root)],text=True,capture_output=True,env=env)
        first=call(2103456)
        check('actual_original_key_adapter_installs_candidate',first.returncode==0 and 'VERIFIED_VERSION=0.3.5.57' in first.stdout)
        check('native_module_verifier_accepts_installed_candidate',subprocess.run([str(verifier),str(addons),str(r.FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem')],capture_output=True).returncode==0)
        old_manifest=r.file_sha(addons/r.module_bundle.CC/r.module_bundle.MANIFEST)
        # Metadata backups (2), addon backup (1), addon replacement (1), then
        # interrupt the next write: exercise a genuinely mixed code generation.
        fail=call(2103457,fail=5)
        check('interrupted_recovery_is_reported_not_success',fail.returncode!=0 and 'Injected host atomic-write failure' in fail.stderr)
        check('interruption_occurred_after_source_write_before_manifest_commit',
              b'version="0.3.5.58"' in (addons/r.module_bundle.CC/'addon.xml').read_bytes()
              and r.file_sha(addons/r.module_bundle.CC/r.module_bundle.MANIFEST)==old_manifest)
        recovered=call(2103457)
        check('same_recovery_resumes_interrupted_write',recovered.returncode==0 and 'VERIFIED_VERSION=0.3.5.58' in recovered.stdout)
        check('native_module_verifier_accepts_recovery',subprocess.run([str(verifier),str(addons),str(r.FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem')],capture_output=True).returncode==0)
        check('all_recovery_signed_files_installed_exactly',all((addons/p.relative_to(assets[2103457])).read_bytes()==p.read_bytes() for p in assets[2103457].rglob('*') if p.is_file()))
        check('previous_authenticated_generation_backed_up',(addons/'.infinity-module-previous'/old_manifest/'INFINITY-MODULES.v1').exists())
        check('userdata_sentinel_preserved',r.file_sha(sentinel)==sentinel_hash)
        before=snapshot(storage);downgrade=call(2103456)
        check('older_module_does_not_replace_recovery',downgrade.returncode==0 and 'VERIFIED_VERSION=0.3.5.58' in downgrade.stdout and snapshot(storage)==before)
        # Verify an actually retained candidate helper cannot enter the restored
        # authenticated service. This uses original contract code and signed files.
        leftover=addons/r.module_bundle.CC/'media_view.py'
        check('candidate_helper_retained_without_destructive_cleanup',leftover.exists())
        contract_path=addons/r.module_bundle.CC/'module_contract.py'
        spec=importlib.util.spec_from_file_location('_recovery_contract',contract_path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        manifest=addons/r.module_bundle.CC/r.module_bundle.MANIFEST;raw=manifest.read_bytes()
        files={line.split('\t')[2]:line.split('\t')[1] for line in raw.decode().splitlines() if line.startswith('file\t')}
        identity=module.Identity('0.3.5.58',1,r.digest(raw));contract=module.Contract(addons,identity,files,{},set())
        denied=False
        try:contract.source(r.module_bundle.CC+'/media_view.py')
        except module.ContractRejected as e:denied='unlisted' in str(e)
        check('leftover_helper_rejected_by_original_import_contract',denied)
        tamper=addons/r.module_bundle.CC/'common.py';saved=tamper.read_bytes();tamper.write_bytes(saved+b'\n# unknown local edit\n')
        before=snapshot(storage);rejected=call(2103457)
        check('unknown_source_refused_without_overwrite',rejected.returncode!=0 and snapshot(storage)==before)
        tamper.write_bytes(saved)
        sig=assets[2103457]/r.module_bundle.CC/(r.module_bundle.MANIFEST+'.sig');saved_sig=sig.read_bytes()
        try:
            sig.write_bytes(bytes([saved_sig[0]^1])+saved_sig[1:]);before=snapshot(storage);bad=call(2103457)
            check('invalid_original_signature_refused_without_writes',bad.returncode!=0 and snapshot(storage)==before)
        finally:sig.write_bytes(saved_sig)
        check('no_user_data_loss_after_all_negative_cases',r.file_sha(sentinel)==sentinel_hash)
    # Restored skin entry points cannot reach stale UI helpers/windows. The
    # baseline bytes are the recovery bytes; no broad cleanup is introduced.
    needles=[b'media_view',b'infinity_library_navigation',b'InfinityMediaView',b'Infinity.MediaView.Default',
             b'Includes_InfinityMediaLists',b'Includes_InfinityVideoOptions']
    references=[]
    with ZipFile(baseline) as z:
        for n in z.namelist():
            if n.startswith((r.CC,r.SKIN)) and n.endswith(('.xml','.py')):
                raw=z.read(n)
                if any(x in raw for x in needles) or re.search(rb'(?:ActivateWindow|Dialog\.Close)\(113[678](?:[,)]|\s)',raw):references.append(n)
    check('restored_source_has_no_candidate_helper_or_window_routes',not references)
    dialogs=[]
    for p in (r.UI/'overlay'/r.SKIN/'unified').glob('custom_113*.xml'):
        node=ET.fromstring(p.read_bytes());dialogs.append(node.get('id'))
        check('retained_dialog_'+node.get('id')+'_has_no_auto_visibility',node.get('type')=='dialog' and node.find('visible') is None)
    check('exact_three_candidate_only_dialogs',set(dialogs)=={'1136','1137','1138'})
    return dict(status='PASS_ORIGINAL_KEY_HOST_RECOVERY_AND_ENTRY_REACHABILITY',checks=results,
        original_key_replaced=False,installer_source_sha256=r.digest(original.encode()),
        source_template_sha256=r.file_sha(r.FIRST/'InfinityInstalledModules.java.in'),
        userdata_accessed='Disposable sentinel only; no real profile or database opened',
        Android='NOT_RUN_NO_CONNECTED_COMPATIBLE_TARGET',physical_recovery='PENDING',
        limits=['Host POSIX adapter execution validates original installer algorithm/JCA signatures, not Android ABI or actual Fold installation.',
                'Retained first-party helper is denied by restored authenticated import contract; baseline routes do not reach candidate-only skin code and modal dialogs have no automatic visibility.',
                'This is not a sandbox claim against deliberate manual RunScript/ActivateWindow calls or third-party scripts with arbitrary execution privileges.',
                'Actual installed skin generation selection, window registration and install-over recovery require physical Android verification.',
                'Cannot recover unsaved in-memory data; unresolved checkpoint obligations remain blocking.'],
        Scudo='UNRESOLVED_NOT_CHANGED',accepted_pointer_updated=False)
