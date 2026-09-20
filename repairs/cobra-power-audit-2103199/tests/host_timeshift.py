from pathlib import Path
import argparse, importlib.util, subprocess, json, hashlib
spec=importlib.util.spec_from_file_location('source_tools',Path(__file__).resolve().parents[1]/'apply_timeshift.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def member(s,name):
 return mod.member(s,name)
def compile_run(source,out):
 s=source.read_text();out.mkdir(parents=True,exist_ok=True)
 ticker=s[s.index('  private final Runnable mCobraPresentationTick'):s.index('  private boolean mCobraPreviewAutoplayAllowed')]
 names=['cobraTimeshiftTimelineAvailable','cobraUpdateTimeshiftSeek','cobraCanRewindLive','cobraLiveWindowSeekable','cobraCanGoLive','cobraUpdateLiveRewindControls','cobraRecoverLocalTimeshiftSource','cobraActivateLocalTimeshift','cobraFallbackFromLocalTimeshift']
 methods='\n'.join(member(s,n) for n in names)
 # Execute the actual construction/reset statements with only the platform widget replaced.
 timeline_line=next(line for line in member(s,'cobraBuildPlayerChrome').splitlines() if 'mCobraTimeshiftSeek=new android.widget.SeekBar(this);' in line)
 timeline_construction=timeline_line.split('mCobraTimeshiftSeek.setTag(',1)[0].replace('new android.widget.SeekBar(this)','new Bar()')
 methods += '\n private void recreateTimelineControl(){'+timeline_construction+'}\n'
 j='''import java.util.*;
public class ActualTimeshiftHarness {
 static final class C {static final long TIME_UNSET=-9223372036854775807L;}
 static final class View {static final int GONE=8,VISIBLE=0;}
 static class Bar {int progress,visibility;void setProgress(int p){progress=p;}void setVisibility(int v){visibility=v;}}
 static class Button {boolean enabled;void setEnabled(boolean v){enabled=v;}void setAlpha(float v){}void setSelected(boolean v){}void setContentDescription(String v){}}
 static class Channel {String id="one",primaryUrl="https://example.invalid/one.ts";}
 static class ExoPlayer {long duration=120000,position=30000;boolean seekable=true,requested=true;int prepares=0,sets=0;boolean isCurrentMediaItemSeekable(){return seekable;}long getDuration(){return duration;}long getCurrentPosition(){return position;}boolean getPlayWhenReady(){return requested;}void setMediaItem(Object o){sets++;}void play(){requested=true;}void pause(){requested=false;}void seekTo(long p){position=p;} }
 static class CobraLocalTimeshiftSession {boolean ready(){return true;}String playlistUrl(){return "http://127.0.0.1/live.m3u8";}long latestSequence(){return 2;}boolean awaitSequenceAfter(long a,long b){return true;}String diagnostic(){return "safe";}long windowDurationMs(){return 120000;}}
 static class PlaybackException extends RuntimeException {}
 static final class CobraTimeshiftRecoveryPolicy {static final long ADVANCE_WAIT_MS=12000;static boolean recoverable(Object o){return true;}}
 static final class InfinityCobraDiagnostics {static void record(Object a,String b,String c,String d){}static void failure(Object a,String b,Object c){}}
 static class LiveSource {String id;}
 static class Features {boolean sourceEnabled(String id){return true;}}
 static class Adapter {void notifyDataSetChanged(){}}
 static class Main {void postDelayed(Runnable r,long delay){}}
 private ExoPlayer mPlayer=new ExoPlayer(),mCobraPreviewPlayer=null,mCobraTimeshiftPlayer=mPlayer,mCobraTimeshiftProxyPlayer=null;
 private Channel mPlaying=new Channel(),mGuidePreviewChannel=null;
 private CobraLocalTimeshiftSession mCobraTimeshiftSession=new CobraLocalTimeshiftSession();
 private boolean mCobraProviderCatchupActive=false,mCobraTimeshiftDragging=false;
 private long mCobraPendingLocalRewindMs=0;
 private int mCobraTimeshiftRecoveryGeneration=0,mCobraLastTickerMinute=0;
 private String mPlayingVodKey="",mCobraPreviewSessionKey="";
 private Bar mCobraTimeshiftSeek=new Bar(),mCobraPlayerProgramProgress=new Bar();
 private Button mCobraLiveRewindButton=new Button(),mCobraGoLiveButton=new Button();
 private List<LiveSource> mSources=new ArrayList<>();private Features mFeatures=new Features();private Adapter mCobraGuideAdapter=null;private Main mMain=new Main();
 private java.util.IdentityHashMap<ExoPlayer,Boolean> mBackgroundResumePlayers=new java.util.IdentityHashMap<>();
 private Runnable pendingIo,pendingUi;
 private boolean cobraLiveRewindEnabled(){return true;}private boolean cobraLiveChannel(Channel c){return c!=null;}private boolean cobraCanRestartCurrentProgram(){return false;}
 private boolean presentationActive=true;private boolean cobraGuidePresentationActive(){return presentationActive;}private void cobraRefreshProgrammeLabels(){}private void cobraInspectMultiHealth(){}private void cobraUpdatePerformanceOverlay(){}
 private void loadGuideAsync(LiveSource s){}private void cobraRequestShortEpg(Channel c){}
 private boolean submitCobraIo(Runnable r){pendingIo=r;return true;}private void publishCobraUi(Runnable r){pendingUi=r;}
 private void cobraSetTimeshiftUiState(String s,String d){}private Object mediaItem(String s){return s;}private void cobraPrepareObserved(ExoPlayer p,String s){p.prepares++;}private void startCobraPlayer(ExoPlayer p){p.play();}
 private void cobraStopLocalTimeshift(String reason){mCobraTimeshiftSession=null;mCobraTimeshiftPlayer=null;mCobraTimeshiftProxyPlayer=null;}
 private void releaseSinglePlayer(){mPlayer=null;}private void cobraDisposePlayer(ExoPlayer p){}
 private void cobraStartDirectSinglePlayer(Channel c,String url,String reason){cobraStartDirectSinglePlayer(c,url,reason,true);}
 private void cobraStartDirectSinglePlayer(Channel c,String url,String reason,boolean requested){mPlayer=new ExoPlayer();mPlayer.requested=requested;}
 private void cobraStartDirectPreview(Channel c,String reason){cobraStartDirectPreview(c,reason,true);}
 private void cobraStartDirectPreview(Channel c,String reason,boolean requested){mCobraPreviewPlayer=new ExoPlayer();mCobraPreviewPlayer.requested=requested;}
''' + ticker+methods+'''
 private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
 private static void test(String name,Runnable task){try{task.run();System.out.println("PASS "+name);}catch(Throwable t){failures++;System.out.println("FAIL "+name+": "+t.getMessage());}}
 private static int failures;
 public static void main(String[] args){
 test("timeline advances without playback-state event",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.cobraUpdateTimeshiftSeek();check(h.mCobraTimeshiftSeek.progress==250,"initial progress");h.mPlayer.position=60000;h.mCobraPresentationTick.run();check(h.mCobraTimeshiftSeek.progress==500,"timeline stayed at "+h.mCobraTimeshiftSeek.progress);});
 test("rewind re-enables after earliest boundary",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.mPlayer.position=0;h.cobraUpdateLiveRewindControls();check(!h.mCobraLiveRewindButton.enabled,"initial disabled");h.mPlayer.position=2000;h.mCobraPresentationTick.run();check(h.mCobraLiveRewindButton.enabled,"still disabled after two seconds");});
 test("drag preview not overwritten by runtime refresh",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.mCobraTimeshiftDragging=true;h.mCobraTimeshiftSeek.progress=750;h.mCobraPlayerProgramProgress.progress=750;h.cobraUpdateTimeshiftSeek();check(h.mCobraTimeshiftSeek.progress==750&&h.mCobraPlayerProgramProgress.progress==750,"drag progress was overwritten");});
 test("pause during source recovery stays paused",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();ExoPlayer player=h.mPlayer;h.cobraRecoverLocalTimeshiftSource(player,h.mPlaying,new PlaybackException());h.pendingIo.run();player.pause();h.pendingUi.run();check(!player.requested,"recovery resumed paused player");check(player.prepares==1,"recovery still prepares source");});
 test("playing source recovery continues playback",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();ExoPlayer player=h.mPlayer;h.cobraRecoverLocalTimeshiftSource(player,h.mPlaying,new PlaybackException());h.pendingIo.run();h.pendingUi.run();check(player.requested,"recovery lost play intent");});
 test("stale recovery cannot mutate replacement player",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();ExoPlayer old=h.mPlayer;h.cobraRecoverLocalTimeshiftSource(old,h.mPlaying,new PlaybackException());h.pendingIo.run();h.mPlayer=new ExoPlayer();h.mCobraTimeshiftPlayer=h.mPlayer;h.pendingUi.run();check(old.prepares==0,"stale player prepared");});
 test("rewind activation preserves paused state",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.mCobraTimeshiftProxyPlayer=h.mPlayer;h.mCobraTimeshiftPlayer=null;h.mPlayer.pause();check(h.cobraActivateLocalTimeshift(h.mPlayer,h.mPlaying,30000),"activation rejected");check(!h.mPlayer.requested,"rewind unpaused playback");});
 test("paused local fallback preserves paused state",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.mPlayer.pause();h.cobraFallbackFromLocalTimeshift(h.mPlayer,h.mPlaying,"test");check(!h.mPlayer.requested,"fallback unpaused playback");});
 test("preview paused fallback preserves paused state",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();ExoPlayer old=h.mPlayer;h.mPlayer=null;h.mPlaying=null;h.mCobraPreviewPlayer=old;h.mGuidePreviewChannel=new Channel();old.pause();h.cobraFallbackFromLocalTimeshift(old,h.mGuidePreviewChannel,"test");check(!h.mCobraPreviewPlayer.requested,"preview fallback unpaused playback");});
 test("background resume intent survives replacement",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();ExoPlayer old=h.mPlayer;old.pause();h.mBackgroundResumePlayers.put(old,Boolean.TRUE);h.cobraFallbackFromLocalTimeshift(old,h.mPlaying,"test");check(h.mPlayer.requested,"background resume request discarded");});
 test("inactive presentation does not update timeline",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.cobraUpdateTimeshiftSeek();h.presentationActive=false;h.mPlayer.position=60000;h.mCobraPresentationTick.run();check(h.mCobraTimeshiftSeek.progress==250,"inactive presentation updated");});
 test("unseekable duration cannot expose timeline",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.mPlayer.duration=C.TIME_UNSET;h.cobraUpdateTimeshiftSeek();check(h.mCobraTimeshiftSeek.visibility==View.GONE,"unset duration exposed timeline");h.mPlayer.duration=120000;h.mPlayer.seekable=false;h.cobraUpdateTimeshiftSeek();check(h.mCobraTimeshiftSeek.visibility==View.GONE,"unseekable media exposed timeline");});
 test("timeline clamps stale positions to available window",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.mPlayer.position=-2000;h.cobraUpdateTimeshiftSeek();check(h.mCobraTimeshiftSeek.progress==0,"negative thumb position");h.mPlayer.position=240000;h.cobraUpdateTimeshiftSeek();check(h.mCobraTimeshiftSeek.progress==1000,"thumb exceeded window");});
 test("recreated timeline does not retain old touch gesture",()->{ActualTimeshiftHarness h=new ActualTimeshiftHarness();h.mCobraTimeshiftDragging=true;h.recreateTimelineControl();check(!h.mCobraTimeshiftDragging,"old dragging flag survived control recreation");h.cobraUpdateTimeshiftSeek();check(h.mCobraTimeshiftSeek.progress==250,"new timeline never resumed clock sync");});
 System.out.println("TOTAL failures="+failures);System.exit(failures==0?0:1);
 }
}
'''
 (out/'ActualTimeshiftHarness.java').write_text(j)
 c=subprocess.run(['java','com.sun.tools.javac.Main',str(out/'ActualTimeshiftHarness.java')],capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 r=subprocess.run(['java','-cp',str(out),'ActualTimeshiftHarness'],capture_output=True,text=True)
 result={'source':str(source),'sha256':hashlib.sha256(s.encode()).hexdigest(),'kind':'host tests on actual extracted Java methods with fake UI/player/network collaborators; not Android or physical-device verification','exit_code':r.returncode,'output':r.stdout}
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raise SystemExit(compile_run(a.source,a.out)["exit_code"])
