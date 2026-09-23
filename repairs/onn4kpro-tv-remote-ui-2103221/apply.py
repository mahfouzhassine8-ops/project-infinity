#!/usr/bin/env python3
"""2103221 onn. 4K Pro TV remote interaction pass.

Parent: exact locked-for-now 2103220 TV Grid RC3 source.
Scope: TV/armeabi-v7a generated Android UI only. ARM64 phone/Fold source is untouched.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103221
OLD_VERSION=2103220
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Grid-RC3'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Remote-UI-RC4'
SOURCE='tools/android/packaging/xbmc/'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def require(v,m):
    if not v: raise RuntimeError(m)
def once(text,old,new,label):
    require(text.count(old)==1,f'{label} anchor drift ({text.count(old)})')
    return text.replace(old,new,1)
def method_span(text:str, signature:str):
    start=text.find(signature);require(start>=0,'Missing method signature: '+signature)
    brace=text.find('{',start);require(brace>=0,'Missing method brace: '+signature)
    depth=0
    for i in range(brace,len(text)):
        if text[i]=='{': depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return start,i+1
    raise RuntimeError('Unclosed method: '+signature)
def replace_method(text,signature,replacement):
    a,b=method_span(text,signature);return text[:a]+replacement+text[b:]
def method_by_name(text,name):
    pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:public|private|protected)\s+(?:static\s+)?[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{]*\)\s*\{')
    m=pat.search(text);require(m is not None,'Missing method by name: '+name)
    brace=text.find('{',m.start());depth=0
    for i in range(brace,len(text)):
        if text[i]=='{':depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return m.start(),brace,i+1
    raise RuntimeError('Unclosed method by name: '+name)
def replace_body(text,name,body):
    start,brace,end=method_by_name(text,name)
    prefix=text[start:brace];indent=re.match(r'\s*',prefix).group(0)
    rendered='{\n'+''.join(indent+'  '+line+'\n' for line in body.splitlines())+indent+'}'
    return text[:brace]+rendered+text[end:]

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
            'Expected exact 2103220 TV Grid RC3 parent')
    require(receipt.get('tv_grid_only') is True and receipt.get('tv_target_abi')=='armeabi-v7a',
            'Expected locked 2103220 TV-only parent')
    require(receipt.get('mobile_parent_untouched') is True,'Mobile/Fold protection receipt missing')

    gradle=shell/(SOURCE+'build.gradle.in')
    live=shell/(SOURCE+'src/InfinityLiveActivity.java.in')
    manifest=shell/(SOURCE+'AndroidManifest.xml.in')
    for p in (gradle,live,manifest):require(p.is_file(),'Missing generated source: '+str(p))

    g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName')
    gradle.write_text(g)

    s=live.read_text()

    # Stronger, immediate 10-foot focus feedback everywhere on this TV-only line.
    s=once(s,
      'v.setScaleX(focused?1.012f:1f);v.setScaleY(focused?1.012f:1f);v.setAlpha(focused?1f:.985f);',
      'v.setScaleX(focused?1.045f:1f);v.setScaleY(focused?1.045f:1f);v.setAlpha(focused?1f:.95f);',
      'TV remote focus visibility')

    # Channel groups: always open a real overlay. 2103220's wide-TV path tried to focus
    # a zero-width directory because Grid RC3 intentionally removed the permanent rail.
    s=replace_method(s,'private void cobraToggleModeGroups()','''private void cobraToggleModeGroups(){
    cobraRememberModeScroll();
    cobraOpenTvDirectory(false);
  }''')

    s=replace_method(s,'private void cobraDirectory(LinearLayout parent,boolean sources)','''private void cobraDirectory(LinearLayout parent,boolean sources){
    ArrayList<String> names=new ArrayList<>(),values=new ArrayList<>(),counts=new ArrayList<>();
    if(sources){names.add("All playlists");values.add("");counts.add("");for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id)){names.add(source.name);values.add(source.id);counts.add("Playlist");}}
    else{
      java.util.TreeMap<String,Integer> groups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);int all=0,favorites=0,recent=0;
      for(Channel channel:mChannels){
        if(channel==null||(!mCobraGuideSource.isEmpty()&&!mCobraGuideSource.equals(sourceIdForChannel(channel)))||!mFeatures.sourceEnabled(sourceIdForChannel(channel)))continue;
        String providerGroup=cobraNormalizeProviderGroup(channel.group);
        if(!providerGroup.isEmpty()&&!mFeatures.looksAdult(providerGroup)&&!groups.containsKey(providerGroup))groups.put(providerGroup,0);
        if(cobraChannelAllowed(channel)){all++;if(mFavorites.contains(channel.id))favorites++;if(mRecents.contains(channel.id))recent++;if(!providerGroup.isEmpty()&&!mFeatures.looksAdult(providerGroup))groups.put(providerGroup,groups.get(providerGroup)+1);}
      }
      Collections.addAll(names,"Favorites","Recently played","All channels");Collections.addAll(values,"FAVORITES","RECENT","ALL");Collections.addAll(counts,""+favorites,""+recent,""+all);
      for(Map.Entry<String,Integer> entry:groups.entrySet()){names.add(entry.getKey());values.add(entry.getKey());counts.add(""+entry.getValue());}
      for(String group:cobraCustomGroups()){names.add(group);values.add("MY:"+group);counts.add("My group");}
    }
    if(!sources){Button playlist=cobraTextButton(cobraModeSourceName()+"  ▾",cobraModeDark(),()->cobraOpenTvDirectory(true));playlist.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);playlist.setPadding(dp(14),0,dp(10),0);playlist.setSingleLine(true);parent.addView(playlist,new LinearLayout.LayoutParams(-1,dp(58)));}
    android.widget.ListView list=new android.widget.ListView(this);list.setDividerHeight(0);list.setSelector(android.R.color.transparent);list.setFastScrollEnabled(false);list.setItemsCanFocus(true);list.setFocusable(true);list.setFocusableInTouchMode(false);
    list.setAdapter(new android.widget.BaseAdapter(){public int getCount(){return names.size();}public Object getItem(int p){return values.get(p);}public long getItemId(int p){return CobraModeLayout.stableId(values.get(p));}public boolean hasStableIds(){return true;}
      public View getView(int position,View recycled,android.view.ViewGroup host){
        CobraDirectoryRow row=recycled instanceof CobraDirectoryRow?(CobraDirectoryRow)recycled:new CobraDirectoryRow();String value=values.get(position);
        row.bind(names.get(position),counts.get(position),value.equals(sources?mCobraGuideSource:mCategory));
        row.setOnClickListener(v->{cobraRememberModeScroll();if(sources){mCobraGuideSource=value;mCategory="ALL";mSearch="";if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();mCobraGuideRoute="channels";cobraRenderGuideBrowser();}else selectCobraCategory(value);});return row;
      }});
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    final String current=sources?mCobraGuideSource:mCategory;final int index=Math.max(0,values.indexOf(current));
    list.setSelection(index);
    list.post(()->{if(list.getAdapter()==null||list.getAdapter().getCount()==0)return;list.setSelection(index);list.post(()->{int childIndex=index-list.getFirstVisiblePosition();View row=childIndex>=0&&childIndex<list.getChildCount()?list.getChildAt(childIndex):null;if(row!=null&&row.isShown())row.requestFocus();else list.requestFocus();});});
  }''')

    s=replace_method(s,'private void cobraOpenTvDirectory(boolean sources)','''private void cobraOpenTvDirectory(boolean sources){
    if(!"grid".equals(mCobraGuideStyle)){mCobraGuideStyle="grid";mCobraGuideRoute="channels";}
    closeCobraActionSheet();FrameLayout decor=(FrameLayout)getWindow().getDecorView();
    mCobraSheetPreviousFocus=getCurrentFocus();mCobraSheetKind="tv-directory";
    FrameLayout scrim=new FrameLayout(this);mCobraActionSheet=scrim;scrim.setTag("cobra_tv_directory_overlay");scrim.setBackgroundColor(0x77000000);scrim.setClickable(true);scrim.setOnClickListener(v->closeCobraActionSheet());
    LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setClickable(true);panel.setFocusable(false);panel.setDescendantFocusability(android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS);panel.setBackgroundColor(cobraModeColor("rail"));panel.setPadding(dp(14),dp(12),dp(14),dp(12));
    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    TextView label=cobraText(sources?"PLAYLISTS":"CHANNEL GROUPS",cobraModeColor("text"),20);label.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));label.setPadding(dp(8),0,0,0);
    heading.addView(label,new LinearLayout.LayoutParams(0,dp(58),1));heading.addView(cobraIcon("close","Close "+(sources?"playlists":"channel groups"),cobraModeDark(),v->closeCobraActionSheet()),new LinearLayout.LayoutParams(dp(56),dp(56)));panel.addView(heading);
    cobraDirectory(panel,sources);
    int w=decor.getWidth()>0?decor.getWidth():getResources().getDisplayMetrics().widthPixels,h=decor.getHeight()>0?decor.getHeight():getResources().getDisplayMetrics().heightPixels;
    int top=dp(28),bottom=dp(20);if(Build.VERSION.SDK_INT>=23&&decor.getRootWindowInsets()!=null){top+=decor.getRootWindowInsets().getSystemWindowInsetTop();bottom+=decor.getRootWindowInsets().getSystemWindowInsetBottom();}
    int width=Math.max(dp(320),Math.min(dp(430),Math.round(w*.42f)));FrameLayout.LayoutParams position=new FrameLayout.LayoutParams(Math.min(width,w-dp(24)),Math.max(1,h-top-bottom),Gravity.TOP|Gravity.LEFT);position.topMargin=top;position.bottomMargin=bottom;
    scrim.addView(panel,position);decor.addView(scrim,new FrameLayout.LayoutParams(-1,-1));
    panel.setTranslationX(-position.width);panel.animate().translationX(0f).setDuration(80L).start();
  }''')

    # Directory rows get a strong focused ring and larger TV row height.
    s=replace_method(s,'void bind(String label,String total,boolean active)','''void bind(String label,String total,boolean active){
      name.setText(label);count.setText(total);name.setTextColor(active?cobraModeColor("accent"):cobraModeColor("text"));count.setTextColor(cobraModeColor("muted"));
      android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
      states.addState(new int[]{android.R.attr.state_focused},surface(cobraModeColor("panel"),14,cobraModeColor("accent"),3));
      states.addState(new int[]{android.R.attr.state_selected},surface(cobraModeColor("panel"),14,cobraModeColor("accent"),1));
      states.addState(new int[]{},surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));
      setBackground(states);setSelected(active);setContentDescription(label+(total.isEmpty()?"":", "+total));setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(62)));
    }''')
    s=once(s,'CobraDirectoryRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(vtheme().dimension("cobra.CobraDirectoryRow.dimensions.1",12)),0,dp(vtheme().dimension("cobra.CobraDirectoryRow.dimensions.2",12)),0);addView(name,new LinearLayout.LayoutParams(0,-1,1));count.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-2,-1);p.leftMargin=dp(vtheme().dimension("cobra.CobraDirectoryRow.dimensions.3",6));addView(count,p);setFocusable(true);setFocusableInTouchMode(false);setClickable(true);}',
      'CobraDirectoryRow(){super(InfinityLiveActivity.this);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(16),0,dp(14),0);addView(name,new LinearLayout.LayoutParams(0,-1,1));count.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-2,-1);p.leftMargin=dp(8);addView(count,p);setFocusable(true);setFocusableInTouchMode(false);setClickable(true);cobraPolishFocusable(this);}',
      'directory row TV polish')

    # After switching group/source, the guide always owns a visible focus target.
    old_install='''  private void cobraInstallModeList(LinearLayout parent,android.widget.AbsListView list,android.widget.BaseAdapter adapter){
    mCobraGuideList=list;mCobraGuideAdapter=adapter;list.setSelector(android.R.color.transparent);list.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);list.setFastScrollEnabled(adapter.getCount()>160);list.setClipToPadding(false);
    if(list instanceof android.widget.GridView)((android.widget.GridView)list).setAdapter(adapter);else{((android.widget.ListView)list).setItemsCanFocus("grid".equals(mCobraGuideStyle));((android.widget.ListView)list).setDividerHeight(0);((android.widget.ListView)list).setAdapter(adapter);}
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    list.setOnScrollListener(new android.widget.AbsListView.OnScrollListener(){public void onScrollStateChanged(android.widget.AbsListView v,int state){if(state==SCROLL_STATE_IDLE)cobraQueueVisibleGuides();else mMain.removeCallbacks(mCobraVisibleGuideFetch);}public void onScroll(android.widget.AbsListView v,int a,int b,int c){}});cobraQueueVisibleGuides();
  }'''
    require(old_install in s,'guide list method drift')
    new_install='''  private void cobraInstallModeList(LinearLayout parent,android.widget.AbsListView list,android.widget.BaseAdapter adapter){
    mCobraGuideList=list;mCobraGuideAdapter=adapter;list.setSelector(android.R.color.transparent);list.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);list.setFastScrollEnabled(false);list.setClipToPadding(false);list.setFocusable(true);list.setFocusableInTouchMode(false);
    if(list instanceof android.widget.GridView)((android.widget.GridView)list).setAdapter(adapter);else{((android.widget.ListView)list).setItemsCanFocus(true);((android.widget.ListView)list).setDividerHeight(0);((android.widget.ListView)list).setAdapter(adapter);}
    parent.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    list.setOnScrollListener(new android.widget.AbsListView.OnScrollListener(){public void onScrollStateChanged(android.widget.AbsListView v,int state){if(state==SCROLL_STATE_IDLE)cobraQueueVisibleGuides();else mMain.removeCallbacks(mCobraVisibleGuideFetch);}public void onScroll(android.widget.AbsListView v,int a,int b,int c){}});cobraQueueVisibleGuides();
    list.post(()->{if(list.findFocus()!=null)return;View preferred=mGuidePreviewChannel==null?null:list.findViewWithTag("cobra-channel:"+mGuidePreviewChannel.id);if(preferred!=null){preferred.requestFocus();return;}if(list.getChildCount()>0){View first=list.getChildAt(0);if(first instanceof android.view.ViewGroup)cobraTvFocusFirst((android.view.ViewGroup)first);else first.requestFocus();}else list.requestFocus();});
  }'''
    s=s.replace(old_install,new_install,1)

    # Preview is informational on TV. It never enters the D-pad focus graph.
    s=replace_method(s,'private FrameLayout cobraPreviewPanel(Channel channel,boolean guide)','''private FrameLayout cobraPreviewPanel(Channel channel,boolean guide) {
    if(mCobraPreviewHost!=null)return mCobraPreviewHost;
    FrameLayout host=new FrameLayout(this);mCobraPreviewHost=host;host.setTag("cobra_preview_host");host.setBackgroundColor(Color.BLACK);
    host.setFocusable(false);host.setFocusableInTouchMode(false);host.setClickable(false);host.setLongClickable(false);host.setDescendantFocusability(android.view.ViewGroup.FOCUS_BLOCK_DESCENDANTS);
    mCobraPreviewTexture=new TextureView(this);mCobraPreviewTexture.setFocusable(false);mCobraPreviewTexture.setClickable(false);host.addView(mCobraPreviewTexture,new FrameLayout.LayoutParams(-1,-1));
    TextView state=cobraText("PREVIEW",Color.WHITE,12);state.setTag("cobra_preview_label");state.setPadding(dp(10),dp(5),dp(10),dp(5));state.setBackgroundColor(0xa8000000);
    FrameLayout.LayoutParams statePos=new FrameLayout.LayoutParams(-2,dp(30),Gravity.TOP|Gravity.RIGHT);statePos.setMargins(dp(8),dp(8),dp(8),0);host.addView(cobraPulseStatus(state),statePos);
    TextView hint=cobraText("Select the current channel again to watch",0xffd8e6f2,11);hint.setGravity(Gravity.CENTER);hint.setPadding(dp(10),0,dp(10),0);hint.setBackgroundColor(0xb0000000);
    host.addView(hint,new FrameLayout.LayoutParams(-1,dp(34),Gravity.BOTTOM));
    cobraUpdatePreviewSubtitleState();return host;
  }''')

    # The preview details panel is display-only on TV too; the guide keeps D-pad ownership.
    s=once(s,'    epg.setTag("cobra_preview_epg");',
      '    epg.setTag("cobra_preview_epg");epg.setFocusable(false);epg.setFocusableInTouchMode(false);epg.setClickable(false);epg.setVisibility(View.GONE);',
      'preview EPG focus removal')

    # Slightly larger TV preview than RC3 while still leaving the EPG dominant.
    s=once(s,
      'int hero=Math.min(Math.round(108+10*(f-1)),Math.max(76,avail*20/100));\n        int vw=Math.min(Math.round(192+16*(f-1)),Math.min(Math.max(120,body/4),hero*16/9));',
      'int hero=Math.min(Math.round(132+12*(f-1)),Math.max(96,avail*24/100));\n        int vw=Math.min(Math.round(236+20*(f-1)),Math.min(Math.max(150,body/3),hero*16/9));',
      'TV preview geometry')

    # Quick Peek video is also passive; focus lands on Watch.
    s=once(s,
      '    preview.setFocusable(true);preview.setClickable(true);preview.setContentDescription("Watch "+channel.name+" in the main player");\n    preview.setOnClickListener(v->{if(profile.equals(mFeatures.activeProfileId())&&cobraSessionChannelAllowed(channel))cobraRecallTune(channel);});',
      '    preview.setFocusable(false);preview.setFocusableInTouchMode(false);preview.setClickable(false);preview.setLongClickable(false);preview.setDescendantFocusability(android.view.ViewGroup.FOCUS_BLOCK_DESCENDANTS);preview.setContentDescription("Preview for "+channel.name);\n    actions.post(()->{if(play.isAttachedToWindow())play.requestFocus();});',
      'Quick Peek TV focus')

    # Player remote ownership: controls get focus immediately; Back unwinds one layer.
    player_helpers='''  private static final String COBRA_TV_REMOTE_UI_BUILD="cobra_tv_remote_ui_2103221";

  private boolean cobraTvViewInside(View root,View child){
    if(root==null||child==null)return false;View current=child;
    while(current!=null){if(current==root)return true;android.view.ViewParent parent=current.getParent();current=parent instanceof View?(View)parent:null;}
    return false;
  }

  private void cobraTvFocusPlayerPrimary(){
    if(mPlayerChrome==null||!mPlayerChrome.isAttachedToWindow()||mPlayerChrome.getVisibility()!=View.VISIBLE)return;
    View target=mPlayerChrome.findViewWithTag("cobra_player_play_pause");if(target!=null&&target.isShown()&&target.isFocusable())target.requestFocus();else cobraTvFocusFirst(mPlayerChrome);
  }

  private void cobraTvHidePlayerChrome(){
    mMain.removeCallbacks(mHideChrome);if(mPlayerChrome!=null){cobraResetMotion(mPlayerChrome);mPlayerChrome.setVisibility(View.GONE);}
    if(mPlayerOverlay!=null&&mPlayerOverlay.isAttachedToWindow())mPlayerOverlay.requestFocus();
  }

  private boolean cobraTvNudgeTimeline(int direction){
    if(mCobraTimeshiftSeek==null||mCobraTimeshiftSeek.getVisibility()!=View.VISIBLE||!cobraTimeshiftTimelineAvailable())return false;
    int step=50;int value=Math.max(0,Math.min(1000,mCobraTimeshiftSeek.getProgress()+direction*step));
    mCobraTimeshiftSeek.setProgress(value);cobraCommitTimelineSeek(value);cobraUpdateTimeshiftSeek();return true;
  }

  private boolean cobraTvHandleDirectoryKey(KeyEvent event){
    if(event.getAction()!=KeyEvent.ACTION_DOWN||!"tv-directory".equals(mCobraSheetKind)||mCobraActionSheet==null)return false;
    int code=event.getKeyCode();if(code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_DPAD_LEFT){closeCobraActionSheet();return true;}return false;
  }

  private boolean cobraTvHandlePlayerKey(KeyEvent event){
    if(event.getAction()!=KeyEvent.ACTION_DOWN||mPlayerOverlay==null||mCobraPlayerLocked)return false;
    int code=event.getKeyCode();
    if(mCobraPlayerDrawer!=null){
      if(code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_DPAD_LEFT){closeCobraPlayerDrawer();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}
      return false;
    }
    if(mCobraMultiPicker!=null){
      if(code==KeyEvent.KEYCODE_BACK){closeCobraMultiPicker(false);showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}
      return false;
    }
    if(mCobraActionSheet!=null){
      if(code==KeyEvent.KEYCODE_BACK){closeCobraActionSheet();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}
      return false;
    }
    if(code==KeyEvent.KEYCODE_MENU){showCobraPlayerDrawer();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE){toggleCobraPlayerPlayPause();return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_REWIND){cobraRewindLive(30000L);return true;}
    if(code==KeyEvent.KEYCODE_MEDIA_FAST_FORWARD){if(!cobraTvNudgeTimeline(1))cobraGoLive();return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_UP){stepChannel(1);return true;}
    if(code==KeyEvent.KEYCODE_CHANNEL_DOWN){stepChannel(-1);return true;}
    if(code==KeyEvent.KEYCODE_BACK){
      if(mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE){cobraTvHidePlayerChrome();return true;}
      return false;
    }
    View focus=getCurrentFocus();boolean inChrome=mPlayerChrome!=null&&cobraTvViewInside(mPlayerChrome,focus);
    if(code==KeyEvent.KEYCODE_DPAD_CENTER||code==KeyEvent.KEYCODE_ENTER||code==KeyEvent.KEYCODE_DPAD_UP||code==KeyEvent.KEYCODE_DPAD_DOWN||code==KeyEvent.KEYCODE_DPAD_LEFT||code==KeyEvent.KEYCODE_DPAD_RIGHT){
      if(mPlayerChrome==null||mPlayerChrome.getVisibility()!=View.VISIBLE||!inChrome){showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return true;}
    }
    return false;
  }

  private void cobraTvFocusPlayerDrawerTarget(){
    if(mCobraPlayerDrawerList==null||mCobraPlayerDrawerList.getAdapter()==null||mCobraPlayerDrawerList.getAdapter().getCount()==0)return;
    int target=0;android.widget.ListAdapter adapter=mCobraPlayerDrawerList.getAdapter();
    for(int i=0;i<adapter.getCount();i++){Object item=adapter.getItem(i);if(item instanceof Channel&&mPlaying!=null&&mPlaying.id.equals(((Channel)item).id)){target=i;break;}if(item instanceof String&&mPlaying!=null&&((String)item).equals(mPlaying.group)){target=i;break;}}
    final int selected=target;mCobraPlayerDrawerList.setSelection(selected);mCobraPlayerDrawerList.post(()->{int childIndex=selected-mCobraPlayerDrawerList.getFirstVisiblePosition();View row=childIndex>=0&&childIndex<mCobraPlayerDrawerList.getChildCount()?mCobraPlayerDrawerList.getChildAt(childIndex):null;if(row!=null)row.requestFocus();else mCobraPlayerDrawerList.requestFocus();});
  }

'''
    s=once(s,'  @Override public boolean dispatchKeyEvent(KeyEvent event) {',
      player_helpers+'  @Override public boolean dispatchKeyEvent(KeyEvent event) {',
      'TV player helper insertion')
    s=once(s,
      '  @Override public boolean dispatchKeyEvent(KeyEvent event) {\n    if(cobraTvHandleDrawerKey(event))return true;',
      '  @Override public boolean dispatchKeyEvent(KeyEvent event) {\n    if(cobraTvHandleDrawerKey(event))return true;\n    if(cobraTvHandleDirectoryKey(event))return true;\n    if(cobraTvHandlePlayerKey(event))return true;',
      'TV remote dispatch')

    s=replace_method(s,'private void showPlayerChromeTemporarily()','''private void showPlayerChromeTemporarily() {
    if(mPlayerChrome==null||mCobraPlayerLocked||mInPictureInPicture||mCobraPlayerDrawer!=null||mCobraMultiPicker!=null||mCobraActionSheet!=null)return;
    final LinearLayout chrome=mPlayerChrome;cobraResetMotion(chrome);chrome.setAlpha(1f);chrome.setVisibility(View.VISIBLE);
    if(!cobraTvViewInside(chrome,getCurrentFocus()))chrome.post(this::cobraTvFocusPlayerPrimary);
    scheduleChromeHide();
  }''')
    try:
      s=replace_body(s,'scheduleChromeHide','mMain.removeCallbacks(mHideChrome);')
    except RuntimeError:
      # Exact fallback for the observed RC3 one-line body.
      old='if(mPlayerChrome!=null&&!mCobraPlayerLocked&&!mInPictureInPicture&&mCobraActionSheet==null&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null)mMain.postDelayed(mHideChrome,CobraPresentationEffects.chromeDelay(cobraNightCinemaActive()));'
      require(old in s,'scheduleChromeHide drift');s=s.replace(old,'mMain.removeCallbacks(mHideChrome);',1)

    # Timeline becomes a real D-pad target. Left/right commits ±5% of the rewind window.
    timeline_anchor='mCobraTimeshiftSeek.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.TRANSPARENT));'
    timeline_add=timeline_anchor+'mCobraTimeshiftSeek.setFocusable(true);mCobraTimeshiftSeek.setFocusableInTouchMode(false);mCobraTimeshiftSeek.setOnKeyListener((v,key,event)->{if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvNudgeTimeline(-1);if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvNudgeTimeline(1);if(key==KeyEvent.KEYCODE_DPAD_UP){cobraTvFocusPlayerPrimary();return true;}return false;});cobraPolishFocusable(mCobraTimeshiftSeek);'
    s=once(s,timeline_anchor,timeline_add,'TV timeline keys')

    # Player chrome starts with an actual selected control, not the full-screen container.
    chrome_anchor='if(chrome.getVisibility()==View.VISIBLE)cobraAnimatePlayerChromeIn(chrome);'
    s=once(s,chrome_anchor,chrome_anchor+'if(chrome.getVisibility()==View.VISIBLE&&mCobraActionSheet==null&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null)chrome.post(()->{if(!cobraTvViewInside(chrome,getCurrentFocus()))cobraTvFocusPlayerPrimary();});','player primary focus')

    # Player channel drawer: no touch language, no fast-scroll, tune-and-close, focus current channel/group.
    s=once(s,'mCobraPlayerDrawerList.setFastScrollEnabled(true);','mCobraPlayerDrawerList.setFastScrollEnabled(false);','player drawer fast scroll')
    s=once(s,
      'TextView hint=cobraText(vtheme().copy("cobra.showCobraPlayerDrawer.copy.2","Tap to tune • tap playing channel to expand • hold for Quick Peek"),vtheme().color("cobra.showCobraPlayerDrawer.colors.3",0xff91a8be),11);',
      'TextView hint=cobraText("Select to tune • Back to close • hold Select for Quick Peek",vtheme().color("cobra.showCobraPlayerDrawer.colors.3",0xff91a8be),12);',
      'player drawer remote hint')
    s=once(s,
      'if(groups){String group=names.get(p);row.setText(group);row.setSelected(false);row.setOnClickListener(v->cobraRenderPlayerDrawer("GROUP:"+group));row.setOnLongClickListener(null);}',
      'if(groups){String group=names.get(p);row.setText(group);row.setSelected(mPlaying!=null&&group.equals(mPlaying.group));row.setOnClickListener(v->cobraRenderPlayerDrawer("GROUP:"+group));row.setOnLongClickListener(null);}',
      'player drawer group current')
    old_tune='row.setOnClickListener(v->{if(mPlaying!=null&&mPlaying.id.equals(c.id)){closeCobraPlayerDrawer();return;}mPlaying=c;mPlayingIndex=mChannels.indexOf(c);mPlayingVodKey="";mPendingResumeMs=0;startSinglePlayer(c.primaryUrl);cobraBuildPlayerChrome();if(mCobraPlayerDrawerList!=null&&mCobraPlayerDrawerList.getAdapter() instanceof android.widget.BaseAdapter)((android.widget.BaseAdapter)mCobraPlayerDrawerList.getAdapter()).notifyDataSetChanged();});'
    new_tune='row.setOnClickListener(v->{if(mPlaying!=null&&mPlaying.id.equals(c.id)){closeCobraPlayerDrawer();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return;}mPlaying=c;mPlayingIndex=mChannels.indexOf(c);mPlayingVodKey="";mPendingResumeMs=0;startSinglePlayer(c.primaryUrl);closeCobraPlayerDrawer();cobraBuildPlayerChrome();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();});'
    s=once(s,old_tune,new_tune,'player drawer one-press tune')
    old_motion='mCobraPlayerDrawerList.setAlpha(.72f);mCobraPlayerDrawerList.setTranslationY(dp(5));mCobraPlayerDrawerList.animate().alpha(1f).translationY(0f).setDuration(150L).setInterpolator(new android.view.animation.DecelerateInterpolator()).start();'
    s=once(s,old_motion,'mCobraPlayerDrawerList.setAlpha(1f);mCobraPlayerDrawerList.setTranslationY(0f);mCobraPlayerDrawerList.post(this::cobraTvFocusPlayerDrawerTarget);','player drawer immediate focus')

    # Keep groups reachable from channel title with one Left press; make remote wording TV-native.
    s=s.replace('tap to preview or hold for schedule','Select to preview or hold Select for schedule')

    live.write_text(s)

    # Source-level gates before any expensive build.
    for token in (
      'COBRA_TV_GRID_ONLY_BUILD="cobra_tv_grid_only_2103220"',
      'COBRA_TV_REMOTE_UI_BUILD="cobra_tv_remote_ui_2103221"',
      'private void cobraToggleModeGroups(){\n    cobraRememberModeScroll();\n    cobraOpenTvDirectory(false);',
      'mCobraTimeshiftSeek.setOnKeyListener',
      'cobraTvHandlePlayerKey(event)',
      'cobraTvFocusPlayerDrawerTarget',
      'Select to tune • Back to close',
      'Select the current channel again to watch',
      'preview.setFocusable(false)',
      'epg.setFocusable(false)',
      'list.setFastScrollEnabled(false)',
      'versionCode 2103221',
    ):
      require(token in (s+g),'2103221 source gate missing: '+token)
    for forbidden in (
      'mCobraGuideDirectory.requestFocus();return;',
      'heading.requestFocus();',
      'bar.setTag("cobra_preview_controls")',
      'Tap to tune • tap playing channel to expand',
    ):
      require(forbidden not in s,'TV touch/invisible-focus path remains: '+forbidden)

    for rel in (SOURCE+'build.gradle.in',SOURCE+'AndroidManifest.xml.in',SOURCE+'src/InfinityLiveActivity.java.in'):
      require(rel in receipt['files'],'Receipt missing '+rel)
      receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
      candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
      tv_variant=True,tv_target='onn. 4K Pro / Google TV',tv_target_abi='armeabi-v7a',
      tv_grid_only=True,tv_remote_ui=True,tv_group_overlay_always=True,
      tv_group_current_focus=True,tv_guide_initial_focus=True,tv_preview_focusable=False,
      tv_preview_controls='passive',tv_player_primary_focus=True,tv_player_back_layers=True,
      tv_player_timeline_dpad=True,tv_player_drawer_current_focus=True,
      tv_player_drawer_one_press_tune=True,tv_quick_peek_video_focusable=False,
      mobile_parent_untouched=True,same_package=True,same_signer_required=True,
      playback_engine_unchanged=True,
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final 2103221 receipt drift: '+name)

    Path('audit221').mkdir(exist_ok=True)
    Path('audit221/tv-remote-ui-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,
      'marker':'cobra_tv_remote_ui_2103221','target_abi':'armeabi-v7a',
      'mobile_fold_untouched':True,'group_overlay_always':True,'group_current_focus':True,
      'guide_initial_focus':True,'preview_focusable':False,'preview_phone_controls':False,
      'player_primary_focus':True,'player_back_layers':True,'timeline_dpad':True,
      'player_drawer_current_focus':True,'player_drawer_one_press_tune':True,
      'quick_peek_video_focusable':False,'playback_engine_unchanged':True,
      'physical_device_verified':False,
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103221 TV group/player/preview remote UI applied over locked 2103220; ARM64/mobile untouched')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
