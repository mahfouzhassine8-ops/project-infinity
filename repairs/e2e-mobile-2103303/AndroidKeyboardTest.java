package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Looper;
import android.view.inputmethod.EditorInfo;
import java.util.ArrayList;
import java.util.List;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
public class AndroidKeyboardTest {
  static final class Capture implements InfinityAndroidKeyboard.Sink {
    final List<String> changes=new ArrayList<>();int completed;boolean accepted;String finalText;
    public void change(long token,String text,boolean done,boolean keep){
      if(done){completed++;accepted=keep;finalText=text;}else changes.add(text);
    }
  }
  @Test public void unicodeEditsAndSearchSubmitExactlyOnce(){
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();Capture sink=new Capture();
    InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(a,1,"initial","Search",false,true,sink);
    e.input.setText("été العربية 🎬");
    e.input.onEditorAction(EditorInfo.IME_ACTION_SEARCH);
    e.finish(true);
    assertEquals("été العربية 🎬",sink.finalText);assertTrue(sink.accepted);assertEquals(1,sink.completed);
    assertFalse(e.dialog.isShowing());assertEquals("",e.input.getText().toString());
  }
  @Test public void passwordMasksAndDisablesSavedViewState(){
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();Capture sink=new Capture();
    InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(a,2,"secret","Password",true,false,sink);
    assertTrue(e.input.getTransformationMethod() instanceof android.text.method.PasswordTransformationMethod);
    assertFalse(e.input.isSaveEnabled());e.finish(false);assertFalse(sink.accepted);
  }
  @Test public void remoteReplacementPreservesSelectionAndIgnoresStaleToken(){
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();Capture sink=new Capture();
    InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(a,3,"abcdef","Path",false,false,sink);
    e.input.setSelection(2,4);
    InfinityAndroidKeyboard.replace(2,"stale",false);shadowOf(Looper.getMainLooper()).idle();
    assertEquals("abcdef",e.input.getText().toString());
    InfinityAndroidKeyboard.replace(3,"abcdefgh",false);shadowOf(Looper.getMainLooper()).idle();
    assertEquals(2,e.input.getSelectionStart());assertEquals(4,e.input.getSelectionEnd());e.finish(false);
  }
  @Test public void ownerPauseCancelsWithoutSubmittingAndOldOwnerCannotCloseNewEditor(){
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();
    Activity b=Robolectric.buildActivity(Activity.class).setup().get();Capture first=new Capture(),second=new Capture();
    InfinityAndroidKeyboard.show(a,4,"one","Name",false,false,first);
    InfinityAndroidKeyboard.Editor e=InfinityAndroidKeyboard.show(b,5,"two","Name",false,false,second);
    assertEquals(1,first.completed);assertFalse(first.accepted);
    InfinityAndroidKeyboard.cancelOwner(a);assertTrue(e.dialog.isShowing());
    InfinityAndroidKeyboard.cancelOwner(b);assertFalse(e.dialog.isShowing());assertEquals(1,second.completed);
  }
  @Test public void mobileUsesIMEAndTelevisionKeepsRemoteKeyboard(){
    Activity a=Robolectric.buildActivity(Activity.class).setup().get();
    shadowOf(a.getPackageManager()).setSystemFeature(PackageManager.FEATURE_TOUCHSCREEN,true);
    shadowOf(a.getPackageManager()).setSystemFeature(PackageManager.FEATURE_LEANBACK,false);
    assertTrue(InfinityAndroidKeyboard.isMobile(a));
    shadowOf(a.getPackageManager()).setSystemFeature(PackageManager.FEATURE_LEANBACK,true);
    assertFalse(InfinityAndroidKeyboard.isMobile(a));
  }
}
