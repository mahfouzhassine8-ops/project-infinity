"""One exact integrated candidate feature; independent lanes stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION='UserOct26 final correction after Home-entry413: verify existing final-continue actual local movie and TV Home cards with exact identity/source/season/episode/resume time, no autoplay, original removal-preservation, generated-clip progress and deliberate rewind. Use original unchanged assertions and read-only observer; no writer grant, Search repetitions, Close or physical Fold acceptance in this lane.'
EXPECTED={'schema': 1, 'kind': 'integrated-candidate', 'selected_case': 'final-continue', 'candidate_build': 40336380247, 'candidate_source_commit': '282a12a5e538a3ba05d5544d94a318b1c5de5ad4', 'candidate_apk_sha256': 'b3af984c5f035f6c0e51f70f71726b317ddbb503764eb5306505b583c0643ec4', 'candidate_artifact': 'Infinity-2103413-Home-Corrective-Verification-40336380247', 'authorization': 'UserOct26 final correction after Home-entry413: verify existing final-continue actual local movie and TV Home cards with exact identity/source/season/episode/resume time, no autoplay, original removal-preservation, generated-clip progress and deliberate rewind. Use original unchanged assertions and read-only observer; no writer grant, Search repetitions, Close or physical Fold acceptance in this lane.', 'request_id': 'integrated413-local-continue-movie-tv-and-position-01'}


def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20' if EXPECTED.get('post_feature') else '')
