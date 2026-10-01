#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
REL='1.0.9-Chooser-Responsive-Repair-RC1';VC=2103286
BC='c0c150b30008cee17df39e2a79a0c07e9a91f72a';BA='64ed5ce79096a3e09d02907cf72d3a5c4ad20186da231898c92db83e540d266b';BE='f6eb05f091bfe7a624105a0a83744a292e229b385d39c1b6a23f8bf954a2522a'
C='tools/android/packaging/xbmc/src/InfinityGlassChooser.java.in';S='tools/android/packaging/xbmc/src/Splash.java.in';G='tools/android/packaging/xbmc/build.gradle.in'
PRE={C:'000b38487f4b8dbae7548aa6a08bc07d438b35df523f8f16b3ff5dd60230ffa6',S:'ca7dfe911c2633f4275fb9419c55efbc00de7f1887c3db8315d1eb3cc04f18b0',G:'cbd359f2d98599b24236263e7c26287f7131e7daf83c9c43d681b7c29653992e'}
h=lambda b:hashlib.sha256(b).hexdigest()
def rep(s,a,b,n=1):
 if s.count(a)!=n:raise RuntimeError(f'preimage count {s.count(a)} != {n}: {a[:90]!r}')
 return s.replace(a,b)
def patch_chooser(s):
 s=rep(s,'setTag("infinity_glass_chooser_2103257");','setTag("infinity_glass_chooser_2103286");\n    // No hidden chooser gestures; theme/recovery lives behind explicit gear controls.\n    setLongClickable(false);')
 s=rep(s,'content.setClipToPadding(true);content.setClipChildren(true);','content.setClipToPadding(true);content.setClipChildren(true);content.setLongClickable(false);')
 s=rep(s,'boolean responsive,stacked;int responsiveHeader,headingHeight;','boolean responsive,compactResponsive,adaptiveWide,stacked;int responsiveHeader,headingHeight;')
 s=rep(s,'// Existing theme management remains available from the non-card background.\n      setOnLongClickListener(v->{actions.themes();return true;});','// A hold on unused chooser space intentionally does nothing.\n      setLongClickable(false);')
 s=rep(s,'responsive=multi || (viewport>0 && viewport<px(280) && w>=px(280));','''float aspect=viewport>0?w/(float)Math.max(1,viewport):0f;
      compactResponsive=(viewport>0 && viewport<px(280) && w>=px(280)) || (multi && (viewport<px(440)||w<px(520)));
      adaptiveWide=!compactResponsive && viewport>0 && w>=px(280) && (aspect>=0.68f || w>=px(600));
      responsive=compactResponsive||adaptiveWide;''')
 s=rep(s,'responsiveHeading.setVisibility(responsive?VISIBLE:GONE);responsiveBrand.setVisibility(responsive&&viewport>=px(360)?VISIBLE:GONE);\n      backdrop.setVisibility(responsive?GONE:VISIBLE);infinity.responsive=responsive;cobra.responsive=responsive;','''responsiveHeading.setVisibility(responsive?VISIBLE:GONE);responsiveBrand.setVisibility(responsive&&viewport>=px(360)?VISIBLE:GONE);
      backdrop.setVisibility(compactResponsive?GONE:VISIBLE);infinity.responsive=responsive;cobra.responsive=responsive;infinity.adaptive=adaptiveWide;cobra.adaptive=adaptiveWide;''')
 s=rep(s,'int h=Math.max(1,viewport),margin=px(12),gap=px(12);','int h=Math.max(1,viewport),margin=px(adaptiveWide?18:12),gap=px(adaptiveWide?18:12);')
 s=rep(s,'px(20)*Math.min(1.4f,font)','px(adaptiveWide?22:20)*Math.min(1.4f,font)')
 s=rep(s,'headingHeight=Math.max(px(32),responsiveHeading.getMeasuredHeight());','headingHeight=Math.max(px(adaptiveWide?36:32),responsiveHeading.getMeasuredHeight());')
 s=rep(s,'int header=px(16)+headingHeight+(responsiveBrand.getVisibility()==VISIBLE?px(28):0);responsiveHeader=header;\n        stacked=w<px(360)&&h>=px(440);\n        int usableW=Math.max(1,w-2*margin),usableH=Math.max(1,h-header-margin);\n        if(stacked){int ch=Math.max(1,(usableH-gap)/2);infinityBounds.set(margin,header,margin+usableW,header+ch);cobraBounds.set(margin,header+ch+gap,margin+usableW,h-margin);}\n        else{int cw=Math.max(1,(usableW-gap)/2);infinityBounds.set(margin,header,margin+cw,h-margin);cobraBounds.set(margin+cw+gap,header,w-margin,h-margin);}','''int header=px(adaptiveWide?20:16)+headingHeight+(responsiveBrand.getVisibility()==VISIBLE?px(28):0);responsiveHeader=header;
        int usableW=Math.max(1,w-2*margin),usableH=Math.max(1,h-header-margin);stacked=!adaptiveWide&&w<px(360)&&h>=px(440);
        if(adaptiveWide){
          float ir=infinity.rw/infinity.rh,cr=cobra.rw/cobra.rh;int cardH=usableH,iw=Math.max(1,Math.round(cardH*ir)),cw=Math.max(1,Math.round(cardH*cr));int room=Math.max(2,usableW-gap);
          if(iw+cw>room){float fit=room/(float)(iw+cw);iw=Math.max(1,Math.round(iw*fit));cw=Math.max(1,room-iw);cardH=Math.max(1,Math.min(usableH,Math.round(Math.min(iw/ir,cw/cr))));iw=Math.max(1,Math.round(cardH*ir));cw=Math.max(1,Math.round(cardH*cr));}
          int total=iw+gap+cw,x=Math.max(margin,(w-total)/2),y=header+Math.max(0,(usableH-cardH)/2);infinityBounds.set(x,y,x+iw,y+cardH);cobraBounds.set(x+iw+gap,y,x+iw+gap+cw,y+cardH);
          backdrop.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(h,MeasureSpec.EXACTLY));
        }else if(stacked){int ch=Math.max(1,(usableH-gap)/2);infinityBounds.set(margin,header,margin+usableW,header+ch);cobraBounds.set(margin,header+ch+gap,margin+usableW,h-margin);}
        else{int cw=Math.max(1,(usableW-gap)/2);infinityBounds.set(margin,header,margin+cw,h-margin);cobraBounds.set(margin+cw+gap,header,w-margin,h-margin);}''')
 s=rep(s,'responsiveHeading.layout(px(12),px(8),getWidth()-px(12),px(8)+headingHeight);\n        responsiveBrand.layout(px(12),px(10)+headingHeight,getWidth()-px(12),px(34)+headingHeight);','''if(adaptiveWide)backdrop.layout(0,0,getWidth(),getHeight());int rm=px(adaptiveWide?18:12),ht=px(adaptiveWide?10:8);
        responsiveHeading.layout(rm,ht,getWidth()-rm,ht+headingHeight);responsiveBrand.layout(rm,ht+headingHeight+px(2),getWidth()-rm,ht+headingHeight+px(26));''')
 s=rep(s,'boolean responsive;final java.util.IdentityHashMap<View,Rect>','boolean responsive,adaptive;final java.util.IdentityHashMap<View,Rect>')
 s=rep(s,'material.setVisibility(responsive?GONE:VISIBLE);\n      if(responsive){measureResponsive(w,h);return;}','material.setVisibility(responsive&&!adaptive?GONE:VISIBLE);\n      if(responsive){if(adaptive)material.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(h,MeasureSpec.EXACTLY));measureResponsive(w,h);return;}')
 s=rep(s,'GradientDrawable glass=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{light?0xfaffffff:0xff14283a,light?(cobra?0xffd0edf4:0xfff4e7c9):0xff06101c});\n      glass.setCornerRadius(px(18));glass.setStroke(px(1),cobra?(light?0xff59b7d0:0xff53cbeb):(light?0xffcead6c:0xffd7ba74));setBackground(glass);','''if(adaptive)setBackground(null);else{GradientDrawable glass=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{light?0xfaffffff:0xff14283a,light?(cobra?0xffd0edf4:0xfff4e7c9):0xff06101c});
      glass.setCornerRadius(px(18));glass.setStroke(px(1),cobra?(light?0xff59b7d0:0xff53cbeb):(light?0xffcead6c:0xffd7ba74));setBackground(glass);}''')
 s=rep(s,'if(responsive){for(java.util.Map.Entry<View,Rect> item:responsiveBoxes.entrySet())','if(responsive){if(adaptive)material.layout(0,0,getWidth(),getHeight());for(java.util.Map.Entry<View,Rect> item:responsiveBoxes.entrySet())')
 s=rep(s,'float referenceW=light?840:941,referenceH=light?1873:1672;\n      float scale=getWidth()/referenceW;','''float referenceW=light?840:941,referenceH=light?1873:1672;float referenceAspect=referenceW/referenceH,viewAspect=getWidth()/(float)Math.max(1,getHeight());
      if(viewAspect>referenceAspect*1.35f){float factor=Math.max(getWidth()/(float)bitmap.getWidth(),getHeight()/(float)bitmap.getHeight()),sourceW=getWidth()/factor,sourceH=getHeight()/factor;int sx=Math.max(0,Math.round((bitmap.getWidth()-sourceW)/2f)),sy=Math.max(0,Math.round((bitmap.getHeight()-sourceH)*.42f));src.set(sx,sy,Math.min(bitmap.getWidth(),sx+Math.round(sourceW)),Math.min(bitmap.getHeight(),sy+Math.round(sourceH)));dst.set(0,0,getWidth(),getHeight());canvas.drawBitmap(bitmap,src,dst,paint);return;}
      float scale=getWidth()/referenceW;''')
 return s
