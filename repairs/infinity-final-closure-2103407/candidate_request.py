"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 SAME signed419 independent Search50 on explicit published Android17/API37.0 AOSPdefault x86_64 image. PreserveGoogle37.0pre-Python AT_RANDOMcrashes and37.1strict16KiBloader failures, all0stresscounts; actual46of47bundledELFsdo notmeetstrict16KiB. No native/shared/Cobra/chooser/APK edit, ABIoverride, deadlineextension, apprestart/retrytopass orfalse rootcausefix. Sameoriginalrealnative Enter/Matrix603/provider/results/History/Home then50actualadditionalSearchinteractions, original45keyboard/90terminal/native20lease. Exactproviderattribution/terminal/contentfailures/History/cancel/doubleEnter/oldresult/process safety guards intact; realproviderfailuresstayfalsecontent. Actualcachedcard/art/PSS/RSS/threads/FD/nativeframes andOSbuild/ABI/pagesize/bridge availability observed, missing results remainunavailable. Home30/rotation20 independentNOTSELECTED here, norotationsetting/Close test. OriginalAPI37/qemu/freshinstallover/UIDsentinel/signer/source/protectedstate guards unchanged; unsupportedARM/rendering/startupfailurestaysFAIL withoutfallback. Preserve419Power3/writerPASS and411Close3. PhysicalFold/page-size finalgate, no lock.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-search-all-enter', 'candidate_build': 40396544415, 'candidate_source_commit': 'a24db78554da7bc40a2a0b658ba441793f1c1605', 'candidate_apk_sha256': '0b202e3af93ce25be8cd5ecb2853043411ba5fbbf88dac0df94ef4b2ce55605a', 'candidate_artifact': 'Infinity-2103419-Home-Playlist-Corrective-Verification-40396544415', 'authorization': 'UserOct26 SAME signed419 independent Search50 on explicit published Android17/API37.0 AOSPdefault x86_64 image. PreserveGoogle37.0pre-Python AT_RANDOMcrashes and37.1strict16KiBloader failures, all0stresscounts; actual46of47bundledELFsdo notmeetstrict16KiB. No native/shared/Cobra/chooser/APK edit, ABIoverride, deadlineextension, apprestart/retrytopass orfalse rootcausefix. Sameoriginalrealnative Enter/Matrix603/provider/results/History/Home then50actualadditionalSearchinteractions, original45keyboard/90terminal/native20lease. Exactproviderattribution/terminal/contentfailures/History/cancel/doubleEnter/oldresult/process safety guards intact; realproviderfailuresstayfalsecontent. Actualcachedcard/art/PSS/RSS/threads/FD/nativeframes andOSbuild/ABI/pagesize/bridge availability observed, missing results remainunavailable. Home30/rotation20 independentNOTSELECTED here, norotationsetting/Close test. OriginalAPI37/qemu/freshinstallover/UIDsentinel/signer/source/protectedstate guards unchanged; unsupportedARM/rendering/startupfailurestaysFAIL withoutfallback. Preserve419Power3/writerPASS and411Close3. PhysicalFold/page-size finalgate, no lock.', 'request_id': 'integrated419-search50-AOSP37.0-environment-01', 'post_feature': {'search': 50, 'playback_home': 0, 'rotation': 0}, 'measure_cached_poster': True, 'expected_skin_version': '1.0.5.246', 'emulator_api': '37.0', 'emulator_target': 'default'}

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
