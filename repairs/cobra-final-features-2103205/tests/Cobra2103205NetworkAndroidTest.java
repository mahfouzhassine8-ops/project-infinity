package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.net.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.*;
import static org.junit.Assert.*;

/** Production callback adapter with Android shadows, not actual Wi-Fi/cellular/VPN acceptance. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205NetworkAndroidTest {
  Application app;ConnectivityManager manager;ShadowConnectivityManager shadow;
  @Before public void setup(){
    app=RuntimeEnvironment.getApplication();manager=(ConnectivityManager)app.getSystemService(Context.CONNECTIVITY_SERVICE);
    shadow=Shadows.shadowOf(manager);shadow.clearAllNetworks();shadow.setActiveNetworkInfo(null);
  }
  static NetworkCapabilities caps(int transport,boolean valid){
    NetworkCapabilities value=ShadowNetworkCapabilities.newInstance();ShadowNetworkCapabilities shadow=Shadows.shadowOf(value);
    shadow.addTransportType(transport);shadow.addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
    if(valid)shadow.addCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);return value;
  }
  ConnectivityManager.NetworkCallback only(){assertEquals(1,shadow.getNetworkCallbacks().size());return shadow.getNetworkCallbacks().iterator().next();}

  @Test public void registersExactlyOnceAndUnregistersDespiteRepeatedClose(){
    CobraNetworkIntelligence observer=new CobraNetworkIntelligence(app);observer.start();observer.start();only();
    observer.close();observer.close();observer.start();assertTrue(shadow.getNetworkCallbacks().isEmpty());
    assertEquals("Closed",observer.snapshot().observation);
  }
  @Test public void usesCallbackCapabilitiesEvenWhenSynchronousManagerSnapshotIsEmpty(){
    CobraNetworkIntelligence observer=new CobraNetworkIntelligence(app);try{
      observer.start();ConnectivityManager.NetworkCallback callback=only();Network wifi=ShadowNetwork.newInstance(31);
      callback.onAvailable(wifi);assertEquals("Connecting",observer.snapshot().status);
      callback.onCapabilitiesChanged(wifi,caps(NetworkCapabilities.TRANSPORT_WIFI,true));
      assertEquals(CobraNetworkIntelligence.WIFI,observer.snapshot().transportBits);assertTrue(observer.snapshot().validated);
      assertNull(manager.getActiveNetwork());
    }finally{observer.close();}
  }
  @Test public void staleOldNetworkLossDoesNotMarkCellularOfflineAndLateCloseCallbacksAreIgnored(){
    CobraNetworkIntelligence observer=new CobraNetworkIntelligence(app);observer.start();ConnectivityManager.NetworkCallback callback=only();
    Network wifi=ShadowNetwork.newInstance(31),cell=ShadowNetwork.newInstance(32);
    callback.onAvailable(wifi);callback.onCapabilitiesChanged(wifi,caps(NetworkCapabilities.TRANSPORT_WIFI,true));
    callback.onAvailable(cell);callback.onCapabilitiesChanged(cell,caps(NetworkCapabilities.TRANSPORT_CELLULAR,true));callback.onLost(wifi);
    assertTrue(observer.snapshot().connected);assertEquals(CobraNetworkIntelligence.CELLULAR,observer.snapshot().transportBits);
    long changes=observer.snapshot().transitions;observer.close();callback.onLost(cell);callback.onAvailable(wifi);
    assertEquals(changes,observer.snapshot().transitions);assertEquals(CobraNetworkIntelligence.CELLULAR,observer.snapshot().transportBits);
  }
  @Test public void passiveObservationDoesNotWritePreferencesOrBindRouting()throws Exception{
    SharedPreferences prefs=app.getSharedPreferences("cobra_provider_network",Context.MODE_PRIVATE);
    prefs.edit().putInt("family",6).putString("user_value","preserve").commit();Map<String,?> before=new HashMap<>(prefs.getAll());
    CobraNetworkIntelligence observer=new CobraNetworkIntelligence(app);try{
      observer.start();ConnectivityManager.NetworkCallback callback=only();Network wifi=ShadowNetwork.newInstance(7);
      callback.onAvailable(wifi);callback.onCapabilitiesChanged(wifi,caps(NetworkCapabilities.TRANSPORT_WIFI,false));
      observer.snapshot().json();callback.onLost(wifi);assertEquals(before,prefs.getAll());
      assertNull(manager.getBoundNetworkForProcess());assertTrue(shadow.getReportedNetworkConnectivity().isEmpty());
    }finally{observer.close();}
  }
  @Test public void unavailableServiceIsExplicitAndDoesNotPreventStartup()throws Exception{
    CobraNetworkIntelligence observer=new CobraNetworkIntelligence(null);observer.start();
    assertEquals("Unavailable",observer.snapshot().observation);assertFalse(observer.snapshot().known);
    assertTrue(observer.snapshot().json().isNull("connected"));observer.close();
  }
  @Implements(ConnectivityManager.class) public static class RegistrationFailure extends ShadowConnectivityManager {
    @Implementation protected void registerDefaultNetworkCallback(ConnectivityManager.NetworkCallback callback){throw new SecurityException("Synthetic registration denial");}
  }
  @Config(shadows=RegistrationFailure.class) @Test public void callbackRegistrationFailureRemainsSnapshotOnlyAndDoesNotLeak(){
    CobraNetworkIntelligence observer=new CobraNetworkIntelligence(app);observer.start();observer.start();
    assertTrue(observer.snapshot().observation.contains("callback unavailable"));assertTrue(shadow.getNetworkCallbacks().isEmpty());
    observer.close();assertTrue(shadow.getNetworkCallbacks().isEmpty());
  }
}
