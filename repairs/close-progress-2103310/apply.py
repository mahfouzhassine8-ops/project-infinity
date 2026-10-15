#!/usr/bin/env python3
"""Replace the 3309 spinner with completed-stage progress; retain all shutdown policy."""
import argparse
import hashlib
import json
from pathlib import Path

PREFIX='tools/android/packaging/xbmc/src/'
PREIMAGES={PREFIX+'InfinityGlassChooser.java.in':'7f35c7e3713f0e2572bd9f42d7e26bfec7621a72e73c3fd01ba0cb242180ed32'}
SOURCE_MAP='3d5a6df8f27d261d99fb04bd69712bf0f33217843b4bd890b80242a49f08d36a'
def sha(data):return hashlib.sha256(data).hexdigest()
def manifest(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def once(s,old,new):
    assert s.count(old)==1,(old[:100],s.count(old));return s.replace(old,new,1)

PROGRESS='''    private final RectF closeArc=new RectF();
    private boolean closePending,closeReady,progressPosted;
    private float closeFromSweep,closeTargetSweep;
    private long closeSweepChangedAt;
    private InfinityExitCompletion.Plan.Phase shownClosePhase=InfinityExitCompletion.Plan.Phase.RUNNING;
    private final Runnable closeTick=()->syncCloseProgress();
    private boolean closeVisible(){
      return !cobra && isAttachedToWindow() && getWindowVisibility()==VISIBLE && isShown();
    }
    private boolean closeMotion(){
      return android.os.Build.VERSION.SDK_INT<26 || android.animation.ValueAnimator.areAnimatorsEnabled();
    }
    // These are completed milestones, not a prediction of remaining time/work.
    // Android stop -> shutdown handoff -> native destruction returned.
    static int completedCloseStages(InfinityExitCompletion.Plan.Phase phase){
      switch(phase){
        case QUIT_QUEUED:return 1;
        case DESTROYING:return 2;
        case COMPLETE:return 3;
        case FORCED:return -1; // A force request is not completed cleanup.
        default:return 0;
      }
    }
    private float displayedCloseSweep(long now){
      if(!closeMotion() || !hasWindowFocus())return closeTargetSweep;
      float elapsed=Math.max(0,Math.min(1,(now-closeSweepChangedAt)/180f));
      float eased=elapsed*elapsed*(3-2*elapsed);
      return closeFromSweep+(closeTargetSweep-closeFromSweep)*eased;
    }
    private void syncCloseProgress(){
      removeCallbacks(closeTick);progressPosted=false;
      if(!closeVisible())return;
      InfinityExitCompletion.Plan.Phase phase=InfinityExitCompletion.closePhase();
      boolean pending=phase!=InfinityExitCompletion.Plan.Phase.RUNNING && phase!=InfinityExitCompletion.Plan.Phase.COMPLETE;
      long now=SystemClock.uptimeMillis();
      if(phase!=shownClosePhase){
        boolean wasPending=closePending;
        float displayed=displayedCloseSweep(now);
        shownClosePhase=phase;closePending=pending;
        int stages=completedCloseStages(phase);
        if(phase==InfinityExitCompletion.Plan.Phase.RUNNING){
          closeReady=false;closeFromSweep=closeTargetSweep=0;
        }else if(phase==InfinityExitCompletion.Plan.Phase.COMPLETE){
          // A new chooser shown after an already completed close uses its normal
          // gear. A chooser that watched the close keeps the finished blue ring.
          closeReady=wasPending || closeReady;
          closeFromSweep=displayed;closeTargetSweep=closeReady?360:0;
        }else{
          if(!wasPending){displayed=0;closeTargetSweep=0;}
          closeReady=false;closeFromSweep=displayed;
          if(stages>=0)closeTargetSweep=stages*120f;
        }
        closeSweepChangedAt=now;
        setContentDescription(pending ? "Infinity is finishing its close. Settings and Health Center" :
            phase==InfinityExitCompletion.Plan.Phase.COMPLETE ? "Infinity is ready to reopen. Settings and Health Center" :
            "Infinity settings and Health Center");
        if(wasPending && phase==InfinityExitCompletion.Plan.Phase.COMPLETE)
          announceForAccessibility("Infinity is ready to reopen");
        invalidate();
      }
      boolean animate=hasWindowFocus() && closeMotion() &&
          (closePending || Math.abs(displayedCloseSweep(now)-closeTargetSweep)>.05f);
      if(animate)invalidate();
      progressPosted=postDelayed(closeTick,animate?33:250);
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();if(!cobra)syncCloseProgress();}
    @Override protected void onDetachedFromWindow(){removeCallbacks(closeTick);progressPosted=false;super.onDetachedFromWindow();}
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);if(closeTick!=null && !cobra)syncCloseProgress();}
    @Override protected void onVisibilityChanged(View changed,int visibility){super.onVisibilityChanged(changed,visibility);if(closeTick!=null && !cobra)syncCloseProgress();}
    @Override public void onWindowFocusChanged(boolean focus){super.onWindowFocusChanged(focus);if(closeTick!=null && !cobra)syncCloseProgress();}
'''

DRAW='''      if(!cobra && (closePending || closeReady)){
        float radius=s*.46f,stroke=Math.min(s*.055f,px(getContext(),2.5f));
        p.setShader(null);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(stroke);p.setStrokeCap(Paint.Cap.ROUND);
        p.setColor(light?0x35249ce8:0x4546c4ff);c.drawCircle(cx,cy,radius,p);
        float sweep=displayedCloseSweep(SystemClock.uptimeMillis());
        closeArc.set(cx-radius,cy-radius,cx+radius,cy+radius);
        p.setColor(light?0xff079de8:0xff39caff);
        if(sweep>0)c.drawArc(closeArc,-90,sweep,false,p);
        // A breathing tip stays at the completed-stage position; time alone
        // never fills the ring. At confirmed completion the full ring is still.
        if(closePending || sweep<359.95f){
          double end=Math.toRadians(-90+sweep);p.setStyle(Paint.Style.FILL);
          p.setColor(light?0xff079de8:0xff39caff);
          if(closePending && closeMotion())p.setAlpha(150+(int)(105*(.5+.5*Math.sin(SystemClock.uptimeMillis()*Math.PI/700))));
          c.drawCircle(cx+(float)Math.cos(end)*radius,cy+(float)Math.sin(end)*radius,stroke*.75f,p);
          p.setAlpha(255);
        }
        p.setStrokeCap(Paint.Cap.BUTT);
      }
'''

def transform(s):
    start=s.index('    private final RectF closeArc=new RectF();');end=s.index('    Gear(Context c,boolean light,boolean cobra){',start)
    s=s[:start]+PROGRESS+s[end:]
    start=s.index('      if(!cobra && closePending){');end=s.index('    }\n    @Override protected void drawableStateChanged()',start)
    return s[:start]+DRAW+s[end:]

def apply(source,out):
    before=manifest(source)
    assert len(before)==250 and sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==SOURCE_MAP,'Wrong complete 3309 source'
    for name,h in PREIMAGES.items():
        assert before[name]==h,name;p=source/name;p.write_text(transform(p.read_text()))
    after=manifest(source)
    assert before.keys()==after.keys() and {n for n in before if before[n]!=after[n]}==set(PREIMAGES)
    out.mkdir(parents=True,exist_ok=True)
    (out/'SOURCE-PRESERVATION.json').write_text(json.dumps({'apk_parent':2103309,'before':before,'after':after,
        'changed':sorted(PREIMAGES),'unchanged_files':249,'native_changed':False,'skin_changed':False,
        'cobra_source_changed':False,'shutdown_policy_changed':False},indent=2)+'\n')
    print('PASS: only the Infinity gear progress presentation changed; all 249 other source files preserved.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.out)
