#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,sys,difflib
import importlib.util
spec=importlib.util.spec_from_file_location('display268',Path(__file__).resolve().parent.parent/'display-player-2103268/apply.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
span,member,once,sha=old.span,old.member,old.once,old.sha
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
CHOOSER='tools/android/packaging/xbmc/src/InfinityGlassChooser.java.in'
PARENT_APK='de03a34643a4693162c2cd46912b826b4a77aaafbb4491ce46d1d33bf1f6d4e8'
PARENT_COMMIT='46de646cc8a87c4dfafe2e7bf9b1776c011cadeb'
ALLOWED=['isCompact','isMedium','isPortrait','cobraWidthDp','cobraHeightDp','toggleCobraDrawer','cobraBuildPlayerChrome']
HELPERS='''
  /** Current UI window, never the physical panel size. No navigation/media ownership. */
  private int cobraWindowPixels(boolean width){
    View decor=getWindow().getDecorView();int measured=width?decor.getWidth():decor.getHeight();
    if(measured>0)return measured;
    if(Build.VERSION.SDK_INT>=30){android.graphics.Rect bounds=getWindowManager().getCurrentWindowMetrics().getBounds();return width?bounds.width():bounds.height();}
    Configuration config=getResources().getConfiguration();int dp=width?config.screenWidthDp:config.screenHeightDp;
    if(dp>0)return Math.round(dp*getResources().getDisplayMetrics().density);
    return width?getResources().getDisplayMetrics().widthPixels:getResources().getDisplayMetrics().heightPixels;
  }
'''
def activity(s):
 for name,code in {
  'isCompact':'  private boolean isCompact(){return cobraWidthDp()<600;}',
  'isMedium':'  private boolean isMedium(){int width=cobraWidthDp();return width>=600&&width<840;}',
  'isPortrait':'  private boolean isPortrait(){return cobraHeightDp()>=cobraWidthDp();}',
  'cobraWidthDp':'  private int cobraWidthDp(){return Math.round(cobraWindowPixels(true)/getResources().getDisplayMetrics().density);}',
  'cobraHeightDp':'  private int cobraHeightDp(){return Math.round(cobraWindowPixels(false)/getResources().getDisplayMetrics().density);}'}.items():s=member(s,name,code)
 a,b=span(s,'toggleCobraDrawer');v=s[a:b]
 anchor='shield.addView(panel,new FrameLayout.LayoutParams(width,-1,Gravity.LEFT));decor.addView(shield,new FrameLayout.LayoutParams(-1,-1));'
 v=once(v,anchor,anchor+'''
    shield.addOnLayoutChangeListener((view,l,t,r,b,ol,ot,or,ob)->{
      if(r-l==or-ol)return;int actual=Math.max(1,r-l);
      int next=Math.max(1,Math.min(actual-dp(24),Math.min(dp(340),Math.max(dp(236),Math.round(actual*.80f)))));
      FrameLayout.LayoutParams position=(FrameLayout.LayoutParams)panel.getLayoutParams();
      if(position.width!=next){position.width=next;panel.setLayoutParams(position);}
    });''')
 s=s[:a]+v+s[b:]
 a,b=span(s,'cobraBuildPlayerChrome');v=s[a:b]
 v=once(v,'header.setPadding(left,top,right,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.4",6)));','header.setPadding(left,height<dp(240)?0:top,right,height<dp(240)?0:dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.4",6)));')
 v=once(v,'footer.addView(programLine,new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.27",30))));','if(height<dp(300))programLine.setVisibility(View.GONE);footer.addView(programLine,new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.27",30))));')
 s=s[:a]+v+s[b:];return s[:s.rfind('\n}')]+HELPERS+s[s.rfind('\n}'):]

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();shell=a.root/'shell-kodi';a.out.mkdir(parents=True,exist_ok=True)
 f=shell/ACTIVITY;before=f.read_text();assert sha(f.read_bytes())=='1eb04d22d7cfe344c34a270dc7d30949b6c0377360b95b65eb5525dbdf789bbc';f.write_text(activity(before))
 chooser=shell/CHOOSER;original=chooser.read_text();chooser.write_text((Path(__file__).parent/'InfinityGlassChooser.java.in').read_text())
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';gradle.write_text(gradle.read_text().replace('2103268','2103269').replace('1.0.9-Cobra-Display-Player-RC1','1.0.9-Responsive-Window-RC1'))
 script=a.root/'scripts/infinity_background_resume.py';v=script.read_text().replace('VERSION_CODE = 2103268','VERSION_CODE = 2103269').replace("RELEASE = '1.0.9-Cobra-Display-Player-RC1'","RELEASE = '1.0.9-Responsive-Window-RC1'").replace("BASE_COMMIT = '292351efa4e0840c1f01b343a81e62b8905ba3f0'","BASE_COMMIT = '"+PARENT_COMMIT+"'").replace("BASE_APK_SHA256 = '686d606534906358d35934bf6430972279efeab387731b4178d2dfbd2fe12070'","BASE_APK_SHA256 = '"+PARENT_APK+"'");script.write_text(v)
 package=a.root/'scripts/package_background_resume.py';v=package.read_text().replace('Infinity-2103268-Cobra-Display-Player-RC1','Infinity-2103269-Responsive-Window-RC1').replace("'base_run':36684966394","'base_run':36699564793").replace("ROOT/'repairs/display-player-2103268/DEVICE-TEST.md'","ROOT/'repairs/responsive-window-2103269/DEVICE-TEST.md'");package.write_text(v)
 receipt=a.root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK,version_code=2103269,release='1.0.9-Responsive-Window-RC1',candidate_locked=False,physical_device_verified=False)
 for n in [ACTIVITY,CHOOSER,'tools/android/packaging/xbmc/build.gradle.in']:r['files'].setdefault(n,{})['after']=sha((shell/n).read_bytes())
 receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 (a.out/'responsive.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),f.read_text().splitlines(True),fromfile='candidate268/'+ACTIVITY,tofile='candidate269/'+ACTIVITY))+''.join(difflib.unified_diff(original.splitlines(True),chooser.read_text().splitlines(True),fromfile='candidate268/'+CHOOSER,tofile='candidate269/'+CHOOSER)))
 print('Applied bounded presentation-only responsive changes; player/provider/native/skin source unchanged.')
if __name__=='__main__':main()
