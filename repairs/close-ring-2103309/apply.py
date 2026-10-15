#!/usr/bin/env python3
"""Add close-state presentation to the exact Android source retained by APK 3308."""
import argparse
import hashlib
import json
from pathlib import Path

PREFIX = 'tools/android/packaging/xbmc/src/'
PREIMAGES = {
    PREFIX+'InfinityExitCompletion.java.in': 'b569d56d868582d8c3ef8ac5a9a32aadb15cb48923dfd54917bda8a83184fa19',
    PREFIX+'InfinityGlassChooser.java.in': 'b7698cfa6c7b74b8250bea7633766bd077a9ba410e269c4353fa183f664f0019',
}
SOURCE_MAP = '0fc7d638fa95a20dde6f331923cdf694c1774cbb748d186bc04965a4532e69f1'

def sha(data): return hashlib.sha256(data).hexdigest()
def manifest(root): return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def once(text, old, new):
    assert text.count(old)==1, (old[:100], text.count(old))
    return text.replace(old,new,1)

def transform_exit(s):
    s=once(s, '  static final class Plan {', '''  // Keep the last close plan, not an Activity or a saved preference. A missing
  // Activity slot or elapsed timeout must never be presented as completed cleanup.
  private static volatile Plan observedClosePlan;
  private static final java.util.concurrent.atomic.AtomicLong planGeneration=new java.util.concurrent.atomic.AtomicLong();
  private static synchronized void observeClose(Plan plan) {
    Plan current=observedClosePlan;
    if(current==null || current.generation<=plan.generation) observedClosePlan=plan;
  }
  private static synchronized void forgetClose(Plan plan) {
    if(observedClosePlan==plan) observedClosePlan=null;
  }
  static Plan.Phase closePhase() {
    Plan plan=observedClosePlan;
    return plan==null ? Plan.Phase.RUNNING : plan.phase();
  }
  static final class Plan {
    private final long generation=planGeneration.incrementAndGet();''')
    s=once(s, 'requestedAt=SystemClock.elapsedRealtime();phase = Phase.WAITING_FOR_STOP; return true;',
        'requestedAt=SystemClock.elapsedRealtime();phase = Phase.WAITING_FOR_STOP; observeClose(this); return true;')
    s=once(s, '      phase = Phase.RUNNING; return true;',
        '      phase = Phase.RUNNING; forgetClose(this); return true;')
    s=once(s, '      phase = Phase.FORCED; return true;',
        '      phase = Phase.FORCED; observeClose(this); return true;')
    s=once(s, 'synchronized void destroying() { if (phase != Phase.FORCED) phase = Phase.DESTROYING; }',
        'synchronized void destroying() { if (phase != Phase.FORCED) phase = Phase.DESTROYING; observeClose(this); }')
    return s

