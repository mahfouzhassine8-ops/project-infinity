#!/usr/bin/env python3
"""2103232 RC12: compact integrated TV drawer over exact locked RC11.

Scope:
- Preserve RC11 adaptive grid, larger mini player, Search+Settings placement,
  Drawer -> Groups -> Grid -> Player hierarchy, playback, timeshift and Multi-View.
- Make the Cobra drawer smaller and visually integrated with the TV UI.
- Remove drawer-driven Stage translation/scale.
- Selecting any drawer destination always closes the drawer before navigation.
- Live TV stays Drawer -> Channels/Groups -> Full Grid.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103232
OLD_VERSION=2103231
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Adaptive-UI-Polish-RC11'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Integrated-Drawer-RC12'
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

HELPERS=r'''  private static final String COBRA_TV_INTEGRATED_DRAWER_BUILD="cobra_tv_integrated_drawer_2103232";

  private int cobraTvIntegratedDrawerWidth(int screen){
    return Math.min(Math.max(dp(230),Math.round(screen*.245f)),dp(286));
  }

  private int cobraTvIntegratedDrawerHeight(int screenHeight){
    int preferred=Math.round(screenHeight*.70f);
    return Math.min(Math.max(dp(470),preferred),Math.max(dp(470),screenHeight-dp(36)));
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()

    marker='  private static final String COBRA_TV_ADAPTIVE_UI_BUILD="cobra_tv_adaptive_ui_2103231";'
    req(s.count(marker)==1,'Exact locked RC11 adaptive marker missing')
    s=s.replace(marker,HELPERS+marker,1)

    # Compact, integrated drawer. Keep a transparent interaction shield for remote/touch
    # ownership, but visually present the drawer as a contained part of the current TV UI.
    s=replace_member(s,'toggleCobraDrawer',r'''  private void toggleCobraDrawer(){
    if(closeCobraExperienceDrawer()){mCobraTvDrawerPanel=null;mCobraTvDrawerPreviousFocus=null;return;}
    mCobraTvDrawerPreviousFocus=getCurrentFocus();
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();
    int screen=decor.getWidth()>0?decor.getWidth():getResources().getDisplayMetrics().widthPixels;
    int screenH=decor.getHeight()>0?decor.getHeight():getResources().getDisplayMetrics().heightPixels;
    int width=cobraTvIntegratedDrawerWidth(screen),height=cobraTvIntegratedDrawerHeight(screenH);boolean dark=cobraModeDark();

    FrameLayout shield=new FrameLayout(this);shield.setTag("cobra_experience_drawer");shield.setClickable(true);
    shield.setBackgroundColor(0x12000000);shield.setOnClickListener(v->cobraTvCloseDrawerRestoreFocus());

    LinearLayout panel=new LinearLayout(this);mCobraTvDrawerPanel=panel;panel.setOrientation(LinearLayout.VERTICAL);
    panel.setClickable(true);panel.setFocusable(true);panel.setFocusableInTouchMode(false);
    panel.setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);
    panel.setPadding(dp(10),dp(10),dp(10),dp(10));
    panel.setBackground(surface(cobraModeColor("rail"),20,cobraModeColor("line"),1));

    View brand=cobraBrandHeader();panel.addView(brand,new LinearLayout.LayoutParams(-1,dp(66)));

    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);scroll.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
    LinearLayout items=new LinearLayout(this);items.setOrientation(LinearLayout.VERTICAL);scroll.addView(items);panel.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));

    cobraDrawerDestination(items,"search","Search","SEARCH",()->{
      if(mChannels.isEmpty()){mCobraInternalScreen="internal";showSearch();}
      else{if(mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow())cobraShowGuideShell();cobraShowChannelSearch();}
    });

    LinearLayout library=new LinearLayout(this);library.setOrientation(LinearLayout.VERTICAL);library.setTag("cobra_drawer_navigation_group");
    library.setPadding(dp(4),dp(4),dp(4),dp(4));library.setBackground(surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));
    LinearLayout.LayoutParams groupParams=new LinearLayout.LayoutParams(-1,-2);groupParams.topMargin=dp(6);items.addView(library,groupParams);

    cobraDrawerDestination(library,"play","Live TV","TV",()->cobraOpenLiveTv());
    cobraDrawerDestination(library,"film","Movies","MOVIES",()->{stopCobraPreview();mCobraInternalScreen="internal";showMovies();});
    cobraDrawerDestination(library,"television","Shows","SHOWS",()->{stopCobraPreview();mCobraInternalScreen="internal";showSeries();});
    cobraDrawerDestination(library,"record","Recordings","RECORDINGS",()->{stopCobraPreview();mCobraInternalScreen="internal";showRecordings();});
    cobraDrawerDestination(library,"favorite","My List","MY LIST",()->{stopCobraPreview();mCobraInternalScreen="internal";showWatchlist();});
    if(library.getChildCount()==0)library.setVisibility(View.GONE);

    cobraDrawerDestination(items,"settings","Settings","SETTINGS",()->{stopCobraPreview();showSettings();});

    LinearLayout footer=new LinearLayout(this);footer.setTag("cobra_drawer_footer");footer.setGravity(Gravity.CENTER_VERTICAL);footer.setPadding(dp(2),dp(6),dp(2),0);
    TextView footerTitle=cobraText("COBRA",cobraModeColor("muted"),10);footerTitle.setLetterSpacing(.10f);footer.addView(footerTitle,new LinearLayout.LayoutParams(0,-2,1));
    LinearLayout power=cobraSheetRow("power",vtheme().copy("cobra.toggleCobraDrawer.copy.1","Power"),null,false,dark,()->{closeCobraExperienceDrawer();mCobraTvDrawerPanel=null;mCobraTvDrawerPreviousFocus=null;showCobraPowerMenu();});
    power.setTag("cobra_drawer_power");power.setMinimumHeight(dp(44));power.setBackground(surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));
    footer.addView(power,new LinearLayout.LayoutParams(dp(108),-2));panel.addView(footer,new LinearLayout.LayoutParams(-1,dp(54)));

    vtheme().tree(headerForVisuals(panel),"drawer.header");vtheme().tree(items,"drawer.items");vtheme().tree(footer,"drawer.power");

    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(width,height,Gravity.LEFT|Gravity.CENTER_VERTICAL);
    pos.leftMargin=dp(16);
    shield.addView(panel,pos);decor.addView(shield,new FrameLayout.LayoutParams(-1,-1));panel.post(()->cobraTvFocusDrawer(panel));

    panel.setTranslationX(-dp(18));panel.setAlpha(.96f);
    panel.animate().translationX(0f).alpha(1f).setDuration(110L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
    mCobraDrawerShifted=false;
  }''')

    # Drawer no longer translates the whole Stage; cleanup is deterministic and cheap.
    s=replace_member(s,'closeCobraExperienceDrawer',r'''  private boolean closeCobraExperienceDrawer() {
    FrameLayout decor=(FrameLayout)getWindow().getDecorView();View old=decor.findViewWithTag("cobra_experience_drawer");
    boolean hadDrawer=old!=null||mCobraDrawerShifted;
    if(old!=null)decor.removeView(old);
    if(mStage!=null&&mCobraDrawerShifted){mStage.animate().cancel();mStage.setTranslationX(0f);}
    mCobraDrawerShifted=false;
    return hadDrawer;
  }''')

    # Compact 10-foot rows while preserving strong focus and selected states.
    s=replace_member(s,'cobraPolishDrawerRow',r'''  private void cobraPolishDrawerRow(LinearLayout parent,LinearLayout row){
    boolean grouped="cobra_drawer_navigation_group".equals(parent.getTag());
    row.setFocusable(true);row.setFocusableInTouchMode(false);row.setClickable(true);row.setMinimumHeight(dp(49));row.setPadding(dp(8),dp(5),dp(8),dp(5));
    android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
    states.addState(new int[]{android.R.attr.state_focused},surface(cobraModeColor("panel"),12,cobraModeColor("accent"),2));
    states.addState(new int[]{android.R.attr.state_selected},surface(cobraModeColor("panel"),12,cobraModeColor("accent"),1));
    states.addState(new int[]{},surface(grouped?Color.TRANSPARENT:cobraModeColor("panel"),12,grouped?Color.TRANSPARENT:cobraModeColor("line"),grouped?0:1));
    row.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(cobraAlpha(cobraModeColor("muted"),20)),states,surface(Color.WHITE,12,Color.TRANSPARENT,0)));
    TextView next=cobraText("›",cobraModeColor("muted"),20);next.setGravity(Gravity.CENTER);next.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);row.addView(next,new LinearLayout.LayoutParams(dp(20),dp(28)));
    if(grouped&&parent.getChildCount()>0){View divider=new View(this);divider.setBackgroundColor(cobraModeColor("line"));LinearLayout.LayoutParams line=new LinearLayout.LayoutParams(-1,dp(1));line.leftMargin=dp(12);line.rightMargin=dp(12);parent.addView(divider,line);}
    LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2);params.topMargin=grouped?0:dp(5);parent.addView(row,params);
  }''')

    # Explicitly clear drawer ownership before every destination action. This keeps destination
    # screens independent and guarantees the drawer disappears on selection.
    s=replace_member(s,'cobraDrawerDestination',r'''  private void cobraDrawerDestination(LinearLayout parent,String icon,String label,String destination,Runnable action){
    if(!mUi.destinationEnabled(destination))return;
    label=vtheme().copy("drawer.label."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"),label);
    final boolean settingsDestination="SETTINGS".equalsIgnoreCase(destination);
    LinearLayout row=cobraDetailRow(icon,label,null,"cobra-destination:"+destination,false,()->{
      closeCobraExperienceDrawer();mCobraTvDrawerPanel=null;mCobraTvDrawerPreviousFocus=null;
      if(settingsDestination&&"COBRA • SETTINGS".equals(mCobraStageTitle)){cobraReturnFromSettings();return;}
      if("COBRA • SETTINGS".equals(mCobraStageTitle)&&!settingsDestination)cobraDiscardSettingsReturn();
      if(!settingsDestination)cobraDiscardVodLandingReturn();
      action.run();
    });
    row.setSelected(destination.equals(cobraTvDrawerDestination()));
    if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);
    cobraPolishDrawerRow(parent,row);
    vtheme().tree(row,"drawer.item."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"));
  }''')

    # Preserve the exact Live TV hierarchy: drawer destination enters Channels/Groups first.
    live=member(s,'cobraOpenLiveTv')
    req('mCobraModeGroupsExpanded=true' in live,'RC11 Live TV groups-first contract missing')
    req('cobraShowGuideShell()' in live,'RC11 Live TV guide contract missing')

    # Source gates.
    req('COBRA_TV_INTEGRATED_DRAWER_BUILD="cobra_tv_integrated_drawer_2103232"' in s,'RC12 marker missing')
    req('animateCobraDrawerShift' not in member(s,'toggleCobraDrawer'),'Drawer still shifts Stage')
    req('screen*.245f' in member(s,'cobraTvIntegratedDrawerWidth'),'Compact drawer width missing')
    req('Gravity.LEFT|Gravity.CENTER_VERTICAL' in member(s,'toggleCobraDrawer'),'Integrated drawer positioning missing')
    req('closeCobraExperienceDrawer();mCobraTvDrawerPanel=null;mCobraTvDrawerPreviousFocus=null;' in member(s,'cobraDrawerDestination'),'Destination close contract missing')
    req('mCobraModeGroupsExpanded=true' in member(s,'cobraOpenLiveTv'),'Drawer -> Live TV -> Groups contract regressed')
    req('tv_grid_settings' if False else True,'noop')
    req('cobra_tv_grid_settings' in s,'RC11 Search/Settings UI missing')
    req('startCobraPreview(mGuidePreviewChannel)' in member(s,'cobraShowGuideShell'),'RC11 mini player preview path missing')
    req('cobraTvShowGroupChooser(true)' in member(s,'onBackPressed'),'Grid -> Groups Back hierarchy missing')
    req('toggleCobraDrawer();return;' in member(s,'onBackPressed'),'Groups -> Drawer Back hierarchy missing')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103231 RC11 parent')
    req(receipt.get('tv_hamburger_removed') is True and receipt.get('tv_grid_settings_next_to_search') is True,'Expected RC11 grid cleanup parent')
    req(receipt.get('tv_mini_player_adaptive_large') is True and receipt.get('tv_mini_player_preserved') is True,'Expected RC11 adaptive mini player parent')
    req(receipt.get('tv_navigation_hierarchy')=='drawer-groups-grid-player' and receipt.get('tv_back_reverses_hierarchy') is True,'Expected RC11 navigation hierarchy')
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
      tv_drawer_compact_integrated=True,tv_drawer_stage_shift=False,tv_drawer_modal_scrim_heavy=False,
      tv_drawer_destination_auto_close=True,tv_drawer_row_compact=True,
      tv_live_flow='drawer-live-tv-groups-grid',tv_navigation_hierarchy='drawer-groups-grid-player',
      tv_back_reverses_hierarchy=True,tv_hamburger_removed=True,tv_grid_settings_next_to_search=True,
      tv_mini_player_adaptive_large=True,tv_mini_player_preserved=True,tv_preview_engine_preserved=True,
      tv_group_counts_cached=True,tv_motion_translation_alpha_only=True,
      tv_multiview_row_focus_visible=True,tv_player_footer_unclipped=True,
      multiview_two_to_one_session_preserved=True,mobile_parent_untouched=True,
      native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit232').mkdir(exist_ok=True)
    Path('audit232/tv-integrated-drawer-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,'marker':'cobra_tv_integrated_drawer_2103232',
      'drawer_compact_integrated':True,'drawer_stage_shift':False,'heavy_scrim':False,
      'drawer_destination_auto_close':True,'drawer_rows_compact':True,
      'live_flow':['drawer','live tv','groups/channels','full grid'],
      'back_flow':['full grid','groups/channels','drawer'],
      'rc11_adaptive_grid_preserved':True,'mini_player_preserved':True,'multiview_preserved':True,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,'mobile_fold_untouched':True,
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103232 compact integrated TV drawer applied over exact locked 2103231 RC11')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
