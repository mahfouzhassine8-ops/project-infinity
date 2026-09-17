#!/usr/bin/env python3
"""Exact locked 2103157 + drawer selector -> audited Cobra completion candidate.
No native files, legacy receipts/recipes, provider logic or identities are edited.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, re
ROOT=Path(__file__).resolve().parent
BASE_SHA='b5d25a639b0c2eb09cf2503b5af40f4d9c5ed4545db9406e8bc7413ef0aa2943'
BASE_COMMIT='7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(value):return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
nav=load('completion_nav',ROOT.parent/'cobra-navigation-2103157/apply.py')
drawer=load('completion_drawer',ROOT.parent/'cobra-drawer-view/apply.py')
span=nav.span
def once(text,old,new):
 if text.count(old)!=1:raise ValueError('Anchor drift: '+old[:110])
 return text.replace(old,new,1)
def patch(before):
 if sha(before)!=BASE_SHA:raise ValueError('Expected exact locked 2103157 generated Activity')
 text=drawer.patch(before.encode()).decode();changes=[('method','toggleCobraDrawer')]
 def replace(name,code,kind='method'):
  nonlocal text
  a,b=span(text,name,kind);text=text[:a]+code.rstrip()+text[b:];changes.append((kind,name))
 def change(name,old,new,kind='method'):
  a,b=span(text,name,kind);replace(name,once(text[a:b],old,new),kind)
 # All new runtime data stays within this Activity and a new preference namespace.
 change('CobraPlayerBinding','    CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;}', '''    final String preferenceKey;
    CobraPlaybackChoice choice;
    final androidx.media3.common.TrackSelectionParameters trackDefaults;
    boolean restoringTracks,trackRestoreFailed;
    final CobraSurfaceRecovery recovery=new CobraSurfaceRecovery();
    CobraPlayerBinding(ExoPlayer p,Channel c){player=p;channel=c;preferenceKey=cobraPreferenceKey(c);choice=cobraReadChoice(preferenceKey);trackDefaults=p.getTrackSelectionParameters();}
    @Override public void onTracksChanged(Tracks tracks){if(current()){cobraRestoreChannelTracks(this);recovery.suspend("tracks_changed");}}
''','class')
 change('buildPlayer','    cobraAttachVideo(player,texture);','    cobraRestoreChannelTracks(binding);\n    cobraAttachVideo(player,texture);')
 change('cobraAttachVideo','    binding.texture=texture;player.setVideoTextureView(texture);','    binding.recovery.suspend("surface_changed");\n    binding.texture=texture;player.setVideoTextureView(texture);')
 change('cobraDisposePlayer','if(binding!=null){binding.closed=true;','if(binding!=null){binding.recovery.suspend("disposed");binding.closed=true;')
 change('mCobraPresentationTick','      cobraInspectMultiHealth();','      cobraInspectMultiHealth();\n      cobraInspectSurfaceRecovery();','field')
 change('onResume','    resumeCobraAfterBackground();','    resumeCobraAfterBackground();\n    mCobraHealthForeground=true;cobraSuspendRecovery();')
 change('onPause','    super.onPause();','    mCobraHealthForeground=false;cobraSuspendRecovery();\n    super.onPause();')
 change('onPictureInPictureModeChanged','mInPictureInPicture=inPictureInPictureMode;','mInPictureInPicture=inPictureInPictureMode;cobraSuspendRecovery();')
 change('openPlayerOverlay','mAspectMode=mPrefs.getInt(COBRA_ASPECT_MODE,0);','mAspectMode=cobraReadChoice(cobraPreferenceKey(channel)).aspect;')
 change('cobraFitBinding','cobraFitVideo(binding.texture,binding.player,binding.player==mPlayer&&!mInPictureInPicture?mAspectMode:0);','cobraFitVideo(binding.texture,binding.player,mInPictureInPicture?0:binding.preferenceKey.isEmpty()?(binding.player==mPlayer?mAspectMode:0):binding.choice.aspect);')
 change('cobraFitVideo','    VideoSize size=player.getVideoSize();','    VideoSize size=player.getVideoSize();\n    CobraPlayerBinding binding=mCobraPlayerBindings.get(player);\n    CobraPlaybackChoice choice=binding==null||binding.preferenceKey.isEmpty()?null:binding.choice;')
 change('cobraFitVideo','mode,mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f),mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f));','mode,choice==null?mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X,1.15f):choice.x,choice==null?mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y,.92f):choice.y);')
 replace('showTrackChooser','''  private void showTrackChooser(){cobraShowTracksFor(mPlayer,mPlaying);}''')
 change('showCobraAspectPicker','    if(mPlayer==null||mCobraPlayerLocked)return;','    if(mPlayer==null||mCobraPlayerLocked)return;\n    if(!cobraPreferenceKey(mPlaying).isEmpty()){cobraChooseChannelAspect(mPlaying);return;}')
 change('showCobraCustomAspectEditor','    if(mPlayerTexture==null||mCobraPlayerLocked)return;','    if(mPlayerTexture==null||mCobraPlayerLocked)return;\n    if(!cobraPreferenceKey(mPlaying).isEmpty()){cobraEditChannelSize(mPlaying);return;}')
 replace('toggleCobraPreviewCaptions','''  private void toggleCobraPreviewCaptions(){
    Channel channel=mGuidePreviewChannel;String key=cobraPreferenceKey(channel);if(key.isEmpty())return;
    CobraPlaybackChoice choice=cobraReadChoice(key);choice.captions="off".equals(choice.captions)?"on":"off";
    if(cobraWriteChoice(channel,key,choice)){mCobraPreviewCaptions="on".equals(choice.captions);toast(mCobraPreviewCaptions?"Captions on when available":"Captions off");}
  }''')
 change('showCobraChannelActions','    rows.addView(cobraSheetRow("record","Schedule recording"','    cobraCompletionRow(rows,"settings","Playback preferences","Only this channel and profile","cobra_channel_preferences",()->showCobraChannelPreferences(channel));\n    rows.addView(cobraSheetRow("record","Schedule recording"')
 # Drawer health entry does not invoke stopCobraPreview or navigate away from Live.
 change('toggleCobraDrawer','    cobraDrawerDestination(items,"more","Settings"','    cobraCompletionRow(items,"settings","Health Center","Playback, guide and diagnostics","cobra_drawer_health",()->{closeCobraExperienceDrawer();showCobraHealthCenter();});\n    cobraDrawerDestination(items,"more","Settings"')
 replace('showCobraHealthSnapshot','''  private void showCobraHealthSnapshot(){showCobraHealthCenter();}''')
 change('showSettings','action("COBRA HEALTH SNAPSHOT")','action("Cobra Health Center")')
 # Visible polish only. Keep the route title used by lifecycle and every action/destination ID.
 a,b=span(text,'showSettings');s=text[a:b]
 labels={'ASK WHICH EXPERIENCE ON NEXT LAUNCH':'Choose experience on next launch','INSTALL COBRA UI PACKAGE':'Install Cobra UI package','APPEARANCE  •  ':'Appearance  •  ','RELOAD COBRA UI THEME':'Reload Cobra appearance','REFRESH CURRENT SOURCE':'Refresh current source','REFRESH ALL ENABLED SOURCES':'Refresh enabled sources','PROFILES & PARENTAL CONTROLS':'Profiles & parental controls','EXPORT CRASH & DIAGNOSTICS ZIP':'Export Crash & Diagnostics ZIP','CUSTOM EPG FOR ACTIVE SOURCE':'Custom guide for active source'}
 for old,new in labels.items():s=once(s,'"'+old+'"','"'+new+'"')
 replace('showSettings',s)
 # Long labels now wrap, including accessibility font scaling. Row actions/focus handling are unchanged.
 change('cobraSheetRow','title.setMaxLines(1);copy.addView(title,new LinearLayout.LayoutParams(-1,dp(24)));','title.setMaxLines(2);title.setEllipsize(android.text.TextUtils.TruncateAt.END);copy.addView(title,new LinearLayout.LayoutParams(-1,-2));')
 change('cobraOpenSheet','dark?0xf5141c27:cobraThemeColor("panel",mTheme.panel)','"oled".equals(cobraEffectiveAppearanceMode())?Color.BLACK:dark?0xf5141c27:cobraThemeColor("panel",mTheme.panel)')
 change('cobraModeColor','oled?0xff080b10:dark?','oled?Color.BLACK:dark?')
 change('cobraModeColor','oled?0xff0c1118:dark?','oled?Color.BLACK:dark?')
 change('cobraDrawerDestination','parent.addView(row,new LinearLayout.LayoutParams(-1,dp(50)));','parent.addView(row,new LinearLayout.LayoutParams(-1,-2));')
 # Fresh health fields from actual player state. No URL, credentials or raw channel names.
 change('cobraFreshHealthSnapshot','      root.put("dropped_diagnostic_events",InfinityCobraDiagnostics.droppedEvents());','''      root.put("dropped_diagnostic_events",InfinityCobraDiagnostics.droppedEvents());
      root.put("health_center_schema",1);root.put("surface_recovery_enabled",mPrefs.getBoolean(COBRA_RECOVERY_ENABLED,true));
      root.put("recovery_foreground",mCobraHealthForeground);
      try{android.app.ActivityManager manager=(android.app.ActivityManager)getSystemService(ACTIVITY_SERVICE);android.app.ActivityManager.MemoryInfo memory=new android.app.ActivityManager.MemoryInfo();if(manager==null)root.put("device_memory","Unavailable");else{manager.getMemoryInfo(memory);root.put("device_memory",(memory.availMem/(1024*1024))+" MiB available · low memory: "+memory.lowMemory);}}catch(RuntimeException unavailable){root.put("device_memory","Unavailable");}''')
 change('cobraFreshHealthSnapshot','        p.put("fallback_attempted",binding.fallback);players.put(p);','''        p.put("fallback_attempted",binding.fallback);
        p.put("suppression_reason",binding.player.getPlaybackSuppressionReason());
        p.put("surface_attached",binding.texture!=null&&binding.texture.isAttachedToWindow());p.put("surface_available",binding.texture!=null&&binding.texture.isAvailable());
        p.put("surface_width",binding.texture==null?0:binding.texture.getWidth());p.put("surface_height",binding.texture==null?0:binding.texture.getHeight());
        p.put("surface_recovery_state",binding.recovery.state);p.put("surface_recovery_attempts",binding.recovery.attempts);
        p.put("channel_track_restore_failed",binding.trackRestoreFailed);
        p.put("channel_preferences_scoped",!binding.preferenceKey.isEmpty());p.put("channel_aspect",binding.choice.aspect);
        Format format=binding.player.getVideoFormat();p.put("video_format",format==null?"Not exposed":format.width+" × "+format.height+" "+format.sampleMimeType);
        players.put(p);''')
 module=(ROOT/'completion.java.inc').read_text();index=text.rfind('\n}');text=text[:index]+'\n'+module+text[index:]
 # Reverse every replaced member and appended byte to prove complete scope containment.
 reverse=text[:text.rfind('\n'+module)] + text[text.rfind('\n'+module)+1+len(module):]
 # The insertion above removes exactly its introduced newline and module.
 members=sorted(set(changes))
 for kind,name in members:
  a,b=span(before,name,kind);c,d=span(reverse,name,kind);reverse=reverse[:c]+before[a:b]+reverse[d:]
 if reverse!=before:raise ValueError('Unlisted whole-file source delta')
 return text,{'baseline_commit':BASE_COMMIT,'before_sha256':sha(before),'after_sha256':sha(text),'changed_members':members,'native_modified':False,'outside_listed_members_byte_identical':True,'device_verified':False,'official':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 if a.output.resolve()==a.input.resolve() or a.output.exists():raise ValueError('Output must be new; never overwrite the locked input')
 after,report=patch(a.input.read_text());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(after);a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n');print('PASS: isolated Cobra completion patch; '+report['after_sha256'])
if __name__=='__main__':main()
