#!/usr/bin/env python3
"""Execute the REAL focus adapter against instrumented fake Android classes.

This tests our object ownership / request lifecycle, not Android audio service or
Samsung behavior. API signatures are independently checked against android.jar.
"""
from pathlib import Path
import argparse
import subprocess

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
src=a.out/'src';classes=a.out/'classes'
fixtures={
'android/os/Build.java':'''package android.os; public class Build {public static class VERSION {public static int SDK_INT=34;}}''',
'android/util/Log.java':'''package android.util; public class Log {public static int i(String t,String s){return 0;} public static int w(String t,String s,Throwable e){return 0;}}''',
'android/content/Context.java':'''package android.content; public class Context {
 public static final String AUDIO_SERVICE="audio"; public android.media.AudioManager manager;
 public Context(android.media.AudioManager m){manager=m;} public Context getApplicationContext(){return this;}
 public Object getSystemService(String s){return manager;}
}''',
'android/media/AudioAttributes.java':'''package android.media; public class AudioAttributes {
 public static final int CONTENT_TYPE_UNKNOWN=0, CONTENT_TYPE_SPEECH=1, CONTENT_TYPE_MUSIC=2, CONTENT_TYPE_MOVIE=3, CONTENT_TYPE_SONIFICATION=4, USAGE_MEDIA=1;
 public int usage, content; public static class Builder {
 private final AudioAttributes a=new AudioAttributes();
 public Builder setUsage(int v){a.usage=v;return this;}
 public Builder setContentType(int v){a.content=v;return this;}
 public AudioAttributes build(){return a;}
 }}''',
'android/media/AudioFocusRequest.java':'''package android.media; public class AudioFocusRequest {
 public AudioAttributes attributes;public AudioManager.OnAudioFocusChangeListener listener;
 public boolean delay, duck; public static class Builder {
 private final AudioFocusRequest r=new AudioFocusRequest(); public Builder(int gain){}
 public Builder setAudioAttributes(AudioAttributes a){r.attributes=a;return this;}
 public Builder setAcceptsDelayedFocusGain(boolean b){r.delay=b;return this;}
 public Builder setWillPauseWhenDucked(boolean b){r.duck=b;return this;}
 public Builder setOnAudioFocusChangeListener(AudioManager.OnAudioFocusChangeListener l){r.listener=l;return this;}
 public AudioFocusRequest build(){return r;}
 }}''',
'android/media/AudioManager.java':'''package android.media; public class AudioManager {
 public static final int STREAM_MUSIC=3,AUDIOFOCUS_GAIN=1,AUDIOFOCUS_REQUEST_GRANTED=1,AUDIOFOCUS_REQUEST_DELAYED=2;
 public interface OnAudioFocusChangeListener {void onAudioFocusChange(int f);}
 public Object lastRequest,lastAbandon; public int requests,abandons,result=1,abandonResult=1,stream=-1;public boolean requestThrows,abandonThrows;
 public int requestAudioFocus(AudioFocusRequest r){lastRequest=r;requests++;if(requestThrows)throw new SecurityException();return result;}
 public int requestAudioFocus(OnAudioFocusChangeListener l,int s,int g){lastRequest=l;stream=s;requests++;if(requestThrows)throw new SecurityException();return result;}
 public int abandonAudioFocusRequest(AudioFocusRequest r){lastAbandon=r;abandons++;if(abandonThrows)throw new IllegalStateException();return abandonResult;}
 public int abandonAudioFocus(OnAudioFocusChangeListener l){lastAbandon=l;abandons++;if(abandonThrows)throw new IllegalStateException();return abandonResult;}
}''',
'com/projectinfinity/kodi/FocusTest.java':'''package com.projectinfinity.kodi;
import android.media.*;import android.content.Context;import android.os.Build;
public final class FocusTest {
 static void require(boolean b,String s){if(!b)throw new AssertionError(s);}
 public static void main(String[] args){
  int checks=0;
  for(int sdk:new int[]{21,25,26,34}) {
   Build.VERSION.SDK_INT=sdk;AudioManager m=new AudioManager();
   AudioManager.OnAudioFocusChangeListener l=(f)->{};
   InfinityAudioFocusHook h=new InfinityAudioFocusHook(new Context(m));
   require(h.acquire(3,l),"video focus");Object first=m.lastRequest;
   if(sdk>=26){AudioFocusRequest r=(AudioFocusRequest)first;require(r.attributes.usage==1&&r.attributes.content==3,"movie attributes");require(r.listener==l&&r.duck&&r.delay,"preserve listener options");}
   else require(m.stream==AudioManager.STREAM_MUSIC,"legacy volume stream remains MUSIC, not content type");
   require(h.acquire(3,l)&&m.lastRequest==first,"reuse same request");
   require(h.release()&&m.lastAbandon==first,"abandon exact object");
   int n=m.abandons;require(h.release()&&m.abandons==n,"idempotent stop");
   require(h.acquire(3,l),"resume");Object resumed=m.lastRequest;
   require(h.acquire(2,l),"video to music");
   require(m.lastAbandon==resumed,"release old before replacing");
   if(sdk>=26) require(((AudioFocusRequest)m.lastRequest).attributes.content==2,"music attributes");
   require(h.acquire(999,l),"invalid becomes music");
   h.release();m.result=0;require(!h.acquire(3,l),"failed focus not success");n=m.abandons;h.release();require(m.abandons==n,"failed request not owned");
   m.result=2;if(sdk>=26){require(!h.acquire(3,l),"delayed is not granted yet");Object delayed=m.lastRequest;h.release();require(m.lastAbandon==delayed,"cancel pending delayed request");}
   m.result=1;m.requestThrows=true;require(!h.acquire(3,l),"request exception isolated");m.requestThrows=false;
   require(h.acquire(3,l),"recovery");Object recovery=m.lastRequest;m.abandonThrows=true;
   require(!h.release(),"release exception reported");m.abandonThrows=false;require(h.release()&&m.lastAbandon==recovery,"retry releases exact owned object");
   require(!h.acquire(3,null),"null listener rejected");
   require(!new InfinityAudioFocusHook(new Context(null)).acquire(3,l),"missing service rejected");checks++;
  }
  System.out.println("PASS: real focus adapter lifecycle under fake Android, "+checks+" API scenarios; device test pending");
 }
}'''
}
for rel,text in fixtures.items():
 f=src/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
f=src/'com/projectinfinity/kodi/InfinityAudioFocusHook.java'
f.write_text((ROOT/'patches/infinity-audio-policy/InfinityAudioFocusHook.java.in').read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi'))
classes.mkdir(parents=True,exist_ok=True)
subprocess.run(['javac','-source','8','-target','8','-d',str(classes),*[str(f) for f in src.rglob('*.java')]],check=True)
subprocess.run(['java','-cp',str(classes),'com.projectinfinity.kodi.FocusTest'],check=True)
