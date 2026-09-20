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
    settings=block(text,'showSettings');sources=block(text,'showSources');actions=block(text,'showSourceActions')
    checks={
      'exact_2103192_parent':patch.get('base_build')==2103192 and patch.get('base_commit')=='6277ab3bf7bc9e65010af84d0e62534c3e75ce18',
      'settings_exposes_sources':'Button tvSources = action("TV SOURCES")' in settings and 'tvSources.setTag("cobra_tv_sources")' in settings,
      'button_opens_existing_manager':'tvSources.setOnClickListener(v -> showSources())' in settings,
      'system_sources_placement':'SYSTEM & SOURCES' in settings and settings.index('list.addView(tvSources')>settings.index('list.addView(filePicker'),
      'existing_manager_preserved':'+  ADD TV SOURCE' in sources and 'showSourceActions(source)' in sources,
      'source_actions_preserved':'Delete' in actions or 'Remove' in actions or 'showSources()' in actions,
      'refresh_controls_preserved':'REFRESH CURRENT SOURCE' in settings and 'REFRESH ALL ENABLED SOURCES' in settings,
      'pace_guard_preserved':'timeshift_provider_pace_limited' in text and 'REWRITE_ENABLED=false' in text,
      'parser_preserved':'DETECT_ACCESS_UNITS+ALLOW_NON_IDR_KEYFRAMES' in text,
      'playback_unchanged':patch.get('playback_behavior_changed') is False,
      'network_unchanged':patch.get('network_selection_changed') is False,
      'timeshift_unchanged':patch.get('timeshift_ownership_changed') is False,
      'source_loading_unchanged':patch.get('source_loading_changed') is False,
      'native_unchanged':patch.get('native_changed') is False,
      'theme_unchanged':patch.get('theme_zip_changed') is False,
      'physical_unverified':patch.get('physical_device_verified') is False,
    }
    failed=[k for k,v in checks.items() if not v]
    result={'passed':not failed,'checks':checks,'failed':failed,'build':2103193,'physical_device_verified':False}
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    if failed: raise RuntimeError('2103193 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'2103193 source checks')
if __name__=='__main__':main()
