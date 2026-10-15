package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual bounded persistence and admission policies; no provider/decoder/device claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205SessionPolicyTest {
  SharedPreferences prefs;final long now=1900000000000L;
  @Before public void setup(){prefs=RuntimeEnvironment.getApplication().getSharedPreferences("cobra205-session-policy",0);prefs.edit().clear().commit();}
  CobraSmartReturn.Snapshot snapshot(){CobraSmartReturn.Snapshot s=new CobraSmartReturn.Snapshot();s.profile="profile-a";s.savedAt=now;s.source="source-one";s.channel="source-one:17";s.selected="source-one:18";s.mode="grid";s.category="News";s.route="channels";s.playback="fullscreen";s.requested=false;s.guideWindow=now;s.scroll.put("grid|source-one|News",new int[]{17,-12});s.focus.put("grid|source-one|News","cobra-channel:source-one:18");return s;}
  CobraSmartReturn.Snapshot round(CobraSmartReturn.Snapshot s){return CobraSmartReturn.decode(CobraSmartReturn.encode(s),"profile-a",now);}
  CobraQuickPeekSession.Capacity capacity(String maximum,String active)throws Exception{return CobraQuickPeekSession.Capacity.from(new JSONObject().put("max_connections",maximum).put("active_cons",active),now);}

  @Test public void smartReturnDefaultsOffAndDoesNotWriteSnapshot(){CobraSmartReturn.save(prefs,"a",snapshot());assertFalse(CobraSmartReturn.enabled(prefs));assertFalse(prefs.contains("a"));}
  @Test public void storesAndRecoversChannelSelectionModeAndGuidePosition(){CobraSmartReturn.Snapshot s=round(snapshot());assertNotNull(s);assertEquals("source-one:17",s.channel);assertEquals("source-one:18",s.selected);assertEquals("grid",s.mode);assertArrayEquals(new int[]{17,-12},s.scroll.get("grid|source-one|News"));assertEquals("cobra-channel:source-one:18",s.focus.get("grid|source-one|News"));}
  @Test public void pausedIntentNeverDefaultsToPlaying(){assertFalse(round(snapshot()).requested);assertFalse(CobraSmartReturn.decode("{\"schema\":1,\"profile\":\"profile-a\",\"saved\":"+now+"}","profile-a",now).requested);}
  @Test public void snapshotsAreIsolatedByActiveProfile(){assertNull(CobraSmartReturn.decode(CobraSmartReturn.encode(snapshot()),"profile-b",now));}
  @Test public void expiredAndFutureSnapshotsAreRejected(){String s=CobraSmartReturn.encode(snapshot());assertNull(CobraSmartReturn.decode(s,"profile-a",now+CobraSmartReturn.MAX_AGE_MS+1));assertNull(CobraSmartReturn.decode(s,"profile-a",now-60001));}
  @Test public void corruptUnknownSchemaAndOversizedSnapshotsAreRejected(){assertNull(CobraSmartReturn.decode("not-json","profile-a",now));assertNull(CobraSmartReturn.decode("{\"schema\":9}","profile-a",now));assertNull(CobraSmartReturn.decode(new String(new char[CobraSmartReturn.MAX_BYTES+1]),"profile-a",now));}
  @Test public void malformedPreferenceTypeDoesNotCrashStartup(){prefs.edit().putInt(CobraSmartReturn.ENABLED,4).commit();assertFalse(CobraSmartReturn.enabled(prefs));prefs.edit().putBoolean(CobraSmartReturn.ENABLED,true).putInt("state",2).commit();assertNull(CobraSmartReturn.read(prefs,"state","profile-a",now));}
  @Test public void turnOffPreservesPreviousSnapshotAndUnrelatedData(){prefs.edit().putBoolean(CobraSmartReturn.ENABLED,true).putString("theme","keep").commit();CobraSmartReturn.save(prefs,"a",snapshot());String saved=prefs.getString("a","");prefs.edit().putBoolean(CobraSmartReturn.ENABLED,false).commit();CobraSmartReturn.save(prefs,"a",new CobraSmartReturn.Snapshot());assertEquals(saved,prefs.getString("a",""));assertEquals("keep",prefs.getString("theme",""));assertNull(CobraSmartReturn.read(prefs,"a","profile-a",now));}
  @Test public void positionInventoryAndIndexesAreBounded(){CobraSmartReturn.Snapshot s=snapshot();s.scroll.clear();for(int i=0;i<100;i++)s.scroll.put("key"+i,new int[]{Integer.MAX_VALUE,Integer.MIN_VALUE});CobraSmartReturn.Snapshot copy=round(s);assertEquals(32,copy.scroll.size());assertArrayEquals(new int[]{50000,-10000},copy.scroll.get("key0"));}
  @Test public void unknownModeAndUnsafeDestinationDoNotEnterArbitraryRoutes()throws Exception{JSONObject j=new JSONObject(CobraSmartReturn.encode(snapshot())).put("mode","unknown");assertNull(CobraSmartReturn.decode(j.toString(),"profile-a",now));assertEquals("guide",CobraSmartReturn.destination("content://anything"));}
  @Test public void myListHasItsOwnSemanticDestination(){CobraSmartReturn.Snapshot s=snapshot();s.destination="watchlist";assertEquals("watchlist",round(s).destination);}
  @Test public void staleGuideWindowResetsWithoutChangingChannel(){CobraSmartReturn.Snapshot s=snapshot();s.guideWindow=now-2*24*3600000L;CobraSmartReturn.Snapshot copy=round(s);assertEquals(0,copy.guideWindow);assertEquals(s.channel,copy.channel);}
  @Test public void schemaContainsNoTransportOrCredentialFields()throws Exception{JSONObject j=new JSONObject(CobraSmartReturn.encode(snapshot()));for(String key:new String[]{"url","primary_url","headers","password","username","seek_ms","timeshift_offset","token"})assertFalse(j.has(key));}
  @Test public void restoreGateOffersSnapshotOnlyOnce(){CobraSmartReturn.Gate gate=new CobraSmartReturn.Gate(snapshot(),7);assertNotNull(gate.take("profile-a",7));assertNull(gate.take("profile-a",7));}
  @Test public void realUserInteractionCancellationCannotBeRearmedByLoading(){CobraSmartReturn.Gate gate=new CobraSmartReturn.Gate(snapshot(),7);gate.cancel();gate.loading(9);assertFalse(gate.pending());assertNull(gate.take("profile-a",9));}
  @Test public void navigationEpochAndProfileChangesDiscardPendingRestore(){CobraSmartReturn.Gate gate=new CobraSmartReturn.Gate(snapshot(),7);assertNull(gate.take("profile-a",8));assertNull(gate.take("profile-a",7));assertNull(new CobraSmartReturn.Gate(snapshot(),7).take("profile-b",7));}
  @Test public void expectedBootstrapLoadingCanAdvanceGateEpoch(){CobraSmartReturn.Gate gate=new CobraSmartReturn.Gate(snapshot(),7);gate.loading(8);assertNotNull(gate.take("profile-a",8));}
  @Test public void unknownCapacityBlocksAnySameSourcePlayback(){assertFalse(CobraQuickPeekSession.capacityAllows(null,1,now));assertFalse(CobraQuickPeekSession.capacityAllows(null,4,now));assertTrue(CobraQuickPeekSession.capacityAllows(null,0,now));}
  @Test public void exhaustedProviderOrLocalCountBlocksPreview()throws Exception{assertFalse(CobraQuickPeekSession.capacityAllows(capacity("2","2"),1,now));assertFalse(CobraQuickPeekSession.capacityAllows(capacity("2","0"),2,now));}
  @Test public void freshSpareCapacityAllowsExactlyOnePreview()throws Exception{assertTrue(CobraQuickPeekSession.capacityAllows(capacity("2","1"),1,now));}
  @Test public void staleFutureAndUnknownActiveCapacityCannotRiskMain()throws Exception{CobraQuickPeekSession.Capacity c=capacity("3","0");assertFalse(CobraQuickPeekSession.capacityAllows(c,1,now+CobraQuickPeekSession.CAPACITY_MAX_AGE_MS+1));assertFalse(CobraQuickPeekSession.capacityAllows(c,1,now-1));assertFalse(CobraQuickPeekSession.capacityAllows(capacity("3",""),1,now));}
  @Test public void malformedUnlimitedAndNegativeCapacityAreNotAssumedSafe()throws Exception{for(String value:new String[]{"","-1","0","unlimited","999999999999"})assertNull(capacity(value,"0"));assertFalse(CobraQuickPeekSession.capacityAllows(capacity("3","1"),-1,now));}
}
