package com.projectinfinity.kodi;

import org.junit.Test;
import static org.junit.Assert.*;

/** Exact production state machine with synthetic Android routing events; not device/network proof. */
public class Cobra2103205NetworkPolicyTest {
  private final CobraNetworkIntelligence.State state=new CobraNetworkIntelligence.State();
  private final Object wifi=new Object(),cell=new Object();
  private void ready(Object key,int bits,boolean metered,long now){
    state.available(key,now);state.capabilities(key,bits,true,true,true,true,metered,false,now);
  }
  private CobraNetworkIntelligence.Snapshot at(long time){return state.snapshot(time,"test observation");}

  @Test public void unknownIsNotClaimedOfflineOrConnected()throws Exception{
    assertEquals("Not reported",at(0).status);assertFalse(at(0).known);
    assertTrue(at(0).json().isNull("connected"));assertTrue(at(0).json().isNull("internet_validated"));
    assertTrue(at(0).json().isNull("metered"));assertEquals(-1,at(0).changedAgeMs);
  }
  @Test public void availableWaitsForCapabilitiesWithoutInventingInternet(){
    state.available(wifi,100);assertEquals("Connecting",at(100).status);
    assertEquals("Not reported",CobraNetworkIntelligence.transportLabel(at(100).transportBits));
    assertFalse(at(100).validatedKnown);
  }
  @Test public void wifiCanBeMeteredAndCellularCanBeUnmetered(){
    ready(wifi,CobraNetworkIntelligence.WIFI,true,0);assertTrue(at(0).metered);
    assertTrue(at(0).summary().contains("Wi-Fi • Connected • Metered"));
    ready(cell,CobraNetworkIntelligence.CELLULAR,false,1000);assertFalse(at(1000).metered);
    assertEquals(1,at(1000).transitions);assertEquals(0,at(1000).reconnections);
  }
  @Test public void vpnRetainsReportedUnderlyingTransport(){
    ready(wifi,CobraNetworkIntelligence.VPN|CobraNetworkIntelligence.WIFI,false,0);
    assertEquals("VPN + Wi-Fi",CobraNetworkIntelligence.transportLabel(at(0).transportBits));
  }
  @Test public void outageThenValidatedReturnReportsAndExpiresRecovery(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,0);state.lost(wifi,1000);
    assertEquals("No default network",at(1000).status);assertEquals(1,at(1000).disconnects);
    ready(cell,CobraNetworkIntelligence.CELLULAR,true,2000);
    assertEquals("Reconnected",at(2000).status);assertEquals(1,at(2000).reconnections);
    assertEquals("Connected",at(12000).status);assertEquals(10000,at(12000).recoveryAgeMs);
  }
  @Test public void oldNetworkLossAndCapabilitiesCannotOverwriteNewDefault(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,0);ready(cell,CobraNetworkIntelligence.CELLULAR,true,1000);
    state.lost(wifi,1100);state.capabilities(wifi,CobraNetworkIntelligence.WIFI,true,true,false,true,false,true,1200);
    assertTrue(at(1300).connected);assertTrue(at(1300).validated);
    assertEquals(CobraNetworkIntelligence.CELLULAR,at(1300).transportBits);
    assertEquals(0,at(1300).disconnects);assertEquals(1,at(1300).transitions);
  }
  @Test public void repeatedIdenticalCallbacksAndCostChangesDoNotInflateInstability(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,0);
    for(int i=1;i<=10000;i++)ready(wifi,CobraNetworkIntelligence.WIFI,i%2==0,i);
    assertEquals(0,at(10000).transitions);assertEquals(0,at(10000).recentChanges);
  }
  @Test public void validationLossAndRecoveryAreNotATransportSpeedAssumption(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,0);
    state.capabilities(wifi,CobraNetworkIntelligence.WIFI,true,true,false,true,false,false,1000);
    assertEquals("Internet not validated",at(1000).status);
    state.capabilities(wifi,CobraNetworkIntelligence.WIFI,true,true,true,true,false,false,2000);
    assertEquals("Reconnected",at(2000).status);assertEquals(1,at(2000).reconnections);
  }
  @Test public void captivePortalIsNotPresentedAsRecovery(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,0);state.lost(wifi,100);
    state.available(cell,200);state.capabilities(cell,CobraNetworkIntelligence.WIFI,true,true,false,true,false,true,200);
    assertEquals("Sign-in may be required",at(200).status);assertEquals(0,at(200).reconnections);
  }
  @Test public void frequentChangesUseABoundedRollingWindow(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,0);
    for(int i=1;i<=10000;i++)ready(i%2==0?wifi:cell,i%2==0?CobraNetworkIntelligence.WIFI:CobraNetworkIntelligence.CELLULAR,false,i);
    assertEquals(10000,at(10000).transitions);assertEquals(8,at(10000).recentChanges);
    assertEquals("Frequent route changes",at(10000).status);
    assertEquals(0,at(40000).recentChanges);assertEquals("Connected",at(40000).status);
  }
  @Test public void unknownValidationRemainsUnknownInDiagnostics()throws Exception{
    state.available(wifi,0);state.capabilities(wifi,CobraNetworkIntelligence.WIFI,true,false,false,true,true,false,0);
    assertEquals("Connected",at(0).status);assertTrue(at(0).json().isNull("internet_validated"));
  }
  @Test public void clockRollbackDoesNotCreateNegativeOrPermanentInstability(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,1000);state.lost(wifi,2000);ready(cell,CobraNetworkIntelligence.CELLULAR,false,3000);
    ready(cell,CobraNetworkIntelligence.CELLULAR,false,100);
    assertEquals(0,at(100).recentChanges);assertEquals(-1,at(100).recoveryAgeMs);assertEquals(-1,at(100).changedAgeMs);
  }
  @Test public void closeIgnoresLateCallbacksAndOpaqueIdentityIsNeverExported()throws Exception{
    Object privateKey=new Object(){@Override public String toString(){throw new AssertionError("Network identity escaped");}};
    ready(privateKey,CobraNetworkIntelligence.WIFI,false,0);state.close();
    state.lost(privateKey,100);state.available(cell,200);state.unavailable(300);
    String json=at(400).json().toString();assertTrue(at(400).connected);assertEquals(0,at(400).transitions);
    assertFalse(json.contains("SSID"));assertFalse(json.contains("http"));assertTrue(json.contains("observation_only"));
  }
  @Test public void failedReadBecomesUnknownWithoutInventingAnOutage(){
    ready(wifi,CobraNetworkIntelligence.WIFI,false,0);state.unavailable(100);
    assertEquals("Not reported",at(100).status);assertFalse(at(100).known);assertEquals(0,at(100).disconnects);
  }
}
