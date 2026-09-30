from pathlib import Path
import argparse,hashlib,json,re
HERE=Path(__file__).parent
BASE='2359c77ef104cc9421da5afd9ec648579ae0f681'
ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
AMBIENT='tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
RELEASE='1.0.9-Mini-Player-Fill-RC1'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
def patch_activity(s):
 s=once(s,'    // Restore full-pane fullscreen Best Fit without changing Pro/preview or PiP safety fitting.','''    // Embedded surfaces always use minimum aspect-preserving center crop.
    // Fullscreen, PiP and Multi-View retain their locked display policies.
    boolean embedded=CobraMiniFillPolicy.active(texture==mCobraPreviewTexture,
        mPlayerOverlay!=null,mInPictureInPicture,cobraMultiViewPlayer(player));
    // Restore full-pane fullscreen Best Fit without changing PiP safety fitting.''')
 s=once(s,'    float[] scale=mode==0&&player==mPlayer&&mPlayerOverlay!=null&&!mInPictureInPicture','''    float[] scale=embedded
        ?CobraFoldAspectPolicy.fill(size.width,size.height,size.pixelWidthHeightRatio,texture.getWidth(),texture.getHeight())
        :mode==0&&player==mPlayer&&mPlayerOverlay!=null&&!mInPictureInPicture''')
 s=once(s,'    matrix.setScale(scale[0],scale[1],texture.getWidth()/2f,texture.getHeight()/2f);texture.setTransform(matrix);\n  }','''    matrix.setScale(scale[0],scale[1],texture.getWidth()/2f,texture.getHeight()/2f);texture.setTransform(matrix);
    if(embedded&&mCobraImmersiveAmbient!=null)mCobraImmersiveAmbient.geometryChanged();
  }''')
 s=once(s,'  static final class CobraFoldAspectPolicy {','''  static final class CobraMiniFillPolicy {
    static boolean active(boolean preview,boolean fullscreen,boolean pip,boolean multi){
      return preview&&!fullscreen&&!pip&&!multi;
    }
  }

  static final class CobraFoldAspectPolicy {''')
 return s

def patch_ambient(s):
 return once(s,'  private void updateSourceRect() {','''  // A paused frame must follow a resized/repositioned player without a ticker.
  void geometryChanged() {
    updateSourceRect();fieldDirty=true;invalidate();invalidateGlass();
    if(enabled&&!animateFrames&&haveFrame)capture();
  }

  private void updateSourceRect() {''')

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.root;shell=root/'shell-kodi'
 for path,fn in [(ACTIVITY,patch_activity),(AMBIENT,patch_ambient)]:
  f=shell/path;f.write_text(fn(f.read_text()))
 f=shell/GRADLE;f.write_text(once(once(f.read_text(),'versionCode 2103276','versionCode 2103277'),'1.0.9-Whole-UI-Ambient-RC1',RELEASE))
 f=root/'scripts/infinity_background_resume.py';s=f.read_text()
 for key,value in [('VERSION_CODE','2103277'),('RELEASE',repr(RELEASE)),('BASE_COMMIT',repr(BASE)),('BASE_APK_SHA256',repr('6ece90dc54b6078a3a58365bee3a13ec28e01329995d88c184de1507f5a62ac6'))]:
  s,n=re.subn(r'^'+key+r' = .*$',key+' = '+value,s,flags=re.M);assert n==1
 f.write_text(s)
 f=root/'scripts/package_background_resume.py';f.write_text(f.read_text().replace('Infinity-2103276-Whole-UI-Ambient-RC1','Infinity-2103277-Mini-Player-Fill-RC1').replace("'base_run':36783367196","'base_run':36787860835").replace('repairs/whole-ui-ambient-2103276/DEVICE-TEST.md','repairs/mini-player-fill-2103277/DEVICE-TEST.md'))
 f=root/'engine/background-resume-source.json';r=json.loads(f.read_text());r.update(base_source_commit=BASE,base_apk_sha256='6ece90dc54b6078a3a58365bee3a13ec28e01329995d88c184de1507f5a62ac6',version_code=2103277,release=RELEASE,candidate_locked=False,physical_device_verified=False,mini_player_center_crop=True)
 for path in [ACTIVITY,AMBIENT,GRADLE]:r['files'].setdefault(path,{})['after']=sha((shell/path).read_bytes())
 f.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');a.out.mkdir(parents=True,exist_ok=True)
 print('Applied bounded 2103277 mini-player fill and paused ambient geometry refresh.')
if __name__=='__main__':main()
