#!/usr/bin/env python3
"""Locked 317 -> retained 318 changes -> user-reported playback/appearance repairs."""
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(here.parent / 'cobra-pro-handoff-317/apply.py'), str(root)], check=True)
src = root / 'tools/android/packaging/xbmc/src'

def one(s, old, new):
    assert s.count(old) == 1, (old[:120], s.count(old))
    return s.replace(old, new)

p = src / 'InfinityLiveActivity.java.in'
s = p.read_text()
s = one(s, '  private boolean mCobraProPlaybackOwned,mCobraProHeroBrowsing;', '''  private boolean mCobraProPlaybackOwned,mCobraProHeroBrowsing;
  private String mCobraProSportsPlaybackGameId="",mCobraProSportsPlaybackChannelKey="";''')
# Appearance selection never depends on Ambient. The material helper only decides
# whether the selected dark palette needs an unlit surface, not which palette wins.
s = one(s, 'private boolean cobraOledOff(){return mPrefs!=null&&CobraPresentationEffects.ambientMode(mPrefs)==CobraPresentationEffects.OFF&&!cobraNightCinemaActive();}', 'private boolean cobraOledOff(){return !"light".equals(cobraEffectiveAppearanceMode())&&mPrefs!=null&&CobraPresentationEffects.ambientMode(mPrefs)==CobraPresentationEffects.OFF&&!cobraNightCinemaActive();}')
s = one(s, '    if(cobraOledOff())return "oled";\n    if(CobraPresentationSafety.isSafe(this))return "dark";', '    if(CobraPresentationSafety.isSafe(this))return "oled";')
s = one(s, '    return CobraAppearancePolicy.effective(cobraStoredAppearanceMode(),cobraSystemDarkVariant(),night);', '    String selected=CobraAppearancePolicy.effective(cobraStoredAppearanceMode(),cobraSystemDarkVariant(),night);\n    return "dark".equals(selected)?"oled":selected;')
# Reserve the same video and control-strip geometry throughout control fading.
resize = next(line for line in s.splitlines(True) if 'int delta=Math.min(74' in line)
s = one(s, resize, '')
s = one(s, 'public void controlsChanged(){cobraLayoutGuide();}', 'public void controlsChanged(){/* Control visibility does not own video geometry. */}')
# Only a carousel step restores Preview after explicit Play. Ordinary row focus,
# redraws, and taps on the panel must not clear that override.
s = one(s, '    mCobraProHeroBrowsing=mCobraProPlaybackOwned;\n    if(!mCobraProPlaybackOwned)', '    if(!mCobraProPlaybackOwned)')
s = one(s, 'if(!mCobraProActive||mCobraProSlots.size()<2)return;int size=', 'if(!mCobraProActive||mCobraProSlots.size()<2)return;if(mCobraProPlaybackOwned)mCobraProHeroBrowsing=true;int size=')
s = one(s, 'if(selected<0)selected=0;\n      if(!mCobraProSlots.isEmpty())', 'if(selected<0)selected=0;if(mCobraProPlaybackOwned){int playing=cobraFindProSlot(mGuidePreviewChannel);if(playing>=0)selected=playing;}\n      if(!mCobraProSlots.isEmpty())')
s = one(s, 'CobraProUi.Program data=sports?cobraProSportsProgram(cobraProCurrentSportsGame()):cobraProProgram(cobraProCurrentChannel());', 'CobraProUi.Program data=sports?cobraProSportsProgram(cobraProCurrentSportsGame()):cobraProProgram(mCobraProPlaybackOwned&&!mCobraProHeroBrowsing?mGuidePreviewChannel:cobraProCurrentChannel());')
s = one(s, '    mCobraProHeroUi.bringToFront();', '''    // Keep the active decoder/session intact while a different preview panel is
    // selected. Do not display that old channel as the selected panel's preview.
    if(mCobraPreviewTexture!=null)mCobraPreviewTexture.setAlpha(mCobraProHeroBrowsing||(cobraProSportsHeroActive()&&cobraProLiveGameForChannel(mGuidePreviewChannel)==null)?0f:1f);
    mCobraProHeroUi.bringToFront();''')
s = one(s, 'mCobraProHeroUi=null;mCobraProOverlay=null;mCobraPreviewAutoplayAllowed=', 'mCobraProHeroUi=null;mCobraProOverlay=null;if(mCobraPreviewTexture!=null)mCobraPreviewTexture.setAlpha(1f);mCobraPreviewAutoplayAllowed=')
# Gate Sports only at Sports actions/data boundaries. Carousel stepping alone
# must never stop, release, retune, or start an owned stream.
s = one(s, 'mCobraProSportsResolvingId="";mCobraProHeroBrowsing=mCobraProPlaybackOwned;', 'mCobraProSportsResolvingId="";')
s = one(s, 'if(index==4){mCobraProSportsActive=true;mSearch="";', 'if(index==4){mCobraProSportsActive=true;cobraProEnforceSportsPlayback();mSearch="";')
s = one(s, '  private void cobraProOnSportsDataChanged(){\n    if(mCobraProActive){', '  private void cobraProOnSportsDataChanged(){\n    if(mCobraProActive){\n      if(mCobraProSportsActive&&mPlayerOverlay==null&&mMultiOverlay==null)cobraProEnforceSportsPlayback();')
s = one(s, 'mCobraProSportsResolvingId="";if(cobraSportsUniqueStrong(matches))mCobraProSportsResolvedChannel=', 'mCobraProSportsResolvingId="";CobraSportsGame current=cobraSportsGame(gameId);if(current!=null&&current.live()&&cobraSportsUniqueStrong(matches))mCobraProSportsResolvedChannel=')
s = one(s, '    if(game==null)return;final String gameId=game.id,profile=', '    if(game==null||!game.live())return;final String gameId=game.id,profile=')
s = one(s, '    cobraProSelectPlayingSlot(channel);mCobraProHeroBrowsing=false;', '''    if(mCobraProSportsActive&&cobraProLiveGameForChannel(channel)==null){toast("Select an available live sports broadcast");return;}
    if(!cobraChannelKey(channel).equals(mCobraProSportsPlaybackChannelKey)){mCobraProSportsPlaybackGameId="";mCobraProSportsPlaybackChannelKey="";}
    cobraProSelectPlayingSlot(channel);if(mCobraProSportsActive){int sports=cobraProSportsSlotIndex();if(sports>=0)mCobraProHeroIndex=sports;}mCobraProHeroBrowsing=false;''')
