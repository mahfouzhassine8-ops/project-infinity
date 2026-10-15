package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Application;
import android.content.res.ColorStateList;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckedTextView;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.time.Duration;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Full production renderer and Android AlertDialog, including native text rasterization.
 * The Activity is a controlled host, not the full app or a physical-device claim. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103204DialogTest {
  ActivityController<Activity> controller;
  Activity activity;
  AlertDialog open;

  @Before public void before(){
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    controller=Robolectric.buildActivity(Activity.class);activity=controller.get();
    activity.setTheme(android.R.style.Theme_Material_NoActionBar);controller.setup().visible();
    frames();
  }
  @After public void after(){
    if(open!=null)open.dismiss();frames();controller.pause().stop().destroy();
    CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
  }
  static void frames(){Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(480));}
  CobraVisualRenderer.DialogBuilder builder(String mode){return new CobraVisualRenderer.DialogBuilder(activity,new CobraVisualRenderer(activity).mode(mode),"dialog");}
  View layout(AlertDialog d){
    open=d;frames();View decor=d.getWindow().getDecorView();
    decor.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(500,View.MeasureSpec.AT_MOST));
    // Keep the real Window/ViewRoot and manual bitmap viewport synchronized.
    // Otherwise a later traversal restores the larger window and makes list
    // scroll positions/selector focus disagree with the captured viewport.
    d.getWindow().setLayout(360,decor.getMeasuredHeight());
    Object root=org.robolectric.util.ReflectionHelpers.callInstanceMethod(decor,"getViewRootImpl");
    org.robolectric.shadows.ShadowViewRootImpl viewRoot=org.robolectric.shadow.api.Shadow.extract(root);
    viewRoot.callDispatchResized();if(!decor.hasWindowFocus())viewRoot.callWindowFocusChanged(true);
    decor.layout(0,0,360,decor.getMeasuredHeight());frames();
    assertTrue(d.isShowing());assertTrue(decor.getWidth()>0&&decor.getHeight()>0);return decor;
  }
  static TextView text(View v,String exact){
    if(v instanceof TextView&&exact.contentEquals(((TextView)v).getText()))return (TextView)v;
    if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){TextView found=text(g.getChildAt(i),exact);if(found!=null)return found;}}
    return null;
  }
  static Bitmap render(View view){Bitmap b=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(b));return b;}
  static double linear(int c){double x=c/255d;return x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4);}
  static double luminance(int c){return .2126*linear(Color.red(c))+.7152*linear(Color.green(c))+.0722*linear(Color.blue(c));}
  static double contrast(int a,int b){double x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
  static boolean near(int a,int b){return Math.abs(Color.red(a)-Color.red(b))<8&&Math.abs(Color.green(a)-Color.green(b))<8&&Math.abs(Color.blue(a)-Color.blue(b))<8;}
  static int over(int ink,int surface){float a=Color.alpha(ink)/255f;return Color.rgb(Math.round(Color.red(ink)*a+Color.red(surface)*(1-a)),Math.round(Color.green(ink)*a+Color.green(surface)*(1-a)),Math.round(Color.blue(ink)*a+Color.blue(surface)*(1-a)));}
  static void rasterizedText(TextView text,int ink,int surface){
    assertNotNull("The actual dialog contains this text",text);assertTrue(text.getWidth()>0&&text.getHeight()>0);
    assertNotNull(text.getLayout());assertEquals("Text is not ellipsized",0,text.getLayout().getEllipsisCount(0));
    Bitmap pixels=Bitmap.createBitmap(text.getWidth(),text.getHeight(),Bitmap.Config.ARGB_8888);pixels.eraseColor(surface);text.draw(new Canvas(pixels));
    int renderedInk=over(ink,surface);
    try{
      int glyphs=0;for(int y=0;y<pixels.getHeight();y++)for(int x=0;x<pixels.getWidth();x++){
        int pixel=pixels.getPixel(x,y);if(Color.alpha(pixel)>240&&near(pixel,renderedInk))glyphs++;
      }
      assertTrue("Real native-rendered glyph pixels are visible, not only a stored color: "+text.getText()+" / "+glyphs,glyphs>8);
      assertTrue("Rendered glyph/background contrast: "+text.getText(),contrast(renderedInk,surface)>=4.5);
    }finally{pixels.recycle();}
  }
  static void save(Bitmap b,String name)throws Exception{
    File folder=new File(System.getProperty("cobra.evidence","build/cobra204-dialog-evidence"));assertTrue(folder.isDirectory()||folder.mkdirs());
    try(FileOutputStream out=new FileOutputStream(new File(folder,"cobra204-dialog-"+name+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}
  }
  void nativeDialog(String mode)throws Exception{
    AlertDialog d=builder(mode).setTitle("Delete recording?").setMessage("This removes the selected recording only.")
        .setPositiveButton("DELETE",null).setNegativeButton("CANCEL",null).show();
    View decor=layout(d);Bitmap pixels=render(decor);
    try{
      int surface=pixels.getPixel(pixels.getWidth()/2,10);boolean light=mode.equals("light");
      assertTrue("Actual dialog surface matches the selected appearance",light?luminance(surface)>.9:luminance(surface)<.035);
      rasterizedText(text(decor,"Delete recording?"),light?0xff101b2c:0xfff7faff,surface);
      rasterizedText(text(decor,"This removes the selected recording only."),light?0xff101b2c:0xfff7faff,surface);
      rasterizedText(d.getButton(AlertDialog.BUTTON_POSITIVE),light?0xff145fdf:0xff62aaff,surface);
      rasterizedText(d.getButton(AlertDialog.BUTTON_NEGATIVE),light?0xff145fdf:0xff62aaff,surface);
      save(pixels,mode+"-title-body-actions");
    }finally{pixels.recycle();}
  }
  @Test public void lightDialogRendersReadableTitleBodyAndBlueActions()throws Exception{nativeDialog("light");}
  @Test public void darkDialogRendersReadableTitleBodyAndBlueActions()throws Exception{nativeDialog("dark");}
  @Test public void oledDialogRendersReadableTitleBodyAndBlueActions()throws Exception{nativeDialog("oled");}

  @Test public void createdDialogPreservesValidationOnShowAndCustomButtonCallback(){
    int[] events={0,0};AlertDialog d=builder("light").setTitle("TV source").setPositiveButton("TEST & SAVE",null).create();
    d.setOnShowListener(ignored->{events[0]++;d.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->events[1]++);});
    d.show();layout(d);assertEquals(1,events[0]);assertTrue(d.getButton(AlertDialog.BUTTON_POSITIVE).performClick());frames();
    assertEquals(1,events[1]);assertTrue("Validation listener owns dismissal",d.isShowing());
    d.dismiss();frames();d.show();layout(d);assertEquals(2,events[0]);
    assertTrue(d.getButton(AlertDialog.BUTTON_POSITIVE).performClick());frames();assertEquals(2,events[1]);assertTrue(d.isShowing());
  }
  @Test public void builderShowPreservesNativeButtonActionAndDismissal(){
    int[] actions={0};AlertDialog d=builder("dark").setTitle("Delete recording?").setPositiveButton("DELETE",(dialog,which)->actions[0]++).show();
    layout(d);assertTrue(d.getButton(AlertDialog.BUTTON_POSITIVE).performClick());frames();assertEquals(1,actions[0]);assertFalse(d.isShowing());frames();assertEquals(1,actions[0]);
  }
  @Test public void disabledNativeActionHasDistinctRenderedStateAndCannotClick(){
    for(String mode:new String[]{"light","dark"}){
      int[] clicks={0};AlertDialog d=builder(mode).setTitle("Checking source").setPositiveButton("TEST & SAVE",(dialog,which)->clicks[0]++).show();
      layout(d);Button button=d.getButton(AlertDialog.BUTTON_POSITIVE);int enabled=button.getCurrentTextColor();
      button.setEnabled(false);frames();int disabled=button.getCurrentTextColor();
      assertNotEquals("Disabled validation action must not look enabled",enabled,disabled);
      rasterizedText(button,disabled,mode.equals("light")?Color.WHITE:0xff0b0f16);
      long t=android.os.SystemClock.uptimeMillis();
      android.view.MotionEvent down=android.view.MotionEvent.obtain(t,t,android.view.MotionEvent.ACTION_DOWN,button.getWidth()/2f,button.getHeight()/2f,0);
      android.view.MotionEvent up=android.view.MotionEvent.obtain(t,t+20,android.view.MotionEvent.ACTION_UP,button.getWidth()/2f,button.getHeight()/2f,0);
      try{button.dispatchTouchEvent(down);button.dispatchTouchEvent(up);}finally{down.recycle();up.recycle();}
      frames();assertEquals(0,clicks[0]);assertTrue(d.isShowing());
      button.setEnabled(true);frames();assertEquals(enabled,button.getCurrentTextColor());d.dismiss();frames();
    }
  }
  @Test public void keyedAndUnkeyedDecorTagsRemainOwnedByCaller(){
    AlertDialog d=builder("dark").setTitle("Preserved tags").create();View decor=d.getWindow().getDecorView();
    // setTag with a framework ID throws on Android. A legal app-owned key and
    // ordinary tag must both survive; the framework custom key stays untouched.
    int callerKey=0x7f020001;Object marker=new Object();decor.setTag(callerKey,marker);decor.setTag("caller-tag");d.show();layout(d);
    assertSame(marker,decor.getTag(callerKey));assertEquals("caller-tag",decor.getTag());assertNull(decor.getTag(android.R.id.custom));
  }
  @Test public void customFormKeepsItsFontStateColorsHintAndInputBackground(){
    EditText field=new EditText(activity);field.setText("Source name");field.setHint("Name");
    Typeface font=Typeface.create("monospace",Typeface.BOLD);field.setTypeface(font);
    ColorStateList ink=new ColorStateList(new int[][]{new int[]{-android.R.attr.state_enabled},new int[]{}},new int[]{Color.GRAY,Color.MAGENTA});
    ColorStateList hints=ColorStateList.valueOf(Color.CYAN),tint=ColorStateList.valueOf(Color.GREEN);
    field.setTextColor(ink);field.setHintTextColor(hints);field.setBackgroundTintList(tint);
    LinearLayout form=new LinearLayout(activity);form.addView(field,new LinearLayout.LayoutParams(-1,64));
    AlertDialog d=builder("light").setTitle("Source").setView(form).setPositiveButton("SAVE",null).show();layout(d);
    assertSame(font,field.getTypeface());assertSame(ink,field.getTextColors());assertSame(hints,field.getHintTextColors());assertSame(tint,field.getBackgroundTintList());
    assertSame(form,field.getParent());assertEquals("Source name",field.getText().toString());
  }
  @Test public void importedDialogStylingWinsAfterShowLayoutAndReshow()throws Exception{
    // Exercise production resolution with an in-memory theme, not its separately
    // tested ZIP installer. No fallback may overwrite a resolved imported style.
    CobraVisualRenderer.active.data.put("base",new JSONObject().put("styles",new JSONObject()
        .put("dialog.button",new JSONObject().put("text","#8234AC").put("font_family","serif"))));
    AlertDialog d=builder("light").setTitle("Imported appearance").setPositiveButton("CONFIRM",null).show();
    for(int i=0;i<3;i++){
      View decor=layout(d);rasterizedText(d.getButton(AlertDialog.BUTTON_POSITIVE),0xff8234ac,Color.WHITE);
      assertEquals(Typeface.create("serif",Typeface.NORMAL),d.getButton(AlertDialog.BUTTON_POSITIVE).getTypeface());
      Bitmap b=render(decor);try{save(b,"imported-button-pass-"+i);}finally{b.recycle();}
      d.dismiss();frames();if(i<2)d.show();
    }
  }
  @Test public void actualListRowsStayReadableAndKeepOriginalSelectionAction()throws Exception{
    for(String mode:new String[]{"light","dark","oled"}){
      int[] choice={-1};AlertDialog d=builder(mode).setTitle("Add TV source").setItems(new String[]{"Xtream-compatible login","M3U / M3U8 playlist"},(dialog,which)->choice[0]=which).show();
      View decor=layout(d);ListView list=d.getListView();assertNotNull(list);assertEquals(2,list.getChildCount());
      Bitmap pixels=render(decor);
      try{
        int surface=pixels.getPixel(pixels.getWidth()/2,10);
        for(int i=0;i<list.getChildCount();i++){
          TextView row=text(list.getChildAt(i),i==0?"Xtream-compatible login":"M3U / M3U8 playlist");
          assertNotNull(row);rasterizedText(row,row.getCurrentTextColor(),surface);
        }
        save(pixels,mode+"-source-list");
      }finally{pixels.recycle();}
      assertTrue(list.performItemClick(list.getChildAt(1),1,list.getAdapter().getItemId(1)));frames();assertEquals(1,choice[0]);assertFalse(d.isShowing());
    }
  }
  static void hasBlueCheck(CheckedTextView row,int blue)throws Exception{
    assertTrue(row.isChecked());Bitmap image=render(row);
    try{int count=0;for(int y=0;y<image.getHeight();y++)for(int x=0;x<image.getWidth();x++)if(near(image.getPixel(x,y),blue)&&Color.alpha(image.getPixel(x,y))>240)count++;
      assertTrue("Native checked glyph actually renders the selected blue, not framework teal: "+count,count>8);
    }finally{image.recycle();}
  }
  @Test public void singleChoiceNativeChecksRenderBlueAndRetainRadioSemantics()throws Exception{
    for(String mode:new String[]{"light","dark"}){
      int[] events={0,-1};AlertDialog d=builder(mode).setTitle("Guide density").setSingleChoiceItems(new String[]{"Comfortable","Compact"},0,(dialog,which)->{events[0]++;events[1]=which;}).show();
      View decor=layout(d);ListView list=d.getListView();int blue=mode.equals("light")?0xff145fdf:0xff62aaff;
      hasBlueCheck((CheckedTextView)list.getChildAt(0),blue);
      assertTrue(list.performItemClick(list.getChildAt(1),1,list.getAdapter().getItemId(1)));frames();
      assertEquals(1,events[0]);assertEquals(1,events[1]);assertEquals(1,list.getCheckedItemPosition());assertFalse(((CheckedTextView)list.getChildAt(0)).isChecked());hasBlueCheck((CheckedTextView)list.getChildAt(1),blue);
      Bitmap b=render(decor);try{save(b,mode+"-single-choice");}finally{b.recycle();}d.dismiss();frames();
    }
  }
  @Test public void multipleChoiceNativeChecksRenderBlueAndKeepIndependentState()throws Exception{
    int[] events={0};AlertDialog d=builder("dark").setTitle("Existing choices").setMultiChoiceItems(new String[]{"First","Second"},new boolean[]{true,false},(dialog,which,checked)->events[0]++).show();
    View decor=layout(d);ListView list=d.getListView();hasBlueCheck((CheckedTextView)list.getChildAt(0),0xff62aaff);
    assertTrue(list.performItemClick(list.getChildAt(1),1,list.getAdapter().getItemId(1)));frames();
    assertTrue(list.isItemChecked(0));assertTrue(list.isItemChecked(1));assertEquals(1,events[0]);hasBlueCheck((CheckedTextView)list.getChildAt(1),0xff62aaff);
    Bitmap b=render(decor);try{save(b,"dark-multiple-choice");}finally{b.recycle();}
  }
  @Test public void recycledChoiceRowsAndReshownDialogRetainBlueChecks()throws Exception{
    String[] labels=new String[60];for(int i=0;i<labels.length;i++)labels[i]="Category "+i;
    AlertDialog d=builder("dark").setTitle("Choose category").setSingleChoiceItems(labels,0,(dialog,which)->{}).show();layout(d);
    ListView list=d.getListView();assertTrue(list.getChildCount()<labels.length);
    for(int target:new int[]{40,5,55,0}){
      list.setItemChecked(target,true);list.setSelectionFromTop(target,0);list.forceLayout();list.measure(View.MeasureSpec.makeMeasureSpec(list.getWidth(),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(list.getHeight(),View.MeasureSpec.EXACTLY));list.layout(list.getLeft(),list.getTop(),list.getRight(),list.getBottom());layout(d);
      int child=target-list.getFirstVisiblePosition();assertTrue("Target="+target+" first="+list.getFirstVisiblePosition()+" children="+list.getChildCount()+" selected="+list.getSelectedItemPosition(),child>=0&&child<list.getChildCount());
      hasBlueCheck((CheckedTextView)list.getChildAt(child),0xff62aaff);
    }
    d.dismiss();frames();d.show();layout(d);hasBlueCheck((CheckedTextView)list.getChildAt(0),0xff62aaff);
  }
  @Test public void plainNativeListFocusRendersBlueSelectorWithoutChoiceGlyphs()throws Exception{
    AlertDialog d=builder("light").setTitle("Add TV source").setItems(new String[]{"Xtream-compatible login","M3U / M3U8 playlist"},(dialog,which)->{}).show();layout(d);
    ListView list=d.getListView();assertTrue(list.requestFocusFromTouch());list.setSelection(1);list.forceLayout();list.measure(View.MeasureSpec.makeMeasureSpec(list.getWidth(),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(list.getHeight(),View.MeasureSpec.EXACTLY));list.layout(list.getLeft(),list.getTop(),list.getRight(),list.getBottom());layout(d);assertTrue(list.hasFocus());
    list.refreshDrawableState();assertTrue("D-pad selector host itself has focus",list.isFocused());Bitmap pixels=render(list);
    try{int blue=0;for(int y=0;y<pixels.getHeight();y++)for(int x=0;x<pixels.getWidth();x++)if(near(pixels.getPixel(x,y),0xff145fdf)&&Color.alpha(pixels.getPixel(x,y))>240)blue++;
      assertTrue("Actual focused native list selector renders blue trim: "+blue+" / "+list.getSelector().getBounds()+" / "+java.util.Arrays.toString(list.getSelector().getState())+" / selected="+list.getSelectedItemPosition()+" touch="+list.isInTouchMode()+" windowFocus="+list.hasWindowFocus()+" enabled="+list.isEnabled(),blue>8);
      Bitmap window=render(d.getWindow().getDecorView());try{save(window,"light-native-list-focus");}finally{window.recycle();}
    }finally{pixels.recycle();}
  }
  static int choiceObservers(android.view.ViewTreeObserver observer){
    Object listeners=org.robolectric.util.ReflectionHelpers.getField(observer,"mOnPreDrawListeners");if(listeners==null)return 0;
    java.util.List<?> data=org.robolectric.util.ReflectionHelpers.getField(listeners,"mData");int count=0;
    for(Object listener:data)if(listener.getClass().getName().endsWith("ChoiceTint"))count++;return count;
  }
  @Test public void repeatedDetachAndReshowKeepOneChoiceObserverAndNativeArtwork()throws Exception{
    AlertDialog d=builder("dark").setTitle("Guide density").setSingleChoiceItems(new String[]{"Comfortable","Compact"},0,(dialog,which)->{}).create();
    for(int i=0;i<8;i++){
      d.show();layout(d);ListView list=d.getListView();android.view.ViewTreeObserver observer=list.getViewTreeObserver();
      assertEquals("Exactly one bounded visible-row observer",1,choiceObservers(observer));
      CheckedTextView row=(CheckedTextView)list.getChildAt(0);hasBlueCheck(row,0xff62aaff);
      android.graphics.drawable.Drawable[] artwork=row.getCompoundDrawablesRelative();frames();
      assertArrayEquals("Native choice artwork is tinted, never replaced",artwork,row.getCompoundDrawablesRelative());
      d.dismiss();frames();if(observer.isAlive())assertEquals("Detached window must not retain the callback",0,choiceObservers(observer));
    }
  }
}
