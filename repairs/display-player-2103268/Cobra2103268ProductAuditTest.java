package com.projectinfinity.kodi;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Product oracles are defined in ACCEPTANCE.md before observing implementation.
 * Real production Activity/views/TextureView transforms, controlled source metadata.
 * Diagnostic video backgrounds are explicitly synthetic, not decoder/device evidence. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103268ProductAuditTest {
 Cobra2103202LifecycleTest f;InfinityLiveActivity a;Cobra2103202LifecycleTest.State s;TextureView texture;Object channel;int sw=1920,sh=1080;float pixel=1;
 static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
 static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
 Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(a,n,v);}
 @Before public void before()throws Exception{f=new Cobra2103202LifecycleTest();f.before();a=f.a;channel=f.channels.get(0);}
 @After public void after()throws Exception{f.after();}
 void single(int w,int h)throws Exception{
  s=f.new State(){@Override public Object invoke(Object p,Method m,Object[] v){if(m.getName().equals("getVideoSize"))return new VideoSize(sw,sh,0,pixel);return super.invoke(p,m,v);}};
  f.states.add(s);put(a,"mPlayer",s.player);put(a,"mPlaying",channel);call("openPlayerOverlay",channel);texture=(TextureView)get(a,"mPlayerTexture");f.bind(s,channel,texture);measure(w,h);
 }
 void measure(int w,int h)throws Exception{RuntimeEnvironment.setQualifiers("w"+w+"dp-h"+h+"dp-"+(w>h?"land":"port")+"-mdpi");f.ui.measure(a,w,h);call("cobraBuildPlayerChrome");f.ui.measure(a,w,h);call("applyCobraAspectTransform");f.ui.frames(15);}
 void mode(int mode)throws Exception{String key=(String)call("cobraPreferenceKey",channel);Object p=call("cobraReadPreferences",key);put(p,"aspect",mode);assertEquals(true,call("cobraSavePreferences",channel,key,p,false));call("applyCobraAspectTransform");}
 RectF picture() {RectF r=new RectF(0,0,texture.getWidth(),texture.getHeight());texture.getTransform(new Matrix()).mapRect(r);return r;}
 void centered(RectF r){assertEquals(texture.getWidth()/2f,r.centerX(),.6f);assertEquals(texture.getHeight()/2f,r.centerY(),.6f);}
 void shape(RectF r,float aspect){assertEquals(aspect,r.width()/r.height(),.006f);centered(r);}
 void fills(RectF r){assertTrue("No unexplained left bar "+r,r.left<=.6f);assertTrue("No unexplained top bar "+r,r.top<=.6f);assertTrue("No unexplained right bar "+r,r.right>=texture.getWidth()-.6f);assertTrue("No unexplained bottom bar "+r,r.bottom>=texture.getHeight()-.6f);assertTrue("Minimum crop must meet at least one viewport edge",Math.abs(r.width()-texture.getWidth())<.6f||Math.abs(r.height()-texture.getHeight())<.6f);}
 View row(String tag){return a.getWindow().getDecorView().findViewWithTag(tag);}
 void click(String tag){View v=row(tag);assertNotNull(tag,v);assertTrue(tag,v.performClick());}
 static View description(View v,String d){if(d.contentEquals(v.getContentDescription()==null?"":v.getContentDescription()))return v;if(v instanceof android.view.ViewGroup)for(int i=0;i<((android.view.ViewGroup)v).getChildCount();i++){View found=description(((android.view.ViewGroup)v).getChildAt(i),d);if(found!=null)return found;}return null;}
 void image(String name)throws Exception{
  View decor=a.getWindow().getDecorView();Bitmap b=Bitmap.createBitmap(decor.getWidth(),decor.getHeight(),Bitmap.Config.ARGB_8888);decor.draw(new Canvas(b));File dir=new File(System.getProperty("cobra.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,out);}b.recycle();
 }
 void diagnostic(){texture.setBackground(new Drawable(){final Paint p=new Paint(3);public void draw(Canvas c){RectF r=picture();c.save();c.clipRect(0,0,texture.getWidth(),texture.getHeight());p.setColor(0xff25547a);c.drawRect(r,p);for(int i=0;i<=12;i++){p.setColor(i==6?0xfff3cb52:0xff709bbd);c.drawLine(r.left+r.width()*i/12f,r.top,r.left+r.width()*i/12f,r.bottom,p);}for(int j=0;j<=8;j++)c.drawLine(r.left,r.top+r.height()*j/8f,r.right,r.top+r.height()*j/8f,p);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(4);p.setColor(Color.WHITE);c.drawCircle(r.centerX(),r.centerY(),r.height()*.25f,p);p.setStyle(Paint.Style.FILL);p.setTextSize(16);c.drawText("SYNTHETIC SOURCE • UI/GEOMETRY ONLY",12,28,p);c.restore();}public void setAlpha(int a){}public void setColorFilter(ColorFilter f){}public int getOpacity(){return PixelFormat.OPAQUE;}});}

 @Test public void fullscreenBestFitFillsWithoutStretchingAcrossRepresentativeSourcesAndPanes()throws Exception{
  single(800,600);for(int[] pane:new int[][]{{800,600},{600,800},{320,720},{960,540}}){measure(pane[0],pane[1]);for(int[] source:new int[][]{{1920,1080},{1440,1080},{1080,1920},{2390,1000},{720,576}}){sw=source[0];sh=source[1];pixel=sw==720?1.422222f:1;mode(0);RectF r=picture();shape(r,sw*pixel/sh);fills(r);}}
 }
 @Test public void foldFitReducesBandsWhileFillUsesOnlyNecessaryCenteredCrop()throws Exception{
  single(800,600);sw=1920;sh=1080;mode(12);RectF fit=picture();shape(fit,16f/9);assertTrue("Fold Fit reduces strict-contain top/bottom bands",fit.height()>450);assertTrue("Balanced fit keeps less crop than Fill",fit.width()<1067);mode(13);RectF fill=picture();shape(fill,16f/9);fills(fill);assertTrue(fill.height()>fit.height());mode(1);assertEquals(fill,picture());
 }
 @Test public void fixedWideShortZoomCustomHaveLabelledGeometryAndNoTransformResidue()throws Exception{
  single(800,600);for(int[] source:new int[][]{{1920,1080},{1440,1080},{1080,1920},{2390,1000}}){sw=source[0];sh=source[1];mode(2);shape(picture(),16f/9);mode(3);shape(picture(),4f/3);
   // Preview/PiP contain is an independent whole-frame reference for labeled modifiers.
   put(a,"mInPictureInPicture",true);mode(0);RectF whole=picture();put(a,"mInPictureInPicture",false);
   for(int i=4;i<=6;i++){mode(i);RectF r=picture();float factor=i==4?1.10f:i==5?1.25f:1.40f;assertEquals(whole.width()*factor,r.width(),.7f);assertEquals(whole.height(),r.height(),.7f);centered(r);}
   mode(7);assertEquals(whole.width()*1.24f,picture().width(),.7f);assertEquals(whole.height()*.84f,picture().height(),.7f);centered(picture());
   for(int i=8;i<=10;i++){mode(i);RectF r=picture();shape(r,sw*pixel/sh);float zoom=i==8?1.25f:i==9?1.5f:2f;assertEquals(whole.width()*zoom,r.width(),.7f);assertEquals(whole.height()*zoom,r.height(),.7f);}
   String key=(String)call("cobraPreferenceKey",channel);Object p=call("cobraReadPreferences",key);put(p,"aspect",11);put(p,"x",1.6f);put(p,"y",.6f);call("cobraSavePreferences",channel,key,p,false);assertEquals(whole.width()*1.6f,picture().width(),.7f);assertEquals(whole.height()*.6f,picture().height(),.7f);
   mode(13);fills(picture());mode(3);shape(picture(),4f/3);
  }
 }
 @Test public void inheritRemovesOverrideAndFollowsLaterGlobalDefaultWithTruthfulCheckmark()throws Exception{
  single(800,600);mode(3);call("showCobraAspectPicker");click("cobra-channel-aspect:-1");Object p=call("cobraReadPreferences",call("cobraPreferenceKey",channel));assertEquals(-1,get(p,"aspect"));assertTrue(row("cobra-channel-aspect:-1").isSelected());put(a,"mAspectMode",2);call("applyCobraAspectTransform");shape(picture(),16f/9);put(a,"mAspectMode",3);call("applyCobraAspectTransform");shape(picture(),4f/3);assertEquals(-1,get(call("cobraReadPreferences",call("cobraPreferenceKey",channel)),"aspect"));
 }
 @Test public void displayScrollAffordanceIsVisibleAndSelectedBottomChoiceRevealsItself()throws Exception{
  single(320,720);mode(10);call("showCobraAspectPicker");f.ui.measure(a,320,720);f.ui.frames(15);f.ui.measure(a,320,720);ScrollView scroll=(ScrollView)row("cobra_display_scroll");assertNotNull("15 choices must announce scrolling",scroll);assertTrue(scroll.isVerticalScrollBarEnabled());assertFalse(scroll.isScrollbarFadingEnabled());assertTrue(row("cobra_display_scroll_cue").isShown());View selected=row("cobra-channel-aspect:10");assertTrue(selected.isSelected());Rect selectedBounds=new Rect(),viewport=new Rect();assertTrue(selected.getGlobalVisibleRect(selectedBounds));scroll.getGlobalVisibleRect(viewport);assertTrue("Selected item must fit inside viewport",viewport.contains(selectedBounds));assertTrue(scroll.getScrollY()>0);image("display-cover-selected-zoom-dark");
 }
 @Test public void channelCustomResetIsReachablePersistsAndDoesNotAffectOtherChannel()throws Exception{
  single(320,720);String key=(String)call("cobraPreferenceKey",channel);Object p=call("cobraReadPreferences",key);put(p,"aspect",11);put(p,"x",1.6f);put(p,"y",.6f);call("cobraSavePreferences",channel,key,p,false);call("cobraShowChannelCustomAspect",channel);f.ui.measure(a,320,720);click("cobra-channel-custom-reset");p=call("cobraReadPreferences",key);assertEquals(1f,(Float)get(p,"x"),0);assertEquals(1f,(Float)get(p,"y"),0);assertEquals(11,get(p,"aspect"));Object other=call("cobraReadPreferences",call("cobraPreferenceKey",f.channels.get(1)));assertEquals(-1,get(other,"aspect"));assertEquals(1f,(Float)get(other,"x"),0);assertEquals(1f,(Float)get(other,"y"),0);
 }
 @Test public void allFiveTransportControlsStayReachableOnCoverAndLargeText()throws Exception{
  single(320,720);Configuration c=new Configuration(a.getResources().getConfiguration());c.fontScale=1.5f;a.getResources().updateConfiguration(c,a.getResources().getDisplayMetrics());measure(320,720);View root=(View)get(a,"mPlayerOverlay");for(String label:new String[]{"Previous channel","cobra_live_rewind_30","Pause","cobra_live_edge","Next channel"}){View v=label.startsWith("cobra_")?row(label):description(root,label);assertNotNull(label,v);Rect r=new Rect();v.getDrawingRect(r);((android.view.ViewGroup)root).offsetDescendantRectToMyCoords(v,r);assertTrue(label+" escapes pane: "+r,r.left>=0&&r.right<=root.getWidth());assertTrue(label+" touch target",v.getWidth()>=48);assertTrue(v.isShown());}image("player-cover-large-text-dark");
 }
 @Test public void channelsDotTracksActualSessionIndependentlyOfDrawerFocus()throws Exception{
  single(800,600);call("showCobraPlayerDrawer");f.ui.measure(a,800,600);android.widget.ListView list=(android.widget.ListView)get(a,"mCobraPlayerDrawerList");View playing=list.findViewWithTag("cobra-player-channel-row:fixture:0");assertNotNull("Actual player Channels must carry locked playing dot",playing);View dot=playing.findViewWithTag("cobra_player_playing_dot");assertNotNull(dot);assertEquals(View.VISIBLE,dot.getVisibility());list.setSelection(2);f.ui.measure(a,800,600);assertEquals(true,call("cobraChannelActuallyPlaying",channel));assertEquals(false,call("cobraChannelActuallyPlaying",f.channels.get(2)));s.requested=false;call("cobraRefreshPlayingIndicators");assertEquals(View.INVISIBLE,dot.getVisibility());s.requested=true;call("cobraRefreshPlayingIndicators");assertEquals(View.VISIBLE,dot.getVisibility());image("player-channels-dot-dark");
 }
 @Test public void emptyVideoHoldNeverOpensMenuAndLockedTapCannotActOnPlayback()throws Exception{
  single(800,600);View overlay=(View)get(a,"mPlayerOverlay");overlay.performLongClick();assertNull(get(a,"mCobraPlayerDrawer"));assertNull(get(a,"mCobraActionSheet"));call("lockCobraPlayer");assertTrue((Boolean)get(a,"mCobraPlayerLocked"));overlay.performClick();overlay.performLongClick();assertTrue(s.requested);assertNull(get(a,"mCobraPlayerDrawer"));assertNull(get(a,"mCobraActionSheet"));click("cobra_player_unlock");assertFalse((Boolean)get(a,"mCobraPlayerLocked"));overlay.performClick();assertNull(get(a,"mCobraPlayerDrawer"));assertSame(s.player,get(a,"mPlayer"));
 }
 @Test public void bottomMenusAreMutuallyExclusiveAndBackReturnsSamePlayback()throws Exception{
  single(800,600);call("showCobraPlayerDrawer");call("showCobraAspectPicker");assertNull(get(a,"mCobraPlayerDrawer"));assertEquals("channel-aspect",get(a,"mCobraSheetKind"));call("showPlayerSettingsDrawer");assertEquals("player-settings",get(a,"mCobraSheetKind"));assertNull(get(a,"mCobraPlayerDrawer"));a.onBackPressed();assertNull(get(a,"mCobraActionSheet"));assertSame(s.player,get(a,"mPlayer"));assertEquals(0,s.prepares);assertEquals(0,s.releases);
 }
 @Test public void pipUsesSafetyFitThenRestoresSavedDisplayWithoutRestart()throws Exception{
  single(800,600);mode(10);RectF zoom=picture();put(a,"mInPictureInPicture",true);call("applyCobraAspectTransform");RectF safe=picture();assertTrue(safe.width()<=texture.getWidth()+.6f&&safe.height()<=texture.getHeight()+.6f);put(a,"mInPictureInPicture",false);call("applyCobraAspectTransform");assertEquals(zoom,picture());assertSame(s.player,get(a,"mPlayer"));assertEquals(0,s.prepares);assertEquals(0,s.releases);
 }
 @Test public void foldOrientationReflowsExistingSurfaceAndRendersGlassInBothAppearances()throws Exception{
  single(800,600);mode(12);TextureView owner=texture;diagnostic();for(String appearance:new String[]{"oled","light"}){f.prefs.edit().putString("cobra_appearance_mode",appearance).commit();for(int[] pane:new int[][]{{800,600},{600,800},{320,720},{960,540}}){Configuration c=new Configuration(a.getResources().getConfiguration());c.orientation=pane[0]>pane[1]?Configuration.ORIENTATION_LANDSCAPE:Configuration.ORIENTATION_PORTRAIT;a.onConfigurationChanged(c);measure(pane[0],pane[1]);assertSame(owner,get(a,"mPlayerTexture"));assertSame(s.player,get(a,"mPlayer"));shape(picture(),16f/9);image("player-"+appearance+"-"+pane[0]+"x"+pane[1]);call("showCobraAspectPicker");f.ui.measure(a,pane[0],pane[1]);f.ui.frames(15);image("display-"+appearance+"-"+pane[0]+"x"+pane[1]);call("closeCobraActionSheet");}}assertEquals(0,s.prepares);assertEquals(0,s.releases);
 }
 @Test public void ambientAndCinemaChangeAtmosphereWithoutVideoTransformOrPlaybackChange()throws Exception{
  single(800,600);mode(12);RectF original=picture();for(int ambient=0;ambient<3;ambient++)for(boolean cinema:new boolean[]{false,true}){f.prefs.edit().putString("cobra_ambient_mode",ambient==0?"off":ambient==1?"subtle":"immersive").putBoolean("cobra_night_cinema",cinema).commit();call("cobraRefreshAmbient");call("cobraRefreshVisualEffects");assertEquals(original,picture());assertSame(s.player,get(a,"mPlayer"));assertTrue(s.requested);}assertEquals(0,s.prepares);assertEquals(0,s.releases);
 }
 @Test public void multiviewDisplayAndAudioOwnershipDoNotPausePeersOrContaminateTiles()throws Exception{
  f.multi(4);List<Cobra2103202LifecycleTest.State> states=f.states;Object[] channels=(Object[])get(a,"mMultiChannels");ExoPlayer[] players=(ExoPlayer[])get(a,"mMultiPlayers");Map<?,?> bindings=(Map<?,?>)get(a,"mCobraPlayerBindings");TextureView t0=(TextureView)get(bindings.get(players[0]),"texture"),t1=(TextureView)get(bindings.get(players[1]),"texture");Matrix original=t1.getTransform(new Matrix());Object p=call("cobraReadPreferences",call("cobraPreferenceKey",channels[0]));put(p,"aspect",3);call("cobraSavePreferences",channels[0],call("cobraPreferenceKey",channels[0]),p,false);assertEquals(original,t1.getTransform(new Matrix()));for(int owner=0;owner<4;owner++){call("setMultiAudio",owner);assertEquals(owner,get(a,"mAudioTile"));for(Cobra2103202LifecycleTest.State state:states){assertTrue(state.requested);assertEquals(0,state.releases);assertEquals(0,state.prepares);}}assertNotEquals(t0.getTransform(new Matrix()),t1.getTransform(new Matrix()));
 }
}