def patch_splash(s):
 s=rep(s,'  private int chooserDp(int value)\n  {\n    return (int) (value * getResources().getDisplayMetrics().density + 0.5f);\n  }','''  private int chooserDp(int value)
  {
    return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
  }

  private int chooserWindowPixels(boolean width)
  {
    View decor=getWindow().getDecorView();int measured=width?decor.getWidth():decor.getHeight();if(measured>0)return measured;
    if(Build.VERSION.SDK_INT>=30){android.graphics.Rect bounds=getWindowManager().getCurrentWindowMetrics().getBounds();int value=width?bounds.width():bounds.height();if(value>0)return value;}
    android.content.res.Configuration config=getResources().getConfiguration();int dp=width?config.screenWidthDp:config.screenHeightDp;if(dp>0)return Math.round(dp*getResources().getDisplayMetrics().density);
    return width?getResources().getDisplayMetrics().widthPixels:getResources().getDisplayMetrics().heightPixels;
  }
  private int chooserWindowDp(boolean width){return Math.round(chooserWindowPixels(width)/getResources().getDisplayMetrics().density);}''')
 s=rep(s,'"Infinity Health Center",\n        "Cobra Recovery"','"Infinity Health Center",\n        "Cobra Recovery",\n        "Cobra Theme controls"')
 s=rep(s,'else if (which == 4 && cobra)\n          {\n            showCobraRecovery();\n          }','else if (which == 4 && cobra)\n          {\n            showCobraRecovery();\n          }\n          else if (which == 5 && cobra) { vtheme().manager(this); }')
 s=s.replace('getResources().getDisplayMetrics().widthPixels - chooserDp(32)','chooserWindowPixels(true) - chooserDp(32)').replace('getResources().getDisplayMetrics().widthPixels-chooserDp(28)','chooserWindowPixels(true)-chooserDp(28)').replace('(int)(getResources().getDisplayMetrics().heightPixels*.78f)','(int)(chooserWindowPixels(false)*.78f)')
 s=rep(s,'Math.round(getResources().getDisplayMetrics().heightPixels/getResources().getDisplayMetrics().density)','chooserWindowDp(false)',2)
 s=rep(s,'Math.round(getResources().getDisplayMetrics().widthPixels / getResources().getDisplayMetrics().density)','chooserWindowDp(true)')
 s=rep(s,'Math.round(getResources().getDisplayMetrics().widthPixels/getResources().getDisplayMetrics().density)','chooserWindowDp(true)')
 s=rep(s,'root.setOnLongClickListener(v->{vtheme().manager(this);return true;});','root.setLongClickable(false);')
 return s
