#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
def req(v,m):
    if not v: raise RuntimeError(m)
def block(t,n,k='method'):
    p=(re.compile(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(n)+r'\s*\(',re.M) if k=='method' else re.compile(r'^[ \t]{2,}(?:(?:private|public|protected|static|final)\s+)*class\s+'+re.escape(n)+r'\b',re.M))
    ms=list(p.finditer(t));req(len(ms)==1,n+' cardinality');s=ms[0].start();i=t.index('{',ms[0].end());d=0;q=None;esc=line=com=False
    while i<len(t):
      c=t[i];x=t[i+1] if i+1<len(t) else ''
      if line:
        if c=='\n':line=False
      elif com:
        if c=='*' and x=='/':com=False;i+=1
      elif q:
        if esc:esc=False
        elif c=='\\':esc=True
        elif c==q:q=None
      elif c=='/' and x=='/':line=True;i+=1
      elif c=='/' and x=='*':com=True;i+=1
      elif c in ('"',"'"):q=c
      elif c=='{':d+=1
      elif c=='}':
        d-=1
        if d==0:return t[s:i+1]
      i+=1
    raise RuntimeError('unclosed '+n)
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 t=(a.source/ACT).read_text();x=json.loads(a.patch.read_text());picker=block(t,'showCobraAspectPicker');channel=block(t,'cobraShowChannelAspect');label=block(t,'cobraAspectLabel');fit=block(t,'cobraFitVideo');policy=block(t,'CobraFoldAspectPolicy','class')
 checks={
 'exact_2103193_parent':x.get('base_build')==2103193 and x.get('base_commit')=='65cee6f8fdc60757a1e9bdaaac113be1ea344a2c',
 'fold_first':'final int[] modes={CobraFoldAspectPolicy.MODE,0,1' in picker,
 'fold_first_live':'final int[] modes={CobraFoldAspectPolicy.MODE,-1,0,1' in channel,
 'fold_named':'"Fold Adaptive"' in picker and 'case 12: return "Fold Adaptive"' in label,
 'mode_12':'static final int MODE=12' in policy,
 'viewport_driven':'viewportWidth' in policy and 'viewportHeight' in policy,
 'conservative_crop':'MAX_CROP=1.06f' in policy and 'mismatch<=1.18f' in policy,
 'extreme_windows_fit':'boolean roomy=Math.min(viewportWidth,viewportHeight)>=600' in policy,
 'fit_dispatch':'mode==CobraFoldAspectPolicy.MODE' in fit and 'CobraLayoutMath.fit' in fit,
 'layout_reactivity':'texture.addOnLayoutChangeListener(binding.layoutListener)' in t and 'cobraFitBinding(binding)' in t,
 'pip_preserved':'mInPictureInPicture?0:mAspectMode' in t,
 'source_manager_preserved':'cobra_tv_sources' in t and 'TV SOURCES' in t,
 'pace_guard_preserved':'timeshift_provider_pace_limited' in t and 'REWRITE_ENABLED=false' in t,
 'parser_preserved':'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES' in t,
 'playback_unchanged':x.get('playback_behavior_changed') is False,
 'network_unchanged':x.get('network_selection_changed') is False,
 'timeshift_unchanged':x.get('timeshift_ownership_changed') is False,
 'native_unchanged':x.get('native_changed') is False,
 'physical_unverified':x.get('physical_device_verified') is False}
 failed=[k for k,v in checks.items() if not v];result={'passed':not failed,'checks':checks,'failed':failed,'build':2103194,'physical_device_verified':False}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 if failed:raise RuntimeError('2103194 source audit failed: '+', '.join(failed))
 print('PASS:',len(checks),'2103194 source checks')
if __name__=='__main__':main()
