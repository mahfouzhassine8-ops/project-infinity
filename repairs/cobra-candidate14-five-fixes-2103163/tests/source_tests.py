#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
SPLASH=Path('tools/android/packaging/xbmc/src/Splash.java.in')
SERVICE=Path('tools/android/packaging/xbmc/src/InfinityExtendedBackgroundService.java.in')
MANIFEST=Path('tools/android/packaging/xbmc/AndroidManifest.xml.in')
PRE={
 str(ACT):'16e75d481a662af6747260feab5f3377acd34f565274b7c768eeb293a8426640',
 str(SPLASH):'b7b88785f6b0e519e733f18675edb30969b0979f8e8d14cc3ddbd35b962d4854',
 str(SERVICE):'bb603dd85dcdf07d4b355d8cee06148ad22a4dd1e0984f4ce4afe7e3ecb14bcc',
 str(MANIFEST):'eeef97b36f64711c9c5e545f0b969e4a5041378a0c1875b0be161bc3ec17c138'
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--phase',choices=['pre','post'],required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 rows=[];passed=True
 if a.phase=='pre':
  for rel,expected in PRE.items():
   actual=sha(a.source/rel);ok=actual==expected;rows.append({'check':'preimage '+rel,'ok':ok,'actual':actual});passed&=ok
 else:
  act=(a.source/ACT).read_text();spl=(a.source/SPLASH).read_text();svc=(a.source/SERVICE).read_text();man=(a.source/MANIFEST).read_text()
  checks={
   'player settings bottom anchored':'playerSettings?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL' in act,
   'group normalization':'cobraNormalizeProviderGroup' in act and 'MAX_CHANNELS = 50000' in act,
   'mini-only background toggle':'PLAY IN BACKGROUND  •  ' in act and 'cobraMiniPreviewPlaying' in act,
   'fullscreen PiP preserved':'if (hasCobraVideo()) enterCobraPictureInPicture();' in act,
   'native media session':'Notification.MediaStyle' in svc and 'FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK' in svc,
   'mini service actions':'MINI_BACKGROUND_START' in svc and 'MINI_BACKGROUND_STOP' in svc,
   'compact chooser':'compactHeight=heightDp<700' in spl and 'adaptiveCardHeight' in spl,
   'file picker modes':'ACTION_GET_CONTENT' in act and 'MiXplorer' in act and 'ACTION_OPEN_DOCUMENT' in act,
   'media playback manifest':'FOREGROUND_SERVICE_MEDIA_PLAYBACK' in man and 'specialUse|mediaPlayback' in man,
   'no native global rotation mutation':'ACCELEROMETER_ROTATION' not in act and 'Settings.System' not in act,
  }
  for k,v in checks.items():rows.append({'check':k,'ok':bool(v)});passed&=bool(v)
 (a.out/'source-tests.json').write_text(json.dumps({'phase':a.phase,'passed':passed,'checks':rows},indent=2)+'\n')
 if not passed:raise SystemExit('FAIL: source acceptance')
 print('PASS:',a.phase,'source acceptance',len(rows),'checks')
if __name__=='__main__':main()
