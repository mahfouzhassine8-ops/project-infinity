#!/usr/bin/env python3
"""Exact source-only follow-up on 8f2c9c7. Never edits the baseline or native engine."""
from pathlib import Path
import hashlib,json,argparse,re
ROOT=Path(__file__).resolve().parent
SRC=Path('tools/android/packaging/xbmc/src')
PRE={'InfinityLiveActivity.java.in':'2226306907b9a702e8d3b54bdffddc2f116aa597142d64cef19228b202789feb',
     'Splash.java.in':'56778e9bd4382c0b29393a36734856a2798199f30f612432b874ccc3e29ba6bd',
     'InfinityExtendedBackgroundService.java.in':'1a20a06c446fc4b5d2467ea44cd768fa7b3271132f6022a7ea3abd6fec71afcb'}
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def once(s,old,new):
 if s.count(old)!=1:raise ValueError('Exact anchor drift: '+repr(old[:160])+' count='+str(s.count(old)))
 return s.replace(old,new,1)
def span(s,name):
 m=list(re.finditer(r'^  (?:@Override(?:[ \t]*\n  |[ \t]+))?(?:private|public|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',s,re.M))
 if len(m)!=1:raise ValueError('Method drift '+name+' '+str(len(m)))
 start=m[0].start();i=s.index('{',m[0].end());depth=0;quote=None;escape=False;line=False;comment=False
 while i<len(s):
  c=s[i];n=s[i+1] if i+1<len(s) else ''
  if line:
   if c=='\n':line=False
  elif comment:
   if c=='*' and n=='/':comment=False;i+=1
  elif quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c==quote:quote=None
  elif c=='/' and n=='/':line=True;i+=1
  elif c=='/' and n=='*':comment=True;i+=1
  elif c in ('"',"'"):quote=c
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if not depth:return start,i+1
  i+=1
 raise ValueError('Unclosed '+name)
