package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Instrumentation;
import android.app.PictureInPictureParams;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.os.SystemClock;
import android.util.Rational;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BooleanSupplier;
import java.util.function.Supplier;
import org.json.JSONArray;
import org.json.JSONObject;

/** Injects real Android window input from the instrumentation thread, never private consume(). */
public final class InfinityLockProbeInstrumentation extends Instrumentation {
  private InfinityLockProbeActivity a;
  private final JSONArray checks = new JSONArray();
  private final JSONArray notRun = new JSONArray();
  private String runId;
  private String expectedTheme;
  private String selection;
  private final JSONArray pipWindows = new JSONArray();
  private String phase = "startup", lastInput = "none";
  private long downTime;
  private float x,y;

  @Override public void onCreate(Bundle args) {
    super.onCreate(args);runId=args==null?"missing":args.getString("runId","missing");
    expectedTheme=args==null?"missing":args.getString("expectedTheme","missing");
    selection=args==null?"missing":args.getString("selection","missing");start();
  }
  private <T> T ui(Supplier<T> query) {
    AtomicReference<T> result=new AtomicReference<>();runOnMainSync(()->result.set(query.get()));return result.get();
  }
  private void action(Runnable action) { runOnMainSync(action); }
  private void require(boolean value,String label) {
    if(!value)throw new AssertionError(label);checks.put(label);
  }
  private void waitFor(BooleanSupplier condition,String label) {
    long deadline=SystemClock.uptimeMillis()+8000;
    while(SystemClock.uptimeMillis()<deadline){if(ui(condition::getAsBoolean))return;SystemClock.sleep(20);}
    throw new AssertionError("Deadline: "+label);
  }
  private void begin() {
    int previous=ui(()->a.readyCount);action(a::begin);
    waitFor(()->a.readyCount>previous&&a.dialogFocused(),"focused READY");
    require(ui(a::geometryMatches),"Exact top-left viewport geometry");
  }
  private void inject(int action,float px,float py) {
    long eventTime=SystemClock.uptimeMillis();
    MotionEvent event=MotionEvent.obtain(downTime,eventTime,action,px,py,0);
    event.setSource(InputDevice.SOURCE_TOUCHSCREEN);
    try{pointer(event);}finally{event.recycle();}
  }
  private void pointer(MotionEvent event) {
    lastInput="touch action="+event.getAction()+" pointers="+event.getPointerCount()+
        " x="+event.getX()+" y="+event.getY()+" downTime="+event.getDownTime()+
        " eventTime="+event.getEventTime()+" history="+event.getHistorySize();
    sendPointerSync(event);
  }
  private void key(int code) {
    lastInput="key code="+code;sendKeyDownUpSync(code);
  }
  private void down() {
    require(ui(a::dialogFocused),"Dialog focus present before hold DOWN");
    float[] target=ui(a::target);x=(target[0]+target[2])/2;y=(target[1]+target[3])/2;
    downTime=SystemClock.uptimeMillis();inject(MotionEvent.ACTION_DOWN,x,y);
    waitFor(a::holding,"actual Dialog received hold DOWN");
  }
  private void up() { inject(MotionEvent.ACTION_UP,x,y); }
  private void secondPointer() {
    MotionEvent.PointerProperties[] p={new MotionEvent.PointerProperties(),new MotionEvent.PointerProperties()};
    MotionEvent.PointerCoords[] c={new MotionEvent.PointerCoords(),new MotionEvent.PointerCoords()};
    for(int i=0;i<2;i++){p[i].id=i;p[i].toolType=MotionEvent.TOOL_TYPE_FINGER;c[i].x=x+i;c[i].y=y;c[i].pressure=1;c[i].size=1;}
    MotionEvent event=MotionEvent.obtain(downTime,SystemClock.uptimeMillis(),
        MotionEvent.ACTION_POINTER_DOWN|(1<<MotionEvent.ACTION_POINTER_INDEX_SHIFT),2,p,c,0,0,1,1,0,0,InputDevice.SOURCE_TOUCHSCREEN,0);
    try{pointer(event);}finally{event.recycle();}
    // Prove the second contact cancels the hold before cleanup can cancel it.
    require(ui(()->!a.holding()&&a.locked()),"Actual second pointer cancels hold before cleanup");
    event=MotionEvent.obtain(downTime,SystemClock.uptimeMillis(),
        MotionEvent.ACTION_POINTER_UP|(1<<MotionEvent.ACTION_POINTER_INDEX_SHIFT),2,p,c,0,0,1,1,0,0,InputDevice.SOURCE_TOUCHSCREEN,0);
    try{pointer(event);}finally{event.recycle();}
    up();
  }
  private void noRequestAfter(Runnable gesture,String label) {
    phase=label;
    int previous=ui(()->a.requestCount);gesture.run();SystemClock.sleep(2150);
    require(ui(()->a.locked()&&a.requestCount==previous),label);
  }
  private void holdComplete() {
    phase="continuous hold";
    int previous=ui(()->a.requestCount);down();
    waitFor(()->a.requestCount>previous,"continuous two-second request");
    require(ui(()->a.requestAt-downTime>=2000&&a.locked()),"Two-second hold requests without dismissing lock");
    inject(MotionEvent.ACTION_MOVE,x+.25f,y+.25f);up();
    require(ui(()->a.lock.canConfirmUnlocked(a.session,a.requestEpoch,a.request)),"Completed hold survives ordinary MOVE and UP");
  }
  private void confirmFixture() {
    require(ui(()->a.lock.confirmUnlocked(a.session,a.requestEpoch,a.request)),"Matching explicit Host restoration fixture confirms");
    waitFor(()->!a.locked()&&!a.dialogFocused(),"confirmed Dialog dismissal");
  }
  private void shell(String command) throws Exception {
    try(ParcelFileDescriptor fd=getUiAutomation().executeShellCommand(command);
        java.io.InputStream input=new ParcelFileDescriptor.AutoCloseInputStream(fd)) {
      byte[] buffer=new byte[256];while(input.read(buffer)!=-1){}
    }
  }
  private void foreground() {
    action(()->a.startActivity(new Intent(a,InfinityLockProbeActivity.class)
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)));
    waitFor(()->!a.isInPictureInPictureMode()&&a.dialogFocused(),"foreground lock return");
  }
  private void returnFromPiP() throws Exception {
    phase="PiP system expansion";
    int exited=ui(()->a.pipExitedCallbacks),task=ui(a::getTaskId);
    AccessibilityServiceInfo info=getUiAutomation().getServiceInfo();
    int originalFlags=info.flags;
    boolean expanded=false;
    try {
      info.flags|=AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
      getUiAutomation().setServiceInfo(info);
      long deadline=SystemClock.uptimeMillis()+8000;
      while(!expanded&&SystemClock.uptimeMillis()<deadline) {
        java.util.List<AccessibilityWindowInfo> windows=getUiAutomation().getWindows();
        try {
          for(AccessibilityWindowInfo window:windows) {
            if(!window.isInPictureInPictureMode())continue;
            AccessibilityNodeInfo root=window.getRoot();
            if(root==null)continue;
            try {
              android.graphics.Rect bounds=new android.graphics.Rect();window.getBoundsInScreen(bounds);
              boolean owned="com.projectinfinity.lockqa".contentEquals(root.getPackageName()==null?"":root.getPackageName());
              boolean expandable=root.getActionList().contains(AccessibilityNodeInfo.AccessibilityAction.ACTION_EXPAND);
              if(pipWindows.length()<8)pipWindows.put(new JSONObject().put("window",window.getId())
                  .put("owned",owned).put("visible",root.isVisibleToUser()).put("bounds",bounds.toShortString()).put("expandable",expandable));
              if(owned&&root.isVisibleToUser()&&!bounds.isEmpty()&&expandable) {
                require(ui(()->a.getTaskId()==task&&a.isInPictureInPictureMode()),"Expansion targets the same live owner task");
                require(root.performAction(AccessibilityNodeInfo.ACTION_EXPAND),"System PiP ACTION_EXPAND accepted for exact probe");
                expanded=true;break;
              }
            } finally {root.recycle();}
          }
        } finally {for(AccessibilityWindowInfo window:windows)window.recycle();}
        if(!expanded)SystemClock.sleep(20);
      }
      require(expanded,"Exact visible probe PiP window exposes supported expansion");
    } finally {
      info.flags=originalFlags;getUiAutomation().setServiceInfo(info);
    }
    phase="PiP return READY";
    waitFor(()->a.getTaskId()==task&&a.pipExitedCallbacks>exited&&
        !a.isInPictureInPictureMode()&&a.dialogFocused(),"actual PiP exit callback and foreground lock return");
  }
  private void rotate(int orientation) {
    phase="rotation "+orientation;
    long epoch=ui(()->a.readyEpoch);
    action(()->a.setRequestedOrientation(orientation));
    int configuration=orientation==ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE?
        Configuration.ORIENTATION_LANDSCAPE:Configuration.ORIENTATION_PORTRAIT;
    waitFor(()->a.getResources().getConfiguration().orientation==configuration&&a.readyEpoch>epoch&&a.dialogFocused(),"rotation reflow READY");
    require(ui(()->a.locked()&&a.geometryMatches()),"Rotation preserves lock and exact position");
  }

  @Override public void onStart() {
    boolean pass=false;String error="",stack="";
    try {
      require("full".equals(selection)||"pip_tail".equals(selection),"Explicit valid component selection");
      a=(InfinityLockProbeActivity)startActivitySync(new Intent(getTargetContext(),InfinityLockProbeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      waitFor(()->a.underlay.getWidth()>0&&a.hasWindowFocus(),"owner layout");
      action(()->a.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT));
      waitFor(()->a.getResources().getConfiguration().orientation==Configuration.ORIENTATION_PORTRAIT,"portrait entry");
      begin();int touches=ui(()->a.touches),keys=ui(()->a.keys),heartbeat=ui(()->a.heartbeat);
      require(("light".equals(expectedTheme)||"dark".equals(expectedTheme))&&
          ui(()->a.paletteMatches("light".equals(expectedTheme))),"Selected system night mode and actual Dialog palette match Host fixture");
      float[] outside=ui(()->{int[]p=new int[2];a.underlay.getLocationOnScreen(p);return new float[]{p[0]+a.underlay.getWidth()/2f,p[1]+a.underlay.getHeight()/2f};});
      if ("full".equals(selection)) {
        phase="initial underlay input blocking";
        downTime=SystemClock.uptimeMillis();inject(MotionEvent.ACTION_DOWN,outside[0],outside[1]);
        inject(MotionEvent.ACTION_MOVE,outside[0]+60,outside[1]);inject(MotionEvent.ACTION_UP,outside[0]+60,outside[1]);
        key(KeyEvent.KEYCODE_DPAD_RIGHT);key(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE);
        key(KeyEvent.KEYCODE_BACK);key(KeyEvent.KEYCODE_BACK);
        require(ui(()->a.locked()&&a.touches==touches&&a.keys==keys&&a.requestCount==0),"Separate Dialog window blocks underlay touch/key/Back routing");
        noRequestAfter(()->{down();SystemClock.sleep(250);up();},"Early UP stays locked");
        noRequestAfter(()->{down();SystemClock.sleep(250);inject(MotionEvent.ACTION_MOVE,outside[0],outside[1]);inject(MotionEvent.ACTION_MOVE,x,y);up();},"Outside movement and reentry cancel hold");
        noRequestAfter(()->{down();SystemClock.sleep(250);inject(MotionEvent.ACTION_CANCEL,x,y);},"ACTION_CANCEL stays locked");
        noRequestAfter(()->{down();SystemClock.sleep(250);
          MotionEvent event=MotionEvent.obtain(downTime,SystemClock.uptimeMillis(),MotionEvent.ACTION_MOVE,outside[0],outside[1],0);
          event.setSource(InputDevice.SOURCE_TOUCHSCREEN);event.addBatch(SystemClock.uptimeMillis()+1,x,y,1,1,0);
          try{pointer(event);}finally{event.recycle();}up();},"Batched movement leaving and reentering cancels hold");
        noRequestAfter(()->{down();SystemClock.sleep(250);secondPointer();},"Second pointer cancels hold");
        noRequestAfter(()->{down();SystemClock.sleep(250);key(KeyEvent.KEYCODE_BACK);up();},"Back cancels partial hold without dismissing");
        holdComplete();long oldEpoch=ui(()->a.requestEpoch),oldRequest=ui(()->a.request),oldSession=ui(()->a.session);
        int revoked=ui(()->a.revokeCount);action(a::showFocusFixture);
        waitFor(()->a.revokeCount>revoked&&!a.dialogFocused(),"focus revocation");
        action(a::closeFocusFixture);waitFor(()->a.dialogFocused()&&a.readyEpoch>oldEpoch,"new focused epoch");
        require(ui(()->a.locked()&&a.revokeConfirmRejected&&!a.lock.confirmUnlocked(oldSession,oldEpoch,oldRequest)),"Focus revoke rejects reentrant and stale restoration acknowledgement");
        holdComplete();require(ui(()->!a.lock.confirmUnlocked(oldSession,oldEpoch,oldRequest)),"Old acknowledgement cannot release a fresh hold");
        confirmFixture();begin();
        int beforeRotation=ui(()->a.requestCount);down();SystemClock.sleep(250);
        rotate(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);inject(MotionEvent.ACTION_CANCEL,x,y);
        rotate(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        for(int cycle=1;cycle<5;cycle++){rotate(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);rotate(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);}
        require(ui(()->a.requestCount==beforeRotation&&a.locked()),"Five rotation cycles never unlock or finish interrupted hold");
        long beforeHome=ui(()->a.readyEpoch);shell("input keyevent KEYCODE_HOME");
        waitFor(()->!a.dialogFocused(),"OS Home remains available");foreground();
        require(ui(()->a.locked()&&a.readyEpoch>beforeHome),"Home/background return retains lock with fresh readiness");
      } else notRun.put("Input/hold/focus/rotation/Home prefix retained from run43837801524; not repeated");
      if(a.getPackageManager().hasSystemFeature(PackageManager.FEATURE_PICTURE_IN_PICTURE)) {
        phase="PiP enter settle";
        int callbacks=ui(()->a.pipEnteredCallbacks), frames=ui(()->a.pipDraws);
        int initialWidth=ui(()->a.underlay.getWidth()), initialHeight=ui(()->a.underlay.getHeight());
        int requests=ui(()->a.requestCount);long epoch=ui(()->a.readyEpoch);down();SystemClock.sleep(250);
        require(ui(()->a.enterPictureInPictureMode(new PictureInPictureParams.Builder().setAspectRatio(new Rational(16,9)).build())),"Platform accepted actual PiP entry");
        waitFor(()->a.isInPictureInPictureMode()&&!a.dialogFocused()&&
            a.pipEnteredCallbacks>callbacks&&a.pipDraws>frames&&
            a.pipDrawWidth>0&&a.pipDrawWidth<initialWidth&&
            a.pipDrawHeight>0&&a.pipDrawHeight<initialHeight&&
            a.underlay.isShown()&&a.underlay.getWindowVisibility()==android.view.View.VISIBLE,
            "exact owner PiP callback and visible resized frame");
        require(ui(()->a.locked()&&!a.holding()),"Completed PiP entry cancels hold and retains owner");
        returnFromPiP();require(ui(()->a.locked()&&a.readyEpoch>epoch&&a.requestCount==requests),"Actual PiP cancels hold and retains lock on return");
      } else {
        require(!"pip_tail".equals(selection),"Selected PiP test requires advertised support");
        notRun.put("PiP: emulator does not advertise feature");
      }
      phase="remaining Back, reentrant readiness and retirement";
      int nav=getTargetContext().getResources().getIdentifier("config_navBarInteractionMode","integer","android");
      if(nav!=0&&getTargetContext().getResources().getInteger(nav)==2) {
        int screenY=Math.round(outside[1]);shell("input swipe 1 "+screenY+" 250 "+screenY+" 300");
        require(ui(()->a.locked()&&a.dialogFocused()),"Attempted edge swipe under gestural navigation retains locked input window");
      } else notRun.put("System Back gesture: emulator navigation mode is not gestural; "+
          ("pip_tail".equals(selection)?"Back-key evidence retained from attempt6":"Back keys tested"));
      int readyBefore=ui(()->a.readyCount),revokeBefore=ui(()->a.revokeCount);
      action(()->{a.lock.playbackStopped(a.session);a.reenterReady=true;a.begin();});
      waitFor(()->a.readyCount>readyBefore&&a.revokeCount>revokeBefore&&a.locked()&&!a.dialogFocused(),"reentrant READY revocation");
      action(()->{a.lock.setForeground(true);a.updateViewport();});waitFor(a::dialogFocused,"reentrant recovery");
      require(ui(a::locked),"Synchronous Host READY revocation does not unlock or strand subsequent readiness");
      action(()->a.lock.playbackStopped(a.session-1));require(ui(a::locked),"Stale session stop cannot retire owner");
      require(ui(()->a.heartbeat>heartbeat&&a.touches==touches&&a.keys==keys),"Main Looper advanced and locked events never reached underlay");
      require(ui(()->a.paletteMatches("light".equals(expectedTheme))),"Selected Dialog palette retained through lifecycle checks");
      holdComplete();confirmFixture();begin();int retired=ui(()->a.retiredCount);action(a::finish);
      waitFor(()->!a.alive,"actual owner destruction");require(ui(()->a.retiredCount==retired+1),"Owner destruction retires once");
      pass=true;
    } catch(Throwable failure) {
      error=failure.getClass().getSimpleName()+": "+failure.getMessage();
      java.io.StringWriter detail=new java.io.StringWriter();
      failure.printStackTrace(new java.io.PrintWriter(detail));stack=detail.toString();
      try {
        android.graphics.Bitmap screenshot=getUiAutomation().takeScreenshot();
        if(screenshot!=null)try(java.io.OutputStream out=getTargetContext().openFileOutput("lock-failure-"+runId+".png",0)) {
          screenshot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);screenshot.recycle();
        }
        try(ParcelFileDescriptor fd=getUiAutomation().executeShellCommand("dumpsys window windows");
            java.io.InputStream input=new ParcelFileDescriptor.AutoCloseInputStream(fd);
            java.io.OutputStream out=getTargetContext().openFileOutput("lock-failure-"+runId+"-window.txt",0)) {
          byte[] buffer=new byte[4096];int count;while((count=input.read(buffer))!=-1)out.write(buffer,0,count);
        }
      } catch(Throwable captureFailure) { stack+="\nFailure capture unavailable: "+captureFailure.getClass().getSimpleName(); }
    }
    try {
      notRun.put("BadToken/window-show fault injection; explicit callback path compiled, not Android-fault-injected here");
      JSONObject result=new JSONObject().put("pass",pass).put("runId",runId).put("error",error)
          .put("selection",selection).put("retained_prefix_run", "pip_tail".equals(selection)?43837801524L:0L)
          .put("phase",phase).put("last_input",lastInput).put("failure_stack",stack).put("pip_windows",pipWindows)
          .put("API",android.os.Build.VERSION.SDK_INT).put("checks",checks).put("not_run",notRun)
          .put("palette",expectedTheme).put("native_skin_theme_resolution","NOT_INCLUDED")
          .put("scope","Actual unchanged State/Dialog with Android window-injected input; Host ACK is explicit test fixture")
          .put("native_bridge","NOT_INCLUDED").put("Kodi_playback","NOT_RUN").put("physical_Fold","NOT_RUN")
          .put("Infinity_shutdown","NOT_RUN").put("owner_installer",false);
      if(a!=null)result.put("events",ui(()->a.events)).put("geometry",ui(a::geometryEvidence));
      Bundle report=new Bundle();report.putString("lock_result",result.toString());
      finish(pass?Activity.RESULT_OK:Activity.RESULT_CANCELED,report);
    } catch(Exception failure) { Bundle report=new Bundle();report.putString("stream","Probe receipt failed: "+failure.getClass().getSimpleName());finish(Activity.RESULT_CANCELED,report); }
  }
}
