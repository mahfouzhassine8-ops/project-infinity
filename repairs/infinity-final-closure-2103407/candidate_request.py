"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 original saved-data action integration on same signed414. Prior414action40348051988 failed BEFORE APK install because root retry used unsupported wrapper keyword; corrected against actual retained transport signature with90/30/90 host subprocess budgets. Preserve failure. Run original native labels/Input.Select/Watchlist/Collection/watched/Favorites/unrelated data predicates; capture actual row labels/Favorites RPC/native state. No APK change, production test writer, app action retry, Search/Close or physical gesture acceptance.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-actions', 'candidate_build': 40345149803, 'candidate_source_commit': 'f5dbd03fb3a5df6b2f0f209bc36768d6ebd16c71', 'candidate_apk_sha256': 'a13bd3a5fc10752fc06621e2b49d050b5fd3ba0a8a86ad9e675420335b0313d3', 'candidate_artifact': 'Infinity-2103414-Refresh-Corrective-Verification-40345149803', 'authorization': 'UserOct26 original saved-data action integration on same signed414. Prior414action40348051988 failed BEFORE APK install because root retry used unsupported wrapper keyword; corrected against actual retained transport signature with90/30/90 host subprocess budgets. Preserve failure. Run original native labels/Input.Select/Watchlist/Collection/watched/Favorites/unrelated data predicates; capture actual row labels/Favorites RPC/native state. No APK change, production test writer, app action retry, Search/Close or physical gesture acceptance.', 'request_id': 'integrated414-real-actions-native-transport-signature-02'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
