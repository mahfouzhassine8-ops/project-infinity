#!/usr/bin/env python3
"""Static delivery audit for 2103166.

This is intentionally conservative: the entire ordinary Cobra UI must still hang from the single
browse root, while player/Multi-View remain the only status-bar fullscreen owners.
"""
from pathlib import Path
import argparse,json,re,hashlib

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")

def sha(x):return hashlib.sha256((x if isinstance(x,bytes) else x.encode())).hexdigest()
def require(v,msg):
    if not v:raise RuntimeError(msg)

def span(text,name):
    m=list(re.finditer(r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
    require(len(m)==1,'Method cardinality '+name+' = '+str(len(m)))
    start=m[0].start();i=text.index('{',m[0].end());depth=0;quote=None;esc=False;line=False;block=False
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
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();proof=json.loads(a.patch.read_text());checks={}

    build=span(text,'buildShell');bars=span(text,'cobraApplySystemBarsForSurface')
    checks['single_activity_content_root']=text.count('setContentView(')==1 and 'setContentView(frame);' in build
    checks['browse_root_inset_listener']='cobraInstallBrowseSafeArea(mRoot);' in build and 'mRoot.requestApplyInsets();' in build
    checks['system_and_cutout_insets']='WindowInsets.Type.systemBars()' in text and 'WindowInsets.Type.displayCutout()' in text
    checks['no_global_fullscreen']='FLAG_FULLSCREEN' not in span(text,'onCreate')
    checks['fullscreen_surface_scope']='mPlayerOverlay!=null||mMultiOverlay!=null' in bars
    checks['status_bar_show_hide']='controller.hide(android.view.WindowInsets.Type.statusBars())' in bars and 'controller.show(android.view.WindowInsets.Type.statusBars())' in bars
    checks['navigation_bar_never_hidden']='navigationBars()' not in bars and 'hide(android.view.WindowInsets.Type.navigationBars())' not in text
    checks['bar_contrast_policy']='APPEARANCE_LIGHT_STATUS_BARS' in bars and 'APPEARANCE_LIGHT_NAVIGATION_BARS' in bars
    checks['root_padding_idempotent']='getPaddingTop()!=top' in text and 'v.setPadding(left,top,right,bottom)' in text

    # Internal screens must remain stage/root descendants instead of inventing new windows.
    for name in ('showSettings','showSources','showProfiles','showCobraHealthCenter','showVodLibrary'):
        body=span(text,name)
        checks['internal_'+name]=('setContentView(' not in body and 'getWindow().getDecorView()).addView' not in body)

    # The exact protected contracts recorded during apply must still hash identically.
    protected=proof.get('protected_methods',{})
    require(len(protected)>=25,'Protected-method proof unexpectedly small')
    for name,expected in protected.items():
        checks['protected_'+name]=sha(span(text,name))==expected

    failed=[k for k,v in checks.items() if not v]
    a.out.mkdir(parents=True,exist_ok=True)
    report={'passed':not failed,'checks':checks,'failed':failed,'protected_methods':len(protected),'activity_sha256':sha(text)}
    (a.out/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    if failed:raise RuntimeError('2103166 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'end-to-end source checks;',len(protected),'protected methods byte-identical')

if __name__=='__main__':main()
