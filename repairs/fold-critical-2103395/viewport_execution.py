"""Supplementary UI execution of the exact already-built production DEX.

No candidate source/binary change. The fixture uses provider names, not results.
"""
from pathlib import Path
import argparse,os,shutil,subprocess,json,zipfile,hashlib
import components95 as c, ui_android95
CANDIDATE='f1d32c1bc74c61d4166780eec34f59c349204dc9'
def prepare(root):
 proof=json.loads(Path('ready95/STARTUP-DEX-INTEGRATION.json').read_text());assert proof['source_commit']==CANDIDATE
 dex=Path('ready95/component/classes.dex');assert c.digest(dex)==proof['component_dex_sha256']
 apk=Path('protected-2103394/Infinity-2103394-Fold-Corrective-EXPERIMENTAL.apk');assert c.digest(apk)==c.PARENT
 root.mkdir();src=root/'test-sources';src.mkdir();s=(c.HERE/'Infinity95Test.java').read_text()
 anchor='  return "Infinity.Search.2103395:"'
 assert s.count(anchor)==1
 rows='''  rows.put(new JSONObject().put("id","plugin.video.seren").put("name","Seren").put("description","Search movies").put("available",true).put("icon",""));
  rows.put(new JSONObject().put("id","plugin.video.fenlight").put("name","Fen Light").put("description","Search interface not verified").put("available",false).put("icon",""));
  rows.put(new JSONObject().put("id","plugin.video.themoviedb.helper").put("name","TMDb Helper").put("description","Not installed or disabled").put("available",false).put("icon",""));
'''
 s=s.replace(anchor,rows+anchor)
 s=s.replace('   final InfinityAndroidKeyboard.Editor[] editor={null};', '   waitForIdleSync();android.os.SystemClock.sleep(800);\n   final InfinityAndroidKeyboard.Editor[] editor={null};')
 anchor='   waitForIdleSync();android.os.SystemClock.sleep(600);'
 assert s.count(anchor)==1
 s=s.replace(anchor,'''   runOnMainSync(()->{editor[0].input.requestFocus();((android.view.inputmethod.InputMethodManager)activity.getSystemService(Context.INPUT_METHOD_SERVICE)).showSoftInput(editor[0].input,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);});
   boolean[] visible={false};
   for(int retry=0;retry<30;retry++){
    waitForIdleSync();android.os.SystemClock.sleep(200);
    runOnMainSync(()->{WindowInsets insets=editor[0].input.getRootWindowInsets();visible[0]=insets!=null&&insets.isVisible(WindowInsets.Type.ime());});
    if(visible[0])break;
   }
   check(visible[0],"actual soft keyboard visible "+theme);
   final boolean[] geometry={false};
   runOnMainSync(()->{
    android.graphics.Rect query=new android.graphics.Rect(),all=new android.graphics.Rect();
    View button=((View)editor[0].input.getParent()).findViewById(0x00950001);
    geometry[0]=editor[0].input.getGlobalVisibleRect(query)&&button.getGlobalVisibleRect(all)&&query.height()>=editor[0].dp(48)&&all.height()>=editor[0].dp(48);
   });
   check(geometry[0],"query and Search All remain visible above IME "+theme);
   waitForIdleSync();android.os.SystemClock.sleep(600);
   runOnMainSync(()->{WindowInsets insets=editor[0].input.getRootWindowInsets();visible[0]=insets!=null&&insets.isVisible(WindowInsets.Type.ime());});
   check(visible[0],"IME remains visible at screenshot "+theme);''')
 (src/'Infinity95Test.java').write_text(s);shutil.copyfile(c.HERE/'Infinity95TestActivity.java',src/'Infinity95TestActivity.java');c.HERE=src
 with zipfile.ZipFile(apk) as z:(root/'classes2.dex').write_bytes(z.read('classes2.dex'))
 assert c.digest(root/'classes2.dex')=='d4df6604044e7cb66584229562186bf2ed8f0031d2d3efba03bba8ebe38934ca'
 ui_android95.prepare(root,Path(os.environ['ANDROID_HOME'])/'platforms/android-34/android.jar',Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0',dex,root/'classes2.dex')
 (root/'INPUT.json').write_text(json.dumps({'candidate_source':CANDIDATE,'harness_source':os.environ['GITHUB_SHA'],'dex_sha256':c.digest(dex)}))
def run(root):
 devices=[s.split()[0] for s in subprocess.check_output(['adb','devices'],text=True).splitlines()[1:] if s.endswith('\tdevice')];assert len(devices)==1 and devices[0].startswith('emulator-');device=devices[0]
 def shell(*args):subprocess.run(['adb','-s',device,'shell',*args],check=True)
 shell('settings','put','secure','show_ime_with_hard_keyboard','1');results=[]
 for name,size,density in [('cover','1080x2520','420'),('inner','2184x1968','420')]:
  shell('wm','size',size);shell('wm','density',density)
  result=ui_android95.run(root,'adb',device);assert result['assertions']==42
  for theme in ('light','dark','oled'):(root/('search-'+theme+'.png')).rename(root/(name+'-'+theme+'.png'))
  shutil.copyfile(root/'integrated-search-ui.log',root/(name+'-ui.log'))
  results.append(dict(viewport=name,size=size,density=density,**result))
 (root/'VIEWPORT-EXECUTION.json').write_text(json.dumps(dict(inputs=json.loads((root/'INPUT.json').read_text()),results=results,physical_fold_verified=False),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run']);a=p.parse_args();(prepare if a.mode=='prepare' else run)(Path('viewport95'))
