from pathlib import Path
import argparse,json,hashlib,re,tarfile
from java_members import span
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--evidence',type=Path,default=Path('audit266'));a=p.parse_args();root=a.root.resolve();ev=a.evidence.resolve();ev.mkdir(parents=True,exist_ok=True)
src=root/'shell-kodi';A='tools/android/packaging/xbmc/';before={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
assert before==json.loads((root/'source265/source-hashes-after.json').read_text())
def once(s,x,y):assert s.count(x)==1,(s.count(x),x[:90]);return s.replace(x,y,1)
def member(s,name,new):i,j=span(s,name);return s[:i]+'  '+new.strip()+s[j:]
live=src/(A+'src/InfinityLiveActivity.java.in');old=live.read_text();s=old
s=s.replace('CobraVisualRenderer.phoneGlass(this,','cobraPhoneGlass(')
s=once(s,'    cobraBuildModeChrome();vtheme().paint(mCobraGuideShell,"guide.shell");vtheme().tree(mCobraGuideDirectory,"guide.directory");vtheme().tree(mCobraGuideDetails,"guide.details");cobraRefreshAmbient();','    cobraBuildModeChrome();vtheme().paint(mCobraGuideShell,"guide.shell");vtheme().tree(mCobraGuideDirectory,"guide.directory");vtheme().tree(mCobraGuideDetails,"guide.details");')
i,j=span(s,'cobraRestyleGuide');part=s[i:j];part=part.rstrip()[:-1]+'  cobraRefreshAmbient();\n  }';s=s[:i]+part+s[j:]
s=once(s,'animateCobraDrawerShift(Math.min(width,screen*.28f));','animateCobraDrawerShift(Math.min(width,screen*.28f));cobraRefreshAmbient();')
s=once(s,'close.requestFocus();vtheme().tree(panel,"sheet."+kind);return items;','close.requestFocus();vtheme().tree(panel,"sheet."+kind);cobraRefreshAmbient();return items;')
s=once(s,'    android.graphics.drawable.Drawable current=view.getBackground();','''    android.graphics.drawable.Drawable current=view.getBackground();
    if(current instanceof CobraVisualRenderer.Glass){
      ((CobraVisualRenderer.Glass)current).effects(tint,mode,night);return;
    }''')
s=once(s,'    cobraAmbientSurface(mCobraGuideShell,COBRA_LIVE_AMBIENT_BLUE,surfaceMode,3,false);','    // The shell backdrop has one owner; never wrap it again on every refresh.')
s=once(s,'    int raw=CobraPresentationEffects.ambientMode(mPrefs);\n    cobraAmbientSurface(mCobraPlayerDrawer', '    int raw=cobraVisualEffectsAllowed()?CobraPresentationEffects.ambientMode(mPrefs):CobraPresentationEffects.OFF;\n    cobraAmbientSurface(mCobraPlayerDrawer')
s=once(s,'    cobraRefreshLiveAmbientSurfaces(mode,live,mCobraAmbientTint);','''    cobraRefreshLiveAmbientSurfaces(mode,live,mCobraAmbientTint);
    // Only existing glass backgrounds are updated. Video backgrounds and pixels are never changed.
    cobraRefreshGlassTree(mCobraGuideShell,mode,false);
    View drawer=getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");
    cobraRefreshGlassTree(drawer,mode,false);
    cobraRefreshGlassTree(cobraCurrentSheetPanel(),mode,cobraNightCinemaActive());
    cobraRefreshGlassTree(mCobraPlayerDrawer,mode,cobraNightCinemaActive());
    cobraRefreshGlassTree(mPlayerChrome,mode,cobraNightCinemaActive());
    if(mCobraModeToolbar!=null){View visuals=mCobraModeToolbar.findViewWithTag("cobra_mode_visuals");
      if(visuals!=null)visuals.setSelected(cobraVisualEffectsAllowed()&&(CobraPresentationEffects.ambientMode(mPrefs)!=CobraPresentationEffects.OFF||mPrefs.getBoolean(CobraPresentationEffects.NIGHT,false)));
    }''')
s=once(s,'      if(pause!=null)pause.setBackground(surface(0xd9000000,14,blue,2));','      if(pause!=null)pause.setBackground(cobraPhoneGlass(false,40,true));\n      cobraRefreshGlassTree(mPlayerChrome,CobraPresentationEffects.OFF,true);')
s=once(s,'    if(pause!=null)pause.setBackground(surface(0x9a000000,14,tintEdge,raw==CobraPresentationEffects.IMMERSIVE?2:1));','    if(pause!=null)pause.setBackground(cobraPhoneGlass(false,40,true));\n    cobraRefreshGlassTree(mPlayerChrome,raw,false);')
# Factory supplies the active palette to newly created filters/cards before a refresh.
s=s.rstrip()[:-1]+'''
  private android.graphics.drawable.Drawable cobraPhoneGlass(boolean light,int radius,boolean raised){
    CobraVisualRenderer.Glass glass=(CobraVisualRenderer.Glass)CobraVisualRenderer.phoneGlass(this,light,radius,raised);
    glass.effects(mCobraAmbientTint,cobraAmbientMode(),cobraNightCinemaActive()&&!light);return glass;
  }
  private void cobraRefreshGlassTree(View view,int mode,boolean night){
    if(view==null||view instanceof TextureView||view instanceof android.view.SurfaceView)return;
    android.graphics.drawable.Drawable background=view.getBackground();
    if(background instanceof CobraVisualRenderer.Glass)((CobraVisualRenderer.Glass)background).effects(mCobraAmbientTint,mode,night);
    if(view instanceof android.view.ViewGroup){android.view.ViewGroup group=(android.view.ViewGroup)view;
      for(int i=0;i<group.getChildCount();i++)cobraRefreshGlassTree(group.getChildAt(i),mode,night);
    }
  }
}
'''
live.write_text(s)
renderer=src/(A+'src/CobraVisualRenderer.java.in');s=renderer.read_text()
s=once(s,'    float emphasis;boolean active,enabled=true;', '    int effectTint=0xff49a9ff,effectMode;boolean night;\n    float emphasis;boolean active,enabled=true;')
s=once(s,'    @Override public boolean isStateful(){return true;}', '''    void effects(int tint,int mode,boolean cinema){
      boolean quiet=cinema&&!light;int selected=quiet?0:mode;
      if(effectTint==tint&&effectMode==selected&&night==quiet)return;
      effectTint=tint;effectMode=selected;night=quiet;invalidateSelf();
    }
    @Override public boolean isStateful(){return true;}''')
s=once(s,'      paint.setShader(new LinearGradient(0,rect.top,0,rect.bottom,new int[]{top,bottom},null,Shader.TileMode.CLAMP));', '''      float atmosphere=effectMode==2?(light?.14f:.28f):effectMode==1?(light?.07f:.14f):0f;
      if(atmosphere>0){top=CobraPresentationEffects.blend(top,effectTint,atmosphere);bottom=CobraPresentationEffects.blend(bottom,effectTint,atmosphere*.55f);}
      if(night){top=CobraPresentationEffects.blend(top,Color.BLACK,.70f);bottom=CobraPresentationEffects.blend(bottom,Color.BLACK,.82f);}
      paint.setShader(new LinearGradient(0,rect.top,0,rect.bottom,new int[]{top,bottom},null,Shader.TileMode.CLAMP));''')
s=once(s,'new int[]{light?0x70ffffff:0x30d9f6ff,Color.TRANSPARENT,light?0x16ffffff:0x080cb9e2}', 'new int[]{light?0x70ffffff:night?0x12d9f6ff:0x30d9f6ff,Color.TRANSPARENT,light?0x16ffffff:night?0x020cb9e2:0x080cb9e2}')
s=once(s,'      paint.setColor(blend(light?0xffb7d4e3:0xff3f6374,light?0xff087b9c:0xff28d1f0,emphasis));', '''      int rim=blend(light?0xffb7d4e3:0xff3f6374,light?0xff087b9c:0xff28d1f0,emphasis);
      if(atmosphere>0)rim=CobraPresentationEffects.blend(rim,effectTint,effectMode==2?.62f:.34f);
      if(night)rim=blend(0xff20343d,0xff49a9ff,emphasis*.65f);
      paint.setColor(rim);''')
s=once(s,'new int[]{light?0xb0ffffff:0x85d5f6ff,Color.TRANSPARENT}', 'new int[]{light?0xb0ffffff:night?0x30d5f6ff:0x85d5f6ff,Color.TRANSPARENT}')
renderer.write_text(s)
g=src/(A+'build.gradle.in');g.write_text(g.read_text().replace('2103265','2103266').replace('Phone-Glass-Polish-RC1','Ambient-Glass-Cinema-RC1'))
after={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()};changed=sorted(k for k in before if before[k]!=after[k]);assert changed==sorted([A+'src/InfinityLiveActivity.java.in',A+'src/CobraVisualRenderer.java.in',A+'build.gradle.in'])
allow={'cobraIcon','cobraTextButton','toggleCobraDrawer','cobraOpenSheet','cobraModeFilters','cobraModeSurface','cobraRestyleGuide','cobraPolishDrawerRow','cobraAmbientSurface','cobraRefreshLiveAmbientSurfaces','cobraRefreshAmbient','cobraApplyNightCinema'}
names=set(re.findall(r'(?m)^  private[^\n{;=]*?\b(\w+)\s*\(',old));modified=[]
for name in names:
 try:
  i,j=span(old,name);x,y=span(live.read_text(),name)
  if old[i:j]!=live.read_text()[x:y]:modified.append(name)
 except AssertionError:pass
assert set(modified)<=allow,modified
receiptpath=root/'engine/background-resume-source.json';receipt=json.loads(receiptpath.read_text())
for name in changed:receipt['files'][name]={'before':before[name],'after':after[name]}
receipt.update(version_code=2103266,version_name='1.0.9-Ambient-Glass-Cinema-RC1',source_parent=2103265,native_engine_recompiled=False,physical_device_verified=False);receiptpath.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
with tarfile.open(root/'source265/reconstructed-2103265-shell.tar.gz') as t:
 for name in ['infinity_background_resume.py','package_background_resume.py']:
  s=t.extractfile('scripts/'+name).read().decode().replace('2103265','2103266').replace('Phone-Glass-Polish-RC1','Ambient-Glass-Cinema-RC1')
  if name.startswith('infinity_'):s=re.sub(r"BASE_APK_SHA256 = '[0-9a-f]+'", "BASE_APK_SHA256 = '6ae458dcc400c6259ac793f4d1fc26fc897aa592f6889febcd0fd084d860626c'",s)
  else:s=s.replace("'base_run':36666385684","'base_run':36671687282").replace('repairs/glass-all-modes-2103266/DEVICE-TEST.md','repairs/ambient-glass-2103266/DEVICE-TEST.txt')
  (root/'scripts'/name).write_text(s)
result=dict(candidate_version=2103266,parent_version=2103265,changed=changed,presentation_members=sorted(modified),protected_activity_members=len(names)-len(modified),other_shell_files_byte_identical=len(before)-len(changed),native_engine_recompiled=False,physical_device_verified=False,stable_lock=False)
(ev/'source-verification.json').write_text(json.dumps(result,indent=2)+'\n');(ev/'source-hashes-after.json').write_text(json.dumps(after,indent=2)+'\n');print(json.dumps(result,indent=2))
