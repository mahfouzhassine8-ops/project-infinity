#!/usr/bin/env python3
"""Candidate-14 protected delta: five device-reported fixes on exact 2103162."""
from pathlib import Path
import argparse, hashlib, json, re, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
ACT=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
SPLASH=Path('tools/android/packaging/xbmc/src/Splash.java.in')
SERVICE=Path('tools/android/packaging/xbmc/src/InfinityExtendedBackgroundService.java.in')
MANIFEST=Path('tools/android/packaging/xbmc/AndroidManifest.xml.in')
PRE={
 str(ACT):'16e75d481a662af6747260feab5f3377acd34f565274b7c768eeb293a8426640',
 str(SPLASH):'b7b88785f6b0e519e733f18675edb30969b0979f8e8d14cc3ddbd35b962d4854',
 str(SERVICE):'bb603dd85dcdf07d4b355d8cee06148ad22a4dd1e0984f4ce4afe7e3ecb14bcc',
 str(MANIFEST):'eeef97b36f64711c9c5e545f0b969e4a5041378a0c1875b0be161bc3ec17c138',
}

def sha(v):
 if isinstance(v,str):v=v.encode()
 return hashlib.sha256(v).hexdigest()

def method_end(text,start):
 brace=text.find('{',start)
 if brace<0:raise ValueError('method brace missing')
 d=0;q=None;esc=False;line=False;block=False;i=brace
 while i<len(text):
  c=text[i];n=text[i+1] if i+1<len(text) else ''
  if line:
   if c=='\n':line=False
   i+=1;continue
  if block:
   if c=='*' and n=='/':block=False;i+=2;continue
   i+=1;continue
  if q:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c==q:q=None
   i+=1;continue
  if c=='/' and n=='/':line=True;i+=2;continue
  if c=='/' and n=='*':block=True;i+=2;continue
  if c in ('"',"'"):q=c;i+=1;continue
  if c=='{':d+=1
  elif c=='}':
   d-=1
   if d==0:return i+1
  i+=1
 raise ValueError('method unclosed')

def span(text,name):
 p=re.compile(r'^  (?:@Override(?:[ \t]*\n  |[ \t]+))?(?:private|public|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',re.M)
 m=list(p.finditer(text))
 if len(m)!=1:raise ValueError(f'{name}: expected one method, got {len(m)}')
 return m[0].start(),method_end(text,m[0].start())

def once(s,a,b,label='anchor'):
 if s.count(a)!=1:raise ValueError(f'{label}: expected one match, got {s.count(a)}')
 return s.replace(a,b,1)

def edit(text,name,fn):
 a,b=span(text,name);old=text[a:b];new=fn(old)
 if new==old:raise ValueError(name+': no change')
 return text[:a]+new+text[b:]

def replace_method(text,name,new):
 a,b=span(text,name);return text[:a]+new.rstrip()+'\n'+text[b:]

