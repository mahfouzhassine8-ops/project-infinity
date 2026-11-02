"""Preview presentation/call-only source and owner proof against actual signed448."""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
OLD=R/'repairs/infinity-2103445-standalone-external-player/runtime'
BASE='ecfbfdd00c443bad530d3ed429eb69755f46601f'
spec=importlib.util.spec_from_file_location('prior_scope',R/'repairs/infinity-preview-2103447-resume/scope_guard.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def original(path):return subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(R))]).decode()
def verify(build):
    for n in ('ExternalVideoRoute.java','InfinityExternalState.java','InfinityExternalEngine.java','InfinityExternalResume.java'):
        p=OLD/n;assert p.read_text()==original(p),'Protected source '+n
    p=OLD/'InfinityExternalPlayerActivity.java';a=original(p);b=p.read_text()
    for method in ('existingExperiencePresent','accept','onNewIntent','onPause','onStop','onBackPressed','close','dismissResume','chooseResume','event','size','subtitle','fitVideo','abandonFocus','time'):
        assert prior.method(a,method)==prior.method(b,method),'Protected Preview method '+method
    for method in ('tracks','showResume'):
        assert prior.method(a,method).replace('new AlertDialog.Builder(this)','dialog()')==prior.method(b,method),'Only theme wrapper authorized: '+method
    proof=json.loads((build/'OWNER-BUILD.json').read_text())
    assert proof['baseline']==BASE
    for name,pin in proof['sources'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==pin,name
    allowed=('Lcom/projectinfinity/kodi/InfinityExternalPlayerActivity','Lcom/projectinfinity/kodi/InfinityPreviewChrome')
    assert not proof['removed'],'No accepted class removal'
    for n in proof['changed']+proof['added']:
        assert any(n==root+';' or n.startswith(root+'$') for root in allowed),n
    return dict(status='PASS_PREVIEW_CHROME_CALL_ONLY',baseline=BASE,unchanged_classes=proof['unchanged'],
        decoder_resume_store_route_request_state='SOURCE_AND_CLASS_EXACT',
        original_fit_and_lifecycle_and_resume_actions='SOURCE_EXACT',
        protected_Splash_Cobra_Kodi_shared_native_shutdown='UNCHANGED',
        new_preferences='Preview-only appearance; existing data untouched',physical_Fold='PENDING')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=verify(a.build);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
