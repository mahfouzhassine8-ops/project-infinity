#!/usr/bin/env python3
"""Apply 2103212 presentation-only polish over exact 2103211.

Scope: Infinity Health Center visuals + ambient-aware Movies/TV Shows trim.
No diagnostic behavior, media data routes, playback, Live TV, providers or native engine changes.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VERSION=2103212
OLD_VERSION=2103211
OLD_NAME='1.0.9-Cobra-Library-Health-Refinement-RC1'
NEW_NAME='1.0.9-Cobra-Health-Media-Trim-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE_SHA='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
PARENT={
 SOURCE+'InfinityLiveActivity.java.in':'b4c4607fb76acd6735baf8d2858e99f3b43572870071b7f6825b89dd1dc8924a',
 SOURCE+'Splash.java.in':'3be7a6789d756f1349d76b645f49dd9b7112e5d1c15ce6153898332078f16d0f',
 SOURCE+'Main.java.in':'ddf18d30c4040369b30e861ded588a53846ff3de319a89a219344771f8db9318',
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
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def require(value,message):
 if not value:raise RuntimeError(message)
def once(text,old,new,label):
 require(text.count(old)==1,label+' anchor drift');return text.replace(old,new,1)
def method_range(text,sig):
 i=text.find(sig);require(i>=0,'Missing method: '+sig);b=text.find('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return i,j+1
 raise RuntimeError('Unbalanced method: '+sig)
def method(text,sig):
 a,b=method_range(text,sig);return text[a:b]
def contract(text):
 out={}
 for sig,expected in PROTECTED.items():
  digest=sha_bytes(method(text,sig).encode());require(digest==expected,'Protected Live TV/player drift: '+sig);out[sig]=digest
 return out

def patch_health(path):
 s=path.read_text()
 # Replace presentation only: the diagnostic collection/export methods after infinityShowHealthText stay byte-for-byte.
 a,_=method_range(s,'  private void showInfinityHealthCenter()')
 _,b=method_range(s,'  private void infinityShowHealthText(String title,String body)')
 ui=(ROOT/'health-ui.java.inc').read_text()
 s=s[:a]+ui+s[b:]
 for token in ('infinityHealthExitHistory(false)','infinityExportHealthReport()','infinityCopyHealthReport()',
               'infinityHealthBuildInfo()','DIAGNOSTICS  •  RECOVERY','chooserControlSurface'):
  require(token in s,'Health UI contract missing: '+token)
 # Core collector/export behavior must remain present and untouched in ownership.
 for token in ('getHistoricalProcessExitReasons','getTraceInputStream','ACTION_CREATE_DOCUMENT',
               'infinityHealthReport()','infinityShouldOfferCrashRecovery'):
  require(token in s,'Health behavior lost: '+token)
 path.write_text(s)

def patch_media(path):
 s=path.read_text();before=contract(s)
 field='  private String mCobraAmbientContext="";\n'
 s=once(s,field,field+'  private final HashMap<View,String> mCobraVodTrimRoles=new HashMap<>();\n','VOD trim registry')

 helpers='''  private int cobraVodAmbientTrimColor(){
    int mode=cobraAmbientMode();int base=cobraModeColor("line");
    if(mode==CobraPresentationEffects.OFF)return base;
    return CobraPresentationEffects.blend(base,mCobraAmbientTint,
        mode==CobraPresentationEffects.IMMERSIVE?.68f:.30f);
  }

  private int cobraVodAmbientPanelColor(){
    int mode=cobraAmbientMode();int base=cobraModeColor("panel");
    if(mode==CobraPresentationEffects.OFF)return base;
    return CobraPresentationEffects.blend(base,mCobraAmbientTint,
        mode==CobraPresentationEffects.IMMERSIVE?.10f:.04f);
  }

  private int cobraVodAmbientFocusColor(){
    int mode=cobraAmbientMode();int base=cobraModeColor("accent");
    if(mode==CobraPresentationEffects.OFF)return base;
    return CobraPresentationEffects.blend(base,mCobraAmbientTint,
        mode==CobraPresentationEffects.IMMERSIVE?.44f:.18f);
  }

  private android.graphics.drawable.Drawable cobraVodTrimDrawable(String role){
    int trim=cobraVodAmbientTrimColor(),focus=cobraVodAmbientFocusColor();
    int stroke=cobraAmbientMode()==CobraPresentationEffects.IMMERSIVE?2:1;
    if("hero".equals(role))return surface(Color.TRANSPARENT,20,trim,stroke);
    if("section".equals(role))return surface(trim,2,trim,0);
    int radius="genre".equals(role)?16:14;
    int fill="genre".equals(role)?cobraVodAmbientPanelColor():Color.TRANSPARENT;
    android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
    states.addState(new int[]{android.R.attr.state_focused},surface(fill,radius,focus,stroke+1));
    states.addState(new int[]{},surface(fill,radius,trim,stroke));
    return states;
  }

  private <T extends View> T cobraTrackVodTrim(T view,String role){
    mCobraVodTrimRoles.put(view,role);view.setBackground(cobraVodTrimDrawable(role));return view;
  }

  private void cobraRefreshVodAmbientTrim(){
    if(mCobraVodTrimRoles.isEmpty())return;
    ArrayList<View> stale=new ArrayList<>();
    for(Map.Entry<View,String> entry:mCobraVodTrimRoles.entrySet()){
      View view=entry.getKey();
      if(view==null||view.getParent()==null){stale.add(view);continue;}
      view.setBackground(cobraVodTrimDrawable(entry.getValue()));
    }
    for(View view:stale)mCobraVodTrimRoles.remove(view);
  }

'''
 marker='  private View cobraVodHeroCarousel(ArrayList<VodItem> items, boolean series) {'
 require(s.count(marker)==1,'VOD helper insertion point drift')
 s=s.replace(marker,helpers+marker,1)

 start='''    clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");
    status(items.size() + " titles across enabled providers");'''
 repl='''    clearStage(series ? "COBRA • TV SHOWS" : "COBRA • MOVIES");
    mCobraVodTrimRoles.clear();
    status(items.size() + " titles across enabled providers");'''
 s=once(s,start,repl,'Clear trim registry on VOD render')

 hero_anchor='''    veil.setBackground(fade);hero.addView(veil,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout copy=new LinearLayout(this);'''
 hero_repl='''    veil.setBackground(fade);hero.addView(veil,new FrameLayout.LayoutParams(-1,-1));
    View trim=cobraTrackVodTrim(new View(this),"hero");
    hero.addView(trim,new FrameLayout.LayoutParams(-1,-1));
    LinearLayout copy=new LinearLayout(this);'''
 s=once(s,hero_anchor,hero_repl,'Hero trim')

 heading_anchor='''    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    TextView label=text(title,cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);'''
 heading_repl='''    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    View edge=cobraTrackVodTrim(new View(this),"section");
    LinearLayout.LayoutParams edgeLp=new LinearLayout.LayoutParams(dp(4),dp(24));edgeLp.rightMargin=dp(8);heading.addView(edge,edgeLp);
    TextView label=text(title,cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);'''
 s=once(s,heading_anchor,heading_repl,'Shelf heading trim')

 genre_heading='''    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    TextView label=text("Genres",cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);'''
 genre_repl='''    LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
    View edge=cobraTrackVodTrim(new View(this),"section");
    LinearLayout.LayoutParams edgeLp=new LinearLayout.LayoutParams(dp(4),dp(24));edgeLp.rightMargin=dp(8);heading.addView(edge,edgeLp);
    TextView label=text("Genres",cobraModeColor("text"),18,Gravity.LEFT|Gravity.CENTER_VERTICAL);'''
 s=once(s,genre_heading,genre_repl,'Genre heading trim')

 genre_button='''      genre.setTextSize(13);genre.setBackground(surface(cobraModeColor("panel"),16,cobraModeColor("line"),1));
      final String genreName=entry.getKey();'''
 genre_button_repl='''      genre.setTextSize(13);cobraTrackVodTrim(genre,"genre");
      final String genreName=entry.getKey();'''
 s=once(s,genre_button,genre_button_repl,'Genre button ambient trim')

 card_old='''    android.graphics.drawable.StateListDrawable focus=new android.graphics.drawable.StateListDrawable();
    focus.addState(new int[]{android.R.attr.state_focused},surface(Color.TRANSPARENT,14,cobraModeColor("accent"),2));
    focus.addState(new int[]{},surface(Color.TRANSPARENT,14,Color.TRANSPARENT,0));card.setBackground(focus);
    return card;'''
 card_new='''    cobraTrackVodTrim(card,"card");
    return card;'''
 s=once(s,card_old,card_new,'Card ambient trim')

 ambient_anchor='''    mCobraEffects.backdrop(mCobraBrowseBackground,cobraThemeColor("background",mTheme.background),mCobraAmbientTint,mode);
    mCobraEffects.backdrop(mCobraGuideShell,cobraModeColor("background"),mCobraAmbientTint,mode);
  }'''
 ambient_repl='''    mCobraEffects.backdrop(mCobraBrowseBackground,cobraThemeColor("background",mTheme.background),mCobraAmbientTint,mode);
    mCobraEffects.backdrop(mCobraGuideShell,cobraModeColor("background"),mCobraAmbientTint,mode);
    cobraRefreshVodAmbientTrim();
  }'''
 s=once(s,ambient_anchor,ambient_repl,'Ambient refresh hook')

 for token in ('cobraVodAmbientTrimColor()','cobraRefreshVodAmbientTrim()','"hero"','"card"','"genre"','"section"'):
  require(token in s,'Ambient media trim missing: '+token)
 path.write_text(s)
 require(contract(s)==before,'Live TV/player protected methods changed')

def patch_identity(shell):
 gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
 g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','Gradle version')
 g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','Gradle name');gradle.write_text(g)
 runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
 r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','Runtime version')
 r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'Runtime name');runtime.write_text(r)
 pack=Path('scripts/package_background_resume.py');p=pack.read_text();old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
 require(p.count(old)>=2,'Packager identity drift');pack.write_text(p.replace(old,new))
 return gradle

def apply(shell):
 for name,digest in PARENT.items():require(sha(shell/name)==digest,'Not exact locked 2103211 parent: '+name)
 activity=shell/(SOURCE+'InfinityLiveActivity.java.in');splash=shell/(SOURCE+'Splash.java.in')
 patch_media(activity);patch_health(splash);gradle=patch_identity(shell)
 # Main is presentation-untouched.
 require(sha(shell/(SOURCE+'Main.java.in'))==PARENT[SOURCE+'Main.java.in'],'Main changed unexpectedly')

 receipt_path=Path('engine/background-resume-source.json');receipt=json.loads(receipt_path.read_text())
 require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Wrong 2103211 receipt')
 for name in PARENT:
  require(name in receipt['files'],'Receipt missing '+name);receipt['files'][name]['after']=sha(shell/name)
 rel='tools/android/packaging/xbmc/build.gradle.in';receipt['files'][rel]['after']=sha(gradle)
 receipt.update(version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
   candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
   native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE_SHA,
   presentation_only=True,health_center_infinity_styled=True,
   health_center_behavior_unchanged=True,movies_shows_trim_added=True,
   movies_shows_trim_ambient_aware=True,ambient_modes=['off','subtle','immersive'],
   live_tv_source_untouched=True,media_information_architecture_unchanged=True)
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 for name,row in receipt['files'].items():require(sha(shell/name)==row['after'],'Final receipt drift: '+name)

 scope={
  'build':VERSION,'parent_build':OLD_VERSION,'native_engine_sha256':NATIVE_SHA,
  'changed_java_files':[SOURCE+'InfinityLiveActivity.java.in',SOURCE+'Splash.java.in'],
  'main_unchanged':True,'live_tv_protected_methods':contract(activity.read_text()),
  'live_tv_source_untouched':True,'native_engine_rebuilt':False,
  'health_behavior_unchanged':True,'health_presentation':'Infinity styled responsive sheet',
  'media_structure_unchanged':True,'media_trim':'ambient-aware',
  'ambient_off':'restrained neutral trim','ambient_subtle':'light ambient tint',
  'ambient_immersive':'stronger atmospheric edge/focus trim','video_recolored':False,
 }
 Path('audit212').mkdir(exist_ok=True);Path('audit212/scope.json').write_text(json.dumps(scope,indent=2)+'\n')
 print('PASS: 2103212 presentation-only Health + ambient media trim; protected behavior untouched')

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);args=p.parse_args();apply(args.shell)
if __name__=='__main__':main()
