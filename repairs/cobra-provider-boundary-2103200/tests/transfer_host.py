#!/usr/bin/env python3
"""Execute exact provider TransferThread against controlled file/output collaborators."""
from pathlib import Path
import argparse, hashlib, json, subprocess

p=argparse.ArgumentParser();p.add_argument('--provider',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
text=a.provider.read_text();start=text.index('  static class TransferThread extends Thread');depth=0;begin=text.index('{',start)
for index in range(begin,len(text)):
    depth += (text[index]=='{')-(text[index]=='}')
    if depth==0:thread=text[start:index+1];break
harness=r'''
import java.io.*;
public class FileTransferHost {
 static final String TAG="Fixture";
 static String scenario;
 static int inputCloses,outputCloses,reads,bytes;
 static class Log {static void w(String t,String m){}static void e(String t,String m,Throwable e){}}
 static class XBMCFile {
   XBMCFile(){if(scenario.equals("linkage_error"))throw new NoClassDefFoundError("fixture");}
   boolean Open(String path){return !scenario.equals("false_open");}
   boolean Eof(){if(scenario.equals("eof_error"))throw new IllegalStateException("fixture");return reads>0;}
   byte[] Read(){reads++;if(scenario.equals("read_error"))throw new IllegalStateException("fixture");if(scenario.equals("null_read"))return null;return new byte[]{1,2,3};}
   void Close(){inputCloses++;if(scenario.equals("native_close_error"))throw new IllegalStateException("fixture");}
 }
 static class Output extends OutputStream {
   @Override public void write(int b)throws IOException{if(scenario.equals("write_error"))throw new IOException("fixture");bytes++;}
   @Override public void flush()throws IOException{if(scenario.equals("flush_error"))throw new IOException("fixture");}
   @Override public void close()throws IOException{outputCloses++;if(scenario.equals("output_close_error"))throw new IOException("fixture");}
 }
 /* EXACT_THREAD */
 public static void main(String[] args){
   int failed=0;
   for(String name:new String[]{"success","false_open","read_error","write_error","flush_error","native_close_error","output_close_error","eof_error","linkage_error","null_read"}){
     scenario=name;inputCloses=outputCloses=reads=bytes=0;Throwable caught=null;
     try{new TransferThread("fixture",new Output()).run();}catch(Throwable e){caught=e;}
     boolean pass=caught==null&&outputCloses==1&&(name.equals("linkage_error")||name.equals("false_open")||inputCloses==1)&&(!name.equals("success")||bytes==3);
     if(!pass)failed++;
     System.out.println(name+":"+(pass?"PASS":"FAIL")+":inputCloses="+inputCloses+":outputCloses="+outputCloses+":bytes="+bytes+":thrown="+(caught==null?"none":caught.getClass().getSimpleName()));
   }
   System.out.println("TOTAL=10 FAILED="+failed);if(failed>0)System.exit(1);
 }
}
'''.replace('/* EXACT_THREAD */',thread)
(a.out/'FileTransferHost.java').write_text(harness)
compiled=subprocess.run(['java','-XX:-UsePerfData','com.sun.tools.javac.Main',str(a.out/'FileTransferHost.java')],capture_output=True,text=True)
if compiled.returncode:print(compiled.stderr);raise SystemExit(compiled.returncode)
result=subprocess.run(['java','-XX:-UsePerfData','-cp',str(a.out),'FileTransferHost'],capture_output=True,text=True);log=result.stdout+result.stderr;(a.out/'tests.log').write_text(log)
(a.out/'result.json').write_text(json.dumps({'source_class_sha256':hashlib.sha256(thread.encode()).hexdigest(),'exit_code':result.returncode,'scenarios':10,'evidence':'Exact production TransferThread control flow with deterministic native-file/output collaborators; not JNI/physical stream evidence','output':log},indent=2)+'\n')
print(log);raise SystemExit(result.returncode)
