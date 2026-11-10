"""Four affected original-installer cases; requires the original signed manifests."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import prepare_modules as prep


def load(path):
    return json.loads(path.read_bytes())


def verify(root):
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify',
                    str(prep.ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                    '-signature', str(root/prep.CC/'INFINITY-MODULES.v1.sig'),
                    str(root/prep.CC/'INFINITY-MODULES.v1')], check=True, capture_output=True)


def audit(prepared, out):
    assert not out.exists()
    t = prep.tools()
    path = prep.ROOT/'repairs/infinity-tracking-integration-2103469-20261108/verify_tracking_modules.py'
    frozen = subprocess.check_output(['git', 'show', '0245abf5e4a10d490bd38677b118e873c01e5504:'+path.relative_to(prep.ROOT).as_posix()], cwd=prep.ROOT)
    assert path.read_bytes() == frozen, 'UNCHANGED_RETAINED_INSTALLER_VERIFICATION_ADAPTER'
    spec = importlib.util.spec_from_file_location('original_installer_tools_only', path)
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    bundle, java_source, reference, host, original_tools = old.original_tools()
    stage = load(prepared/'PREPARATION.json')
    signed = {}
    for label, version in prep.PAIRS:
        count = 80
        work = prepared/label
        assert prep.sha((work/'INPUTS.json').read_bytes()) == stage['inputs'][label]
        pins = load(work/'INPUTS.json'); root = work/'modules'
        current = prep.hashes(root)
        assert {n:v for n,v in current.items() if n != prep.CC+'/INFINITY-MODULES.v1.sig'} == pins['modules']
        payload, files = bundle.build(root)
        assert len(files) == count and prep.sha(payload) == pins['manifest_sha256']
        assert payload == (root/prep.CC/'INFINITY-MODULES.v1').read_bytes()
        verify(root)
        signed[label] = dict(version=version, files=current,
                             manifest_sha256=prep.sha(payload),
                             signature_sha256=current[prep.CC+'/INFINITY-MODULES.v1.sig'])
    verify(prepared/'baseline-modules')
    out.mkdir(parents=True)
    rows = []
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        tmp = Path(temporary)
        java = tmp/'InfinityInstalledCheckpointInstaller.java'; java.write_text(java_source)
        classes = tmp/'classes'; classes.mkdir()
        first = prep.ROOT/'repairs/infinity-final-closure-2103407'
        subprocess.run(['javac', '--release', '8', '-g:none', '-d', str(classes), str(java),
                        *map(str, sorted((first/'host-java').rglob('*.java')))], check=True)
        storage = tmp/'device'
        shutil.copytree(prepared/'baseline-modules', storage/'.kodi/addons')
        sentinels = {
            '.kodi/userdata/addon_data/'+prep.CC+'/settings.xml': b'<settings><setting id="performance_fixture">auto</setting><setting id="retained">yes</setting></settings>',
            '.kodi/userdata/addon_data/'+prep.CC+'/continue-watching.json': b'{"schema":2,"revision":17,"retain":"tracking"}',
            '.kodi/userdata/Database/retain.db': b'disposable database byte sentinel',
            '.kodi/userdata/guisettings.xml': b'<settings>retain skin and navigation</settings>',
            '.kodi/addons/plugin.video.sentinel/source.py': b'# unrelated provider source\n',
            '.kodi/addons/'+prep.CC+'/unknown-user-file.txt': b'retain unknown data'}
        for name, raw in sentinels.items():
            p = storage/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
        def apply(label):
            assets = tmp/('assets-'+label)
            if not assets.exists():
                shutil.copytree(prepared/label/'modules', assets/'addons')
            result = subprocess.run(['java', '-cp', str(classes), 'com.projectinfinity.kodi.Main',
                                     str(storage), str(assets)], capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, result.stderr
            return result.stdout
        def check(label):
            assert 'VERIFIED_VERSION='+signed[label]['version'] in apply(label)
            for name, raw in sentinels.items():
                assert (storage/name).read_bytes() == raw, name
            for name, wanted in signed[label]['files'].items():
                assert prep.sha((storage/'.kodi/addons'/name).read_bytes()) == wanted, name
        check('candidate')
        rows.append(dict(case='signed75_to_performance78_complete80_preserves_data', status='PASS_REAL_ORIGINAL_JAVA'))
        before = prep.hashes(storage); check('candidate'); assert prep.hashes(storage) == before
        rows.append(dict(case='same_candidate_noop', status='PASS_REAL_ORIGINAL_JAVA'))
        check('recovery')
        rows.append(dict(case='higher79_restores_original75_functionality_with_data', status='PASS_REAL_ORIGINAL_JAVA'))
        before = prep.hashes(storage)
        assert 'VERIFIED_VERSION='+signed['recovery']['version'] in apply('candidate')
        assert prep.hashes(storage) == before
        rows.append(dict(case='older78_cannot_overwrite_authenticated79_recovery', status='PASS_NO_WRITE'))
    prep.save(out/'MODULE-UPGRADE-RECOVERY.json', dict(
        status='PASS_FOUR_AFFECTED_ORIGINAL_INSTALLER_CASES', cases=rows,
        original_generated_java_sha256=prep.sha(java_source.encode()),
        original_host_java=host, original_tools=original_tools, signed_inputs=signed,
        baseline=2103477, original_installer_changed=False, user_data_modified=False,
        Android='NOT_RUN_BY_THIS_HOST_TEST', APK=False, registry_mutation=False))
    print('PASS original signatures and four real Java generation/recovery cases; Android acceptance remains pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args(); audit(args.prepared, args.out)
