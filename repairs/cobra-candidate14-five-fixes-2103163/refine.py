#!/usr/bin/env python3
"""Behavioral audit corrections over the exact 2103163 run-5 source; no lock edits."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,re,shutil
ROOT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('patch163',ROOT/'apply.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
SRC=Path('tools/android/packaging/xbmc/src')
PRE={'InfinityLiveActivity.java.in':'2226306907b9a702e8d3b54bdffddc2f116aa597142d64cef19228b202789feb','Splash.java.in':'56778e9bd4382c0b29393a36734856a2798199f30f612432b874ccc3e29ba6bd','InfinityExtendedBackgroundService.java.in':'1a20a06c446fc4b5d2467ea44cd768fa7b3271132f6022a7ea3abd6fec71afcb','CobraVisualScene.java.in':'87b92d6b1796c9da7a409465a845cf7216c646f3d90fe6b8ce98d6963cb34dd8'}
POST={'InfinityLiveActivity.java.in': '2ddd50e78ae7927d897e7d1fba352ceec6d8bdafbdba6c776848fa1c96922daf', 'Splash.java.in': '591a355c1b026b33cfbb710671c16ef9c79fd26683bc5c1bc658294afda8b764', 'InfinityExtendedBackgroundService.java.in': 'f99788bbbd8debb6f03970f1dbe6c17e6fe661c11a527eff96b98346f1a22406', 'CobraVisualScene.java.in': 'c89583c692e116a05dd9dc4d5785effc86785ea2ddb16d6c51dafdd493cdde11'}
sha=a.sha
once=a.once

def activity(text):
 original=text;changed=[]
 def edit(name,fn):
  nonlocal text
  text=a.edit(text,name,fn);changed.append(name)
 text=once(text,'  private boolean mCobraMiniBackgroundActive=false;','  private boolean mCobraMiniBackgroundActive=false;\n  private boolean mCobraMiniBackgroundSurfaceDetached=false;')
 for match in re.finditer(r'  // @(method|new) (\w+)\n([\s\S]*?)(?=  // @|\Z)',(ROOT/'refinement-activity.java.inc').read_text()):
  kind,name,body=match.groups()
  if kind=='method':text=a.replace_method(text,name,body);changed.append(name)
  else:text=text[:text.rfind('\n}')]+ '\n'+body+text[text.rfind('\n}'):]
 edit('onStop',lambda b:once(b,'if(!mCobraMiniBackgroundActive)mCobraMiniBackgroundActive=cobraBeginMiniBackgroundPlayback();','mCobraMiniBackgroundActive=InfinityExtendedBackgroundService.keepsMiniPlayback(mCobraPreviewPlayer);'))
 edit('showCobraBackgroundModePicker',lambda b:b[:-1]+'  cobraAddMiniBackgroundSwitch(rows);\n  }')
 # Fullscreen and the main guide must enumerate the same allowed provider groups.
 edit('cobraRenderPlayerDrawer',lambda b:once(once(b,'java.util.TreeSet<String> g=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);for(Channel c:mChannels)if(cobraChannelAllowed(c)&&c.group!=null&&!c.group.isEmpty())g.add(c.group);names.addAll(g);','names.addAll(cobraProviderGroups(false).keySet());'),'filter.substring(6).equals(c.group)','cobraGroupMatches(filter.substring(6),c.group)'))
 def directory(b):
  start=b.index('      java.util.TreeMap<String,Integer> groups=');end=b.index('      Collections.addAll(names',start)
  replacement='''      java.util.SortedMap<String,Integer> groups=cobraProviderGroups(true);int all=0,favorites=0,recent=0;
      for(Channel c:mChannels)if(cobraChannelAllowed(c)&&(mCobraGuideSource.isEmpty()||mCobraGuideSource.equals(sourceIdForChannel(c)))){all++;if(mFavorites.contains(c.id))favorites++;if(mRecents.contains(c.id))recent++;}
'''
  return b[:start]+replacement+b[end:]
 edit('cobraDirectory',directory)
 edit('filteredChannels',lambda b:once(b,'!mCategory.equals(channel.group)','!cobraGroupMatches(mCategory,channel.group)'))
 # Keep resource protection, but never silently publish a truncated catalogue as complete.
 edit('loadXtream',lambda b:once(b,'for (int i = 0; i < streams.length() && channels.size() < MAX_CHANNELS; i++) {','for (int i = 0; i < streams.length(); i++) {\n      if(channels.size()>=MAX_CHANNELS)throw new LiveException("Provider exceeds the safe 50,000-channel limit; catalogue not replaced. Use a smaller provider playlist.");'))
 edit('parseM3u',lambda b:once(once(b,'      if (isPlayableUrl(resolved)) {','      if (isPlayableUrl(resolved)) {\n        if(channels.size()>=MAX_CHANNELS)throw new LiveException("Playlist exceeds the safe 50,000-channel limit; catalogue not replaced.");'),'        if (channels.size() >= MAX_CHANNELS) break;',''))
 def sheet(b):
  b=once(b,'FrameLayout scrim=new FrameLayout(this);mCobraActionSheet=scrim;','''final LinearLayout[] sheetPanel=new LinearLayout[1];
    FrameLayout scrim=new FrameLayout(this){
      @Override protected void onMeasure(int ws,int hs){super.onMeasure(ws,hs);if(sheetPanel[0]!=null){cobraConstrainSheet(this,sheetPanel[0],"player-settings".equals(kind));super.onMeasure(ws,hs);}}
    };mCobraActionSheet=scrim;''')
  b=once(b,'LinearLayout panel=new LinearLayout(this);panel.setOrientation','LinearLayout panel=new LinearLayout(this);sheetPanel[0]=panel;panel.setOrientation')
  b=once(b,'    final int limit=Math.min(dp(vtheme().dimension("cobra.cobraOpenSheet.dimensions.11",480)),Math.round(available*.67f));','')
  b=once(b,'@Override protected void onMeasure(int w,int h) { super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(limit,View.MeasureSpec.AT_MOST)); }','''@Override protected void onMeasure(int w,int h) {
        android.graphics.Rect safe=cobraSheetSafeBounds(parent,"player-settings".equals(kind));
        int limit=Math.max(1,Math.min(dp(480),safe.height()-header.getMeasuredHeight()-panel.getPaddingTop()-panel.getPaddingBottom()));
        super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(limit,View.MeasureSpec.AT_MOST));
      }''')
  b=once(b,'close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;','''close.requestFocus();vtheme().tree(panel,"sheet."+kind);
    panel.setTag("cobra_sheet_panel");scrim.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->cobraConstrainSheet(scrim,panel,playerSettings));
    scrim.setOnApplyWindowInsetsListener((v,insets)->{cobraConstrainSheet(scrim,panel,playerSettings);return insets;});
    cobraConstrainSheet(scrim,panel,playerSettings);return items;''')
  return b
 edit('cobraOpenSheet',sheet)
 def result(b):
  old='''    try {
      getContentResolver().takePersistableUriPermission(uri,
          data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION));
    } catch (Exception ignored) {}'''
  new='''    if((data.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)!=0){
      try{getContentResolver().takePersistableUriPermission(uri,data.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION);}
      catch(SecurityException unavailable){toast("This file is available for this session only");}
    }else toast("File opened for this session. Use System picker for persistent access.");'''
  return once(b,old,new)
 edit('onActivityResult',result)
 # Verify EVERY non-targeted top-level method, not merely the presence of feature words.
 protected=[]
 for name in set(re.findall(r'^  (?:@Override\s+)?(?:private|public|protected) [^\n;=(){}]*\b(\w+)\s*\(',original,re.M))-set(changed):
  try:x,y=a.span(original,name);u,v=a.span(text,name)
  except ValueError:continue
  if original[x:y]!=text[u:v]:raise RuntimeError('Unexpected method change: '+name)
  protected.append(name)
 return text,{'changed_methods':changed,'protected_methods':sorted(protected)}

def splash(text):
 # Never disable the approved theme simply because the screen is short.
 text=once(text,'    int availableHeightDp=Math.round(getResources().getDisplayMetrics().heightPixels/getResources().getDisplayMetrics().density);\n    if(availableHeightDp<700)return false;','')
 # The styled fallback uses measured available bounds and divides stacked height by two.
 text=once(text,'    boolean stacked = widthDp < theme.stackBelowWidth;','    boolean stacked = widthDp < Math.min(theme.stackBelowWidth,600);')
 text=once(text,'int adaptiveCardHeight=compactHeight?Math.min(theme.cardHeight,Math.max(200,heightDp-285)):theme.cardHeight;','int adaptiveCardHeight=compactHeight?Math.min(theme.cardHeight,Math.max(200,(heightDp-285-(stacked?theme.cardGap:0))/(stacked?2:1))):theme.cardHeight;')
 # Keep the insets and actual window width authoritative; scene reflows itself during measurement.
 return text

def scene(text):
 start=text.index('  static View build(');end=a.method_end(text,start)
 return text[:start]+(ROOT/'scene-build.java.inc').read_text().rstrip()+text[end:]

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
 receipt=json.loads(args.receipt.read_text());pending={};proof={}
 for name,expected in PRE.items():
  path=args.source/SRC/name;before=path.read_text()
  if sha(before)!=expected:raise RuntimeError('Audit preimage drift: '+name)
  detail={}
  if name.startswith('InfinityLiveActivity'):after,detail=activity(before)
  elif name.startswith('Splash'):after=splash(before)
  elif name.startswith('CobraVisualScene'):after=scene(before)
  else:after=(ROOT/'mini-service.java.in').read_text()
  if sha(after)!=POST[name]:raise RuntimeError('Locally audited postimage drift: '+name)
  pending[path]=(before,after);proof[name]={'before':sha(before),'after':sha(after),**detail}
 # CPU wake mode is held by ExoPlayer only while the leased player is active.
 manifest=args.source/'tools/android/packaging/xbmc/AndroidManifest.xml.in'
 if manifest.exists():
  before=manifest.read_text()
  if sha(before)!='fbe569bad4685e26f9e275f59db511b297ecfb16ba03366ba46fa8629bfc836b':raise RuntimeError('Manifest preimage drift')
  after=once(before,'<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />','<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />\n<uses-permission android:name="android.permission.WAKE_LOCK" />')
  pending[manifest]=(before,after)
 for path,(before,after) in pending.items():
  rel=str(path.relative_to(args.source));backup=args.out/'before'/rel;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_text(before)
  path.write_text(after)
  row=receipt['files'].setdefault(rel,{'before':sha(before)});row['after']=sha(after)
 args.out.mkdir(parents=True,exist_ok=True);(args.out/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
 args.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print('PASS: exact behavioral audit refinement; untouched Activity methods:',len(proof['InfinityLiveActivity.java.in']['protected_methods']))
if __name__=='__main__':main()
