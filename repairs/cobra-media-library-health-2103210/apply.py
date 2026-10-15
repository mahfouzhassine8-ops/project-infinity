#!/usr/bin/env python3
"""Apply scoped 2103210 Movies/Shows + chooser Health Center shell changes.
Live TV ownership methods are exact-hash protected. Native code is never rebuilt here.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VERSION=2103210; OLD_VERSION=2103209
OLD_NAME='1.0.9-Cobra-Python311-GIL-Stability-RC1'; NEW_NAME='1.0.9-Cobra-Media-Library-Health-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE_SHA='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
FILES={
 SOURCE+'InfinityLiveActivity.java.in':('8e930cf0a018950ea2e86923684bcfc7076298b09c6c5c8d8d72c90808508dc5','0d5172b619c8901994eb332050ae2330b0b6b607dae5e58e84a5b332581a8f5b'),
 SOURCE+'Splash.java.in':('89d10b3eab529cb3faa3a810acf66cb2f30d3e6b1a03757deb40473b1131b121','e440ed7cfff5021c4e620ef825669c3e63126ce18e0fbeaa58a39cba3e216e93'),
 SOURCE+'Main.java.in':('ddf18d30c4040369b30e861ded588a53846ff3de319a89a219344771f8db9318','240d08c21cbdbdfbff8f06f4af3f7a633516d499e49a24481c304990a705173f'),
}
INCLUDES={
 'vod-browse-1.java.inc':'4a59fd84d74f3578fa640ef07c4485e4ba1d5e2adc6d543e1cdcd28f134e8076',
 'vod-browse-2.java.inc':'2525e525bb089746cc65db587d6bf3a87710db4effa638f082d2b6cbee26dd0f',
 'splash-settings.java.inc':'cef653046713f12882964c414491fba2dc2ec2a4c56fac52d6f16f0c8f14e7b4',
}
PROTECTED={
 'private void cobraOpenLiveTv()':'ca2104682cc43724a138310dac87361973d57a40a00a5db0e6557a3fa8f6a602',
 'private void showGuide()':'f57772610779aea49fc43c6d94db2df804e911e9c82cf224d9e5f6f96f9a93a4',
 'private void startSinglePlayer(String url)':'1c1a40c28072b5876e61ecedc5c64cfb6483b8d1c464041a16ee2b0128213708',
 'private void cobraShowQuickPeek(Channel channel,View anchor)':'bea049b1f6941709e13545eefd647915c64c2500e6b6716da2e246ab3718f869',
 'private void cobraStartLocalTimeshift':'758df5bc2d2c32df5836b13c23b33a44c35a90ef910cf3513516e4f8a3a6800a',
 'private void playChannel(Channel channel)':'48729254f6a27441b487fe8425b899ede48a804819c3d6bb466695d654087de3',
 'private void startCobraPreview(Channel channel)':'db8403d7256e8d353c9b7cef8397076ef7874646782d3972e7b3db2afa0a227c',
 'private void releaseSinglePlayer()':'1cd0ff7182a28e632f6601202c57050c87de10a923080ee64c062ced76f5b385',
 'private void releaseMulti()':'cc1a975f97fbb11dc9faa12f07e76045980e89911ed1f6cc7f0d8899886a1cad',
 'private LoadResult loadXtream(LiveSource source)':'6e9c2300e1c65095f2f8340f8764783e6852cbd8ccbc23ad238d14172e3ac2cb',
 'private LoadResult loadM3u(LiveSource source)':'ba2a26616379cd59e6b0514258e2734a19925f48627065ca33095793977d11b0',
}
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def require(v,m):
 if not v:raise RuntimeError(m)
def once(text,old,new,label):
 require(text.count(old)==1,label+' anchor drift');return text.replace(old,new,1)
def method(text,sig):
 i=text.find(sig);require(i>=0,'Missing protected method: '+sig);b=text.find('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise RuntimeError('Unbalanced method: '+sig)
def contract(text):
 out={}
 for sig,expected in PROTECTED.items():
  digest=sha_bytes(method(text,sig).encode());require(digest==expected,'Live TV parent drift: '+sig);out[sig]=digest
 return out
def method_range(text,sig):
 i=text.find(sig);require(i>=0,'Missing method: '+sig);b=text.find('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return i,j+1
 raise RuntimeError('Unbalanced method: '+sig)

def patch_activity(path):
 s=path.read_text();before=contract(s)
 cache='''  private final Handler mMain = new Handler(Looper.getMainLooper());\n  // Movies/Shows-only artwork cache. Live TV, guide, provider playback and player ownership are untouched.\n  private final LinkedHashMap<String, android.graphics.Bitmap> mCobraVodArtwork =\n      new LinkedHashMap<String, android.graphics.Bitmap>(32, 0.75f, true) {\n        @Override protected boolean removeEldestEntry(Map.Entry<String, android.graphics.Bitmap> eldest) {\n          return size() > 32;\n        }\n      };\n'''
 s=once(s,'  private final Handler mMain = new Handler(Looper.getMainLooper());\n',cache,'VOD cache')
 s=once(s,'cobraPublishNavigation(ticket,() -> renderVodItems(items, series, failures));','cobraPublishNavigation(ticket,() -> renderVodBrowse(items, series, failures));','VOD render handoff')
 marker='  private void renderVodItems(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {'
 require(s.count(marker)==1,'Legacy VOD renderer anchor drift')
 block=(ROOT/'vod-browse-1.java.inc').read_text()+(ROOT/'vod-browse-2.java.inc').read_text();s=s.replace(marker,block+marker,1);path.write_text(s)
 require(contract(s)==before,'Live TV bytes changed')

def patch_splash(path):
 s=path.read_text();a,b=method_range(s,'  private void showExperienceCardSettings(String experience)')
 block=(ROOT/'splash-settings.java.inc').read_text().rstrip('\n');s=s[:a]+block+s[b:];path.write_text(s)

def patch_main(path):
 s=path.read_text()
 fields='''  private XBMCJsonRPC mJsonRPC = null;\n  private static final String INFINITY_HEALTH_CENTER_EXTRA = "infinity_launch_kodi_health_center";\n  private static final String INFINITY_HEALTH_CENTER_ADDON = "script.kodihealthcenter";\n  private boolean mInfinityHealthCenterPending = false;\n  private int mInfinityHealthCenterAttempts = 0;\n  private final Runnable mInfinityHealthCenterLaunch = new Runnable()\n  {\n    @Override public void run()\n    {\n      if (!mInfinityHealthCenterPending || mInfinityDestroyed) return;\n      if (mJsonRPC == null) mJsonRPC = new XBMCJsonRPC();\n      if (mJsonRPC.Ping())\n      {\n        String response = mJsonRPC.request_string("{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"Addons.ExecuteAddon\\\",\\\"params\\\":{\\\"addonid\\\":\\\"" + INFINITY_HEALTH_CENTER_ADDON + "\\\"},\\\"id\\\":1}");
        if (response != null && !response.contains("\\\"error\\\""))
        {
          mInfinityHealthCenterPending = false;
          mInfinityHealthCenterAttempts = 0;
          return;
        }
      }
      if (++mInfinityHealthCenterAttempts < 12) handler.postDelayed(this, 500L);
      else
      {
        mInfinityHealthCenterPending = false;
        mInfinityHealthCenterAttempts = 0;
        android.widget.Toast.makeText(Main.this, "Kodi Health Center is not installed or could not be opened.", android.widget.Toast.LENGTH_LONG).show();
      }
    }
  };\n'''
 s=once(s,'  private XBMCJsonRPC mJsonRPC = null;\n',fields,'Health fields')
 s=once(s,'    super.onCreate(savedInstanceState);\n\n    setContentView(R.layout.activity_main);','    super.onCreate(savedInstanceState);\n    infinityCaptureHealthCenterRequest(getIntent());\n\n    setContentView(R.layout.activity_main);','Health onCreate')
 s=once(s,'    super.onNewIntent(intent);\n    if (infinityHandlePlayerRotationIntent(intent)) return;\n    // Delay until after Resume','    super.onNewIntent(intent);\n    boolean healthCenter = infinityCaptureHealthCenterRequest(intent);\n    if (infinityHandlePlayerRotationIntent(intent)) return;\n    if (healthCenter) { if (!mPaused) infinityScheduleHealthCenterLaunch(); return; }\n    // Delay until after Resume','Health new intent')
 helper='''    InfinityExtendedBackgroundService.sync(this);\n    infinityScheduleHealthCenterLaunch();\n  }\n\n\n  private boolean infinityCaptureHealthCenterRequest(Intent intent)\n  {\n    if (intent == null || !intent.getBooleanExtra(INFINITY_HEALTH_CENTER_EXTRA, false)) return false;\n    intent.removeExtra(INFINITY_HEALTH_CENTER_EXTRA);\n    mInfinityHealthCenterPending = true;\n    mInfinityHealthCenterAttempts = 0;\n    return true;\n  }\n\n  private void infinityScheduleHealthCenterLaunch()\n  {\n    if (!mInfinityHealthCenterPending || mInfinityDestroyed) return;\n    handler.removeCallbacks(mInfinityHealthCenterLaunch);\n    handler.postDelayed(mInfinityHealthCenterLaunch, 250L);\n  }'''
 s=once(s,'    InfinityExtendedBackgroundService.sync(this);\n  }',helper,'Health resume/helper')
 s=once(s,'    mInfinityDestroyed = true;\n','    mInfinityDestroyed = true;\n    handler.removeCallbacks(mInfinityHealthCenterLaunch);\n','Health destroy')
 path.write_text(s)

def patch_packaging():
 runtime=Path('scripts/infinity_background_resume.py');s=runtime.read_text();s=once(s,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime version');s=once(s,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime name');runtime.write_text(s)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME;require(p.count(old)>=2,'packager name anchor drift');p=p.replace(old,new)
 obsolete="for token in (b'InfinityExtendedBackgroundService',b'EXTENDED BACKGROUND MODE',b'InfinityCoreBridge',b'InfinityCobraDeviceBridge',b'getPlayWhenReady',b'Turn off'):"
 current="for token in (b'InfinityExtendedBackgroundService',b'InfinityBackgroundControlActivity',b'BACKGROUND_MODE_NORMAL',b'BACKGROUND_MODE_EXTENDED',b'InfinityCoreBridge',b'InfinityCobraDeviceBridge',b'getPlayWhenReady',b'Turn off'):"
 p=once(p,obsolete,current,'current runtime verifier');pack.write_text(p)

def apply(shell):
 for name,digest in INCLUDES.items():require(sha(ROOT/name)==digest,'Reviewed include drift: '+name)
 for name,(before,_) in FILES.items():require(sha(shell/name)==before,'Wrong exact Android parent source: '+name)
 patch_activity(shell/(SOURCE+'InfinityLiveActivity.java.in'));patch_splash(shell/(SOURCE+'Splash.java.in'));patch_main(shell/(SOURCE+'Main.java.in'))
 for name,(_,after) in FILES.items():require(sha(shell/name)==after,'Unexpected scoped source result: '+name)
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text();g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','Gradle version');g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','Gradle name');gradle.write_text(g);patch_packaging()
 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text());require(receipt.get('version_code')==OLD_VERSION,'Wrong prepared 2103209 receipt')
 for name in FILES:require(name in receipt['files'],'Source missing from receipt: '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle);receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,live_tv_source_untouched=True,movies_shows_cinematic_browse=True,kodi_health_center_chooser_shortcut=True);receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final shell receipt drift: '+name)
 Path('audit210').mkdir(exist_ok=True);live=contract((shell/(SOURCE+'InfinityLiveActivity.java.in')).read_text());(Path('audit210')/'scope.json').write_text(json.dumps({'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,'changed_java_files':sorted(FILES),'live_tv_protected_methods':live,'live_tv_source_untouched':True,'native_engine_rebuilt':False,'health_center_addon':'script.kodihealthcenter'},indent=2)+'\n');print('PASS: Movies/Shows + Kodi Health Center applied; Live TV byte contracts unchanged')
def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();apply(a.shell)
if __name__=='__main__':main()
