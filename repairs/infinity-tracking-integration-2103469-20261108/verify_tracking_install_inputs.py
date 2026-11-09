"""Read-only official signed APK intake for the manual post-sign feature job.

No app, signing, authority update or global helper override. Root supplies the
committed enabled request and exact official74/75 producer/artifact pins.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUEST = HERE / 'POST-SIGN-INSTALL-REQUEST.json'
WORKFLOW = '.github/workflows/infinity-saved-navigation-android.yml'
BRANCH = 'work/infinity-tracking-integration-20261108'
REPO = 'mahfouzhassine8-ops/project-infinity'
ORIGINAL = 'a76e29b84996304241e6b309d56a31e6659ad190'
FROZEN = {
    'verify_tracking_install.py': 'ed500734e7c851e4ac157d33b56c3cf1c1cd1ba72117fc470a800f96181265c1',
    'verify_tracking_android.py': '04e736720a44f6a56d99132cce24498c32311ab8df728d8305284a28d4e10315',
    'tracking_android_observer.py': '517e9edf111b129d0907190cf2783d427c4775f78a5f0188416bd4245dcf9b50',
    'qualify_android_baseline.py': '9b4cf409c35688a77e94849361aff510b6b896871314b32b15cc5844b4e23734',
    'stage_tracking_android.py': 'd5d2e8e99721a576e6e52611fa9f0ca8a02a9c89f639f6fe99ba90db020323b8',
}
BASELINE = dict(workflow_id=397702717, workflow_path='.github/workflows/infinity-combined-release.yml', conclusion='success',
    source=ORIGINAL, run_id=42514440156, artifact=dict(id=13631340281,
    name='Infinity-Watchlist-Original-Signed-2103469-42514440156-INTERNAL-QA',
    sha256='f9d054ee500326b77ee2bf4ce8673af2bd54c54115831899d374d931a98dff43', size=329126132))


def require(value, label):
    if not value: raise RuntimeError(label)


def sha(path):
    digest = hashlib.sha256()  # Pre-setup runner Python3.10 has no file_digest.
    with Path(path).open('rb') as stream:
        while data := stream.read(1024 * 1024): digest.update(data)
    return digest.hexdigest()


def load(path): return json.loads(Path(path).read_bytes())


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPO + '/' + path], timeout=30))


def gate():
    require(REQUEST.is_file(), 'POST_SIGN_REQUEST_ABSENT_NO_DOWNLOADS_OR_DEVICE')
    request = load(REQUEST)
    require(request.get('enabled') is True and request.get('application_tests') is True and
            request.get('operation') == 'verify-experimental-tracking-signed-pair-install', 'POST_SIGN_REQUEST_DISABLED_NO_DOWNLOADS_OR_DEVICE')
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REPOSITORY') == REPO and
            os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch',
            'MANUAL_CURRENT_TRACKING_BRANCH_ONLY')
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(head == os.environ['GITHUB_SHA'], 'EXACT_CURRENT_WORKFLOW_SOURCE_NOT_ALTERNATE_REF')
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=no'], text=True).strip(), 'CLEAN_COMMITTED_SOURCE')
    require(sha(ROOT / WORKFLOW) == request['workflow_sha256'], 'EXACT_REVIEWED_MANUAL_FEATURE_WORKFLOW')
    needed = set(FROZEN) | {'verify_tracking_install_inputs.py', 'admit_tracking_android.py',
        'POST-SIGN-INSTALL-SOURCE-REVIEW.json', 'POST-SIGN-INSTALL-HOST.json', 'POST-SIGN-INSTALL-WORKFLOW-REVIEW.json'}
    require(needed <= set(request['source_bindings']), 'EXACT_INTAKE_ROUTING_AND_REVIEW_BINDINGS')
    for relative, wanted in request['source_bindings'].items():
        path = HERE / relative
        require(path.resolve().is_relative_to(HERE.resolve()) and sha(path) == wanted, 'SOURCE_BOUND_BEFORE_IMPORT:' + relative)
    for relative, wanted in FROZEN.items(): require(sha(HERE / relative) == wanted, 'INDEPENDENTLY_FROZEN_READER:' + relative)
    first = ROOT / 'repairs/infinity-final-closure-2103407'
    for relative in ('module_bundle.py', 'FIRSTPARTY-COMPOSITION-PLAN.json', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem', 'p0/manifest.py'):
        path = first / relative
        original = subprocess.check_output(['git', '-C', str(ROOT), 'show', ORIGINAL + ':' + path.relative_to(ROOT).as_posix()])
        require(path.read_bytes() == original, 'SOLE_ORIGINAL_SOURCE_TOOL_BEFORE_IMPORT:' + relative)
    pair = request['official_signed_pair']
    require(set(pair) == {'2103474', '2103475'} and request['official_signing'] == pair['2103475'], 'TWO_OFFICIAL_PRODUCERS_WITH_EXACT75_PRIMARY')
    for row in pair.values():
        require(row['workflow_id'] == 397702717 and row['workflow_path'] == '.github/workflows/infinity-combined-release.yml' and
                row['conclusion'] == 'success' and re.fullmatch(r'[0-9a-f]{40}', row['source']) and type(row['run_id']) is int,
                'EXACT_ORIGINAL_SIGNING_PRODUCER')
        artifact = row['artifact']
        require(type(artifact['id']) is int and re.fullmatch(r'[0-9a-f]{64}', artifact['sha256']) and
                type(artifact['size']) is int and 0 < artifact['size'] <= 2 * 1024**3 and bool(artifact['name']), 'EXACT_WHOLE_SIGNED_ARTIFACT_PIN')
    print('PASS enabled manual request and frozen source/tool gate; no downloads/device')
    return request


def module():
    spec = importlib.util.spec_from_file_location('frozen_post_sign_install', HERE / 'verify_tracking_install.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def download(row, out, tools):
    producer = api('actions/runs/' + str(row['run_id']))
    require(producer['workflow_id'] == row['workflow_id'] and producer['path'] == row['workflow_path'] and
            producer['head_sha'] == row['source'] and producer['status'] == 'completed' and producer['conclusion'] == 'success', 'ACTUAL_COMPLETED_ORIGINAL_PRODUCER')
    wanted = row['artifact']; actual = api('actions/artifacts/' + str(wanted['id']))
    require(actual['id'] == wanted['id'] and not actual['expired'] and actual['workflow_run']['id'] == row['run_id'] and actual['workflow_run']['head_sha'] == row['source'] and
            actual['name'] == wanted['name'] and actual['digest'] == 'sha256:' + wanted['sha256'] and actual['size_in_bytes'] == wanted['size'], 'ACTUAL_WHOLE_ARTIFACT_METADATA')
    out.mkdir(parents=True)
    archive = out / 'artifact.zip'
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', 'repos/' + REPO + '/actions/artifacts/' + str(wanted['id']) + '/zip'], stdout=stream, check=True, timeout=600)
    require(archive.stat().st_size == wanted['size'] and sha(archive) == wanted['sha256'], 'ACTUAL_WHOLE_ARCHIVE_SHA_SIZE')
    with ZipFile(archive) as zipped:
        tools.base.safe_zip(zipped)
        require(all(not item.flag_bits & 1 for item in zipped.infolist()), 'UNENCRYPTED_OFFICIAL_ARCHIVE')
        zipped.extractall(out / 'files')
    (out / 'API-PROVENANCE.json').write_text(json.dumps(dict(run=producer, artifact=actual), indent=2, sort_keys=True) + '\n')
    return out / 'files'


def unique(root, name):
    matches = [path for path in root.rglob(name) if path.is_file()]
    require(len(matches) == 1, 'ONE_EXACT_OFFICIAL_ARTIFACT_MEMBER:' + name)
    return matches[0]


def prepare(sdk, out):
    request = gate()
    require(not out.exists(), 'FRESH_POST_SIGN_INTAKE_DIRECTORY'); out.mkdir(parents=True)
    tools = module()
    tools.checked_request()  # Original frozen helper's independent fixed version/certificate/map scope.
    current = api('actions/runs/' + os.environ['GITHUB_RUN_ID'])
    require(current['workflow_id'] == 393886994 and current['path'] == WORKFLOW and
            current['head_sha'] == os.environ['GITHUB_SHA'] and current['event'] == 'workflow_dispatch', 'ACTUAL_EXISTING_MANUAL_FEATURE_JOB')
    sources = {2103469: download(BASELINE, out / 'original69', tools)}
    for version in (2103474, 2103475):
        sources[version] = download(request['official_signed_pair'][str(version)], out / str(version), tools)
    inputs = out / 'inputs'; inputs.mkdir()
    for expected in request['apks']:
        version = expected['versionCode']; source = sources[version]
        apk = unique(source, expected['filename'])
        require(apk.stat().st_size == expected['size'] and sha(apk) == expected['sha256'], 'OFFICIAL_MEMBER_APK_SHA_SIZE')
        receipt = load(unique(source, 'BUILD-RECEIPT.json'))
        producer = BASELINE if version == 2103469 else request['official_signed_pair'][str(version)]
        require(receipt['versionCode'] == version and receipt['signed_apk_sha256'] == expected['sha256'] and
                receipt['certificate_sha256'] == tools.base.CERT and receipt['source'] == producer['source'] and
                receipt['accepted_pointer_updated'] is False, 'UNCHANGED_ORIGINAL_BUILD_RECEIPT_BINDING')
        shutil.copyfile(apk, inputs / expected['filename'])
        (out / ('BUILD-RECEIPT-' + str(version) + '.json')).write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    dependencies = []; zips = inputs / 'zips'; zips.mkdir()
    pins = load(HERE / 'TRACKING-DEPENDENCY-PINS.json')
    by_id = {row['addon']: row for row in pins['archives']}
    for index, aid in enumerate(pins['installation_order']):
        row = by_id[aid]; name = '%02d-' % index + aid + '-' + row['version'] + '.zip'
        require(row['url'].startswith('https://'), 'PINNED_HTTPS_PUBLISHER_ONLY')
        target = zips / name
        with urllib.request.urlopen(row['url'], timeout=45) as response, target.open('xb') as stream:
            count = 0
            while data := response.read(1024 * 1024):
                count += len(data); require(count <= 64 * 1024 * 1024, 'BOUNDED_PINNED_DEPENDENCY_BYTES'); stream.write(data)
        require(sha(target) == row['sha256'], 'EXACT_UNMODIFIED_PUBLISHER_DEPENDENCY')
        dependencies.append(dict(addon=aid, version=row['version'], archive=name, sha256=row['sha256']))
    payload = dict(status='OFFICIAL_SIGNED_APK_INPUTS_ADMITTED', request_sha256=sha(REQUEST),
        official_signing=request['official_signing'], official_signed_pair=request['official_signed_pair'], apks=request['apks'], dependencies=dependencies)
    (inputs / 'INSTALL-INPUTS.json').write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    # No emulator exists yet. Separate output keeps frozen run()'s fresh-directory
    # invariant; it revalidates actual APKs before any later device action.
    host = out / 'host-preflight'; host.mkdir()
    tools.admit_inputs(inputs, sdk, host)
    proof = dict(status='PASS_OFFICIAL_PAIR_API_ARCHIVES_ORIGINAL_CERT_AND80_HOST_ONLY', request_sha256=sha(REQUEST),
        official_signed_pair=request['official_signed_pair'], baseline=BASELINE, source=os.environ['GITHUB_SHA'],
        inputs=str(inputs.resolve()), application_execution=False, build_sign_dispatch=False)
    (out / 'INTAKE.json').write_text(json.dumps(proof, indent=2, sort_keys=True) + '\n')
    print(proof['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('gate', 'prepare'))
    parser.add_argument('--sdk', type=Path); parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.operation == 'gate': gate()
    else:
        require(args.sdk is not None and args.out is not None, 'HOST_INTAKE_ARGUMENTS')
        prepare(args.sdk, args.out)
