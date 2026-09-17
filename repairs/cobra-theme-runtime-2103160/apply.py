#!/usr/bin/env python3
"""Generate a source-site visual resource catalog over immutable 2103159.
Only literal visual resources and enumerated UI adapters are changed; no player algorithm.
"""
from pathlib import Path
import argparse, hashlib, json, re, os
ROOT=Path(__file__).resolve().parent
BASE='257a49d742890acf0c7d3e0220bded5a8aa80c57'
ACT='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
SPLASH='tools/android/packaging/xbmc/src/Splash.java.in'
HASHES={ACT:'e5081d9bf28e3cb38db40de9e9bbbbfb2797e492f10d9aa6e387f9c819d93429',SPLASH:'740aa927b312b4782fc2f1c295baf770eb8bffc824b0b10725ff6f87765ccba0'}
def sha(b):return hashlib.sha256(b.encode() if isinstance(b,str) else b).hexdigest()
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Anchor not unique: '+a[:150])
 return s.replace(a,b,1)
def mask(s):
 # Lexical mask retains positions, braces and identifiers but erases comments/strings.
 return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',lambda m:' '.join('' for _ in range(len(m.group())+1)),s)
def members(s):
 code=mask(s);start=code.index('{',code.index('class '));depth=1;begin=start+1;opened=None
 for i in range(start+1,len(code)):
  c=code[i]
  if c=='{':
   if depth==1:opened=i
   depth+=1
  elif c=='}':
   depth-=1
   if depth==1 and opened is not None:
    header=code[begin:opened].strip();cl=re.search(r'\bclass\s+(\w+)',header)
    m=re.search(r'(\w+)\s*\([^{};]*\)\s*(?:throws[^{}]*)?$',header)
    name=cl.group(1) if cl else m.group(1) if m else 'field'+str(s[:begin].count('\n')+1)
    yield begin,i+1,name,bool(re.search(r'\bstatic\b',header)),header
    begin=i+1;opened=None
   if depth==0:break
  elif c==';' and depth==1:begin=i+1

def method_span(s,name):
 found=[(a,b) for a,b,n,static,h in members(s) if n==name and not re.search(r'\bclass\s',h)]
 if len(found)!=1:raise ValueError('Expected one member '+name+', got '+str(len(found)))
 return found[0]

