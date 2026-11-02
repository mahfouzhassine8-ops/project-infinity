package com.projectinfinity.kodi;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.graphics.*;
import android.media.AudioManager;
import android.net.Uri;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowAlertDialog;
import org.robolectric.util.ReflectionHelpers;
import static org.robolectric.Shadows.shadowOf;
import static org.robolectric.util.ReflectionHelpers.ClassParameter.from;
import static org.junit.Assert.*;

/** Actual production Activity/view rendering; decoder terminal spy, not decoding evidence. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk=35,qualifiers="w614dp-h640dp-320dpi",
        shadows=PreviewChromeTest.Decoder.class,instrumentedPackages={"com.projectinfinity.kodi"})
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class PreviewChromeTest {
    @Implements(InfinityExternalEngine.class)
    public static class Decoder {
        static Decoder last;
        InfinityExternalEngine.Observer observer;
        int opens,plays,pauses,seeks;long lastSeek;float volume=1;boolean destroyed,choice;
        @Implementation protected void __constructor__(Context c,InfinityExternalEngine.Observer o){last=this;observer=o;}
        @Implementation protected void open(Intent i,long p,boolean offer){opens++;}
        @Implementation protected void surface(Surface s){}
        @Implementation protected void play(){plays++;observer.event("playing","");}
        @Implementation protected void pause(){pauses++;observer.event("paused","");}
        @Implementation protected void suspend(){}
        @Implementation protected void destroy(){destroyed=true;}
        @Implementation protected void volume(float v){volume=v;}
        @Implementation protected void seek(int p){seeks++;lastSeek=p;}
        @Implementation protected void chooseResume(boolean restore){choice=restore;observer.event("resume_ready","");}
        @Implementation protected void listTracks(boolean caption){observer.tracks(new String[0],new int[0],-1,caption);}
        @Implementation protected void selectTrack(int index,boolean caption){}
    }
    ActivityController<InfinityExternalPlayerActivity> controller;
    InfinityExternalPlayerActivity a;FrameLayout root;AudioManager audio;
    static <T>T get(Object o,String field){return ReflectionHelpers.getField(o,field);}
    static void call(Object o,String method){ReflectionHelpers.callInstanceMethod(o,method);}
    void create(int mode,boolean focusGranted){
        Context app=RuntimeEnvironment.getApplication();app.getSharedPreferences("infinity_preview_ui",0).edit().clear().commit();
        audio=(AudioManager)app.getSystemService(Context.AUDIO_SERVICE);audio.setMode(mode);
        shadowOf(audio).setNextFocusRequestResponse(focusGranted?AudioManager.AUDIOFOCUS_REQUEST_GRANTED:AudioManager.AUDIOFOCUS_REQUEST_FAILED);
        Intent i=new Intent(Intent.ACTION_VIEW,Uri.parse("content://qa.private/sample-500mb.mp4")).putExtra("infinity.external.request","fixture-1");
        controller=Robolectric.buildActivity(InfinityExternalPlayerActivity.class,i);a=controller.get();
        a.setTheme(android.R.style.Theme_Material_NoActionBar);controller.create().start().resume().visible();root=get(a,"root");
        measure();a.position(0,300000);a.size(1920,1080);a.event("ready","");measure();
    }
    void measure(){
        int w=a.getResources().getDisplayMetrics().widthPixels,h=a.getResources().getDisplayMetrics().heightPixels;
        for(int i=0;i<3;i++){root.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));root.layout(0,0,w,h);}
    }
    Button find(View v,String text){
        if(v instanceof Button && ((Button)v).getText().toString().equals(text))return (Button)v;
        if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){Button b=find(((ViewGroup)v).getChildAt(i),text);if(b!=null)return b;}
        return null;
    }
    void press(String label){
        Button b=find(root,label);assertNotNull(label,b);View parent=b;
        while(parent.getParent() instanceof View){parent=(View)parent.getParent();if(parent instanceof HorizontalScrollView){((HorizontalScrollView)parent).scrollTo(Math.max(0,b.getLeft()-20),0);break;}}
        measure();Rect r=new Rect();assertTrue(label,b.getGlobalVisibleRect(r));assertTrue("48dp touch height",b.getHeight()>=a.getResources().getDisplayMetrics().density*48);
        int[] origin=new int[2];root.getLocationOnScreen(origin);long now=SystemClock.uptimeMillis();
        MotionEvent down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,r.exactCenterX()-origin[0],r.exactCenterY()-origin[1],0);
        MotionEvent up=MotionEvent.obtain(now,now+30,MotionEvent.ACTION_UP,r.exactCenterX()-origin[0],r.exactCenterY()-origin[1],0);
        assertTrue(root.dispatchTouchEvent(down));assertTrue(root.dispatchTouchEvent(up));down.recycle();up.recycle();shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(100));
    }
    void mode(int value){audio.setMode(value);shadowOf(Looper.getMainLooper()).idle();ReflectionHelpers.callInstanceMethod(a,"syncCallMode",from(boolean.class,true));}
    @After public void finish(){if(controller!=null)controller.pause().stop().destroy();}
    @Test public void deniedFocusDuringCallKeepsVideoMutedAndManualUnmutePermitted(){
        create(AudioManager.MODE_IN_CALL,false);assertTrue(Decoder.last.plays>0);assertEquals(0,Decoder.last.volume,0);
        assertEquals("Unmute",((Button)get(a,"mute")).getText().toString());int opens=Decoder.last.opens;
        press("Unmute");assertEquals(1,Decoder.last.volume,0);assertEquals(opens,Decoder.last.opens);
        press("Mute");assertEquals(0,Decoder.last.volume,0);press("Unmute");assertEquals(1,Decoder.last.volume,0);
        AudioManager.OnAudioFocusChangeListener listener=get(a,"focus");int pauses=Decoder.last.pauses;
        listener.onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);shadowOf(Looper.getMainLooper()).idle();assertEquals(pauses,Decoder.last.pauses);
    }
    @Test public void ordinaryDeniedFocusAndTransientLossStillPause(){
        create(AudioManager.MODE_NORMAL,false);assertEquals(0,Decoder.last.plays);assertTrue(((TextView)get(a,"message")).getText().toString().contains("Audio is in use"));
        shadowOf(audio).setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_GRANTED);press("Play");assertEquals(1,Decoder.last.plays);
        AudioManager.OnAudioFocusChangeListener listener=get(a,"focus");listener.onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);shadowOf(Looper.getMainLooper()).idle();assertEquals(1,Decoder.last.pauses);
        listener.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);shadowOf(Looper.getMainLooper()).idle();assertEquals(2,Decoder.last.plays);
    }
    @Test public void callEntryMutesRestoresLevelAndDoesNotOverrideUserPause(){
        create(AudioManager.MODE_NORMAL,true);ReflectionHelpers.setField(a,"level",.37f);int opens=Decoder.last.opens;
        mode(AudioManager.MODE_IN_COMMUNICATION);assertEquals(0,Decoder.last.volume,0);assertTrue((Boolean)get(a,"wantsPlay"));
        press("Pause");int plays=Decoder.last.plays;mode(AudioManager.MODE_NORMAL);
        assertEquals(plays,Decoder.last.plays);assertEquals(.37f,Decoder.last.volume,0);assertFalse((Boolean)get(a,"wantsPlay"));assertEquals(opens,Decoder.last.opens);
        press("Play");mode(AudioManager.MODE_IN_CALL);mode(AudioManager.MODE_NORMAL);assertEquals(.37f,Decoder.last.volume,0);
    }
    @Test public void failedFocusAtCallEndDoesNotLeakAudioOrRestartPlayback(){
        create(AudioManager.MODE_IN_CALL,false);int plays=Decoder.last.plays;mode(AudioManager.MODE_NORMAL);
        assertEquals(plays,Decoder.last.plays);assertEquals(0,Decoder.last.volume,0);assertFalse((Boolean)get(a,"wantsPlay"));
    }
    @Test public void realViewInputPreservesExistingActionsAndResumeDialog(){
        create(AudioManager.MODE_NORMAL,true);press("Pause");press("Play");a.position(20000,300000);press("−10 s");assertEquals(10000,Decoder.last.lastSeek);press("+10 s");assertEquals(30000,Decoder.last.lastSeek);
        press("Display");AlertDialog d=ShadowAlertDialog.getLatestAlertDialog();assertTrue(d.isShowing());d.getListView().performItemClick(d.getListView().getChildAt(1),1,1);assertTrue((Boolean)get(a,"filling"));
        press("Auto rotate");assertEquals(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_LOCKED,a.getRequestedOrientation());press("Rotation locked");assertEquals(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,a.getRequestedOrientation());
        press("Audio");d=ShadowAlertDialog.getLatestAlertDialog();assertTrue(d.isShowing());d.dismiss();press("Subtitles");d=ShadowAlertDialog.getLatestAlertDialog();assertTrue(d.isShowing());d.dismiss();
        press("Volume");d=ShadowAlertDialog.getLatestAlertDialog();assertTrue(d.isShowing());d.dismiss();
        a.event("resume","60000");a.event("ready","");d=ShadowAlertDialog.getLatestAlertDialog();assertTrue("Resume choice visible",d.isShowing());d.getButton(AlertDialog.BUTTON_POSITIVE).performClick();shadowOf(Looper.getMainLooper()).idle();assertTrue("Original Resume callback",Decoder.last.choice);
        press("Stop");assertTrue(a.isFinishing());
    }
    @Test public void themeGeometryAndVideoTapPreserveEngineIdentity() throws Exception {
        create(AudioManager.MODE_NORMAL,true);int opens=Decoder.last.opens;FrameLayout picture=get(a,"picture");Rect before=new Rect(picture.getLeft(),picture.getTop(),picture.getRight(),picture.getBottom());
        for(int theme:new int[]{1,2,0}){ReflectionHelpers.setField(a,"appearance",theme);call(a,"applyChrome");measure();assertEquals(before,new Rect(picture.getLeft(),picture.getTop(),picture.getRight(),picture.getBottom()));}
        SurfaceView video=get(a,"video");video.performClick();assertEquals(View.GONE,((View)get(a,"controls")).getVisibility());video.performClick();assertEquals(View.VISIBLE,((View)get(a,"controls")).getVisibility());assertEquals(opens,Decoder.last.opens);
    }
    @Test public void renderBothThemesAndResponsiveWindows() throws Exception {
        create(AudioManager.MODE_NORMAL,true);int opens=Decoder.last.opens;
        java.nio.file.Path out=Paths.get(System.getProperty("preview.render.out"));Files.createDirectories(out);
        StringBuilder measurements=new StringBuilder("Host Activity rendering; synthetic bars, no decoder evidence.\n");
        for(String dimensions:new String[]{"w614dp-h640dp-320dpi","w411dp-h960dp-420dpi","w960dp-h411dp-320dpi","w360dp-h320dp-320dpi"}){
            RuntimeEnvironment.setQualifiers(dimensions);a.onConfigurationChanged(a.getResources().getConfiguration());measure();
            for(int theme:new int[]{1,2}){
                ReflectionHelpers.setField(a,"appearance",theme);call(a,"applyChrome");measure();FrameLayout picture=get(a,"picture");View top=get(a,"top"),controls=get(a,"controls");
                assertTrue(picture.getTop()>=top.getBottom());assertTrue(picture.getBottom()<=controls.getTop());assertTrue(picture.getWidth()>0&&picture.getHeight()>0);
                Bitmap image=Bitmap.createBitmap(root.getWidth(),root.getHeight(),Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(image);root.draw(canvas);
                // Mark the otherwise unavailable SurfaceView with explicitly synthetic bars.
                Paint p=new Paint();int[] colors={Color.WHITE,Color.YELLOW,Color.CYAN,Color.GREEN,Color.MAGENTA,Color.RED,Color.BLUE};
                RectF frame=new RectF(picture.getLeft()+2,picture.getTop()+2,picture.getRight()-2,picture.getBottom()-2);canvas.save();android.graphics.Path clip=new android.graphics.Path();clip.addRoundRect(frame,20,20,android.graphics.Path.Direction.CW);canvas.clipPath(clip);
                for(int i=0;i<colors.length;i++){p.setColor(colors[i]);canvas.drawRect(frame.left+frame.width()*i/7,frame.top,frame.left+frame.width()*(i+1)/7,frame.bottom,p);}canvas.restore();
                String name=dimensions+"-"+(theme==1?"light":"dark");try(java.io.OutputStream s=Files.newOutputStream(out.resolve(name+".png"))){image.compress(Bitmap.CompressFormat.PNG,100,s);}image.recycle();
                measurements.append(name+" root="+root.getWidth()+"x"+root.getHeight()+" video="+frame+" header="+top.getTop()+","+top.getBottom()+" controls="+controls.getTop()+","+controls.getBottom()+"\n");
            }
        }
        Files.write(out.resolve("MEASUREMENTS.txt"),measurements.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));assertEquals(opens,Decoder.last.opens);
    }
}
