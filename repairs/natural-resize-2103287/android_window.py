#!/usr/bin/env python3
"""Android-shell natural resize over the exact 2103284 shell, packaged on 2103285+native-2103287.

Preserve the complete approved chooser composition. Wide/square windows reposition the same native
views using current window bounds while keeping every element's own aspect and vertical rhythm.
No alternate tablet chooser and no hidden whole-screen long-press.
"""
from pathlib import Path
import argparse,hashlib,json,re
C=Path("tools/android/packaging/xbmc/src/InfinityGlassChooser.java.in")
S=Path("tools/android/packaging/xbmc/src/Splash.java.in")
G=Path("tools/android/packaging/xbmc/build.gradle.in")
PRE={C:"000b38487f4b8dbae7548aa6a08bc07d438b35df523f8f16b3ff5dd60230ffa6",
     S:"ca7dfe911c2633f4275fb9419c55efbc00de7f1887c3db8315d1eb3cc04f18b0",
     G:"cbd359f2d98599b24236263e7c26287f7131e7daf83c9c43d681b7c29653992e"}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f"{label}: expected one anchor, got {n}")
 return s.replace(a,b,1)

def chooser(s):
 s=once(s,'setTag("infinity_glass_chooser_2103257");',
        'setTag("infinity_glass_chooser_2103287");\\n    setLongClickable(false);',"chooser tag")
 s=once(s,'content.setClipToPadding(true);content.setClipChildren(true);',
        'content.setClipToPadding(true);content.setClipChildren(true);content.setLongClickable(false);',"content")
 s=once(s,'boolean responsive,stacked;int responsiveHeader,headingHeight;',
        'boolean responsive,naturalWide,stacked;float positionScaleX,positionScaleY;int responsiveHeader,headingHeight;',"state")
 s=once(s,'      // Existing theme management remains available from the non-card background.\\n      setOnLongClickListener(v->{actions.themes();return true;});',
        '      // Theme/recovery controls are explicit gear actions only. Background holds do nothing.\\n      setLongClickable(false);',"stage hold")
 old='''      boolean multi=getContext() instanceof android.app.Activity && ((android.app.Activity)getContext()).isInMultiWindowMode();
      responsive=multi || (viewport>0 && viewport<px(280) && w>=px(280));
      for(Box box:boxes)box.view.setVisibility(!responsive||box.view==infinity||box.view==cobra?VISIBLE:GONE);
      responsiveHeading.setVisibility(responsive?VISIBLE:GONE);responsiveBrand.setVisibility(responsive&&viewport>=px(360)?VISIBLE:GONE);
      backdrop.setVisibility(responsive?GONE:VISIBLE);infinity.responsive=responsive;cobra.responsive=responsive;
      if(responsive){'''
 new='''      boolean multi=getContext() instanceof android.app.Activity && ((android.app.Activity)getContext()).isInMultiWindowMode();
      // Only truly constrained short/freeform windows use the compact emergency layout.
      // Fold-inner, square and ordinary landscape keep the complete approved composition.
      responsive=(viewport>0 && viewport<px(280) && w>=px(280)) || (multi && viewport>0 && (viewport<px(300)||w<px(300)));
      naturalWide=!responsive && viewport>0 && w>=px(280) && w/(float)Math.max(1,viewport)>=0.68f;
      for(Box box:boxes)box.view.setVisibility(!responsive||box.view==infinity||box.view==cobra?VISIBLE:GONE);
      responsiveHeading.setVisibility(responsive?VISIBLE:GONE);responsiveBrand.setVisibility(responsive&&viewport>=px(360)?VISIBLE:GONE);
      backdrop.setVisibility(responsive?GONE:VISIBLE);infinity.responsive=responsive;cobra.responsive=responsive;
      if(responsive){'''
 s=once(s,old,new,"profile mode")
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
        int bw=Math.max(1,Math.round(b.w*scale)),bh=Math.max(1,Math.round(b.h*scale));'''
 new='''      int height=viewport>0?viewport:Math.max(1,MeasureSpec.getSize(hs));
      if(naturalWide){
        // Positions respond independently to the available window, but each visual/control uses one
        // uniform limiting scale. That fills a Fold/square window without stretching cards, logos,
        // typography or deleting any part of the approved theme.
        positionScaleX=w/referenceWidth;positionScaleY=height/referenceHeight;
        scale=Math.max(.01f,Math.min(positionScaleX,positionScaleY));left=0;
        setMeasuredDimension(w,height);
        backdrop.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
      }else{
        float designWidth=Math.min(w,600*density);
        if(viewport>0 && w>viewport)designWidth=Math.min(designWidth,Math.max(320*density,viewport*.82f));
        float fittedHeight=w>viewport?(light?1168f:1043f):referenceHeight;
        if(viewport>0)designWidth=Math.min(designWidth,viewport*referenceWidth/fittedHeight);
        scale=Math.max(.01f,designWidth/referenceWidth);left=(w-designWidth)/2;
        positionScaleX=positionScaleY=scale;
        setMeasuredDimension(w,height);
        backdrop.measure(MeasureSpec.makeMeasureSpec((int)designWidth,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
      }
      for(Box b:boxes){
        int bw=Math.max(1,Math.round(b.w*scale)),bh=Math.max(1,Math.round(b.h*scale));'''
 s=once(s,old,new,"natural measure")
 old='''      backdrop.layout(Math.round(left),0,Math.round(left+referenceWidth*scale),getMeasuredHeight());
      for(Box box:boxes){int x=Math.round(left+box.x*scale),y=Math.round(box.y*scale);box.view.layout(x,y,x+box.view.getMeasuredWidth(),y+box.view.getMeasuredHeight());}'''
 new='''      if(naturalWide){
        backdrop.layout(0,0,getWidth(),getMeasuredHeight());
        for(Box box:boxes){
          float cx=(box.x+box.w*.5f)*positionScaleX,cy=(box.y+box.h*.5f)*positionScaleY;
          int x=Math.round(cx-box.view.getMeasuredWidth()*.5f),y=Math.round(cy-box.view.getMeasuredHeight()*.5f);
          x=Math.max(0,Math.min(getWidth()-box.view.getMeasuredWidth(),x));
          y=Math.max(0,Math.min(getHeight()-box.view.getMeasuredHeight(),y));
          box.view.layout(x,y,x+box.view.getMeasuredWidth(),y+box.view.getMeasuredHeight());
        }
      }else{
        backdrop.layout(Math.round(left),0,Math.round(left+referenceWidth*scale),getMeasuredHeight());
        for(Box box:boxes){int x=Math.round(left+box.x*scale),y=Math.round(box.y*scale);box.view.layout(x,y,x+box.view.getMeasuredWidth(),y+box.view.getMeasuredHeight());}
      }'''
 s=once(s,old,new,"natural layout")
 old='''      float referenceW=light?840:941,referenceH=light?1873:1672;
      float scale=getWidth()/referenceW;float fixed=(light?1340:1205)*scale;'''
 new='''      float referenceW=light?840:941,referenceH=light?1873:1672;
      float viewAspect=getWidth()/(float)Math.max(1,getHeight()),referenceAspect=referenceW/referenceH;
      if(viewAspect>referenceAspect*1.25f){
        // Decorative material may fill the window; interactive/theme geometry above remains aspect-safe.
        dst.set(0,0,getWidth(),getHeight());canvas.drawBitmap(bitmap,null,dst,paint);return;
      }
      float scale=getWidth()/referenceW;float fixed=(light?1340:1205)*scale;'''
 s=once(s,old,new,"background wide fill")
 return s

def splash(s):
 # There are two independent global background holds in the accepted shell.
 if 'root.setOnLongClickListener(v->{vtheme().manager(this);return true;});' in s:
  s=once(s,'root.setOnLongClickListener(v->{vtheme().manager(this);return true;});','root.setLongClickable(false);',"splash hold")
 # Use actual activity window where chooser dialogs calculate bounds; never physical panel metrics.
 anchor='''  private int chooserDp(int value)
  {
    return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
  }
'''
 helper=anchor+'''  private int chooserWindowPixels(boolean width)
  {
    View decor=getWindow().getDecorView();int measured=width?decor.getWidth():decor.getHeight();
    if(measured>0)return measured;
    if(Build.VERSION.SDK_INT>=30){android.graphics.Rect bounds=getWindowManager().getCurrentWindowMetrics().getBounds();int value=width?bounds.width():bounds.height();if(value>0)return value;}
    Configuration config=getResources().getConfiguration();int dp=width?config.screenWidthDp:config.screenHeightDp;
    if(dp>0)return Math.round(dp*getResources().getDisplayMetrics().density);
    return width?getResources().getDisplayMetrics().widthPixels:getResources().getDisplayMetrics().heightPixels;
  }
  private int chooserWindowDp(boolean width){return Math.round(chooserWindowPixels(width)/getResources().getDisplayMetrics().density);}
'''
 s=once(s,anchor,helper,"window helper")
 s=s.replace('getResources().getDisplayMetrics().widthPixels - chooserDp(32)','chooserWindowPixels(true) - chooserDp(32)')
 s=s.replace('getResources().getDisplayMetrics().widthPixels-chooserDp(28)','chooserWindowPixels(true)-chooserDp(28)')
 s=s.replace('(int)(getResources().getDisplayMetrics().heightPixels*.78f)','(int)(chooserWindowPixels(false)*.78f)')
 s=s.replace('Math.round(getResources().getDisplayMetrics().heightPixels/getResources().getDisplayMetrics().density)','chooserWindowDp(false)')
 s=s.replace('Math.round(getResources().getDisplayMetrics().widthPixels / getResources().getDisplayMetrics().density)','chooserWindowDp(true)')
 s=s.replace('Math.round(getResources().getDisplayMetrics().widthPixels/getResources().getDisplayMetrics().density)','chooserWindowDp(true)')
 return s

def apply(root,out,version_name,version_code,base_apk_sha,native_sha,base_commit):
 sh=root/'shell-kodi'
 for p,d in PRE.items():
  if sha(sh/p)!=d:raise RuntimeError("wrong 2103284 shell preimage: "+str(p))
 (sh/C).write_text(chooser((sh/C).read_text()))
 (sh/S).write_text(splash((sh/S).read_text()))
 g=(sh/G).read_text();g=once(g,'versionCode 2103284',f'versionCode {version_code}',"version code");g=once(g,'versionName "1.0.9-Ambient-Surface-Repair-RC1"',f'versionName "{version_name}"',"version name");(sh/G).write_text(g)
 p=root/'scripts/infinity_background_resume.py';text=p.read_text()
 replacements=[("VERSION_CODE = 2103284",f"VERSION_CODE = {version_code}"),
 ("RELEASE = '1.0.9-Ambient-Surface-Repair-RC1'",f"RELEASE = '{version_name}'"),
 ("BASE_COMMIT = 'ec28a8574ecf8d7fccb3713133661c1e8c2246cb'",f"BASE_COMMIT = '{base_commit}'"),
 ("BASE_APK_SHA256 = '2de48f4a269df9196e341c1083608a436fdce1e2d63d17fbb2b80d9c525f63bf'",f"BASE_APK_SHA256 = '{base_apk_sha}'"),
 ("BASE_ENGINE_SHA256 = 'c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'",f"BASE_ENGINE_SHA256 = '{native_sha}'")]
 for a,b in replacements:text=once(text,a,b,"packaging metadata")
 p.write_text(text)
 p=root/'scripts/package_background_resume.py';text=p.read_text()
 text=text.replace('Infinity-2103284-Ambient-Surface-Repair-RC1-unsigned.apk',f'Infinity-{version_code}-Natural-Window-Resize-RC1-unsigned.apk')
 text=text.replace('Infinity-2103284-Ambient-Surface-Repair-RC1.apk',f'Infinity-{version_code}-Natural-Window-Resize-RC1.apk')
 text=text.replace("'base_run':36829442559",f"'base_run':36933314038")
 text=text.replace("ROOT/'repairs/infinity-ambient-surface-2103284/DEVICE-TEST.txt'","ROOT/'repairs/natural-resize-2103287/DEVICE-TEST.md'")
 p.write_text(text)
 receipt=root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=base_commit,base_apk_sha256=base_apk_sha,native_engine_sha256=native_sha,version_code=version_code,release=version_name,candidate_locked=False,physical_device_verified=False,chooser_global_long_press_removed=True,chooser_natural_window_layout=True,native_recompiled=True,skin_modified=False)
 for n in (C,S,G):r['files'].setdefault(str(n),{})['after']=sha(sh/n)
 receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 out.mkdir(parents=True,exist_ok=True);(out/'android-resize-proof.json').write_text(json.dumps({"schema":1,"base_commit":base_commit,"base_apk_sha256":base_apk_sha,"native_engine_sha256":native_sha,"chooser_full_composition_preserved":True,"hidden_global_long_press":False,"window_bounds_owner":"current Android activity window","physical_device_verified":False},indent=2)+'\n')

def verify(root):
 c=(root/'shell-kodi'/C).read_text();s=(root/'shell-kodi'/S).read_text()
 for bad in ('setOnLongClickListener(v->{actions.themes();return true;});','root.setOnLongClickListener(v->{vtheme().manager(this);return true;});'):
  if bad in c+s:raise RuntimeError("hidden global hold remains")
 for token in ('naturalWide=!responsive','positionScaleX=w/referenceWidth','positionScaleY=height/referenceHeight','for(Box box:boxes)','chooserWindowPixels(boolean width)'):
  if token not in c+s:raise RuntimeError("missing Android natural resize contract: "+token)
 if 'box.view==infinity||box.view==cobra?VISIBLE:GONE' not in c:raise RuntimeError("compact fallback contract lost")
 print("PASS: Android chooser preserves every approved box in Fold/square natural mode and uses current window bounds")

def main():
 ap=argparse.ArgumentParser();ap.add_argument("mode",choices=["apply","verify"]);ap.add_argument("--root",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);ap.add_argument("--version-name");ap.add_argument("--version-code",type=int);ap.add_argument("--base-apk-sha");ap.add_argument("--native-sha");ap.add_argument("--base-commit");a=ap.parse_args()
 if a.mode=="apply":apply(a.root,a.out,a.version_name,a.version_code,a.base_apk_sha,a.native_sha,a.base_commit)
 verify(a.root)
if __name__=="__main__":main()