def meta(root):
 p=root/'scripts/infinity_background_resume.py';s=p.read_text()
 for a,b in [("VERSION_CODE = 2103284",f"VERSION_CODE = {VC}"),("RELEASE = '1.0.9-Ambient-Surface-Repair-RC1'",f"RELEASE = '{REL}'"),("BASE_COMMIT = 'ec28a8574ecf8d7fccb3713133661c1e8c2246cb'",f"BASE_COMMIT = '{BC}'"),("BASE_APK_SHA256 = '2de48f4a269df9196e341c1083608a436fdce1e2d63d17fbb2b80d9c525f63bf'",f"BASE_APK_SHA256 = '{BA}'"),("BASE_ENGINE_SHA256 = 'c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'",f"BASE_ENGINE_SHA256 = '{BE}'")]:s=rep(s,a,b)
 p.write_text(s);p=root/'scripts/package_background_resume.py';s=p.read_text().replace('Infinity-2103284-Ambient-Surface-Repair-RC1-unsigned.apk','Infinity-2103286-Chooser-Responsive-Repair-RC1-unsigned.apk').replace('Infinity-2103284-Ambient-Surface-Repair-RC1.apk','Infinity-2103286-Chooser-Responsive-Repair-RC1.apk').replace("'base_run':36829442559","'base_run':36933314038").replace("ROOT/'repairs/infinity-ambient-surface-2103284/DEVICE-TEST.txt'","ROOT/'repairs/chooser-responsive-2103286/DEVICE-TEST.md'");p.write_text(s)