def instrument(s,namespace):
 edits=[];catalog=[]
 for a,b,member,static,header in members(s):
  if static or member in ('StateMachine','cobraReadEpgCache','cobraWriteEpgCache','dp','chooserDp','vtheme','cobraThemeColor','cobraModeColor','cobraEffectiveAppearanceMode','cobraBuiltInAppearanceColor','installCobraUiPackage','showLegacyInfinityExperienceChooser','loadExperienceTheme','showExperienceCardSettings','launchInfinityExperience','startXBMC','onCreate','onDestroy','onResume','onPause','onStop','onStart','onConfigurationChanged','onPictureInPictureModeChanged'):
   continue
  raw=s[a:b];code=mask(raw);counts={}
  def add(start,end,kind,fallback,expr):
   n=counts.get(kind,0)+1;counts[kind]=n;key=f'{namespace}.{member}.{kind}.{n}'
   edits.append((a+start,a+end,expr(key)))
   catalog.append({'key':key,'group':kind,'member':member,'line':s[:a+start].count('\n')+1,'default':fallback})
  # Scope is visual resource literals only, not decoder values, intervals, flags or routing IDs.
  for m in re.finditer(r'\b(?:chooserDp|dp)\(\s*(\d+)\s*\)',code):
   value=int(m.group(1))
   if value>2048:continue
   start,end=m.span(1);add(start,end,'dimensions',value,lambda key,v=value:f'vtheme().dimension("{key}",{v})')
  for m in re.finditer(r'(?<![\w.])0[xX][0-9a-fA-F]{8}(?![0-9a-fA-F\w])|(?:(?:android\.graphics\.)?Color\.(?:WHITE|BLACK|TRANSPARENT))',code):
   literal=raw[m.start():m.end()]
   # Bit masks/alpha composition operands are implementation math, not independent colors.
   if re.search(r'[&|^]\s*$',code[:m.start()]) or re.match(r'\s*[&|^]',code[m.end():]):continue
   add(m.start(),m.end(),'colors',literal,lambda key,v=literal:f'vtheme().color("{key}",{v})')
  # Only literal UI labels. Dynamic health/provider data and internal IDs stay untouched.
  for m in re.finditer(r'\b(?:text|cobraText|action|cobraTextButton|chooserText|chooserStyledText|setTitle)\(\s*("(?:\\.|[^"\\])+"\s*)',raw):
   if code[m.start():m.start()+3].strip()=='':continue
   start,end=m.span(1);literal=m.group(1)
   add(start,end,'copy',literal,lambda key,v=literal:f'vtheme().copy("{key}",{v})')
  for method,low,high in [('setLetterSpacing',-.02,.25),('setTextSize',8,96)]:
   for m in re.finditer(r'\.'+method+r'\(\s*([0-9]*\.?[0-9]+f?)\s*\)',code):
    start,end=m.span(1);literal=raw[start:end];add(start,end,'numbers',literal,lambda key,v=literal,lo=low,hi=high:f'vtheme().number("{key}",{v},{lo}f,{hi}f)')
  for m in re.finditer(r'\b(?:android\.graphics\.)?Typeface\.create\(',code):
   begin=m.start();at=m.end();depth=1
   while at<len(code) and depth:
    if code[at]=='(':depth+=1
    elif code[at]==')':depth-=1
    at+=1
   literal=raw[begin:at]
   if depth:raise ValueError('Unclosed Typeface expression')
   add(begin,at,'styles',literal,lambda key,v=literal:f'vtheme().font("{key}",{v})')
  for m in re.finditer(r'\.setDuration\(\s*(\d+)\s*\)',code):
   start,end=m.span(1);literal=raw[start:end];add(start,end,'numbers',literal,lambda key,v=literal:f'vtheme().motion("{key}",{v})')
 # Exact edit bounds must never overlap, even with nested expression candidates.
 edits.sort();last=-1
 for a,b,_ in edits:
  if a<last:raise ValueError('Overlapping generated visual edits')
  last=b
 out=s
 for a,b,new in reversed(edits):out=out[:a]+new+out[b:]
 # Independent byte-reversal proof for every generated substitution.
 reverse=out;offset=0
 for a,b,new in edits:
  pos=a+offset
  assert reverse[pos:pos+len(new)]==new
  reverse=reverse[:pos]+s[a:b]+reverse[pos+len(new):]
 assert reverse==s
 return out,catalog

