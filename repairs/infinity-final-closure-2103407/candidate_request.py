"""One exact integrated candidate feature; baseline-reference requests stay separate."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
AUTHORIZATION=('UserOct26 explicitlyrequires API37 repeated50Search,30nativegeneratedclipplayback-to-Home and20OSrotation scenarios, '
    'afteroriginalSearchAll Enter/history/results/BackHome gate. Includeactualproviderselection, historyreuse, duplicatesubmission andcancel, '
    'rawmemory/frame observations; noClose/reset/physicalFoldacceptance.')
EXPECTED=dict(schema=1,kind='integrated-candidate',selected_case='final-search-all-enter',
    candidate_build=40295309934,candidate_source_commit='b65ae4981f10bd6badf118ce95f360d28499c2d7',
    candidate_apk_sha256='4d68e3bf21ee109a9196267e9ed2b21ea8430fff8dede331af3c199e9921bf21',
    candidate_artifact='Infinity-2103409-Integrated-INTERNAL-NOT-FINAL-40295309934',
    authorization=AUTHORIZATION,request_id='integrated409-search50-playback30-rotation20-01',
    post_feature={'search':50,'playback_home':30,'rotation':20})


def validate(request):
    if request!=EXPECTED:raise ValueError('Exact scoped integrated candidate request required')
    return dict(CANDIDATE_BUILD=str(EXPECTED['candidate_build']),SELECTED_CASE=EXPECTED['selected_case'],
        CANDIDATE_ARTIFACT=EXPECTED['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/ANDROID17-REQUEST.json',
        FEATURE_PROBE='repairs/infinity-final-closure-2103407/android17_candidate_probe.py',
        FEATURE_STRESS='signed409-50-30-20')
