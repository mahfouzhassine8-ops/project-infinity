package com.projectinfinity.kodi;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import org.junit.Before;
import org.junit.After;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(manifest=Config.NONE,sdk=35)
public class PreviewResumeTest {
    Context context; InfinityExternalResume store;
    @Before public void setup() {
        context=RuntimeEnvironment.getApplication();
        // This is an isolated host-test database; never an installed app/user database.
        context.deleteDatabase(InfinityExternalResume.DATABASE);store=new InfinityExternalResume(context);
    }
    @After public void close() { store.close(); }
    InfinityExternalResume.Identity media(String uri,String file,long size,long modified,String sample) {
        return new InfinityExternalResume.Identity(uri,file,sample,size,modified);
    }
    InfinityExternalResume.Identity media(String name) {return media(name,"",1000,10,"digest-"+name);}
    @Test public void separateVideosRetainExactMillisecondsAcrossDatabaseReopen() {
        store.save(store.load(media("A"),600000),137581);
        store.save(store.load(media("B"),600000),279209);store.close();
        store=new InfinityExternalResume(context);
        assertEquals(137581,store.load(media("A"),600000).position);
        assertEquals(279209,store.load(media("B"),600000).position);
    }
    @Test public void sameGrantedFileAcrossProvidersUsesOneRecordAndStartOverClearsAliases() {
        InfinityExternalResume.Identity a=media("provider-a","same-device-inode-extent",1000,10,"same");
        InfinityExternalResume.Identity b=media("provider-b","same-device-inode-extent",1000,10,"same");
        store.save(store.load(a,600000),123456);
        InfinityExternalResume.Entry other=store.load(b,600000);assertEquals(123456,other.position);
        store.save(other,145678);assertEquals(145678,store.load(a,600000).position);
        store.clear(other);assertEquals(0,store.load(a,600000).position);assertEquals(0,store.load(b,600000).position);
    }
    @Test public void unrelatedProvidersAndSameNamesNeverMergeBySampleOrSize() {
        store.save(store.load(media("provider-a/movie.mp4","file-a",1000,10,"same-sample"),600000),123456);
        assertEquals(0,store.load(media("provider-b/movie.mp4","file-b",1000,10,"same-sample"),600000).position);
    }
    @Test public void replacedSizeInvalidatesOldPosition() {
        store.save(store.load(media("A"),600000),123456);
        assertEquals(0,store.load(media("A","",2000,10,"digest-A"),600000).position);
    }
    @Test public void changedDurationInvalidatesOldPosition() {
        store.save(store.load(media("A"),600000),123456);
        assertEquals(0,store.load(media("A"),602001).position);
    }
    @Test public void changedSamplesOrSameFileModificationInvalidateEvenAtEqualLength() {
        InfinityExternalResume.Identity a=media("A","file",1000,10,"one");
        store.save(store.load(a,600000),123456);
        assertEquals(0,store.load(media("A","file",1000,10,"changed"),600000).position);
        store.save(store.load(a,600000),123456);
        assertEquals(0,store.load(media("A","file",1000,11,"one"),600000).position);
    }
    @Test public void stableDocumentSurvivesProviderCacheDescriptorReplacement() {
        store.save(store.load(media("document","cache-one",1000,10,"sample"),600000),123456);
        assertEquals(123456,store.load(media("document","cache-two",1000,20,"sample"),600000).position);
    }
    @Test public void completedNearEndAndShortProgressResetOnlyThatVideo() {
        for(long end:new long[]{600000,590000,570000,29999,0}) {
            store.save(store.load(media("A"),600000),123456);
            store.save(store.load(media("B"),600000),234567);
            store.save(store.load(media("A"),600000),end);
            assertEquals(0,store.load(media("A"),600000).position);
            assertEquals(234567,store.load(media("B"),600000).position);
        }
    }
    @Test public void noPromptForLiveOrFinalThirtySecondsAndExactBoundaryIsDefined() {
        assertFalse(InfinityExternalResume.resumable(60000,0));
        assertFalse(InfinityExternalResume.resumable(60000,90000));
        assertFalse(InfinityExternalResume.resumable(950000,1000000));
        assertFalse(InfinityExternalResume.resumable(29999,600000));
        assertTrue(InfinityExternalResume.resumable(30000,600000));
        assertTrue(InfinityExternalResume.resumable(569999,600000));
    }
    @Test public void treeAndDocumentUrisShareIdentityWithoutProviderSpecificRules() {
        String a=InfinityExternalResume.documentIdentity(Uri.parse("content://documents/document/primary%3AMovies%2Fa.mp4"));
        String b=InfinityExternalResume.documentIdentity(Uri.parse("content://documents/tree/primary%3AMovies/document/primary%3AMovies%2Fa.mp4"));
        assertEquals(a,b);
        assertNotEquals(a,InfinityExternalResume.documentIdentity(Uri.parse("content://other/document/primary%3AMovies%2Fa.mp4")));
    }
    @Test public void secretsAndRawUrisAreNotStoredAndKeySurvivesReopen() {
        String raw="https://host/private/movie.mp4?token=secret-credential";
        InfinityExternalResume.Identity id=store.identify(Uri.parse(raw),null,0,-1);
        assertTrue(id.uri.matches("[0-9a-f]{64}"));store.save(store.load(id,600000),123456);store.close();
        store=new InfinityExternalResume(context);assertEquals(id.uri,store.identify(Uri.parse(raw),null,0,-1).uri);
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT key FROM alias",null)) {
            while(c.moveToNext())assertTrue(c.getString(0).matches("[0-9a-f]{64}"));
        }
    }
    @Test public void recordsAndAliasesAreBoundedWithoutTouchingOtherDatabases() {
        for(int n=0;n<InfinityExternalResume.LIMIT+2;n++)store.save(store.load(media("file"+n),600000),60000+n);
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT COUNT(*) FROM video",null)) {
            assertTrue(c.moveToFirst());assertEquals(InfinityExternalResume.LIMIT,c.getInt(0));
        }
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT COUNT(*) FROM alias",null)) {
            assertTrue(c.moveToFirst());assertTrue(c.getInt(0)<=4000);
        }
        assertEquals(61001,store.load(media("file1001"),600000).position);
    }
}
