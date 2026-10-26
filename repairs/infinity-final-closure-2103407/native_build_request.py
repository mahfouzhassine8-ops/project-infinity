"""One narrow explicitly authorized full-native request on the final work branch."""
import json
import os
from pathlib import Path
import subprocess

BRANCH='refs/heads/work/infinity-final-corrective-from-2103407-20261025'
BASELINE='0e8739d2d0e1be0ab8f127519b526556426fb160'
REQUEST='repairs/infinity-final-closure-2103407/NATIVE-BUILD-REQUEST.json'
AUTHORIZATION=('Existing final takeover: compile complete matching engine for native module/selection/checkpoint '
               'corrections and subsequent internal Android17 integration. No final APK acceptance, user installation '
               'or shutdown verification is implied.')
EXPECTED=dict(schema=1,request_id='final407-native-modules-01',kind='full-matching-arm64-engine',
              protected_commit=BASELINE,source_count=9411,existing_source_changes=7,new_source_files=4,
              targeted_source_checks='test_native_integration.py6 + test_identity_audit.py2',authorization=AUTHORIZATION)


def validate(request,event,head,changed):
    if (event.get('ref')!=BRANCH or event.get('deleted') or event.get('after')!=head or
        event.get('repository',{}).get('full_name')!='mahfouzhassine8-ops/project-infinity'):
        raise ValueError('Wrong native request branch/event/source')
    if request!=EXPECTED or REQUEST not in changed:raise ValueError('A new exact native compile request is required')
    allowed={'.github/workflows/infinity-2103407-search-pressure-host-gate.yml',
             '.github/workflows/infinity-saved-navigation-android.yml',
             '.github/workflows/infinity-2103402-native-owner-build.yml'}
    if not all(n.startswith('repairs/infinity-final-closure-2103407/') or n in allowed for n in changed):
        raise ValueError('Unrelated source in native request')
    return True


def main():
    if os.environ['GITHUB_EVENT_NAME']!='push':raise ValueError('Exact narrow branch push required')
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    before=event.get('before','')
    if len(before)!=40 or before=='0'*40:raise ValueError('Existing checkpoint required')
    for ref in (BASELINE,before):subprocess.run(['git','merge-base','--is-ancestor',ref,head],check=True)
    changed=subprocess.check_output(['git','diff','--name-only',before,head],text=True).splitlines()
    validate(json.loads(Path(REQUEST).read_text()),event,head,changed)
    scope=json.loads(Path('repairs/infinity-final-closure-2103407/SCOPE.json').read_text())
    if scope['baseline']['commit']!=BASELINE or len(scope['workstreams'])!=7:raise ValueError('Final scope changed')
    Path('NATIVE-REQUEST-EVIDENCE.json').write_text(json.dumps(dict(EXPECTED,source_commit=head,
        Android17='NOT RUN',physical_Fold='NOT RUN',final_release_accepted=False),indent=2)+'\n')


if __name__=='__main__':main()