def patch_activity(s):
 s=once(s,'  private static final int MAX_CHANNELS = 12000;','  private static final int MAX_CHANNELS = 50000;','channel cap')
 s=edit(s,'cobraOpenSheet',lambda b:once(b,
'''    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(Math.min(width-dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.12",24)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.13",440))),-2,
        isPortrait()?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:Gravity.RIGHT|Gravity.CENTER_VERTICAL);''',
'''    final boolean playerSettings="player-settings".equals(kind);
    FrameLayout.LayoutParams pos=new FrameLayout.LayoutParams(Math.min(width-dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.12",24)),dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.13",440))),-2,
        playerSettings?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:(isPortrait()?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL:Gravity.RIGHT|Gravity.CENTER_VERTICAL));''','player settings geometry'))
 s=edit(s,'loadXtream',lambda b:once(b,
'''      String group = categories.get(categoryId);
      if (group == null || group.trim().isEmpty()) group = "Other";''',
'''      String group = cobraNormalizeProviderGroup(categories.get(categoryId));
      if (group.isEmpty()) group = "Other";''','xtream group normalize'))
 s=edit(s,'parseM3u',lambda b:once(b,
'''      String group = attributes.get("group-title");
      if (group == null || group.trim().isEmpty()) group = "Other";''',
'''      String group = cobraNormalizeProviderGroup(attributes.get("group-title"));
      if (group.isEmpty()) group = "Other";''','m3u group normalize'))
 s=edit(s,'cobraDirectory',lambda b:once(b,
'''      java.util.TreeMap<String,Integer> groups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);int all=0,favorites=0,recent=0;
      for(Channel c:mChannels)if(cobraChannelAllowed(c)&&(mCobraGuideSource.isEmpty()||mCobraGuideSource.equals(sourceIdForChannel(c)))){all++;if(mFavorites.contains(c.id))favorites++;if(mRecents.contains(c.id))recent++;if(c.group!=null&&!c.group.isEmpty())groups.put(c.group,groups.containsKey(c.group)?groups.get(c.group)+1:1);}''',
'''      java.util.TreeMap<String,Integer> groups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);int all=0,favorites=0,recent=0;
      for(Channel c:mChannels){
        if(c==null||(!mCobraGuideSource.isEmpty()&&!mCobraGuideSource.equals(sourceIdForChannel(c)))||!mFeatures.sourceEnabled(sourceIdForChannel(c)))continue;
        String providerGroup=cobraNormalizeProviderGroup(c.group);
        if(!providerGroup.isEmpty()&&!mFeatures.looksAdult(providerGroup)&&!groups.containsKey(providerGroup))groups.put(providerGroup,0);
        if(cobraChannelAllowed(c)){all++;if(mFavorites.contains(c.id))favorites++;if(mRecents.contains(c.id))recent++;if(!providerGroup.isEmpty()&&!mFeatures.looksAdult(providerGroup))groups.put(providerGroup,groups.get(providerGroup)+1);}
      }''','complete group directory'))
 def settings(b):
  b=once(b,
'''    Button backgroundMode = action("BACKGROUND MODE  •  " + cobraBackgroundModeLabel());
    backgroundMode.setTag("cobra_background_mode");
    backgroundMode.setOnClickListener(v -> showCobraBackgroundModePicker());''',
'''    Button backgroundMode = action("BACKGROUND MODE  •  " + cobraBackgroundModeLabel());
    backgroundMode.setTag("cobra_background_mode");
    backgroundMode.setOnClickListener(v -> showCobraBackgroundModePicker());

    Button miniBackground = action("PLAY IN BACKGROUND  •  " + cobraMiniBackgroundLabel());
    miniBackground.setTag("cobra_mini_background");
    miniBackground.setOnClickListener(v -> showCobraMiniBackgroundPicker());

    Button filePicker = action("FILE PICKER  •  " + cobraFilePickerLabel());
    filePicker.setTag("cobra_file_picker");
    filePicker.setOnClickListener(v -> showCobraFilePickerPicker());''','settings buttons')
  return once(b,
'''    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));''',
'''    list.addView(backgroundMode, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(miniBackground, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(filePicker, new LinearLayout.LayoutParams(-1, dp(56)));
    list.addView(uiState, new LinearLayout.LayoutParams(-1, dp(44)));''','settings rows')
 s=edit(s,'showSettings',settings)
 s=edit(s,'onUserLeaveHint',lambda b:once(b,'    if (hasCobraVideo()) enterCobraPictureInPicture();','    if (hasCobraVideo()) enterCobraPictureInPicture();\n    else mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();','mini foreground handoff'))
 s=edit(s,'onStop',lambda b:once(b,'    if (!isCobraInPictureInPicture()) pauseCobraForBackground();','    if (!isCobraInPictureInPicture()) {if(!mCobraMiniBackgroundActive)mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();pauseCobraForBackground();}','mini onStop fallback'))
 s=edit(s,'onResume',lambda b:once(b,
'''    mCobraHealthForeground=true;cobraStartHealthTicker();
    InfinityExtendedBackgroundService.sync(this);''',
'''    mCobraHealthForeground=true;cobraStartHealthTicker();
    cobraEndMiniBackgroundPlayback();
    InfinityExtendedBackgroundService.sync(this);''','mini onResume'))
 s=edit(s,'pauseCobraForBackground',lambda b:once(b,
'''    rememberAndPauseCobraPlayer(mPlayer);rememberAndPauseCobraPlayer(mCobraPreviewPlayer);
    rememberAndPauseCobraPlayer(mCobraCarryPlayer);rememberAndPauseCobraPlayer(mCobraTransferPlayer);''',
'''    rememberAndPauseCobraPlayer(mPlayer);if(!mCobraMiniBackgroundActive)rememberAndPauseCobraPlayer(mCobraPreviewPlayer);
    rememberAndPauseCobraPlayer(mCobraCarryPlayer);rememberAndPauseCobraPlayer(mCobraTransferPlayer);''','preview keepalive'))
 s=edit(s,'stopCobraPreviewPlayerOnly',lambda b:once(b,'  private void stopCobraPreviewPlayerOnly() {\n    ExoPlayer previous=mCobraPreviewPlayer;','  private void stopCobraPreviewPlayerOnly() {\n    cobraEndMiniBackgroundPlayback();\n    ExoPlayer previous=mCobraPreviewPlayer;','preview stop'))
 s=edit(s,'onDestroy',lambda b:once(b,'    // Terminal state must be visible before callbacks, views or decoder sessions are released.','    if(!isChangingConfigurations())cobraEndMiniBackgroundPlayback();\n    // Terminal state must be visible before callbacks, views or decoder sessions are released.','destroy cleanup'))
 s=replace_method(s,'openCobraUiPackagePicker','''  private void openCobraUiPackagePicker() {
    cobraOpenFilePicker(REQUEST_COBRA_UI_PACKAGE,"application/zip",
        new String[]{"application/zip","application/x-zip-compressed","application/octet-stream"},false);
  }''')
 s=replace_method(s,'openDocumentPicker','''  private void openDocumentPicker() {
    cobraOpenFilePicker(REQUEST_LOCAL_MEDIA,"*/*",new String[]{"video/*","audio/*"},true);
  }''')
 helpers=(ROOT/'activity-helpers.java.inc').read_text().rstrip()
 pos=s.rfind('\n}')
 if pos<0:raise ValueError('Activity class terminator missing')
 s=s[:pos]+'\n'+helpers+'\n'+s[pos:]
 for token in ('playerSettings?Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL','MAX_CHANNELS = 50000','cobraNormalizeProviderGroup','PLAY IN BACKGROUND  •  ','InfinityExtendedBackgroundService.startMiniPlayback','MiXplorer','ACTION_GET_CONTENT'):
  if token not in s:raise ValueError('missing activity contract '+token)
 a,b=span(s,'onUserLeaveHint');leave=s[a:b]
 if 'if (hasCobraVideo()) enterCobraPictureInPicture();' not in leave or 'else mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();' not in leave:raise ValueError('PiP/mini-player ownership changed')
 return s