def method(s,name):a,b=span(s,name);return s[a:b]
def edit(s,name,f):a,b=span(s,name);return s[:a]+f(s[a:b])+s[b:]
def insert(s,block):i=s.rfind('\n}');assert i>0;return s[:i]+'\n'+block.rstrip()+'\n'+s[i:]
def activity(s):
 s=edit(s,'cobraOpenSheet',lambda b:once(once(once(once(b,
  '    FrameLayout scrim=new FrameLayout(this);',
  '    final boolean videoSheet=mPlayerOverlay!=null||mMultiOverlay!=null;\n    FrameLayout scrim=videoSheet?new CobraVideoSettingsSheet():new FrameLayout(this);'),
  '    LinearLayout panel=new LinearLayout(this);panel.setOrientation',
  '    LinearLayout panel=new LinearLayout(this);panel.setTag("cobra_settings_panel");panel.setOrientation'),
  'super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(limit,View.MeasureSpec.AT_MOST));',
  'int cap=Math.min(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.11",480)),MeasureSpec.getMode(h)==MeasureSpec.UNSPECIFIED?limit:MeasureSpec.getSize(h));super.onMeasure(w,MeasureSpec.makeMeasureSpec(Math.max(0,cap),MeasureSpec.AT_MOST));'),
  '    close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;',
  '    close.requestFocus();vtheme().tree(panel,"sheet."+kind);scrim.requestApplyInsets();return items;'))
 s=edit(s,'onConfigurationChanged',lambda b:once(b,'    closeCobraActionSheet();mRebuildShellAfterPlayer=false;',
  '    if(!(mCobraActionSheet instanceof CobraVideoSettingsSheet))closeCobraActionSheet();else mCobraActionSheet.requestLayout();mRebuildShellAfterPlayer=false;'))
 s=edit(s,'onCreate',lambda b:once(b,'    mPrefs = getSharedPreferences(PREFS, MODE_PRIVATE);',
  '    mPrefs = getSharedPreferences(PREFS, MODE_PRIVATE);\n    mCobraPreviewAutoplayAllowed=!mPrefs.getBoolean(COBRA_EXPLICIT_STOP,false);'))
 s=edit(s,'onResume',lambda b:once(once(b,'    super.onResume();','    super.onResume();mCobraActivityStarted=true;'),
  '    resumeCobraAfterBackground();',
  '    cobraConsumeBrowseRequest();\n    if(mCobraPipDismissed)mBackgroundResumePlayers.clear();\n    mCobraPipWasActive=false;\n    resumeCobraAfterBackground();'))
 s=edit(s,'onUserLeaveHint',lambda b:once(b,
  '    if (hasCobraVideo()) enterCobraPictureInPicture();',
  '    if (hasCobraVideo()) {\n      if(Build.VERSION.SDK_INT>=31&&mMultiOverlay==null)configureCobraPip(true);\n      else enterCobraPictureInPicture();\n    }'))
 s=edit(s,'onStop',lambda b:once(b,
  '    if (!isCobraInPictureInPicture()) {if(!mCobraMiniBackgroundActive)mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();pauseCobraForBackground();}',
  '    mCobraActivityStarted=false;\n    if(mCobraPipWasActive||isCobraInPictureInPicture()){cobraStopDismissedPip();}\n    else{mCobraMiniBackgroundActive=cobraMiniBackgroundStillOwned();pauseCobraForBackground();}'))
 s=edit(s,'onPictureInPictureModeChanged',lambda b:once(b,
  '    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;',
  '    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;\n    if(inPictureInPictureMode){cobraEndMiniBackgroundPlayback();mCobraPipWasActive=true;}\n    else if(!mCobraActivityStarted&&mCobraPipWasActive)cobraStopDismissedPip();'))
 s=edit(s,'onDestroy',lambda b:once(b,'    if(!isChangingConfigurations())cobraEndMiniBackgroundPlayback();',
  '    cobraEndMiniBackgroundPlayback();'))
 s=edit(s,'pauseCobraForBackground',lambda b:once(b,'if(!mCobraMiniBackgroundActive)rememberAndPauseCobraPlayer(mCobraPreviewPlayer);',
  'if(!cobraMiniBackgroundStillOwned())rememberAndPauseCobraPlayer(mCobraPreviewPlayer);'))
 s=edit(s,'startCobraPlayer',lambda b:'''  private void startCobraPlayer(ExoPlayer player) {
    if(player==null)return;
    if(mCobraPipDismissed){mBackgroundResumePlayers.remove(player);player.pause();return;}
    if(mBackgroundStopped&&!(player==mCobraPreviewPlayer&&cobraMiniBackgroundStillOwned())){
      mBackgroundResumePlayers.put(player,Boolean.TRUE);player.pause();
    }else player.play();
  }''')
 s=edit(s,'configureCobraPip',lambda b:once(b,
  'PictureInPictureParams params = cobraPipParams(autoEnter && mMultiOverlay == null);',
  'PictureInPictureParams params = cobraPipParams(autoEnter && mMultiOverlay == null && mPlayerOverlay!=null\n          && !mCobraPipDismissed && !mBackgroundStopped && mPlayer!=null && mPlayer.getPlayWhenReady());'))
 s=edit(s,'enterCobraPictureInPicture',lambda b:once(b,'    if(!hasCobraVideo())return;',
  '    if(mCobraPipDismissed||!hasCobraVideo()||isCobraInPictureInPicture())return;'))
 # Existing callbacks, one binding/one audio owner: refresh auto-enter when paused/played.
 s=once(s,'if(player==mPlayer)cobraApplyPlayerRotation("is-playing");',
  'if(player==mPlayer){cobraApplyPlayerRotation("is-playing");configureCobraPip(player.getPlayWhenReady());}')
 s=edit(s,'onBackPressed',lambda b:b.replace('moveTaskToBack(true)','cobraBackgroundTask()'))
 s=edit(s,'playChannel',lambda b:once(b,'    if(channel==null||!isCobraAsyncAlive())return;',
  '    if(channel==null||!isCobraAsyncAlive())return;\n    cobraMarkExplicitPlayback();'))
 s=edit(s,'selectGuidePreview',lambda b:once(b,'    if(channel==null)return;',
  '    if(channel==null)return;\n    cobraMarkExplicitPlayback();'))
 s=edit(s,'toggleCobraPreviewPlayPause',lambda b:once(b,'  private void toggleCobraPreviewPlayPause() {',
  '  private void toggleCobraPreviewPlayPause() {\n    cobraMarkExplicitPlayback();'))
 s=edit(s,'playVodUrl',lambda b:b[:b.index('{')+1]+'\n    cobraMarkExplicitPlayback();'+b[b.index('{')+1:])
 s=edit(s,'promoteCobraPreviewToFullscreen',lambda b:once(b,'    mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";',
  '    cobraEndMiniBackgroundPlayback();\n    mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";'))
 # Same existing UI preference. Returning foreground detaches media presence only.
 mini=(ROOT/'mini-owner.java.inc').read_text()
 for name in ('cobraBeginMiniBackgroundPlayback','cobraEndMiniBackgroundPlayback'):
  replacement=method(mini,name);s=edit(s,name,lambda _,r=replacement:r)
 s=insert(s,(ROOT/'activity-164.java.inc').read_text())
 return s

def splash(s):
 return edit(s,'launchInfinityExperience',lambda b:once(b,
  '    if ("live".equals(experience))\n      intent.putExtra("infinity_live_profile", "cobra");',
  '    if ("live".equals(experience)) {\n      intent.putExtra("infinity_live_profile", "cobra");\n      intent.putExtra("cobra_open_browse",true);\n    }'))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 original={n:(a.source/SRC/n).read_bytes() for n in PRE}
 for n,v in original.items():
  if sha(v)!=PRE[n]:raise ValueError('Wrong 8f2c9c7 preimage: '+n+' '+sha(v))
 after={'InfinityLiveActivity.java.in':activity(original['InfinityLiveActivity.java.in'].decode()).encode(),
        'Splash.java.in':splash(original['Splash.java.in'].decode()).encode(),
        'InfinityExtendedBackgroundService.java.in':(ROOT/'InfinityExtendedBackgroundService.java.in').read_bytes()}
 # Preserve all exact original files before any mutation.
 for n,v in original.items():(a.out/('before-'+n)).write_bytes(v)
 report={'base_commit':'8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261','base_build':2103163,'target_build':2103164,'files':{str(SRC/n):{'before':sha(original[n]),'after':sha(v)} for n,v in after.items()}}
 for n,v in after.items():(a.source/SRC/n).write_bytes(v)
 (a.out/'patch.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: exact 8f2c9c7 -> 2103164 Android-only playback/popup corrections')
if __name__=='__main__':main()
