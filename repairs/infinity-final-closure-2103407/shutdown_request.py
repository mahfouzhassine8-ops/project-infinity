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
AUTHORIZATION='UserOct26 current signed418 independent native writer/persistence controls:16real native multi-image controls with unique jobs/tokens/generations, exact factory terminals and retirement receipts including separately identified unchanged-unstarted jobs. One actual protected positive Close/reopen with all16/native/twoJava/engine+coordinator/zeroUID/SQLite/data/preference proofs, then actual opaque child marker writer must veto Close with no save/auth/death claim and unchanged protected state. Preserve411ordinary3PASS40317069331/417Power3PASS40373328781/417writerPASS40376891135; current418realTV3run40386278200 and Search50/Home30/rotation20run40386278214 stay independent and untouched. No runtimeAPK/native/chooser/Cobra changes, synthetic success, count waiver, reset or physical acceptance.'
EXPECTED=dict(schema=1,kind="independent-essential-first",request_id="integrated418-native-image-and-unsafe-separate-01",
    scenario="integrated-native-image-and-unsafe",candidate_build=CANDIDATE["candidate_build"],
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
