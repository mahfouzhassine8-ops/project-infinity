#!/usr/bin/env python3
"""RC3 user-visible 2.5-second stall escalation, without unauthorized hard exit.

Reuses Infinity's approved chooser recovery dialog and Android foreground
notification. Notification tap is an explicit user action; background-service
launch restrictions mean it does not pop a new Activity automatically.
"""
from pathlib import Path
import hashlib
import json

ROOT=Path("tools/android/packaging/xbmc/src")
GUARD=str(ROOT/"InfinityCloseGuardService.java.in")
SPLASH=str(ROOT/"Splash.java.in")
PINS={
 GUARD:"fa53fecd9eb9436d3cd64b77f1e88ac83496cda606be75850cae79fe7c264459",
 SPLASH:"338a40fff74cd6d1e1f4a605a044c9c5df0a9b045dba0189f57c4c062c7f6aa3",
}
def sha(data): return hashlib.sha256(data).hexdigest()

def once(body,old,new,name):
    if body.count(old)!=1:raise RuntimeError("RC3 guarded Android anchor: "+name+" count="+str(body.count(old)))
    return body.replace(old,new,1)

def apply(root):
    root=Path(root)
    before={p:(root/p).read_bytes() for p in PINS}
    if any(sha(before[p])!=PINS[p] for p in PINS):
        raise RuntimeError("RC3 blocker UI needs exact preserved 274-test Android source")
    guard=before[GUARD].decode()
    splash=before[SPLASH].decode()
    guard=once(guard,
        '  private volatile String phase="IDLE",error="";',
        '''  private volatile String phase="IDLE",error="";
  private volatile boolean rc3RecoveryOffered=false;
  private String rc4LastMessage="";
  private static final long RC3_RECOVERY_GRACE_MS=6500L;''',
        "guard state")
    guard=once(guard,
        '      ui.post(poll);ui.postDelayed(this::deadline,',
        '      ui.post(poll);ui.postDelayed(this::offerRC3Recovery,RC3_RECOVERY_GRACE_MS);ui.postDelayed(this::deadline,',
        "grace scheduling")
    guard=once(guard,
        '''Intent open=new Intent(this,Splash.class).putExtra("infinity_checkpoint_chooser",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP);''',
        '''Intent open=new Intent(this,Splash.class).putExtra("infinity_checkpoint_chooser",true)
        .putExtra("infinity_close_recovery_hint",rc3RecoveryOffered)
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP);''',
        "recovery intent")
    guard=once(guard,
        '  private void deadline(){',
        '''  // A stalled, unverified writer is not permission to kill the engine.
  // Offer the existing recovery dialog through the notification's explicit
  // chooser tap. No lifecycle/Recents/termination authority changes.
  private void offerRC3Recovery(){
    // A 2.5s snapshot names healthy writers before their ordinary drain.
    // This advisory is not permission to bypass a required save receipt.
    if(ended||consumed||revoked||session==null||!inTime()||
       "COMPLETE".equals(phase)||"SAFE_TO_TERMINATE".equals(phase)||
       "ENGINE_TERMINATING".equals(phase)||"CHECKPOINT_FAILED".equals(phase))return;
    java.util.LinkedHashSet<String> names=new java.util.LinkedHashSet<>();
    int pendingCount=0;
    try{
      JSONObject status=new JSONObject(lastNativeJson);
      JSONObject scripts=status.optJSONObject("script_persistence");
      org.json.JSONArray pending=scripts!=null?scripts.optJSONArray("pending_writers"):null;
      if(pending!=null){
        for(int i=0;i<pending.length();i++){
          String name=pending.optString(i,"");
          if(name.isEmpty())continue;
          pendingCount++;
          if(name.startsWith("plugin.video.playlistbrowser:"))names.add("Playlist Browser");
          else if(name.startsWith("plugin.video.umbrella:"))names.add("Umbrella");
          else if(name.startsWith("repository.zeus768:"))names.add("Zeus768");
          else if(name.startsWith("script.trakt:"))names.add("Trakt");
          else if(name.startsWith("unidentified:infinity_continuity"))names.add("Infinity Continuity");
          else names.add("another add-on");
        }
      }
    }catch(Exception unavailable){/* Recheck next poll; never invent a pending owner. */}
    String noticeText;
    if(pendingCount==0){
      noticeText="Still closing: verifying saved data. Tap for options";
    }else{
      StringBuilder label=new StringBuilder();
      int visible=0;
      for(String name:names){
        if(visible==2)break;
        if(visible!=0)label.append(", ");
        label.append(name);
        visible++;
      }
      if(names.size()>2)label.append(" +").append(names.size()-2).append(" more");
      noticeText="Still closing: "+label+" ("+pendingCount+" pending). Tap for options";
    }
    rc3RecoveryOffered=true;
    InfinityCloseProgress.display=new InfinityCloseProgress.Display(
        session.pid,session.owner,session.started,phase,noticeText,false);
    try{((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).notify(NOTICE,notice(noticeText));}
    catch(RuntimeException unavailable){}
    if(!noticeText.equals(rc4LastMessage)){
      rc4LastMessage=noticeText;
      evidence("rc4.pending_service_notice_refresh",phase,noticeText);
    }
    // Keep the named blocker current as services retire. No termination action.
    ui.postDelayed(this::offerRC3Recovery,1000L);
  }
  private void deadline(){''',
        "non-killing recovery offer")
    splash=once(splash,
        '''  private void showInfinityClosingRecovery(){
    InfinityKodiShutdown.Snapshot owner=InfinityKodiShutdown.state();
    if(!owner.stalled())return;''',
        '''  private void showInfinityClosingRecovery(){showInfinityClosingRecovery(false);}
  private boolean infinityRC3RecoveryEligible(InfinityKodiShutdown.Snapshot owner){
    return owner.pending()&&owner.closeAt>0&&
        System.currentTimeMillis()-owner.closeAt>=6500L;
  }
  private void showInfinityClosingRecovery(boolean afterGraceNotice){
    InfinityKodiShutdown.Snapshot owner=InfinityKodiShutdown.state();
    if(!owner.stalled()&&!(afterGraceNotice&&infinityRC3RecoveryEligible(owner)))return;''',
        "existing choice dialog")
    splash=once(splash,
        '''if(current.pid==owner.pid&&current.owner.equals(owner.owner)&&current.stalled())''',
        '''if(current.pid==owner.pid&&current.owner.equals(owner.owner)&&
         (current.stalled()||(afterGraceNotice&&infinityRC3RecoveryEligible(current))))''',
        "explicit force choice ownership")
    splash=once(splash,
        '''      mInfinitySawClosing=true;showInfinityExperienceChooser();return;
    }
    if (infinityLaunchPreferredCobra())''',
        '''      mInfinitySawClosing=true;showInfinityExperienceChooser();
      if (getIntent().getBooleanExtra("infinity_close_recovery_hint",false))
        showInfinityClosingRecovery(true);
      return;
    }
    if (infinityLaunchPreferredCobra())''',
        "initial notification recovery")
    splash=once(splash,
        '''if(intent!=null && intent.getBooleanExtra("infinity_checkpoint_chooser",false)){mInfinitySawClosing=true;showInfinityExperienceChooser();return;}''',
        '''if(intent!=null && intent.getBooleanExtra("infinity_checkpoint_chooser",false)){
      mInfinitySawClosing=true;showInfinityExperienceChooser();
      if(intent.getBooleanExtra("infinity_close_recovery_hint",false))
        showInfinityClosingRecovery(true);
      return;}''',
        "new-intent recovery")
    out={GUARD:guard.encode(),SPLASH:splash.encode()}
    for p,data in out.items():(root/p).write_bytes(data)
    return {"before":PINS,"after":{p:sha(data) for p,data in out.items()},"changed":sorted(out),
       "no_force_exit_without_explicit_user":True,
       "no_native_checkpoint_authority_change":True,
       "no_recents_navigation_changes":True,
       "recovery_grace_ms":6500,
       "ui_kind":"Existing chooser recovery dialog surfaced from notification tap",
       "no_claim_of_automatic_dialog_from_background_service":True}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    result=apply(a.source)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
