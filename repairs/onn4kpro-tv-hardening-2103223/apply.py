#!/usr/bin/env python3
"""2103223 onn. 4K Pro TV deep hardening pass.

Parent: exact 2103222 TV Player/Multi-View RC5 source.
This is an Android/TV-layer pass only. The locked 2103221 ARMv7 engine and the
regular ARM64 phone/Fold line are not modified.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103223
OLD_VERSION=2103222
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Player-MultiView-RC5'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Hardening-RC6'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v:raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)

def span(text:str,name:str,kind='method'):
    if kind=='ctor':
        pat=re.compile(r'(?m)^\s*'+re.escape(name)+r'\s*\([^;\n]*\)\s*\{')
    else:
        pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    ms=list(pat.finditer(text));req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start();brace=text.find('{',ms[0].start());depth=0;quote=None;esc=line=block=False;i=brace
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

def member(text,name,kind='method'):
    a,b=span(text,name,kind);return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind);return text[:a]+new.rstrip()+text[b:]

HARDENING_HELPERS=r'''  private static final String COBRA_TV_HARDENING_BUILD="cobra_tv_hardening_2103223";
  private boolean mCobraTvGuideLayoutBusy=false;
  private boolean mCobraTvInsetsInstalled=false;
  private long mCobraTvLastProgrammeUi=0L;
  private final Runnable mCobraTvGuideRebuild=()->{
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&mPlayerOverlay==null&&mMultiOverlay==null)
      cobraRenderGuideBrowser();
  };
  private final Runnable mCobraTvGuideDataRefresh=()->{
    cobraRefreshProgrammeLabels();cobraQueueVisibleGuides();
    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();
    if(mCobraPlayerDrawerList!=null&&mCobraPlayerDrawerList.getAdapter() instanceof android.widget.BaseAdapter)
      ((android.widget.BaseAdapter)mCobraPlayerDrawerList.getAdapter()).notifyDataSetChanged();
  };

  private void cobraTvSetText(TextView view,CharSequence value){
    if(view==null)return;CharSequence next=value==null?"":value,current=view.getText();
    if(!android.text.TextUtils.equals(current,next))view.setText(next);
  }

  private void cobraTvScheduleGuideRebuild(long delay){
    mMain.removeCallbacks(mCobraTvGuideRebuild);mMain.postDelayed(mCobraTvGuideRebuild,Math.max(0L,delay));
  }

  private void cobraTvScheduleGuideDataRefresh(){
    mMain.removeCallbacks(mCobraTvGuideDataRefresh);mMain.postDelayed(mCobraTvGuideDataRefresh,180L);
  }

  private void cobraTvPositionIfChanged(View child,int left,int top,int width,int height){
    if(child==null)return;
    FrameLayout.LayoutParams old=child.getLayoutParams() instanceof FrameLayout.LayoutParams?(FrameLayout.LayoutParams)child.getLayoutParams():null;
    int w=Math.max(1,width),h=Math.max(1,height),x=Math.max(0,left),y=Math.max(0,top);
    if(old!=null&&old.width==w&&old.height==h&&old.leftMargin==x&&old.topMargin==y)return;
    FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(w,h);p.leftMargin=x;p.topMargin=y;child.setLayoutParams(p);
  }

  private android.view.ViewGroup cobraTvTransientRoot(){
    if(mCobraActionSheet!=null&&mCobraActionSheet.isAttachedToWindow())return mCobraActionSheet;
    if(mCobraMultiPicker!=null&&mCobraMultiPicker.isAttachedToWindow())return mCobraMultiPicker;
    if(mCobraPlayerDrawer!=null&&mCobraPlayerDrawer.isAttachedToWindow())return mCobraPlayerDrawer;
    return null;
  }

  private android.widget.ListView cobraTvAncestorList(View view){
    android.view.ViewParent p=view==null?null:view.getParent();
    while(p instanceof View){if(p instanceof android.widget.ListView)return (android.widget.ListView)p;p=p.getParent();}
    return null;
  }

  private View cobraTvDirectListChild(android.widget.ListView list,View view){
    View child=view;
    while(child!=null&&child.getParent()!=list){
      android.view.ViewParent p=child.getParent();child=p instanceof View?(View)p:null;
    }
    return child;
  }

  private void cobraTvReveal(View view){
    if(view==null)return;android.graphics.Rect r=new android.graphics.Rect(0,0,view.getWidth(),view.getHeight());
    view.requestRectangleOnScreen(r,false);
  }

  private boolean cobraTvMoveTransientFocus(int key){
    android.view.ViewGroup root=cobraTvTransientRoot();if(root==null)return false;
    View current=getCurrentFocus();
    if(current!=null&&cobraTvViewInside(root,current)&&(key==KeyEvent.KEYCODE_DPAD_UP||key==KeyEvent.KEYCODE_DPAD_DOWN)){
      android.widget.ListView list=cobraTvAncestorList(current);
      if(list!=null&&list.getAdapter()!=null&&list.getAdapter().getCount()>0){
        View direct=cobraTvDirectListChild(list,current);int child=direct==null?-1:list.indexOfChild(direct);
        if(child>=0){
          int pos=list.getFirstVisiblePosition()+child,delta=key==KeyEvent.KEYCODE_DPAD_DOWN?1:-1;
          int next=Math.max(0,Math.min(list.getAdapter().getCount()-1,pos+delta));
          if(next!=pos){list.setSelection(next);final int wanted=next;list.post(()->{
            int ci=wanted-list.getFirstVisiblePosition();View row=ci>=0&&ci<list.getChildCount()?list.getChildAt(ci):null;
            if(row instanceof android.view.ViewGroup)cobraTvFocusFirst((android.view.ViewGroup)row);else if(row!=null)row.requestFocus();else list.requestFocus();
          });return true;}
        }
      }
    }
    java.util.ArrayList<View> candidates=root.getFocusables(View.FOCUS_FORWARD);
    if(candidates.isEmpty())return true;
    if(current==null||!cobraTvViewInside(root,current)){
      for(View v:candidates)if(v!=root&&v.isShown()&&v.isEnabled()&&v.isFocusable()&&!(v instanceof android.widget.ScrollView)&&!(v instanceof android.widget.ListView)){v.requestFocus();cobraTvReveal(v);return true;}
      return true;
    }
    int[] here=new int[2];current.getLocationOnScreen(here);int cx=here[0]+current.getWidth()/2,cy=here[1]+current.getHeight()/2;
    View best=null;long score=Long.MAX_VALUE;
    for(View v:candidates){
      if(v==current||v==root||!v.isShown()||!v.isEnabled()||!v.isFocusable()||v instanceof android.widget.ScrollView||v instanceof android.widget.ListView)continue;
      int[] there=new int[2];v.getLocationOnScreen(there);int x=there[0]+v.getWidth()/2,y=there[1]+v.getHeight()/2,primary,secondary;
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){if(y<=cy+2)continue;primary=y-cy;secondary=Math.abs(x-cx);}
      else if(key==KeyEvent.KEYCODE_DPAD_UP){if(y>=cy-2)continue;primary=cy-y;secondary=Math.abs(x-cx);}
      else if(key==KeyEvent.KEYCODE_DPAD_RIGHT){if(x<=cx+2)continue;secondary=Math.abs(y-cy);if(secondary>Math.max(current.getHeight(),v.getHeight())*2)continue;primary=x-cx;}
      else if(key==KeyEvent.KEYCODE_DPAD_LEFT){if(x>=cx-2)continue;secondary=Math.abs(y-cy);if(secondary>Math.max(current.getHeight(),v.getHeight())*2)continue;primary=cx-x;}
      else return false;
      long s=(long)primary*10000L+secondary;if(s<score){score=s;best=v;}
    }
    if(best!=null){best.requestFocus();cobraTvReveal(best);return true;}
    return true; // never let an open TV overlay leak focus to the surface behind it
  }

  private boolean cobraTvCloseTransient(){
    if(mCobraActionSheet!=null){closeCobraActionSheet();return true;}
    if(mCobraMultiPicker!=null){closeCobraMultiPicker(false);if(mPlayerOverlay!=null)mMain.post(this::cobraTvFocusPlayerPrimary);return true;}
    if(mCobraPlayerDrawer!=null){
      if(mCobraDrawerFilter!=null&&mCobraDrawerFilter.startsWith("GROUP:")){cobraRenderPlayerDrawer("CATEGORIES");return true;}
      closeCobraPlayerDrawer();if(mPlayerOverlay!=null)mMain.post(this::cobraTvFocusPlayerPrimary);return true;
    }
    return false;
  }

  private boolean cobraTvHandleTransientKey(KeyEvent event){
    android.view.ViewGroup root=cobraTvTransientRoot();if(root==null||event.getAction()!=KeyEvent.ACTION_DOWN)return false;
    int key=event.getKeyCode();
    if(key==KeyEvent.KEYCODE_BACK)return cobraTvCloseTransient();
    if(key==KeyEvent.KEYCODE_DPAD_UP||key==KeyEvent.KEYCODE_DPAD_DOWN||key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT)
      return cobraTvMoveTransientFocus(key);
    return false;
  }

  private int cobraTvGuideListPosition(View focus){
    if(mCobraGuideList==null||focus==null)return -1;View child=focus;
    while(child!=null&&child.getParent()!=mCobraGuideList){android.view.ViewParent p=child.getParent();child=p instanceof View?(View)p:null;}
    return child==null?-1:mCobraGuideList.getFirstVisiblePosition()+mCobraGuideList.indexOfChild(child);
  }

  private void cobraTvFocusGuideBody(){
    if(mCobraGuideList==null)return;
    View preferred=mGuidePreviewChannel==null?null:mCobraGuideList.findViewWithTag("cobra-channel:"+mGuidePreviewChannel.id);
    if(preferred!=null&&preferred.isShown()){preferred.requestFocus();return;}
    if(mCobraGuideList.getChildCount()>0){View row=mCobraGuideList.getChildAt(0);if(row instanceof android.view.ViewGroup)cobraTvFocusFirst((android.view.ViewGroup)row);else row.requestFocus();}
  }

  private boolean cobraTvHandleGuideKey(KeyEvent event){
    if(event.getAction()!=KeyEvent.ACTION_DOWN||mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow()||mPlayerOverlay!=null||mMultiOverlay!=null||cobraTvTransientRoot()!=null)return false;
    int key=event.getKeyCode();View focus=getCurrentFocus();Object raw=focus==null?null:focus.getTag();String tag=raw instanceof String?(String)raw:"";
    if(key==KeyEvent.KEYCODE_MENU){toggleCobraDrawer();return true;}
    if((tag.startsWith("cobra-channel:")||tag.startsWith("cobra-program:")||tag.startsWith("cobra-gap:"))&&key==KeyEvent.KEYCODE_DPAD_UP&&cobraTvGuideListPosition(focus)==0){
      View group=mCobraGuideBrowser==null?null:mCobraGuideBrowser.findViewWithTag("cobra_tv_grid_group");if(group!=null){group.requestFocus();return true;}
    }
    if(tag.startsWith("cobra_tv_grid_")){
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){cobraTvFocusGuideBody();return true;}
      if(key==KeyEvent.KEYCODE_DPAD_UP){View menu=mCobraModeToolbar==null?null:mCobraModeToolbar.findViewWithTag("cobra_tv_toolbar_menu");if(menu!=null){menu.requestFocus();return true;}}
    }
    if(("cobra_tv_toolbar_menu".equals(tag)||"cobra_mode_visuals".equals(tag))&&key==KeyEvent.KEYCODE_DPAD_DOWN){
      View group=mCobraGuideBrowser==null?null:mCobraGuideBrowser.findViewWithTag("cobra_tv_grid_group");if(group!=null){group.requestFocus();return true;}
    }
    return false;
  }

  private ArrayList<Channel> cobraTvReadLibraryCache(ArrayList<LiveSource> enabled){
    ArrayList<Channel> restored=new ArrayList<>();File file=cobraLibraryCacheFile();
    if(!file.isFile()||file.length()<=0||file.length()>32L*1024L*1024L)return restored;
    try{
      JSONObject root=new JSONObject(readText(new java.io.FileInputStream(file)));
      if(root.optInt("schema",0)!=1||!cobraSourceFingerprint(enabled).equals(root.optString("source_fingerprint","")))return restored;
      JSONArray rows=root.optJSONArray("channels");if(rows==null||rows.length()==0||rows.length()>MAX_CHANNELS)return restored;
      for(int i=0;i<rows.length();i++){
        JSONObject row=rows.optJSONObject(i);if(row==null)continue;String primary=row.optString("primary_url","");if(primary.isEmpty())continue;
        HashMap<String,String> headers=new HashMap<>();JSONObject encoded=row.optJSONObject("headers");
        if(encoded!=null){JSONArray names=encoded.names();if(names!=null)for(int h=0;h<names.length();h++){String name=names.optString(h,"");if(!name.isEmpty())headers.put(name,encoded.optString(name,""));}}
        restored.add(new Channel(row.optString("id",""),row.optString("name","Live channel"),row.optString("group","Other"),row.optString("epg_id",""),row.optString("icon",""),primary,row.optString("fallback_url",""),headers));
      }
    }catch(Exception ignored){restored.clear();}
    return restored;
  }

  private void cobraTvInstallWarmLibrary(ArrayList<LiveSource> enabled,ArrayList<Channel> restored){
    if(restored==null||restored.isEmpty()||!isCobraAsyncAlive())return;
    mChannels.clear();mChannels.addAll(restored);String active=mPrefs.getString(ACTIVE_SOURCE,"");mActiveSource=null;
    for(LiveSource source:enabled)if(source.id.equals(active)){mActiveSource=source;break;}
    if(mActiveSource==null&&!enabled.isEmpty())mActiveSource=enabled.get(0);
    status(restored.size()+" channels • saved library • refreshing quietly");
    if(!cobraTrySmartReturn())showCobraPrimaryView();
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    marker='  private static final String COBRA_TV_PLAYER_MULTIVIEW_BUILD="cobra_tv_player_multiview_2103222";'
    req(s.count(marker)==1,'2103222 TV marker missing')
    s=s.replace(marker,HARDENING_HELPERS+marker,1)

    # 2103222 accidentally stopped maintaining these dimensions. Its guide-shell onLayout
    # consequently rebuilt the entire 20k-channel browser on every layout pass.
    shell=member(s,'cobraShowGuideShell')
    req(shell.count('cobraLayoutGuide();cobraRenderGuideBrowser();')==2,'guide shell render anchor drift')
    shell=shell.replace('cobraLayoutGuide();cobraRenderGuideBrowser();','cobraLayoutGuide();if(mCobraGuideBrowser!=null&&mCobraGuideBrowser.getChildCount()==0)cobraRenderGuideBrowser();',1)
    s=replace_member(s,'cobraShowGuideShell',shell)

    s=replace_member(s,'cobraLayoutGuide',r'''  private void cobraLayoutGuide(){
    if(mCobraGuideShell==null||mCobraTvGuideLayoutBusy)return;int w=mCobraGuideShell.getWidth(),h=mCobraGuideShell.getHeight();if(w<=0||h<=0)return;
    mCobraTvGuideLayoutBusy=true;
    try{
      mCobraLastGuideWidth=w;mCobraLastGuideHeight=h;float density=Math.max(.01f,getResources().getDisplayMetrics().density);
      mCobraModeLayout=CobraModeLayout.solve("grid",Math.max(1,Math.round(w/density)),Math.max(1,Math.round(h/density)),getResources().getConfiguration().fontScale,false);
      int[][] boxes={mCobraModeLayout.toolbar,mCobraModeLayout.rail,mCobraModeLayout.directory,mCobraModeLayout.video,mCobraModeLayout.details,mCobraModeLayout.browser,mCobraModeLayout.footer};
      View[] views={mCobraModeToolbar,mCobraModeRail,mCobraGuideDirectory,mCobraGuideVideo,mCobraGuideDetails,mCobraGuideBrowser,mCobraModeFooter};
      for(int i=0;i<boxes.length;i++){
        int[] r=boxes[i];int x=Math.max(0,Math.min(w,Math.round(r[0]*density))),y=Math.max(0,Math.min(h,Math.round(r[1]*density)));
        int rw=Math.max(0,Math.min(w-x,Math.round(r[2]*density))),rh=Math.max(0,Math.min(h-y,Math.round(r[3]*density)));
        if(views[i]==null)continue;if(rw<=0||rh<=0){if(views[i].getVisibility()!=View.GONE)views[i].setVisibility(View.GONE);continue;}
        if(views[i].getVisibility()!=View.VISIBLE)views[i].setVisibility(View.VISIBLE);cobraTvPositionIfChanged(views[i],x,y,rw,rh);
      }
    }finally{mCobraTvGuideLayoutBusy=false;}
  }''')

    # A newly built root needs its own one-time inset listener; player returns no longer rebuild it.
    build=member(s,'buildShell')
    build=once(build,'  private void buildShell() {\n','  private void buildShell() {\n    mCobraTvInsetsInstalled=false;\n','TV root inset reset')
    s=replace_member(s,'buildShell',build)

    # TV system bars are static. Reassert immersive flags but never trigger a fresh layout tree.
    s=replace_member(s,'cobraApplySystemBarsForSurface',r'''  private void cobraApplySystemBarsForSurface(){
    Window window=getWindow();View decor=window.getDecorView();
    window.clearFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    int flags=View.SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
        |View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY;
    if(decor.getSystemUiVisibility()!=flags)decor.setSystemUiVisibility(flags);
    if(window.getStatusBarColor()!=Color.TRANSPARENT)window.setStatusBarColor(Color.TRANSPARENT);
    if(window.getNavigationBarColor()!=Color.TRANSPARENT)window.setNavigationBarColor(Color.TRANSPARENT);
    if(Build.VERSION.SDK_INT>=30&&window.getInsetsController()!=null){
      android.view.WindowInsetsController controller=window.getInsetsController();
      controller.setSystemBarsBehavior(android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
      controller.hide(android.view.WindowInsets.Type.statusBars()|android.view.WindowInsets.Type.navigationBars());
    }
    if(mRoot!=null&&!mCobraTvInsetsInstalled){
      mCobraTvInsetsInstalled=true;mRoot.setOnApplyWindowInsetsListener((v,insets)->{if(v.getPaddingLeft()!=0||v.getPaddingTop()!=0||v.getPaddingRight()!=0||v.getPaddingBottom()!=0)v.setPadding(0,0,0,0);return insets;});
      if(mRoot.getPaddingLeft()!=0||mRoot.getPaddingTop()!=0||mRoot.getPaddingRight()!=0||mRoot.getPaddingBottom()!=0)mRoot.setPadding(0,0,0,0);
    }
  }''')

    # Do not touch Android display-mode IDs on this fixed 60-Hz TV target. This avoids HDMI
    # mode handshakes / black frames when player surfaces open and close.
    s=replace_member(s,'cobraApplyDisplayPerformance',r'''  private void cobraApplyDisplayPerformance(String reason){
    android.view.Display display=cobraCurrentDisplay();mCobraRequestedHz=0f;mCobraMaxHz=0f;
    if(display!=null&&Build.VERSION.SDK_INT>=23){android.view.Display.Mode mode=display.getMode();if(mode!=null){mCobraActiveHz=mode.getRefreshRate();mCobraMaxHz=mCobraActiveHz;}}
    mCobraRefreshStatus="TV SYSTEM";cobraUpdatePerformanceOverlay();
  }''')

    # Decorative motion must never delay remote interaction on this ARMv7 target.
    s=replace_member(s,'cobraAnimateChildrenIn',r'''  private void cobraAnimateChildrenIn(LinearLayout group){
    if(group==null)return;for(int i=0;i<group.getChildCount();i++){View child=group.getChildAt(i);if(child!=null){cobraResetMotion(child);child.setAlpha(1f);child.setTranslationX(0f);child.setTranslationY(0f);child.setScaleX(1f);child.setScaleY(1f);}}
  }''')
    s=replace_member(s,'cobraAnimatePanelIn',r'''  private void cobraAnimatePanelIn(View view,boolean horizontal){
    if(view==null)return;cobraResetMotion(view);view.setAlpha(1f);view.setTranslationX(0f);view.setTranslationY(0f);view.setScaleX(1f);view.setScaleY(1f);
  }''')

    # Focus inspection is coalesced rather than recomputing details for every fast D-pad repeat.
    s=replace_member(s,'cobraInspectProgramme',r'''  private void cobraInspectProgramme(Channel channel,GuideProgram program){
    if(channel==null)return;
    boolean sameChannel=mCobraInspectedChannel!=null&&channel.id.equals(mCobraInspectedChannel.id);
    boolean sameProgram=(program==null&&mCobraInspectedProgram==null)||(program!=null&&mCobraInspectedProgram!=null&&program.start==mCobraInspectedProgram.start);
    if(sameChannel&&sameProgram)return;
    mCobraTvPendingInspectChannel=channel;mCobraTvPendingInspectProgram=program;mMain.removeCallbacks(mCobraTvApplyProgrammeFocus);mMain.postDelayed(mCobraTvApplyProgrammeFocus,85L);
  }''')

    # Only mutate labels when values actually changed; avoid a layout cascade every ticker.
    s=replace_member(s,'cobraRefreshModeDetails',r'''  private void cobraRefreshModeDetails(){
    if(mCobraModeEyebrow==null||mCobraModeLayout==null)return;
    Channel channel="grid".equals(mCobraGuideStyle)&&mCobraInspectedChannel!=null?mCobraInspectedChannel:mGuidePreviewChannel;
    GuideProgram now=channel==mCobraInspectedChannel&&mCobraInspectedProgram!=null?mCobraInspectedProgram:cobraCurrentProgram(channel),next=cobraNextProgram(channel);
    boolean playing=channel!=null&&mGuidePreviewChannel!=null&&channel.id.equals(mGuidePreviewChannel.id);
    cobraTvSetText(mCobraModeEyebrow,channel==null?"LIVE TELEVISION":(playing?"NOW PLAYING  /  ":"BROWSING  /  ")+channel.name);
    cobraTvSetText(mCobraGuideNowLabel,now==null?channel==null?"Choose a channel":channel.name:now.title);
    cobraTvSetText(mCobraGuideNextLabel,now==null?cobraGuideStatus(channel):formatTime(now.start)+" – "+formatTime(now.stop)+(next==null?"":"\nNext  "+next.title));
    cobraTvSetText(mCobraModeDescription,now==null?"":now.description);
    mCobraGuideDetails.setContentDescription(channel==null?"Programme information":channel.name+", "+(now==null?cobraGuideStatus(channel):now.title)+", open programme details");
    boolean progress=now!=null&&now.start<=System.currentTimeMillis()&&now.stop>System.currentTimeMillis()&&mCobraModeLayout.details[3]>=96;
    if(mCobraGuideProgress.getVisibility()!=(progress?View.VISIBLE:View.GONE))mCobraGuideProgress.setVisibility(progress?View.VISIBLE:View.GONE);
    if(now!=null){int value=Math.round(CobraGuideMath.progress(now.start,now.stop,System.currentTimeMillis())*1000);if(mCobraGuideProgress.getProgress()!=value)mCobraGuideProgress.setProgress(value);}
    if(mCobraModeSub!=null)cobraTvSetText(mCobraModeSub,"COBRA LIVE  ·  "+String.format(Locale.getDefault(),"%,d",mChannels.size())+" CHANNELS");
  }''')

    s=replace_member(s,'cobraRefreshProgrammeLabels',r'''  private void cobraRefreshProgrammeLabels(){
    if(!isCobraAsyncAlive())return;long nowMs=System.currentTimeMillis();mCobraTvLastProgrammeUi=nowMs;cobraRefreshQuickPeek();
    Channel channel=mGuidePreviewChannel;GuideProgram now=cobraCurrentProgram(channel),next=cobraNextProgram(channel);
    cobraTvSetText(mCobraGuideNowLabel,channel==null?"Select a channel":channel.name+(now==null?"":"  ·  "+now.title));
    cobraTvSetText(mCobraGuideNextLabel,now==null?cobraGuideStatus(channel):(formatTime(now.start)+" – "+formatTime(now.stop)+"  ·  "+Math.max(0,(now.stop-nowMs+59999)/60000)+" min left\n"+(next==null?"Upcoming schedule unavailable":"Next  "+next.title)));
    if(mCobraGuideProgress!=null){int visibility=now==null?View.INVISIBLE:View.VISIBLE;if(mCobraGuideProgress.getVisibility()!=visibility)mCobraGuideProgress.setVisibility(visibility);if(now!=null){int p=Math.round(CobraGuideMath.progress(now.start,now.stop,nowMs)*1000);if(mCobraGuideProgress.getProgress()!=p)mCobraGuideProgress.setProgress(p);}}
    channel=mPlaying;now=cobraCurrentProgram(channel);next=cobraNextProgram(channel);
    cobraTvSetText(mCobraPlayerProgram,now==null?channel==null?"":channel.name:now.title);
    cobraTvSetText(mCobraPlayerSchedule,now==null?cobraGuideStatus(channel):formatTime(now.start)+" – "+formatTime(now.stop)+"   ·   "+Math.max(0,(now.stop-nowMs+59999)/60000)+" min left");
    cobraTvSetText(mCobraPlayerUpcoming,next==null?"":"Next  "+next.title);
    if(mCobraPlayerProgramProgress!=null&&!cobraTimeshiftTimelineAvailable()){int visibility=now==null?View.INVISIBLE:View.VISIBLE;if(mCobraPlayerProgramProgress.getVisibility()!=visibility)mCobraPlayerProgramProgress.setVisibility(visibility);if(now!=null){int p=Math.round(CobraGuideMath.progress(now.start,now.stop,nowMs)*1000);if(mCobraPlayerProgramProgress.getProgress()!=p)mCobraPlayerProgramProgress.setProgress(p);}}
    if(mPlayerOverlay!=null){View play=mPlayerOverlay.findViewWithTag("cobra_player_play_pause");if(play instanceof CobraIconButton)((CobraIconButton)play).icon(mPlayer!=null&&mPlayer.getPlayWhenReady()?"pause":"play");}
    cobraRefreshModeDetails();
  }''')

    # EPGs from multiple enabled sources arrive in bursts. Merge data immediately but coalesce
    # expensive visible-list invalidation into one UI pass.
    epg=member(s,'cobraInstallEpg')
    epg=once(epg,'    cobraRefreshProgrammeLabels();cobraQueueVisibleGuides();\n    if(mCobraGuideAdapter!=null)mCobraGuideAdapter.notifyDataSetChanged();\n    if(mCobraPlayerDrawerList!=null && mCobraPlayerDrawerList.getAdapter() instanceof android.widget.BaseAdapter)\n      ((android.widget.BaseAdapter)mCobraPlayerDrawerList.getAdapter()).notifyDataSetChanged();',
             '    cobraTvScheduleGuideDataRefresh();','EPG redraw coalescing')
    s=replace_member(s,'cobraInstallEpg',epg)

    # Main startup fix: decode the potentially 20k+ channel JSON cache on the IO executor,
    # publish the saved guide as soon as it is decoded, then refresh providers in the same worker.
    s=replace_member(s,'loadAllEnabledSources',r'''  private void loadAllEnabledSources(boolean showBusy){
    if(mSources.isEmpty()){showWelcome();return;}
    final ArrayList<LiveSource> enabled=new ArrayList<>();for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id))enabled.add(source);
    if(enabled.isEmpty()){status("No sources enabled");showSources();return;}
    final boolean alreadyWarm=!mChannels.isEmpty();final ArrayList<Channel> previous=new ArrayList<>(mChannels);
    if(showBusy&&!alreadyWarm){
      clearStage("COBRA • LIVE TV");status("Opening saved TV library…");
      mStage.addView(text("LOADING TV GUIDE…",cobraThemeColor("muted",mTheme.muted),16,Gravity.CENTER),new LinearLayout.LayoutParams(-1,0,1));
    }else if(alreadyWarm)status(mChannels.size()+" channels • refreshing in background");
    cobraSmartLoading();
    if(!submitCobraIo(()->{
      final ArrayList<Channel> cached=alreadyWarm?new ArrayList<>(previous):cobraTvReadLibraryCache(enabled);
      final boolean cacheReady=!alreadyWarm&&!cached.isEmpty();
      if(cacheReady)publishCobraUi(()->{if(isCobraAsyncAlive()&&mChannels.isEmpty())cobraTvInstallWarmLibrary(enabled,cached);});
      final ArrayList<Channel> fallback=!cached.isEmpty()?cached:previous;
      ArrayList<Channel> merged=new ArrayList<>();ArrayList<String> failures=new ArrayList<>();
      for(LiveSource source:enabled){
        try{LoadResult result=loadSource(source,false);merged.addAll(result.channels);}
        catch(LiveException error){failures.add(source.name+": "+error.userMessage);for(Channel old:fallback)if(old.id!=null&&old.id.startsWith(source.id+":"))merged.add(old);}
      }
      final ArrayList<Channel> resolved=merged;
      final boolean changed=!resolved.isEmpty()&&!cobraLibrariesEqual(fallback,resolved);
      publishCobraUi(()->{
        if(!isCobraAsyncAlive())return;
        if(resolved.isEmpty()){
          if(!mChannels.isEmpty()){status(mChannels.size()+" channels • using saved library • refresh unavailable");return;}
          clearStage("COBRA • SOURCE ERROR");status("No enabled source could load");
          String message=failures.isEmpty()?"No playable channels were returned.":android.text.TextUtils.join("\n\n",failures);
          mStage.addView(text(message,cobraThemeColor("text",mTheme.text),15,Gravity.CENTER),new LinearLayout.LayoutParams(-1,0,1));return;
        }
        boolean hadVisible=!mChannels.isEmpty();mChannels.clear();mChannels.addAll(resolved);
        if(mActiveSource==null||!mFeatures.sourceEnabled(mActiveSource.id))mActiveSource=enabled.get(0);
        if(!alreadyWarm&&!cacheReady){mCategory="ALL";mSearch="";}
        String suffix=failures.isEmpty()?"ready":failures.size()+" source refresh unavailable";
        status(resolved.size()+" channels • "+enabled.size()+" enabled source"+(enabled.size()==1?"":"s")+" • "+suffix);
        if(changed&&hadVisible)cobraRefreshChannelMetadata();
        if(!hadVisible){if(!cobraTrySmartReturn())showCobraPrimaryView();}
        else if(changed)cobraTvScheduleGuideRebuild(220L);
        final ArrayList<Channel> persist=new ArrayList<>(resolved);submitCobraIo(()->saveCobraLibraryCache(enabled,persist));
        for(LiveSource source:enabled)loadGuideAsync(source);
        mFeatures.writeHealth("live",mActiveSource==null?"":mActiveSource.id,"","ready",failures.isEmpty()?"":failures.get(0),0,0,-1,"idle","loading");
      });
    })&&!alreadyWarm)toast("Cobra is closing; source refresh was skipped");
  }''')

    # Keep compatibility for any legacy caller but move all actual cache parsing to the pure IO helper.
    s=replace_member(s,'restoreCobraLibraryCache',r'''  private boolean restoreCobraLibraryCache(ArrayList<LiveSource> enabled){
    ArrayList<Channel> restored=cobraTvReadLibraryCache(enabled);if(restored.isEmpty())return false;cobraTvInstallWarmLibrary(enabled,restored);return true;
  }''')

    # Metadata refresh no longer destroys/recreates the guide immediately.
    s=replace_member(s,'cobraRefreshChannelMetadata',r'''  private void cobraRefreshChannelMetadata(){
    Channel oldPreview=mGuidePreviewChannel,oldPlaying=mPlaying,oldInspect=mCobraInspectedChannel;
    mGuidePreviewChannel=oldPreview==null?null:findChannel(oldPreview.id);mPlaying=oldPlaying==null?null:findChannel(oldPlaying.id);
    Channel inspect=oldInspect==null?null:findChannel(oldInspect.id);if(inspect!=null&&oldInspect!=null&&!java.util.Objects.equals(inspect.epgId,oldInspect.epgId))mCobraInspectedProgram=null;mCobraInspectedChannel=inspect;
    mCobraResolvedEpg.clear();cobraRefreshProgrammeLabels();
    if(mCobraPlayerDrawerList!=null)cobraRenderPlayerDrawer(mCobraDrawerFilter);
  }''')

    # Avoid rebuilding the entire shell when a player closes. TV surfaces are persistent.
    s=replace_member(s,'rebuildCobraShellIfNeeded',r'''  private void rebuildCobraShellIfNeeded(){
    if(!mRebuildShellAfterPlayer||mReflowingMulti||isFinishing())return;mRebuildShellAfterPlayer=false;mTheme=Theme.load(this);mUi=UiContract.load(this);
    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraRestyleGuide();cobraLayoutGuide();cobraTvScheduleGuideRebuild(0L);}
    else if(mRoot!=null)mRoot.invalidate();
  }''')

    # TV sheets open fully drawn and immediately focus the first actual action.
    sheet=member(s,'cobraOpenSheet')
    sheet=once(sheet,'    CobraIconButton close=cobraIcon("close","Close menu",dark,v->closeCobraActionSheet());header.addView(close,new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.9",48)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.10",48))));',
                     '    CobraIconButton close=cobraIcon("close","Close menu",dark,v->closeCobraActionSheet());close.setTag("cobra_tv_sheet_close");header.addView(close,new LinearLayout.LayoutParams(dp(52),dp(52)));','sheet close tag')
    sheet=once(sheet,'    panel.setAlpha(0f);panel.setTranslationY(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.18",12)));panel.setScaleX(.985f);panel.setScaleY(.985f);\n    panel.animate().alpha(1f).translationY(0f).scaleX(1f).scaleY(1f).setDuration(vtheme().motion("cobra.cobraOpenSheet.numbers.1",190)).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();',
                     '    panel.setAlpha(1f);panel.setTranslationY(0f);panel.setScaleX(1f);panel.setScaleY(1f);','sheet animation removal')
    sheet=once(sheet,'    close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;',
                     '    items.post(()->cobraTvFocusFirst(items));vtheme().tree(panel,"sheet."+kind);return items;','sheet action focus')
    s=replace_member(s,'cobraOpenSheet',sheet)

    # Multi-View / picker: the list, not the phone-style search field, owns normal opening focus.
    picker=member(s,'showCobraMultiPicker')
    picker=picker.replace('list.setFastScrollEnabled(true);','list.setFastScrollEnabled(false);')
    picker=once(picker,'parent.addView(panel,new FrameLayout.LayoutParams(1,1));if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);cobraLayoutPlayerPanels();renderCobraMultiPicker("RECENT");',
                  'parent.addView(panel,new FrameLayout.LayoutParams(1,1));if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);cobraLayoutPlayerPanels();renderCobraMultiPicker("RECENT");list.post(()->{if(list.getChildCount()>0){View row=list.getChildAt(0);if(row!=null)row.requestFocus();}else list.requestFocus();});',
                  'Multi-View initial remote focus')
    s=replace_member(s,'showCobraMultiPicker',picker)

    # Main TV Grid gets explicit routes between toolbar -> group/search row -> EPG.
    header=member(s,'cobraModeBrowserHeader')
    header=header.replace('Button group=cobraTextButton(name+"  ▾",cobraModeDark(),()->cobraToggleModeGroups());',
                          'Button group=cobraTextButton(name+"  ▾",cobraModeDark(),()->cobraToggleModeGroups());group.setTag("cobra_tv_grid_group");')
    header=header.replace('row.addView(cobraIcon("source","Choose playlist",cobraModeDark(),v->cobraOpenTvDirectory(true)),',
                          'CobraIconButton source=cobraIcon("source","Choose playlist",cobraModeDark(),v->cobraOpenTvDirectory(true));source.setTag("cobra_tv_grid_source");row.addView(source,')
    header=header.replace('row.addView(cobraIcon("search","Search channels",cobraModeDark(),v->cobraShowChannelSearch()),',
                          'CobraIconButton search=cobraIcon("search","Search channels",cobraModeDark(),v->cobraShowChannelSearch());search.setTag("cobra_tv_grid_search");row.addView(search,')
    s=replace_member(s,'cobraModeBrowserHeader',header)

    menu='mCobraModeToolbar.addView(cobraIcon("guide","Open Cobra navigation",dark,v->toggleCobraDrawer()),new LinearLayout.LayoutParams(dp(vtheme().dimension("cobra.cobraBuildModeChrome.dimensions.1",48)),-1));'
    req(menu in s,'toolbar menu anchor missing')
    s=s.replace(menu,'CobraIconButton tvMenu=cobraIcon("guide","Open Cobra navigation",dark,v->toggleCobraDrawer());tvMenu.setTag("cobra_tv_toolbar_menu");mCobraModeToolbar.addView(tvMenu,new LinearLayout.LayoutParams(dp(52),-1));',1)

    # Dispatch owned overlays before player/default Android focus can escape behind them.
    dispatch=member(s,'dispatchKeyEvent')
    dispatch=once(dispatch,'    if(cobraTvHandleDirectoryKey(event))return true;\n    if(cobraTvHandlePlayerKey(event))return true;',
                  '    if(cobraTvHandleDirectoryKey(event))return true;\n    if(cobraTvHandleTransientKey(event))return true;\n    if(cobraTvHandleGuideKey(event))return true;\n    if(cobraTvHandlePlayerKey(event))return true;',
                  'TV transient/guide key ownership')
    s=replace_member(s,'dispatchKeyEvent',dispatch)

    # The ticker already uses a one-second cadence after its first pass; do not front-load a heavy
    # programme/layout refresh 200 ms after every surface transition.
    s=s.replace('mMain.postDelayed(mCobraPresentationTick,200L)','mMain.postDelayed(mCobraPresentationTick,750L)')

    # Source gates.
    for token in (
      'COBRA_TV_HARDENING_BUILD="cobra_tv_hardening_2103223"',
      'mCobraLastGuideWidth=w;mCobraLastGuideHeight=h',
      'cobraTvReadLibraryCache(enabled)',
      'cobraTvHandleTransientKey(event)',
      'cobraTvHandleGuideKey(event)',
      'mCobraRefreshStatus="TV SYSTEM"',
      'cobraTvScheduleGuideDataRefresh();',
      'list.setFastScrollEnabled(false)',
      'cobra_tv_grid_group',
      'cobra_tv_toolbar_menu',
    ):req(token in s,'2103223 source gate missing: '+token)
    req('if (!warm) warm = restoreCobraLibraryCache(enabled);' not in s,'Synchronous startup cache restore remains')
    req(member(s,'cobraShowGuideShell').count('cobraLayoutGuide();cobraRenderGuideBrowser();')==1,'Guide onLayout redraw loop remains')
    req('decor.requestLayout()' not in member(s,'cobraApplySystemBarsForSurface'),'System-bar layout churn remains')
    req('preferredDisplayModeId' not in member(s,'cobraApplyDisplayPerformance'),'TV display-mode handshake remains')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact 2103222 TV candidate source')
    req(receipt.get('tv_player_focus_graph') is True and receipt.get('multiview_fullscreen_reversible') is True,'2103222 parent contract missing')
    req(receipt.get('tv_target_abi')=='armeabi-v7a' and receipt.get('mobile_parent_untouched') is True,'TV isolation receipt mismatch')
    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    before,after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode');g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)
    for rel in (ACT,SOURCE+'build.gradle.in'):
      req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_hardening=True,tv_guide_layout_rebuild_loop_fixed=True,tv_cache_restore_off_main=True,
      tv_display_mode_switching_disabled=True,tv_system_bar_layout_churn_fixed=True,
      tv_transient_focus_owned=True,tv_grid_focus_graph=True,tv_epg_refresh_coalesced=True,
      tv_decorative_motion_minimized=True,tv_programme_label_diffing=True,
      tv_shell_rebuild_after_player_disabled=True,black_screen_root_causes_addressed=['main_thread_library_cache','guide_layout_rebuild_loop','display_mode_handshake','system_bar_layout_churn'],
      multiview_fullscreen_reversible=True,multiview_other_tiles_preserved=True,
      player_ui_design_preserved=True,mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final 2103223 receipt drift: '+name)
    Path('audit223').mkdir(exist_ok=True)
    Path('audit223/tv-hardening-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,'marker':'cobra_tv_hardening_2103223',
      'mobile_fold_untouched':True,'guide_layout_rebuild_loop_fixed':True,'cache_restore_off_main':True,
      'display_mode_switching_disabled':True,'system_bar_layout_churn_fixed':True,
      'transient_focus_owned':True,'grid_focus_graph':True,'epg_refresh_coalesced':True,
      'decorative_motion_minimized':True,'player_ui_design_preserved':True,
      'multiview_preserved':True,'native_engine_rebuilt':False,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103223 TV hardening applied over exact 2103222 source; ARM64/mobile untouched')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
