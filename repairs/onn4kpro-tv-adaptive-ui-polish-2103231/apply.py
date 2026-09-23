#!/usr/bin/env python3
"""2103231 RC11: preservation-first adaptive TV UI polish.

Parent: exact locked 2103230 RC10.

Approved scope:
- Keep RC10 Drawer -> Groups -> Grid -> Player behavior and all playback/Multi-View contracts.
- Remove the redundant on-screen hamburger from TV Grid (drawer still via Back/Menu).
- Remove the large group dropdown row beneath the mini player.
- Put Settings immediately beside Search in the compact grid utility row.
- Enlarge the existing RC10 mini player adaptively; do not replace/recreate its preview engine.
- Preserve short translation/alpha motion and 32-bit TV performance.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

VERSION=2103231
OLD_VERSION=2103230
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Navigation-Motion-RC10'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Adaptive-UI-Polish-RC11'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)

def span(text:str,name:str):
    pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    ms=list(pat.finditer(text)); req(len(ms)==1,f'method cardinality {name}={len(ms)}')
    start=ms[0].start();brace=text.find('{',start);depth=0;quote=None;esc=line=block=False;i=brace
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
            if depth==0:return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)

def member(text,name):
    a,b=span(text,name);return text[a:b]
def replace_member(text,name,new):
    a,b=span(text,name);return text[:a]+new.rstrip()+text[b:]

HELPERS=r'''  private static final String COBRA_TV_ADAPTIVE_UI_BUILD="cobra_tv_adaptive_ui_2103231";

  private int cobraTvClamp(int value,int low,int high){
    return Math.max(low,Math.min(high,value));
  }

  private void cobraTvOpenSettingsFromGuide(){
    stopCobraPreview();
    showSettings();
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    marker='  private static final String COBRA_TV_NAVIGATION_MOTION_BUILD="cobra_tv_navigation_motion_2103230";'
    req(s.count(marker)==1,'Exact locked RC10 navigation marker missing')
    s=s.replace(marker,HELPERS+marker,1)

    # Remove the redundant hamburger trigger from the TV toolbar. The drawer remains reachable
    # through RC10 Back hierarchy and the remote MENU key.
    chrome=member(s,'cobraBuildModeChrome')
    old='    CobraIconButton tvMenu=cobraIcon("guide","Open Cobra navigation",dark,v->toggleCobraDrawer());tvMenu.setTag("cobra_tv_toolbar_menu");mCobraModeToolbar.addView(tvMenu,new LinearLayout.LayoutParams(dp(52),-1));\n'
    req(chrome.count(old)==1,'TV hamburger anchor missing')
    chrome=chrome.replace(old,'',1)
    chrome=chrome.replace('title.setPadding(dp(vtheme().dimension("cobra.cobraBuildModeChrome.dimensions.2",8)),0,0,0);',
                          'title.setPadding(dp(18),0,0,0);',1)
    s=replace_member(s,'cobraBuildModeChrome',chrome)

    # Replace the large group dropdown row below the preview with a compact right-aligned utility
    # strip. Group selection now belongs to RC10's dedicated Groups level.
    s=replace_member(s,'cobraModeBrowserHeader',r'''  private void cobraModeBrowserHeader(LinearLayout parent,String name){
    LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL|Gravity.RIGHT);row.setPadding(dp(14),dp(2),dp(14),dp(2));
    TextView context=cobraText(name,cobraModeColor("muted"),11);context.setSingleLine(true);context.setEllipsize(android.text.TextUtils.TruncateAt.END);context.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
    row.addView(context,new LinearLayout.LayoutParams(0,dp(46),1));
    CobraIconButton source=cobraIcon("source","Choose playlist",cobraModeDark(),v->cobraOpenTvDirectory(true));source.setTag("cobra_tv_grid_source");row.addView(source,new LinearLayout.LayoutParams(dp(48),dp(48)));
    CobraIconButton search=cobraIcon("search","Search channels",cobraModeDark(),v->cobraShowChannelSearch());search.setTag("cobra_tv_grid_search");LinearLayout.LayoutParams searchLp=new LinearLayout.LayoutParams(dp(48),dp(48));searchLp.leftMargin=dp(6);row.addView(search,searchLp);
    CobraIconButton settings=cobraIcon("settings","Settings",cobraModeDark(),v->cobraTvOpenSettingsFromGuide());settings.setTag("cobra_tv_grid_settings");LinearLayout.LayoutParams settingsLp=new LinearLayout.LayoutParams(dp(48),dp(48));settingsLp.leftMargin=dp(6);row.addView(settings,settingsLp);
    parent.addView(row,new LinearLayout.LayoutParams(-1,dp(50)));
  }''')

    # Search and Settings are adjacent in the D-pad graph; the removed group dropdown and
    # hamburger are no longer focus destinations.
    s=replace_member(s,'cobraTvMoveGridHeader',r'''  private boolean cobraTvMoveGridHeader(String tag,int direction){
    String[] tags={"cobra_tv_grid_source","cobra_tv_grid_search","cobra_tv_grid_settings"};int at=-1;
    for(int i=0;i<tags.length;i++)if(tags[i].equals(tag)){at=i;break;}if(at<0)return false;
    int next=Math.max(0,Math.min(tags.length-1,at+direction));return cobraTvFocusTagged(mCobraGuideBrowser,tags[next]);
  }''')

    s=replace_member(s,'cobraTvHandleGuideKey',r'''  private boolean cobraTvHandleGuideKey(KeyEvent event){
    if(event.getAction()!=KeyEvent.ACTION_DOWN||mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow()||mPlayerOverlay!=null||mMultiOverlay!=null||cobraTvTransientRoot()!=null)return false;
    int key=event.getKeyCode();View focus=getCurrentFocus();Object raw=focus==null?null:focus.getTag();String tag=raw instanceof String?(String)raw:"";
    if(key==KeyEvent.KEYCODE_MENU){toggleCobraDrawer();return true;}
    boolean gridHeader=tag.startsWith("cobra_tv_grid_")&&!tag.startsWith("cobra_tv_grid_time");
    boolean gridTime=tag.startsWith("cobra_tv_grid_time");
    if(gridHeader){
      if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvMoveGridHeader(tag,-1);
      if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvMoveGridHeader(tag,1);
      if(key==KeyEvent.KEYCODE_DPAD_UP){View visuals=mCobraModeToolbar==null?null:mCobraModeToolbar.findViewWithTag("cobra_mode_visuals");if(visuals!=null){visuals.requestFocus();return true;}return true;}
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_time_now"))return true;cobraTvFocusGuideBody();return true;}
    }
    if(gridTime){
      if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvMoveGridTime(tag,-1);
      if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvMoveGridTime(tag,1);
      if(key==KeyEvent.KEYCODE_DPAD_UP){if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_search"))return true;return cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_settings");}
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){cobraTvFocusGuideBody();return true;}
    }
    if((tag.startsWith("cobra-channel:")||tag.startsWith("cobra-program:")||tag.startsWith("cobra-gap:"))&&key==KeyEvent.KEYCODE_DPAD_UP&&cobraTvGuideListPosition(focus)==0){
      if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_time_now"))return true;
      return cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_search");
    }
    if("cobra_mode_visuals".equals(tag)&&key==KeyEvent.KEYCODE_DPAD_DOWN){
      if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_search"))return true;
      return cobraTvFocusGuideBody();
    }
    return false;
  }''')

    # Adaptive 10-foot layout: preserve the exact RC10 preview engine and guide objects, but
    # allocate a larger 16:9 preview band and let the EPG consume the remaining height.
    s=replace_member(s,'cobraLayoutGuide',r'''  private void cobraLayoutGuide(){
    if(mCobraGuideShell==null||mCobraTvGuideLayoutBusy)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;
    mCobraTvGuideLayoutBusy=true;
    try{
      mCobraLastGuideWidth=w;mCobraLastGuideHeight=h;float density=Math.max(.01f,getResources().getDisplayMetrics().density);
      mCobraModeLayout=CobraModeLayout.solve("grid",Math.max(1,Math.round(w/density)),Math.max(1,Math.round(h/density)),getResources().getConfiguration().fontScale,false);
      int[][] boxes={mCobraModeLayout.toolbar,mCobraModeLayout.rail,mCobraModeLayout.directory,mCobraModeLayout.video,mCobraModeLayout.details,mCobraModeLayout.browser,mCobraModeLayout.footer};
      View[] views={mCobraModeToolbar,mCobraModeRail,mCobraGuideDirectory,mCobraGuideVideo,mCobraGuideDetails,mCobraGuideBrowser,mCobraModeFooter};

      int groupW=mCobraModeGroupsExpanded?Math.min(w-dp(220),cobraTvGroupPanelWidth(w)):0;
      int toolbarBottom=Math.max(0,Math.min(h,Math.round((mCobraModeLayout.toolbar[1]+mCobraModeLayout.toolbar[3])*density)));
      int footerY=h;
      if(mCobraModeLayout.footer[3]>0){
        int fy=Math.round(mCobraModeLayout.footer[1]*density);if(fy>toolbarBottom&&fy<h)footerY=fy;
      }
      int contentX=groupW,contentW=Math.max(1,w-contentX),availableH=Math.max(1,footerY-toolbarBottom);
      int gap=dp(10);
      int desiredBand=Math.round(availableH*(groupW>0?.32f:.37f));
      int previewBand=cobraTvClamp(desiredBand,dp(190),Math.max(dp(190),Math.min(dp(340),availableH-dp(260))));
      int videoH=Math.max(dp(150),previewBand-gap*2);
      int videoW=Math.min(Math.round(contentW*(groupW>0?.44f:.46f)),Math.round(videoH*16f/9f));
      videoW=Math.max(Math.min(dp(360),Math.max(1,contentW-gap*3)),videoW);
      videoW=Math.min(videoW,Math.max(1,contentW-gap*3));
      int videoX=contentX+gap,videoY=toolbarBottom+gap;
      int detailsX=videoX+videoW+gap,detailsW=Math.max(1,w-gap-detailsX);
      int browserY=toolbarBottom+previewBand;
      int browserH=Math.max(1,footerY-browserY);

      for(int i=0;i<boxes.length;i++){
        View view=views[i];if(view==null)continue;
        if(i==2){
          if(groupW<=0){if(view.getVisibility()!=View.GONE)view.setVisibility(View.GONE);continue;}
          if(view.getVisibility()!=View.VISIBLE)view.setVisibility(View.VISIBLE);
          cobraTvPositionIfChanged(view,0,toolbarBottom,groupW,Math.max(1,footerY-toolbarBottom));continue;
        }
        if(i==3){
          if(view.getVisibility()!=View.VISIBLE)view.setVisibility(View.VISIBLE);
          cobraTvPositionIfChanged(view,videoX,videoY,videoW,videoH);continue;
        }
        if(i==4){
          if(view.getVisibility()!=View.VISIBLE)view.setVisibility(View.VISIBLE);
          cobraTvPositionIfChanged(view,detailsX,videoY,detailsW,videoH);continue;
        }
        if(i==5){
          if(view.getVisibility()!=View.VISIBLE)view.setVisibility(View.VISIBLE);
          cobraTvPositionIfChanged(view,contentX,browserY,contentW,browserH);continue;
        }
        int[] r=boxes[i];int x=Math.max(0,Math.min(w,Math.round(r[0]*density))),y=Math.max(0,Math.min(h,Math.round(r[1]*density)));
        int rw=Math.max(0,Math.min(w-x,Math.round(r[2]*density))),rh=Math.max(0,Math.min(h-y,Math.round(r[3]*density)));
        if(rw<=0||rh<=0){if(view.getVisibility()!=View.GONE)view.setVisibility(View.GONE);continue;}
        if(view.getVisibility()!=View.VISIBLE)view.setVisibility(View.VISIBLE);cobraTvPositionIfChanged(view,x,y,rw,rh);
      }
    }finally{mCobraTvGuideLayoutBusy=false;}
  }''')

    # Source gates.
    req('COBRA_TV_ADAPTIVE_UI_BUILD="cobra_tv_adaptive_ui_2103231"' in s,'RC11 marker missing')
    req('cobra_tv_toolbar_menu' not in member(s,'cobraBuildModeChrome'),'TV hamburger survived')
    req('cobra_tv_grid_settings' in member(s,'cobraModeBrowserHeader'),'Settings not beside Search')
    req('name+"  ▾"' not in member(s,'cobraModeBrowserHeader'),'Redundant group dropdown survived')
    req('startCobraPreview(mGuidePreviewChannel)' in member(s,'cobraShowGuideShell'),'Mini-player preview engine removed')
    req('mCobraPreviewPlayer=session' in member(s,'closeFullscreenToCobraView'),'Fullscreen -> mini-player handoff removed')
    req('cobraTvShowGroupChooser(true)' in member(s,'onBackPressed'),'RC10 Groups Back hierarchy regressed')
    req('toggleCobraDrawer();return;' in member(s,'onBackPressed'),'RC10 Drawer Back hierarchy regressed')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103230 RC10 parent')
    req(receipt.get('tv_navigation_hierarchy')=='drawer-groups-grid-player' and receipt.get('tv_back_reverses_hierarchy') is True,'Expected locked RC10 navigation hierarchy')
    req(receipt.get('tv_mini_player_preserved') is True and receipt.get('tv_preview_engine_preserved') is True,'Expected RC10 mini-player preservation')
    req(receipt.get('tv_target_abi')=='armeabi-v7a' and receipt.get('mobile_parent_untouched') is True,'Expected isolated ARMv7 TV parent')

    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle):req(p.is_file(),'Missing '+str(p))
    before,after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
      req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_hamburger_removed=True,tv_drawer_back_menu_preserved=True,
      tv_grid_group_dropdown_removed=True,tv_grid_settings_next_to_search=True,
      tv_grid_settings_returns_to_guide=True,tv_mini_player_adaptive_large=True,
      tv_mini_player_preserved=True,tv_preview_engine_preserved=True,
      tv_navigation_hierarchy='drawer-groups-grid-player',tv_back_reverses_hierarchy=True,
      tv_group_counts_cached=True,tv_motion_translation_alpha_only=True,
      tv_multiview_row_focus_visible=True,tv_player_footer_unclipped=True,
      multiview_two_to_one_session_preserved=True,mobile_parent_untouched=True,
      native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit231').mkdir(exist_ok=True)
    Path('audit231/tv-adaptive-ui-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,'marker':'cobra_tv_adaptive_ui_2103231',
      'hamburger_removed':True,'drawer_via_back_and_menu_preserved':True,
      'grid_group_dropdown_removed':True,'settings_next_to_search':True,
      'mini_player_adaptive_large':True,'mini_player_engine_preserved':True,
      'navigation_hierarchy_preserved':True,'multiview_preserved':True,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,
      'mobile_fold_untouched':True,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103231 adaptive TV UI polish applied over exact locked 2103230 RC10')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
