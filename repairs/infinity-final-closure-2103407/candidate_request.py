"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 original saved action integration on genuine latest signed417 CC47/Skin245 after Continue Watching and Home scheduler corrections. Run original Watchlist add/remove, Collection add/remove, watched/unwatched, native Favorites add/remove, exact labels/Input.Select and unrelated-data assertions. Use actual nullable native response and exact presence/absence within REMAINING original90sec popup deadline; no input retries, false receipt or timeout waiver. Preserve415actions PASS40362471408. No firstparty test import/writer grant, reset, Search, Close or physical gesture acceptance in this feature lane.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-actions', 'candidate_build': 40371026995, 'candidate_source_commit': 'd10fffd80182c796955534ffdecc5ccc288da99b', 'candidate_apk_sha256': '4428332453714adc1aa652ee5db76ff2e79f705171dab8e020d7915631e00d83', 'candidate_artifact': 'Infinity-2103417-Continue-Watching-Corrective-Verification-40371026995', 'authorization': 'UserOct26 original saved action integration on genuine latest signed417 CC47/Skin245 after Continue Watching and Home scheduler corrections. Run original Watchlist add/remove, Collection add/remove, watched/unwatched, native Favorites add/remove, exact labels/Input.Select and unrelated-data assertions. Use actual nullable native response and exact presence/absence within REMAINING original90sec popup deadline; no input retries, false receipt or timeout waiver. Preserve415actions PASS40362471408. No firstparty test import/writer grant, reset, Search, Close or physical gesture acceptance in this feature lane.', 'request_id': 'integrated417-real-protected-saved-actions-01'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
