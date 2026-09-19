#!/usr/bin/env python3
"""2103176: optional Live TV rewind + Xtream catch-up over exact passed 2103175.

Safety contract:
- OFF by default.
- No second ExoPlayer and no parallel provider connection.
- Existing live playback path is unchanged while feature is off.
- Rewind uses the current seekable live window when Media3 exposes one.
- Xtream catch-up is used only when the provider advertises tv_archive metadata.
- Going LIVE explicitly restores the normal live URL.
"""
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
BASE_BUILD=2103175
BASE_COMMIT="8f29df5a3a51e9462336412222e0d674af1d5969"

def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
 c=s.count(a)
 if c!=1:raise RuntimeError(f"{label}: expected one anchor, got {c}")
 return s.replace(a,b,1)

def matches(text,name):
 return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
def span(text,name):
 ms=matches(text,name)
 if len(ms)!=1:raise RuntimeError(f"Method cardinality {name}={len(ms)}")
 start=ms[0].start();i=text.index("{",ms[0].end());d=0;q=None;esc=line=block=False
 while i<len(text):
  c=text[i];n=text[i+1] if i+1<len(text) else ""
  if line:
   if c=="\n":line=False
  elif block:
   if c=="*" and n=="/":block=False;i+=1
  elif q:
   if esc:esc=False
   elif c=="\\":esc=True
   elif c==q:q=None
  elif c=="/" and n=="/":line=True;i+=1
  elif c=="/" and n=="*":block=True;i+=1
  elif c in ('"',"'"):q=c
  elif c=="{":d+=1
  elif c=="}":
   d-=1
   if d==0:return start,i+1
  i+=1
 raise RuntimeError("Unclosed "+name)
def method(text,name):
 a,b=span(text,name);return text[a:b]
def replace_method(text,name,new):
 a,b=span(text,name);return text[:a]+new.rstrip()+"\n"+text[b:]

CHANNEL_OLD=r'''  private static final class Channel {
    final String id;
    final String name;
    final String group;
    final String epgId;
    final String icon;
    final String primaryUrl;
    final String fallbackUrl;
    final Map<String, String> headers;

    Channel(
        String id, String name, String group, String epgId, String icon,
        String primaryUrl, String fallbackUrl, Map<String, String> headers) {
      this.id = id;
      this.name = name;
      this.group = group == null || group.isEmpty() ? "Other" : group;
      this.epgId = epgId == null ? "" : epgId;
      this.icon = icon == null ? "" : icon;
      this.primaryUrl = primaryUrl;
      this.fallbackUrl = fallbackUrl == null ? "" : fallbackUrl;
      this.headers = headers == null ? Collections.emptyMap() : headers;
    }
  }'''

CHANNEL_NEW=r'''  private static final class Channel {
    final String id;
    final String name;
    final String group;
    final String epgId;
    final String icon;
    final String primaryUrl;
    final String fallbackUrl;
    final Map<String, String> headers;
    final boolean catchup;
    final int catchupDays;
    final String providerStreamId;
    final String containerExtension;
    final String catchupTimezone;

    Channel(
        String id, String name, String group, String epgId, String icon,
        String primaryUrl, String fallbackUrl, Map<String, String> headers) {
      this(id,name,group,epgId,icon,primaryUrl,fallbackUrl,headers,false,0,"","ts","UTC");
    }

    Channel(
        String id, String name, String group, String epgId, String icon,
        String primaryUrl, String fallbackUrl, Map<String, String> headers,
        boolean catchup, int catchupDays, String providerStreamId,
        String containerExtension, String catchupTimezone) {
      this.id = id;
      this.name = name;
      this.group = group == null || group.isEmpty() ? "Other" : group;
      this.epgId = epgId == null ? "" : epgId;
      this.icon = icon == null ? "" : icon;
      this.primaryUrl = primaryUrl;
      this.fallbackUrl = fallbackUrl == null ? "" : fallbackUrl;
      this.headers = headers == null ? Collections.emptyMap() : headers;
      this.catchup=catchup;
      this.catchupDays=CobraLiveRewindPolicy.archiveDays(catchupDays);
      this.providerStreamId=providerStreamId==null?"":providerStreamId;
      this.containerExtension=containerExtension==null||containerExtension.isEmpty()?"ts":containerExtension;
      this.catchupTimezone=catchupTimezone==null||catchupTimezone.trim().isEmpty()?"UTC":catchupTimezone.trim();
    }
  }'''

