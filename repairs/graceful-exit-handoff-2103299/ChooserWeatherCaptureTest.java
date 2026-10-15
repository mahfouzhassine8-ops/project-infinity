package com.projectinfinity.kodi;
import android.content.Context;
import android.widget.TextView;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35) @LooperMode(LooperMode.Mode.PAUSED)
public class ChooserWeatherCaptureTest {
  private Context app;
  private static final String REAL="{\"result\":{\"Weather.Location\":\"Configured city\",\"Weather.Temperature\":\"15°C\",\"Weather.Conditions\":\"Cloudy\"}}";
  @Before public void reset(){app=RuntimeEnvironment.getApplication();app.getSharedPreferences("infinity_chooser_weather",0).edit().clear().commit();Main.MainActivity=null;}
  @Test public void mainCaptureNeedsNoChooserViewAndColdChooserRetainsReading(){
    InfinityChooserWeather capture=new InfinityChooserWeather(app,null,()->REAL);
    assertTrue(capture.accept(REAL));capture.renderCached();capture.stop();
    TextView label=new TextView(app);InfinityChooserWeather chooser=new InfinityChooserWeather(app,label,()->null);chooser.renderCached();
    assertTrue(label.getText().toString().contains("Configured city"));assertTrue(label.getText().toString().contains("15°C"));
    assertTrue(label.getText().toString().contains("last known"));assertNull(Main.MainActivity);
  }
  @Test public void unavailableOrMalformedReadingNeverErasesRealCache(){
    TextView label=new TextView(app);InfinityChooserWeather w=new InfinityChooserWeather(app,label,()->null);
    assertTrue(w.accept(REAL));assertFalse(w.accept(null));assertFalse(w.accept("{}"));
    assertFalse(w.accept("{\"result\":{\"Weather.Location\":\"Other\",\"Weather.Temperature\":\"N/A\",\"Weather.Conditions\":\"Cloudy\"}}"));
    w.renderCached();assertTrue(label.getText().toString().contains("Configured city"));
  }
  @Test public void expiredReadingIsNotPresentedAsLive(){
    TextView label=new TextView(app);InfinityChooserWeather w=new InfinityChooserWeather(app,label,()->null);w.accept(REAL);
    w.cache.edit().putLong("timestamp",System.currentTimeMillis()-25*60*60*1000L).commit();w.renderCached();assertEquals("Weather unavailable",label.getText().toString());
  }
  @Test public void nullViewCaptureDoesNotLeakCallbacksAfterStop(){
    InfinityChooserWeather w=new InfinityChooserWeather(app,null,()->null);w.start();w.stop();
    assertFalse(w.started);assertNull(w.worker);assertFalse(w.inFlight);
  }
  @Test public void coldChooserDoesNotLoadOrStartKodiForWeather(){
    InfinityChooserWeather w=new InfinityChooserWeather(app,new TextView(app));
    assertNull(w.reader.read());assertNull(Main.MainActivity);
  }
}
