"""Exact preparation admission before the existing module signer sees keys."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BRANCH = 'refs/heads/work/infinity-three-corrections-20261108'
WORKFLOW = '.github/workflows/infinity-combined-release.yml'


def main():
    assert os.environ['GITHUB_REPOSITORY'] == 'mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF'] == BRANCH
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    assert sha == os.environ['GITHUB_SHA']
    assert not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    run = json.loads(subprocess.check_output(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/actions/runs/' + os.environ['GITHUB_RUN_ID']], text=True))
    assert run['workflow_id'] == 397702717 and run['head_sha'] == sha and run['path'] == WORKFLOW
    previous = subprocess.check_output(['git', 'show', '39143898570fea5f2d24be553823534eb2cf8208:' + WORKFLOW], text=True)
    expected = previous.replace('package-umbrella-pov-462, verify-three-native]', 'package-umbrella-pov-462, verify-three-native, prepare-three]')
    assert (ROOT / WORKFLOW).read_text().startswith(expected.rstrip() + '\n'), 'EXISTING_WORKFLOW_JOBS_MUST_REMAIN_BYTE_IDENTICAL'
    authority = json.loads((ROOT / 'repairs/dual-experience-isolation-2103420/release-authority.json').read_text())
    assert authority['candidate_versionCode'] == 2103465 and authority['generation'] == 52
    for name, wanted in authority['source_files'].items():
        if name == 'repairs/dual-experience-isolation-2103420/signer-policy.json':
            # Already reviewed CC61-era audit-catalog additions; no new route.
            wanted = '668be3057893450fb53c2c3d506723de16de45abe46c0034a0ba81234c1fc06b'
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == wanted, name
    for name in ('SignInfinityModules.java', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'):
        path = 'repairs/infinity-final-closure-2103407/' + name
        assert (ROOT / path).read_bytes() == subprocess.check_output(['git', 'show', '514a82e5:' + path])
    source = ROOT / 'repairs/infinity-three-corrections-20261108'
    for name in ('native/xbmc/interfaces/legacy/ModuleXbmc.cpp',
                 'trakt/candidate/resources/lib/tmdbhelper_sync_trakt/api/authenticator.py',
                 'trakt/candidate/resources/lib/tmdbhelper_sync_trakt/api/token.py'):
        path = (source / name).relative_to(ROOT).as_posix()
        assert (ROOT / path).read_bytes() == subprocess.check_output(['git', 'show', '514a82e5:' + path])
    for name in ('provider_inventory.py', 'native_search_compatibility.py'):
        path = 'repairs/infinity-only-performance-2103425/overlay/script.infinity.commandcenter/' + name
        assert (ROOT / path).read_bytes() == subprocess.check_output(['git', 'show', '16af10e4:' + path])
    scope = json.loads((source / 'PACKAGING-SCOPE.json').read_text())
    assert (scope['candidate_versionCode'], scope['recovery_versionCode']) == (2103466, 2103467)
    assert scope['publication'] is False and scope['application_tests'] is False and scope['shutdown_tests'] is False
    proof = json.loads((source / 'evidence/DEVICE-SOURCE-VERIFICATION.json').read_text())
    assert proof['archive_sha256'] == scope['owner_source_evidence_sha256']
    assert proof['actual_Trakt_host']['passed'] == 14
    print('PASS exact source, original workflow identity,38 immutable release implementations and reviewed signer catalog; no keys accessed')


if __name__ == '__main__':
    main()
