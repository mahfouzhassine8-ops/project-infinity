#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,json,re,hashlib
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('patch164',ROOT/'apply.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
ALLOWED={'cobraBeginMiniBackgroundPlayback','cobraEndMiniBackgroundPlayback','cobraOpenSheet','configureCobraPip','enterCobraPictureInPicture','onBackPressed','onConfigurationChanged','onCreate','onDestroy','onPictureInPictureModeChanged','onResume','onStop','onUserLeaveHint','pauseCobraForBackground','playChannel','playVodUrl','promoteCobraPreviewToFullscreen','selectGuidePreview','startCobraPlayer','toggleCobraPreviewPlayPause'}
def audit(source,out):
 before=(source/p.SRC/'InfinityLiveActivity.java.in').read_text();after=p.activity(before)
 assert p.sha(before)==p.PRE['InfinityLiveActivity.java.in'],'Wrong exact accepted Activity'
 pattern=r'^  (?:@Override(?:[ \t]*\n  |[ \t]+))?(?:private|public|protected) [^\n;=(){}]*\b(\w+)\s*\('
 names=[m.group(1) for m in re.finditer(pattern,before,re.M)]
 assert len(names)==len(set(names))==456,'Method catalog changed'
 changed={n for n in names if p.method(before,n)!=p.method(after,n)}
 assert changed==ALLOWED,('unexpected method changes',changed^ALLOWED)
 for n in ['loadXtream','parseM3u','cobraDirectory','cobraLayoutGuide','cobraRenderGuideBrowser','showCobraHealthCenter','cobraSavePreferences','startSinglePlayer','closeFullscreenToCobraView','cobraDisposePlayer','onPause','showSettings','cobraOpenFilePicker','showCobraFilePickerPicker']:
  assert p.method(before,n)==p.method(after,n),n
 splash=(source/p.SRC/'Splash.java.in').read_text();patchedSplash=p.splash(splash)
 assert p.sha(splash)==p.PRE['Splash.java.in']
 # Reversing the single navigation change proves chooser artwork/geometry/settings/native startup untouched.
 a,b=p.span(splash,'launchInfinityExperience');c,d=p.span(patchedSplash,'launchInfinityExperience')
 assert splash[:a]+splash[b:]==patchedSplash[:c]+patchedSplash[d:]
 assert 'if ("live".equals(experience)) {' in p.method(patchedSplash,'launchInfinityExperience')
 assert 'cobraBeginMiniBackgroundPlayback()' not in p.method(after,'onStop')
 assert 'isCobraInPictureInPicture()' not in p.method(after,'startCobraPlayer')
 assert 'mBackgroundResumePlayers.clear()' in p.method(after,'cobraStopDismissedPip')
 service=(ROOT/'InfinityExtendedBackgroundService.java.in').read_text()
 assert 'new ExoPlayer' not in service and 'setMediaItem' not in service and 'prepare()' not in service
 assert 'setCallback(new android.media.session.MediaSession.Callback()' in service
 assert 'owner.state()' in service and 'owner.position()' in service
 for n in ['detachMiniPlayback','stopMiniPlayback','stopForExit']:
  assert 'startForegroundService' not in p.method(service,n) and 'request(context,' not in p.method(service,n),n
 assert 'setRequestedOrientation(' not in after,'A second orientation owner was introduced'
 assert 'Settings.System' not in after and 'ACCELEROMETER_ROTATION' not in after
 out.mkdir(parents=True,exist_ok=True)
 result={'accepted_commit':'8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261','activity_methods_total':len(names),'unchanged_activity_methods':len(names)-len(changed),'changed_activity_methods':sorted(changed),'splash_only_change':'Cobra-specific consumed browse intent','media_service_owns_player':False,'mini_foreground_handoff_only':True,'native_recompiled':False,'physical_device_verified':False}
 (out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS:',result['unchanged_activity_methods'],'existing Activity methods byte-identical; exact accepted preimages; targeted lifecycle/popup delta')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();audit(a.source,a.out)
