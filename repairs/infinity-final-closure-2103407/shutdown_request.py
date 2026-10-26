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
AUTHORIZATION='UserOct26 latest signed419 integrated THREE actual visible Power Close/reopen cycles: exact unfinished nativeTV position/source readback first, actual completed watched100/removedContinue/verifiedS2E1 selection second, completed warm third. Preserve successful ordinary41140317069331 and actual41840387720854; integration-specific reason is new14Home onload246native absent-provider path, while all75CC48/native/DEX/Power/chooser/Cobra bytes exact418. Verify16owners, protectednative/Python/twoJava writes, authentic engine termination/coordinator completion and externally owned remainingprocesses, AndroidHome/RecentApps separate, rememberedInfinityprefs, protectedJSON/7SQLite readback and noautoplay. Original20start/45completion/35Close gates retained, no retries/reset/fakes/install-userdata or forcedchooser. Actualemulator not Samsung physical. Independent Search40397437746 and Home/rotation requests untouched, no packaging/feature dependency, no finalacceptance/no lock.'
EXPECTED=dict(schema=1,kind="independent-essential-first",request_id="integrated419-real-TV-three-visible-Power-cycles-01",
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