HELPERS=r'''
  private static final String COBRA_LIVE_REWIND_ENABLED="cobra_live_rewind_enabled";
  private CobraIconButton mCobraLiveRewindButton,mCobraGoLiveButton;
  private boolean mCobraProviderCatchupActive;
  private Channel mCobraLiveRewindChannel;

  static final class CobraLiveRewindPolicy {
    static boolean archiveFlag(String value){
      return "1".equals(value)||"true".equalsIgnoreCase(value);
    }
    static int archiveDays(int value){return Math.max(0,Math.min(365,value));}
    static boolean withinArchive(long now,long start,int days){
      return days>0&&start>0&&start<=now&&now-start<=days*86400000L;
    }
    static long rewindTarget(long now,long programStart,long amount){
      return Math.max(programStart,Math.max(0L,now-Math.max(0L,amount)));
    }
    static int durationMinutes(long start,long end){
      if(end<=start)return 1;
      return Math.max(1,Math.min(1440,(int)((end-start+59999L)/60000L)));
    }
  }

  private boolean cobraLiveRewindEnabled(){return mPrefs!=null&&mPrefs.getBoolean(COBRA_LIVE_REWIND_ENABLED,false);}
  private String cobraLiveRewindLabel(){return cobraLiveRewindEnabled()?"ON":"OFF";}

  private void showCobraLiveRewindPicker(){
    LinearLayout rows=cobraOpenSheet("Live TV Rewind",
        "Uses a seekable live window when available and provider catch-up only when the channel advertises it. No second player is created.","live-rewind");
    boolean dark=cobraSheetIsDark();
    rows.addView(cobraSheetRow("close","Off",cobraLiveRewindEnabled()?null:"Selected",false,dark,()->{
      if(mCobraProviderCatchupActive)cobraGoLive();
      mPrefs.edit().putBoolean(COBRA_LIVE_REWIND_ENABLED,false).apply();
      cobraUpdateLiveRewindControls();closeCobraActionSheet();toast("Live TV rewind • Off");showSettings();
    }));
    rows.addView(cobraSheetRow("recent","On",cobraLiveRewindEnabled()?"Selected":"Enable rewind where the stream/provider supports it",false,dark,()->{
      mPrefs.edit().putBoolean(COBRA_LIVE_REWIND_ENABLED,true).apply();
      cobraUpdateLiveRewindControls();closeCobraActionSheet();toast("Live TV rewind • On");showSettings();
    }));
  }

  private LiveSource cobraSourceForChannel(Channel channel){
    if(channel==null)return null;String id=sourceIdForChannel(channel);
    for(LiveSource source:mSources)if(source.id.equals(id))return source;
    return null;
  }

  private boolean cobraProviderCatchupAvailable(Channel channel){
    if(channel==null||!channel.catchup||channel.catchupDays<=0||channel.providerStreamId.isEmpty())return false;
    LiveSource source=cobraSourceForChannel(channel);
    return source!=null&&"xtream".equals(source.type)&&!source.server.isEmpty()&&!source.username.isEmpty();
  }

  private String cobraCatchupUrl(Channel channel,long start,long end){
    if(!cobraProviderCatchupAvailable(channel))return "";
    LiveSource source=cobraSourceForChannel(channel);if(source==null)return "";
    long now=System.currentTimeMillis();
    if(!CobraLiveRewindPolicy.withinArchive(now,start,channel.catchupDays))return "";
    java.util.TimeZone zone=java.util.TimeZone.getTimeZone(channel.catchupTimezone);
    java.text.SimpleDateFormat clock=new java.text.SimpleDateFormat("yyyy-MM-dd:HH-mm",java.util.Locale.US);clock.setTimeZone(zone);
    int minutes=CobraLiveRewindPolicy.durationMinutes(start,Math.min(now,end>start?end:now));
    return source.server+"/timeshift/"+encPath(source.username)+"/"+encPath(source.password)+"/"
        +minutes+"/"+clock.format(new java.util.Date(start))+"/"+encPath(channel.providerStreamId)+"."+channel.containerExtension;
  }

  private boolean cobraLiveWindowSeekable(){
    try{return mPlayer!=null&&mPlaying!=null&&cobraLiveChannel(mPlaying)&&mPlayingVodKey.isEmpty()&&mPlayer.isCurrentMediaItemSeekable();}
    catch(RuntimeException unavailable){return false;}
  }

  private boolean cobraCanRestartCurrentProgram(){
    return cobraLiveRewindEnabled()&&mPlaying!=null&&cobraProviderCatchupAvailable(mPlaying)
        &&cobraCurrentProgram(mPlaying)!=null;
  }

  private boolean cobraCanRewindLive(){
    if(!cobraLiveRewindEnabled()||mPlayer==null||mPlaying==null||!cobraLiveChannel(mPlaying)||!mPlayingVodKey.isEmpty())return false;
    if(mCobraProviderCatchupActive)return mPlayer.isCurrentMediaItemSeekable()&&mPlayer.getCurrentPosition()>1000L;
    if(cobraLiveWindowSeekable()&&mPlayer.getCurrentPosition()>1000L)return true;
    return cobraCanRestartCurrentProgram();
  }

  private boolean cobraCanGoLive(){
    return cobraLiveRewindEnabled()&&mPlayer!=null&&mPlaying!=null&&cobraLiveChannel(mPlaying)
        &&(mCobraProviderCatchupActive||cobraLiveWindowSeekable());
  }

  private void cobraUpdateLiveRewindControls(){
    if(mCobraLiveRewindButton!=null){
      boolean enabled=cobraCanRewindLive();mCobraLiveRewindButton.setEnabled(enabled);
      mCobraLiveRewindButton.setAlpha(enabled?1f:.35f);
      mCobraLiveRewindButton.setContentDescription(enabled?"Rewind Live TV 30 seconds":"Rewind unavailable on this channel");
    }
    if(mCobraGoLiveButton!=null){
      boolean enabled=cobraCanGoLive();mCobraGoLiveButton.setEnabled(enabled);
      mCobraGoLiveButton.setAlpha(enabled?1f:.35f);
      mCobraGoLiveButton.setSelected(mCobraProviderCatchupActive);
      mCobraGoLiveButton.setContentDescription(mCobraProviderCatchupActive?"Return to live broadcast":"Jump to live edge");
    }
  }

  private void cobraResetLiveRewindState(){
    mCobraProviderCatchupActive=false;mCobraLiveRewindChannel=null;
    cobraUpdateLiveRewindControls();
  }

  private void cobraStartProviderCatchup(Channel channel,GuideProgram program,long target){
    if(!cobraLiveRewindEnabled()||mPlayer==null||channel==null||program==null)return;
    long now=System.currentTimeMillis(),end=Math.min(now,program.stop>program.start?program.stop:now);
    String url=cobraCatchupUrl(channel,program.start,end);
    if(url.isEmpty()){toast("Provider catch-up is unavailable for this program");return;}
    long offset=Math.max(0L,Math.min(end-program.start,target-program.start));
    CobraPlayerBinding binding=mCobraPlayerBindings.get(mPlayer);
    if(binding!=null)binding.fallback=true;
    try{
      mCobraProviderCatchupActive=true;mCobraLiveRewindChannel=channel;
      mPlayer.setMediaItem(mediaItem(url),offset);mPlayer.prepare();startCobraPlayer(mPlayer);
      cobraUpdatePlaybackLabels();cobraUpdateLiveRewindControls();showPlayerChromeTemporarily();
    }catch(RuntimeException failure){
      mCobraProviderCatchupActive=false;mCobraLiveRewindChannel=null;
      if(binding!=null)binding.fallback=false;
      toast("Provider catch-up could not start");cobraUpdateLiveRewindControls();
    }
  }

  private void cobraRestartCurrentProgram(){
    if(!cobraCanRestartCurrentProgram()){toast("Restart is not available for this channel");return;}
    GuideProgram program=cobraCurrentProgram(mPlaying);cobraStartProviderCatchup(mPlaying,program,program.start);
  }

  private void cobraRewindLive(long amountMs){
    if(!cobraLiveRewindEnabled()){toast("Turn on Live TV Rewind in Cobra Settings");return;}
    if(mPlayer==null||mPlaying==null||!cobraLiveChannel(mPlaying)){toast("Live TV rewind is unavailable");return;}
    try{
      if(mCobraProviderCatchupActive&&mPlayer.isCurrentMediaItemSeekable()){
        mPlayer.seekTo(Math.max(0L,mPlayer.getCurrentPosition()-amountMs));cobraUpdateLiveRewindControls();showPlayerChromeTemporarily();return;
      }
      if(cobraLiveWindowSeekable()){
        mPlayer.seekTo(Math.max(0L,mPlayer.getCurrentPosition()-amountMs));cobraUpdateLiveRewindControls();showPlayerChromeTemporarily();return;
      }
    }catch(RuntimeException ignored){}
    GuideProgram program=cobraCurrentProgram(mPlaying);
    if(program!=null&&cobraProviderCatchupAvailable(mPlaying)){
      cobraStartProviderCatchup(mPlaying,program,CobraLiveRewindPolicy.rewindTarget(System.currentTimeMillis(),program.start,amountMs));return;
    }
    toast("This channel does not expose a rewind window");
  }

  private void cobraGoLive(){
    if(mPlayer==null||mPlaying==null||!cobraLiveChannel(mPlaying))return;
    if(mCobraProviderCatchupActive){
      CobraPlayerBinding binding=mCobraPlayerBindings.get(mPlayer);if(binding!=null)binding.fallback=false;
      try{
        mCobraProviderCatchupActive=false;mCobraLiveRewindChannel=null;
        mPlayer.setMediaItem(mediaItem(mPlaying.primaryUrl));mPlayer.prepare();startCobraPlayer(mPlayer);
      }catch(RuntimeException failure){toast("Could not return to live broadcast");}
    }else if(cobraLiveWindowSeekable()){
      try{mPlayer.seekToDefaultPosition();}catch(RuntimeException ignored){}
    }
    cobraUpdatePlaybackLabels();cobraUpdateLiveRewindControls();showPlayerChromeTemporarily();
  }
'''

