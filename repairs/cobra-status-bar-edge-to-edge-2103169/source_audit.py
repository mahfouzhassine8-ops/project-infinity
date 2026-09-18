#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,re

REL=Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
def sha(s):return hashlib.sha256((s if isinstance(s,bytes) else s.encode())).hexdigest()
def require(v,msg):
    if not v:raise RuntimeError(msg)
def method_span(text,name):
    ms=list(re.finditer(r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
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
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    text=(a.source/REL).read_text();proof=json.loads(a.patch.read_text());checks={}
    bars=method_span(text,'cobraApplySystemBarsForSurface')
    confirm=method_span(text,'cobraConfirmBrowseSystemBars')
    helper=method_span(text,'cobraBrowseSystemBarSurfaceColor')
    edge=method_span(text,'cobraConfigureEdgeToEdgeSystemBars')
    safe=method_span(text,'cobraInstallBrowseSafeArea')
    checks['scope_two_methods']=proof.get('changed_methods')==['cobraApplySystemBarsForSurface','cobraConfirmBrowseSystemBars']
    checks['two_bar_helpers']=proof.get('new_helpers')==['cobraConfigureEdgeToEdgeSystemBars','cobraBrowseSystemBarSurfaceColor']
    checks['layout_unchanged']=proof.get('layout_changed') is False
    checks['safe_area_unchanged']=proof.get('safe_area_changed') is False
    checks['player_unchanged']=proof.get('player_changed') is False
    checks['transparent_browse_bar']='setStatusBarColor(fullscreen?Color.BLACK:Color.TRANSPARENT)' in bars
    checks['edge_helper_called_browse']='cobraConfigureEdgeToEdgeSystemBars(window,decor)' in bars
    checks['edge_helper_called_confirmation']='cobraConfigureEdgeToEdgeSystemBars(window,decor)' in confirm
    checks['modern_edge_to_edge']='window.setDecorFitsSystemWindows(false)' in edge
    checks['modern_edge_to_edge_idempotent']='if(!mCobraEdgeToEdgeConfigured)' in edge and 'mCobraEdgeToEdgeConfigured=true' in edge
    checks['draws_system_bar_backgrounds']='FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS' in edge
    checks['clears_translucent_status']='FLAG_TRANSLUCENT_STATUS' in edge
    checks['legacy_layout_through_status']='SYSTEM_UI_FLAG_LAYOUT_STABLE' in edge and 'SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN' in edge
    checks['transparent_confirmation']='setStatusBarColor(Color.TRANSPARENT)' in confirm
    checks['confirmation_preserves_delivered_insets']='requestApplyInsets()' not in confirm and 'requestLayout()' in confirm
    checks['root_band_matches_bar']='mRoot.setBackgroundColor(barColor)' in bars and 'mRoot.setBackgroundColor(barColor)' in confirm
    checks['persistent_theme_pointer']='CobraVisualTheme.readPointer(this)' in helper and 'CobraVisualTheme.readFile(manifestFile,CobraVisualTheme.MAX_JSON)' in helper
    checks['persistent_theme_integrity']='generation.equals(CobraVisualTheme.hash(raw))' in helper
    checks['screen_style_cascade']='new String[]{"all.panel","screen.panel","screen"}' in helper
    checks['variant_precedence']='manifest.optJSONObject("base")' in helper and 'variants.optJSONObject(layout)' in helper and 'variants.optJSONObject(palette)' in helper
    checks['runtime_theme_fallback']='renderer.get("styles",key)' in helper and 'renderer.color("palette.background",fallback)' in helper
    checks['base_palette_fallback']='cobraThemeColor("background",mTheme.background)' in helper
    checks['fullscreen_black_preserved']='fullscreen?Color.BLACK:cobraBrowseSystemBarSurfaceColor()' in bars
    checks['inset_owner_preserved']='WindowInsets.Type.systemBars()' in safe and 'WindowInsets.Type.displayCutout()' in safe
    protected=proof.get('protected_methods',{})
    require(len(protected)>=35,'Protected method proof too small')
    for name,expected in protected.items():checks['protected_'+name]=sha(method_span(text,name))==expected
    failed=[k for k,v in checks.items() if not v]
    a.out.mkdir(parents=True,exist_ok=True)
    report={'passed':not failed,'checks':checks,'failed':failed,'protected_methods':len(protected),'activity_sha256':sha(text)}
    (a.out/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    if failed:raise RuntimeError('2103169 source audit failed: '+', '.join(failed))
    print('PASS:',len(checks),'status-bar edge-to-edge checks;',len(protected),'protected methods byte-identical')
if __name__=='__main__':main()
