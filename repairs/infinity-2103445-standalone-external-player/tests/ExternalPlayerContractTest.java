package com.projectinfinity.kodi;
import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;
import android.os.Looper;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

@RunWith(RobolectricTestRunner.class) @Config(manifest=Config.NONE,sdk=35)
@LooperMode(LooperMode.Mode.PAUSED)
public class ExternalPlayerContractTest {
    Intent view(String uri,String type) { return new Intent(Intent.ACTION_VIEW).setDataAndType(Uri.parse(uri),type); }
    @Test public void videoSchemesReachIsolatedPlayerIncludingUnsupportedErrors() {
        for (String scheme:new String[]{"content","file","http","https","ftp"})
            assertTrue(ExternalVideoRoute.accepts(view(scheme+"://source/movie", "video/mp4")));
    }
    @Test public void ordinaryLauncherAndAudioImagesRemainOriginal() {
        assertFalse(ExternalVideoRoute.accepts(new Intent(Intent.ACTION_MAIN)));
        for (String type:new String[]{"audio/mp4","image/jpeg","text/html"})
            assertFalse(ExternalVideoRoute.accepts(view("content://source/movie.mp4",type)));
    }
    @Test public void missingMimeRequiresRecognizableVideoPath() {
        assertTrue(ExternalVideoRoute.accepts(view("https://example.org/movie.MP4?token=private",null)));
        assertTrue(ExternalVideoRoute.accepts(view("file:///sdcard/movie.mkv","application/octet-stream")));
        assertFalse(ExternalVideoRoute.accepts(view("content://source/opaque-id",null)));
        assertFalse(ExternalVideoRoute.accepts(view("https://example.org/watch?id=123",null)));
    }
    @Test public void shareMustBeSingleVideoStream() {
        Intent send=new Intent(Intent.ACTION_SEND).setType("video/mp4").putExtra(Intent.EXTRA_STREAM,Uri.parse("content://source/1"));
        assertTrue(ExternalVideoRoute.accepts(send));
        assertFalse(ExternalVideoRoute.accepts(new Intent(send).setAction(Intent.ACTION_SEND_MULTIPLE)));
        assertFalse(ExternalVideoRoute.accepts(new Intent(Intent.ACTION_SEND).setType("video/mp4")));
        assertFalse(ExternalVideoRoute.accepts(new Intent(send).setType("image/png")));
    }
    @Test public void malformedAndAbsentRequestsAreNotAccepted() {
        assertFalse(ExternalVideoRoute.accepts(null));
        assertFalse(ExternalVideoRoute.accepts(new Intent(Intent.ACTION_VIEW).setType("video/mp4")));
        assertFalse(ExternalVideoRoute.accepts(view("/relative/movie.mp4","video/mp4")));
    }
    @Test public void gatewayPreservesGrantsClipDataMimeAndExtrasWithoutTaskDestruction() {
        Activity activity=Robolectric.buildActivity(Activity.class).setup().get();
        Intent in=view("content://source/1","video/mp4");
        ClipData clip=ClipData.newRawUri("Source",in.getData());in.setClipData(clip);
        in.setFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                |Intent.FLAG_ACTIVITY_CLEAR_TASK|Intent.FLAG_ACTIVITY_MULTIPLE_TASK);
        in.putExtra("source.value","retained");
        ExternalVideoRoute.open(activity,in);
        Intent out=shadowOf(activity).getNextStartedActivity();
        assertEquals("com.projectinfinity.kodi.InfinityExternalPlayerActivity",out.getComponent().getClassName());
        assertEquals(in.getData(),out.getData());assertEquals(in.getType(),out.getType());
        assertEquals(in.getClipData().getItemCount(),out.getClipData().getItemCount());
        assertEquals(in.getClipData().getItemAt(0).getUri(),out.getClipData().getItemAt(0).getUri());
        assertEquals(in.getClipData().getDescription().getLabel(),out.getClipData().getDescription().getLabel());
        assertEquals(in.getClipData().getDescription().getMimeType(0),out.getClipData().getDescription().getMimeType(0));
        assertEquals("retained",out.getStringExtra("source.value"));
        assertTrue((out.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
        assertEquals(0,out.getFlags()&(Intent.FLAG_ACTIVITY_CLEAR_TASK|Intent.FLAG_ACTIVITY_MULTIPLE_TASK));
        assertTrue(activity.isFinishing());assertNull(shadowOf(activity).getNextStartedActivity());
        assertNull(in.getStringExtra("infinity.external.request"));
    }
    @Test public void repeatedSameFileHasNewRequestIdentity() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        Intent in=view("content://source/same","video/mp4");
        ExternalVideoRoute.open(a,in);String first=shadowOf(a).getNextStartedActivity().getStringExtra("infinity.external.request");
        ExternalVideoRoute.open(a,in);String next=shadowOf(a).getNextStartedActivity().getStringExtra("infinity.external.request");
        assertNotEquals(first,next);
    }
    @Test public void sharedUriGetsReadGrantClipDataAndViewNormalization() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        Uri uri=Uri.parse("content://source/shared");
        Intent in=new Intent(Intent.ACTION_SEND).setType("video/mp4").putExtra(Intent.EXTRA_STREAM,uri)
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        ExternalVideoRoute.open(a,in);Intent out=shadowOf(a).getNextStartedActivity();
        assertEquals(Intent.ACTION_VIEW,out.getAction());assertEquals(uri,out.getData());
        assertEquals(uri,out.getClipData().getItemAt(0).getUri());
    }
    @Test public void lateResultsCannotChangeNewRequest() {
        InfinityExternalState s=new InfinityExternalState();long a=s.begin("A"),b=s.begin("B");
        assertFalse(s.set(a,InfinityExternalState.Phase.PLAYING));assertTrue(s.loading());
        assertTrue(s.set(b,InfinityExternalState.Phase.PLAYING));assertFalse(s.loading());
        assertFalse(s.set(a,InfinityExternalState.Phase.ERROR));assertEquals(InfinityExternalState.Phase.PLAYING,s.phase());
    }
    @Test public void duplicateTicketDoesNotReopenAndReleaseRejectsCallbacks() {
        InfinityExternalState s=new InfinityExternalState();long a=s.begin("A");
        assertEquals(-1,s.begin("A"));s.release();assertFalse(s.set(a,InfinityExternalState.Phase.READY));assertFalse(s.loading());
        assertTrue(s.begin("fresh-same-file")>a);
    }
    @Test public void loadingEndsForEveryTerminalOrInteractiveState() {
        for (InfinityExternalState.Phase phase:new InfinityExternalState.Phase[]{InfinityExternalState.Phase.READY,
                InfinityExternalState.Phase.PLAYING,InfinityExternalState.Phase.PAUSED,InfinityExternalState.Phase.ERROR,InfinityExternalState.Phase.ENDED}) {
            InfinityExternalState s=new InfinityExternalState();long t=s.begin("x");assertTrue(s.loading());
            s.set(t,phase);assertFalse(s.loading());
        }
    }
    @Test public void queuedGatewayIntentsSelectOnlyLatestAfterDelivery() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        for (String name:new String[]{"a","b","c"}) ExternalVideoRoute.stage(a,view("content://source/"+name,"video/mp4"));
        assertFalse(a.isFinishing());assertNull(shadowOf(a).getNextStartedActivity());
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals("content://source/c",shadowOf(a).getNextStartedActivity().getDataString());
        assertNull(shadowOf(a).getNextStartedActivity());
    }
    @Test public void normalRequestCanSupersedeUnlaunchedVideoWithoutBecomingPlayer() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        Intent main=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
        assertFalse(ExternalVideoRoute.captures(a,main));
        ExternalVideoRoute.stage(a,view("content://source/a","video/mp4"));
        assertTrue(ExternalVideoRoute.captures(a,main));ExternalVideoRoute.stage(a,main);
        shadowOf(Looper.getMainLooper()).idle();
        Intent out=shadowOf(a).getNextStartedActivity();
        assertEquals(Intent.ACTION_MAIN,out.getAction());assertTrue(out.hasCategory(Intent.CATEGORY_LAUNCHER));
        assertEquals("com.projectinfinity.kodi.Splash",out.getComponent().getClassName());
        assertNull(out.getStringExtra("infinity.external.request"));assertFalse(ExternalVideoRoute.captures(a,main));
    }
    @Test public void pendingGatewayOwnershipDoesNotCrossActivityInstances() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get(),b=Robolectric.buildActivity(Activity.class).setup().get();
        ExternalVideoRoute.stage(a,view("content://source/a","video/mp4"));
        ExternalVideoRoute.stage(b,view("content://source/b","video/mp4"));
        Activity canceled=Robolectric.buildActivity(Activity.class).setup().get();
        ExternalVideoRoute.stage(canceled,view("content://source/canceled","video/mp4"));canceled.finish();
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals("content://source/b",shadowOf(b).getNextStartedActivity().getDataString());
        assertEquals("content://source/a",shadowOf(a).getNextStartedActivity().getDataString());
        assertNull(shadowOf(a).getNextStartedActivity());assertNull(shadowOf(b).getNextStartedActivity());
        assertNull(shadowOf(canceled).getNextStartedActivity());
    }
}
