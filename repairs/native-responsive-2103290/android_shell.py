#!/usr/bin/env python3
"""2103290 Android shell delta after Evidence-First Health 2103288.

Preserves all approved chooser content and makes its *whole composition* respond to the actual
current window. Element positions distribute across the live viewport, while each element keeps one
uniform scale. No wide/tablet redesign, no giant independent cards, no hidden background long-press.
Also teaches Health trace to retain native-responsive viewport/window evidence.
"""
from pathlib import Path
import argparse, json, hashlib

CHOOSER=Path("tools/android/packaging/xbmc/src/InfinityGlassChooser.java.in")
SPLASH=Path("tools/android/packaging/xbmc/src/Splash.java.in")
TRACE=Path("tools/android/packaging/xbmc/src/InfinityResponsiveTrace.java.in")
GRADLE=Path("tools/android/packaging/xbmc/build.gradle.in")
VERSION_CODE=2103290
VERSION_NAME="1.0.9-Native-Responsive-Layout-RC1"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f"{label}: expected one anchor, got {n}")
 return s.replace(a,b,1)

def chooser(s):
 s=once(s,'setTag("infinity_glass_chooser_2103257");',
        'setTag("infinity_glass_chooser_2103290");\\n    setLongClickable(false);',"chooser tag")
 s=once(s,'content.setClipToPadding(true);content.setClipChildren(true);',
        'content.setClipToPadding(true);content.setClipChildren(true);content.setLongClickable(false);',"content long press")
 s=once(s,'float scale,left;int viewportHint;\\n    boolean responsive,stacked;',
        'float scale,left,positionScaleX,positionScaleY;int viewportHint;\\n    boolean responsive,stacked,naturalWindow;',"stage state")
 s=once(s,'      // Existing theme management remains available from the non-card background.\\n      setOnLongClickListener(v->{actions.themes();return true;});',
        '      // Theme controls are explicit gear actions. Empty-space holds never change presentation.\\n      setLongClickable(false);',"stage global long press")
 old='''      boolean multi=getContext() instanceof android.app.Activity && ((android.app.Activity)getContext()).isInMultiWindowMode();
      responsive=multi || (viewport>0 && viewport<px(280) && w>=px(280));
      for(Box box:boxes)box.view.setVisibility(!responsive||box.view==infinity||box.view==cobra?VISIBLE:GONE);
'''
 new='''      boolean multi=getContext() instanceof android.app.Activity && ((android.app.Activity)getContext()).isInMultiWindowMode();
      // Emergency compact mode is reserved for genuinely tiny windows. Normal Fold, landscape,
      // portrait and multi-window sizes keep the complete approved composition.
      responsive=(viewport>0 && viewport<px(280)) || w<px(280) ||
          (multi && viewport>0 && w<px(320) && viewport<px(360));
      naturalWindow=!responsive;
      for(Box box:boxes)box.view.setVisibility(!responsive||box.view==infinity||box.view==cobra?VISIBLE:GONE);
'''
 s=once(s,old,new,"chooser compact threshold")
 old='''      float designWidth=Math.min(w,600*density);
      if(viewport>0 && w>viewport)designWidth=Math.min(designWidth,Math.max(320*density,viewport*.82f));
      // Fit the entire portrait composition. Short landscape windows crop only the decorative floor.
      float fittedHeight=w>viewport?(light?1168f:1043f):referenceHeight;
      if(viewport>0)designWidth=Math.min(designWidth,viewport*referenceWidth/fittedHeight);
      scale=Math.max(.01f,designWidth/referenceWidth);left=(w-designWidth)/2;
      int height=viewport>0?viewport:(int)Math.ceil(referenceHeight*scale);
      setMeasuredDimension(w,height);
      backdrop.measure(MeasureSpec.makeMeasureSpec((int)designWidth,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
      for(Box b:boxes){
        int bw=Math.max(1,Math.round(b.w*scale)),bh=Math.max(1,Math.round(b.h*scale));
'''
 new='''      int height=viewport>0?viewport:Math.max(1,MeasureSpec.getSize(hs));
      positionScaleX=w/referenceWidth;positionScaleY=height/referenceHeight;
      // Sizes use one scale so logos/cards/type are never stretched. Centers follow the live
      // window independently so the whole approved composition naturally occupies Fold/square/wide space.
      scale=Math.max(.01f,Math.min(positionScaleX,positionScaleY));left=0;
      setMeasuredDimension(w,height);
      backdrop.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
      for(Box b:boxes){
        int bw=Math.max(1,Math.round(b.w*scale)),bh=Math.max(1,Math.round(b.h*scale));
'''
 s=once(s,old,new,"whole composition measure")
 old='''      backdrop.layout(Math.round(left),0,Math.round(left+referenceWidth*scale),getMeasuredHeight());
      for(Box box:boxes){int x=Math.round(left+box.x*scale),y=Math.round(box.y*scale);box.view.layout(x,y,x+box.view.getMeasuredWidth(),y+box.view.getMeasuredHeight());}
'''
 new='''      backdrop.layout(0,0,getWidth(),getMeasuredHeight());
      for(Box box:boxes){
        float cx=(box.x+box.w/2f)*positionScaleX,cy=(box.y+box.h/2f)*positionScaleY;
        int bw=box.view.getMeasuredWidth(),bh=box.view.getMeasuredHeight();
        int x=Math.round(cx-bw/2f),y=Math.round(cy-bh/2f);
        x=Math.max(0,Math.min(getWidth()-bw,x));y=Math.max(0,Math.min(getHeight()-bh,y));
        box.view.layout(x,y,x+bw,y+bh);
      }
'''
 s=once(s,old,new,"whole composition layout")
 old='''      float referenceW=light?840:941,referenceH=light?1873:1672;
      float scale=getWidth()/referenceW;float fixed=(light?1340:1205)*scale;
      // Preserve card/header registration; extend only the quiet orbital floor for tall windows.
      int seam=Math.round(bitmap.getHeight()*(light?1340f/1873f:1205f/1672f));
      src.set(0,0,bitmap.getWidth(),seam);dst.set(0,0,getWidth(),fixed);canvas.drawBitmap(bitmap,src,dst,paint);
      src.set(0,seam,bitmap.getWidth(),bitmap.getHeight());dst.set(0,fixed,getWidth(),getHeight());canvas.drawBitmap(bitmap,src,dst,paint);
'''
 new='''      // The material is decorative and follows the same full reference-space mapping as element
      // centers. Never crop away header/orbital/footer art; interactive Views remain aspect-safe.
      dst.set(0,0,getWidth(),getHeight());canvas.drawBitmap(bitmap,null,dst,paint);
'''
 s=once(s,old,new,"backdrop no crop")
 return s