def transform_gear(s):
    s=once(s, '    Gear(Context c,boolean light,boolean cobra){', '''    private final RectF closeArc=new RectF();
    private boolean closePending,progressPosted;
    private InfinityExitCompletion.Plan.Phase shownClosePhase=InfinityExitCompletion.Plan.Phase.RUNNING;
    private final Runnable closeTick=()->syncCloseProgress();
    private boolean closeVisible(){
      return !cobra && isAttachedToWindow() && getWindowVisibility()==VISIBLE && isShown();
    }
    private boolean closeMotion(){
      return android.os.Build.VERSION.SDK_INT<26 || android.animation.ValueAnimator.areAnimatorsEnabled();
    }
    private void syncCloseProgress(){
      removeCallbacks(closeTick);progressPosted=false;
      if(!closeVisible())return;
      InfinityExitCompletion.Plan.Phase phase=InfinityExitCompletion.closePhase();
      boolean pending=phase!=InfinityExitCompletion.Plan.Phase.RUNNING && phase!=InfinityExitCompletion.Plan.Phase.COMPLETE;
      if(phase!=shownClosePhase){
        boolean wasPending=closePending;shownClosePhase=phase;closePending=pending;
        setContentDescription(pending ? "Infinity is finishing its close. Settings and Health Center" :
            phase==InfinityExitCompletion.Plan.Phase.COMPLETE ? "Infinity is ready to reopen. Settings and Health Center" :
            "Infinity settings and Health Center");
        if(wasPending && phase==InfinityExitCompletion.Plan.Phase.COMPLETE)
          announceForAccessibility("Infinity is ready to reopen");
        invalidate();
      }
      if(closePending && hasWindowFocus() && closeMotion())invalidate();
      progressPosted=postDelayed(closeTick,closePending && hasWindowFocus() && closeMotion()?33:250);
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();if(!cobra)syncCloseProgress();}
    @Override protected void onDetachedFromWindow(){removeCallbacks(closeTick);progressPosted=false;super.onDetachedFromWindow();}
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);if(closeTick!=null && !cobra)syncCloseProgress();}
    @Override protected void onVisibilityChanged(View changed,int visibility){super.onVisibilityChanged(changed,visibility);if(closeTick!=null && !cobra)syncCloseProgress();}
    @Override public void onWindowFocusChanged(boolean focus){super.onWindowFocusChanged(focus);if(closeTick!=null && !cobra)syncCloseProgress();}
    Gear(Context c,boolean light,boolean cobra){''')
    s=once(s, '''      if(isFocused()||isPressed()){p.setColor(cobra?0xff4cddff:0xffffd077);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(3);c.drawCircle(cx,cy,s*.46f,p);}
    }
    @Override protected void drawableStateChanged()''', '''      if(isFocused()||isPressed()){p.setColor(cobra?0xff4cddff:0xffffd077);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(3);c.drawCircle(cx,cy,s*.46f,p);}
      if(!cobra && closePending){
        float radius=s*.46f,stroke=Math.min(s*.055f,px(getContext(),2.5f));
        p.setShader(null);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(stroke);p.setStrokeCap(Paint.Cap.ROUND);
        p.setColor(light?0x35249ce8:0x4546c4ff);c.drawCircle(cx,cy,radius,p);
        float start=closeMotion()?(SystemClock.uptimeMillis()%1600)*360f/1600-90:-90;
        closeArc.set(cx-radius,cy-radius,cx+radius,cy+radius);
        p.setColor(light?0xff079de8:0xff39caff);c.drawArc(closeArc,start,275,false,p);
        double end=Math.toRadians(start+275);p.setStyle(Paint.Style.FILL);p.setColor(light?0xffd9f7ff:0xffe9fcff);
        c.drawCircle(cx+(float)Math.cos(end)*radius,cy+(float)Math.sin(end)*radius,stroke*.48f,p);
        p.setStrokeCap(Paint.Cap.BUTT);
      }
    }
    @Override protected void drawableStateChanged()''')
    return s

def apply(source,out):
    before=manifest(source)
    assert len(before)==250 and sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==SOURCE_MAP, 'Wrong complete 3308 Android source'
    for name,h in PREIMAGES.items(): assert before[name]==h, name
    for name,func in [('InfinityExitCompletion',transform_exit),('InfinityGlassChooser',transform_gear)]:
        p=source/(PREFIX+name+'.java.in');p.write_text(func(p.read_text()))
    after=manifest(source)
    assert before.keys()==after.keys() and {n for n in before if before[n]!=after[n]}==set(PREIMAGES)
    out.mkdir(parents=True,exist_ok=True)
    (out/'SOURCE-PRESERVATION.json').write_text(json.dumps({'apk_parent':2103308,'android_source_parent':2103307,
        'before':before,'after':after,'changed':sorted(PREIMAGES),'unchanged_files':248,
        'native_changed':False,'skin_changed':False,'cobra_source_changed':False,'shutdown_policy_changed':False},indent=2)+'\n')
    print('PASS: only the close observer and Infinity gear presentation changed; 248 source files preserved.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.out)