def adapt_activity(before):
 s=before;changes=[]
 def change(name,fn):
  nonlocal s
  a,b=method_span(s,name);s=s[:a]+fn(s[a:b])+s[b:];changes.append(name)
 # Asset slots in existing Canvas renderers: no view/player replacement.
 s=once(s,'      int save=c.save();c.scale(getWidth()/40f,getHeight()/40f);','      if(vtheme().draw(c,"drawer.badge",0,0,getWidth(),getHeight(),"contain"))return;\n      int save=c.save();c.scale(getWidth()/40f,getHeight()/40f);')
 s=once(s,'      int save=canvas.save();canvas.translate(cx-dp(12),cy-dp(12));','''      if(vtheme().draw(canvas,getTag() instanceof String&&((String)getTag()).startsWith("cobra-drawer-icon:")?"drawer.icon."+((String)getTag()).substring(18).toLowerCase(java.util.Locale.ROOT).replace(" ","_"):"icon."+glyph,cx-dp(12),cy-dp(12),cx+dp(12),cy+dp(12),"contain")){
        if(!caption.isEmpty()){paint.reset();paint.setAntiAlias(true);paint.setColor(ink);paint.setTextSize(dp(10));paint.setTextAlign(android.graphics.Paint.Align.CENTER);canvas.drawText(caption,cx,getHeight()-dp(5),paint);}return;
      }
      int save=canvas.save();canvas.translate(cx-dp(12),cy-dp(12));''')
 changes+=['CobraBrandMark.onDraw','CobraIconButton.onDraw']
 change('cobraBrandHeader',lambda b:once(b,'return header;','vtheme().tree(header,"drawer.header");header.setOnLongClickListener(v->{vtheme().manager(this);return true;});return header;'))
 change('toggleCobraDrawer',lambda b:once(b,'    shield.addView(panel,','''    if(vtheme().hasImage("drawer.footer")){
      View decoration=vtheme().art(this,"drawer.footer",100);panel.addView(decoration,new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("drawer.footer.height",100))));
    }
    vtheme().paint(panel,"drawer.panel");vtheme().tree(headerForVisuals(panel),"drawer.header");vtheme().tree(items,"drawer.items");vtheme().tree(footer,"drawer.power");
    shield.addView(panel,'''))
 change('toggleCobraDrawer',lambda b:once(b,'panel.addView(footer);', 'if(vtheme().hasImage("drawer.ribbon"))panel.addView(vtheme().art(this,"drawer.ribbon",96),new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("drawer.ribbon.height",96))));panel.addView(footer);'))
 change('cobraDrawerDestination',lambda b:once(b,'if(!mUi.destinationEnabled(destination))return;', 'if(!mUi.destinationEnabled(destination))return;label=vtheme().copy("drawer.label."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"),label);'))
 change('cobraDrawerDestination',lambda b:once(b,'parent.addView(row,','if(row.getChildCount()>0)row.getChildAt(0).setTag("cobra-drawer-icon:"+destination);vtheme().tree(row,"drawer.item."+destination.toLowerCase(java.util.Locale.ROOT).replace(" ","_"));parent.addView(row,'))
 change('cobraDrawerView',lambda b:once(b,'items.addView(row,','vtheme().tree(row,"drawer.item.view");items.addView(row,'))
 for name,var in [('text','view'),('cobraText','view'),('cobraTextButton','b'),('action','button'),('field','input')]:
  try:change(name,lambda b,n=name,v=var:once(b,'return '+v+';','vtheme().paint('+v+',"widget.'+n+'");return '+v+';'))
  except ValueError:
   # Fail closed if a known factory changed unexpectedly, never silently omit a requested surface.
   raise
 change('cobraSheetRow',lambda b:once(b,'return row;','vtheme().tree(row,"sheet.row");return row;'))
 change('cobraDetailRow',lambda b:once(b,'return row;','vtheme().tree(row,"sheet.detail");return row;'))
 change('cobraOpenSheet',lambda b:once(b,'return items;','vtheme().tree(panel,"sheet."+kind);return items;'))
 # Source shape/JSON/theme control reload does not dispose, stop or recreate any player.
 change('installCobraUiPackage',lambda b:once(b,'      try {','''      try {
        boolean visual=false;
        try(InputStream input=getContentResolver().openInputStream(uri);java.util.zip.ZipInputStream scan=new java.util.zip.ZipInputStream(new CobraVisualTheme.LimitedInput(input,64L*1024*1024))){
          java.util.zip.ZipEntry entry;int entries=0;long scanned=0;byte[] buffer=new byte[8192];
          while((entry=scan.getNextEntry())!=null){if(++entries>256)throw new java.io.IOException("Too many ZIP entries");
            if(entry.getName().equals("script.infinity.cobra.theme/resources/visual-theme.json")){visual=true;break;}
            int n;while((n=scan.read(buffer))!=-1){if(n==0||(scanned+=n)>64L*1024*1024)throw new java.io.IOException("ZIP scan limit exceeded");}
          }
        }
        if(visual){
          synchronized(CobraVisualTheme.STORE_LOCK){
            CobraVisualTheme installed=CobraVisualTheme.install(getApplicationContext(),getContentResolver().openInputStream(uri));
            CobraVisualRenderer.publish(installed,"Visual ZIP installed");
          }
          publishCobraUi(()->{toast("Visual theme installed. Reopen menus for layout changes; playback is not restarted.");if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&mPlayerOverlay==null&&mMultiOverlay==null){cobraRestyleGuide();cobraRenderGuideBrowser();}});
          return;
        }
'''))
 change('showSettings',lambda b:once(b,'    ScrollView settingsScroll', '''    Button visualControls=new Button(this);visualControls.setText("Theme controls · reset / rollback");visualControls.setAllCaps(false);visualControls.setTag("cobra-visual-theme-controls");visualControls.setOnClickListener(v->vtheme().manager(this));list.addView(visualControls,new LinearLayout.LayoutParams(-1,dp(56)));
    vtheme().tree(list,"settings");
    ScrollView settingsScroll'''))
 # Avoid theme replacement of this unthemed escape hatch in the renderer itself (tag exclusion).
 # Named chrome surfaces are separate from their video textures. Do not reparent a player.
 change('buildShell',lambda b:once(b,'    setContentView(frame);','    setContentView(frame);vtheme().tree(mRail,"rail");vtheme().paint(mStage,"screen");vtheme().paint(mHeader,"screen.header");vtheme().paint(mStatus,"screen.status");'))
 change('cobraLayoutGuide',lambda b:once(b,'    for(int i=0;i<views.length;i++)','    org.json.JSONObject custom=vtheme().guideLayout(mCobraGuideStyle);\n    if(CobraVisualGeometry.guide(custom,boxes,mCobraModeLayout.width,mCobraModeLayout.height,getResources().getConfiguration().fontScale)){mCobraModeLayout.columns=custom.optInt("columns",mCobraModeLayout.columns);mCobraModeLayout.channelWidth=custom.optInt("channel_width_dp",mCobraModeLayout.channelWidth);}\n    for(int i=0;i<views.length;i++)'))
 change('cobraRestyleGuide',lambda b:once(b,'    cobraBuildModeChrome();','    cobraBuildModeChrome();vtheme().paint(mCobraGuideShell,"guide.shell");vtheme().tree(mCobraGuideDirectory,"guide.directory");vtheme().tree(mCobraGuideDetails,"guide.details");'))
 change('cobraBuildPlayerChrome',lambda b:once(b,'    cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();','    vtheme().tree(chrome,"player.chrome");cobraRefreshProgrammeLabels();cobraUpdatePlaybackLabels();'))
 change('showCobraPlayerDrawer',lambda b:once(b,'cobraLayoutPlayerPanels();','cobraLayoutPlayerPanels();vtheme().tree(content,"player.channels");'))
 change('cobraRenderGuideBrowser',lambda b:once(b,'    cobraRestoreModeScroll();cobraRefreshModeDetails();','    cobraRestoreModeScroll();cobraRefreshModeDetails();vtheme().tree(mCobraGuideBrowser,"guide.browser");'))
 change('cobraFreshHealthSnapshot',lambda b:once(b,'root.put("ui_runtime",3);','root.put("ui_runtime",3);root.put("visual_theme_runtime",2);root.put("visual_theme",vtheme().description());'))
 # Framework dialogs keep their exact callbacks/actions; only the visual Builder is substituted.
 s=once(s,'  private int cobraModeColor(String name){','  private int cobraModeColor(String name){return vtheme().color("palette."+name,cobraModeColorBuiltin(name));}\n  private int cobraModeColorBuiltin(String name){')
 changes.append('cobraModeColor')
 s=s.replace('new AlertDialog.Builder(this)','new CobraVisualRenderer.DialogBuilder(this,vtheme(),"dialog")')
 # Shared controls/rows use the view style registry, not filesystem reads during rendering.
 helper='''
  private CobraVisualRenderer mVisualTheme;
  private CobraVisualRenderer vtheme(){if(mVisualTheme==null)mVisualTheme=new CobraVisualRenderer(this);return mVisualTheme.mode(cobraEffectiveAppearanceMode());}
  private View headerForVisuals(LinearLayout panel){return panel.getChildCount()>0?panel.getChildAt(0):panel;}
'''
 i=s.rfind('\n}');s=s[:i]+helper+s[i:]
 return s,changes

