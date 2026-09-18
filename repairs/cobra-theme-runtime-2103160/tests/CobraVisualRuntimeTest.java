package com.projectinfinity.kodi;
import android.app.Application;
import android.content.Context;
import android.graphics.*;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real Android JSON/bitmap/storage/view tests. No physical provider or decoder claims. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraVisualRuntimeTest {
 Context context;
 @Before public void setup()throws Exception{context=RuntimeEnvironment.getApplication();CobraVisualRenderer.loading.set(true);CobraVisualTheme.deleteTree(CobraVisualTheme.store(context));CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();}
 @After public void cleanup(){CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();CobraVisualTheme.deleteTree(CobraVisualTheme.store(context));}
 JSONObject root(String id)throws Exception{return new JSONObject().put("schema",2).put("scope","cobra-presentation").put("minimum_runtime",2).put("minimum_build",2103160).put("id",id).put("name","Visual test "+id).put("assets",new JSONObject()).put("base",new JSONObject());}
 byte[] png(int color)throws Exception{Bitmap b=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);b.eraseColor(color);ByteArrayOutputStream out=new ByteArrayOutputStream();assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));b.recycle();return out.toByteArray();}
 Map<String,byte[]> withImage(JSONObject data,int color)throws Exception{byte[] image=png(color);String path="resources/assets/badge.png";data.getJSONObject("assets").put("badge",new JSONObject().put("path",path).put("sha256",CobraVisualTheme.hash(image)));Map<String,byte[]> files=new LinkedHashMap<>();files.put(CobraVisualTheme.MANIFEST,data.toString().getBytes(StandardCharsets.UTF_8));files.put(path,image);return files;}
 byte[] zip(Map<String,byte[]> files)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(out)){for(Map.Entry<String,byte[]> e:files.entrySet()){z.putNextEntry(new ZipEntry(CobraVisualTheme.PREFIX+e.getKey()));z.write(e.getValue());z.closeEntry();}}return out.toByteArray();}
 Map<String,byte[]> manifest(JSONObject data)throws Exception{Map<String,byte[]> files=new LinkedHashMap<>();files.put(CobraVisualTheme.MANIFEST,data.toString().getBytes(StandardCharsets.UTF_8));return files;}
 CobraVisualTheme install(JSONObject root)throws Exception{return CobraVisualTheme.install(context,new ByteArrayInputStream(zip(manifest(root))));}
 void activate(CobraVisualTheme theme){CobraVisualRenderer.publish(theme,"test publication");Shadows.shadowOf(Looper.getMainLooper()).idle();}
 interface Checked {void run()throws Exception;}
 void rejects(Checked action)throws Exception{boolean failed=false;try{action.run();}catch(Exception expected){failed=true;}assertTrue("Malformed/untrusted package must be rejected",failed);}
 @Test public void atomicInstallAndReloadKeepExactManifestIdentity()throws Exception{CobraVisualTheme one=install(root("one"));assertEquals("one",one.id);assertEquals("one",CobraVisualTheme.load(context).id);assertTrue(new File(one.directory,CobraVisualTheme.MANIFEST).isFile());}
 @Test public void corruptImageCannotReplaceCurrentTheme()throws Exception{install(root("good"));JSONObject broken=root("broken");Map<String,byte[]> files=withImage(broken,Color.RED);files.put("resources/assets/badge.png",new byte[]{1,2,3});rejects(()->CobraVisualTheme.install(context,new ByteArrayInputStream(zip(files))));assertEquals("good",CobraVisualTheme.load(context).id);}
 @Test public void wrongSchemaAndFutureRuntimeRefused()throws Exception{for(String key:new String[]{"schema","minimum_runtime","minimum_build"}){JSONObject bad=root("bad");bad.put(key,9999999);rejects(()->install(bad));}assertEquals("builtin",CobraVisualTheme.load(context).id);}
 @Test public void executableAndUnlistedFilesRefused()throws Exception{Map<String,byte[]> files=manifest(root("bad"));files.put("lib/evil.py","print('no')".getBytes(StandardCharsets.UTF_8));rejects(()->CobraVisualTheme.install(context,new ByteArrayInputStream(zip(files))));assertFalse(new File(CobraVisualTheme.store(context),"active.json").exists());}
 @Test public void unknownThemeFieldAndUnknownAssetSlotAreRejected()throws Exception{JSONObject bad=root("bad");bad.put("player_owner","theme");rejects(()->install(bad));JSONObject data=root("bad-two");data.getJSONObject("base").put("images",new JSONObject().put("badge-that-is-not-wired","nothing"));final JSONObject invalid=data;rejects(()->install(invalid));}
 @Test public void previousThemeAndResetAreDataPreserving()throws Exception{context.getSharedPreferences("existing-userdata",0).edit().putString("playlist","unchanged").commit();install(root("one"));install(root("two"));assertEquals("one",CobraVisualTheme.rollback(context).id);assertEquals("two",CobraVisualTheme.rollback(context).id);CobraVisualTheme.reset(context);assertEquals("builtin",CobraVisualTheme.load(context).id);assertEquals("two",CobraVisualTheme.rollback(context).id);assertEquals("unchanged",context.getSharedPreferences("existing-userdata",0).getString("playlist",""));}
 @Test public void exactBadgeAssetIsDrawnByProductionCobraBrandMark()throws Exception{JSONObject data=root("badge");data.getJSONObject("base").put("images",new JSONObject().put("drawer.badge","badge"));CobraVisualTheme theme=CobraVisualTheme.install(context,new ByteArrayInputStream(zip(withImage(data,Color.MAGENTA))));activate(theme);CobraNavigationUiTest helper=new CobraNavigationUiTest();helper.clock();InfinityLiveActivity a=helper.fixture(24);
  try{View mark=(View)CobraNavigationUiTest.construct("CobraBrandMark",a);mark.measure(View.MeasureSpec.makeMeasureSpec(80,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(80,View.MeasureSpec.EXACTLY));mark.layout(0,0,80,80);Bitmap b=Bitmap.createBitmap(80,80,Bitmap.Config.ARGB_8888);mark.draw(new Canvas(b));assertEquals(Color.MAGENTA,b.getPixel(40,40));save(b,"actual-cobra-custom-badge.png");b.recycle();}finally{helper.clean(a);}}
 @Test public void paletteOverridesAndBoundedDimensionsResolve()throws Exception{JSONObject data=root("palette");data.getJSONObject("base").put("colors",new JSONObject().put("palette.accent","#123456"));data.put("variants",new JSONObject().put("oled",new JSONObject().put("colors",new JSONObject().put("palette.accent","#ABCDEF"))));activate(install(data));CobraVisualRenderer r=new CobraVisualRenderer(context);assertEquals(Color.parseColor("#123456"),r.mode("light").color("palette.accent",0));assertEquals(Color.parseColor("#ABCDEF"),r.mode("oled").color("palette.accent",0));assertEquals(48,r.dimension("missing",48));}
 @Test public void viewStylesDoNotReplaceClicksTagsOrAccessibility()throws Exception{JSONObject data=root("style");data.getJSONObject("base").put("styles",new JSONObject().put("drawer.item.tv",new JSONObject().put("fill","#012345").put("text","#FFFFFF").put("font_family","serif").put("radius_dp",20)));activate(install(data));Button b=new Button(context);b.setTag("action-tv");b.setContentDescription("Live TV");int[] clicks={0};b.setOnClickListener(v->clicks[0]++);new CobraVisualRenderer(context).paint(b,"drawer.item.tv");assertTrue(b.performClick());assertEquals(1,clicks[0]);assertEquals("action-tv",b.getTag());assertEquals("Live TV",b.getContentDescription());assertNotNull(b.getBackground());}
 @Test public void textureViewsAreNeverStyledRecreatedOrReparented()throws Exception{JSONObject data=root("safe");data.getJSONObject("base").put("styles",new JSONObject().put("all.panel",new JSONObject().put("fill","#FF0000").put("padding_dp",50)));activate(install(data));FrameLayout parent=new FrameLayout(context);TextureView texture=new TextureView(context);parent.addView(texture,new FrameLayout.LayoutParams(100,80));Object params=texture.getLayoutParams();new CobraVisualRenderer(context).tree(parent,"player.chrome");assertSame(parent,texture.getParent());assertSame(params,texture.getLayoutParams());assertEquals(0,texture.getPaddingLeft());assertNull(texture.getBackground());}
 @Test public void nativeThemeEscapeHatchCannotBeRestyled()throws Exception{JSONObject data=root("safe");data.getJSONObject("base").put("styles",new JSONObject().put("all.button",new JSONObject().put("padding_dp",40).put("text","#000000")));activate(install(data));Button button=new Button(context);button.setTag("cobra-visual-theme-controls");int padding=button.getPaddingLeft();new CobraVisualRenderer(context).paint(button,"settings");assertEquals(padding,button.getPaddingLeft());}
 @Test public void themeInstallDoesNotReplaceGuideOrItsVideoTexture()throws Exception{CobraNavigationUiTest helper=new CobraNavigationUiTest();helper.clock();InfinityLiveActivity a=helper.fixture(96);try{CobraNavigationUiTest.call(a,"cobraOpenLiveTv");helper.measure(a,412,915);Object shell=CobraNavigationUiTest.get(a,"mCobraGuideShell"),texture=CobraNavigationUiTest.get(a,"mCobraPreviewTexture");JSONObject data=root("new-look");data.getJSONObject("base").put("styles",new JSONObject().put("drawer.panel",new JSONObject().put("fill","#F0F6FC")));activate(install(data));assertSame(shell,CobraNavigationUiTest.get(a,"mCobraGuideShell"));assertSame(texture,CobraNavigationUiTest.get(a,"mCobraPreviewTexture"));helper.guide(a);CobraNavigationUiTest.call(a,"toggleCobraDrawer");helper.measure(a,412,915);View drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNotNull(drawer);Bitmap image=Bitmap.createBitmap(412,915,Bitmap.Config.ARGB_8888);drawer.draw(new Canvas(image));save(image,"actual-themed-drawer.png");image.recycle();}finally{helper.clean(a);}}
 @Test public void corruptedStoredManifestFailsClosed()throws Exception{CobraVisualTheme good=install(root("good"));try(FileOutputStream out=new FileOutputStream(new File(good.directory,CobraVisualTheme.MANIFEST))){out.write("{}".getBytes(StandardCharsets.UTF_8));}rejects(()->CobraVisualTheme.load(context));CobraVisualTheme.reset(context);assertEquals("builtin",CobraVisualTheme.load(context).id);}
 @Test public void invalidFontHeaderIsRejectedBeforeActivation()throws Exception{JSONObject data=root("font");byte[] bad=new byte[]{1,2,3,4};String path="resources/assets/custom.ttf";data.getJSONObject("assets").put("font",new JSONObject().put("kind","font").put("path",path).put("sha256",CobraVisualTheme.hash(bad)));Map<String,byte[]> files=manifest(data);files.put(path,bad);rejects(()->CobraVisualTheme.install(context,new ByteArrayInputStream(zip(files))));assertEquals("builtin",CobraVisualTheme.load(context).id);}
 @Test public void imageCannotBeUsedAsFontAsset()throws Exception{JSONObject data=root("mixed-kind");data.getJSONObject("base").put("styles",new JSONObject().put("font.all",new JSONObject().put("font_asset","badge")));Map<String,byte[]> files=withImage(data,Color.BLUE);rejects(()->CobraVisualTheme.install(context,new ByteArrayInputStream(zip(files))));assertEquals("builtin",CobraVisualTheme.load(context).id);}
 @Test public void previousSnapshotSurvivesFailedInstallation()throws Exception{install(root("one"));install(root("two"));JSONObject bad=root("bad");bad.put("unknown-field",true);rejects(()->install(bad));assertEquals("two",CobraVisualTheme.load(context).id);assertEquals("one",CobraVisualTheme.rollback(context).id);}
 @Test public void createdDialogsKeepExistingOnShowAndButtonActions()throws Exception{
  JSONObject data=root("dialog");
  data.getJSONObject("base").put("styles",new JSONObject().put("dialog.button",new JSONObject().put("text","#123456")));
  activate(install(data));
  CobraNavigationUiTest helper=new CobraNavigationUiTest();helper.clock();
  InfinityLiveActivity a=helper.fixture(24);
  try{
   // The inherited fixture pauses both Looper and Choreographer. ViewRootImpl
   // traversal barriers hold synchronous dialog messages until a scheduled frame.
   // Exercise the unmodified framework dialog as a control, not only our builder.
   for(boolean themed:new boolean[]{false,true}){
    int[] events={0,0};
    android.app.AlertDialog.Builder builder=themed
        ?new CobraVisualRenderer.DialogBuilder(a,new CobraVisualRenderer(a),"dialog")
        :new android.app.AlertDialog.Builder(a);
    android.app.AlertDialog dialog=builder.setTitle("Preserved actions")
        .setPositiveButton("OK",(d,w)->events[1]++).create();
    dialog.setOnShowListener(d->events[0]++);
    try{
     dialog.show();
     View decor=dialog.getWindow().getDecorView();
     decor.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(240,View.MeasureSpec.EXACTLY));
     decor.layout(0,0,360,240);
     assertEquals("OnShow is queued, not missing; themed="+themed,0,events[0]);
     // A plain idle() cannot pass the pending ViewRoot traversal barrier. Advance
     // the configured 16ms frame through the SAME frame helper as the locked tests.
     // Do not invoke callbacks, remove barriers, or force a production layout.
     helper.frames(1);
     assertEquals("Original OnShow delivered once; themed="+themed,1,events[0]);
     Button positive=dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE);
     assertNotNull(positive);
     if(themed)assertEquals("Theme actually styled the live dialog",Color.parseColor("#123456"),positive.getCurrentTextColor());
     assertTrue(positive.performClick());
     assertEquals("Button listener is queued; themed="+themed,0,events[1]);
     helper.frames(1);
     assertEquals("Original button delivered once; themed="+themed,1,events[1]);
     assertFalse("Native button dismissal retained; themed="+themed,dialog.isShowing());
     helper.frames(1);
     assertEquals("No duplicate OnShow; themed="+themed,1,events[0]);
     assertEquals("No duplicate button; themed="+themed,1,events[1]);
    }finally{dialog.dismiss();helper.frames(1);}
   }
  }finally{helper.clean(a);}
 }
 void save(Bitmap b,String name)throws Exception{File dir=new File(System.getProperty("cobra.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());try(FileOutputStream out=new FileOutputStream(new File(dir,name))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}}
}
