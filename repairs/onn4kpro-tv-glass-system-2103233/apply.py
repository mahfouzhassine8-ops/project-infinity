#!/usr/bin/env python3
"""2103233 RC13 — end-to-end lightweight TV glass system.

Parent: exact locked 2103232 RC12.

The locked glass mockups are the visual specification. This pass changes the
TV presentation layer only: static/translucent glass surfaces, unified cyan
focus language, restrained alpha/translation motion and no real-time blur.
Ambient Mode is retired on TV. Existing navigation, player, timeshift,
Multi-View, providers and ARMv7 native engine are preserved.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103233
OLD_VERSION=2103232
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Integrated-Drawer-RC12'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Glass-System-RC13'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v:raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)
def span_sig(text,sig):
    i=text.find(sig);req(i>=0,'Missing '+sig);b=text.find('{',i);req(b>=0,'No body '+sig)
    d=0;q=None;esc=line=block=False;j=b
    while j<len(text):
        c=text[j];n=text[j+1] if j+1<len(text) else ''
        if line:
            if c=='\n':line=False
        elif block:
            if c=='*' and n=='/':block=False;j+=1
        elif q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==q:q=None
        elif c=='/' and n=='/':line=True;j+=1
        elif c=='/' and n=='*':block=True;j+=1
        elif c in ('"',"'"):q=c
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return i,j+1
        j+=1
    raise RuntimeError('Unclosed '+sig)
def repl(text,sig,new):
    a,b=span_sig(text,sig);return text[:a]+new.rstrip()+text[b:]

HELPERS=r'''  private static final String COBRA_TV_GLASS_SYSTEM_BUILD="cobra_tv_glass_system_2103233";
  private static final int COBRA_TV_GLASS_ACCENT=0xff47d7ff;

  private int cobraTvGlassBuiltInColor(String mode,String key,int fallback){
    boolean light="light".equals(mode),oled="oled".equals(mode);
    if(light){
      if("background".equals(key))return 0xffedf4f8;
      if("rail".equals(key))return 0xf2f6fbff;
      if("panel".equals(key))return 0xe8ffffff;
      if("panel2".equals(key))return 0xf4ffffff;
      if("focus".equals(key))return 0xffd7edf7;
      if("accent".equals(key))return 0xff007fa9;
      if("accent_soft".equals(key))return 0xff2aa8cd;
      if("text".equals(key))return 0xff102235;
      if("muted".equals(key))return 0xff526b80;
      if("line".equals(key))return 0x805e7b91;
    }
    if("background".equals(key))return oled?Color.BLACK:0xff07111c;
    if("rail".equals(key))return oled?0xf2070d14:0xeb0a1624;
    if("panel".equals(key))return oled?0xeb0a111a:0xdf172737;
    if("panel2".equals(key))return oled?0xf20d1622:0xea203448;
    if("focus".equals(key))return 0xe62a536d;
    if("accent".equals(key))return COBRA_TV_GLASS_ACCENT;
    if("accent_soft".equals(key))return 0xff82e5ff;
    if("text".equals(key))return 0xfff4f8fb;
    if("muted".equals(key))return 0xffa2b4c6;
    if("line".equals(key))return 0x8c536f87;
    return fallback;
  }

  private android.graphics.drawable.Drawable cobraTvGlassBackdrop(){
    int bg=cobraThemeColor("background",mTheme.background),panel=cobraThemeColor("panel",mTheme.panel),accent=cobraThemeColor("accent",mTheme.accent);
    int mid=CobraPresentationEffects.blend(bg,panel,.28f),edge=CobraPresentationEffects.blend(bg,accent,.08f);
    return new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{edge,mid,bg});
  }

  private android.graphics.drawable.Drawable cobraTvGlassPanelSurface(int radius,boolean strong){
    int base=cobraThemeColor(strong?"panel2":"panel",strong?mTheme.panel2:mTheme.panel);
    return cobraPanelSurface(cobraAlpha(base,strong?238:218),Math.max(10,radius),cobraAlpha(cobraThemeColor("line",mTheme.line),205));
  }

  private android.graphics.drawable.Drawable cobraTvGlassRowSurface(int radius){
    int r=Math.max(10,radius),accent=cobraThemeColor("accent",mTheme.accent);
    android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
    states.addState(new int[]{android.R.attr.state_focused},cobraPanelSurface(cobraAlpha(cobraThemeColor("focus",mTheme.focus),242),r,accent));
    states.addState(new int[]{android.R.attr.state_selected},cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),236),r,cobraAlpha(accent,190)));
    states.addState(new int[]{android.R.attr.state_activated},cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),236),r,cobraAlpha(accent,190)));
    states.addState(new int[]{},cobraPanelSurface(cobraAlpha(cobraThemeColor("panel",mTheme.panel),210),r,cobraAlpha(cobraThemeColor("line",mTheme.line),185)));
    return new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(cobraAlpha(accent,34)),states,surface(Color.WHITE,r,Color.TRANSPARENT,0));
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes();s=before.decode()
    marker='  private static final String COBRA_TV_INTEGRATED_DRAWER_BUILD="cobra_tv_integrated_drawer_2103232";'
    req(s.count(marker)==1,'Exact locked RC12 marker missing');s=s.replace(marker,HELPERS+marker,1)

    s=repl(s,'  private int cobraThemeColor(String key, int fallback)',r'''  private int cobraThemeColor(String key, int fallback) {
    String mode=cobraEffectiveAppearanceMode();JSONObject palette=cobraAppearancePalette(mode);
    if(palette!=null){String encoded=palette.optString(key,"");if(encoded!=null&&!encoded.isEmpty())try{return android.graphics.Color.parseColor(encoded);}catch(IllegalArgumentException ignored){}}
    return cobraTvGlassBuiltInColor(mode,key,cobraBuiltInAppearanceColor(mode,key,fallback));
  }''')

    s=repl(s,'  private GradientDrawable cobraPanelSurface(int fill,int radius,int stroke)',r'''  private GradientDrawable cobraPanelSurface(int fill,int radius,int stroke) {
    int a=Color.alpha(fill);int top=Color.argb(a,Math.min(255,Color.red(fill)+10),Math.min(255,Color.green(fill)+12),Math.min(255,Color.blue(fill)+15));
    int bottom=Color.argb(a,Math.max(0,Color.red(fill)-5),Math.max(0,Color.green(fill)-6),Math.max(0,Color.blue(fill)-7));
    GradientDrawable drawable=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{top,fill,bottom});
    drawable.setCornerRadius(dp(Math.max(10,radius)));drawable.setStroke(dp(1),stroke);return drawable;
  }''')

    s=repl(s,'  private StateListDrawable focusSurface(int normal, int focused, int radius)',r'''  private StateListDrawable focusSurface(int normal,int focused,int radius) {
    int r=Math.max(10,radius),accent=cobraThemeColor("accent",mTheme.accent);StateListDrawable state=new StateListDrawable();
    state.addState(new int[]{android.R.attr.state_focused},cobraPanelSurface(cobraAlpha(focused,240),r,accent));
    state.addState(new int[]{android.R.attr.state_pressed},cobraPanelSurface(cobraAlpha(focused,245),r,cobraAlpha(accent,220)));
    state.addState(new int[]{android.R.attr.state_selected},cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),232),r,cobraAlpha(accent,175)));
    state.addState(new int[]{},cobraPanelSurface(cobraAlpha(normal,214),r,cobraAlpha(cobraThemeColor("line",mTheme.line),190)));
    return state;
  }''')

    s=repl(s,'  private android.graphics.drawable.Drawable cobraPressSurface(boolean dark)',r'''  private android.graphics.drawable.Drawable cobraPressSurface(boolean dark) {
    return cobraTvGlassRowSurface(12);
  }''')

    s=repl(s,'  private int cobraModeColorBuiltin(String name)',r'''  private int cobraModeColorBuiltin(String name){
    if("accent".equals(name))return cobraThemeColor("accent",mTheme.accent);
    if("text".equals(name))return cobraThemeColor("text",mTheme.text);
    if("muted".equals(name))return cobraThemeColor("muted",mTheme.muted);
    if("line".equals(name))return cobraThemeColor("line",mTheme.line);
    if("rail".equals(name))return cobraThemeColor("rail",mTheme.rail);
    if("panel".equals(name))return cobraThemeColor("panel",mTheme.panel);
    return cobraThemeColor("background",mTheme.background);
  }''')

    s=repl(s,'  private android.graphics.drawable.Drawable cobraModeSurface(int radius,boolean raised)',r'''  private android.graphics.drawable.Drawable cobraModeSurface(int radius,boolean raised){
    return cobraTvGlassRowSurface(Math.max(8,radius));
  }''')
    s=repl(s,'  private android.graphics.drawable.Drawable cobraSheetDetailSurface(int radius)',r'''  private android.graphics.drawable.Drawable cobraSheetDetailSurface(int radius){
    return cobraTvGlassRowSurface(Math.max(12,radius));
  }''')

    # Retire dynamic Ambient Mode on the TV variant.
    s=repl(s,'  private int cobraAmbientMode()',r'''  private int cobraAmbientMode(){return CobraPresentationEffects.OFF;}''')
    s=repl(s,'  private void cobraAmbientSurface(View view,int tint,int mode,int radius,boolean night)',r'''  private void cobraAmbientSurface(View view,int tint,int mode,int radius,boolean night){
    // Retired on TV: static glass surfaces replace dynamic Ambient layering.
  }''')
    s=repl(s,'  private void cobraRefreshLiveAmbientSurfaces(int mode,boolean live,int tint)',r'''  private void cobraRefreshLiveAmbientSurfaces(int mode,boolean live,int tint){
    // Retired on TV: no per-surface Ambient invalidation.
  }''')
    s=repl(s,'  private void cobraRefreshAmbient()',r'''  private void cobraRefreshAmbient(){
    // Deliberately no-op: the TV glass system is always active.
  }''')
    s=repl(s,'  private void cobraRefreshVisualEffects()',r'''  private void cobraRefreshVisualEffects(){
    if(mCobraEffects==null)return;boolean visible=cobraVisualEffectsAllowed()&&!mInPictureInPicture&&!mBackgroundStopped;
    mCobraEffects.updateStatus(mPlayerChrome,cobraVisualPulseState(mPlayer),visible&&!mCobraPlayerLocked&&mCobraActionSheet==null&&mCobraPlayerDrawer==null&&mCobraMultiPicker==null);
    mCobraEffects.updateStatus(mCobraPreviewHost,cobraVisualPulseState(mCobraPreviewPlayer),visible&&mPlayerOverlay==null&&mMultiOverlay==null);
  }''')
    s=repl(s,'  private void cobraAddPresentationSettings(LinearLayout list)',r'''  private void cobraAddPresentationSettings(LinearLayout list){
    Button greeting=action("CUSTOM GREETING");greeting.setTag("cobra_custom_greeting");greeting.setOnClickListener(v->cobraEditGreeting());
    list.addView(greeting,new LinearLayout.LayoutParams(-1,dp(56)));
  }''')
    s=repl(s,'  private void cobraShowAmbientMode()',r'''  private void cobraShowAmbientMode(){toast("Ambient Mode is retired on TV. Lightweight Glass UI is always active.");}''')
    s=repl(s,'  private void cobraShowVisualMenu(View anchor)',r'''  private void cobraShowVisualMenu(View anchor){
    LinearLayout rows;mCobraNextSheetAnchor=anchor;try{rows=cobraOpenSheet("Visual settings","Lightweight Glass UI is always active.","visual-settings");}finally{mCobraNextSheetAnchor=null;}
    cobraInfoText(rows,"Night Cinema");boolean night=mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false);
    for(int i=0;i<2;i++){final boolean enabled=i==1;cobraAddDetail(rows,"visuals",enabled?"On":"Off",null,"cobra-visual-night:"+(enabled?"on":"off"),night==enabled,()->{
      mPrefs.edit().putBoolean(CobraPresentationEffects.NIGHT,enabled).apply();if(mPlayerOverlay!=null)cobraBuildPlayerChrome();cobraRefreshVisualEffects();cobraRefreshModeDetails();
    });}
  }''')

    s=repl(s,'  private void cobraApplyNightCinema(View header,View footer,View pause)',r'''  private void cobraApplyNightCinema(View header,View footer,View pause){
    if(header==null||footer==null)return;boolean night=cobraNightCinemaActive();int accent=cobraThemeColor("accent",mTheme.accent);
    if(night){
      header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{cobraAlpha(accent,42),0xe8000000,0xb0000000,Color.TRANSPARENT}));
      footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{Color.TRANSPARENT,0xc8000000,0xef000000,cobraAlpha(accent,34)}));
      if(pause!=null)pause.setBackground(cobraTvGlassRowSurface(18));if(mCobraPlayerSchedule!=null)mCobraPlayerSchedule.setVisibility(View.GONE);if(mCobraPlayerUpcoming!=null)mCobraPlayerUpcoming.setVisibility(View.GONE);return;
    }
    header.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),228),cobraAlpha(cobraThemeColor("panel",mTheme.panel),176),Color.TRANSPARENT}));
    footer.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{Color.TRANSPARENT,cobraAlpha(cobraThemeColor("panel",mTheme.panel),184),cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),238)}));
    if(pause!=null)pause.setBackground(cobraTvGlassRowSurface(18));
  }''')

    s=repl(s,'  private void cobraRestyleGuide()',r'''  private void cobraRestyleGuide(){
    if(mRoot!=null)mRoot.setBackgroundColor(Color.TRANSPARENT);if(mStage!=null)mStage.setBackgroundColor(Color.TRANSPARENT);
    if(mHeader!=null)mHeader.setTextColor(cobraModeColor("text"));if(mStatus!=null)mStatus.setTextColor(cobraModeColor("muted"));
    if(mCobraGuideShell==null)return;mCobraGuideShell.setBackground(cobraTvGlassBackdrop());mCobraGuideBrowser.setBackgroundColor(Color.TRANSPARENT);
    mCobraGuideDirectory.setBackground(cobraTvGlassPanelSurface(18,true));mCobraGuideDetails.setBackground(cobraTvGlassPanelSurface(18,false));
    if(mCobraModeToolbar!=null)mCobraModeToolbar.setBackground(cobraTvGlassPanelSurface(16,false));if(mCobraModeRail!=null)mCobraModeRail.setBackground(cobraTvGlassPanelSurface(16,false));
    mCobraGuideNowLabel.setTextColor(cobraModeColor("text"));mCobraGuideNextLabel.setTextColor(cobraModeColor("muted"));mCobraModeDescription.setTextColor(cobraModeColor("muted"));mCobraModeEyebrow.setTextColor(cobraModeColor("accent"));
    cobraBuildModeChrome();vtheme().paint(mCobraGuideShell,"guide.shell");vtheme().tree(mCobraGuideDirectory,"guide.directory");vtheme().tree(mCobraGuideDetails,"guide.details");
  }''')

    # Guide toolbar keeps navigation but removes the now-retired visual/Ambient button.
    s=repl(s,'  private void cobraBuildModeChrome()',r'''  private void cobraBuildModeChrome(){
    if(mCobraModeToolbar==null)return;boolean dark=true;mCobraModeToolbar.removeAllViews();mCobraModeToolbar.setBackground(cobraTvGlassPanelSurface(16,false));
    LinearLayout title=new LinearLayout(this);title.setOrientation(LinearLayout.VERTICAL);title.setGravity(Gravity.CENTER_VERTICAL);title.setPadding(dp(18),0,0,0);
    mCobraModeTitle=cobraText(cobraModeName(mCobraGuideStyle),cobraModeColor("text"),19);mCobraModeTitle.setTypeface(vtheme().font("cobra.cobraBuildModeChrome.styles.1",Typeface.create("sans-serif-medium",0)));mCobraModeTitle.setSingleLine(true);
    mCobraModeSub=cobraText("COBRA LIVE",cobraModeColor("muted"),10);mCobraModeSub.setSingleLine(true);mCobraModeSub.setLetterSpacing(.10f);title.addView(mCobraModeTitle);title.addView(mCobraModeSub);title.setClickable(false);title.setFocusable(false);mCobraModeToolbar.addView(title,new LinearLayout.LayoutParams(0,-1,1));
    mCobraModeRail.removeAllViews();mCobraModeRail.setBackground(cobraTvGlassPanelSurface(16,false));String[] icons={"search","guide","favorite","recent","multi","more"},labels={"Search","Groups","Favorites","Recent","Views","Menu"};
    for(int i=0;i<icons.length;i++){final int action=i;CobraIconButton b=cobraIcon(icons[i],labels[i],dark,v->{if(action==0)cobraShowChannelSearch();else if(action==1)cobraToggleModeGroups();else if(action==2)selectCobraCategory("FAVORITES");else if(action==3)selectCobraCategory("RECENT");else if(action==4)showCobraViewModeMenu();else toggleCobraDrawer();});mCobraModeRail.addView(b,new LinearLayout.LayoutParams(-1,dp(48)));}
    mCobraModeFooter.removeAllViews();mCobraModeFooter.setBackground(cobraTvGlassPanelSurface(16,false));String[] fi={"play","guide","search","multi"},fl={"Live","Groups","Search","Views"};
    for(int i=0;i<fi.length;i++){final int a=i;CobraIconButton b=cobraIcon(fi[i],fl[i],dark,v->{if(a==0){mCobraGuideRoute="channels";cobraRenderGuideBrowser();}else if(a==1)cobraToggleModeGroups();else if(a==2)cobraShowChannelSearch();else showCobraViewModeMenu();});b.caption(fl[i]);mCobraModeFooter.addView(b,new LinearLayout.LayoutParams(0,-1,1));}
  }''')

    s=repl(s,'  private void cobraModeBrowserHeader(LinearLayout parent,String name)',r'''  private void cobraModeBrowserHeader(LinearLayout parent,String name){
    LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL|Gravity.RIGHT);row.setPadding(dp(12),dp(2),dp(12),dp(2));row.setBackground(cobraTvGlassPanelSurface(14,false));
    TextView context=cobraText(name,cobraModeColor("text"),12);context.setSingleLine(true);context.setEllipsize(android.text.TextUtils.TruncateAt.END);context.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);context.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));row.addView(context,new LinearLayout.LayoutParams(0,dp(48),1));
    CobraIconButton source=cobraIcon("source","Choose playlist",true,v->cobraOpenTvDirectory(true));source.setTag("cobra_tv_grid_source");row.addView(source,new LinearLayout.LayoutParams(dp(48),dp(48)));
    CobraIconButton search=cobraIcon("search","Search channels",true,v->cobraShowChannelSearch());search.setTag("cobra_tv_grid_search");LinearLayout.LayoutParams searchLp=new LinearLayout.LayoutParams(dp(48),dp(48));searchLp.leftMargin=dp(6);row.addView(search,searchLp);
    CobraIconButton settings=cobraIcon("settings","Settings",true,v->cobraTvOpenSettingsFromGuide());settings.setTag("cobra_tv_grid_settings");LinearLayout.LayoutParams settingsLp=new LinearLayout.LayoutParams(dp(48),dp(48));settingsLp.leftMargin=dp(6);row.addView(settings,settingsLp);
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(52));lp.leftMargin=dp(4);lp.rightMargin=dp(4);lp.bottomMargin=dp(5);parent.addView(row,lp);
  }''')

    s=repl(s,'  private void cobraRenderGridMode(LinearLayout parent,ArrayList<Channel> channels)',r'''  private void cobraRenderGridMode(LinearLayout parent,ArrayList<Channel> channels){
    cobraModeBrowserHeader(parent,cobraModeGroupName());if(mCobraGuideWindow==0){long t=System.currentTimeMillis();mCobraGuideWindow=t-t%1800000L;}
    LinearLayout time=new LinearLayout(this);time.setGravity(Gravity.CENTER_VERTICAL);time.setPadding(dp(12),0,dp(12),0);time.setBackground(cobraTvGlassPanelSurface(12,false));
    CobraIconButton earlier=cobraIcon("back","Earlier programmes",true,v->cobraMoveGuideTime(-1));earlier.setTag("cobra_tv_grid_time_back");time.addView(earlier,new LinearLayout.LayoutParams(dp(50),dp(50)));
    Button live=cobraTextButton("Now",true,()->cobraMoveGuideTime(0));live.setTag("cobra_tv_grid_time_now");LinearLayout.LayoutParams nowLp=new LinearLayout.LayoutParams(dp(72),dp(50));nowLp.leftMargin=dp(8);time.addView(live,nowLp);
    TextView date=cobraText(new SimpleDateFormat("EEE, d MMM",Locale.getDefault()).format(new Date(mCobraGuideWindow)),cobraModeColor("muted"),12);mCobraModeDate=date;date.setSingleLine(true);date.setGravity(Gravity.CENTER);time.addView(date,new LinearLayout.LayoutParams(0,dp(50),1));
    CobraIconButton later=cobraIcon("next","Later programmes",true,v->cobraMoveGuideTime(1));later.setTag("cobra_tv_grid_time_next");time.addView(later,new LinearLayout.LayoutParams(dp(50),dp(50)));
    if(mCobraModeLayout.browser[3]>=230){LinearLayout.LayoutParams tp=new LinearLayout.LayoutParams(-1,dp(52));tp.leftMargin=dp(4);tp.rightMargin=dp(4);parent.addView(time,tp);}
    mCobraGuideRuler=new CobraGuideRuler();mCobraGuideRuler.setTag("cobra_tv_time_ruler");parent.addView(mCobraGuideRuler,new LinearLayout.LayoutParams(-1,dp(32)));
    if(channels.isEmpty()){cobraModeEmpty(parent,"No channels in this group.");return;}
    cobraInstallModeList(parent,new android.widget.ListView(this),new CobraModeAdapter(channels){public View getView(int p,View old,android.view.ViewGroup host){CobraBroadcastRow row=old instanceof CobraBroadcastRow?(CobraBroadcastRow)old:new CobraBroadcastRow();row.bind(getItem(p),p);return row;}});
  }''')

    s=repl(s,'  private FrameLayout cobraPreviewPanel(Channel channel,boolean guide)',r'''  private FrameLayout cobraPreviewPanel(Channel channel,boolean guide) {
    if(mCobraPreviewHost!=null)return mCobraPreviewHost;FrameLayout host=new FrameLayout(this);mCobraPreviewHost=host;host.setTag("cobra_preview_host");host.setBackground(cobraTvGlassPanelSurface(18,true));
    host.setFocusable(false);host.setFocusableInTouchMode(false);host.setClickable(false);host.setLongClickable(false);host.setDescendantFocusability(android.view.ViewGroup.FOCUS_BLOCK_DESCENDANTS);
    mCobraPreviewTexture=new TextureView(this);mCobraPreviewTexture.setFocusable(false);mCobraPreviewTexture.setClickable(false);host.addView(mCobraPreviewTexture,new FrameLayout.LayoutParams(-1,-1));
    View rim=new View(this);rim.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);rim.setFocusable(false);rim.setClickable(false);rim.setBackground(surface(Color.TRANSPARENT,18,cobraAlpha(cobraThemeColor("accent",mTheme.accent),145),1));host.addView(rim,new FrameLayout.LayoutParams(-1,-1));
    TextView state=cobraText("PREVIEW",cobraThemeColor("text",mTheme.text),11);state.setTag("cobra_preview_label");state.setPadding(dp(10),dp(5),dp(10),dp(5));state.setBackground(cobraPanelSurface(cobraAlpha(cobraThemeColor("panel2",mTheme.panel2),220),12,cobraAlpha(cobraThemeColor("line",mTheme.line),190)));FrameLayout.LayoutParams statePos=new FrameLayout.LayoutParams(-2,dp(30),Gravity.TOP|Gravity.RIGHT);statePos.setMargins(dp(8),dp(8),dp(8),0);host.addView(cobraPulseStatus(state),statePos);
    TextView hint=cobraText("Select the current channel again to watch",cobraThemeColor("text",mTheme.text),11);hint.setGravity(Gravity.CENTER);hint.setPadding(dp(10),0,dp(10),0);hint.setBackground(cobraPanelSurface(cobraAlpha(cobraThemeColor("panel",mTheme.panel),225),12,cobraAlpha(cobraThemeColor("line",mTheme.line),180)));FrameLayout.LayoutParams hintPos=new FrameLayout.LayoutParams(-1,dp(34),Gravity.BOTTOM);hintPos.leftMargin=dp(6);hintPos.rightMargin=dp(6);hintPos.bottomMargin=dp(6);host.addView(hint,hintPos);cobraUpdatePreviewSubtitleState();return host;
  }''')

    # Drawer, channel playlist, sheets, player channels and Multi-View share the same surface language.
    s=once(s,'shield.setBackgroundColor(0x12000000);','shield.setBackgroundColor(0x0f000000);','drawer shield')
    s=once(s,'panel.setBackground(surface(cobraModeColor("rail"),20,cobraModeColor("line"),1));','panel.setBackground(cobraTvGlassPanelSurface(20,true));','drawer panel')
    s=once(s,'library.setPadding(dp(4),dp(4),dp(4),dp(4));library.setBackground(surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));','library.setPadding(dp(4),dp(4),dp(4),dp(4));library.setBackground(cobraTvGlassPanelSurface(14,false));','drawer library')
    s=once(s,'power.setTag("cobra_drawer_power");power.setMinimumHeight(dp(44));power.setBackground(surface(cobraModeColor("panel"),14,cobraModeColor("line"),1));','power.setTag("cobra_drawer_power");power.setMinimumHeight(dp(44));power.setBackground(cobraTvGlassRowSurface(14));','drawer power')

    s=repl(s,'    void bind(String label,String total,boolean active)',r'''    void bind(String label,String total,boolean active){
      name.setText(label);count.setText(total);name.setTextColor(active?cobraModeColor("accent"):cobraModeColor("text"));count.setTextColor(cobraModeColor("muted"));
      setBackground(cobraTvGlassRowSurface(14));setSelected(active);setContentDescription(label+(total.isEmpty()?"":", "+total));setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(62)));
    }''')
    s=repl(s,'  private android.graphics.drawable.Drawable cobraTvMultiRowSurface()',r'''  private android.graphics.drawable.Drawable cobraTvMultiRowSurface(){return cobraTvGlassRowSurface(12);}''')

    s=once(s,'scrim.setBackgroundColor(0x77000000);','scrim.setBackgroundColor(0x26000000);','playlist scrim')
    s=once(s,'panel.setBackgroundColor(cobraModeColor("rail"));panel.setPadding(dp(14),dp(12),dp(14),dp(12));','panel.setBackground(cobraTvGlassPanelSurface(20,true));panel.setPadding(dp(14),dp(12),dp(14),dp(12));','playlist panel')
    s=once(s,'panel.setBackground(cobraPanelSurface(dark?("oled".equals(cobraEffectiveAppearanceMode())?vtheme().color("cobra.cobraOpenSheet.colors.2",0xfc000000):vtheme().color("cobra.cobraOpenSheet.colors.3",0xf7080b11)):cobraAlpha(cobraThemeColor("panel",mTheme.panel),250),22,\n        dark?vtheme().color("cobra.cobraOpenSheet.colors.4",0xff344359):cobraThemeColor("line",mTheme.line)));panel.setElevation(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.5",14)));','panel.setBackground(cobraTvGlassPanelSurface(22,true));panel.setElevation(dp(10));','sheet panel')
    s=once(s,'panel.setTag("cobra_player_channel_drawer");panel.setBackground(cobraPanelSurface(vtheme().color("cobra.showCobraPlayerDrawer.colors.1",0xfc080b11),0,0xff293244));panel.setElevation(dp(vtheme().dimension("cobra.showCobraPlayerDrawer.dimensions.1",12)));','panel.setTag("cobra_player_channel_drawer");panel.setBackground(cobraTvGlassPanelSurface(20,true));panel.setElevation(dp(10));','player drawer panel')
    s=once(s,'panel.setTag("cobra_multi_picker");panel.setBackground(cobraPanelSurface(0xfc080b11,0,0xff293244));panel.setElevation(dp(12));','panel.setTag("cobra_multi_picker");panel.setBackground(cobraTvGlassPanelSurface(20,true));panel.setElevation(dp(10));','multi picker panel')
    s=once(s,'search.setBackground(cobraPanelSurface(0xff101722,12,0xff33465b));','search.setBackground(cobraTvGlassRowSurface(12));','multi picker search')

    # Avoid repeat 20K group scans in player-channel and Multi-View group menus.
    s=once(s,'if(groups){java.util.TreeSet<String> g=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);for(Channel c:mChannels)if(cobraChannelAllowed(c)&&c.group!=null&&!c.group.isEmpty())g.add(c.group);names.addAll(g);}','if(groups){cobraTvEnsureGroupCache();names.addAll(mCobraTvGroupCacheGroups.keySet());}','player group cache')
    s=once(s,'if(groups){java.util.TreeSet<String> all=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);for(Channel c:mChannels)if(cobraChannelAllowed(c)&&c.group!=null&&!c.group.isEmpty())all.add(c.group);names.addAll(all);}','if(groups){cobraTvEnsureGroupCache();names.addAll(mCobraTvGroupCacheGroups.keySet());}','multiview group cache')

    # Static glass backdrop at shell construction.
    s=once(s,'frame.setBackgroundColor(cobraThemeColor("background", mTheme.background));','frame.setBackground(cobraTvGlassBackdrop());','shell frame')
    s=once(s,'mCobraBrowseBackground.setBackgroundColor(cobraThemeColor("background", mTheme.background));','mCobraBrowseBackground.setBackground(cobraTvGlassBackdrop());','browse background')
    s=once(s,'mRail.setBackground(surface(cobraAlpha(cobraThemeColor("rail", mTheme.rail), 244), 0, cobraThemeColor("line", mTheme.line), 1));','mRail.setBackground(cobraTvGlassPanelSurface(16,true));','legacy rail glass')

    # Remove on-screen hamburger ownership across TV. Back/Menu remain the drawer controls.
    s=repl(s,'  private void clearStage(String title)',r'''  private void clearStage(String title) {
    mHeader.setCompoundDrawablesRelative(null,null,null,null);mCobraSmartWatchlist=false;mCobraNavigation.advance();mCobraStageTitle=title;cobraRememberModeScroll();
    mHeader.setVisibility(View.VISIBLE);mStatus.setVisibility(View.VISIBLE);mHeader.setClickable(false);mHeader.setFocusable(false);mHeader.setOnClickListener(null);mHeader.setTag(null);mHeader.setContentDescription(title);
    mStage.setPadding(dp(vtheme().dimension("cobra.clearStage.dimensions.1",12)),dp(vtheme().dimension("cobra.clearStage.dimensions.2",10)),dp(vtheme().dimension("cobra.clearStage.dimensions.3",12)),dp(vtheme().dimension("cobra.clearStage.dimensions.4",12)));
    while(mStage.getChildCount()>2)mStage.removeViewAt(2);mHeader.setText(title);cobraRestoreSmartScreenPosition();
  }''')
    s=once(s,'''    if(mHeader!=null){
      mHeader.setText("☰  COBRA • SETTINGS");
      mHeader.setClickable(true);mHeader.setFocusable(true);
      mHeader.setContentDescription("Open Cobra navigation drawer");
      mHeader.setTag("cobra_settings_drawer_header");
      mHeader.setOnClickListener(v->toggleCobraDrawer());
    }''','''    if(mHeader!=null){mHeader.setText("COBRA • SETTINGS");mHeader.setClickable(false);mHeader.setFocusable(false);mHeader.setOnClickListener(null);mHeader.setTag(null);mHeader.setContentDescription("Cobra Settings");}''','settings hamburger')

    # Cyan outline, not large scaling, carries focus.
    s=once(s,'v.setScaleX(focused?1.045f:1f);v.setScaleY(focused?1.045f:1f);v.setAlpha(focused?1f:.95f);','v.setScaleX(focused?1.012f:1f);v.setScaleY(focused?1.012f:1f);v.setAlpha(1f);','focus motion')

    s=repl(s,'  private boolean cobraTvHandleGuideKey(KeyEvent event)',r'''  private boolean cobraTvHandleGuideKey(KeyEvent event){
    if(event.getAction()!=KeyEvent.ACTION_DOWN||mCobraGuideShell==null||!mCobraGuideShell.isAttachedToWindow()||mPlayerOverlay!=null||mMultiOverlay!=null||cobraTvTransientRoot()!=null)return false;
    int key=event.getKeyCode();View focus=getCurrentFocus();Object raw=focus==null?null:focus.getTag();String tag=raw instanceof String?(String)raw:"";if(key==KeyEvent.KEYCODE_MENU){toggleCobraDrawer();return true;}
    boolean gridHeader=tag.startsWith("cobra_tv_grid_")&&!tag.startsWith("cobra_tv_grid_time"),gridTime=tag.startsWith("cobra_tv_grid_time");
    if(gridHeader){if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvMoveGridHeader(tag,-1);if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvMoveGridHeader(tag,1);if(key==KeyEvent.KEYCODE_DPAD_UP)return true;if(key==KeyEvent.KEYCODE_DPAD_DOWN){if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_time_now"))return true;cobraTvFocusGuideBody();return true;}}
    if(gridTime){if(key==KeyEvent.KEYCODE_DPAD_LEFT)return cobraTvMoveGridTime(tag,-1);if(key==KeyEvent.KEYCODE_DPAD_RIGHT)return cobraTvMoveGridTime(tag,1);if(key==KeyEvent.KEYCODE_DPAD_UP){if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_search"))return true;return cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_settings");}if(key==KeyEvent.KEYCODE_DPAD_DOWN){cobraTvFocusGuideBody();return true;}}
    if((tag.startsWith("cobra-channel:")||tag.startsWith("cobra-program:")||tag.startsWith("cobra-gap:"))&&key==KeyEvent.KEYCODE_DPAD_UP&&cobraTvGuideListPosition(focus)==0){if(cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_time_now"))return true;return cobraTvFocusTagged(mCobraGuideBrowser,"cobra_tv_grid_search");}
    return false;
  }''')

    # Gates: preserve behavior; Ambient is no longer exposed or dynamically rendered.
    req('AMBIENT MODE  •' not in s,'Ambient setting still exposed')
    req('Visual settings: Ambient Mode' not in s,'Guide Ambient button survived')
    req('COBRA_TV_GLASS_SYSTEM_BUILD="cobra_tv_glass_system_2103233"' in s,'Glass marker missing')
    req('startCobraPreview(mGuidePreviewChannel)' in s,'Mini-player preview path lost')
    req('cobra_tv_integrated_drawer_2103232' in s,'RC12 drawer marker lost')
    req('cobra_tv_grid_settings' in s,'Search/Settings contract lost')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103232 RC12 parent')
    req(receipt.get('tv_drawer_compact_integrated') is True and receipt.get('tv_live_flow')=='drawer-live-tv-groups-grid','Expected locked RC12 integrated drawer')
    req(receipt.get('tv_mini_player_adaptive_large') is True and receipt.get('tv_mini_player_preserved') is True,'Expected locked RC11 adaptive mini-player')
    req(receipt.get('tv_navigation_hierarchy')=='drawer-groups-grid-player' and receipt.get('tv_back_reverses_hierarchy') is True,'Expected protected TV navigation hierarchy')
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
      tv_glass_system=True,tv_glass_reference_locked=True,tv_glass_static_gradient=True,tv_glass_real_time_blur=False,
      tv_glass_drawer=True,tv_glass_playlist=True,tv_glass_guide=True,tv_glass_preview=True,
      tv_glass_sheets=True,tv_glass_player_surfaces=True,tv_glass_multiview=True,
      tv_ambient_mode_retired=True,tv_ambient_dynamic_layering=False,tv_ambient_setting_exposed=False,
      tv_group_cache_reused_player=True,tv_group_cache_reused_multiview=True,
      tv_focus_scale=1.012,tv_hamburger_removed=True,tv_grid_settings_next_to_search=True,
      tv_drawer_compact_integrated=True,tv_live_flow='drawer-live-tv-groups-grid',
      tv_navigation_hierarchy='drawer-groups-grid-player',tv_back_reverses_hierarchy=True,
      tv_mini_player_adaptive_large=True,tv_mini_player_preserved=True,tv_preview_engine_preserved=True,
      tv_multiview_row_focus_visible=True,tv_player_footer_unclipped=True,multiview_two_to_one_session_preserved=True,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit233').mkdir(exist_ok=True)
    Path('audit233/tv-glass-system-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':before,'activity_after_sha256':after,'marker':'cobra_tv_glass_system_2103233',
      'locked_mockups_visual_spec':True,'surfaces':['drawer','playlist','guide','preview','details','settings','sheets','player-channels','multiview','player-chrome'],
      'static_gradient_glass':True,'real_time_blur':False,'ambient_mode_retired':True,'dynamic_ambient_layering':False,
      'focus_scale':1.012,'group_cache_reused':['player-drawer','multiview-groups'],
      'navigation_preserved':'drawer-groups-grid-player','mini_player_preserved':True,'multiview_preserved':True,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,'mobile_fold_untouched':True,
      'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103233 end-to-end lightweight TV glass system applied over exact locked 2103232 RC12')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
