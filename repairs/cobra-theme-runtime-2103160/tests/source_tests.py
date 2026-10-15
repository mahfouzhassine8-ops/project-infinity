#!/usr/bin/env python3
"""Executable source-scope, corruption refusal, inventory and real Java archive-policy checks."""
from pathlib import Path
import argparse, importlib.util, json, re, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('patch160',ROOT/'apply.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def run(baseline,out):
 original={m.ACT:(baseline/'InfinityLiveActivity.java.in').read_text(),m.SPLASH:(baseline/'Splash.java.in').read_text()}
 changed,slots,proof=m.generate(original);count=0
 for path in original:
  assert m.sha(original[path])==m.HASHES[path];count+=1
  wrong=dict(original);wrong[path]+='\n'
  try:m.generate(wrong)
  except ValueError:count+=1
  else:raise AssertionError('Unknown preimage was accepted')
  wrong=dict(original);wrong[path]=changed[path]
  try:m.generate(wrong)
  except ValueError:count+=1
  else:raise AssertionError('Already patched source was accepted')
 assert len(slots)>750 and len({x['key'] for x in slots})==len(slots);count+=1
 # All static data/EPG/player policies remain exact. No aesthetic token enters a core policy.
 for a,b,name,static,h in m.members(original[m.ACT]):
  if not static:continue
  matches=[(x,y) for x,y,n,st,he in m.members(changed[m.ACT]) if n==name and st]
  if len(matches)==1:
   x,y=matches[0];assert original[m.ACT][a:b]==changed[m.ACT][x:y],name;count+=1
 protected=['cobraReadEpgCache','cobraWriteEpgCache','buildPlayer','loadGuideAsync','startSinglePlayer','startCobraPreview','setMultiAudio','returnToInfinity','pauseCobraForBackground','resumeCobraAfterBackground','cobraInspectMultiHealth','cobraInspectSurfaceRecovery','cobraPreferenceKey','cobraSavePreferences']
 checked=[]
 for name in protected:
  # Names vary across old recipe forks; require the actual current member when it exists.
  found=[n for _,_,n,_,_ in m.members(original[m.ACT])]
  if name not in found:continue
  a,b=m.method_span(original[m.ACT],name);x,y=m.method_span(changed[m.ACT],name)
  assert original[m.ACT][a:b]==changed[m.ACT][x:y],name;checked.append(name);count+=1
 # Cache headers are binary format sentinels, not colors. The first audit caught this hazard.
 assert 'cobra.cobraReadEpgCache.colors' not in changed[m.ACT] and 'cobra.cobraWriteEpgCache.colors' not in changed[m.ACT];count+=1
 before_state=[(a,b) for a,b,n,_,_ in m.members(original[m.SPLASH]) if n=='StateMachine'][0]
 after_state=[(a,b) for a,b,n,_,_ in m.members(changed[m.SPLASH]) if n=='StateMachine'][0]
 assert original[m.SPLASH][slice(*before_state)]==changed[m.SPLASH][slice(*after_state)];count+=1
 for name in ('startXBMC','launchInfinityExperience','onCreate','showExperienceCardSettings','showLegacyInfinityExperienceChooser'):
  a,b=m.method_span(original[m.SPLASH],name);x,y=m.method_span(changed[m.SPLASH],name)
  assert original[m.SPLASH][a:b]==changed[m.SPLASH][x:y],name;count+=1
 runtime=(ROOT/'CobraVisualTheme.java.in').read_text();renderer=(ROOT/'CobraVisualRenderer.java.in').read_text()
 for forbidden in ('ExoPlayer','setMediaItem','setVideoTextureView','DexClassLoader','loadLibrary','Runtime.getRuntime','HttpURLConnection','WebViewClient','evaluateJavascript'):
  assert forbidden not in runtime+renderer,forbidden;count+=1
 for name in ('safeName','inside','hash','read','unpack'):
  m.method_span(runtime,name);count+=1
 out.mkdir(parents=True,exist_ok=True)
 imports='import java.io.*;import java.nio.charset.StandardCharsets;import java.security.MessageDigest;import java.util.*;import java.util.zip.*;import java.nio.file.*;'
 code=imports+'\npublic class PackagePolicyHost {\nstatic final String PREFIX="script.infinity.cobra.theme/";static final long MAX_FILE=12L*1024*1024,MAX_ZIP=64L*1024*1024,MAX_TOTAL=64L*1024*1024;static final int MAX_FILES=256;\n'
 for name in ('safeName','inside','hash','read','unpack'):
  a,b=m.method_span(runtime,name);code+=runtime[a:b]+'\n'
 for a,b,name,static,h in m.members(runtime):
  if name=='LimitedInput':code+=runtime[a:b]+'\n'
 code+='''
 static int checks;static void ok(boolean value){checks++;if(!value)throw new AssertionError("policy check "+checks);}
 interface Throwing {void run()throws Exception;}
 static void reject(Throwing run)throws Exception{boolean failed=false;try{run.run();}catch(IOException e){failed=true;}ok(failed);}
 static byte[] zip(String...names)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(out)){for(String name:names){z.putNextEntry(new ZipEntry(name));z.write(new byte[]{1,2,3});z.closeEntry();}}return out.toByteArray();}
 public static void main(String[]args)throws Exception{
  for(String bad:new String[]{"../x","a/../x","/x","C:/x","a\\\\b","a//b","a/./b","a/", "https://evil/x", "a\\u0000b"})ok(!safeName(bad));
  for(String good:new String[]{"resources/assets/badge.png","resources/visual-theme.json","file-1_2.webp"})ok(safeName(good));
  ok(hash("abc".getBytes("UTF-8")).equals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"));
  ok(read(new ByteArrayInputStream(new byte[]{1,2,3}),3).length==3);reject(()->read(new ByteArrayInputStream(new byte[4]),3));
  reject(()->read(new InputStream(){public int read(){return 0;}public int read(byte[]b){return 0;}},100));
  reject(()->unpack(new ByteArrayInputStream(zip(PREFIX+"../escape"))));reject(()->unpack(new ByteArrayInputStream(zip("wrong-root/a"))));
  reject(()->unpack(new ByteArrayInputStream(zip(PREFIX+"a.png",PREFIX+"A.png"))));
  ok(unpack(new ByteArrayInputStream(zip(PREFIX+"resources/visual-theme.json"))).size()==1);
  Path tmp=Files.createTempDirectory("visual-policy");Path outside=Files.createTempDirectory("visual-outside");try{Files.createSymbolicLink(tmp.resolve("link"),outside);reject(()->inside(tmp.toFile(),"link/escape.png"));ok(inside(tmp.toFile(),"normal/file").getCanonicalPath().startsWith(tmp.toFile().getCanonicalPath()+File.separator));}finally{Files.deleteIfExists(tmp.resolve("link"));Files.delete(tmp);Files.delete(outside);}
  String[] many=new String[257];for(int i=0;i<many.length;i++)many[i]=PREFIX+"file-"+i;reject(()->unpack(new ByteArrayInputStream(zip(many))));
  System.out.println("PASS: "+checks+" actual Java archive/path/read policy checks; bitmap/Android gates are separate.");
 }
}'''
 java=out/'PackagePolicyHost.java';java.write_text(code)
 subprocess.run(['javac','--release','8','-encoding','UTF-8','-d',str(out/'classes'),str(java)],check=True)
 result=subprocess.run(['java','-cp',str(out/'classes'),'PackagePolicyHost'],capture_output=True,text=True,check=True,timeout=20)
 print(result.stdout);(out/'java-policy.log').write_text(result.stdout)
 (out/'results.json').write_text(json.dumps({'source_checks':count,'slot_count':len(slots),'protected_members':checked,'source_before_after':proof,'java_policy_passed':True,'android_tests_run':False,'physical_device_verified':False,'official':False},indent=2)+'\n')
 print('PASS:',count,'source guards;',len(slots),'catalogued visual resource sites')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.baseline,a.out)
