package com.projectinfinity.kodi;
import android.content.Context;
import android.content.Intent;
import android.media.MediaFormat;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Looper;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.Implementation;
import org.robolectric.annotation.Implements;
import org.robolectric.annotation.LooperMode;
import org.robolectric.shadows.ShadowMediaPlayer;
import org.robolectric.shadows.util.DataSource;
import org.robolectric.util.ReflectionHelpers;
import static org.robolectric.util.ReflectionHelpers.ClassParameter.from;
import static org.robolectric.Shadows.shadowOf;
import static org.junit.Assert.*;
import java.util.concurrent.atomic.AtomicReference;

/** Host scheduling/identity boundaries; this does not claim real decoding. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk=35,shadows=PreviewResumeBoundaryTest.VideoPlayer.class)
@LooperMode(LooperMode.Mode.PAUSED)
public class PreviewResumeBoundaryTest {
    @Implements(MediaPlayer.class)
    public static class VideoPlayer extends ShadowMediaPlayer {
        @Implementation protected MediaPlayer.TrackInfo[] getTrackInfo() {
            return new MediaPlayer.TrackInfo[]{ReflectionHelpers.callConstructor(MediaPlayer.TrackInfo.class,
                    from(int.class,MediaPlayer.TrackInfo.MEDIA_TRACK_TYPE_VIDEO),from(MediaFormat.class,new MediaFormat()))};
        }
    }
    @Test public void unregisteredProviderCannotMergeDifferentQueryResourcesByDocumentPath() {
        Context context=RuntimeEnvironment.getApplication();context.deleteDatabase(InfinityExternalResume.DATABASE);
        try(InfinityExternalResume store=new InfinityExternalResume(context)) {
            String a=store.identify(Uri.parse("content://opaque.example/document/movie?revision=A"),null,0,-1).uri;
            String b=store.identify(Uri.parse("content://opaque.example/document/movie?revision=B"),null,0,-1).uri;
            assertNotEquals("Only a real Android document provider can use document-ID canonicalization",a,b);
        }
    }
    @Test public void registeredDocumentProviderCanonicalizesTreeAndPlainDocumentUris() {
        Context context=RuntimeEnvironment.getApplication();context.deleteDatabase(InfinityExternalResume.DATABASE);
        android.content.pm.ResolveInfo resolve=new android.content.pm.ResolveInfo();
        resolve.providerInfo=new android.content.pm.ProviderInfo();resolve.providerInfo.authority="documents";
        resolve.providerInfo.packageName="qa.documents";resolve.providerInfo.name="qa.Documents";
        shadowOf(context.getPackageManager()).addResolveInfoForIntent(new Intent(android.provider.DocumentsContract.PROVIDER_INTERFACE),resolve);
        try(InfinityExternalResume store=new InfinityExternalResume(context)) {
            Uri a=Uri.parse("content://documents/document/primary%3Aa.mp4");
            Uri b=Uri.parse("content://documents/tree/primary%3A/document/primary%3Aa.mp4");
            assertTrue(android.provider.DocumentsContract.isDocumentUri(context,a));
            assertEquals(store.identify(a,null,0,-1).uri,store.identify(b,null,0,-1).uri);
        }
    }
    @Test public void restoredDecoderUsesCommittedProgressEvenWhenUiPositionIsStillZero() throws Exception {
        Context context=RuntimeEnvironment.getApplication();context.deleteDatabase(InfinityExternalResume.DATABASE);
        Uri uri=Uri.parse("https://fixture.invalid/a.mp4");
        try(InfinityExternalResume store=new InfinityExternalResume(context)) {
            store.save(store.load(store.identify(uri,null,0,-1),600000),139581);
        }
        ShadowMediaPlayer.addMediaInfo(DataSource.toDataSource(context,uri),new ShadowMediaPlayer.MediaInfo(600000,0));
        AtomicReference<MediaPlayer> player=new AtomicReference<>();
        ShadowMediaPlayer.setCreateListener((p,s)->player.set(p));
        AtomicReference<String> ready=new AtomicReference<>();
        InfinityExternalEngine engine=new InfinityExternalEngine(context,new InfinityExternalEngine.Observer(){
            public void event(String e,String detail){if(e.equals("ready")||e.equals("error"))ready.set(e+detail);}
            public void position(int p,int d){} public void size(int w,int h){}
            public void tracks(String[] l,int[] i,int s,boolean c){} public void subtitle(String s){}
        });
        try {
            engine.open(new Intent(Intent.ACTION_VIEW,uri),0,false);
            long deadline=System.nanoTime()+5_000_000_000L;
            while(ready.get()==null && System.nanoTime()<deadline){shadowOf(Looper.getMainLooper()).idle();Thread.sleep(10);}
            assertEquals("ready",ready.get());assertNotNull(player.get());
            assertEquals(139581,shadowOf(player.get()).getCurrentPositionRaw());
        } finally {
            engine.destroy();
            android.os.HandlerThread thread=ReflectionHelpers.getField(engine,"thread");thread.join(5000);
            assertFalse("Decoder worker released",thread.isAlive());
        }
    }
}
