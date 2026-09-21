package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.TextureView;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.util.Locale;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual production Android views/drawables and interaction dispatch with controlled
 * guide data. Screenshots are Android/Robolectric evidence, not physical Fold,
 * GPU/decoder, live streaming, SystemUI, or device performance acceptance. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103204PresentationTest {
  CobraNavigationUiTest ui;
  Locale previousLocale;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static Object call(Object o,String n,Object...v)throws Exception{return CobraNavigationUiTest.call(o,n,v);}

  @Before public void before()throws Exception{
    previousLocale=Locale.getDefault();Locale.setDefault(Locale.US);
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();
    // Only Robolectric's isolated application files: built-in assertions must not
    // accidentally inspect a legacy external palette written by another fixture.
    File ext=RuntimeEnvironment.getApplication().getExternalFilesDir(null);
    if(ext!=null){File palette=new File(ext,".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json");if(palette.exists())assertTrue(palette.delete());}
  }
  @After public void after(){CobraVisualRenderer.clients.clear();Locale.setDefault(previousLocale);}
  static void qualifiers(int width,int height){RuntimeEnvironment.setQualifiers("w"+width+"dp-h"+height+"dp-"+(width>height?"land":"port")+"-mdpi");}
  InfinityLiveActivity activity(String mode,int width,int height)throws Exception{
    qualifiers(width,height);InfinityLiveActivity a=ui.fixture(96);
    ((SharedPreferences)get(a,"mPrefs")).edit().putString("cobra_appearance_mode",mode).commit();
    call(a,"buildShell");ui.measure(a,width,height);return a;
  }
  void shot(InfinityLiveActivity a,String name,int width,int height)throws Exception{
    Cobra2103201MenuPolishTest.capture(a,ui,"cobra204-"+name,width,height);
  }
  View tag(InfinityLiveActivity a,String name){return a.getWindow().getDecorView().findViewWithTag(name);}
  static TextView text(View view,String exact){
    if(view instanceof TextView&&exact.contentEquals(((TextView)view).getText()))return (TextView)view;
    if(view instanceof ViewGroup){ViewGroup g=(ViewGroup)view;for(int i=0;i<g.getChildCount();i++){TextView result=text(g.getChildAt(i),exact);if(result!=null)return result;}}
    return null;
  }
  static TextView firstText(View view){
    if(view instanceof TextView&&((TextView)view).getText().length()>0)return (TextView)view;
    if(view instanceof ViewGroup){ViewGroup g=(ViewGroup)view;for(int i=0;i<g.getChildCount();i++){TextView result=firstText(g.getChildAt(i));if(result!=null)return result;}}
    return null;
  }
  static Bitmap background(View view,int underlay){
    int w=Math.max(32,view.getWidth()),h=Math.max(32,view.getHeight());
    Bitmap b=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);b.eraseColor(underlay);
    Drawable d=view.getBackground();assertNotNull("Production view has a background",d);
    Rect previous=new Rect(d.getBounds());d.setBounds(0,0,w,h);d.draw(new Canvas(b));d.setBounds(previous);return b;
  }
  static double linear(int value){double x=value/255d;return x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4);}
  static double luminance(int color){return .2126*linear(Color.red(color))+.7152*linear(Color.green(color))+.0722*linear(Color.blue(color));}
  static double contrast(int a,int b){double x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
  static void readable(TextView text,View background,int underlay){
    assertNotNull(text);Bitmap pixels=background(background,underlay);
    try{for(int y:new int[]{pixels.getHeight()/4,pixels.getHeight()/2,pixels.getHeight()*3/4}){
      int surface=pixels.getPixel(pixels.getWidth()/2,y);double ratio=contrast(text.getCurrentTextColor(),surface);
      assertTrue("Actual text/drawable contrast for '"+text.getText()+"': "+ratio,ratio>=4.5);
    }}finally{pixels.recycle();}
  }
  static void inWindow(InfinityLiveActivity a,View view){
    assertNotNull(view);Rect visible=new Rect();assertTrue(view.getGlobalVisibleRect(visible));
    Rect window=new Rect();assertTrue(a.getWindow().getDecorView().getGlobalVisibleRect(window));
    assertTrue("Surface stays inside attached window: "+visible+" / "+window,window.contains(visible));
    assertTrue(view.getWidth()>0&&view.getHeight()>0);
    int[] location=new int[2];view.getLocationOnScreen(location);
    Rect bounds=new Rect(location[0],location[1],location[0]+view.getWidth(),location[1]+view.getHeight());
    // getGlobalVisibleRect is root-relative, while getLocationOnScreen includes
    // the window origin. Full (unclipped) bounds must use the same coordinates.
    View decor=a.getWindow().getDecorView();int[] origin=new int[2];decor.getLocationOnScreen(origin);
    Rect screenWindow=new Rect(origin[0],origin[1],origin[0]+decor.getWidth(),origin[1]+decor.getHeight());
    assertTrue("Full laid-out control must fit, not only its clipped visible portion: "+bounds+" / screenWindow="+screenWindow+" / visibleRoot="+window,screenWindow.contains(bounds));
  }
  static void tapIcon(View row,boolean cancel){
    assertTrue(row instanceof ViewGroup);View icon=((ViewGroup)row).getChildAt(0);
    float x=icon.getLeft()+icon.getWidth()/2f,y=icon.getTop()+icon.getHeight()/2f;long t=SystemClock.uptimeMillis();
    MotionEvent down=MotionEvent.obtain(t,t,MotionEvent.ACTION_DOWN,x,y,0),up=MotionEvent.obtain(t,t+20,cancel?MotionEvent.ACTION_CANCEL:MotionEvent.ACTION_UP,x,y,0);
    try{assertTrue("Decorative icon area dispatches to the actual row",row.dispatchTouchEvent(down));row.dispatchTouchEvent(up);}finally{down.recycle();up.recycle();}
  }
  void guideMatrix(String appearance)throws Exception{
    for(int[] size:new int[][]{{320,720},{768,1024},{960,540}}){
      InfinityLiveActivity a=activity(appearance,size[0],size[1]);
      try{
        call(a,"cobraOpenLiveTv");ui.measure(a,size[0],size[1]);TextureView texture=(TextureView)get(a,"mCobraPreviewTexture");
        for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
          call(a,"cobraSwitchMode",mode);ui.measure(a,size[0],size[1]);
          // Retain the first-traversal checks above, then let the established
          // 190 ms browser transition finish naturally before settled geometry.
          ui.frames(20);ui.measure(a,size[0],size[1]);
          View browser=(View)get(a,"mCobraGuideBrowser");
          assertEquals("Browser transition must finish without a stale offset",0f,browser.getTranslationY(),.001f);
          assertEquals("Browser transition must finish fully visible",1f,browser.getAlpha(),.001f);
          assertSame("Visual guide modes retain the existing preview surface",texture,get(a,"mCobraPreviewTexture"));
          assertTrue(texture.isAttachedToWindow());assertTrue(texture.getWidth()>24&&texture.getHeight()>24);
          View shell=(View)get(a,"mCobraGuideShell");AbsListView list=(AbsListView)get(a,"mCobraGuideList");
          assertNotNull(list);assertTrue("Real virtualized rows, not empty placeholders",list.getChildCount()>0);
          assertTrue("Guide list must not eagerly render all channels",list.getChildCount()<96);
          Bitmap canvas=background(shell,Color.MAGENTA);
          int wanted="light".equals(appearance)?Color.WHITE:Color.BLACK;
          try{assertEquals("Actual "+appearance+" canvas",wanted,canvas.getPixel(canvas.getWidth()/2,canvas.getHeight()/2));}finally{canvas.recycle();}
          readable((TextView)get(a,"mCobraModeTitle"),shell,wanted);
          readable((TextView)get(a,"mCobraModeSub"),shell,wanted);
          inWindow(a,list);shot(a,"guide-"+mode+"-"+appearance+"-"+size[0]+"x"+size[1],size[0],size[1]);
        }
      }finally{ui.clean(a);}
    }
  }
  @Test(timeout=180000) public void lightGuideModesRenderWhiteCanvasAcrossCoverFoldAndLandscape()throws Exception{guideMatrix("light");}
  @Test(timeout=180000) public void darkGuideModesRenderBlackCanvasAcrossCoverFoldAndLandscape()throws Exception{guideMatrix("dark");}
  @Test(timeout=180000) public void oledGuideModesRenderBlackCanvasAcrossCoverFoldAndLandscape()throws Exception{guideMatrix("oled");}

  void screens(String mode)throws Exception{
    InfinityLiveActivity a=activity(mode,412,915);
    try{
      for(String method:new String[]{"showWelcome","showSettings","showSources","showRecordings","showWatchlist","showMovies","showSeries"}){
        call(a,"closeCobraActionSheet");call(a,method);ui.measure(a,412,915);
        View stage=(View)get(a,"mStage");assertTrue(stage.isAttachedToWindow());inWindow(a,stage);
        shot(a,method+"-"+mode+"-412x915",412,915);
      }
      call(a,"showSettings");call(a,"showCobraHealthCenter");ui.measure(a,412,915);
      assertNotNull(tag(a,"cobra-health-refresh"));assertNotNull(tag(a,"cobra-health-export"));
      inWindow(a,tag(a,"cobra_sheet_panel"));shot(a,"health-idle-"+mode+"-412x915",412,915);
      call(a,"closeCobraActionSheet");call(a,"toggleCobraDrawer");ui.measure(a,412,915);
      inWindow(a,tag(a,"cobra_experience_drawer"));shot(a,"drawer-"+mode+"-412x915",412,915);
    }finally{ui.clean(a);}
  }
  @Test(timeout=120000) public void lightInternalScreensAndIdleStatesUseProductionViews()throws Exception{screens("light");}
  @Test(timeout=120000) public void darkInternalScreensAndIdleStatesUseProductionViews()throws Exception{screens("dark");}

  @Test public void sheetNormalSelectedAndFocusedRowsHaveReadableActualPixels()throws Exception{
    for(String mode:new String[]{"light","dark","oled"}){
      InfinityLiveActivity a=activity(mode,412,915);
      try{
        LinearLayout rows=(LinearLayout)call(a,"cobraOpenSheet","Audio & subtitles","Existing control states","presentation-fixture");
        View row=(View)call(a,"cobraDetailRow","cc","English","Available subtitle track","cobra204-contrast-row",false,(Runnable)()->{});rows.addView(row);
        ui.measure(a,412,915);ui.frames(20);View panel=tag(a,"cobra_sheet_panel");
        int under="light".equals(mode)?Color.WHITE:Color.BLACK;
        Bitmap p=background(panel,under);int panelColor=p.getPixel(p.getWidth()/2,p.getHeight()/2);p.recycle();
        TextView title=text(row,"English");TextView detail=text(row,"Available subtitle track");
        readable(title,row,panelColor);readable(detail,row,panelColor);
        row.setSelected(true);ui.frames(2);readable(title,row,panelColor);readable(detail,row,panelColor);
        assertTrue("Existing D-pad/touch focus entry is still available",row.requestFocusFromTouch());ui.frames(20);
        assertTrue(row.hasFocus());readable(title,row,panelColor);readable(detail,row,panelColor);
        assertEquals("Focus feedback never translates a touch target",0f,row.getTranslationX(),.001f);
        assertEquals(0f,row.getTranslationY(),.001f);
        shot(a,"sheet-selected-focused-"+mode+"-412x915",412,915);
      }finally{ui.clean(a);}
    }
  }

  @Test public void repeatedTapsDuringSheetEntryDoNotDelayOrDuplicateTheAction()throws Exception{
    InfinityLiveActivity a=activity("dark",412,915);final int[] actions={0};
    try{
      for(int i=0;i<12;i++){
        LinearLayout rows=(LinearLayout)call(a,"cobraOpenSheet","Menu","Immediate action fixture","presentation-tap");
        View row=(View)call(a,"cobraSheetRow","cc","Subtitles off","Immediate existing action",false,true,(Runnable)()->actions[0]++);rows.addView(row);
        ui.measure(a,412,915); // Six frames: deliberately before a 190 ms entry settles.
        int before=actions[0];tapIcon(row,true);ui.frames(2);assertEquals(before,actions[0]);
        assertNotNull(get(a,"mCobraActionSheet"));tapIcon(row,false);ui.frames(2);
        assertEquals("One tap invokes exactly one action while animating",before+1,actions[0]);
        assertNull("Dismissal must not wait for the decorative animation",get(a,"mCobraActionSheet"));
        ui.frames(14);assertNull("A stale animation cannot resurrect the menu",get(a,"mCobraActionSheet"));
      }
      assertEquals(12,actions[0]);
    }finally{ui.clean(a);}
  }

  @Test public void rapidMenuReplacementDoesNotLeaveInvisibleInterceptingOverlays()throws Exception{
    InfinityLiveActivity a=activity("light",320,720);
    try{
      for(int i=0;i<12;i++){
        call(a,"cobraOpenSheet","First","Closing during entry","presentation-first");ui.measure(a,320,720);
        View old=(View)get(a,"mCobraActionSheet");
        call(a,"cobraOpenSheet","Replacement","Must own input immediately","presentation-second");ui.measure(a,320,720);ui.frames(20);
        assertFalse(old.isAttachedToWindow());View current=(View)get(a,"mCobraActionSheet");assertTrue(current.isAttachedToWindow());
        View panel=tag(a,"cobra_sheet_panel");assertEquals(1f,panel.getAlpha(),.001f);inWindow(a,panel);
        assertTrue((Boolean)call(a,"closeCobraActionSheet"));ui.frames(20);assertFalse(current.isAttachedToWindow());assertNull(get(a,"mCobraActionSheet"));
      }
    }finally{ui.clean(a);}
  }

  @Test public void fourteenRowEntryKeepsHitRectanglesAndFinishesWithinQuarterSecondFrameBudget()throws Exception{
    InfinityLiveActivity a=activity("dark",412,915);final int[] clicks=new int[14];
    try{
      FrameLayout root=new FrameLayout(a);root.setFocusable(true);root.setFocusableInTouchMode(true);a.setContentView(root);
      LinearLayout group=new LinearLayout(a);group.setOrientation(LinearLayout.VERTICAL);root.addView(group,new FrameLayout.LayoutParams(-1,-2));
      for(int i=0;i<14;i++){
        final int index=i;Button button=(Button)call(a,"action","Action "+(i+1));button.setOnClickListener(v->clicks[index]++);
        group.addView(button,new LinearLayout.LayoutParams(-1,48));
      }
      ui.measure(a,412,915);assertTrue(root.requestFocus());
      call(a,"cobraAnimateChildrenIn",group);ui.frames(1);
      for(int i=0;i<14;i++){
        View child=group.getChildAt(i);assertEquals(0f,child.getTranslationX(),.001f);assertEquals(0f,child.getTranslationY(),.001f);
        assertEquals(1f,child.getScaleX(),.001f);assertEquals(1f,child.getScaleY(),.001f);
        assertTrue("The complete declared fade fits comfortably inside 250 ms",child.animate().getStartDelay()+child.animate().getDuration()<=226L);
        assertTrue("Entry must really be unfinished when input is dispatched",child.getAlpha()<1f);
      }
      for(int index:new int[]{0,13}){
        View button=group.getChildAt(index);Rect hit=new Rect();button.getDrawingRect(hit);group.offsetDescendantRectToMyCoords(button,hit);
        long now=SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,hit.exactCenterX(),hit.exactCenterY(),0);
        MotionEvent up=MotionEvent.obtain(now,now+1,MotionEvent.ACTION_UP,hit.exactCenterX(),hit.exactCenterY(),0);
        try{assertTrue("Parent dispatch must hit the visible rectangle",group.dispatchTouchEvent(down));assertTrue(group.dispatchTouchEvent(up));}finally{down.recycle();up.recycle();}
      }
      ui.frames(1);assertEquals("First row invokes during entry",1,clicks[0]);assertEquals("Last row invokes without waiting for its fade",1,clicks[13]);
      for(int i=1;i<13;i++)assertEquals(0,clicks[i]);
      // 16 x 16 ms = 256 ms, a 250 ms budget rounded up to the next display frame.
      // The first Choreographer callback may itself consume one frame; the actual
      // declared animation budget above remains at most 66 + 160 = 226 ms.
      ui.frames(14);
      for(int i=0;i<14;i++){
        View child=group.getChildAt(i);assertEquals("All rows finish within the frame-rounded budget",1f,child.getAlpha(),.000001f);
        assertEquals(0f,child.getTranslationX(),.001f);assertEquals(0f,child.getTranslationY(),.001f);
        assertEquals(1f,child.getScaleX(),.001f);assertEquals(1f,child.getScaleY(),.001f);
      }
    }finally{ui.clean(a);}
  }

  @Test public void followSystemChangesActualGuidePixelsWithoutReplacingTexture()throws Exception{
    InfinityLiveActivity a=activity("system",320,720);
    try{
      SharedPreferences prefs=(SharedPreferences)get(a,"mPrefs");prefs.edit().putString("cobra_system_dark_variant","oled").commit();
      call(a,"cobraOpenLiveTv");ui.measure(a,320,720);Object texture=get(a,"mCobraPreviewTexture");
      for(boolean night:new boolean[]{false,true,false,true}){
        Configuration c=new Configuration(a.getResources().getConfiguration());c.uiMode=(c.uiMode&~Configuration.UI_MODE_NIGHT_MASK)|(night?Configuration.UI_MODE_NIGHT_YES:Configuration.UI_MODE_NIGHT_NO);
        c.fontScale=1.5f;a.getResources().updateConfiguration(c,a.getResources().getDisplayMetrics());a.onConfigurationChanged(c);ui.measure(a,320,720);
        assertSame(texture,get(a,"mCobraPreviewTexture"));View shell=(View)get(a,"mCobraGuideShell");Bitmap pixels=background(shell,Color.MAGENTA);
        try{assertEquals(night?Color.BLACK:Color.WHITE,pixels.getPixel(pixels.getWidth()/2,pixels.getHeight()/2));}finally{pixels.recycle();}
        shot(a,"follow-system-"+(night?"night":"day")+"-cover-font150",320,720);
      }
      assertEquals("system",prefs.getString("cobra_appearance_mode",""));assertEquals("oled",prefs.getString("cobra_system_dark_variant",""));
    }finally{ui.clean(a);}
  }

  @Test public void playerChromeAndPlaybackSheetsStayReadableWithoutTransportWrites()throws Exception{
    // This nested fixture is invoked as Java, so its own @Config is not applied.
    // Set the actual window configuration before constructing its activity.
    qualifiers(960,540);
    Cobra2103199DisplayRegressionTest f=new Cobra2103199DisplayRegressionTest();f.before();
    try{
      InfinityLiveActivity a=f.a;Cobra2103199DisplayRegressionTest.Controlled player=f.new Controlled();
      TextureView texture=f.texture(960,540);Object channel=f.channel(0);f.bind(player,channel,texture,true);player.writes.clear();
      for(String mode:new String[]{"light","dark","oled"}){
        f.prefs.edit().putString("cobra_appearance_mode",mode).commit();call(a,"cobraBuildPlayerChrome");f.ui.measure(a,960,540);
        assertSame(texture,get(a,"mPlayerTexture"));assertSame(player.player,get(a,"mPlayer"));
        assertNotNull(tag(a,"cobra_player_aspect_anchor"));assertNotNull(tag(a,"cobra_player_options_anchor"));
        assertTrue("Player title remains readable against dark video-safe chrome",luminance(((TextView)tag(a,"cobra_player_channel_title")).getCurrentTextColor())>.75);
        shot(a,"player-chrome-"+mode+"-960x540",960,540);
        call(a,"cobraShowChannelPreferences",channel);f.ui.measure(a,960,540);f.ui.frames(20);
        View panel=tag(a,"cobra_sheet_panel");Bitmap pixels=background(panel,Color.BLACK);
        try{assertTrue("Playback menus stay video-safe dark even in Light",luminance(pixels.getPixel(pixels.getWidth()/2,pixels.getHeight()/2))<.10);}finally{pixels.recycle();}
        assertNotNull(tag(a,"cobra-channel-pip"));assertNotNull(tag(a,"cobra-channel-background"));assertNotNull(tag(a,"cobra-channel-rewind"));
        shot(a,"player-preferences-"+mode+"-960x540",960,540);call(a,"closeCobraActionSheet");
      }
      assertFalse(player.writes.contains("prepare"));assertFalse(player.writes.contains("release"));assertFalse(player.writes.contains("seekTo"));
      assertFalse(player.writes.contains("setVideoTextureView"));assertFalse(player.writes.contains("clearVideoTextureView"));
    }finally{f.after();}
  }

  @Test public void actualSubtitleSheetHasBlueSelectionAndPreservesSelectedTrackAction()throws Exception{
    Cobra2103201SubtitleTest f=new Cobra2103201SubtitleTest();f.before();
    try{
      f.tracks(Cobra2103201SubtitleTest.group("english","text/vtt","en",true,true));f.cue();
      for(String mode:new String[]{"light","dark","oled"}){
        ((SharedPreferences)get(f.a,"mPrefs")).edit().putString("cobra_appearance_mode",mode).commit();
        f.open();f.ui.frames(20);View row=f.tag("cobra-track:0:0");assertTrue(row.isSelected());
        int accent=(Integer)call(f.a,"cobraModeColor","accent");assertTrue("Selection is blue, not the prior red theme",Color.blue(accent)>Color.red(accent));
        Bitmap selected=background(row,Color.BLACK);row.setSelected(false);Bitmap normal=background(row,Color.BLACK);row.setSelected(true);
        try{
          assertFalse("Selection changes the actual row pixels, not only a preference",selected.sameAs(normal));
          int bluePixels=0;for(int y=0;y<selected.getHeight();y++)for(int x=0;x<selected.getWidth();x++){
            int ink=selected.getPixel(x,y);if(Color.blue(ink)>Color.red(ink)+24&&Color.blue(ink)>Color.green(ink)+10)bluePixels++;
          }
          assertTrue("Selected row visibly renders its blue treatment",bluePixels>=20);
        }finally{selected.recycle();normal.recycle();}
        shot(f.a,"subtitle-english-selected-"+mode+"-412x915",412,915);
        assertSame(f.fake.player,get(f.a,"mPlayer"));call(f.a,"closeCobraActionSheet");
      }
      f.open();tapIcon(f.tag("cobra-track-off"),false);f.ui.frames(2);
      assertTrue(f.fake.params.disabledTrackTypes.contains(androidx.media3.common.C.TRACK_TYPE_TEXT));
      assertEquals(View.GONE,f.captions().getVisibility());
    }finally{f.after();}
  }
}