def verify(root):
 sh=root/'shell-kodi';c=(sh/C).read_text();s=(sh/S).read_text();g=(sh/G).read_text();assert 'setOnLongClickListener(v->{actions.themes();return true;});' not in c and 'root.setOnLongClickListener(v->{vtheme().manager(this);return true;});' not in s;assert 'adaptiveWide=!compactResponsive' in c and 'backdrop.layout(0,0,getWidth(),getHeight())' in c;assert 'chooserWindowPixels(boolean width)' in s and '"Cobra Theme controls"' in s;assert f'versionCode {VC}' in g and f'versionName "{REL}"' in g;r=json.loads((root/'engine/background-resume-source.json').read_text());[(_ for _ in ()).throw(AssertionError(n)) for n,row in r['files'].items() if h((sh/n).read_bytes())!=row['after']];print('PASS chooser responsive source')
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--verify',action='store_true');x=a.parse_args()
 if x.verify:return verify(x.root)
 sh=x.root/'shell-kodi';x.out.mkdir(parents=True,exist_ok=True)
 for n,v in PRE.items():
  if h((sh/n).read_bytes())!=v:raise RuntimeError('wrong source '+n)
 (sh/C).write_text(patch_chooser((sh/C).read_text()));(sh/S).write_text(patch_splash((sh/S).read_text()));g=(sh/G).read_text();g=rep(g,'versionCode 2103284',f'versionCode {VC}');g=rep(g,'versionName "1.0.9-Ambient-Surface-Repair-RC1"',f'versionName "{REL}"');(sh/G).write_text(g);meta(x.root);r=json.loads((x.root/'engine/background-resume-source.json').read_text());r.update(base_source_commit=BC,base_apk_sha256=BA,native_engine_sha256=BE,version_code=VC,release=REL,candidate_locked=False,physical_device_verified=False,chooser_global_long_press_removed=True,chooser_current_window_metrics=True,chooser_fold_wide_reflow=True);[(r['files'].setdefault(n,{}).__setitem__('after',h((sh/n).read_bytes()))) for n in (C,S,G)];(x.root/'engine/background-resume-source.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');(x.out/'source-proof.json').write_text(json.dumps({'schema':1,'base_apk_sha256':BA,'native_engine_sha256':BE,'version_code':VC,'release':REL,'no_native_source_change':True,'no_skin_change':True,'physical_device_verified':False},indent=2)+'\n');verify(x.root)
if __name__=='__main__':main()
