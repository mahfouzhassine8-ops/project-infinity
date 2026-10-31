"""Existing OS-only app_process UI bridge; never an application/test APK."""
import argparse
from pathlib import Path
import sys
from zipfile import ZipFile,ZIP_DEFLATED
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'release-stage'))
from prepare import file_sha,save,run,ISO
sys.path.insert(0,str(ISO))
from compile_runtime import ANDROID_SHA,D8_SHA

def build(android,d8,out):
 assert file_sha(android)==ANDROID_SHA and file_sha(d8)==D8_SHA
 assert not out.exists();out.mkdir(parents=True);classes=out/'classes';classes.mkdir()
 source=HERE/'CobraDrawerDriver.java';source_pin=file_sha(source)
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-cp',android,'-d',classes,source)
 names={str(p.relative_to(classes)) for p in classes.rglob('*.class')};assert names=={'qa/CobraDrawerDriver.class','qa/CobraDrawerDriver$Tree.class'}
 program=out/'program.jar'
 with ZipFile(program,'w',ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes))
 dex=out/'dex';dex.mkdir();run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','23','--lib',android,'--output',dex,program)
 jar=out/'CobraDrawerDriver.jar'
 with ZipFile(jar,'w',ZIP_DEFLATED) as z:z.write(dex/'classes.dex','classes.dex')
 assert file_sha(source)==source_pin,'QA source changed during compilation; refuse stale driver binding'
 save(out/'BUILD.json',dict(status='COMPILED_OS_ONLY_UI_DRIVER_NO_APK',source_sha256=source_pin,android_sha256=ANDROID_SHA,D8_sha256=D8_SHA,jar_sha256=file_sha(jar),classes=sorted(names),production_code='NOT_INCLUDED',shutdown='NOT_RUN'))

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['android','d8','out']:p.add_argument('--'+n,type=Path,required=True)
 build(**vars(p.parse_args()))
