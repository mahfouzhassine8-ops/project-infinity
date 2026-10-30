"""One QA shell DEX main. No application build, signing or lifecycle operation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/"repairs/dual-experience-isolation-2103420/compile_runtime.py").is_file())
sys.path.insert(0,str(REPO/'repairs/dual-experience-isolation-2103420'))
from compile_runtime import ANDROID_SHA,D8_SHA

def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def build(android,d8,out):
    assert sha(android)==ANDROID_SHA and sha(d8)==D8_SHA,'Existing pinned official compilers required'
    assert not out.exists();out.mkdir(parents=True)
    source=HERE/'CobraFoldMoreDriver.java';classes=out/'classes';classes.mkdir()
    subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none',
                    '-cp',str(android),'-d',str(classes),str(source)],check=True)
    names={p.relative_to(classes).as_posix() for p in classes.rglob('*.class')}
    assert names=={'qa/CobraFoldMoreDriver.class','qa/CobraFoldMoreDriver$Tree.class'}
    program=out/'program.jar'
    with ZipFile(program,'w',ZIP_DEFLATED) as archive:
        for p in classes.rglob('*.class'):archive.write(p,p.relative_to(classes))
    dex=out/'dex';dex.mkdir()
    subprocess.run(['java','-cp',str(d8),'com.android.tools.r8.D8','--min-api','23','--lib',str(android),
                    '--output',str(dex),str(program)],check=True)
    assert {p.name for p in dex.iterdir()}=={'classes.dex'}
    jar=out/'CobraFoldMoreDriver.jar'
    with ZipFile(jar,'w',ZIP_DEFLATED) as archive:archive.write(dex/'classes.dex','classes.dex')
    receipt=dict(source_sha256=sha(source),android_sha256=sha(android),D8_sha256=sha(d8),
                 class_files=sorted(names),jar_sha256=sha(jar),APK='EXACT_REJECTED434_UNCHANGED',
                 QA='SINGLE_OS_UIAUTOMATION_CONNECTION; NO_RUNTESТ_JUNIT_OR_INSTRUMENTATION_APK',shutdown='NOT_RUN')
    (out/'BUILD-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('android','d8','out'):p.add_argument('--'+name,type=Path,required=True)
    build(**vars(p.parse_args()))
