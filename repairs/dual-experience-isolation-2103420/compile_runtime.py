"""Compile the narrow production delta; compile-only signatures never ship."""
import argparse
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED
from inventory import HERE, ROOT, file_sha, load, save

ANDROID_SHA='6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad'
D8_SHA='305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5'

def compile_runtime(work,jars,android,d8):
    if file_sha(android)!=ANDROID_SHA or file_sha(d8)!=D8_SHA:raise ValueError('Pinned compiler inputs required')
    pins=load(ROOT/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json')
    if {p.name:file_sha(p) for p in jars.glob('*.jar')}!=pins:raise ValueError('Pinned DEX tools required')
    stubs=work/'compile-only';stubs.mkdir()
    for owner in ('Infinity','Cobra','Shell'):
        name=owner+'JavaWriteBarrier'
        (stubs/(name+'.java')).write_text('''package com.projectinfinity.kodi;
public final class NAME {
 public static Object ownerLock(){throw new AssertionError();}
 public static boolean canBegin(String t){throw new AssertionError();}
 public static boolean begin(String t){throw new AssertionError();}
 public static String sealIfReady(String t){throw new AssertionError();}
 public static boolean authorized(String t,String p){throw new AssertionError();}
 public static String pending(){throw new AssertionError();}
 public static void cancel(String t){throw new AssertionError();}
 public static void userEntry(){throw new AssertionError();}
}'''.replace('NAME',name))
    for owner in ('Cobra','Shell'):
        (stubs/(owner+'JavaPersistence.java')).write_text('''package com.projectinfinity.kodi;
public final class OWNERJavaPersistence {
 public static android.content.SharedPreferences preferences(android.content.Context c,String n,int m){throw new AssertionError();}
 public static void userEntry(android.content.Context c){throw new AssertionError();}
 public static class Output extends java.io.FileOutputStream {
  public Output(java.io.File f)throws java.io.FileNotFoundException {super(f);throw new AssertionError();}
 }
}'''.replace('OWNER',owner))
    classes=work/'compiled';classes.mkdir()
    subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-g:none',
                    '-Xlint:all,-options,-try','-cp',str(android),'-d',str(classes),
                    *map(str,sorted((work/'java').rglob('*.java'))),*map(str,sorted(stubs.glob('*.java')))],check=True)
    excluded={'InfinityJavaWriteBarrier','CobraJavaWriteBarrier','ShellJavaWriteBarrier','CobraJavaPersistence','ShellJavaPersistence'}
    included=[]
    with ZipFile(work/'runtime.jar','w',ZIP_DEFLATED) as jar:
        for p in sorted(classes.rglob('*.class')):
            if p.stem.split('$')[0] in excluded:continue
            name=p.relative_to(classes).as_posix();jar.write(p,name);included.append(name)
    helpers=work/'helpers';helpers.mkdir()
    subprocess.run(['java','-cp',str(d8),'com.android.tools.r8.D8','--min-api','21','--lib',str(android),
                    '--output',str(helpers),str(work/'runtime.jar')],check=True)
    subprocess.run(['java','-cp',str(jars/'*'),'org.jf.smali.Main','assemble','--api','21',
                    str(work/'changed-smali'),'-o',str(work/'changed.dex')],check=True)
    if not (work/'changed.dex').is_file():raise ValueError('smali did not produce DEX')
    save(work/'COMPILE.json',{'status':'COMPILED_NOT_RELEASE_APPROVED','java_classes':included,
                             'compile_only_stubs_packaged':False,'android_sha256':ANDROID_SHA,'d8_sha256':D8_SHA,
                             'outputs':{str(p.relative_to(work)):file_sha(p) for p in (work/'changed.dex',helpers/'classes.dex')}})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('work','jars','android','d8'):p.add_argument('--'+n,type=Path,required=True)
    compile_runtime(**vars(p.parse_args()))
