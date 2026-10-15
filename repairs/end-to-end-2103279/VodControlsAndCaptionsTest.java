package com.projectinfinity.kodi;
import android.app.Application;import android.graphics.*;import android.view.*;import android.widget.*;
import androidx.media3.common.*;import androidx.media3.common.text.*;
import java.util.*;import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class) @Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class VodControlsAndCaptionsTest {
 Cobra2103201ScrubberTest f;
 Object call(String method,Object...args)throws Exception{return CobraNavigationUiTest.call(f.a,method,args);}
 @Before public void setup()throws Exception{f=new Cobra2103201ScrubberTest();f.before();CobraNavigationUiTest.put(f.a,"mPlayingVodKey","fixture:movie");f.prefs.edit().putBoolean("cobra_live_rewind_enabled",false).commit();call("cobraUpdateTimeshiftSeek");call("cobraUpdateLiveRewindControls");f.settle();}
 @After public void close()throws Exception{f.after();}
 @Test public void movieHasWorkingTimelineEvenWhenLiveRewindOff()throws Exception{assertEquals(View.VISIBLE,f.seek().getVisibility());assertEquals(500,f.seek().getProgress());assertEquals("Playback timeline",f.seek().getContentDescription());assertEquals(false,CobraNavigationUiTest.get(CobraNavigationUiTest.get(f.a,"mCobraPlayerProgramProgress"),"liveWindow"));}
 @Test public void movieDragSeeksOnceAndPreservesPausedDecoder()throws Exception{f.state.requested=false;float[] p=f.point(f.timeline(),.25f);f.event(MotionEvent.ACTION_DOWN,p);f.event(MotionEvent.ACTION_MOVE,f.point(f.timeline(),.7f));assertTrue(f.state.seeks.isEmpty());int target=f.seek().getProgress();f.event(MotionEvent.ACTION_UP,f.point(f.timeline(),.7f));assertEquals(Collections.singletonList(f.state.duration*target/1000L),f.state.seeks);assertFalse(f.state.requested);assertEquals(0,f.state.prepares);assertEquals(0,f.state.mediaChanges);}
 @Test public void movieTransportUsesExistingButtonsAndNeverRestarts()throws Exception{View rewind=f.overlay.findViewWithTag("cobra_live_rewind_30"),forward=f.overlay.findViewWithTag("cobra_live_edge");assertTrue(rewind.isEnabled());assertEquals("Forward 30 seconds",forward.getContentDescription());rewind.performClick();assertEquals(30000,f.state.position);forward.performClick();assertEquals(60000,f.state.position);assertEquals(0,f.state.prepares);assertEquals(0,f.state.mediaChanges);}
 @Test public void unknownOrUnsupportedDurationDoesNotExposeFalseSeekControl()throws Exception{f.state.duration=C.TIME_UNSET;call("cobraUpdateTimeshiftSeek");assertEquals(View.GONE,f.seek().getVisibility());call("cobraCommitTimelineSeek",500);assertTrue(f.state.seeks.isEmpty());}
 @Test public void captionPixelsStayAboveShownFooterAndReturnAfterHide()throws Exception{
  Object binding=CobraNavigationUiTest.construct("CobraPlayerBinding",f.a,f.player,CobraNavigationUiTest.get(f.a,"mPlaying"));((Map)CobraNavigationUiTest.get(f.a,"mCobraPlayerBindings")).put(f.player,binding);
  TextureView t=(TextureView)CobraNavigationUiTest.get(f.a,"mPlayerTexture");call("cobraAttachVideo",f.player,t);
  Bitmap cue=Bitmap.createBitmap(40,10,Bitmap.Config.ARGB_8888);cue.eraseColor(Color.GREEN);
  CobraNavigationUiTest.call(binding,"onCues",new CueGroup(Collections.singletonList(new Cue.Builder().setBitmap(cue).setSize(.5f).build()),0));f.settle();
  View captions=(View)CobraNavigationUiTest.get(binding,"captions");LinearLayout chrome=(LinearLayout)CobraNavigationUiTest.get(f.a,"mPlayerChrome");chrome.setVisibility(View.VISIBLE);int footer=chrome.getChildAt(chrome.getChildCount()-1).getTop();
  assertTrue(footer>0);assertTrue(bottomPixel(captions)<footer);Object features=CobraNavigationUiTest.get(f.a,"mFeatures");String adaptive=(String)CobraNavigationUiTest.call(features,"profileKey","cobra_subtitle_screen_adaptive");f.prefs.edit().putBoolean(adaptive,false).commit();assertTrue(bottomPixel(captions)>footer);f.prefs.edit().putBoolean(adaptive,true).commit();chrome.setVisibility(View.GONE);assertTrue(bottomPixel(captions)>footer);cue.recycle();
 }
 @Test public void cancelledMovieScrubKeepsPosition()throws Exception{float[] p=f.point(f.timeline(),.8f);f.event(MotionEvent.ACTION_DOWN,p);f.event(MotionEvent.ACTION_CANCEL,p);assertTrue(f.state.seeks.isEmpty());assertEquals(60000,f.state.position);}
 int bottomPixel(View v){Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));int last=-1;for(int y=0;y<b.getHeight();y++)if(Color.alpha(b.getPixel(b.getWidth()/2,y))>0)last=y;b.recycle();assertTrue(last>=0);return last;}
}
