package com.projectinfinity.kodi;

import android.app.Application;
import android.content.*;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.common.text.*;
import java.time.Duration;
import java.util.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Activity rows, Android touch dispatch and caption canvas; controlled tracks, no decoder/device claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103202ControlsTest {
  Cobra2103201SubtitleTest f;InfinityLiveActivity a;SharedPreferences prefs;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  Object call(String n,Object...args)throws Exception{return CobraNavigationUiTest.call(a,n,args);}
  @Before public void before()throws Exception{f=new Cobra2103201SubtitleTest();f.before();a=f.a;prefs=(SharedPreferences)get(a,"mPrefs");}
  @After public void after()throws Exception{if(f!=null)f.after();}
  View tag(String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  void layout()throws Exception{f.ui.measure(a,412,915);f.ui.frames(20);}
  String key()throws Exception{return (String)call("cobraPreferenceKey",f.channel);}
  void open()throws Exception{call("showTrackChooser");layout();}
  void touchIcon(View row,boolean cancel){assertTrue(row instanceof ViewGroup);View icon=((ViewGroup)row).getChildAt(0);float x=icon.getLeft()+icon.getWidth()/2f,y=icon.getTop()+icon.getHeight()/2f;long t=SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(t,t,MotionEvent.ACTION_DOWN,x,y,0),up=MotionEvent.obtain(t,t+30,cancel?MotionEvent.ACTION_CANCEL:MotionEvent.ACTION_UP,x,y,0);try{assertTrue(row.dispatchTouchEvent(down));row.dispatchTouchEvent(up);}finally{down.recycle();up.recycle();}Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(40));}
  void save(String field,String value)throws Exception{Object p=call("cobraReadPreferences",key());put(p,field,value);assertEquals(true,call("cobraSavePreferences",f.channel,key(),p,false));}

  @Test public void languagePreferencesLiveOnlyInsideAudioAndSubtitles()throws Exception{
    call("cobraShowChannelPreferences",f.channel);layout();
    for(String value:new String[]{"cobra-channel-aspect","cobra-channel-audio","cobra-channel-subtitles"})assertNull(tag(value));
    for(String value:new String[]{"cobra-channel-recents","cobra-channel-restart-live","cobra-channel-pip","cobra-channel-background","cobra-channel-rewind","cobra-channel-reset","cobra-channel-fallback","cobra-channel-recovery"})assertNotNull(value,tag(value));
    Cobra2103201MenuPolishTest.capture(a,f.ui,"cobra202-channel-playback-412x915",412,915);
    open();assertNotNull(tag("cobra-channel-audio"));assertNotNull(tag("cobra-channel-subtitles"));
    assertNotNull(tag("cobra-subtitle-size"));assertNotNull(tag("cobra-subtitle-adaptation"));
    Cobra2103201MenuPolishTest.capture(a,f.ui,"cobra202-audio-subtitles-412x915",412,915);
  }
  @Test public void preferredAudioPersistsAndReturnsToCombinedMenu()throws Exception{
    call("cobraShowChannelLanguage",f.channel,false);layout();tag("cobra-channel-language:en").performClick();layout();
    assertEquals("en",new JSONObject(prefs.getString(key(),"")).getString("audio"));assertEquals("tracks",get(a,"mCobraSheetKind"));assertEquals(Collections.singletonList("en"),f.fake.params.preferredAudioLanguages);
  }
  @Test public void preferredSubtitlesPersistsAndReturnsToCombinedMenu()throws Exception{
    call("cobraShowChannelLanguage",f.channel,true);layout();tag("cobra-channel-language:en").performClick();layout();
    assertEquals("en",new JSONObject(prefs.getString(key(),"")).getString("subtitles"));assertEquals("tracks",get(a,"mCobraSheetKind"));assertEquals(Collections.singletonList("en"),f.fake.params.preferredTextLanguages);
  }
  @Test public void changingAudioPreferenceDoesNotTurnOffManuallySelectedSubtitles()throws Exception{
    save("subtitles","off");Tracks.Group english=Cobra2103201SubtitleTest.group("english","text/vtt","en",true,false);f.tracks(english);open();tag("cobra-track:0:0").performClick();
    save("audio","fr");assertFalse(f.fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertTrue(f.fake.params.overrides.containsKey(english.getMediaTrackGroup()));
  }
  @Test public void changingSubtitlePreferenceDoesNotReplaceManualAudioTrack()throws Exception{
    Tracks.Group audio=Cobra2103201SubtitleTest.group("audio","audio/mp4a-latm","es",true,false);f.tracks(audio);open();tag("cobra-track:0:0").performClick();save("subtitles","en");assertTrue(f.fake.params.overrides.containsKey(audio.getMediaTrackGroup()));
  }
  @Test public void subtitleOffIconWorksOnFirstTapAndClearsCues()throws Exception{
    f.tracks(Cobra2103201SubtitleTest.group("english","text/vtt","en",true,true));f.cue();open();touchIcon(tag("cobra-track-off"),false);
    assertTrue(f.fake.params.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT));assertEquals(View.GONE,f.captions().getVisibility());assertNull(get(a,"mCobraActionSheet"));
  }
  @Test public void subtitleCancelledTouchDoesNotChangeSelection()throws Exception{
    open();int before=f.fake.parameterWrites;touchIcon(tag("cobra-track-off"),true);assertEquals(before,f.fake.parameterWrites);assertNotNull(get(a,"mCobraActionSheet"));
  }
  @Test public void filePickerPolicyIconsPersistAllThreeChoices()throws Exception{
    for(String value:new String[]{"system","apps","ask"}){call("showCobraFilePickerPicker");layout();View row=tag("cobra-file-picker:"+value);assertNotNull(row);touchIcon(row,false);assertEquals(value,prefs.getString("cobra_file_picker_mode",""));}
  }
  @Test public void pipGlyphRendersAWindowInsteadOfTheUnknownIconFallback()throws Exception{
    View pip=(View)CobraNavigationUiTest.construct("CobraIconButton",a,"pip","Picture-in-picture",true),fallback=(View)CobraNavigationUiTest.construct("CobraIconButton",a,"unknown-test-icon","Unknown",true);
    Bitmap first=Bitmap.createBitmap(48,48,Bitmap.Config.ARGB_8888),second=Bitmap.createBitmap(48,48,Bitmap.Config.ARGB_8888);pip.layout(0,0,48,48);fallback.layout(0,0,48,48);pip.draw(new Canvas(first));fallback.draw(new Canvas(second));assertFalse("PiP must not draw the generic channel-list fallback",first.sameAs(second));first.recycle();second.recycle();
  }
  @Test public void systemPickerUsesDocumentContractAndReadPermission()throws Exception{
    prefs.edit().putString("cobra_file_picker_mode","system").commit();call("cobraOpenFilePicker",412,"*/*",new String[]{"video/*","audio/*"},true);
    Intent intent=Shadows.shadowOf(a).getNextStartedActivityForResult().intent;assertEquals(Intent.ACTION_OPEN_DOCUMENT,intent.getAction());assertTrue(intent.hasCategory(Intent.CATEGORY_OPENABLE));assertTrue((intent.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);assertTrue((intent.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)!=0);
  }
  @Test public void filesAppChoiceUsesAndroidChooserWithoutPretendingItsGrantPersists()throws Exception{
    prefs.edit().putString("cobra_file_picker_mode","apps").commit();call("cobraOpenFilePicker",412,"*/*",new String[]{"video/*"},true);
    Intent chooser=Shadows.shadowOf(a).getNextStartedActivityForResult().intent;assertEquals(Intent.ACTION_CHOOSER,chooser.getAction());Intent target=chooser.getParcelableExtra(Intent.EXTRA_INTENT);assertEquals(Intent.ACTION_GET_CONTENT,target.getAction());assertEquals(0,target.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
  }
  @Test public void recentsUsesExistingHistoryAndSkipsMissingChannels()throws Exception{
    List<String> recents=(List<String>)get(a,"mRecents");recents.clear();recents.add("missing");String id=(String)get(f.channel,"id");recents.add(id);call("cobraShowPlaybackRecents");layout();assertNull(tag("cobra-playback-recent:missing"));assertNotNull(tag("cobra-playback-recent:"+id));assertEquals(Arrays.asList("missing",id),recents);
  }
  @Test public void staleRestartCannotMutateCurrentPlayerOrPreferences()throws Exception{
    Map<String,?> before=new HashMap<>(prefs.getAll());call("cobraRestartLiveChannel",f.channel,"different-profile-key");assertSame(f.fake.player,get(a,"mPlayer"));assertEquals(before,prefs.getAll());
  }
  @Test public void subtitleSizePersistsAndActuallyChangesPaintSize()throws Exception{
    f.cue();View captions=f.captions();captions.layout(0,0,412,300);Bitmap image=Bitmap.createBitmap(412,300,Bitmap.Config.ARGB_8888);captions.draw(new Canvas(image));float before=((android.text.TextPaint)get(captions,"text")).getTextSize();
    call("cobraShowSubtitleSize");layout();Cobra2103201MenuPolishTest.capture(a,f.ui,"cobra202-subtitle-size-412x915",412,915);tag("cobra-subtitle-size:150").performClick();assertEquals(150,call("cobraSubtitleSize"));captions.layout(0,0,412,300);captions.draw(new Canvas(image));assertEquals(before*1.5f,((android.text.TextPaint)get(captions,"text")).getTextSize(),.01f);image.recycle();
    call("closeCobraActionSheet");open();assertNotNull(f.text(f.root(),"Extra large • 150%"));
  }
  @Test public void adaptiveBitmapCaptionFitsCompleteImageInsideShortViewport()throws Exception{
    View captions=f.captions();Bitmap cueImage=Bitmap.createBitmap(20,200,Bitmap.Config.ARGB_8888);cueImage.eraseColor(Color.GREEN);for(int x=0;x<20;x++){cueImage.setPixel(x,0,Color.RED);cueImage.setPixel(x,199,Color.BLUE);}
    Cue cue=new Cue.Builder().setBitmap(cueImage).setSize(.9f).build();CobraNavigationUiTest.call(f.binding,"onCues",new CueGroup(Collections.singletonList(cue),0));captions.layout(0,0,200,100);
    Bitmap rendered=Bitmap.createBitmap(200,100,Bitmap.Config.ARGB_8888);captions.draw(new Canvas(rendered));int minY=100,maxY=-1;for(int y=0;y<100;y++)for(int x=0;x<200;x++)if(Color.alpha(rendered.getPixel(x,y))>0){minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
    assertTrue(maxY>=minY);assertTrue("Caption must fit with space around it",maxY-minY+1<=88);assertTrue(maxY<100);rendered.recycle();cueImage.recycle();
  }
  @Test public void adaptationOptionPersistsAfterNavigation()throws Exception{
    call("cobraShowSubtitleAdaptation");layout();tag("cobra-subtitle-adaptation:false").performClick();assertEquals(false,call("cobraSubtitleAdaptive"));call("closeCobraActionSheet");open();assertNotNull(f.text(f.root(),"Off • use stream placement"));
  }
}
