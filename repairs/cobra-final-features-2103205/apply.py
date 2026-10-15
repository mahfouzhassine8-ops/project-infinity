"""Apply the frozen, user-requested Java extension over exact locked 2103204."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
ACTIVITY = 'tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
INSTALL = 'cmake/scripts/android/Install.cmake'
PARENT_COMMIT = '166cf9dad40a8a0333563830a3c0965ce4e81da6'
RUNTIME_ALLOWLIST = frozenset([
    ACTIVITY,
    'tools/android/packaging/xbmc/src/Splash.java.in',
    'tools/android/packaging/xbmc/src/CobraVisualRenderer.java.in',
    'tools/android/packaging/xbmc/src/CobraVisualTheme.java.in',
    'tools/android/packaging/xbmc/src/CobraVisualScene.java.in',
    INSTALL,
])
PROTECTED_CLASSES = (
    'CobraLayoutMath', 'CobraModeLayout', 'CobraLocalTimeshiftSession',
    'CobraTimeshiftTransportPolicy', 'CobraTsParserPolicy',
    'CobraTimelineNormalizerPolicy', 'CobraProviderPacePolicy',
    'CobraNetworkFamilyPolicy', 'CobraCallAudioPolicy',
    'CobraWindowLifecyclePolicy', 'CobraTimeshiftRecoveryPolicy',
    'CobraTimeshiftStallPolicy', 'CobraPreferencePolicy', 'CobraPlaybackPolicy',
    'CobraProviderConnection', 'CobraSniSocketFactory', 'CobraTsTimelinePolicy',
    'CobraStreamCadencePolicy', 'CobraLiveRewindPolicy', 'CobraFoldAspectPolicy',
    'CobraRefreshPolicy',
)
PROTECTED_METHODS = (
    'buildPlayer', 'cobraActivateLocalTimeshift', 'cobraRecoverLocalTimeshiftSource',
    'cobraFallbackFromLocalTimeshift', 'cobraAttachVideo', 'cobraFitCaptions', 'cobraFitVideo',
    'cobraPrepareMultiForPip', 'cobraRestoreMultiAfterPip', 'cobraPipParams',
    'cobraPipMediaAvailable', 'cobraReleasePipMediaSession', 'cobraPipMediaCallback',
    'cobraDispatchPipCommand', 'cobraPipPlaybackState', 'cobraUpdatePipMediaSession',
    'cobraUserPlay', 'cobraHandleAudioFocus', 'cobraClaimAudioFocus', 'cobraReleaseAudioFocus',
    'mediaItem', 'cobraStopLocalTimeshift', 'cobraStartLocalTimeshift',
    'cobraStartDirectSinglePlayer', 'cobraStartDirectPreview', 'cobraStartLocalTimeshiftPreview',
    'cobraWatchTimeshiftReady', 'cobraPrepareObserved', 'cobraApplyPendingTimelineSeek',
    'cobraCommitTimelineSeek', 'cobraUpdateTimeshiftSeek', 'cobraRecoverTimeshiftStall',
    'cobraScheduleTimeshiftStallCheck', 'cobraObserveTimeshiftRebufferBurst', 'cobraPermitAutoLiveEdge',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def source_inventory(source):
    """The complete generated Android/media source, not merely receipt owners."""
    paths = [path for folder in ['tools/android/packaging', 'media']
             for path in sorted((source / folder).rglob('*')) if path.is_file()]
    paths.append(source / INSTALL)
    require(all(not p.is_symlink() for p in paths), 'Symlinked source input')
    return {str(p.relative_to(source)): sha(p) for p in paths}


def verify_parent_inventory(source, expected):
    """Keep all original bytes except proven generated-PNG metadata variance.

    The immutable Android reconstruction regenerates PNG metadata. This was
    already observed and pixel-checked in both accepted 204 replica receipts.
    Final packaged native/assets/resources remain subject to exact byte checks.
    """
    actual = source_inventory(source)
    require(set(actual) == set(expected), 'Complete parent source inventory drift')
    pixels = json.loads((ROOT / 'parent-png-pixels.json').read_text())
    variations = []
    for name, digest in expected.items():
        if actual[name] == digest:
            continue
        require(name.lower().endswith('.png') and name in pixels,
                'Complete parent source input drift: ' + name)
        from PIL import Image
        with Image.open(source / name) as picture:
            rgba = picture.convert('RGBA')
            decoded = {'size': list(rgba.size), 'rgba_sha256': hashlib.sha256(rgba.tobytes()).hexdigest()}
        require(decoded == pixels[name], 'Parent PNG pixels/dimensions changed: ' + name)
        variations.append(name)
    return actual, variations


def permitted_file(name, before):
    return (name in RUNTIME_ALLOWLIST if before is not None else
            re.fullmatch(r'tools/android/packaging/xbmc/src/Cobra[A-Za-z0-9]+\.java\.in', name)
            is not None)


def checked_review():
    reviewed = json.loads((ROOT / 'reviewed.json').read_text())
    require(reviewed.get('status') == 'frozen', 'Feature recipe is blocked until review is frozen')
    require(reviewed.get('parent_build') == 2103204 and reviewed.get('parent_commit') == PARENT_COMMIT,
            'Wrong reviewed parent')
    require(bool(reviewed['files']) and all(permitted_file(n, r['before'])
            for n, r in reviewed['files'].items()), 'Unreviewed source owner or empty delta')
    require(sha(ROOT / 'features.patch') == reviewed['patch_sha256'], 'Frozen patch digest drift')
    require(sha(ROOT / 'parent-png-pixels.json') == reviewed['parent_png_pixels_sha256'],
            'Frozen parent PNG pixel contract drift')
    require(bool(reviewed['test_source_hashes']), 'No frozen feature regressions')
    for name, digest in reviewed['test_source_hashes'].items():
        require(re.fullmatch(r'tests/Cobra2103205[A-Za-z0-9]+\.java', name) is not None,
                'Invalid frozen test path')
        require(sha(ROOT / name) == digest, 'Frozen test drift: ' + name)
    require(reviewed['inherited_android_cases'] == 500, 'Inherited identity count drift')
    require(reviewed['parent_source_files'] == 220, 'Parent source inventory drift')
    require(reviewed['new_source_files'] == len([r for r in reviewed['files'].values()
                                                if r['before'] is None]), 'Added file count drift')
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


def validate_install(before, after, additions):
    require(after.startswith(before), 'CMake changed outside append-only Java registration')
    suffix = after[len(before):]
    registrations = re.findall(
        r'configure_file\(\$\{CMAKE_SOURCE_DIR\}/(tools/android/packaging/xbmc/src/(Cobra[A-Za-z0-9]+)\.java\.in)\s+'
        r'\$\{CMAKE_BINARY_DIR\}/tools/android/packaging/xbmc/src/\2\.java @ONLY\)', suffix)
    residual = re.sub(
        r'configure_file\(\$\{CMAKE_SOURCE_DIR\}/tools/android/packaging/xbmc/src/(Cobra[A-Za-z0-9]+)\.java\.in\s+'
        r'\$\{CMAKE_BINARY_DIR\}/tools/android/packaging/xbmc/src/\1\.java @ONLY\)', '', suffix)
    require(not residual.strip(), 'Unexpected added CMake instructions')
    require(len(registrations) == len(additions) and {r[0] for r in registrations} == set(additions),
            'New helper source/CMake registration mismatch')


def apply(source, receipt, out):
    reviewed = checked_review()
    data = json.loads(receipt.read_text())
    expected = json.loads((ROOT / 'parent-source-hashes.json').read_text())
    complete = json.loads((ROOT / 'parent-complete-source-hashes.json').read_text())
    require(data['version_code'] == 2103204, 'Wrong parent version')
    require(len(expected) == 21 and len(complete) == 220, 'Parent inventories changed')
    require({name: row['after'] for name, row in data['files'].items()} == expected, 'Wrong parent receipt')
    actual_parent, png_metadata = verify_parent_inventory(source, complete)
    for name, row in reviewed['files'].items():
        require(row['before'] == complete.get(name) and row['after'] != row['before'],
                'Wrong reviewed preimage or empty delta: ' + name)
    before = (source / ACTIVITY).read_text()
    before_install = (source / INSTALL).read_text()
    patch = ROOT / 'features.patch'
    stats = subprocess.run(['git', '-C', str(source), 'apply', '--numstat', str(patch)],
                           check=True, capture_output=True, text=True).stdout.splitlines()
    require({line.split('\t', 2)[-1] for line in stats} == set(reviewed['files']),
            'Patch inventory differs from frozen manifest')
    subprocess.run(['git', '-C', str(source), 'apply', '--check', str(patch)], check=True)
    # All repeat/input/patch checks run before creating outputs or mutating source.
    out.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(out / 'pre-change-android-source.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(complete):
            archive.write(source / name, name)
        require(len(archive.namelist()) == len(set(archive.namelist())) == 220,
                'Complete parent source backup inventory changed')
    subprocess.run(['git', '-C', str(source), 'apply', str(patch)], check=True)
    wanted = actual_parent | {name: row['after'] for name, row in reviewed['files'].items()}
    require(source_inventory(source) == wanted, 'Unexpected patched source input or file inventory')
    additions = [name for name, row in reviewed['files'].items() if row['before'] is None]
    validate_install(before_install, (source / INSTALL).read_text(), additions)
    preserved = protected_members(before, (source / ACTIVITY).read_text())
    require(preserved == reviewed['protected_runtime_members'], 'Protected member receipt drift')
    result = {
        'parent_build': 2103204, 'parent_commit': PARENT_COMMIT,
        'files': reviewed['files'], 'protected_runtime_members': preserved,
        'parent_source_files': 220, 'final_source_files': len(wanted),
        'parent_png_metadata_variations_identical_pixels': png_metadata,
        'non_png_parent_inputs_byte_identical': True,
        'complete_intermediate_tree_byte_identity_claimed': not png_metadata,
        'native_engine_recompiled': False, 'timeshift_transport_architecture_changed': False,
        'user_requested_controls': True, 'new_features': True, 'physical_device_verified': False,
    }
    (out / 'patch.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: frozen requested Java features; exact parent, complete inventory and protected owners verified')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--source', type=Path, required=True)
    args.add_argument('--receipt', type=Path, required=True)
    args.add_argument('--out', type=Path, required=True)
    parsed = args.parse_args()
    apply(parsed.source.resolve(), parsed.receipt, parsed.out)
