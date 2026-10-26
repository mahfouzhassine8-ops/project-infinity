"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 signed419 local-only Home30/rotation20 on exact Android17/API37.1 google_apis_ps16k emulator with EXPLICIT documented OS 16KiB backcompat for original4KiB libraries. Same original-key APK/source/ABI, no native/manifest/Cobra/chooser change. Strict16KiB rejection and all native-start failures retained. Native ARM Mac capability failed HV_UNSUPPORTED before app; AOSP37.0 x86 lacks ARM bridge. OS-only properties recorded/read back before any app exists; not strict16KiB qualification or physical Fold mode evidence. Original final-participant native/owner/source/UID admission, exact local4 records/source/art/60of180/watched/noautoplay proof,30 actual videoHome and20 rotations with same20sec total deadline; no remoteSearch prerequisite, reset, Close or test waiver. Search50 independent still open. Existing419 Power3 and writer PASS preserved. Physical Fold final gate and all7 workstreams remain open; no final lock.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-participant', 'candidate_build': 40396544415, 'candidate_source_commit': 'a24db78554da7bc40a2a0b658ba441793f1c1605', 'candidate_apk_sha256': '0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a', 'candidate_artifact': 'Infinity-2103419-Home-Playlist-Corrective-Verification-40396544415', 'authorization': 'UserOct26 signed419 local-only Home30/rotation20 on exact Android17/API37.1 google_apis_ps16k emulator with EXPLICIT documented OS 16KiB backcompat for original4KiB libraries. Same original-key APK/source/ABI, no native/manifest/Cobra/chooser change. Strict16KiB rejection and all native-start failures retained. Native ARM Mac capability failed HV_UNSUPPORTED before app; AOSP37.0 x86 lacks ARM bridge. OS-only properties recorded/read back before any app exists; not strict16KiB qualification or physical Fold mode evidence. Original final-participant native/owner/source/UID admission, exact local4 records/source/art/60of180/watched/noautoplay proof,30 actual videoHome and20 rotations with same20sec total deadline; no remoteSearch prerequisite, reset, Close or test waiver. Search50 independent still open. Existing419 Power3 and writer PASS preserved. Physical Fold final gate and all7 workstreams remain open; no final lock.', 'request_id': 'integrated419-local-home30-rotation20-explicit-OS16K-backcompat-01', 'post_feature': {'search': 0, 'playback_home': 30, 'rotation': 20}, 'measure_cached_poster': True, 'expected_skin_version': '1.0.5.246', 'emulator_api': '37.1', 'emulator_target': 'google_apis_ps16k', 'os_page_compat': True}

ENVIRONMENTS={('37.1','google_apis_ps16k'):'repairs/infinity-final-closure-2103407/api37_environment_gate.py',
              ('37.0','default'):'repairs/infinity-final-closure-2103407/api37_aosp_gate.py'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    if (EXPECTED['emulator_api'],EXPECTED['emulator_target']) not in ENVIRONMENTS:
        raise ValueError('Unreviewed emulator environment refused')
    if EXPECTED.get('os_page_compat') is True:
        from api37_page_compat_setup import validate as validate_os_mode
        validate_os_mode(EXPECTED)
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '',
        INFINITY_EMULATOR_API=EXPECTED['emulator_api'],INFINITY_EMULATOR_TARGET=EXPECTED['emulator_target'],
        INFINITY_PAGE_COMPAT='true' if EXPECTED.get('os_page_compat') is True else '',
        INFINITY_API37_GATE=ENVIRONMENTS[(EXPECTED['emulator_api'],EXPECTED['emulator_target'])])
