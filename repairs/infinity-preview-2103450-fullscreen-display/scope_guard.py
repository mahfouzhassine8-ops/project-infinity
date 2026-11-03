"""Protect signed450 playback/lifecycle/route code while allowing selected UI only."""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];OLD=R/'repairs/infinity-2103445-standalone-external-player/runtime';BASE='f372d25e5e3b23634895ef2e9c9ed60e5246d123'
spec=importlib.util.spec_from_file_location('method_parser',R/'repairs/infinity-preview-2103447-resume/scope_guard.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def original(p):return subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(R))]).decode()
def verify(build):
 for n in ('ExternalVideoRoute.java','InfinityExternalState.java','InfinityExternalEngine.java','InfinityExternalResume.java'):
  p=OLD/n;assert original(p)==p.read_text(),'Protected source '+n
 p=OLD/'InfinityExternalPlayerActivity.java';a=original(p);b=p.read_text()
 protected=('existingExperiencePresent','accept','onNewIntent','load','onStart','onPause','onStop','close','isCallMode','effectiveMuted','syncCallMode','obtainFocus','abandonFocus','startPlayback','event','position','size','subtitle','tracks','dismissResume','chooseResume','showResume','time','isLight','showStatus','tintTree','resizeChromeControls','place','showTimes')
 for name in protected:assert prior.method(a,name)==prior.method(b,name),'Protected Activity method '+name
 assert prior.method(b,'onCreate').replace('buildUi(); restoreDisplayState(saved); accept','buildUi(); accept')==prior.method(a,'onCreate')
 assert prior.method(b,'onDestroy').replace('        if(displayDialog!=null)displayDialog.dismiss();\n','')==prior.method(a,'onDestroy')
 p=OLD/'InfinityPreviewChrome.java';marker='    public static final class Control extends Button {'
 assert original(p).split(marker)[0]==p.read_text().split(marker)[0],'Unrelated Chrome drawable changed'
 proof=json.loads((build/'OWNER-BUILD.json').read_text());assert proof['baseline']==BASE
 for name,pin in proof['sources'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==pin,name
 def allowed(n):return n=='Lcom/projectinfinity/kodi/InfinityExternalPlayerActivity;' or n.startswith('Lcom/projectinfinity/kodi/InfinityExternalPlayerActivity$') or n=='Lcom/projectinfinity/kodi/InfinityPreviewChrome$Control;' or n.startswith('Lcom/projectinfinity/kodi/InfinityPreviewDisplayDialog$') or n=='Lcom/projectinfinity/kodi/InfinityPreviewDisplayDialog;'
 assert all(allowed(n) for n in proof['changed']+proof['added']+proof['removed'])
 return dict(status='PASS_SELECTED_PREVIEW_FULLSCREEN_DISPLAY_SCOPE',baseline=BASE,unchanged_classes=proof['unchanged'],engine_resume_routing_call_focus_and_close='SOURCE_AND_CLASS_EXACT',Cobra_shared_native_Kodi_shutdown='UNCHANGED',approved_visual_reference='NOT_ACCESSIBLE_PENDING',physical_Fold='NOT_TESTED')
