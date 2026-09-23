#!/usr/bin/env python3
"""2103224 onn. 4K Pro native-TV remote architecture pass.

Parent: exact locked 2103223 TV Hardening RC6 source.
Scope: TV Android layer only. ARM64 phone/Fold and the ARMv7 native engine are untouched.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103224
OLD_VERSION=2103223
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Hardening-RC6'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Native-Remote-RC7'
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

NATIVE_REMOTE_HELPERS=r'''  private static final String COBRA_TV_NATIVE_REMOTE_BUILD="cobra_tv_native_remote_2103224";
  private String mCobraTvMultiFilter="RECENT";
  private int mCobraTvMultiFilterIndex=1;
  private int mCobraTvMultiRow=0;

  private View cobraTvTagged(View root,String tag){
    return root==null?null:root.findViewWithTag(tag);
  }

  private boolean cobraTvFocusTagged(View root,String tag){
    View target=cobraTvTagged(root,tag);
    if(target!=null&&target.isShown()&&target.isEnabled()&&target.isFocusable()){target.requestFocus();cobraTvReveal(target);return true;}
    return false;
  }

  private android.widget.ListView cobraTvMultiList(){
    if(mCobraMultiPicker==null)return null;View raw=mCobraMultiPicker.findViewWithTag("cobra_multi_picker_list");
    return raw instanceof android.widget.ListView?(android.widget.ListView)raw:null;
  }

  private String cobraTvMultiFilterKey(int index){
    String[] keys={"FAVORITES","RECENT","ALL","CATEGORIES"};return keys[Math.max(0,Math.min(keys.length-1,index))];
  }

  private int cobraTvMultiFilterIndex(String filter){
    if("FAVORITES".equals(filter))return 0;if("RECENT".equals(filter))return 1;if("ALL".equals(filter))return 2;return 3;
  }

  private boolean cobraTvFocusMultiFilter(int index){
    if(mCobraMultiPicker==null)return false;mCobraTvMultiFilterIndex=Math.max(0,Math.min(3,index));
    return cobraTvFocusTagged(mCobraMultiPicker,"cobra_multi_filter:"+mCobraTvMultiFilterIndex);
  }

  private void cobraTvRefreshMultiFilterSelection(){
    if(mCobraMultiPicker==null)return;
    for(int i=0;i<4;i++){
      View raw=mCobraMultiPicker.findViewWithTag("cobra_multi_filter:"+i);
      if(raw!=null)raw.setSelected(i==mCobraTvMultiFilterIndex);
    }
  }

  private boolean cobraTvFocusMultiRow(int position){
    android.widget.ListView list=cobraTvMultiList();if(list==null||list.getAdapter()==null||list.getAdapter().getCount()==0)return false;
    mCobraTvMultiRow=Math.max(0,Math.min(list.getAdapter().getCount()-1,position));
    list.setSelection(mCobraTvMultiRow);list.setItemChecked(mCobraTvMultiRow,true);list.requestFocus();
    final int wanted=mCobraTvMultiRow;list.post(()->{if(list!=cobraTvMultiList())return;list.setSelection(wanted);list.setItemChecked(wanted,true);});
    return true;
  }

  private boolean cobraTvActivateMultiRow(){
    android.widget.ListView list=cobraTvMultiList();if(list==null||list.getAdapter()==null||list.getAdapter().getCount()==0)return true;
    final int wanted=Math.max(0,Math.min(list.getAdapter().getCount()-1,mCobraTvMultiRow));mCobraTvMultiRow=wanted;
    list.setSelection(wanted);
    list.post(()->{
      if(list!=cobraTvMultiList()||list.getAdapter()==null||wanted>=list.getAdapter().getCount())return;
      int child=wanted-list.getFirstVisiblePosition();View row=child>=0&&child<list.getChildCount()?list.getChildAt(child):null;
      list.performItemClick(row,wanted,list.getAdapter().getItemId(wanted));
    });
    return true;
  }

  private boolean cobraTvHandleMultiPickerKey(KeyEvent event){
    if(mCobraMultiPicker==null||event.getAction()!=KeyEvent.ACTION_DOWN)return false;
    int key=event.getKeyCode();View focus=getCurrentFocus();Object raw=focus==null?null:focus.getTag();String tag=raw instanceof String?(String)raw:"";
    if(key==KeyEvent.KEYCODE_BACK){closeCobraMultiPicker(false);if(mPlayerOverlay!=null)mMain.post(this::cobraTvFocusPlayerPrimary);else if(mMultiOverlay!=null)mMain.post(this::cobraTvFocusCurrentMultiTile);return true;}
    if(focus==null||!cobraTvViewInside(mCobraMultiPicker,focus)){cobraTvFocusMultiFilter(mCobraTvMultiFilterIndex);return true;}
    if("cobra_multi_close".equals(tag)){
      if(key==KeyEvent.KEYCODE_DPAD_DOWN)return cobraTvFocusTagged(mCobraMultiPicker,"cobra_multi_search");
      if(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER){focus.performClick();return true;}
      return key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT||key==KeyEvent.KEYCODE_DPAD_UP;
    }
    if("cobra_multi_search".equals(tag)){
      if(key==KeyEvent.KEYCODE_DPAD_UP)return cobraTvFocusTagged(mCobraMultiPicker,"cobra_multi_close");
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){
        if("SEARCH".equals(mCobraTvMultiFilter)&&cobraTvMultiList()!=null&&cobraTvMultiList().getAdapter()!=null&&cobraTvMultiList().getAdapter().getCount()>0)return cobraTvFocusMultiRow(0);
        return cobraTvFocusMultiFilter(mCobraTvMultiFilterIndex);
      }
      return false;
    }
    if(tag.startsWith("cobra_multi_filter:")){
      int at=mCobraTvMultiFilterIndex;try{at=Integer.parseInt(tag.substring(tag.indexOf(':')+1));}catch(Exception ignored){}
      mCobraTvMultiFilterIndex=Math.max(0,Math.min(3,at));
      if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvFocusMultiFilter(mCobraTvMultiFilterIndex-1);
      if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvFocusMultiFilter(mCobraTvMultiFilterIndex+1);
      if(key==KeyEvent.KEYCODE_DPAD_UP)return cobraTvFocusTagged(mCobraMultiPicker,"cobra_multi_search");
      if(key==KeyEvent.KEYCODE_DPAD_DOWN)return cobraTvFocusMultiRow(0);
      if(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER){focus.performClick();return true;}
      return false;
    }
    android.widget.ListView list=cobraTvMultiList();
    if(list!=null&&(focus==list||cobraTvViewInside(list,focus))){
      if(key==KeyEvent.KEYCODE_DPAD_UP){
        if(mCobraTvMultiRow<=0)return cobraTvFocusMultiFilter(mCobraTvMultiFilterIndex);
        return cobraTvFocusMultiRow(mCobraTvMultiRow-1);
      }
      if(key==KeyEvent.KEYCODE_DPAD_DOWN)return cobraTvFocusMultiRow(mCobraTvMultiRow+1);
      if(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER)return cobraTvActivateMultiRow();
      if(key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT)return true;
    }
    return true;
  }

  private boolean cobraTvMovePlayerHeader(String tag,int direction){
    String[] tags={"cobra_tv_player_header_back","cobra_last_channel","cobra_tv_player_header_favorite","cobra_tv_player_header_lock"};
    int at=-1;for(int i=0;i<tags.length;i++)if(tags[i].equals(tag)){at=i;break;}if(at<0)at=2;
    for(int step=1;step<=tags.length;step++){
      int next=at+direction*step;if(next<0||next>=tags.length)break;
      if(cobraTvFocusPlayerTag(tags[next]))return true;
    }
    return true;
  }

  private boolean cobraTvMoveGridHeader(String tag,int direction){
    String[] tags={"cobra_tv_grid_group","cobra_tv_grid_source","cobra_tv_grid_search"};int at=-1;
    for(int i=0;i<tags.length;i++)if(tags[i].equals(tag)){at=i;break;}if(at<0)return false;
    int next=Math.max(0,Math.min(tags.length-1,at+direction));return cobraTvFocusTagged(mCobraGuideBrowser,tags[next]);
  }

  private boolean cobraTvMoveGridTime(String tag,int direction){
    String[] tags={"cobra_tv_grid_time_back","cobra_tv_grid_time_now","cobra_tv_grid_time_next"};int at=-1;
    for(int i=0;i<tags.length;i++)if(tags[i].equals(tag)){at=i;break;}if(at<0)return false;
    int next=Math.max(0,Math.min(tags.length-1,at+direction));return cobraTvFocusTagged(mCobraGuideBrowser,tags[next]);
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    marker='  private static final String COBRA_TV_HARDENING_BUILD="cobra_tv_hardening_2103223";'
    req(s.count(marker)==1,'2103223 hardening marker missing')
    s=s.replace(marker,NATIVE_REMOTE_HELPERS+marker,1)

    # Player header becomes an explicit remote row; transport -> Up lands near Favorite/Lock.
    s=replace_member(s,'cobraTvPlayerFocusGraph',r'''  private boolean cobraTvPlayerFocusGraph(int code){
    View focus=getCurrentFocus();if(focus==null||mPlayerChrome==null||!cobraTvViewInside(mPlayerChrome,focus))return false;
    Object raw=focus.getTag();String tag=raw instanceof String?(String)raw:"";
    boolean header=tag.startsWith("cobra_tv_player_header")||"cobra_last_channel".equals(tag);
    boolean transport=tag.startsWith("cobra_tv_player_transport")||"cobra_live_rewind_30".equals(tag)||"cobra_player_play_pause".equals(tag)||"cobra_live_edge".equals(tag);
    boolean tools=tag.startsWith("cobra_tv_player_tool")||"cobra_player_aspect_anchor".equals(tag)||"cobra_player_options_anchor".equals(tag);
    boolean timeline="cobra_live_timeshift_seek".equals(tag);
    if(header&&(code==KeyEvent.KEYCODE_DPAD_LEFT||code==KeyEvent.KEYCODE_DPAD_RIGHT))
      return cobraTvMovePlayerHeader(tag,code==KeyEvent.KEYCODE_DPAD_RIGHT?1:-1);
    if(code==KeyEvent.KEYCODE_DPAD_UP){
      if(tools){if(mCobraTimeshiftSeek!=null&&mCobraTimeshiftSeek.getVisibility()==View.VISIBLE)return mCobraTimeshiftSeek.requestFocus();return cobraTvFocusPlayerTag("cobra_player_play_pause");}
      if(timeline)return cobraTvFocusPlayerTag("cobra_player_play_pause");
      if(transport){if(cobraTvFocusPlayerTag("cobra_tv_player_header_favorite"))return true;return cobraTvFocusPlayerTag("cobra_tv_player_header_back");}
      if(header)return true;
    }
    if(code==KeyEvent.KEYCODE_DPAD_DOWN){
      if(header)return cobraTvFocusPlayerTag("cobra_player_play_pause");
      if(transport){if(mCobraTimeshiftSeek!=null&&mCobraTimeshiftSeek.getVisibility()==View.VISIBLE)return mCobraTimeshiftSeek.requestFocus();return cobraTvFocusPlayerTag("cobra_tv_player_tool_channels");}
      if(timeline)return cobraTvFocusPlayerTag("cobra_tv_player_tool_channels");
      if(tools)return true;
    }
    return false;
  }''')

    # Multi-View has its own navigation owner; never route it through the generic transient focus walker.
    transient=member(s,'cobraTvHandleTransientKey')
    transient=once(transient,'  private boolean cobraTvHandleTransientKey(KeyEvent event){\n',
      '  private boolean cobraTvHandleTransientKey(KeyEvent event){\n    if(mCobraMultiPicker!=null)return cobraTvHandleMultiPickerKey(event);\n',
      'Multi-View dedicated focus owner')
    s=replace_member(s,'cobraTvHandleTransientKey',transient)

    # TV-native picker: filter row and ListView own focus; rows are data, not competing child focus targets.
    s=replace_member(s,'showCobraMultiPicker',r'''  private void showCobraMultiPicker(boolean adding){
    if(mCobraPlayerLocked)return;closeCobraPlayerDrawer();closeCobraActionSheet();closeCobraMultiPicker(false);
    FrameLayout parent=adding?mMultiOverlay:mPlayerOverlay;if(parent==null)return;mCobraMultiPickerAdding=adding;
    mCobraTvMultiFilter="RECENT";mCobraTvMultiFilterIndex=1;mCobraTvMultiRow=0;
    FrameLayout panel=new FrameLayout(this);mCobraMultiPicker=panel;panel.setTag("cobra_multi_picker");panel.setBackground(cobraPanelSurface(0xfc080b11,0,0xff293244));panel.setElevation(dp(12));
    LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(16),dp(12),dp(16),dp(16));panel.addView(content,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);
    TextView title=cobraText(mCobraMultiReplaceIndex>=0?"Change screen":adding?"Add screen":"Pick a second screen",Color.WHITE,18);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));
    header.addView(title,new LinearLayout.LayoutParams(0,dp(52),1));
    CobraIconButton close=cobraIcon("close","Close Multi-View picker",true,v->closeCobraMultiPicker(false));close.setTag("cobra_multi_close");header.addView(close,new LinearLayout.LayoutParams(dp(52),dp(52)));content.addView(header,new LinearLayout.LayoutParams(-1,dp(54)));
    EditText search=new EditText(this);search.setTag("cobra_multi_search");search.setSingleLine(true);search.setHint("Search channels");search.setTextColor(Color.WHITE);search.setHintTextColor(0xff9fb0c2);
    search.setBackground(cobraPanelSurface(0xff101722,12,0xff33465b));search.setPadding(dp(14),0,dp(14),0);search.setFocusable(true);search.setFocusableInTouchMode(false);
    search.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence x,int a,int b,int c){}public void onTextChanged(CharSequence x,int a,int b,int c){}public void afterTextChanged(android.text.Editable e){renderCobraMultiPickerSearch(e.toString());}});
    LinearLayout.LayoutParams searchLp=new LinearLayout.LayoutParams(-1,dp(54));searchLp.bottomMargin=dp(8);content.addView(search,searchLp);
    LinearLayout filters=new LinearLayout(this);filters.setTag("cobra_multi_filters");String[] labels={"Favorites","Recent","All","Groups"},keys={"FAVORITES","RECENT","ALL","CATEGORIES"};
    for(int i=0;i<labels.length;i++){final int index=i;final String filter=keys[i];Button b=cobraTextButton(labels[i],true,()->{mCobraTvMultiFilterIndex=index;mCobraTvMultiFilter=filter;renderCobraMultiPicker(filter);cobraTvRefreshMultiFilterSelection();});b.setTag("cobra_multi_filter:"+i);b.setContentDescription(labels[i]+" Multi-View channels");filters.addView(b,new LinearLayout.LayoutParams(0,dp(52),1));}
    LinearLayout.LayoutParams filterLp=new LinearLayout.LayoutParams(-1,dp(52));filterLp.bottomMargin=dp(8);content.addView(filters,filterLp);
    android.widget.ListView list=new android.widget.ListView(this);list.setTag("cobra_multi_picker_list");list.setDividerHeight(0);list.setFastScrollEnabled(false);list.setItemsCanFocus(false);list.setFocusable(true);list.setFocusableInTouchMode(false);list.setChoiceMode(android.widget.ListView.CHOICE_MODE_SINGLE);
    list.setSelector(surface(0xff15263a,12,0xff41c8ef,2));content.addView(list,new LinearLayout.LayoutParams(-1,0,1));
    parent.addView(panel,new FrameLayout.LayoutParams(1,1));if(mPlayerChrome!=null)mPlayerChrome.setVisibility(View.GONE);cobraLayoutPlayerPanels();renderCobraMultiPicker("RECENT");
    panel.post(()->cobraTvFocusMultiFilter(1));
  }''')

    s=replace_member(s,'renderCobraMultiPicker',r'''  private void renderCobraMultiPicker(String filter){
    android.widget.ListView list=cobraTvMultiList();if(list==null)return;
    String resolved=filter==null?"RECENT":filter;boolean groups="CATEGORIES".equals(resolved);
    final ArrayList<String> names=new ArrayList<>();final ArrayList<Channel> channels=new ArrayList<>();
    if(groups){java.util.TreeSet<String> all=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);for(Channel c:mChannels)if(cobraChannelAllowed(c)&&c.group!=null&&!c.group.isEmpty())all.add(c.group);names.addAll(all);}
    else {for(Channel c:cobraMultiChannels(resolved))if(cobraChannelAllowed(c)&&mCobraTiles.get(c.id)==null)channels.add(c);}
    if(!groups&&channels.isEmpty()&&"RECENT".equals(resolved)){resolved="ALL";mCobraTvMultiFilterIndex=2;for(Channel c:cobraMultiChannels("ALL"))if(cobraChannelAllowed(c)&&mCobraTiles.get(c.id)==null)channels.add(c);}
    final String activeFilter=resolved;mCobraTvMultiFilter=activeFilter;mCobraTvMultiFilterIndex=cobraTvMultiFilterIndex(activeFilter);mCobraTvMultiRow=0;
    list.setAdapter(new android.widget.BaseAdapter(){
      public int getCount(){return groups?names.size():channels.size();}
      public Object getItem(int p){return groups?names.get(p):channels.get(p);}
      public long getItemId(int p){return p;}
      public View getView(int p,View old,android.view.ViewGroup host){
        TextView row=old instanceof TextView?(TextView)old:cobraText("",Color.WHITE,14);row.setTextColor(Color.WHITE);row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setPadding(dp(16),0,dp(12),0);row.setMaxLines(2);row.setFocusable(false);row.setClickable(false);
        row.setBackground(surface(0xff0d141d,10,0xff263748,1));row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(68)));
        if(groups)row.setText(names.get(p));else{Channel c=channels.get(p);GuideProgram current=cobraCurrentProgram(c);row.setText(c.name+"\n"+(current==null?cobraGuideStatus(c):current.title));}
        return row;
      }});
    list.setOnItemClickListener((parent,row,position,id)->{
      Object item=parent.getAdapter()==null?null:parent.getAdapter().getItem(position);
      if(item instanceof String){String group=(String)item;mCobraTvMultiFilter="GROUP:"+group;mCobraTvMultiFilterIndex=3;renderCobraMultiPicker(mCobraTvMultiFilter);mMain.post(()->cobraTvFocusMultiRow(0));}
      else if(item instanceof Channel)selectCobraMultiChannel((Channel)item);
    });
    list.setSelection(0);list.setItemChecked(0,true);cobraTvRefreshMultiFilterSelection();
  }''')

    s=replace_member(s,'renderCobraMultiPickerSearch',r'''  private void renderCobraMultiPickerSearch(String query){
    android.widget.ListView list=cobraTvMultiList();if(list==null)return;final String needle=query==null?"":query.trim().toLowerCase(Locale.ROOT);
    if(needle.isEmpty()){mCobraTvMultiFilter="RECENT";mCobraTvMultiFilterIndex=1;renderCobraMultiPicker("RECENT");return;}
    mCobraTvMultiFilter="SEARCH";mCobraTvMultiRow=0;final ArrayList<Channel> channels=new ArrayList<>();
    for(Channel c:mChannels){String name=c.name==null?"":c.name.toLowerCase(Locale.ROOT),group=c.group==null?"":c.group.toLowerCase(Locale.ROOT);if(cobraChannelAllowed(c)&&mCobraTiles.get(c.id)==null&&(name.contains(needle)||group.contains(needle)))channels.add(c);}
    list.setAdapter(new android.widget.BaseAdapter(){
      public int getCount(){return channels.size();}public Channel getItem(int p){return channels.get(p);}public long getItemId(int p){return p;}
      public View getView(int p,View old,android.view.ViewGroup host){Channel c=channels.get(p);TextView row=old instanceof TextView?(TextView)old:cobraText("",Color.WHITE,14);GuideProgram current=cobraCurrentProgram(c);
        row.setText(c.name+"\n"+(current==null?cobraGuideStatus(c):current.title));row.setTextColor(Color.WHITE);row.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);row.setPadding(dp(16),0,dp(12),0);row.setMaxLines(2);row.setFocusable(false);row.setClickable(false);row.setBackground(surface(0xff0d141d,10,0xff263748,1));row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(68)));return row;}});
    list.setOnItemClickListener((parent,row,position,id)->{Object item=parent.getAdapter()==null?null:parent.getAdapter().getItem(position);if(item instanceof Channel)selectCobraMultiChannel((Channel)item);});
    if(!channels.isEmpty()){list.setSelection(0);list.setItemChecked(0,true);}
  }''')

    # Compact TiviMate-inspired group/Favorites header: no full-width blue focus slab.
    s=replace_member(s,'cobraModeBrowserHeader',r'''  private void cobraModeBrowserHeader(LinearLayout parent,String name){
    LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(14),dp(3),dp(14),dp(3));
    int screen=getResources().getDisplayMetrics().widthPixels;int groupWidth=Math.min(dp(360),Math.max(dp(220),Math.round(screen*.34f)));
    Button group=cobraTextButton(name+"  ▾",cobraModeDark(),()->cobraToggleModeGroups());group.setTag("cobra_tv_grid_group");group.setSingleLine(true);group.setEllipsize(android.text.TextUtils.TruncateAt.END);group.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);group.setPadding(dp(16),0,dp(12),0);
    android.graphics.drawable.StateListDrawable groupStates=new android.graphics.drawable.StateListDrawable();
    groupStates.addState(new int[]{android.R.attr.state_focused},surface(cobraModeColor("panel"),14,cobraModeColor("accent"),2));
    groupStates.addState(new int[]{android.R.attr.state_selected},surface(cobraModeColor("panel"),14,cobraModeColor("accent"),1));
    groupStates.addState(new int[]{},surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));
    group.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(cobraAlpha(cobraModeColor("muted"),24)),groupStates,surface(Color.WHITE,14,Color.TRANSPARENT,0)));
    group.setContentDescription("Channel group "+name+". Select to change group.");
    row.addView(group,new LinearLayout.LayoutParams(groupWidth,dp(52)));row.addView(new View(this),new LinearLayout.LayoutParams(0,1,1));
    CobraIconButton source=cobraIcon("source","Choose playlist",cobraModeDark(),v->cobraOpenTvDirectory(true));source.setTag("cobra_tv_grid_source");row.addView(source,new LinearLayout.LayoutParams(dp(52),dp(52)));
    CobraIconButton search=cobraIcon("search","Search channels",cobraModeDark(),v->cobraShowChannelSearch());search.setTag("cobra_tv_grid_search");LinearLayout.LayoutParams searchLp=new LinearLayout.LayoutParams(dp(52),dp(52));searchLp.leftMargin=dp(8);row.addView(search,searchLp);
    parent.addView(row,new LinearLayout.LayoutParams(-1,dp(58)));
  }''')

    # Explicit guide header/time/EPG focus path.
    s=replace_member(s,'cobraRenderGridMode',r'''  private void cobraRenderGridMode(LinearLayout parent,ArrayList<Channel> channels){
    cobraModeBrowserHeader(parent,cobraModeGroupName());
    if(mCobraGuideWindow==0){long t=System.currentTimeMillis();mCobraGuideWindow=t-t%1800000L;}
    LinearLayout time=new LinearLayout(this);time.setGravity(Gravity.CENTER_VERTICAL);time.setPadding(dp(14),0,dp(14),0);
    CobraIconButton earlier=cobraIcon("back","Earlier programmes",cobraModeDark(),v->cobraMoveGuideTime(-1));earlier.setTag("cobra_tv_grid_time_back");time.addView(earlier,new LinearLayout.LayoutParams(dp(50),dp(50)));
    Button live=cobraTextButton("Now",cobraModeDark(),()->cobraMoveGuideTime(0));live.setTag("cobra_tv_grid_time_now");LinearLayout.LayoutParams nowLp=new LinearLayout.LayoutParams(dp(72),dp(50));nowLp.leftMargin=dp(8);time.addView(live,nowLp);
    TextView date=cobraText(new SimpleDateFormat("EEE, d MMM",Locale.getDefault()).format(new Date(mCobraGuideWindow)),cobraModeColor("muted"),12);mCobraModeDate=date;date.setSingleLine(true);date.setGravity(Gravity.CENTER);time.addView(date,new LinearLayout.LayoutParams(0,dp(50),1));
    CobraIconButton later=cobraIcon("next","Later programmes",cobraModeDark(),v->cobraMoveGuideTime(1));later.setTag("cobra_tv_grid_time_next");time.addView(later,new LinearLayout.LayoutParams(dp(50),dp(50)));
    if(mCobraModeLayout.browser[3]>=230)parent.addView(time,new LinearLayout.LayoutParams(-1,dp(52)));
    mCobraGuideRuler=new CobraGuideRuler();mCobraGuideRuler.setTag("cobra_tv_time_ruler");parent.addView(mCobraGuideRuler,new LinearLayout.LayoutParams(-1,dp(32)));
    if(channels.isEmpty()){cobraModeEmpty(parent,"No channels in this group.");return;}
    cobraInstallModeList(parent,new android.widget.ListView(this),new CobraModeAdapter(channels){public View getView(int p,View old,android.view.ViewGroup host){CobraBroadcastRow row=old instanceof CobraBroadcastRow?(CobraBroadcastRow)old:new CobraBroadcastRow();row.bind(getItem(p),p);return row;}});
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
      if(key==KeyEvent.KEYCODE_DPAD_UP){View menu=mCobraModeToolbar==null?null:mCobraModeToolbar.findViewWithTag("cobra_tv_toolbar_menu");if(menu!=null){menu.requestFocus();return true;}return true;}
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_time_now"))return true;cobraTvFocusGuideBody();return true;}
    }
    if(gridTime){
      if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvMoveGridTime(tag,-1);
      if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvMoveGridTime(tag,1);
      if(key==KeyEvent.KEYCODE_DPAD_UP)return cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_group");
      if(key==KeyEvent.KEYCODE_DPAD_DOWN){cobraTvFocusGuideBody();return true;}
    }
    if((tag.startsWith("cobra-channel:")||tag.startsWith("cobra-program:")||tag.startsWith("cobra-gap:"))&&key==KeyEvent.KEYCODE_DPAD_UP&&cobraTvGuideListPosition(focus)==0){
      if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_time_now"))return true;
      return cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_group");
    }
    if(("cobra_tv_toolbar_menu".equals(tag)||"cobra_mode_visuals".equals(tag))&&key==KeyEvent.KEYCODE_DPAD_DOWN)
      return cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_group");
    return false;
  }''')

    # TV wording only; preserve Multi-View engine behavior.
    begin=member(s,'beginMultiView')
    begin=begin.replace('toast("Play a channel first, then tap Multi-View");','toast("Play a channel first, then select Multi-View");')
    s=replace_member(s,'beginMultiView',begin)

    # Identity.
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103223 TV baseline')
    req(receipt.get('tv_hardening') is True and receipt.get('tv_target_abi')=='armeabi-v7a','Expected 2103223 TV hardening parent')
    req(receipt.get('mobile_parent_untouched') is True,'ARM64/mobile preservation marker missing')
    activity=shell/ACT;gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle):req(p.is_file(),'Missing '+str(p))
    before,after=patch_activity(activity)
    g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode');g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName');gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
      req(rel in receipt['files'],'Receipt missing '+rel);receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_native_remote_architecture=True,tv_player_header_focus_graph=True,
      tv_multiview_picker_focus_owner=True,tv_multiview_list_select_dispatch=True,
      tv_multiview_filters_remote=True,tv_multiview_groups_remote=True,
      tv_grid_compact_group_header=True,tv_grid_favorites_polished=True,tv_grid_time_focus_graph=True,
      tv_hardening_preserved=True,tv_cache_restore_off_main=True,tv_display_mode_switching_disabled=True,
      multiview_fullscreen_reversible=True,mobile_parent_untouched=True,native_engine_rebuilt=False,
      playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    java=activity.read_text()
    for token in (
      'cobra_tv_native_remote_2103224','cobraTvHandleMultiPickerKey','cobra_multi_filter:','list.performItemClick',
      'cobra_tv_player_header_favorite','cobra_tv_player_header_lock','cobra_tv_grid_time_now',
      'Channel group "+name+". Select to change group.','versionCode 2103224'
    ):req(token in (java+g),'2103224 source gate missing '+token)
    req('row.addView(group,new LinearLayout.LayoutParams(0,dp' not in java,'Full-width phone group bar remains')
    req('list.setItemsCanFocus(false)' in java,'Multi-View list still delegates focus to child buttons')

    Path('audit224').mkdir(exist_ok=True)
    Path('audit224/tv-native-remote-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,'marker':'cobra_tv_native_remote_2103224',
      'mobile_fold_untouched':True,'native_engine_rebuilt':False,
      'player_header_explicit_focus':True,'multiview_picker_single_focus_owner':True,
      'multiview_center_select_dispatch':True,'multiview_filters_remote':True,'multiview_groups_remote':True,
      'grid_group_compact':True,'favorites_header_polished':True,'grid_time_remote':True,
      'hardening_2103223_preserved':True,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103224 native-TV remote architecture applied over exact locked 2103223')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
