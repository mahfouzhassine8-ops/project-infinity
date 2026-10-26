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
AUTHORIZATION='UserOct26 actual native TV preservation across ONE visible Power Close/reopen on unchanged signed417. Preserve40378085987 failure before any Close: first typed clip produced MediaCodec/sync errors after immediate harness seek and observer never returned; runtime cause not proven. Require native advancing AV clock/speed1 within SAME20sec start predicate before test seek, retaining actual progress/completion/Next identities and all16 native+Java/engine+coordinator/zeroUID/readback/SQLite/launch proofs. No action retry/reset/APK/chooser/Cobra change, timeout waiver or repeated three-cycle suite. Collect actual QA profile/native stack on failure. Ordinary411PASS40317069331 and ordinary417Power3PASS40373328781 remain preserved. Physical Fold NOT RUN.'
EXPECTED=dict(schema=1,kind="independent-essential-first",request_id="integrated417-real-native-TV-visible-power-durable-02-AV-clock",
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