s = one(s, 'Channel channel=cobraProCurrentChannel();if(channel==null)return;mCobraProPlaybackOwned=false;', 'Channel channel=cobraProCurrentChannel();if(channel==null)return;if((mCobraProSportsActive||cobraProSportsHeroActive())&&cobraProLiveGameForChannel(channel)==null){toast("Select an available live sports broadcast");return;}mCobraProPlaybackOwned=false;')
helpers = '''  private CobraSportsGame cobraProLiveGameForChannel(Channel channel){
    if(channel==null)return null;
    if(cobraChannelKey(channel).equals(mCobraProSportsPlaybackChannelKey)){
      CobraSportsGame selected=cobraSportsGame(mCobraProSportsPlaybackGameId);
      // A known game ending invalidates its receipt; do not silently substitute
      // a different game that happens to share the broadcast network.
      if(!mCobraProSportsPlaybackGameId.isEmpty())return selected!=null&&selected.live()?selected:null;
    }
    ArrayList<GuideProgram> programs=cobraPrograms(channel);
    CobraSportsChannelInfo info=new CobraSportsChannelInfo(channel,cobraSportsNorm(channel.name+" "+channel.group+" "+channel.epgId),programs==null?new ArrayList<>():new ArrayList<>(programs));
    for(CobraSportsGame game:mCobraSportsGames){if(!game.live())continue;
      ArrayList<CobraSportsMatch> matches=cobraSportsResolve(game,java.util.Collections.singletonList(info));
      if(cobraSportsUniqueStrong(matches))return game;
    }
    return null;
  }
  private void cobraProEnforceSportsPlayback(){
    CobraSportsGame live=cobraProLiveGameForChannel(mGuidePreviewChannel);
    if(mCobraPreviewPlayer!=null&&live!=null){mCobraProSportsPlaybackGameId=live.id;mCobraProSportsPlaybackChannelKey=cobraChannelKey(mGuidePreviewChannel);return;}
    mCobraProPlaybackOwned=false;mCobraProHeroBrowsing=false;mCobraProState=COBRA_PRO_RESTING;
    mCobraProSportsPlaybackGameId="";mCobraProSportsPlaybackChannelKey="";
    stopCobraPreviewPlayerOnly();mCobraPreviewMuted=true;mCobraPreviewAutoplayAllowed=false;
    mGuidePreviewChannel=null;mGuidePreviewKey="";mGuidePreviewArmed=false;
    mCobraProPriorPlaying=false;mCobraProPriorMuted=true;mCobraProPriorAutoplayAllowed=false;
  }
  private void cobraPlaySportsBroadcast(CobraSportsGame game,Channel channel){
    CobraSportsGame current=game==null?null:cobraSportsGame(game.id);
    if(current==null||!current.live()){toast("This game is not live now");return;}
    if(mCobraProActive&&mPlayerOverlay==null&&mMultiOverlay==null){
      mCobraProSportsPlaybackGameId=current.id;mCobraProSportsPlaybackChannelKey=cobraChannelKey(channel);
      mCobraProSportsGameId=current.id;mCobraProSportsManualSelection=true;
    }
    playChannel(channel);
  }
'''
s = one(s, '  private void cobraProSportsWatch(){', helpers+'\n  private void cobraProSportsWatch(){')
a=s.index('  private void cobraSportsWatch(');b=s.index('\n',a)
watch=s[a:b].replace('playChannel(matches.get(0).channel)', 'cobraPlaySportsBroadcast(game,matches.get(0).channel)').replace('()->playChannel(m.channel)', '()->cobraPlaySportsBroadcast(game,m.channel)')
s=s[:a]+watch+s[b:]
p.write_text(s)

p=src/'CobraProUi.java.in';s=p.read_text()
s=one(s, 'void revealControls(){controlsVisible=true;', 'void revealControls(){if(browsing)return;controlsVisible=true;')
s=one(s, 'transport.setVisibility(watching&&!controlsVisible&&!browsing?GONE:VISIBLE);', 'transport.setVisibility(VISIBLE);')
s=one(s, 'bed=px(getContext(),state==WATCHING&&!controlsVisible&&!browsing?0:state==WATCHING?82:80)', 'bed=px(getContext(),state==WATCHING?82:80)')
# Light buttons must use light material colors when Subtle is selected.
s=one(s, 'p.setColor(material(getContext(),active?0xff185464:0xff1b2b34));', 'p.setColor(material(getContext(),light&&!overlay?(active?0xffdbeefa:0xfff0f6fa):(active?0xff185464:0xff1b2b34)));')
p.write_text(s)
print('Applied Cobra 2103319 corrections over retained 2103318 changes; locked input 2103317.')
