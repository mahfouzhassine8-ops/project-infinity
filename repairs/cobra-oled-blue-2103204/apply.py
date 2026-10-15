"""Apply only the frozen Java visual delta over the exact locked 2103203 input."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
ACTIVITY = 'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PARENT_COMMIT = '45eac1987c7cd583572d6715eee2ba191130ad71'
RUNTIME_ALLOWLIST = frozenset([
    ACTIVITY,
    'tools/android/packaging/xbmc/src/Splash.java.in',
    'tools/android/packaging/xbmc/src/CobraVisualRenderer.java.in',
])
PROTECTED_CLASSES = (
    'CobraLayoutMath', 'CobraModeLayout', 'CobraLocalTimeshiftSession',
    'CobraTimeshiftTransportPolicy', 'CobraTsParserPolicy',
    'CobraTimelineNormalizerPolicy', 'CobraProviderPacePolicy',
    'CobraNetworkFamilyPolicy', 'CobraCallAudioPolicy',
    'CobraWindowLifecyclePolicy', 'CobraTimeshiftRecoveryPolicy',
    'CobraTimeshiftStallPolicy', 'CobraPreferencePolicy', 'CobraPlaybackPolicy',
)
PROTECTED_METHODS = (
    'buildPlayer', 'cobraActivateLocalTimeshift', 'cobraRecoverLocalTimeshiftSource',
    'cobraFallbackFromLocalTimeshift', 'cobraAttachVideo', 'cobraFitCaptions', 'cobraFitVideo',
    'cobraPrepareMultiForPip', 'cobraRestoreMultiAfterPip', 'cobraPipParams',
    'cobraPipMediaAvailable', 'cobraReleasePipMediaSession', 'cobraPipMediaCallback',
    'cobraDispatchPipCommand', 'cobraPipPlaybackState', 'cobraUpdatePipMediaSession',
    'cobraUserPlay', 'cobraHandleAudioFocus', 'cobraClaimAudioFocus', 'cobraReleaseAudioFocus',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def checked_review():
    reviewed = json.loads((ROOT / 'reviewed.json').read_text())
    require(reviewed.get('status') == 'frozen', 'Visual recipe is blocked until review is frozen')
    require(reviewed['parent_build'] == 2103203 and reviewed['parent_commit'] == PARENT_COMMIT,
            'Wrong reviewed parent')
    require(bool(reviewed['files']) and set(reviewed['files']) <= RUNTIME_ALLOWLIST,
            'Unreviewed runtime owner or empty visual delta')
    require(sha(ROOT / 'visual.patch') == reviewed['patch_sha256'], 'Frozen patch digest drift')
    require(bool(reviewed['test_source_hashes']), 'No frozen visual regressions')
    for name, digest in reviewed['test_source_hashes'].items():
        require(name.startswith('tests/Cobra2103204') and name.endswith('.java') and
                '/' not in name[len('tests/'):], 'Invalid frozen test path')
        require(sha(ROOT / name) == digest, 'Frozen test drift: ' + name)
    return reviewed


def protected_members(before, after):
    spec = importlib.util.spec_from_file_location(
        'member_parser', ROOT.parent / 'cobra-original-player-menu-2103197/apply.py')
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    preserved = {}
    for kind, names in [('class', PROTECTED_CLASSES), ('method', PROTECTED_METHODS)]:
        for name in names:
            old = parser.member(before, name, kind) if kind == 'class' else parser.member(before, name)
            new = parser.member(after, name, kind) if kind == 'class' else parser.member(after, name)
            require(old == new, 'Protected runtime owner changed: ' + name)
            preserved[name] = hashlib.sha256(old.encode()).hexdigest()
    return preserved


def apply(source, receipt, out):
    reviewed = checked_review()
    data = json.loads(receipt.read_text())
    expected = json.loads((ROOT / 'parent-source-hashes.json').read_text())
    require(data['version_code'] == 2103203, 'Wrong parent version')
    require(len(expected) == 21, 'Parent receipt inventory changed')
    require({name: row['after'] for name, row in data['files'].items()} == expected,
            'Wrong parent receipt')
    require(set(reviewed['files']) <= set(expected), 'Changed owner missing from parent receipt')
    for name, digest in expected.items():
        require(sha(source / name) == digest, 'Parent input drift: ' + name)
    for name, row in reviewed['files'].items():
        require(row['before'] == expected[name] and row['after'] != row['before'],
                'Wrong reviewed preimage or empty delta: ' + name)
    before = (source / ACTIVITY).read_text()
    out.mkdir(parents=True, exist_ok=False)
    original = {}
    with zipfile.ZipFile(out / 'pre-change-android-source.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        paths = [path for folder in ['tools/android/packaging', 'media']
                 for path in sorted((source / folder).rglob('*')) if path.is_file()]
        paths.append(source / 'cmake/scripts/android/Install.cmake')
        for path in paths:
            require(not path.is_symlink(), 'Symlinked source input: ' + str(path))
            name = str(path.relative_to(source))
            archive.write(path, name)
            original[name] = sha(path)
        require(len(archive.namelist()) == len(set(archive.namelist())) == 220,
                'Complete parent source backup inventory changed')
    patch = ROOT / 'visual.patch'
    # Reject a patch that changes anything outside its frozen Java file manifest.
    stats = subprocess.run(['git', '-C', str(source), 'apply', '--numstat', str(patch)],
                           check=True, capture_output=True, text=True).stdout.splitlines()
    require({line.split('\t', 2)[-1] for line in stats} == set(reviewed['files']),
            'Patch file inventory differs from frozen manifest')
    subprocess.run(['git', '-C', str(source), 'apply', '--check', str(patch)], check=True)
    subprocess.run(['git', '-C', str(source), 'apply', str(patch)], check=True)
    for name, digest in original.items():
        wanted = reviewed['files'][name]['after'] if name in reviewed['files'] else digest
        require(sha(source / name) == wanted, 'Unexpected patched source input: ' + name)
    preserved = protected_members(before, (source / ACTIVITY).read_text())
    result = {
        'parent_build': 2103203, 'parent_commit': PARENT_COMMIT,
        'files': reviewed['files'], 'protected_runtime_members': preserved,
        'native_engine_recompiled': False, 'timeshift_transport_architecture_changed': False,
        'new_controls': False, 'new_features': False, 'physical_device_verified': False,
    }
    (out / 'patch.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: frozen Java visual delta; exact parent and protected playback owners verified')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--source', type=Path, required=True)
    args.add_argument('--receipt', type=Path, required=True)
    args.add_argument('--out', type=Path, required=True)
    parsed = args.parse_args()
    apply(parsed.source.resolve(), parsed.receipt, parsed.out)
