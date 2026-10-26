"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 whole-app original saved-data actions on latest signed414 after actual disabled-refresh runtime correction. Preserve six successful413 Watchlist/Collection/watched toggles and original Favorites selection failure. Run original final-actions exact native menu labels/Input.Select/persisted-state/unrelated records, capture actual row labels/Favorites RPC/native committed state for the unresolved Favorites cause. Valid generated test clip and strict disposable bootstrap only. No production test writer, APK edits, Search repeat, Close or physical touch acceptance.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-actions', 'candidate_build': 40345149803, 'candidate_source_commit': 'f5dbd03fb3a5df6b2f0f209bc36768d6ebd16c71', 'candidate_apk_sha256': 'a13bd3a5fc10752fc06621e2b49d050b5fd3ba0a8a86ad9e675420335b0313d3', 'candidate_artifact': 'Infinity-2103414-Refresh-Corrective-Verification-40345149803', 'authorization': 'UserOct26 whole-app original saved-data actions on latest signed414 after actual disabled-refresh runtime correction. Preserve six successful413 Watchlist/Collection/watched toggles and original Favorites selection failure. Run original final-actions exact native menu labels/Input.Select/persisted-state/unrelated records, capture actual row labels/Favorites RPC/native committed state for the unresolved Favorites cause. Valid generated test clip and strict disposable bootstrap only. No production test writer, APK edits, Search repeat, Close or physical touch acceptance.', 'request_id': 'integrated414-real-saved-actions-and-favourites-readback-01'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
