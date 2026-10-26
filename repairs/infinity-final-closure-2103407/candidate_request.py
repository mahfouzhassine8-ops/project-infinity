"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 signed419 LOCAL-FIRST Home30/rotation20 on explicit AOSPAndroid17/API37.0/default x86_64. Existing final-participant actual native/module/source/owner/UIDsentinel installover admission replaces unrelated remoteSearch prerequisite; Search50originalstrictfixture remainsunchanged inindependentrun40402313427. Samefrozen4verifiedlocalrecords/actualdeclared180secclip/cachedart seededONLYbeforefirstlaunchin freshdisposableAPI37profile, neverexistinguserdata. ActualparticipantpreconditionmustPASS; Home-only dispatcherrefusesSearch. Then30actualgenerated8secvideoHome and20OSrotations, everyreturn genuinecanonical movie/TVcard/source/exact60of180nativeposition/33percent/watchedfalse/noautoplay/cachedsurfacebitmap within SAME20sec total proofdeadline. PID/owner/ABI/signer/source/API37/qemu/protectedbuckets/restoredOSsettings/noClose/noreset guards intact. Allpriornative/strict16KiB failures retained, noAPI/ABIoverride/native/shared/Cobra/chooser/APK changes or retrytopass. OneAOSPHome request287a hadnoGithubruncreated; thiscorrectedactualcaseattempt isnotarestartofcompletedwork.419Power3/writerPASS preserved; physicalFold/page-size acceptance and Search50stillopen, no lock.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-participant', 'candidate_build': 40396544415, 'candidate_source_commit': 'a24db78554da7bc40a2a0b658ba441793f1c1605', 'candidate_apk_sha256': '0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a', 'candidate_artifact': 'Infinity-2103419-Home-Playlist-Corrective-Verification-40396544415', 'authorization': 'UserOct26 signed419 LOCAL-FIRST Home30/rotation20 on explicit AOSPAndroid17/API37.0/default x86_64. Existing final-participant actual native/module/source/owner/UIDsentinel installover admission replaces unrelated remoteSearch prerequisite; Search50originalstrictfixture remainsunchanged inindependentrun40402313427. Samefrozen4verifiedlocalrecords/actualdeclared180secclip/cachedart seededONLYbeforefirstlaunchin freshdisposableAPI37profile, neverexistinguserdata. ActualparticipantpreconditionmustPASS; Home-only dispatcherrefusesSearch. Then30actualgenerated8secvideoHome and20OSrotations, everyreturn genuinecanonical movie/TVcard/source/exact60of180nativeposition/33percent/watchedfalse/noautoplay/cachedsurfacebitmap within SAME20sec total proofdeadline. PID/owner/ABI/signer/source/API37/qemu/protectedbuckets/restoredOSsettings/noClose/noreset guards intact. Allpriornative/strict16KiB failures retained, noAPI/ABIoverride/native/shared/Cobra/chooser/APK changes or retrytopass. OneAOSPHome request287a hadnoGithubruncreated; thiscorrectedactualcaseattempt isnotarestartofcompletedwork.419Power3/writerPASS preserved; physicalFold/page-size acceptance and Search50stillopen, no lock.', 'request_id': 'integrated419-local-only-home30-rotation20-AOSP37.0-01', 'post_feature': {'search': 0, 'playback_home': 30, 'rotation': 20}, 'measure_cached_poster': True, 'expected_skin_version': '1.0.5.246', 'emulator_api': '37.0', 'emulator_target': 'default'}

ENVIRONMENTS={('37.1','google_apis_ps16k'):'repairs/infinity-final-closure-2103407/api37_environment_gate.py',
              ('37.0','default'):'repairs/infinity-final-closure-2103407/api37_aosp_gate.py'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    if (EXPECTED['emulator_api'],EXPECTED['emulator_target']) not in ENVIRONMENTS:
        raise ValueError('Unreviewed emulator environment refused')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '',
        INFINITY_EMULATOR_API=EXPECTED['emulator_api'],INFINITY_EMULATOR_TARGET=EXPECTED['emulator_target'],
        INFINITY_API37_GATE=ENVIRONMENTS[(EXPECTED['emulator_api'],EXPECTED['emulator_target'])])
