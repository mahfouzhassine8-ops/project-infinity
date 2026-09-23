package com.projectinfinity.kodi;
import android.app.Application;
import androidx.media3.exoplayer.ExoPlayer;
import java.util.*;
import org.junit.*;import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Same actual ownership operations on exact 229 and candidate; no provider/decoder claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103230OwnershipProofTest {
  Cobra2103230RegressionProofTest f;InfinityLiveActivity a;
  Object get(Object o,String n)throws Exception{return Cobra2103230RegressionProofTest.get(o,n);}
  Object call(Object o,String n,Object...args)throws Exception{return Cobra2103230RegressionProofTest.call(o,n,args);}
  @Before public void before()throws Exception{f=new Cobra2103230RegressionProofTest();f.before();a=f.a;f.grid();call(a,"cobraPromoteMultiTileFullscreen","audit:0");}
  @After public void after()throws Exception{
    if(a!=null)for(Object p:new ArrayList<>(((Map<?,?>)get(a,"mCobraPlayerBindings")).keySet()))call(a,"cobraDisposePlayer",p);
    if(f!=null)f.after();
  }
  @Test public void promotedManualRestartKeepsTileRegistryAndReturnCoherent()throws Exception{
    String key=(String)call(a,"cobraPreferenceKey",f.channels[0]);call(a,"cobraRestartLiveChannel",f.channels[0],key);
    ExoPlayer current=(ExoPlayer)get(a,"mPlayer");assertNotNull(current);assertNotSame(f.players[0].player,current);
    assertSame("Restart must update the promoted tile registry",current,get(f.tiles[0],"player"));
    assertEquals(0,f.players[1].releases);assertEquals(0,f.players[1].prepares);assertEquals(true,call(a,"cobraReturnToMultiFromFullscreen"));
    assertSame(current,((ExoPlayer[])get(a,"mMultiPlayers"))[0]);
  }
  @Test public void promotedRecallOfPeerReusesBothSessionsAndKeepsMultiView()throws Exception{
    call(a,"playChannel",f.channels[1]);assertNotNull("Explicit recall must retain Multi-View",get(a,"mMultiOverlay"));
    assertSame(f.players[1].player,get(a,"mPlayer"));assertEquals(0,f.players[0].releases);assertEquals(0,f.players[1].releases);
    assertEquals(0,f.players[0].prepares);assertEquals(0,f.players[1].prepares);assertEquals(true,call(a,"cobraReturnToMultiFromFullscreen"));
  }
  @Test @SuppressWarnings("unchecked") public void promotedNewChannelReplacesOnlyTheSelectedTile()throws Exception{
    Object next=CobraNavigationUiTest.construct("Channel","audit:2","Audit 2","Test","epg2","","https://example.invalid/live/primary2","",Collections.emptyMap());
    ((List<Object>)get(a,"mChannels")).add(next);call(a,"playChannel",next);
    assertEquals("Healthy peer must survive explicit channel replacement",0,f.players[1].releases);assertEquals(0,f.players[1].prepares);
    Object tile=call(get(a,"mCobraTiles"),"get","audit:2");assertNotNull(tile);assertSame(get(a,"mPlayer"),get(tile,"player"));
    assertEquals(2,((ExoPlayer[])get(a,"mMultiPlayers")).length);assertEquals(true,call(a,"cobraReturnToMultiFromFullscreen"));
  }
}