def apply(source,receipt_path,out):
 source=Path(source);receipt=json.loads(Path(receipt_path).read_text());out=Path(out)
 if receipt.get("version_code")!=BASE_BUILD:raise RuntimeError("Expected exact passed 2103175 source receipt")
 expected=receipt.get("files",{}).get(str(REL),{}).get("after")
 path=source/REL;before_bytes=path.read_bytes();before=before_bytes.decode()
 if not expected or sha(before_bytes)!=expected:raise RuntimeError("2103175 Activity preimage mismatch")

 protected=[
  "buildPlayer","cobraStartOwnedMiniPlayback","cobraEndMiniBackgroundPlayback",
  "onUserLeaveHint","onStop","onPictureInPictureModeChanged",
  "buildShell","onConfigurationChanged","cobraConfirmBrowseSystemBars",
  "cobraApplySystemBarsForSurface","cobraInstallBrowseSafeArea",
  "cobraReattachObservedSurface","loadM3u","parseM3u"
 ]
 guards={n:sha(method(before,n)) for n in protected}
 text=before

 text=once(text,CHANNEL_OLD,CHANNEL_NEW,"Channel catch-up metadata")

 load=method(text,"loadXtream")
 load=once(load,
'''    String statusValue = userInfo.optString("status", "");
    if (!statusValue.isEmpty()
        && !"active".equalsIgnoreCase(statusValue)
        && !"trial".equalsIgnoreCase(statusValue)) {
      throw new LiveException("Account status: " + statusValue);
    }''',
'''    String statusValue = userInfo.optString("status", "");
    if (!statusValue.isEmpty()
        && !"active".equalsIgnoreCase(statusValue)
        && !"trial".equalsIgnoreCase(statusValue)) {
      throw new LiveException("Account status: " + statusValue);
    }
    JSONObject serverInfo=auth.optJSONObject("server_info");
    String catchupTimezone=serverInfo==null?"UTC":serverInfo.optString("timezone","UTC");''',"Xtream timezone")
 load=once(load,
'''      String extension = sanitizeExtension(
          object.optString("container_extension", "ts"));
      String built = xtreamStreamUrl(source, id, extension);''',
'''      String extension = sanitizeExtension(
          object.optString("container_extension", "ts"));
      boolean catchup=CobraLiveRewindPolicy.archiveFlag(object.optString("tv_archive",String.valueOf(object.optInt("tv_archive",0))));
      int catchupDays=CobraLiveRewindPolicy.archiveDays(object.optInt("tv_archive_duration",0));
      String built = xtreamStreamUrl(source, id, extension);''',"Xtream archive metadata")
 load=once(load,
'''          primary,
          fallback,
          Collections.emptyMap()));''',
'''          primary,
          fallback,
          Collections.emptyMap(),
          catchup,catchupDays,id,extension,catchupTimezone));''',"Xtream Channel catch-up constructor")
 text=replace_method(text,"loadXtream",load)

 settings=method(text,"showSettings")
 settings=once(settings,
'''    Button filePicker = action("FILE PICKER  •  " + cobraFilePickerLabel());
    filePicker.setTag("cobra_file_picker");
    filePicker.setOnClickListener(v -> showCobraFilePickerPicker());''',
'''    Button filePicker = action("FILE PICKER  •  " + cobraFilePickerLabel());
    filePicker.setTag("cobra_file_picker");
    filePicker.setOnClickListener(v -> showCobraFilePickerPicker());

    Button liveRewind = action("LIVE TV REWIND  •  " + cobraLiveRewindLabel());
    liveRewind.setTag("cobra_live_rewind");
    liveRewind.setOnClickListener(v -> showCobraLiveRewindPicker());''',"settings rewind button")
 settings=once(settings,
'''    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));''',
'''    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(liveRewind, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));''',"settings rewind row")
 text=replace_method(text,"showSettings",settings)

 chrome=method(text,"cobraBuildPlayerChrome")
 chrome=once(chrome,
'''    CobraIconButton prev=cobraIcon("prev","Previous channel",true,v->stepChannel(-1)),pause=cobraIcon("pause","Pause",true,v->toggleCobraPlayerPlayPause()),next=cobraIcon("next","Next channel",true,v->stepChannel(1));pause.setTag("cobra_player_play_pause");pause.setBackground(surface(vtheme().color("cobra.cobraBuildPlayerChrome.colors.5",0x87000000),40,vtheme().color("cobra.cobraBuildPlayerChrome.colors.6",0x55ffffff),1));
    transport.addView(prev,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.16",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.17",56))));LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(dp(shortScreen?56:72),dp(shortScreen?56:72));pp.leftMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.18",24));pp.rightMargin=dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.19",24));transport.addView(pause,pp);transport.addView(next,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.20",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.21",56))));chrome.addView(transport,new LinearLayout.LayoutParams(-1,dp(shortScreen?60:76)));''',
'''    CobraIconButton prev=cobraIcon("prev","Previous channel",true,v->stepChannel(-1));
    CobraIconButton rewind=cobraIcon("prev","Rewind Live TV 30 seconds",true,v->cobraRewindLive(30000L));rewind.caption("-30s");rewind.setTag("cobra_live_rewind_30");mCobraLiveRewindButton=rewind;
    CobraIconButton pause=cobraIcon("pause","Pause",true,v->toggleCobraPlayerPlayPause());pause.setTag("cobra_player_play_pause");pause.setBackground(surface(vtheme().color("cobra.cobraBuildPlayerChrome.colors.5",0x87000000),40,vtheme().color("cobra.cobraBuildPlayerChrome.colors.6",0x55ffffff),1));
    CobraIconButton live=cobraIcon("play","Go Live",true,v->cobraGoLive());live.caption("LIVE");live.setTag("cobra_live_edge");mCobraGoLiveButton=live;
    CobraIconButton next=cobraIcon("next","Next channel",true,v->stepChannel(1));
    transport.addView(prev,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.16",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.17",56))));
    transport.addView(rewind,new LinearLayout.LayoutParams(dp(52),dp(52)));
    LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(dp(shortScreen?56:68),dp(shortScreen?56:68));pp.leftMargin=dp(14);pp.rightMargin=dp(14);transport.addView(pause,pp);
    transport.addView(live,new LinearLayout.LayoutParams(dp(52),dp(52)));
    transport.addView(next,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.20",56)),dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.21",56))));
    chrome.addView(transport,new LinearLayout.LayoutParams(-1,dp(shortScreen?60:76)));''',"player rewind transport")
 chrome=once(chrome,
'    vtheme().tree(chrome,"player.chrome");cobraUpdatePlayerRotationButton();cobraApplyPlayerRotation("chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();',
'    vtheme().tree(chrome,"player.chrome");cobraUpdatePlayerRotationButton();cobraApplyPlayerRotation("chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();cobraUpdateLiveRewindControls();',"player rewind state")
 text=replace_method(text,"cobraBuildPlayerChrome",chrome)

 drawer=method(text,"showPlayerSettingsDrawer")
 drawer=once(drawer,
'    cobraAddDetail(rows,"health","Health Center","Observe playback without stopping it","cobra-player-health",false,()->showCobraHealthCenter());',
'''    cobraAddDetail(rows,"health","Health Center","Observe playback without stopping it","cobra-player-health",false,()->showCobraHealthCenter());
    if(cobraCanRestartCurrentProgram())rows.addView(cobraSheetRow("recent","Restart current program","Provider catch-up",false,true,()->cobraRestartCurrentProgram()));''',"player restart program row")
 text=replace_method(text,"showPlayerSettingsDrawer",drawer)

 start=method(text,"startSinglePlayer")
 start=once(start,"    if(!isCobraAsyncAlive()||mPlayerTexture==null||mPlaying==null)return;",
'''    if(!isCobraAsyncAlive()||mPlayerTexture==null||mPlaying==null)return;
    cobraResetLiveRewindState();''',"start live reset")
 text=replace_method(text,"startSinglePlayer",start)

 promote=method(text,"promoteCobraPreviewToFullscreen")
 promote=once(promote,"    if(channel==null||mCobraPlayerLocked)return;",
'''    if(channel==null||mCobraPlayerLocked)return;
    cobraResetLiveRewindState();''',"preview promotion rewind reset")
 text=replace_method(text,"promoteCobraPreviewToFullscreen",promote)

 close=method(text,"closePlayer")
 close=once(close,"{","{\n    cobraResetLiveRewindState();mCobraLiveRewindButton=null;mCobraGoLiveButton=null;","close rewind reset")
 text=replace_method(text,"closePlayer",close)

 back=method(text,"closeFullscreenToCobraView")
 back=once(back,"    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}",
'''    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}
    if(mCobraProviderCatchupActive){mCobraProviderCatchupActive=false;mCobraLiveRewindChannel=null;closePlayer();showCobraPrimaryView();return;}''',"catch-up return to browse")
 text=replace_method(text,"closeFullscreenToCobraView",back)

 pos=text.rfind("\n}")
 if pos<0:raise RuntimeError("Activity terminator missing")
 text=text[:pos]+"\n"+HELPERS+"\n"+text[pos:]

 for n,h in guards.items():
  if sha(method(text,n))!=h:raise RuntimeError("Protected contract changed: "+n)

 for token in (
  'COBRA_LIVE_REWIND_ENABLED="cobra_live_rewind_enabled"',
  'LIVE TV REWIND  •  ',
  'tv_archive','tv_archive_duration',
  'providerStreamId','catchupTimezone',
  'cobra_live_rewind_30','cobra_live_edge',
  'mPlayer.isCurrentMediaItemSeekable()',
  '"/timeshift/"','setMediaItem(mediaItem(url),offset)',
  'mPrefs.getBoolean(COBRA_LIVE_REWIND_ENABLED,false)'
 ):
  if token not in text:raise RuntimeError("Live rewind contract missing: "+token)

 # Explicitly prohibit a second player/cache recorder in this first safe implementation.
 helpers=text[text.index('private static final String COBRA_LIVE_REWIND_ENABLED'):]
 if "new ExoPlayer" in helpers or "SimpleCache" in helpers or "CacheDataSource" in helpers:
  raise RuntimeError("Live rewind must not create a second decoder/network cache path")
 if 'private boolean cobraLiveRewindEnabled(){return mPrefs!=null&&mPrefs.getBoolean(COBRA_LIVE_REWIND_ENABLED,false);}' not in text:
  raise RuntimeError("Live rewind must default OFF")

 out.mkdir(parents=True,exist_ok=True);(out/"source-before").mkdir(exist_ok=True)
 (out/"source-before"/path.name).write_bytes(before_bytes)
 after=text.encode();path.write_bytes(after)
 report={
  "base_build":BASE_BUILD,"base_commit":BASE_COMMIT,
  "files":{str(REL):{"before":sha(before_bytes),"after":sha(after)}},
  "feature_default_enabled":False,
  "seekable_live_window_rewind":True,
  "xtream_archive_detection":["tv_archive","tv_archive_duration","server_info.timezone"],
  "provider_catchup_endpoint":"timeshift",
  "rewind_seconds":30,
  "go_live_control":True,
  "restart_current_program":True,
  "parallel_player_created":False,
  "local_disk_ring_buffer":False,
  "ordinary_live_path_when_off":"unchanged",
  "native_changed":False,"physical_device_verified":False
 }
 (out/"patch.json").write_text(json.dumps(report,indent=2)+"\n")
 print("PASS: 2103176 optional Live TV rewind/catch-up delta applied")

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();apply(a.source,a.receipt,a.out)
