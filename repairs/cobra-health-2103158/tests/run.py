#!/usr/bin/env python3
"""Execute production policies plus final-source integration/preservation tests. Not a decoder test."""
import argparse,importlib.util,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cobra158_apply',ROOT/'apply.py');patcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(patcher)
HARNESS=r'''
  static int count;
  static void check(boolean value,String message){count++;if(!value)throw new AssertionError(message);}
  static void feed(CobraRecoveryPolicy p,int begin,int end,boolean eligible,int framesMode,boolean audio,boolean moving,boolean surfaceMoving){
    for(int t=begin;t<=end;t+=1000)p.observe(t,eligible,moving?t:0,framesMode==1?t/20:0,audio?t/10:0,surfaceMoving?t*1000000L+100:100);
  }
  public static void main(String[] args){
    CobraRecoveryPolicy p=new CobraRecoveryPolicy();
    for(int t=0;t<600000;t+=1000)check(!p.observe(t,true,t,t/20,t/10,t*1000000L+100),"healthy frames must never trigger");
    check(p.attempts==0,"healthy budget untouched");
    p=new CobraRecoveryPolicy();for(int t=0;t<20000;t+=1000)check(!p.observe(t,true,t,0,t/10,0),"initial grace");
    check(p.observe(20000,true,20000,0,2000,0),"sustained audio + clock, absent video triggers first reattach");
    check(p.attempts==1,"attempt consumed before adapter");
    for(int t=21000;t<80000;t+=1000)check(!p.observe(t,true,t,0,t/10,0),"grace and cooldown block a second action");
    check(p.observe(80000,true,80000,0,8000,0),"second action only after cooldown");
    for(int t=81000;t<300000;t+=1000)check(!p.observe(t,true,t,0,t/10,0),"session maximum blocks loop");
    check(p.attempts==2&&p.state.equals("automatic_limit_reached"),"exhaustion explicit");
    p.suspend();feed(p,301000,400000,true,0,true,true,false);check(p.attempts==2,"resume cannot reset budget");
    for(int mask=0;mask<8;mask++){
      p=new CobraRecoveryPolicy();boolean eligible=(mask&1)!=0,audio=(mask&2)!=0,moving=(mask&4)!=0;
      feed(p,0,60000,eligible,0,audio,moving,false);check(p.attempts==(mask==7?1:0),"need all eligibility/audio/position conditions "+mask);
    }
    p=new CobraRecoveryPolicy();for(int t=0;t<50000;t+=1000)check(!p.observe(t,true,t,-1,t/10,0),"unknown video counters inhibit");
    p=new CobraRecoveryPolicy();for(int t=0;t<50000;t+=1000)check(!p.observe(t,true,t,t/20,-1,0),"unknown audio counters inhibit");
    p=new CobraRecoveryPolicy();for(int t=0;t<50000;t+=1000)check(!p.observe(t,true,t,t/20,t/10,100),"never-changing/unproven surface timestamps do not defeat healthy counters");
    p=new CobraRecoveryPolicy();p.observe(0,true,0,0,0,100);p.observe(1000,true,1000,50,100,200);
    for(int t=2000;t<=20000;t+=1000)p.observe(t,true,t,t/20,t/10,200);
    check(p.attempts==1&&p.state.equals("surface_timestamp_stalled"),"previously moving surface stalls despite decoded output");
    p=new CobraRecoveryPolicy();feed(p,0,15000,true,0,true,true,false);p.observe(16000,false,16000,0,1600,0);
    for(int t=17000;t<37000;t+=1000)check(!p.observe(t,true,t,0,t/10,0),"pause and resume grant new grace");
    check(p.observe(37000,true,37000,0,3700,0),"resume eventually observes real stall");
    p=new CobraRecoveryPolicy();feed(p,0,15000,true,0,true,true,false);check(!p.observe(70000,true,70000,0,7000,0),"long observer scheduling gap resets suspicion");
    check(!p.observe(69000,true,69000,0,6900,0),"monotonic reversal resets suspicion");
    p=new CobraRecoveryPolicy();feed(p,0,15000,true,1,true,true,true);check(!p.observe(16000,true,1000,0,0,0),"seek/counter replacement resets suspicion");
    p=new CobraRecoveryPolicy();feed(p,0,20000,true,0,true,true,false);feed(p,21000,120000,true,1,true,true,true);check(p.attempts==1,"resumed healthy frame output does not retry");
    check(CobraPreferencePolicy.language(" EN-us ").equals("en-us"),"normalized language");
    for(String value:new String[]{"", "und","password=value","https://provider/secret","a","en_uk","english","en-<secret>","en-123456789"})check(CobraPreferencePolicy.language(value).isEmpty(),"reject non-language data");
    check(CobraPreferencePolicy.scale(Float.NaN)==1f&&CobraPreferencePolicy.scale(Float.POSITIVE_INFINITY)==1f,"nonfinite scale safe");
    for(int i=-100;i<=300;i++){float value=CobraPreferencePolicy.scale(i/100f);check(value>=.55f&&value<=1.8f,"bounded scale");check(CobraPreferencePolicy.aspect(i)==(i>=-1&&i<=11?i:-1),"bounded aspect");}
    String a=CobraPreferencePolicy.key("profile","provider","123"),b=CobraPreferencePolicy.key("profile2","provider","123"),c=CobraPreferencePolicy.key("profile","provider2","123");
    check(!a.equals(b)&&!a.equals(c),"source and profile isolation");check(!CobraPreferencePolicy.key("a|b","c","d").equals(CobraPreferencePolicy.key("a","b|c","d")),"delimiter collision prevented");
    check(a.matches("cobra\\.channel\\.v1\\.[a-f0-9]{64}"),"full SHA256 preference namespace");
    check(CobraPreferencePolicy.choice("evil","on","off").equals("inherit"),"invalid policy inherits");
    System.out.println("PASS: "+count+" executed production policy assertions; no real provider/GPU test");
  }
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 before=a.baseline.read_text();after,receipt=patcher.patch(before);(a.out/'InfinityLiveActivity.java.in').write_text(after)
 tests=[]
 def check(ok,label):
  if not ok:raise AssertionError(label)
  tests.append(label)
 check(len(receipt['protected_methods'])>=370,'375 untargeted methods preserved (minimum guard)')
 x,y=patcher.span(after,'toggleCobraDrawer');drawer=after[x:y]
 check('for(String mode:CobraModeLayout.MODES)' not in drawer and 'cobraDrawerView(items)' in drawer,'Drawer modes hidden behind View action')
 x,y=patcher.span(after,'cobraDrawerView');d=after[x:y];check('showCobraViewModeMenu()' in d and 'stopCobraPreview' not in d and 'clearStage' not in d,'View/health entry does not dispose playback')
 x,y=patcher.span(after,'cobraReattachObservedSurface');recovery=after[x:y]
 for token in ('new ExoPlayer','setMediaItem','prepare(','release(','stop(','seekTo','startCobraPlayer','setVolume'):
  check(token not in recovery,'Surface recovery does not '+token)
 check('clearVideoTextureView(texture)' in recovery and 'setVideoTextureView(texture)' in recovery,'Existing player and exact texture only')
 check('setSurfaceTextureListener' not in after,'ExoPlayer surface callback ownership not replaced')
 x,y=patcher.span(after,'cobraObserveSessions');observe=after[x:y]
 for token in ('mCobraHealthForeground','mBackgroundStopped','isCobraInPictureInPicture','hasWindowFocus','isShown','isAvailable','getPlayerError','getPlaybackSuppressionReason','getAudioFormat','disabledTrackTypes','s.preferenceKey.equals'):
  check(token in observe,'Recovery observation eligibility includes '+token)
 check('cobraPermitBufferRetry(mPlayer)' in after and 'bufferRetries>=2' in after,'Existing buffering watchdog capped')
 check('player.removeAnalyticsListener(binding.vitals)' in after,'Observer disposal wired')
 check('cobraAddSessionHealth(root)' in after,'Health ZIP receives recovery/state observations')
 check('mPrefs.edit().clear()' not in (ROOT/'runtime.java.inc').read_text(),'No global data clearing in preferences')
 check('setVideoFrameMetadataListener' not in after,'No overwrite of another frame metadata listener')
 check('onCues(androidx.media3.common.text.CueGroup' in after and 'cobraAttachCaptions(binding,texture)' in after,'Subtitle selection has a real cue presentation path')
 for invalid in (before+'\n',before.replace('private final ExecutorService','private ExecutorService',1)):
  try:patcher.patch(invalid)
  except ValueError:check(True,'Unknown preimage rejected')
  else:raise AssertionError('Unknown baseline accepted')
 (a.out/'PolicyTest.java').write_text('import java.util.*;import java.nio.charset.StandardCharsets;public class PolicyTest {\n'+(ROOT/'policies.java.inc').read_text()+HARNESS+'\n}')
 subprocess.run(['javac','--release','8','-d',str(a.out/'classes'),str(a.out/'PolicyTest.java')],check=True)
 run=subprocess.run(['java','-cp',str(a.out/'classes'),'PolicyTest'],capture_output=True,text=True,check=True);print(run.stdout)
 (a.out/'results.json').write_text(json.dumps({'source':receipt,'integration_checks':tests,'policy_output':run.stdout,'physical_device_verified':False},indent=2)+'\n')
 print('PASS:',len(tests),'integration guards')
if __name__=='__main__':main()
