"""Build one disposable QA-signed copy of exact candidate payload plus source fixture."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
H=Path(__file__).resolve().parents[1];R=H.parents[1]
sys.path.insert(0,str(R/'repairs/dual-experience-isolation-2103420'))
from component_bundles import set_version
from inventory import file_sha,SIGNATURE
def run(*a):subprocess.run(list(map(str,a)),check=True)
def main(a):
 a.out.mkdir(parents=True);media=a.out/'media';media.mkdir()
 subtitle=a.out/'fixture.srt'
 def stamp(s,ms=0):return f'{s//3600:02}:{s//60%60:02}:{s%60:02},{ms:03}'
 subtitle.write_text(''.join(f'{i+1}\n{stamp(i*5)} --> {stamp(i*5+4,900)}\nExternal subtitle fixture\n\n' for i in range(120)))
 for name,color,tone in [('a','red',440),('b','green',660),('c','blue',880),('end','yellow',550)]:
  args=['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i',f'color=c={color}:s=640x360:r=24','-f','lavfi','-i',f'sine=frequency={tone}:sample_rate=48000']
  if name=='a':args+=['-f','lavfi','-i','sine=frequency=990:sample_rate=48000','-i',str(subtitle),'-map','0:v','-map','1:a','-map','2:a','-map','3:s','-c:s','mov_text','-metadata:s:a:0','language=eng','-metadata:s:a:1','language=fra','-metadata:s:s:0','language=eng']
  args+=['-t','3' if name=='end' else '600','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',media/(name+'.mp4')]
  run(*args)
 run('ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','10','-c:a','aac',media/'audio.mp4')
 (media/'bad.mp4').write_bytes(b'not a video\n')
 assert file_sha(a.baseline)=='2c20613f9056e84fea402cf67729939a205b7d9afb87ec1b6fab800a641efbd3'
 replaced={'classes3.dex':a.owner/'INFINITY-new.dex'}
 with ZipFile(a.baseline) as old,ZipFile(a.out/'candidate-unsigned.apk','w') as new:
  for info in old.infolist():
   if info.filename in SIGNATURE:continue
   raw=replaced[info.filename].read_bytes() if info.filename in replaced else old.read(info.filename)
   if info.filename=='AndroidManifest.xml':raw=set_version(raw,2103449)
   new.writestr(info,raw)
 classes=a.out/'source-classes';classes.mkdir();dex=a.out/'source-dex';dex.mkdir()
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-cp',a.android,'-d',classes,*sorted((R/'repairs/infinity-preview-2103447-resume/android-qa').glob('*.java')))
 with ZipFile(a.out/'source.jar','w',ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes))
 run('java','-cp',a.sdk/'lib/d8.jar','com.android.tools.r8.D8','--min-api','23','--lib',a.android,'--output',dex,a.out/'source.jar')
 observer=a.out/'observer-classes';observer.mkdir();observer_dex=a.out/'observer-dex';observer_dex.mkdir()
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-cp',a.android,'-d',observer,R/'repairs/infinity-2103445-standalone-external-player/android-qa/observer/ImmediateHierarchy.java')
 with ZipFile(a.out/'observer-classes.jar','w',ZIP_DEFLATED) as z:
  for p in observer.rglob('*.class'):z.write(p,p.relative_to(observer))
 run('java','-cp',a.sdk/'lib/d8.jar','com.android.tools.r8.D8','--min-api','23','--lib',a.android,'--output',observer_dex,a.out/'observer-classes.jar')
 with ZipFile(a.out/'InfinityExternalObserver.jar','w',ZIP_DEFLATED) as z:z.write(observer_dex/'classes.dex','classes.dex')
 run(a.sdk/'aapt2','link','-I',a.android,'--manifest',R/'repairs/infinity-preview-2103447-resume/android-qa/AndroidManifest.xml','-A',media,'-o',a.out/'source-unsigned.apk')
 with ZipFile(a.out/'source-unsigned.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
 run('keytool','-genkeypair','-keystore',a.out/'qa-only.jks','-storepass','qa-only-password','-keypass','qa-only-password','-alias','qa','-keyalg','RSA','-dname','CN=Disposable external player QA, O=Not for installation','-validity','2')
 for name in ('candidate','source'):
  run(a.sdk/'zipalign','-p','4',a.out/(name+'-unsigned.apk'),a.out/(name+'-aligned.apk'))
  run(a.sdk/'apksigner','sign','--ks',a.out/'qa-only.jks','--ks-pass','pass:qa-only-password','--key-pass','pass:qa-only-password','--out',a.out/(name+'-qa.apk'),a.out/(name+'-aligned.apk'))
  (a.out/(name+'-unsigned.apk')).unlink();(a.out/(name+'-aligned.apk')).unlink()
 (a.out/'BUILD.json').write_text(json.dumps({'status':'DISPOSABLE_QA_ONLY','source':os.environ.get('GITHUB_SHA'),'candidate_sha256':file_sha(a.out/'candidate-qa.apk'),'original_key':False,'replaced':{n:file_sha(p) for n,p in replaced.items()},'baseline_sha256':file_sha(a.baseline)},indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('baseline','owner','android','sdk','out'):p.add_argument('--'+n,type=Path,required=True)
 main(p.parse_args())
