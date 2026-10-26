"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 SAME signed419 independent Home30/rotation20 on explicitlyrecorded published Android17/API37.0 AOSPdefault x86_64 image. PreserveactualGoogle37.0 AT_RANDOMnativeconstructorfailures40397437746/40397522955 andstrict16KiB37.1loaderfailures40399697939/40399771565;0completedstressinthoseattempts. ActualELFaudit46of47librariesfailstrict16KiB, noABIcompatibilityoverride/sharednative/Cobra/chooser/APK change or claimthisimagefixesrootcause. Originalreal-provider Enter/Matrix603/History/Home setup, then0additionalSearch/30generatednativevideoHome/20actualOSrotation with exactlocalmovie/TVcard/source/native60of180position/watchedfalse/noautoplay/cachedbitmap on everyreturn. Alloriginal20seccardproof/45keyboard/90results/native20lease andliveprocess/source/signer/API37/qemu/freshinstallover/UIDsentinel/readback/protectedrecords guards intact. Recordactualbuild/pagesize/ABI/bridge availability; unavailableARMtranslation/renderingorstartup failurestaysFAIL, nofallback/restart/retrytopass. Search50independent;419Power3/writerPASS preserved. PhysicalFold/page-size acceptance unverified;nofinallock.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-search-all-enter', 'candidate_build': 40396544415, 'candidate_source_commit': 'a24db78554da7bc40a2a0b658ba441793f1c1605', 'candidate_apk_sha256': '0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a', 'candidate_artifact': 'Infinity-2103419-Home-Playlist-Corrective-Verification-40396544415', 'authorization': 'UserOct26 SAME signed419 independent Home30/rotation20 on explicitlyrecorded published Android17/API37.0 AOSPdefault x86_64 image. PreserveactualGoogle37.0 AT_RANDOMnativeconstructorfailures40397437746/40397522955 andstrict16KiB37.1loaderfailures40399697939/40399771565;0completedstressinthoseattempts. ActualELFaudit46of47librariesfailstrict16KiB, noABIcompatibilityoverride/sharednative/Cobra/chooser/APK change or claimthisimagefixesrootcause. Originalreal-provider Enter/Matrix603/History/Home setup, then0additionalSearch/30generatednativevideoHome/20actualOSrotation with exactlocalmovie/TVcard/source/native60of180position/watchedfalse/noautoplay/cachedbitmap on everyreturn. Alloriginal20seccardproof/45keyboard/90results/native20lease andliveprocess/source/signer/API37/qemu/freshinstallover/UIDsentinel/readback/protectedrecords guards intact. Recordactualbuild/pagesize/ABI/bridge availability; unavailableARMtranslation/renderingorstartup failurestaysFAIL, nofallback/restart/retrytopass. Search50independent;419Power3/writerPASS preserved. PhysicalFold/page-size acceptance unverified;nofinallock.', 'request_id': 'integrated419-home30-rotation20-AOSP37.0-environment-01', 'post_feature': {'search': 0, 'playback_home': 30, 'rotation': 20}, 'measure_cached_poster': True, 'expected_skin_version': '1.0.5.246', 'emulator_api': '37.0', 'emulator_target': 'default'}

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
