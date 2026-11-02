"""Only selected Preview layout/control methods may differ from exact signed449."""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];OLD=R/'repairs/infinity-2103445-standalone-external-player/runtime';BASE='dd7bd790e7adc3cfadccb9743c9b38b49e8e7b11'
spec=importlib.util.spec_from_file_location('method_parser',R/'repairs/infinity-preview-2103447-resume/scope_guard.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def original(p):return subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(R))]).decode()
def verify(build):
 for n in ('ExternalVideoRoute.java','InfinityExternalState.java','InfinityExternalEngine.java','InfinityExternalResume.java'):
  p=OLD/n;assert original(p)==p.read_text(),'Protected source '+n
 p=OLD/'InfinityExternalPlayerActivity.java';a=original(p);b=p.read_text()
 for name in ('buildUi','layoutChrome','size','updateButtons'):
  a=a.replace(prior.method(a,name),'');b=b.replace(prior.method(b,name),'')
 assert a==b,'Unrelated Activity method or field changed'
 p=OLD/'InfinityPreviewChrome.java';marker='    public static final class Control extends Button {'
 assert original(p).split(marker)[0]==p.read_text().split(marker)[0],'Unrelated Chrome drawable changed'
 proof=json.loads((build/'OWNER-BUILD.json').read_text());assert proof['baseline']==BASE
 for n,pin in proof['sources'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==pin,n
 def allowed(n):return n=='Lcom/projectinfinity/kodi/InfinityExternalPlayerActivity;' or n.startswith('Lcom/projectinfinity/kodi/InfinityExternalPlayerActivity$') or n=='Lcom/projectinfinity/kodi/InfinityPreviewChrome$Control;'
 assert all(allowed(n) for n in proof['changed']+proof['added']+proof['removed'])
 return dict(status='PASS_ONLY_PREVIEW_LAYOUT_CONTROLS',baseline=BASE,unchanged_classes=proof['unchanged'],engine_resume_route_call_policy_lifecycle='SOURCE_AND_CLASS_EXACT',shutdown='UNCHANGED_NOT_TESTED',physical_Fold='PENDING')