def patch_splash(s):
 s=edit(s,'showVisualExperienceScene',lambda b:once(b,
'    org.json.JSONObject scene=vtheme().scene("chooser");if(scene==null)return false;',
'    org.json.JSONObject scene=vtheme().scene("chooser");if(scene==null)return false;\n    int availableHeightDp=Math.round(getResources().getDisplayMetrics().heightPixels/getResources().getDisplayMetrics().density);\n    if(availableHeightDp<700)return false;','scene height guard'))
 def compact(b):
  b=once(b,
'''    android.widget.LinearLayout content = new android.widget.LinearLayout(this);
    content.setOrientation(android.widget.LinearLayout.VERTICAL); content.setGravity(android.view.Gravity.CENTER_HORIZONTAL);
    content.setPadding(chooserDp(theme.outerPadding), chooserDp(vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.1",20)), chooserDp(theme.outerPadding), chooserDp(vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.2",18)));''',
'''    android.widget.LinearLayout content = new android.widget.LinearLayout(this);
    content.setOrientation(android.widget.LinearLayout.VERTICAL); content.setGravity(android.view.Gravity.CENTER_HORIZONTAL);
    int heightDp=Math.round(getResources().getDisplayMetrics().heightPixels/getResources().getDisplayMetrics().density);
    boolean compactHeight=heightDp<700;
    content.setPadding(chooserDp(theme.outerPadding), chooserDp(compactHeight?8:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.1",20)), chooserDp(theme.outerPadding), chooserDp(compactHeight?8:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.2",18)));''','compact height state')
  b=once(b,'    content.addView(identity, new android.widget.LinearLayout.LayoutParams(-1, chooserDp(vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.8",98))));','    content.addView(identity, new android.widget.LinearLayout.LayoutParams(-1, chooserDp(compactHeight?74:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.8",98))));','compact identity')
  b=once(b,'    android.widget.LinearLayout.LayoutParams titleParams = new android.widget.LinearLayout.LayoutParams(-1, -2); titleParams.topMargin = chooserDp(vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.9",18)); content.addView(title, titleParams);','    android.widget.LinearLayout.LayoutParams titleParams = new android.widget.LinearLayout.LayoutParams(-1, -2); titleParams.topMargin = chooserDp(compactHeight?6:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.9",18)); content.addView(title, titleParams);','compact title')
  b=once(b,'    android.widget.LinearLayout.LayoutParams cardsParams = new android.widget.LinearLayout.LayoutParams(-1, -2); cardsParams.topMargin = chooserDp(vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.10",26)); content.addView(cards, cardsParams);','    android.widget.LinearLayout.LayoutParams cardsParams = new android.widget.LinearLayout.LayoutParams(-1, -2); cardsParams.topMargin = chooserDp(compactHeight?10:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.10",26)); content.addView(cards, cardsParams);\n    int adaptiveCardHeight=compactHeight?Math.min(theme.cardHeight,Math.max(200,heightDp-285)):theme.cardHeight;','compact cards')
  if b.count('chooserDp(theme.cardHeight)')!=4:raise ValueError('unexpected chooser card-height anchors')
  b=b.replace('chooserDp(theme.cardHeight)','chooserDp(adaptiveCardHeight)')
  b=once(b,'    android.widget.LinearLayout.LayoutParams footerParams = new android.widget.LinearLayout.LayoutParams(-1, -2); footerParams.topMargin = chooserDp(vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.11",34)); content.addView(footer, footerParams);','    android.widget.LinearLayout.LayoutParams footerParams = new android.widget.LinearLayout.LayoutParams(-1, -2); footerParams.topMargin = chooserDp(compactHeight?10:vtheme().dimension("chooser.showStyledInfinityExperienceChooser.dimensions.11",34)); content.addView(footer, footerParams);','compact footer')
  return once(b,'    if(vtheme().hasImage("chooser.footer"))content.addView(vtheme().art(this,"chooser.footer",60),new android.widget.LinearLayout.LayoutParams(-1,chooserDp(vtheme().dimension("chooser.footer.height",60))));','    if(!compactHeight&&vtheme().hasImage("chooser.footer"))content.addView(vtheme().art(this,"chooser.footer",60),new android.widget.LinearLayout.LayoutParams(-1,chooserDp(vtheme().dimension("chooser.footer.height",60))));','compact footer art')
 s=edit(s,'showStyledInfinityExperienceChooser',compact)
 for token in ('compactHeight=heightDp<700','adaptiveCardHeight','availableHeightDp<700'):
  if token not in s:raise ValueError('missing chooser contract '+token)
 return s

def patch_manifest(s):
 s=once(s,'<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n','<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />\n','media playback permission')
 s=once(s,'android:foregroundServiceType="specialUse">','android:foregroundServiceType="specialUse|mediaPlayback">','service type')
 ET.fromstring(s)
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 paths={ACT:patch_activity,SPLASH:patch_splash,SERVICE:lambda _: (ROOT/'InfinityExtendedBackgroundService.java.in').read_text(),MANIFEST:patch_manifest}
 report={'base_build':2103162,'target_build':2103163,'locked_candidate14':'1465eabb045badad56142642c48292df94caaa12','files':{},'native_modified':False}
 pending={}
 for rel,fn in paths.items():
  path=a.source/rel;before=path.read_text();actual=sha(before)
  if actual!=PRE[str(rel)]:raise ValueError(f'Candidate 14 preimage drift {rel}: {actual}')
  after=fn(before);pending[path]=after;report['files'][str(rel)]={'before':actual,'after':sha(after)}
 for path,after in pending.items():path.write_text(after)
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: exact Candidate 14 five-fix delta applied; protected native engine untouched')
if __name__=='__main__':main()
