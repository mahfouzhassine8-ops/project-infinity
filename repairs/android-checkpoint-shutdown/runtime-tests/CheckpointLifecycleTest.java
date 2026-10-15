package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.ComponentName;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
public class CheckpointLifecycleTest {
  @Test public void failedLiveOwnerOffersRecoveryWithoutAuthorizingRelaunch(){
    InfinityKodiShutdown.Snapshot failed=new InfinityKodiShutdown.Snapshot(42,"owner","launch","save failed",1,2,
        InfinityExitCompletion.Plan.Phase.CHECKPOINT_FAILED,true,false,false);
    assertTrue(failed.pending());assertTrue(failed.stalled());assertTrue(failed.checkpointFailed());
    assertFalse(failed.complete);assertTrue(failed.closeTitle().contains("failed"));
    assertFalse(failed.closeNotice().contains("finishing"));assertTrue(failed.closeMessage().contains("Waiting will not"));
  }
  @Test public void retiredFailedOwnerDoesNotBecomeSavedOrBlockFreshLaunch(){
    InfinityKodiShutdown.Snapshot dead=new InfinityKodiShutdown.Snapshot(42,"owner","launch","save failed",1,2,
        InfinityExitCompletion.Plan.Phase.CHECKPOINT_FAILED,false,false,false);
    assertFalse(dead.pending());assertFalse(dead.stalled());assertFalse(dead.complete);
  }
  @Test public void closeDestinationIsAndroidHome(){
    Intent intent=InfinityCloseGuardService.homeIntent();
    assertEquals(Intent.ACTION_MAIN,intent.getAction());assertTrue(intent.hasCategory(Intent.CATEGORY_HOME));
    assertNull(intent.getComponent());assertEquals(Intent.FLAG_ACTIVITY_NEW_TASK,intent.getFlags());
  }
  @Test public void mainTaskIsVisibleAndRestorationDoesNotFinishIt()throws Exception{
    ActivityInfo info=RuntimeEnvironment.getApplication().getPackageManager().getActivityInfo(
        new ComponentName("com.projectinfinity.kodi","com.projectinfinity.kodi.Main"),0);
    assertEquals("com.projectinfinity.kodi.infinity.kodi",info.taskAffinity);
    assertEquals(0,info.flags&ActivityInfo.FLAG_EXCLUDE_FROM_RECENTS);
    assertEquals(0,info.flags&ActivityInfo.FLAG_FINISH_ON_TASK_LAUNCH);
    assertEquals(ActivityInfo.LAUNCH_SINGLE_INSTANCE,info.launchMode);
    assertEquals("com.projectinfinity.kodi:kodi",info.processName);
  }
  @Test public void successfulChooserHandoffRemovesItsOwnSingleInstanceTask(){
    final boolean[] removed={false},plainFinished={false};
    Activity chooser=new Activity(){
      @Override public void finishAndRemoveTask(){removed[0]=true;}
      @Override public void finish(){plainFinished[0]=true;}
    };
    Splash.finishSuccessfulExperienceHandoff(chooser);
    assertTrue(removed[0]);assertFalse(plainFinished[0]);
  }

  @Test public void mainHandoffStripsExclusionButKeepsDeepLinkAndLiveTask(){
    Activity activity=Robolectric.buildActivity(Activity.class).create().get();
    Intent input=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("content://example/movie"))
        .addFlags(Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS|Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|
                  Intent.FLAG_GRANT_READ_URI_PERMISSION).putExtra("example","preserved");
    for(boolean live:new boolean[]{false,true}){
      Intent output=InfinityStartupHandoff.mainIntent(activity,input,live);
      assertEquals(0,output.getFlags()&Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS);
      assertEquals(0,output.getFlags()&Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
      assertNotEquals(0,output.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION);
      assertEquals(input.getData(),output.getData());assertEquals("preserved",output.getStringExtra("example"));
      assertEquals(!live,(output.getFlags()&Intent.FLAG_ACTIVITY_CLEAR_TASK)!=0);
    }
    assertNotEquals(0,input.getFlags()&Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS);
  }
}
