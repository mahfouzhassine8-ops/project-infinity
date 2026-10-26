"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 original saved actions on same genuine signed415. Actual415run40360322176 passed6state toggles, displayed AddFavorites and native later readback confirms exact favorite added; original immediate nullable query raced actual async popup action and TypeErrored before remove. Correct only test observation: native null->empty requires exactzero limits; wait exact target presence/absence within REMAINING original90sec popup deadline; each original Input.Select once, all original ui.require predicates unchanged. Run original Watchlist/Collection/watched/Favorites add/remove and unrelated data checks. No runtime change/rebuild, action retry, deadline increase, reset, Search, Close or physical acceptance.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-actions', 'candidate_build': 40358644857, 'candidate_source_commit': 'e92df08f23f9a66d9e004e48954a9e5d5dfc1ef7', 'candidate_apk_sha256': '75e3982300aed71fe791f8d5ccf9542ac0c198f012aea9f124021f3a766eb4ac', 'candidate_artifact': 'Infinity-2103415-Playback-Favourites-Corrective-Verification-40358644857', 'authorization': 'UserOct26 original saved actions on same genuine signed415. Actual415run40360322176 passed6state toggles, displayed AddFavorites and native later readback confirms exact favorite added; original immediate nullable query raced actual async popup action and TypeErrored before remove. Correct only test observation: native null->empty requires exactzero limits; wait exact target presence/absence within REMAINING original90sec popup deadline; each original Input.Select once, all original ui.require predicates unchanged. Run original Watchlist/Collection/watched/Favorites add/remove and unrelated data checks. No runtime change/rebuild, action retry, deadline increase, reset, Search, Close or physical acceptance.', 'request_id': 'integrated415-real-actions-native-async-readback-02'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
