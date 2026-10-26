"""One independent, explicitly authorized shutdown request; no feature trigger."""
import json
import os
from pathlib import Path
import subprocess

from android17_request import BASELINE,BRANCH
from candidate_request import EXPECTED as CANDIDATE

ROOT=Path(__file__).parent
REQUEST='repairs/infinity-final-closure-2103407/SHUTDOWN-REQUEST.json'
WORKFLOW='.github/workflows/infinity-shutdown-verification.yml'
AUTHORIZATION='UserOct26 actualTV preservation through ONE visible Power Close/reopen on unchanged signed417. Preserve blocked40378085987 and40380264449, both BEFORE any Close; advancing clock did not resolve Stop stall, codec errors also present in passing feature and not causal proof. New TV observer issues actual native JSONRPC Player.Stop once rather than synchronous legacy Python Player.stop, retaining exact20sec stopped checks, nativeTV saved position/completion/Next selection and all16 native+Java/zeroUID/SQLite/remembered launch/readback predicates. Own-profile stage logging and failed-state/native-stack capture; no retry/reset/timeout waiver/APK/native/Cobra/chooser change, fake save claim or repeated ordinary3cycles. Root guest-call cause remains unproven on translated VM; physicalFold final gate.'
EXPECTED=dict(schema=1,kind="independent-essential-first",request_id="integrated417-real-native-TV-visible-power-durable-03-native-Stop",
    scenario="integrated-resume-power-ui",candidate_build=CANDIDATE["candidate_build"],
    candidate_source_commit=CANDIDATE["candidate_source_commit"],
    candidate_apk_sha256=CANDIDATE["candidate_apk_sha256"],authorization=AUTHORIZATION)


def validate(request,event,head,changed):
    if (event.get('ref')!=BRANCH or event.get('after')!=head or event.get('deleted') or
        event.get('repository',{}).get('full_name')!='mahfouzhassine8-ops/project-infinity'):
        raise ValueError('Wrong independent shutdown branch/event/source')
    if request!=EXPECTED or REQUEST not in changed:
        raise ValueError('One new exact independent shutdown request required')
    allowed={WORKFLOW,'.github/workflows/infinity-2103407-search-pressure-host-gate.yml',
        '.github/workflows/infinity-2103402-native-owner-build.yml',
        '.github/workflows/infinity-saved-navigation-android.yml'}
    if not all(n.startswith('repairs/infinity-final-closure-2103407/') or n in allowed for n in changed):
        raise ValueError('Unrelated source in independent shutdown request')
    return dict(CANDIDATE_BUILD=str(CANDIDATE['candidate_build']),
        CANDIDATE_ARTIFACT=CANDIDATE['candidate_artifact'],AUTHORIZED_SCOPE=AUTHORIZATION,
        SELECTED_CASE=EXPECTED['scenario'],
        CANDIDATE_REQUEST_PATH='repairs/infinity-final-closure-2103407/SHUTDOWN-CANDIDATE.json')


def main():
    if os.environ['GITHUB_EVENT_NAME']!='push':raise ValueError('Exact independent push required')
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    before=event.get('before','')
    if len(before)!=40 or before=='0'*40:raise ValueError('Existing checkpoint required')
    for ref in (BASELINE,before,CANDIDATE['candidate_source_commit']):
        subprocess.run(['git','merge-base','--is-ancestor',ref,head],check=True)
    changed=subprocess.check_output(['git','diff','--name-only',before,head],text=True).splitlines()
    values=validate(json.loads((ROOT/'SHUTDOWN-REQUEST.json').read_text()),event,head,changed)
    with Path(os.environ['GITHUB_ENV']).open('a') as stream:
        for key,value in values.items():
            if '\n' in value or '\r' in value:raise ValueError('Invalid environment value')
            stream.write(key+'='+value+'\n')
    Path('independent-shutdown-request-evidence.json').write_text(json.dumps(dict(
        EXPECTED,test_source_commit=head,feature_or_packaging_dependency=False,
        physical_Fold='NOT RUN',release_accepted=False),indent=2)+'\n')


if __name__=='__main__':main()
