#!/usr/bin/env python3
"""Compile and execute production policy/geometry/grant classes; no copied model."""
from pathlib import Path
import argparse,importlib.util,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stability_patch',ROOT/'apply.py');patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
def require(v,label):
 if not v:raise AssertionError(label)
def extract(source,name):
 start=source.index('  static final class '+name+' {');return source[start:patch.end(source,start)]
JAVA=r'''
  static int assertions=0,cases=0;
  static void ok(boolean b){assertions++;if(!b)throw new AssertionError("assertion "+assertions+" case "+cases);}
  static CobraPlaybackPolicy fresh(){CobraPlaybackPolicy p=new CobraPlaybackPolicy();p.start();p.resume(false);return p;}
  static void scenario(Runnable r){cases++;r.run();}
  public static void main(String[] args){
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();p.pipChanged(true);ok(p.stop(true,true)==2);ok(p.dismissed);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();p.pipChanged(true);p.pipChanged(false);ok(p.stop(false,true)==2);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();p.pipChanged(true);ok(p.stop(false,true)==2);p.pipChanged(false);ok(p.dismissed);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();ok(p.stop(true,true)==2);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();p.pipChanged(true);p.pipChanged(false);p.resume(false);ok(!p.pipOwned);ok(p.stop(false,true)==1);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();p.pipChanged(true);p.resume(true);p.pipChanged(false);ok(!p.pipOwned);ok(p.stop(false,true)==1);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();ok(p.stop(false,true)==1);ok(!p.dismissed);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();ok(p.stop(false,false)==0);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.dismiss();ok(p.stop(false,true)==0);});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.pause();p.pipChanged(true);p.stop(true,false);ok(p.stop(false,true)==2);});
    scenario(()->{CobraPlaybackPolicy p=fresh();long e=p.epoch;ok(p.acceptsRetry(e,true,true));p.dismiss();ok(!p.acceptsRetry(e,true,true));});
    scenario(()->{CobraPlaybackPolicy p=fresh();ok(!p.acceptsRetry(p.epoch,false,true));ok(!p.acceptsRetry(p.epoch,true,false));});
    scenario(()->{CobraPlaybackPolicy p=fresh();long e=p.epoch;p.epoch++;ok(!p.acceptsRetry(e,true,true));});
    scenario(()->{CobraPlaybackPolicy p=fresh();p.dismiss();long e=p.epoch;p.dismiss();ok(p.epoch==e);p.resume(false);ok(p.acceptsRetry(e,true,true));});
    scenario(()->{CobraPlaybackPolicy p=fresh();for(int i=0;i<1000;i++){p.pause();p.pipChanged(true);p.resume(true);p.pipChanged(false);ok(!p.pipOwned);}});
    scenario(()->{MiniGrant g=new MiniGrant();ok(!g.accepts(0));long n=g.grant();ok(g.accepts(n));g.revoke();ok(!g.accepts(n));});
    scenario(()->{MiniGrant g=new MiniGrant();long old=g.grant(),now=g.grant();ok(!g.accepts(old));ok(g.accepts(now));});
    scenario(()->{MiniGrant g=new MiniGrant();long old=g.grant();g.revoke();long now=g.grant();ok(!g.accepts(old));ok(g.accepts(now));});
    scenario(()->{MiniGrant g=new MiniGrant();for(int i=0;i<1000;i++){long n=g.grant();g.revoke();ok(!g.accepts(n));}ok(!g.requested);});
    scenario(()->{int[] r=CobraSheetGeometry.place(new int[]{8,32,404,880},new int[]{24,160,388,380},new int[]{332,326,380,374},440,250,6);ok(r[0]==24&&r[2]==364&&r[1]==380);});
    scenario(()->{int[] r=CobraSheetGeometry.place(new int[]{8,8,1192,792},new int[]{652,60,1176,360},new int[]{1120,304,1168,352},440,310,6);ok(r[0]==728&&r[1]==358&&r[2]==440);});
    scenario(()->{int[] r=CobraSheetGeometry.place(new int[]{8,8,1192,792},new int[]{8,8,1192,792},new int[]{1010,722,1058,770},440,320,6);ok(r[1]==396&&r[0]==618);});
    scenario(()->{int[] r=CobraSheetGeometry.place(new int[]{24,80,326,502},new int[]{0,50,350,200},new int[]{310,120,348,168},440,900,6);ok(r[0]==24&&r[2]==302&&r[1]>=80&&r[1]+r[3]<=502);});
    scenario(()->{int[] r=CobraSheetGeometry.place(new int[]{0,0,40,30},new int[]{0,0,40,30},new int[]{10,5,25,20},440,500,6);ok(r[0]>=0&&r[1]==0&&r[3]==30);});
    scenario(()->{java.util.Random rnd=new java.util.Random(2103164);for(int i=0;i<20000;i++){
      int left=rnd.nextInt(100),top=rnd.nextInt(100),right=left+1+rnd.nextInt(2000),bottom=top+1+rnd.nextInt(1600);
      int pl=left-100+rnd.nextInt(right-left+200),pr=pl+1+rnd.nextInt(900);int[] pane={pl,top,pr,bottom};
      int al=left-100+rnd.nextInt(right-left+200),at=top-100+rnd.nextInt(bottom-top+200);int[] anchor={al,at,al+48,at+48};
      int[] r=CobraSheetGeometry.place(new int[]{left,top,right,bottom},pane,anchor,1+rnd.nextInt(600),1+rnd.nextInt(1500),6);
      ok(r[0]>=left&&r[1]>=top&&r[2]>0&&r[3]>0&&r[0]+r[2]<=right&&r[1]+r[3]<=bottom);
    }});
    System.out.println("{\"cases\":"+cases+",\"assertions\":"+assertions+",\"random_geometry_cases\":20000}");
  }
'''
def main(source,out):
 out.mkdir(parents=True,exist_ok=True);src=source/patch.SOURCE
 a=(src/'InfinityLiveActivity.java.in').read_text();s=(src/'InfinityExtendedBackgroundService.java.in').read_text()
 gate={
  'on_stop_does_not_trust_stale_pip': 'mCobraPlaybackPolicy.stop(' in a[patch.span(a,'onStop')[0]:patch.span(a,'onStop')[1]],
  'hidden_pip_closure_halts': 'cobraHaltHiddenPlayback();' in a[patch.span(a,'onPictureInPictureModeChanged')[0]:patch.span(a,'onPictureInPictureModeChanged')[1]],
  'on_pause_records_visibility':'mCobraPlaybackPolicy.pause();' in a,
  'mini_identity_bound':'player==mCobraMiniBackgroundPlayer&&player==mCobraPreviewPlayer' in a,
  'no_pending_service_start_after_resume':'revokeMini(false);InfinityExtendedBackgroundService service=sInstance.get();' in s,
  'no_media_start_from_stale_intent':'sMiniGrant.grant()' not in s[patch.span(s,'onStartCommand')[0]:patch.span(s,'onStartCommand')[1]],
  'native_controls_bound':all(x in s for x in ('onPlay(){dispatchMiniCommand','onPause(){dispatchMiniCommand','onStop(){dispatchMiniCommand')),
  'real_media_state':'int state=owner.state();' in s and '.setState(state,owner.position(),' in s,
  'mini_restore_same_activity':'new Intent(this,InfinityLiveActivity.class)' in s,
  'stale_commands_guarded':'command>COMMAND_STOP||!sMiniGrant.accepts(generation))return;' in s,
  'lifecycle_resume_preserved':'!mBackgroundStopped||reason!=Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST' in a,
  'buffering_retains_pip':'configureCobraPip(cobraPlaybackRequested(player))' in a,
  'retry_cancellation':'acceptsRetry(retryEpoch' in a and 'acceptsRetry(episodeEpoch' in a,
  'audible_player_owns_focus':'.setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(),audible)' in a,
  'preview_actual_anchor':'mCobraNextSheetAnchor=v;showCobraChannelActions' in a,
  'nested_anchor_preserved':'View source=mCobraSheetAnchor;closeCobraActionSheet();mCobraNextSheetAnchor=source;' in a,
  'window_local_geometry':'getLocationOnScreen' in a and 'getWindowVisibleDisplayFrame' in a,
  'layout_observer_cleaned':'removeOnGlobalLayoutListener(mCobraSheetLayoutListener)' in a,
  'no_centered_first_frame':'&&!panel.isLayoutRequested())panel.setAlpha(1f)' in a,
  'safe_sheet_scroll':'Math.min(limit,mCobraSheetHeightLimit)' in a,
  'stale_activity_cannot_revoke_replacement':'if(owner!=null&&sMiniOwner.get()==owner)stopMiniPlayback(context);' in s,
  'replacement_owner_pauses_old_session':'previous!=null&&previous!=owner)revokeMini(true)' in s,
  'service_teardown_pauses_owner':'mTerminating=true;sRunning=false;revokeMini(true);releaseMediaSession();' in s,
 }
 for label,passed in gate.items():require(passed,label)
 code='public class StabilityHost {\n'+extract(a,'CobraPlaybackPolicy')+'\n'+extract(a,'CobraSheetGeometry')+'\n'+extract(s,'MiniGrant')+'\n'+JAVA+'\n}\n'
 (out/'StabilityHost.java').write_text(code)
 subprocess.run(['javac','-encoding','UTF-8','-d',str(out),str(out/'StabilityHost.java')],check=True)
 result=subprocess.run(['java','-cp',str(out),'StabilityHost'],check=True,text=True,capture_output=True)
 report=json.loads(result.stdout);report.update(passed=True,source_wiring_checks=gate,production_classes_extracted=True,physical_device_verified=False)
 (out/'host-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.source,a.out)