def adapt_splash(before):
 s=before
 # Carry forward run #11 text-fit repair on top of the immutable run #10 preimage.
 a,b=method_span(s,'chooserStyledText');block=s[a:b]
 block=once(block,'    text.setGravity(gravity);','    text.setPadding(0, 0, 0, 0);\n    text.setGravity(gravity);');s=s[:a]+block+s[b:]
 # Keep original startup routing and legacy chooser fallback intact.
 a,b=method_span(s,'showInfinityExperienceChooser');block=s[a:b]
 block=once(block,'    if (theme == null)','''    if(theme==null&&vtheme().installed()){
      try{org.json.JSONObject defaults=new org.json.JSONObject();defaults.put("schema",1);defaults.put("scope","infinity-experience-chooser");defaults.put("minimum_bridge",1);defaults.put("copy",new org.json.JSONObject());defaults.put("palette",new org.json.JSONObject());theme=new ExperienceTheme(defaults);}catch(Exception invalid){theme=null;}
    }
    if (theme == null)''')
 block=once(block,'    showStyledInfinityExperienceChooser(theme);','    showStyledInfinityExperienceChooser(resolveVisualExperienceTheme(theme));')
 s=s[:a]+block+s[b:]
 s=once(s,'      int w = getWidth(), h = getHeight();\n      canvas.drawColor(theme.background);','      if(vtheme().draw(canvas,"chooser.background",0,0,getWidth(),getHeight(),"cover"))return;\n      int w = getWidth(), h = getHeight();\n      canvas.drawColor(theme.background);')
 s=once(s,'      int w = getWidth(), h = getHeight(); float cx = w / 2f, cy = h / 2f;','      if(vtheme().draw(canvas,cobra?"chooser.mark.cobra":"chooser.mark.infinity",0,0,getWidth(),getHeight(),"contain"))return;\n      int w = getWidth(), h = getHeight(); float cx = w / 2f, cy = h / 2f;')
 a,b=method_span(s,'chooserExperienceCard');block=s[a:b]
 block=once(block,'    return card;','    vtheme().tree(card,infinity?"chooser.card.infinity":"chooser.card.cobra");return card;')
 block=once(block,'      card.setElevation(chooserDp(focused ? 9 : 3));','      card.setElevation(chooserDp(focused ? 9 : 3));vtheme().paint(card,infinity?"chooser.card.infinity":"chooser.card.cobra");')
 s=s[:a]+block+s[b:]
 a,b=method_span(s,'showStyledInfinityExperienceChooser');block=s[a:b]
 block=once(block,'    android.widget.FrameLayout root = new android.widget.FrameLayout(this);','    if(showVisualExperienceScene(theme))return;\n    android.widget.FrameLayout root = new android.widget.FrameLayout(this);')
 block=once(block,'    setContentView(root);','''    if(vtheme().hasImage("chooser.footer"))content.addView(vtheme().art(this,"chooser.footer",60),new android.widget.LinearLayout.LayoutParams(-1,chooserDp(vtheme().dimension("chooser.footer.height",60))));
    setContentView(root);''')
 block=once(block,'    infinity.setElevation(chooserDp(9));','    infinity.setElevation(chooserDp(9));vtheme().tree(root,"chooser");vtheme().whenReady(()->{if(!isFinishing())showInfinityExperienceChooser();});')
 s=s[:a]+block+s[b:]
 helper='''
  private CobraVisualRenderer mVisualTheme;
  private CobraVisualRenderer vtheme(){if(mVisualTheme==null)mVisualTheme=new CobraVisualRenderer(this);return mVisualTheme;}
  private boolean showVisualExperienceScene(ExperienceTheme theme){
    org.json.JSONObject scene=vtheme().scene("chooser");if(scene==null)return false;
    try{
      java.util.Map<String,View> slots=new java.util.LinkedHashMap<>();
      for(String experience:new String[]{"infinity","cobra"}){
        final String destination=experience.equals("infinity")?"infinity":"live";
        android.widget.TextView enter=chooserStyledText("ENTER "+experience.toUpperCase(java.util.Locale.ROOT),theme.text,18,true,android.view.Gravity.CENTER);
        enter.setFocusable(true);enter.setClickable(true);enter.setTag("experience-card-"+experience);enter.setContentDescription("Enter "+experience);enter.setOnClickListener(v->launchInfinityExperience(destination));
        enter.setBackground(chooserSurface(theme.background,experience.equals("infinity")?theme.infinityBorder:theme.cobraBorder,24));slots.put("enter."+experience,enter);
        android.widget.TextView settings=chooserStyledText("Settings",theme.text,14,false,android.view.Gravity.CENTER);settings.setFocusable(true);settings.setClickable(true);settings.setTag("experience-settings-"+experience);settings.setContentDescription(experience+" settings");settings.setOnClickListener(v->showExperienceCardSettings(destination));
        settings.setBackground(chooserSurface(theme.background,experience.equals("infinity")?theme.infinityBorder:theme.cobraBorder,16));slots.put("settings."+experience,settings);
      }
      int width=Math.round(getResources().getDisplayMetrics().widthPixels/getResources().getDisplayMetrics().density);
      View view=CobraVisualScene.build(this,vtheme(),scene,slots,width);if(view==null)return false;
      android.widget.FrameLayout root=new android.widget.FrameLayout(this);root.setTag("experience-themed-root");root.addView(new ExperienceBackdrop(theme),new android.widget.FrameLayout.LayoutParams(-1,-1));root.addView(view,new android.widget.FrameLayout.LayoutParams(-1,-1));
      root.setOnLongClickListener(v->{vtheme().manager(this);return true;});setContentView(root);slots.get("enter.infinity").requestFocus();vtheme().whenReady(()->{if(!isFinishing())showInfinityExperienceChooser();});return true;
    }catch(Exception failed){android.util.Log.w("CobraTheme","Custom chooser could not be laid out; using safe chooser",failed);return false;}
  }
  private ExperienceTheme resolveVisualExperienceTheme(ExperienceTheme fallback){
    try{
      org.json.JSONObject root=new org.json.JSONObject(),copy=new org.json.JSONObject(),colors=new org.json.JSONObject(),layout=new org.json.JSONObject();
      root.put("schema",1);root.put("scope","infinity-experience-chooser");root.put("minimum_bridge",1);root.put("copy",copy);root.put("palette",colors);root.put("layout",layout);
      copy.put("brand",vtheme().copy("chooser.label.brand",fallback.brand));
      copy.put("brand_tagline",vtheme().copy("chooser.label.brand_tagline",fallback.brandTagline));
      copy.put("title",vtheme().copy("chooser.label.title",fallback.title));
      copy.put("personalization",vtheme().copy("chooser.label.personalization",fallback.personalization));
      copy.put("infinity_title",vtheme().copy("chooser.label.infinity_title",fallback.infinityTitle));
      copy.put("infinity_subtitle",vtheme().copy("chooser.label.infinity_subtitle",fallback.infinitySubtitle));
      copy.put("cobra_title",vtheme().copy("chooser.label.cobra_title",fallback.cobraTitle));
      copy.put("cobra_subtitle",vtheme().copy("chooser.label.cobra_subtitle",fallback.cobraSubtitle));
      copy.put("footer_brand",vtheme().copy("chooser.label.footer_brand",fallback.footerBrand));
      copy.put("footer_tagline",vtheme().copy("chooser.label.footer_tagline",fallback.footerTagline));
      copy.put("initials",vtheme().copy("chooser.label.initials",fallback.initials));
      colors.put("background",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.background",fallback.background)));
      colors.put("background_glow",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.background_glow",fallback.backgroundGlow)));
      colors.put("text",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.text",fallback.text)));
      colors.put("muted",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.muted",fallback.muted)));
      colors.put("infinity_top",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.infinity_top",fallback.infinityTop)));
      colors.put("infinity_bottom",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.infinity_bottom",fallback.infinityBottom)));
      colors.put("infinity_border",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.infinity_border",fallback.infinityBorder)));
      colors.put("infinity_glow",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.infinity_glow",fallback.infinityGlow)));
      colors.put("cobra_top",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.cobra_top",fallback.cobraTop)));
      colors.put("cobra_bottom",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.cobra_bottom",fallback.cobraBottom)));
      colors.put("cobra_border",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.cobra_border",fallback.cobraBorder)));
      colors.put("cobra_glow",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.cobra_glow",fallback.cobraGlow)));
      colors.put("badge_fill",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.badge_fill",fallback.badgeFill)));
      colors.put("badge_border",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.badge_border",fallback.badgeBorder)));
      colors.put("horizon",String.format(java.util.Locale.ROOT,"#%08X",vtheme().color("chooser.palette.horizon",fallback.horizon)));
      layout.put("outer_padding_dp",vtheme().dimension("chooser.layout.outer_padding_dp",fallback.outerPadding));
      layout.put("card_radius_dp",vtheme().dimension("chooser.layout.card_radius_dp",fallback.cardRadius));
      layout.put("card_gap_dp",vtheme().dimension("chooser.layout.card_gap_dp",fallback.cardGap));
      layout.put("card_height_dp",vtheme().dimension("chooser.layout.card_height_dp",fallback.cardHeight));
      layout.put("stack_below_width_dp",vtheme().dimension("chooser.layout.stack_below_width_dp",fallback.stackBelowWidth));
      layout.put("motion_ms",vtheme().motion("chooser.layout.motion_ms",fallback.motionMs));
      return new ExperienceTheme(root);
    }catch(org.json.JSONException invalid){return fallback;}
  }
'''
 i=s.rfind('\n}');s=s[:i]+helper+s[i:]
 return s,['chooserStyledText','showVisualExperienceScene','showInfinityExperienceChooser','ExperienceBackdrop.onDraw','ExperienceMark.onDraw','chooserExperienceCard','showStyledInfinityExperienceChooser']

