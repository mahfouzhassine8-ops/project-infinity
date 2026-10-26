"""One exact integrated candidate feature; baseline-reference requests stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION=('Authorized final workstreams1/7: actualAndroid17 SearchAll Enter throughoriginalAndroidkeyboard, '
    'exactresults/providerattribution, persistedhistory, BackandHome responsiveness onintegratedsigned408. '
    'Readonlyfixtureobservations; noClose/shutdown/physicalacceptance.')
EXPECTED=dict(schema=1,kind='integrated-candidate',selected_case='final-search-all-enter',
    candidate_build=40277375964,candidate_source_commit='a43ac034678acdfbd57c90f50b1c8a458531050f',
    candidate_apk_sha256='fc1d726fee8002da7cdccec6dd79a029f6536f0f1c3857791bec94c45d620e50',
    candidate_artifact='Infinity-2103408-Integrated-INTERNAL-NOT-FINAL-40277375964',
    authorization=AUTHORIZATION,request_id='integrated408-search-all-enter-01')


def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py')
