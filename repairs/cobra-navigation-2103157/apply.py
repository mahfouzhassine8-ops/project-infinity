#!/usr/bin/env python3
"""Exact 2103156 -> 2103157 navigation/TV workspace/appearance patch; no native mutation."""
from pathlib import Path
import argparse,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'cobra-epg-rc1'))
from apply_epg_repair import span as original_span
def span(text,name,kind="method"):
 normalized=re.sub(r"^  @Override (public|protected|private) ",lambda m:"  "+m.group(1)+" "+" "*10,text,flags=re.M)
 return original_span(normalized,name,kind)
BASELINE='766238af35d0bdddd80acb6c5c7e3e1c1cf4c38e493d365e0e777d883206079b'
REL='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
def sha(x):return hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact anchor mismatch: '+a[:110])
 return s.replace(a,b,1)
def patch(before):
 if sha(before)!=BASELINE:raise ValueError('Not the verified 2103156 generated Activity')
 text=before;changed=[]
 def replace(name,code,kind='method'):
  nonlocal text
  a,b=span(text,name,kind);text=text[:a]+code.rstrip()+text[b:];changed.append((kind,name))
 def transform(name,fn,kind='method'):
  a,b=span(text,name,kind);replace(name,fn(text[a:b]),kind)
 transform('cobraEffectiveAppearanceMode',lambda s:'''  private String cobraEffectiveAppearanceMode() {
    boolean night=(getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES;
    return CobraAppearancePolicy.effective(cobraStoredAppearanceMode(),cobraSystemDarkVariant(),night);
  }''')
 replace('cobraAppearanceLabel','''  private String cobraAppearanceLabel() {
    String mode=cobraStoredAppearanceMode();
    if("system".equals(mode))return "FOLLOW SYSTEM  •  "+cobraDarkVariantName().toUpperCase(Locale.US);
    return "light".equals(mode)?"LIGHT":"oled".equals(mode)?"TRUE OLED BLACK":"DARK";
  }''')
 replace('showCobraAppearancePicker','''  private void showCobraAppearancePicker() {
    LinearLayout rows=cobraOpenSheet("Cobra appearance","Automatic switching and your preferred dark palette are independent.","appearance");boolean dark=cobraSheetIsDark();
    String[] labels={"Follow System","Light","Dark","True OLED Black"},values={"system","light","dark","oled"};
    for(int i=0;i<values.length;i++){
      final String value=values[i];LinearLayout row=cobraSheetRow("more",labels[i]+(value.equals(cobraStoredAppearanceMode())?" • Selected":""),"system".equals(value)?"System Light → Light · System Dark → "+cobraDarkVariantName():null,false,dark,()->{
        mPrefs.edit().putString(COBRA_APPEARANCE_MODE,value).apply();cobraApplyAppearanceSettings();
      });row.setTag("cobra-appearance:"+value);rows.addView(row);
    }
    LinearLayout preferred=cobraSheetRow("settings","System dark palette: "+cobraDarkVariantName(),"Choose Dark or True OLED Black for Follow System",false,dark,()->showCobraSystemDarkPicker());preferred.setTag("cobra-system-dark-picker");rows.addView(preferred);
  }''')
 # Lifetime-aware sizing. A new shell of the SAME dimensions must not inherit an old layout stamp.
 transform('stopCobraPreview',lambda s:once(s,'    stopCobraPreviewPlayerOnly();','    cobraRememberModeScroll();\n    mCobraLastGuideWidth=-1;mCobraLastGuideHeight=-1;mCobraModeLayout=null;\n    mCobraRenderedMode="";mCobraGuideRuler=null;\n    stopCobraPreviewPlayerOnly();'))
 def shell(s):
  s=once(s,'    mCobraInternalScreen="root";','    mCobraNavigation.advance();mCobraStageTitle="";\n    mCobraInternalScreen="root";\n    if("grid".equals(mCobraGuideStyle)&&!"sources".equals(mCobraGuideRoute))mCobraGuideRoute="channels";')
  s=once(s,'mStage.setPadding(dp(8),0,dp(8),0);','mStage.setPadding("grid".equals(mCobraGuideStyle)?0:dp(8),0,"grid".equals(mCobraGuideStyle)?0:dp(8),0);\n    if(!mCobraDrawerShifted){mStage.animate().cancel();mStage.setTranslationX(0f);}')
  s=once(s,'    if(mCobraGuideShell==null){','    if(mCobraGuideShell==null){\n      mCobraLastGuideWidth=-1;mCobraLastGuideHeight=-1;mCobraModeLayout=null;')
  # Own the direct children's measurement BEFORE FrameLayout positions them.
  # An after-layout listener changes LayoutParams too late for that traversal;
  # caching only the shell's size can then hide unmeasured 1x1 children.
  s=once(s,'mCobraGuideShell=new FrameLayout(this);','''mCobraGuideShell=new FrameLayout(this){
        @Override protected void onLayout(boolean changed,int left,int top,int right,int bottom){
          if(this==mCobraGuideShell&&right>left&&bottom>top){
            if(mCobraModeLayout==null||right-left!=mCobraLastGuideWidth||bottom-top!=mCobraLastGuideHeight){
              cobraLayoutGuide();cobraRenderGuideBrowser();
            }
            int widthSpec=View.MeasureSpec.makeMeasureSpec(right-left,View.MeasureSpec.EXACTLY);
            int heightSpec=View.MeasureSpec.makeMeasureSpec(bottom-top,View.MeasureSpec.EXACTLY);
            for(int i=0;i<getChildCount();i++){
              View child=getChildAt(i);
              if(child.getVisibility()!=View.GONE)measureChildWithMargins(child,widthSpec,0,heightSpec,0);
            }
          }
          super.onLayout(changed,left,top,right,bottom);
        }
      };''')
  s=once(s,'      mCobraGuideShell.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=mCobraLastGuideWidth||b-t!=mCobraLastGuideHeight){cobraLayoutGuide();cobraRenderGuideBrowser();}});','')
  return s
 transform('cobraShowGuideShell',shell)
 transform('buildShell',lambda s:once(s,'    FrameLayout frame = new FrameLayout(this);','    mCobraNavigation.advance();\n    FrameLayout frame = new FrameLayout(this);'))
 transform('clearStage',lambda s:once(s,'    cobraRememberModeScroll();','    mCobraNavigation.advance();mCobraStageTitle=title;\n    cobraRememberModeScroll();'))
 transform('toggleCobraDrawer',lambda s:once(s,'()->{mCobraModeGroupsExpanded=true;mCobraGuideRoute="categories";if("mobile".equals(mCobraGuideStyle))mCobraGuideStyle="grid";cobraShowGuideShell();}','()->cobraOpenLiveTv()'))
 transform('showCobraTvHub',lambda s:once(s,'mCobraGuideRoute="categories"','mCobraGuideRoute="channels"'))
 # Obsolete VOD requests must never clear a newer Live TV/Settings screen on arrival.
 def vod(s):
  s=once(s,'    submitCobraIo(() -> {','    final long ticket=mCobraNavigation.current();\n    submitCobraIo(() -> {')
  return once(s,'publishCobraUi(() -> renderVodItems(items, series, failures))','cobraPublishNavigation(ticket,() -> renderVodItems(items, series, failures))')
 transform('showVodLibrary',vod)
 def series(s):
  s=once(s,'    submitCobraIo(() -> {','    final long ticket=mCobraNavigation.advance();\n    submitCobraIo(() -> {')
  s=s.replace('publishCobraUi(', 'cobraPublishNavigation(ticket,')
  s=once(s,'          mEpisodeQueue.clear();','          if(!mCobraNavigation.accepts(ticket))return;\n          mEpisodeQueue.clear();')
  return s
 transform('openSeries',series)
 # Configuration changes must not force Settings back to live or clobber the user's dark preference.
 transform('onConfigurationChanged',lambda s:once(s,'    buildShell();if(mChannels.isEmpty())','    if("COBRA • SETTINGS".equals(mCobraStageTitle)){buildShell();showSettings();return;}\n    buildShell();if(mChannels.isEmpty())'))
 def policy(s):
  begin=s.index('        int rail=w>=720');end=s.index('      }else if("compact"',begin)
  return s[:begin]+(ROOT/'tv-layout.inc').read_text()+s[end:]
 transform('CobraModeLayout',policy,'class')
 transform('cobraRenderGuideBrowser',lambda s:once(s,'    if(!rail&&!"channels".equals(mCobraGuideRoute)){','    if(!"grid".equals(mCobraGuideStyle)&&!rail&&!"channels".equals(mCobraGuideRoute)){'))
 replace('cobraToggleModeGroups','''  private void cobraToggleModeGroups(){
    cobraRememberModeScroll();
    if("grid".equals(mCobraGuideStyle)){
      if(mCobraModeLayout!=null&&mCobraModeLayout.width>=760){mCobraModeGroupsExpanded=!mCobraModeGroupsExpanded;mCobraGuideRoute="channels";cobraLayoutGuide();cobraRenderGuideBrowser();}
      else cobraOpenTvDirectory(false);
      return;
    }
    mCobraGuideRoute="channels".equals(mCobraGuideRoute)?"categories":"channels";cobraLayoutGuide();cobraRenderGuideBrowser();
  }''')
 transform('cobraModeBrowserHeader',lambda s:once(s,'v->{mCobraGuideRoute="sources";cobraRenderGuideBrowser();}','v->cobraOpenTvDirectory(true)'))
 def directory(s):
  s=once(s,'()->{mCobraGuideRoute="sources";cobraRenderGuideBrowser();}','()->cobraOpenTvDirectory(true)')
  s=once(s,'if(sources){mCobraGuideSource=value;mCobraGuideRoute="categories";cobraRenderGuideBrowser();}', 'if(sources){mCobraGuideSource=value;mCategory="ALL";mSearch="";if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();mCobraGuideRoute="grid".equals(mCobraGuideStyle)?"channels":"categories";cobraRenderGuideBrowser();}')
  return s
 transform('cobraDirectory',directory)
 transform('selectCobraCategory',lambda s:once(s,'{cobraRememberModeScroll();','{if("tv-directory".equals(mCobraSheetKind))closeCobraActionSheet();cobraRememberModeScroll();'))
 transform('CobraBroadcastRow',lambda s:once(s,'mCobraModeGroupsExpanded=true;mCobraGuideRoute="categories";cobraLayoutGuide();cobraRenderGuideBrowser();(mCobraGuideDirectory.getVisibility()==View.VISIBLE?mCobraGuideDirectory:mCobraGuideBrowser).requestFocus();','cobraOpenTvDirectory(false);'),'class')
 def back(s):
  marker='    if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&"channels".equals(mCobraGuideRoute))'
  return once(s,marker,'''    if("grid".equals(mCobraGuideStyle)&&mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){
      if(!mSearch.isEmpty()){mSearch="";cobraRenderGuideBrowser();return;}
      if("sources".equals(mCobraGuideRoute)){mCobraGuideRoute="channels";cobraRenderGuideBrowser();return;}
      if(mCobraModeLayout!=null&&mCobraModeLayout.directory[2]>0){mCobraModeGroupsExpanded=false;cobraLayoutGuide();cobraRenderGuideBrowser();return;}
      moveTaskToBack(true);return;
    }
'''+marker)
 transform('onBackPressed',back)
 # Fresh export now gives measurable video-host evidence for any residual device-only failure.
 transform('cobraFreshHealthSnapshot',lambda s:once(s,'      root.put("view_mode",mCobraGuideStyle);','      root.put("preview_view_attached",mCobraPreviewTexture!=null&&mCobraPreviewTexture.isAttachedToWindow());\n      root.put("preview_texture_available",mCobraPreviewTexture!=null&&mCobraPreviewTexture.isAvailable());\n      root.put("preview_width",mCobraPreviewTexture==null?0:mCobraPreviewTexture.getWidth());\n      root.put("preview_height",mCobraPreviewTexture==null?0:mCobraPreviewTexture.getHeight());\n      root.put("system_dark_palette",cobraSystemDarkVariant());\n      root.put("effective_appearance",cobraEffectiveAppearanceMode());\n      root.put("view_mode",mCobraGuideStyle);'))
 index=text.rfind('\n}');text=text[:index]+'\n'+(ROOT/'presentation.java.inc').read_text()+text[index:]
 # Whole-file preimage, explicit changed-member allowlist, preservation checks for every other method.
 names=set(re.findall(r'^  (?:private|public|protected) [^\n;=(){}]*\b([A-Za-z0-9_]+)\s*\(',before,re.M))
 targeted={n for _,n in changed};protected=[]
 for name in sorted(names-targeted):
  try:a,b=span(before,name);c,d=span(text,name)
  except ValueError:continue
  if before[a:b]!=text[c:d]:raise ValueError('Unexpected method delta: '+name)
  protected.append(name)
 for name in ('CobraPlayerBinding','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow'):
  a,b=span(before,name,'class');c,d=span(text,name,'class');assert before[a:b]==text[c:d],name
 return text,{'base_sha256':sha(before),'after_sha256':sha(text),'changed_members':changed,'protected_methods':protected,'native_modified':False,'device_verified':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 path=a.source/REL;before=path.read_text();text,report=patch(before)
 receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
 if data['version_code']!=2103156:raise ValueError('Expected full 2103156 stack')
 for rel,row in data['files'].items():
  if sha((a.source/rel).read_bytes())!=row['after']:raise ValueError('Source receipt drift: '+rel)
 path.write_text(text);data['files'][REL]['after']=sha(text);receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n');print('PASS: exact 2103156 patch applied; protected methods:',len(report['protected_methods']))
if __name__=='__main__':main()