def generate(inputs):
 results={};catalog=[];proof={}
 for rel,source in inputs.items():
  if sha(source)!=HASHES[rel]:raise ValueError('Locked 2103159 preimage mismatch: '+rel)
  adapted,changed=(adapt_activity if rel==ACT else adapt_splash)(source)
  output,slots=instrument(adapted,'cobra' if rel==ACT else 'chooser')
  results[rel]=output;catalog.extend(slots);proof[rel]={'before':sha(source),'after':sha(output),'manual_adapters':changed,'visual_substitutions':len(slots)}
 return results,catalog,proof

def catalog_java(slots):
 keys=sorted(x['group']+':'+x['key'] for x in slots)
 values=',\n'.join(json.dumps(k) for k in keys)
 return 'package @APP_PACKAGE@;\npublic final class CobraVisualCatalog {\nprivate static final java.util.Set<String> KEYS=new java.util.HashSet<>(java.util.Arrays.asList(\n'+values+'''
));
public static boolean allows(String group,String key){
 if(KEYS.contains(group+":"+key))return true;
 if(group.equals("dimensions"))return key.matches("chooser[.]layout[.](outer_padding_dp|card_radius_dp|card_gap_dp|card_height_dp|stack_below_width_dp)")||key.equals("drawer.footer.height")||key.equals("drawer.ribbon.height")||key.equals("chooser.footer.height")||key.startsWith("art.");
 if(group.equals("guide_layouts"))return key.matches("mobile|grid|compact|cards|focus");
 if(group.equals("scenes"))return key.equals("chooser");
 if(group.equals("numbers"))return key.equals("chooser.layout.motion_ms");
 if(group.equals("copy"))return key.matches("chooser[.]label[.](brand|brand_tagline|title|personalization|infinity_title|infinity_subtitle|cobra_title|cobra_subtitle|footer_brand|footer_tagline|initials)")||key.matches("drawer[.]label[.](search|tv|movies|shows|recordings|my_list|settings)");
 if(group.equals("colors"))return key.matches("chooser[.]palette[.](background|background_glow|text|muted|infinity_top|infinity_bottom|infinity_border|infinity_glow|cobra_top|cobra_bottom|cobra_border|cobra_glow|badge_fill|badge_border|horizon)")||key.matches("argb[.][0-9a-f]{8}")||key.matches("palette[.](background|rail|panel|panel2|text|muted|accent|accent_soft|line|focus)");
 if(group.equals("styles"))return key.matches("(all|widget|drawer|sheet|settings|rail|screen|guide|player|multiview|chooser|dialog|tag|font|art)([./][A-Za-z0-9_:.-]+)*");
 if(group.equals("images"))return key.matches("icon[.](play|pause|next|prev|close|back|more|favorite|favorite_on|multi|lock|unlock|aspect|fullscreen|recent|audio|mute|record|add|remove|search|cast|cc|health|settings|source|guide)")||key.matches("drawer[.]icon[.](search|tv|movies|shows|recordings|my_list|settings)")||java.util.Arrays.asList("drawer.badge","drawer.footer","drawer.ribbon","chooser.background","chooser.mark.cobra","chooser.mark.infinity","chooser.footer").contains(key);
 return false;
}
}
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 inputs={r:(a.source/r).read_text() for r in HASHES};results,catalog,proof=generate(inputs)
 registration='cmake/scripts/android/Install.cmake';original_registration=(a.source/registration).read_bytes()
 if sha(original_registration)!='3348f70ee21061b2a0c424ea060541719f27da51381d4379ef1dd714e9c3ead0':raise ValueError('Locked Java registration preimage mismatch')
 pending={rel:s.encode() for rel,s in results.items()};reg=original_registration.decode()
 for name in ('CobraVisualTheme','CobraVisualRenderer','CobraVisualScene','CobraVisualGeometry','CobraVisualCatalog'):
  rel='tools/android/packaging/xbmc/src/'+name+'.java.in'
  if (a.source/rel).exists() or 'src/'+name+'.java' in reg:raise ValueError('New runtime source/registration already exists')
  pending[rel]=(catalog_java(catalog) if name=='CobraVisualCatalog' else (ROOT/(name+'.java.in')).read_text()).encode()
  proof[rel]={'before':None,'after':sha(pending[rel])}
  reg+='\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/'+name+'.java.in\n               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/'+name+'.java @ONLY)\n'
 pending[registration]=reg.encode();proof[registration]={'before':sha(original_registration),'after':sha(pending[registration])}
 # Preflight the entire edit set and keep exact originals before the first source write.
 a.out.mkdir(parents=True,exist_ok=True);backup=a.out/'source-before';backup.mkdir(exist_ok=False)
 originals={rel:(a.source/rel).read_bytes() if (a.source/rel).exists() else None for rel in pending}
 for rel,content in originals.items():
  if content is not None:
   target=backup/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
   if target.read_bytes()!=content:raise IOError('Backup verification failed: '+rel)
 try:
  for rel,content in pending.items():
   target=a.source/rel;temporary=target.with_name(target.name+'.visual-staging')
   if temporary.exists():raise ValueError('Staging path already exists: '+str(temporary))
   with temporary.open('xb') as f:f.write(content);f.flush();os.fsync(f.fileno())
   os.replace(temporary,target)
 except Exception:
  for rel,content in originals.items():
   target=a.source/rel
   if content is None:target.unlink(missing_ok=True)
   else:target.write_bytes(content)
  raise
 (a.out/'visual-catalog.json').write_text(json.dumps({'runtime':2,'build':2103160,'base':BASE,'slots':catalog,'limitations':['No arbitrary new view hierarchies or actions','Supports system families and user-supplied TTF/OTF; no font files bundled','Raster PNG/WebP/JPEG assets; no SVG execution','Native and provider algorithms are outside theme ownership']},indent=2)+'\n')
 (a.out/'patch.json').write_text(json.dumps({'base':BASE,'files':proof,'device_verified':False,'official':False},indent=2)+'\n')
 print('PASS: generated',len(catalog),'visual token sites; explicit artwork and style adapters installed')
if __name__=='__main__':main()
