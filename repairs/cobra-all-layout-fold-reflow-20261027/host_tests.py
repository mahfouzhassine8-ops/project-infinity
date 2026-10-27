"""Execute only the selected Cobra geometry tests, using rebuilt production DEX."""
import argparse,os,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent;ISO=HERE.parent/'dual-experience-isolation-2103420';sys.path.insert(0,str(ISO))
from inventory import save,file_sha

def run(args):subprocess.run(list(map(str,args)),check=True)
def prepare(work,baseline,dex2jar,out):
 out=out.resolve();out.mkdir();errors=out/'translation-errors';errors.mkdir()
 def translate(path,label):
  jar=out/(label+'.jar');run(['java','-cp',str(dex2jar/'lib/*'),'com.googlecode.dex2jar.tools.Dex2jarCmd',path,'-o',jar,'-e',errors/(label+'.zip')]);return jar
 production=[translate(p,'production-'+p.stem) for p in sorted((work/'owner-dex/COBRA').glob('*.dex'))]
 support=[translate(baseline/n,'support-'+n[:-4]) for n in ['classes.dex','classes2.dex','classes3.dex']]
 for label,inputs in [('production',production),('support',support)]:
  seen=set()
  with ZipFile(out/(label+'.jar'),'w',ZIP_DEFLATED) as target:
   for p in inputs:
    with ZipFile(p) as z:
     for n in z.namelist():
      if n in seen or not n.endswith('.class') or n.startswith(('com/google/common/','com/google/thirdparty/')):continue
      if label=='support' and not n.startswith(('com/projectinfinity/kodi/','androidx/')):continue
      seen.add(n);target.writestr(n,z.read(n))
 tests=out/'src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
 shutil.copyfile(HERE/'tests/CobraMeasuredReflowTest.java',tests/'CobraMeasuredReflowTest.java')
 pom=(ISO/'tests/pom.xml').read_text().replace('${runtime.work}/changed-host.jar',str(out/'production.jar')).replace('${baseline.dex}/application-host.jar',str(out/'support.jar'))
 (out/'pom.xml').write_text(pom)
 # Robolectric's AndroidX dependencies contain classes.jar in AAR archives.
 libs=out/'android-test-libs';libs.mkdir()
 for artifact,name in [('monitor','monitor.jar'),('espresso-idling-resource','espresso.jar')]:
  archives=list((Path.home()/'.m2/repository/androidx/test').rglob(artifact+'-*.aar'))
  if archives:
   with ZipFile(sorted(archives)[-1]) as z:(libs/name).write_bytes(z.read('classes.jar'))
 save(out/'INPUTS.json',{'production_dex':{p.name:file_sha(p) for p in (work/'owner-dex/COBRA').glob('*.dex')},'test_source_sha256':file_sha(HERE/'tests/CobraMeasuredReflowTest.java'),'runtime':'Robolectric API35; translated actual production DEX; disposable views and data; no native playback or shutdown scenario'})
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['work','baseline','dex2jar','out']:p.add_argument('--'+n,type=Path,required=True)
 prepare(**vars(p.parse_args()))
