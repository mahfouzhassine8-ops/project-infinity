#!/usr/bin/env python3
"""Strict additive Cobra 2103158 presentation/health patch on the locked 2103157 Activity."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cobra157_apply',ROOT.parent/'cobra-navigation-2103157/apply.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
span=parent.span
BASE='b5d25a639b0c2eb09cf2503b5af40f4d9c5ed4545db9406e8bc7413ef0aa2943'
LOCKED='7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
def sha(value):return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
def once(text,old,new):
 if text.count(old)!=1:raise ValueError('Expected one source anchor: '+old[:120])
 return text.replace(old,new,1)
def patch(before):
 if sha(before)!=BASE:raise ValueError('Not the exact locked 2103157 Activity')
 text=before;changed=[]
 def transform(name,fn,kind='method'):
  nonlocal text
  a,b=span(text,name,kind);text=text[:a]+fn(text[a:b])+text[b:];changed.append(name)
 transform('CobraIconButton',lambda s:once(s,'      else if("source".equals(glyph))','''      else if("health".equals(glyph)){canvas.drawRoundRect(2,3,22,21,4,4,paint);p.moveTo(4,12);p.lineTo(8,12);p.lineTo(10,7);p.lineTo(14,17);p.lineTo(16,12);p.lineTo(20,12);canvas.drawPath(p,paint);}
      else if("settings".equals(glyph)){canvas.drawCircle(12,12,7,paint);canvas.drawCircle(12,12,2.5f,paint);for(int angle=0;angle<360;angle+=45){int turn=canvas.save();canvas.rotate(angle,12,12);canvas.drawLine(12,1,12,4,paint);canvas.restoreToCount(turn);}}
      else if("source".equals(glyph))'''),'class')
 transform('showCobraViewModeMenu',lambda _: '  private void showCobraViewModeMenu(){cobraPremiumViewMenu();}')
 def drawer(s):
  a=s.index('    LinearLayout header=');b=s.index('\n    ScrollView scroll=',a);s=s[:a]+'    panel.addView(cobraBrandHeader());'+s[b:]
  a=s.index('    TextView layout=');b=s.index('    cobraDrawerDestination(items,"more","Settings"',a)
  return s[:a]+'    cobraDrawerView(items);\n'+s[b:]
 transform('toggleCobraDrawer',drawer)
 transform('cobraDrawerDestination',lambda s:once(s,'LinearLayout row=cobraSheetRow(icon,label,null,false,cobraModeDark(),()->{closeCobraExperienceDrawer();action.run();});parent.addView(row,new LinearLayout.LayoutParams(-1,dp(50)));','LinearLayout row=cobraDetailRow(icon,label,null,"cobra-destination:"+destination,false,()->{closeCobraExperienceDrawer();action.run();});parent.addView(row,new LinearLayout.LayoutParams(-1,-2));'))
 transform('showSettings',lambda s:once(once(s,'action("COBRA HEALTH SNAPSHOT")','action("COBRA HEALTH CENTER")'),'health.setOnClickListener(v -> showCobraHealthSnapshot());','health.setOnClickListener(v -> showCobraHealthCenter());'))
 transform('showCobraChannelActions',lambda s:once(s,'    rows.addView(cobraSheetRow("favorite",','    cobraAddDetail(rows,"settings","Channel playback","Preferences saved for this channel","cobra-channel-preferences",false,()->cobraShowChannelPreferences(channel));\n    rows.addView(cobraSheetRow("favorite",'))
 transform('showPlayerSettingsDrawer',lambda s:once(s,'    rows.addView(cobraSheetRow("record",','    if(cobraLiveChannel(mPlaying)){final Channel selected=mPlaying;cobraAddDetail(rows,"settings","Channel playback","Display, languages and recovery","cobra-player-channel-preferences",false,()->cobraShowChannelPreferences(selected));}\n    cobraAddDetail(rows,"health","Health Center","Observe playback without stopping it","cobra-player-health",false,()->showCobraHealthCenter());\n    rows.addView(cobraSheetRow("record",'))
 transform('onResume',lambda s:once(s,'    super.onResume();','    super.onResume();\n    mCobraHealthForeground=true;cobraStartHealthTicker();'))
 transform('onPause',lambda s:once(s,'    super.onPause();','    cobraSuspendHealth();\n    super.onPause();'))
 transform('onDestroy',lambda s:once(s,'    closeCobraAsyncWork();','    cobraSuspendHealth();\n    closeCobraAsyncWork();'))
 transform('openPlayerOverlay',lambda s:once(s,'mAspectMode=mPrefs.getInt(COBRA_ASPECT_MODE,0);','mAspectMode=cobraChannelAspect(channel);'))
 transform('showCobraAspectPicker',lambda s:once(s,'    if(mPlayer==null||mCobraPlayerLocked)return;','    if(mPlayer==null||mCobraPlayerLocked)return;\n    if(cobraLiveChannel(mPlaying)){cobraShowChannelAspect(mPlaying);return;}'))
 transform('buildPlayer',lambda s:once(s,'    cobraAttachVideo(player,texture);','    player.addAnalyticsListener(binding.vitals);cobraApplyChannelTracks(binding);\n    cobraAttachVideo(player,texture);cobraStartHealthTicker();'))
 def binding(s):
  s=once(s,'    TextureView texture;View.OnLayoutChangeListener layoutListener;','    TextureView texture;View.OnLayoutChangeListener layoutListener;\n    final CobraSessionVitals vitals;CobraCaptionOverlay captions;')
  s=once(s,'CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;}','CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;vitals=new CobraSessionVitals(p,c);}')
  s=once(s,'lastFrameMs=android.os.SystemClock.elapsedRealtime();if(!recentMarked)', 'lastFrameMs=android.os.SystemClock.elapsedRealtime();if(vitals.firstFrameAt<0)vitals.firstFrameAt=lastFrameMs;if("reattach_requested".equals(vitals.lastRecovery))vitals.lastRecovery="first_frame_after_reattach";if(!recentMarked)')
  s=once(s,'    @Override public void onIsPlayingChanged', '    @Override public void onCues(androidx.media3.common.text.CueGroup group){if(current()&&captions!=null)captions.cues("off".equals(vitals.preferences.subtitles)?Collections.emptyList():group.cues);}\n    @Override public void onPositionDiscontinuity(Player.PositionInfo oldPosition,Player.PositionInfo newPosition,int reason){if(current())vitals.recovery.suspend();}\n    @Override public void onTracksChanged(Tracks tracks){if(current())vitals.recovery.suspend();}\n    @Override public void onIsPlayingChanged')
  s=once(s,'      error=failure==null?"UNKNOWN":failure.getErrorCodeName();','      error=failure==null?"UNKNOWN":failure.getErrorCodeName();\n      vitals.lastError=error;vitals.lastErrorAt=System.currentTimeMillis();vitals.recovery.suspend();')
  s=once(s,'if(!fallback&&!channel.fallbackUrl.isEmpty()', 'if(!"primary".equals(vitals.preferences.fallback)&&!fallback&&!channel.fallbackUrl.isEmpty()')
  s=once(s,'          if(!current())return;','          if(!current()||\"primary\".equals(vitals.preferences.fallback))return;')
  return s
 transform('CobraPlayerBinding',binding,'class')
 transform('cobraAttachVideo',lambda s:once(s,'    binding.texture=texture;player.setVideoTextureView(texture);','    binding.texture=texture;player.setVideoTextureView(texture);\n    binding.vitals.recovery.suspend();cobraAttachCaptions(binding,texture);'))
 transform('cobraDisposePlayer',lambda s:once(s,'binding.closed=true;player.removeListener(binding);','binding.closed=true;player.removeListener(binding);player.removeAnalyticsListener(binding.vitals);if(binding.captions!=null&&binding.captions.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)binding.captions.getParent()).removeView(binding.captions);'))
 transform('cobraFitBinding',lambda s:'''  private void cobraFitBinding(CobraPlayerBinding binding) {
    int mode=binding.player==mPlayer?mAspectMode:0;
    if(binding.vitals.live&&binding.vitals.preferences.aspect>=0)mode=binding.vitals.preferences.aspect;
    cobraFitVideo(binding.texture,binding.player,mInPictureInPicture?0:mode);
  }''')
 def fit(s):
  s=once(s,'    VideoSize size=player.getVideoSize();','    VideoSize size=player.getVideoSize();\n    CobraPlayerBinding b=mCobraPlayerBindings.get(player);CobraChannelPreferences saved=b!=null&&b.vitals.live?b.vitals.preferences:null;\n    float customX=saved!=null&&saved.aspect==11?saved.x:mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f);\n    float customY=saved!=null&&saved.aspect==11?saved.y:mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f);')
  return once(s,'mode,mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f),mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f)', 'mode,customX,customY')
 transform('cobraFitVideo',fit)
 transform('cobraFreshHealthSnapshot',lambda s:once(s,'      return root.toString(2);','      cobraAddSessionHealth(root);\n      return root.toString(2);'))
 transform('closeCobraActionSheet',lambda s:once(s,'    mCobraActionSheet=null;', '    mCobraHealthSummary=null;\n    mCobraActionSheet=null;'))
 # A pre-existing unbounded buffering watchdog must not undermine the new recovery limit.
 text=once(text,'        if (System.currentTimeMillis() - mBufferingSince >= 12000L) {\n          mPlaybackRetryCount++;','        if (System.currentTimeMillis() - mBufferingSince >= 12000L) {\n          if(!cobraPermitBufferRetry(mPlayer)){mBufferingSince=0L;return;}\n          mPlaybackRetryCount++;')
 # Keep shader/engine/assets out of branding. The shared sheet honors true black.
 transform('cobraOpenSheet',lambda s:once(s,'surface(dark?0xf5141c27:', 'surface(dark?("oled".equals(cobraEffectiveAppearanceMode())?0xff000000:0xf5141c27):'))
 additions='\n'.join((ROOT/name).read_text() for name in ('policies.java.inc','runtime.java.inc','captions.java.inc','ui.java.inc'))
 pos=text.rfind('\n}');text=text[:pos]+'\n'+additions+text[pos:]
 names=set(re.findall(r'^  (?:private|public|protected) [^\n;=(){}]*\b([A-Za-z0-9_]+)\s*\(',before,re.M));protected=[]
 for name in sorted(names-set(changed)):
  try:a,b=span(before,name);c,d=span(text,name)
  except ValueError:continue
  if before[a:b]!=text[c:d]:raise ValueError('Unexpected method edit: '+name)
  protected.append(name)
 for name in ('CobraModeLayout','CobraMobileChannelRow','CobraBroadcastRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow'):
  a,b=span(before,name,'class');c,d=span(text,name,'class');assert before[a:b]==text[c:d],name
 for name in ('cobraShowGuideShell','cobraLayoutGuide','cobraSwitchMode','setMultiAudio','cobraLayoutMultiTiles','loadGuideAsync'):
  a,b=span(before,name);c,d=span(text,name);assert before[a:b]==text[c:d],name
 return text,{'parent_commit':LOCKED,'before_sha256':sha(before),'after_sha256':sha(text),'changed_members':changed,'changed_field':'mStallWatchdog (two-retry guard only)','protected_methods':protected,'native_modified':False,'physical_device_verified':False,'candidate_locked':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();path=a.source/REL
 text,report=patch(path.read_text());receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
 if data['version_code']!=2103157:raise ValueError('Expected reconstructed locked 2103157')
 for rel,row in data['files'].items():
  if sha((a.source/rel).read_bytes())!=row['after']:raise ValueError('Baseline receipt drift: '+rel)
 path.write_text(text);data['files'][REL]['after']=sha(text);receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n');print('PASS: scoped health/playback delta; protected Activity methods:',len(report['protected_methods']))
if __name__=='__main__':main()
