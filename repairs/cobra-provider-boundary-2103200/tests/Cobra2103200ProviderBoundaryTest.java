package com.projectinfinity.kodi;

import android.app.Application;
import android.app.Notification;
import android.app.NotificationManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Process;
import com.google.gson.*;
import com.projectinfinity.kodi.channels.model.Subscription;
import com.projectinfinity.kodi.channels.model.XBMCDatabase;
import com.projectinfinity.kodi.content.XBMCFileContentProvider;
import com.projectinfinity.kodi.model.Media;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowBinder;
import static org.junit.Assert.*;

/** Actual Java provider/Uri/SharedPreferences policy under Android API 34.
 * Caller UID is a Robolectric Binder shadow, not a physical cross-app check.
 * JNI/native streaming and external OEM search/TV rendering remain device work. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34, application=Application.class, manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103200ProviderBoundaryTest {
  static final String PREFS="cobra_published_media_v1";
  Context context;
  XBMCFileContentProvider provider;
  interface Action { void run() throws Exception; }
  static void field(String name,Object value)throws Exception {
    Field f=XBMCFileContentProvider.class.getDeclaredField(name);f.setAccessible(true);f.set(null,value);
  }
  static Object get(String name)throws Exception {
    Field f=XBMCFileContentProvider.class.getDeclaredField(name);f.setAccessible(true);return f.get(null);
  }
  static String authorize(Uri uri,String mode)throws Exception {
    Method m=XBMCFileContentProvider.class.getDeclaredMethod("authorizeOpen",Uri.class,String.class);m.setAccessible(true);
    try{return (String)m.invoke(null,uri,mode);}catch(InvocationTargetException e){
      Throwable cause=e.getCause();if(cause instanceof Exception)throw (Exception)cause;throw e;
    }
  }
  static void denied(Action action)throws Exception {
    try{action.run();fail("Expected SecurityException before native access");}catch(SecurityException expected){}
  }
  static void failedPublish(Action action)throws Exception {
    try{action.run();fail("Expected failed publication");}catch(IllegalStateException expected){}
  }
  void external(){ShadowBinder.setCallingUid(Process.myUid()+7001);}
  void local(){ShadowBinder.setCallingUid(Process.myUid());}
  void restart()throws Exception {
    field("resourcePreferences",null);field("publishedResources",null);field("legacyResourcesLoaded",false);
  }
  Uri internal(String path){return XBMCFileContentProvider.buildUri(path);}
  Uri published(String path){return XBMCFileContentProvider.buildPublishedUri(path);}
  @Before public void setUp()throws Exception {
    context=RuntimeEnvironment.getApplication();local();restart();field("resourceContext",null);
    context.getSharedPreferences(PREFS,0).edit().clear().commit();
    context.getSharedPreferences("com.projectinfinity.kodi",0).edit().clear().commit();
    provider=Robolectric.buildContentProvider(XBMCFileContentProvider.class).create().get();
  }
  @After public void tearDown()throws Exception {local();restart();field("resourceContext",null);}

  @Test public void arbitraryPrivatePathsAreDeniedBeforePipeOrNativeOpen()throws Exception {
    external();for(String path:new String[]{"/data/user/0/com.projectinfinity.kodi/shared_prefs/secrets.xml","special://profile/passwords.xml","file:///data/private","https://host.invalid/private"})
      denied(()->provider.openFile(internal(path),"r"));
  }
  @Test public void directoryQueriesArePrivateEvenForPublishedPaths()throws Exception {
    Uri uri=published("special://profile/playlists/video/");external();
    denied(()->provider.query(uri,null,null,null,null));
  }
  @Test public void sameUidDirectoryQueryPreservesExactTransportPath()throws Exception {
    final String[] observed={null};XBMCJsonRPC fake=new XBMCJsonRPC(){
      @Override public List<com.projectinfinity.kodi.model.File> getFiles(String path){observed[0]=path;return Collections.emptyList();}
    };
    Field f=XBMCFileContentProvider.class.getDeclaredField("mJsonRPC");f.setAccessible(true);f.set(provider,fake);
    String path="special://profile/playlists/video/";assertNull(provider.query(internal(path),null,null,null,null));assertEquals(path,observed[0]);
  }
  @Test public void sameUidOpenKeepsUnpublishedKodiPaths()throws Exception {
    assertEquals("special://profile/playlists/video/a.xsp",authorize(internal("special://profile/playlists/video/a.xsp"),"r"));
  }
  @Test public void issuedResourceKeepsLegacyUriAndSurvivesProviderRestart()throws Exception {
    String path="image://https%3a%2f%2fhost.invalid%2fcover.png/";Uri uri=published(path);assertEquals(internal(path),uri);
    external();assertEquals(path,authorize(uri,"r"));restart();assertEquals(path,authorize(uri,"r"));
  }
  @Test public void genericInternalUriCreationDoesNotGrantExternalRead()throws Exception {
    Uri uri=internal("/private/internal-bitmap.png");external();denied(()->authorize(uri,"r"));
  }
  @Test public void onlyExactDecodedResourceIsAllowedWithoutPrefixOrExtensionRules()throws Exception {
    published("/media/cover.jpg");external();
    for(String path:new String[]{"/media/cover.jpg/../secret","/media/cover.jpg?other=1","/media/cover.jpg.bak","/media/COVER.jpg","/media/cover.jpg%00","/media/cover2.jpg"})
      denied(()->authorize(internal(path),"r"));
    assertEquals("/media/cover.jpg",authorize(Uri.parse("content://"+XBMCFileContentProvider.AUTHORITY+"#%2Fmedia%2Fcover.jpg"),"r"));
  }
  @Test public void URIShapeMutationsAndWriteModesAreRejected()throws Exception {
    Uri uri=published("/public/art.png");external();
    for(Uri changed:new Uri[]{null,uri.buildUpon().scheme("file").build(),uri.buildUpon().authority("other.file").build(),uri.buildUpon().path("/").build(),uri.buildUpon().appendQueryParameter("allow","true").build(),uri.buildUpon().fragment(null).build()})
      denied(()->authorize(changed,"r"));
    for(String mode:new String[]{null,"","w","rw","rwt","wa","rt"})denied(()->authorize(uri,mode));
  }
  @Test public void invalidUnicodeAndNulCannotAliasAnAuthorizedNativeArgument()throws Exception {
    published("/public/?");external();
    for(String bad:new String[]{"/public/\ud800","/public/\udc00","/public/\u0000","/public/x\ud800y"}){
      denied(()->authorize(Uri.parse("content://"+XBMCFileContentProvider.AUTHORITY+"#"+bad),"r"));
      try{published(bad);fail("Malformed path published");}catch(IllegalArgumentException expected){}
    }
    String valid="/public/\ud83d\udc0d.png";Uri uri=published(valid);assertEquals(valid,authorize(uri,"r"));
  }
  @Test public void pathHashesDoNotPersistSourcePathsOrCredentials()throws Exception {
    published("https://user:secret@provider.invalid/cover?token=private");
    Map<String,?> map=context.getSharedPreferences(PREFS,0).getAll();assertEquals(1,map.size());
    for(Map.Entry<String,?> entry:map.entrySet()){assertTrue(entry.getKey().matches("[a-f0-9]{64}"));assertEquals(Boolean.TRUE,entry.getValue());}
  }
  @Test public void concurrentPublicationsPreserveEveryCommittedResource()throws Exception {
    ExecutorService pool=Executors.newFixedThreadPool(8);List<Future<?>> tasks=new ArrayList<>();
    for(int i=0;i<48;i++){final int index=i;tasks.add(pool.submit(()->published("/public/"+index+".png")));}
    for(Future<?> task:tasks)task.get(20,TimeUnit.SECONDS);pool.shutdown();assertTrue(pool.awaitTermination(10,TimeUnit.SECONDS));
    restart();external();for(int i=0;i<48;i++)assertEquals("/public/"+i+".png",authorize(internal("/public/"+i+".png"),"r"));
  }
  @Test public void cachedCardsBackgroundsAndLocalVideoPreviewsMigrateTogether()throws Exception {
    Subscription sub=Subscription.createSubscription("old","",0);sub.setChannelId(44);XBMCDatabase.saveSubscriptions(context,Collections.singletonList(sub));
    Media media=new Media();media.setCardImageUrl(internal("/old/poster.png").toString());media.setBackgroundImageUrl(internal("/old/fanart.png").toString());media.setVideoUrl(internal("/old/music-video.mp4").toString());
    XBMCDatabase.saveMedias(context,44,Collections.singletonList(media));external();
    for(String path:new String[]{"/old/poster.png","/old/fanart.png","/old/music-video.mp4"})assertEquals(path,authorize(internal(path),"r"));
    restart();assertEquals("/old/music-video.mp4",authorize(internal("/old/music-video.mp4"),"r"));
  }
  @Test public void cachedForeignAuthorityAndDirectoryUriDoNotCreateGrants()throws Exception {
    Subscription sub=Subscription.createSubscription("old",internal("/secret/directory/").toString(),0);sub.setChannelId(44);XBMCDatabase.saveSubscriptions(context,Collections.singletonList(sub));
    Media media=new Media();media.setCardImageUrl("content://forged.file#/secret/file");media.setBackgroundImageUrl("content://"+XBMCFileContentProvider.AUTHORITY+"/forged#/secret/file");XBMCDatabase.saveMedias(context,44,Collections.singletonList(media));
    external();denied(()->authorize(internal("/secret/file"),"r"));denied(()->authorize(internal("/secret/directory/"),"r"));
  }
  @Test public void ownExistingNotificationBackgroundMigratesWithoutChangingUri()throws Exception {
    Notification n=new Notification();n.extras=new android.os.Bundle();n.extras.putString("android.backgroundImageUri",internal("/old/notification.jpg").toString());
    ((NotificationManager)context.getSystemService(Context.NOTIFICATION_SERVICE)).notify(4,n);external();
    assertEquals("/old/notification.jpg",authorize(internal("/old/notification.jpg"),"r"));
    assertEquals(Process.myUid()+7001,android.os.Binder.getCallingUid());
  }
  @Implements(NotificationManager.class)
  public static class ForeignNotifications {
    @Implementation protected android.service.notification.StatusBarNotification[] getActiveNotifications(){
      Context app=RuntimeEnvironment.getApplication();Notification own=new Notification(),foreign=new Notification();own.extras=new android.os.Bundle();foreign.extras=new android.os.Bundle();
      own.extras.putString("android.backgroundImageUri",XBMCFileContentProvider.buildUri("/own/art.jpg").toString());foreign.extras.putString("android.backgroundImageUri",XBMCFileContentProvider.buildUri("/foreign/secret").toString());
      return new android.service.notification.StatusBarNotification[]{
        new android.service.notification.StatusBarNotification("other.package","other.package",1,null,Process.myUid()+8,0,foreign,android.os.Process.myUserHandle(),null,1),
        new android.service.notification.StatusBarNotification(app.getPackageName(),app.getPackageName(),2,null,Process.myUid(),0,own,android.os.Process.myUserHandle(),null,1)};
    }
  }
  @Test @Config(shadows=ForeignNotifications.class)
  public void onlyOwnNotificationPackageMayRecoverLegacyResource()throws Exception {
    external();denied(()->authorize(internal("/foreign/secret"),"r"));assertEquals("/own/art.jpg",authorize(internal("/own/art.jpg"),"r"));
  }
  @Implements(NotificationManager.class)
  public static class FailedNotifications {
    @Implementation protected android.service.notification.StatusBarNotification[] getActiveNotifications(){throw new SecurityException("Fixture service unavailable");}
  }
  @Test @Config(shadows=FailedNotifications.class)
  public void failedNotificationMigrationRestoresCallerIdentityAndFailsClosed()throws Exception {
    external();denied(()->authorize(internal("/unknown/secret"),"r"));assertEquals(Process.myUid()+7001,android.os.Binder.getCallingUid());
    assertEquals("/new/public.jpg",authorize(published("/new/public.jpg"),"r"));
  }
  @Test public void malformedPrivateCacheDoesNotAuthorizeRequestedFileOrDiscardNewPublication()throws Exception {
    context.getSharedPreferences("com.projectinfinity.kodi",0).edit().putStringSet("com.projectinfinity.kodi.prefs.SUBSCRIPTIONS",Collections.singleton("not-json" )).commit();
    external();denied(()->authorize(internal("/private/unknown"),"r"));assertTrue((Boolean)get("legacyResourcesLoaded"));
    Uri uri=published("/public/new.png");assertEquals("/public/new.png",authorize(uri,"r"));
  }

  /** Models Android's documented memory-before-disk commit behavior. */
  static final class DiskPreferences implements InvocationHandler {
    Map<String,Object> memory=new HashMap<>(),disk=new HashMap<>();boolean failNext;int commits;
    final SharedPreferences api=(SharedPreferences)Proxy.newProxyInstance(SharedPreferences.class.getClassLoader(),new Class<?>[]{SharedPreferences.class},this);
    public Object invoke(Object p,Method m,Object[] args){
      switch(m.getName()){
        case "getAll": return new HashMap<>(memory);
        case "edit": {
          Map<String,Object> staged=new HashMap<>();boolean[] clear={false};
          return Proxy.newProxyInstance(SharedPreferences.Editor.class.getClassLoader(),new Class<?>[]{SharedPreferences.Editor.class},(editor,method,values)->{
            if(method.getName().equals("clear")){clear[0]=true;return editor;}
            if(method.getName().equals("putBoolean")){staged.put((String)values[0],values[1]);return editor;}
            if(method.getName().equals("commit")){if(clear[0])memory.clear();memory.putAll(staged);commits++;if(failNext){failNext=false;return false;}disk=new HashMap<>(memory);return true;}
            throw new UnsupportedOperationException(method.getName());
          });
        }
        default: throw new UnsupportedOperationException(m.getName());
      }
    }
    void inject()throws Exception {field("resourcePreferences",api);field("publishedResources",new HashSet<String>());}
  }
  @Test public void failedCommitCannotAuthorizeNowOrLeakThroughLaterCommitAndRestart()throws Exception {
    DiskPreferences store=new DiskPreferences();store.inject();store.failNext=true;
    failedPublish(()->published("/not-issued/a.png"));external();denied(()->authorize(internal("/not-issued/a.png"),"r"));
    published("/issued/b.png");assertEquals(1,store.disk.size());int commits=store.commits;published("/issued/b.png");assertEquals("Repeat publication must avoid disk rewrite",commits,store.commits);
    field("publishedResources",new HashSet<>(store.disk.keySet()));
    denied(()->authorize(internal("/not-issued/a.png"),"r"));assertEquals("/issued/b.png",authorize(internal("/issued/b.png"),"r"));
  }
  @Test public void migrationUsesOneTransactionForManyResources()throws Exception {
    Subscription sub=Subscription.createSubscription("old","",0);sub.setChannelId(44);XBMCDatabase.saveSubscriptions(context,Collections.singletonList(sub));
    List<Media> media=new ArrayList<>();for(int i=0;i<160;i++){Media item=new Media();item.setCardImageUrl(internal("/old/"+i+".png").toString());media.add(item);}XBMCDatabase.saveMedias(context,44,media);
    DiskPreferences store=new DiskPreferences();store.inject();external();assertEquals("/old/159.png",authorize(internal("/old/159.png"),"r"));assertEquals(1,store.commits);assertEquals(160,store.disk.size());
  }
  @Test public void failedMigrationDoesNotPartiallyAuthorizeItsResources()throws Exception {
    Subscription sub=Subscription.createSubscription("old","",0);sub.setChannelId(44);XBMCDatabase.saveSubscriptions(context,Collections.singletonList(sub));Media item=new Media();item.setCardImageUrl(internal("/old/a.png").toString());item.setVideoUrl(internal("/old/b.mp4").toString());XBMCDatabase.saveMedias(context,44,Collections.singletonList(item));
    DiskPreferences store=new DiskPreferences();store.inject();store.failNext=true;external();
    denied(()->authorize(internal("/old/a.png"),"r"));denied(()->authorize(internal("/old/b.mp4"),"r"));assertEquals(1,store.commits);assertTrue(store.disk.isEmpty());
    published("/new/c.png");assertEquals(1,store.disk.size());denied(()->authorize(internal("/old/a.png"),"r"));
  }
  @Test public void uninitializedStoreFailsClosedWithoutPublishing()throws Exception {
    restart();field("resourceContext",null);failedPublish(()->published("/uninitialized/art.png"));
  }

  static final class CapturedSearch extends XBMCJsonRPC {
    JsonArray captured;
    @Override public JsonArray request_array(String request){captured=JsonParser.parseString(request).getAsJsonArray();return new JsonArray();}
  }
  static void collectValues(JsonElement item,List<String> values){
    if(item.isJsonObject())for(Map.Entry<String,JsonElement> entry:item.getAsJsonObject().entrySet()){
      if(entry.getKey().equals("value"))values.add(entry.getValue().getAsString());else collectValues(entry.getValue(),values);
    }else if(item.isJsonArray())for(JsonElement element:item.getAsJsonArray())collectValues(element,values);
  }
  @Test public void externalSearchEscapesMaliciousJSONAndKeepsAllSixFixedMethods()throws Exception {
    String[] methods={"VideoLibrary.GetMovies","VideoLibrary.GetTVShows","AudioLibrary.GetAlbums","AudioLibrary.GetArtists","VideoLibrary.GetMovies","VideoLibrary.GetTVShows"};
    for(String query:new String[]{"ordinary","a\"b\\c\n\t\u0001","\"}]},\"method\":\"Files.GetDirectory\",\"params\":{\"directory\":\"special://profile\"},\"unused\":{\"value\":\"","\ud83d\udc0d"}){
      CapturedSearch rpc=new CapturedSearch();Cursor cursor=rpc.getSuggestions(query,10);assertNotNull(cursor);cursor.close();assertEquals(6,rpc.captured.size());
      for(int i=0;i<6;i++)assertEquals(methods[i],rpc.captured.get(i).getAsJsonObject().get("method").getAsString());
      List<String> values=new ArrayList<>();collectValues(rpc.captured,values);assertEquals(12,values.size());for(String value:values)assertEquals(query,value);
    }
  }
  @Test public void searchPublicationWorksUnderExternalBinderIdentityOnlyForReturnedArtwork()throws Exception {
    external();XBMCJsonRPC rpc=new XBMCJsonRPC(){@Override public JsonArray request_array(String request){return JsonParser.parseString("[{\"id\":\"1\",\"result\":{\"movies\":[{\"movieid\":7,\"title\":\"Fixture\",\"tagline\":\"Fixture\",\"year\":2026,\"runtime\":1,\"art\":{\"poster\":\"/published/movie.jpg\"}}]}}]").getAsJsonArray();}};
    Cursor cursor=rpc.getSuggestions("fixture",10);assertNotNull(cursor);assertTrue(cursor.moveToFirst());Uri uri=Uri.parse(cursor.getString(cursor.getColumnIndexOrThrow(android.app.SearchManager.SUGGEST_COLUMN_ICON_1)));cursor.close();
    assertEquals("/published/movie.jpg",authorize(uri,"r"));denied(()->authorize(internal("/private/unreturned.jpg"),"r"));
  }
}