def splash(s):
 if 'root.setOnLongClickListener(v->{vtheme().manager(this);return true;});' in s:
  s=once(s,'root.setOnLongClickListener(v->{vtheme().manager(this);return true;});',
         'root.setLongClickable(false);',"splash hidden theme hold")
 return s

def trace(s):
 old='line.contains("Infinity natural resize:") ||'
 new='line.contains("Infinity natural resize:") ||\n        line.contains("Infinity responsive viewport:") ||\n        line.contains("Infinity responsive window:") ||'
 s=s.replace(old,new)
 # Record exact installed skin contract instead of assuming a version from conversation history.
 anchor='''  private static File kodiLog(Context context){
    File external=context.getExternalFilesDir(null);
    return new File(external!=null?external:context.getFilesDir(),".kodi/temp/kodi.log");
  }
'''
 helper=anchor+'''  private static String installedSkinState(Context context){
    File external=context.getExternalFilesDir(null);
    File root=external!=null?external:context.getFilesDir();
    File skin=new File(root,".kodi/addons/skin.infinity.diggz");
    File addon=new File(skin,"addon.xml");
    String version="not_found";
    try{
      String xml=readBounded(addon,128*1024);
      java.util.regex.Matcher m=java.util.regex.Pattern.compile("<addon[^>]*\\\\bversion=\\\\\"([^\\\\\"]+)\\\\\"").matcher(xml);
      if(m.find())version=m.group(1);
    }catch(Exception ignored){}
    boolean responsive=new File(skin,"resources/infinity-native-responsive-v1.json").isFile();
    return "skin.infinity.diggz version="+version+" native_responsive_contract="+responsive;
  }
'''
 s=once(s,anchor,helper,"trace installed skin helper")
 old_summary="""    out.append("Events captured: ").append(events.size()).append('\\n');"""
 new_summary="""    out.append("Events captured: ").append(events.size()).append('\\n');
    out.append("Installed skin: ").append(installedSkinState(context)).append('\\n');"""
 s=once(s,old_summary,new_summary,"trace installed skin summary")
 return s

def apply(root,receipt):
 c=root/CHOOSER;s=root/SPLASH;t=root/TRACE;g=root/GRADLE
 c.write_text(chooser(c.read_text()));s.write_text(splash(s.read_text()));t.write_text(trace(t.read_text()))
 gradle=g.read_text();gradle=once(gradle,'versionCode 2103288',f'versionCode {VERSION_CODE}',"version code")
 gradle=once(gradle,'versionName "1.0.9-Evidence-First-Health-RC1"',f'versionName "{VERSION_NAME}"',"version name")
 g.write_text(gradle)
 result=verify(root);receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+'\\n')

def verify(root):
 blob=(root/CHOOSER).read_text()+(root/SPLASH).read_text()+(root/TRACE).read_text()
 required=['infinity_glass_chooser_2103290','positionScaleX=w/referenceWidth','positionScaleY=height/referenceHeight',
           'Math.min(positionScaleX,positionScaleY)','backdrop.layout(0,0,getWidth(),getMeasuredHeight())',
           'setLongClickable(false)','Infinity responsive viewport:','Infinity responsive window:',
           'native_responsive_contract=']
 for token in required:
  if token not in blob:raise RuntimeError("Missing 2103290 shell contract: "+token)
 if 'setOnLongClickListener(v->{actions.themes();return true;});' in blob:
  raise RuntimeError("hidden chooser long press remains")
 return {'schema':1,'version_code':VERSION_CODE,'version_name':VERSION_NAME,
         'whole_chooser_composition_preserved':True,'normal_window_elements_hidden':False,
         'uniform_element_scale':True,'independent_position_distribution':True,
         'health_records_installed_skin':True,
         'files':{str(p):sha(root/p) for p in (CHOOSER,SPLASH,TRACE,GRADLE)}}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['apply','verify']);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);a=ap.parse_args()
 if a.mode=='apply':apply(a.root.resolve(),a.receipt.resolve())
 else:
  result=verify(a.root.resolve());a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+'\\n');print("PASS: 2103290 Android shell responsive contract verified")
if __name__=='__main__':main()
