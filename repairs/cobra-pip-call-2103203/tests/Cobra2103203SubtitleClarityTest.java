package com.projectinfinity.kodi;

import android.app.Application;
import androidx.media3.common.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Current-selection versus saved-preference copy with controlled detected tracks. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103203SubtitleClarityTest {
  Cobra2103201SubtitleTest f;
  @Before public void before()throws Exception{f=new Cobra2103201SubtitleTest();f.before();}
  @After public void after()throws Exception{if(f!=null)f.after();}
  void englishPreference()throws Exception{String key=(String)f.call(f.a,"cobraPreferenceKey",f.channel);Object prefs=f.call(f.a,"cobraReadPreferences",key);f.put(prefs,"subtitles","en");assertEquals(true,f.call(f.a,"cobraSavePreferences",f.channel,key,prefs,false));}
  @Test public void checkedOffExplainsActualPlaybackWhileEnglishRemainsSaved()throws Exception{
    englishPreference();f.call(f.a,"cobraSetCaptionsEnabled",f.fake.player,false);f.tracks(Cobra2103201SubtitleTest.group("audio","audio/mp4a-latm","und",true,true));f.open();
    assertTrue(f.tag("cobra-track-off").isSelected());assertNotNull(f.text(f.root(),"Off is selected for this playback"));assertNotNull(f.text(f.root(),"Saved preference: English • when available"));
    assertNotNull(f.text(f.root(),"No subtitle tracks detected in this playback session."));assertNull(f.text(f.root(),"No subtitle tracks available in this stream."));
    Cobra2103201MenuPolishTest.capture(f.a,f.ui,"cobra203-subtitle-off-preference-412x915",412,915);
  }
  @Test public void enabledPreferenceWithoutDetectedTrackDoesNotFalselySelectOff()throws Exception{
    englishPreference();f.tracks(Cobra2103201SubtitleTest.group("audio","audio/mp4a-latm","und",true,true));f.open();assertFalse(f.tag("cobra-track-off").isSelected());assertNotNull(f.text(f.root(),"No subtitle tracks detected in this playback session."));assertNull(f.text(f.root(),"English"));
  }
  @Test public void lateDetectedTrackReplacesAbsenceMessageButNotSavedPreference()throws Exception{
    englishPreference();f.open();f.tracks(Cobra2103201SubtitleTest.group("english","text/vtt","en",true,true));f.call(f.binding,"onTracksChanged",f.fake.tracks);f.ui.measure(f.a,412,915);
    assertNull(f.text(f.root(),"No subtitle tracks detected in this playback session."));assertNotNull(f.text(f.root(),"English"));assertTrue(f.tag("cobra-track:0:0").isSelected());assertNotNull(f.text(f.root(),"Saved preference: English • when available"));
    Cobra2103201MenuPolishTest.capture(f.a,f.ui,"cobra203-subtitle-english-selected-412x915",412,915);
  }
  @Test public void detectedUnsupportedTrackStillUsesUnsupportedExplanation()throws Exception{
    f.tracks(Cobra2103201SubtitleTest.group("english","text/vtt","en",false,false));f.open();assertNotNull(f.text(f.root(),"Subtitle tracks are present but unsupported on this player."));assertNull(f.text(f.root(),"No subtitle tracks detected in this playback session."));assertNull(f.tag("cobra-track:0:0"));
  }
}
