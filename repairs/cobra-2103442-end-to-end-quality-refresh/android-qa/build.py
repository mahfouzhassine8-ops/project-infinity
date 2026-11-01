"""Compile QA public-UI bridge only; no diagnostic application APK."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
H=Path(__file__).resolve().parent;R=H.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(*args):subprocess.run(list(map(str,args)),check=True)
def build(android,d8,out):
 assert not out.exists();out.mkdir(parents=True);classes=out/'classes';classes.mkdir()
 sources=[H/'CobraQualityDriver.java',R/'repairs/cobra-2103435-followups/drawer-only/android-qa/CobraDrawerDriver.java']
 run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none','-cp',android,'-d',classes,*sources)
 with ZipFile(out/'program.jar','w',ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes))
 dex=out/'dex';dex.mkdir();run('java','-cp',d8,'com.android.tools.r8.D8','--min-api','23','--lib',android,'--output',dex,out/'program.jar')
 with ZipFile(out/'CobraQualityDriver.jar','w',ZIP_DEFLATED) as z:z.write(dex/'classes.dex','classes.dex')
 (out/'BUILD.json').write_text(json.dumps(dict(status='COMPILED_QA_ONLY_NO_APK',sources={str(p.relative_to(R)):sha(p) for p in sources},jar_sha256=sha(out/'CobraQualityDriver.jar')),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ['android','d8','out']:p.add_argument('--'+name,type=Path,required=True)
 build(**vars(p.parse_args()))
