#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
def require(v,msg):
    if not v: raise RuntimeError(msg)
def block(text,name,kind='method'):
    pat=(re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
         if kind=='method' else re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(name)+r'\b',re.M))
    ms=list(pat.finditer(text));require(len(ms)==1,f'{name} cardinality={len(ms)}')
    start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=comment=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif comment:
            if c=='*' and n=='/':comment=False;i+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':comment=True;i+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return text[start:i+1]
        i+=1
    raise RuntimeError('unclosed '+name)
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/ACT).read_text();patch=json.loads(a.patch.read_text())
    hub=block(text,'showCobraPlayerOptionsHub');video=block(text,'showCobraVideoOptions');chrome=block(text,'cobraBuildPlayerChrome')
    settings=block(text,'showSettings');sources=block(text,'showSources');sheet=block(text,'cobraOpenSheet');guide=block(text,'cobraRenderGuideBrowser');pref=block(text,'CobraPreferencePolicy','class');channel_mode=block(text,'cobraChannelAspect');defaults=block(text,'cobraShowPlaybackDefaults')
    checks={
      'exact_2103194_parent':patch.get('base_build')==2103194 and patch.get('base_commit')=='2c2a759bd7f1ef380f21609105675ff2012d4d56',
      'player_hub':all(x in hub for x in ['Player options','Channels','TV Guide','Audio & subtitles','Video & display','Multi-View','Picture in Picture','Health Center','Player settings']),
      'recent_strip':'cobraAddRecentPlayerStrip(rows)' in hub and 'RECENT CHANNELS' in block(text,'cobraAddRecentPlayerStrip') and 'cobra-player-recent:' in text,
      'video_submenu':all(x in video for x in ['Display mode','Video details','Rotation','Display & performance','Picture in Picture']),
      'toolbar_expands':'expandedTools' in chrome and 'Favorite' in chrome and 'Audio' in chrome and 'Options' in chrome,
      'toolbar_narrow_safe':'new String[]{"guide","aspect","multi","more"}' in chrome,
      'player_settings_polished':'Playback, video and session controls' in block(text,'showPlayerSettingsDrawer') and 'cobra-player-settings-video' in text,
      'sheet_motion':'setScaleX(.985f)' in sheet and 'setScaleY(.985f)' in sheet and 'DecelerateInterpolator' in sheet and 'playerHub' in sheet,
      'focus_motion':all(x in block(text,'cobraPolishFocusable') for x in ['setOnFocusChangeListener','focused?1.018f:1f','scaleY(focused?1.018f:1f)','CobraMotionSpec.MICRO','DecelerateInterpolator']) and 'cobraPolishFocusable(row)' in block(text,'cobraSheetRow') and 'cobraPolishFocusable(row)' in block(text,'cobraDetailRow'),
      'global_button_motion':'cobraPolishFocusable(button)' in block(text,'action') and 'cobraPolishFocusable(b)' in block(text,'cobraTextButton'),
      'settings_stagger':'cobraAnimateChildrenIn(list)' in settings,
      'sources_stagger':'cobraAnimateChildrenIn(list)' in sources,
      'drawer_motion':'cobraAnimatePanelIn(panel,!isPortrait())' in block(text,'showCobraPlayerDrawer'),
      'guide_motion':'setTranslationY(dp(7))' in guide and 'DecelerateInterpolator' in guide,
      'empty_state_polish':'cobraModeSurface(18,true)' in block(text,'cobraModeEmpty'),
      'fold_adaptive_preserved':'CobraFoldAspectPolicy' in text and 'case 12: return "Fold Adaptive"' in block(text,'cobraAspectLabel'),
      'fold_channel_persistence':'value<=CobraFoldAspectPolicy.MODE' in pref,
      'fold_global_persistence':'mode<=CobraFoldAspectPolicy.MODE' in channel_mode,
      'fold_global_first':'final int[] modes={CobraFoldAspectPolicy.MODE,0,1,2,3,4,5,6,7,8,9,10}' in defaults,
      'fold_first_live':'final int[] modes={CobraFoldAspectPolicy.MODE,-1,0,1' in block(text,'cobraShowChannelAspect'),
      'tv_sources_preserved':'cobra_tv_sources' in text and 'TV SOURCES' in text,
      'pace_guard_preserved':'timeshift_provider_pace_limited' in text and 'REWRITE_ENABLED=false' in text,
      'parser_preserved':'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES' in text,
      'playback_unchanged':patch.get('playback_behavior_changed') is False,
      'network_unchanged':patch.get('network_selection_changed') is False,
      'timeshift_unchanged':patch.get('timeshift_ownership_changed') is False,
      'buffer_unchanged':patch.get('buffer_policy_changed') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103195,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103195 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103195 source checks')
if __name__=='__main__':main()
