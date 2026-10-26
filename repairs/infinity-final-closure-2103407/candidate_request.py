"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 original Continue Playing/Watching on same genuine signed417. Preserve40373328890 partial: all4original Continue cases, actualTVstop/restoration and native completion/watched succeeded; new source-memory assertion wrongly rejected legitimate actual-playback source remembrance. Correct only that test: foreign sources unchanged, no unexpected keys, played exact identity may record ONLY confirmed native episode file/failures0/positive timestamp. Run original strict predicates plus native TV completion/cross-season Next/local source selection, original45/15/20sec bounds. No APK change, runtime write grant, action retry, reset, Search, Close or physical acceptance in feature lane.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-continue', 'candidate_build': 40371026995, 'candidate_source_commit': 'd10fffd80182c796955534ffdecc5ccc288da99b', 'candidate_apk_sha256': '4428332453714adc1aa652ee5db76ff2e79f705171dab8e020d7915631e00d83', 'candidate_artifact': 'Infinity-2103417-Continue-Watching-Corrective-Verification-40371026995', 'authorization': 'UserOct26 original Continue Playing/Watching on same genuine signed417. Preserve40373328890 partial: all4original Continue cases, actualTVstop/restoration and native completion/watched succeeded; new source-memory assertion wrongly rejected legitimate actual-playback source remembrance. Correct only that test: foreign sources unchanged, no unexpected keys, played exact identity may record ONLY confirmed native episode file/failures0/positive timestamp. Run original strict predicates plus native TV completion/cross-season Next/local source selection, original45/15/20sec bounds. No APK change, runtime write grant, action retry, reset, Search, Close or physical acceptance in feature lane.', 'request_id': 'integrated417-real-continue-native-tv-source-memory-02', 'verify_tv_completion': True}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
