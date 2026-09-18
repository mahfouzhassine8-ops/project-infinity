#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")

def sha(s):return hashlib.sha256((s if isinstance(s,bytes) else s.encode())).hexdigest()
def require(v,msg):
    if not v:raise RuntimeError(msg)

def method_span(text,name):
    ms=list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))
    require(len(ms)==1,'Method cardinality '+name+' = '+str(len(ms)))
    start=ms[0].start();i=text.index('{',ms[0].end());depth=0;quote=None;esc=False;line=False;block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False;i+=1
        elif quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        elif c=='/' and n=='/':line=True;i+=1
        elif c=='/' and n=='*':block=True;i+=1
        elif c in ('"',"'"):quote=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return text[start:i+1]
        i+=1
    raise RuntimeError('Unclosed '+name)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--patch',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    text=(a.source/REL).read_text()
    proof=json.loads(a.patch.read_text())
    checks={}

    bars=method_span(text,'cobraApplySystemBarsForSurface')
    confirm=method_span(text,'cobraConfirmBrowseSystemBars')
    safe=method_span(text,'cobraInstallBrowseSafeArea')
    focus=method_span(text,'onWindowFocusChanged')

    checks['scope_two_changed_methods']=proof.get('changed_methods')==['cobraApplySystemBarsForSurface','onWindowFocusChanged']
    checks['scope_one_new_helper']=proof.get('new_helpers')==['cobraConfirmBrowseSystemBars']
    checks['layout_declared_unchanged']=proof.get('layout_changed') is False
    checks['force_not_fullscreen_browse']='addFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)' in bars
    checks['force_not_fullscreen_cleared_for_player']='clearFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)' in bars
    checks['legacy_fullscreen_scrub']='flags&=~View.SYSTEM_UI_FLAG_FULLSCREEN' in bars
    checks['legacy_immersive_scrub']='SYSTEM_UI_FLAG_IMMERSIVE_STICKY' in bars and 'SYSTEM_UI_FLAG_IMMERSIVE' in bars
    checks['legacy_layout_fullscreen_scrub']='SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN' in bars
    checks['legacy_nav_hide_scrub']='SYSTEM_UI_FLAG_HIDE_NAVIGATION' in bars
    checks['modern_status_show']='controller.show(android.view.WindowInsets.Type.statusBars())' in bars
    checks['modern_status_hide_fullscreen']='controller.hide(android.view.WindowInsets.Type.statusBars())' in bars
    checks['modern_navigation_show']='controller.show(android.view.WindowInsets.Type.navigationBars())' in bars
    checks['default_system_bar_behavior']='BEHAVIOR_DEFAULT' in bars
    checks['next_frame_confirmation']='postOnAnimation(this::cobraConfirmBrowseSystemBars)' in bars
    checks['focus_sync_recovery']='if(hasFocus)' in focus and 'cobraApplySystemBarsForSurface();' in focus
    checks['focus_post_recovery']='mMain.post(this::cobraApplySystemBarsForSurface);' in focus
    checks['confirmation_force_not_fullscreen']='FLAG_FORCE_NOT_FULLSCREEN' in confirm
    checks['confirmation_shows_bars']='statusBars()' in confirm and 'navigationBars()' in confirm
    checks['safe_area_owner_still_present']='WindowInsets.Type.systemBars()' in safe and 'WindowInsets.Type.displayCutout()' in safe

    protected=proof.get('protected_methods',{})
    require(len(protected)>=35,'Protected method proof unexpectedly small')
    for name,expected in protected.items():
        checks['protected_'+name]=sha(method_span(text,name))==expected

    failed=[k for k,v in checks.items() if not v]
    a.out.mkdir(parents=True,exist_ok=True)
    report={'passed':not failed,'checks':checks,'failed':failed,
            'protected_methods':len(protected),'activity_sha256':sha(text)}
    (a.out/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    if failed:raise RuntimeError('2103167 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'status-bar source checks;',len(protected),'protected methods byte-identical')

if __name__=='__main__':main()
