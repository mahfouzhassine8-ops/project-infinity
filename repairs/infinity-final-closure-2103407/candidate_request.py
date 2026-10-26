"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 essential Continue Playing correction on genuine original-key signed415: run original final-continue movie/TV native60of180 exact IDs/source/season/episode/noautoplay/card timing, remove without deletion, real24fps playback45sec alias update, seek/rewind15sec predicates and protected data preservation. Capture actual committed state/native labels/Favorites. Native typed playback fallback and empty Favorites are production fixes, not a test waiver. No app reset, Search, Close or physical acceptance in this feature lane.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-continue', 'candidate_build': 40358644857, 'candidate_source_commit': 'e92df08f23f9a66d9e004e48954a9e5d5dfc1ef7', 'candidate_apk_sha256': '75e3982300aed71fe791f8d5ccf9542ac0c198f012aea9f124021f3a766eb4ac', 'candidate_artifact': 'Infinity-2103415-Playback-Favourites-Corrective-Verification-40358644857', 'authorization': 'UserOct26 essential Continue Playing correction on genuine original-key signed415: run original final-continue movie/TV native60of180 exact IDs/source/season/episode/noautoplay/card timing, remove without deletion, real24fps playback45sec alias update, seek/rewind15sec predicates and protected data preservation. Capture actual committed state/native labels/Favorites. Native typed playback fallback and empty Favorites are production fixes, not a test waiver. No app reset, Search, Close or physical acceptance in this feature lane.', 'request_id': 'integrated415-real-continue-native-typed-progress-01'}

def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
