"""Apply the reviewed Activity-only delta over the exact locked 2103202 input."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
ACTIVITY = 'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PARENT_COMMIT = 'd9ce6b04a76f9f7d66bb626f1ce58875432c10f0'
PARENT_ACTIVITY = 'a06f47163875bb001c731e9ffa3b0dc7294676fe2a7a03b066a185c9d7e8ce8b'
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
    'cobraFallbackFromLocalTimeshift', 'cobraAttachVideo',
    'cobraFitCaptions', 'cobraFitVideo',
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def apply(source, receipt, out):
    reviewed = json.loads((ROOT / 'reviewed.json').read_text())
    data = json.loads(receipt.read_text())
    expected = json.loads((ROOT / 'parent-source-hashes.json').read_text())
    require(reviewed['parent_build'] == 2103202 and reviewed['parent_commit'] == PARENT_COMMIT,
            'Wrong reviewed parent')
    require(data['version_code'] == 2103202, 'Wrong parent version')
    require(len(expected) == 21, 'Parent receipt inventory changed')
    require({name: row['after'] for name, row in data['files'].items()} == expected,
            'Wrong parent receipt')
    for name, digest in expected.items():
        require(sha(source / name) == digest, 'Parent input drift: ' + name)
    require(reviewed['parent_activity_sha256'] == PARENT_ACTIVITY,
            'Reviewed Activity is not the locked parent')
    require(sha(source / ACTIVITY) == PARENT_ACTIVITY, 'Wrong Activity parent')
    require(sha(ROOT / 'activity.patch') == reviewed['patch_sha256'], 'Patch changed after review')
    before = (source / ACTIVITY).read_text()
    out.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(out / 'pre-change-android-source.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        for folder in ['tools/android/packaging', 'media']:
            for path in sorted((source / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, str(path.relative_to(source)))
        archive.write(source / 'cmake/scripts/android/Install.cmake', 'cmake/scripts/android/Install.cmake')
        require(len(archive.namelist()) == 220, 'Complete parent source backup inventory changed')
    subprocess.run(['git', '-C', str(source), 'apply', '--check', str(ROOT / 'activity.patch')], check=True)
    subprocess.run(['git', '-C', str(source), 'apply', str(ROOT / 'activity.patch')], check=True)
    require(sha(source / ACTIVITY) == reviewed['activity_sha256'], 'Unexpected patched source')
    for name, digest in expected.items():
        if name != ACTIVITY:
            require(sha(source / name) == digest, 'Unrelated input changed: ' + name)
    spec = importlib.util.spec_from_file_location(
        'member_parser', ROOT.parent / 'cobra-original-player-menu-2103197/apply.py')
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    after = (source / ACTIVITY).read_text()
    preserved = {}
    for kind, names in [('class', PROTECTED_CLASSES), ('method', PROTECTED_METHODS)]:
        for name in names:
            old = parser.member(before, name, kind) if kind == 'class' else parser.member(before, name)
            new = parser.member(after, name, kind) if kind == 'class' else parser.member(after, name)
            require(old == new, 'Protected runtime owner changed: ' + name)
            preserved[name] = hashlib.sha256(old.encode()).hexdigest()
    result = {
        'parent_build': 2103202,
        'parent_commit': PARENT_COMMIT,
        'files': {ACTIVITY: {'before': PARENT_ACTIVITY, 'after': reviewed['activity_sha256']}},
        'protected_runtime_members': preserved,
        'native_engine_recompiled': False,
        'timeshift_transport_architecture_changed': False,
        'user_requested_controls': True,
        'physical_device_verified': False,
    }
    (out / 'patch.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: exact parent delta; protected owners and player factory verified')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--source', type=Path, required=True)
    args.add_argument('--receipt', type=Path, required=True)
    args.add_argument('--out', type=Path, required=True)
    parsed = args.parse_args()
    apply(parsed.source.resolve(), parsed.receipt, parsed.out)
