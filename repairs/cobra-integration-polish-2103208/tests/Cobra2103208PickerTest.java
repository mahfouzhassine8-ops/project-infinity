package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Application;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.view.View;
import java.util.HashMap;
import java.util.Map;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Exercises the actual Activity picker entry points and Android intent contract.
 * Does not claim to verify OEM resolver contents or third-party app compatibility. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103208PickerTest {
  Cobra2103201SubtitleTest f;
  InfinityLiveActivity a;
  SharedPreferences prefs;
  static final String MODE="cobra_file_picker_mode";
  static final String[] ZIP_TYPES={"application/zip","application/x-zip-compressed","application/octet-stream"};

  @Before public void before()throws Exception{
    f=new Cobra2103201SubtitleTest();f.before();a=f.a;
    prefs=(SharedPreferences)CobraNavigationUiTest.get(a,"mPrefs");
  }
  @After public void after()throws Exception{if(f!=null)f.after();}
  Object call(String name,Object...args)throws Exception{return CobraNavigationUiTest.call(a,name,args);}
  Intent next(){return Shadows.shadowOf(a).getNextStartedActivityForResult().intent;}
  Intent target(Intent chooser){
    assertEquals(Intent.ACTION_CHOOSER,chooser.getAction());
    Intent target=chooser.getParcelableExtra(Intent.EXTRA_INTENT);
    assertNotNull(target);assertEquals(Intent.ACTION_GET_CONTENT,target.getAction());
    assertNull("No vendor or remembered app may bypass Ask",target.getComponent());
    assertNull("Do not force Samsung or any other package",target.getPackage());
    assertTrue(target.hasCategory(Intent.CATEGORY_OPENABLE));
    assertTrue((target.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
    assertEquals(0,target.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
    return target;
  }

  @Test public void askLaunchesAndroidChooserOnEveryRequestWithoutIntermediateSheet()throws Exception{
    prefs.edit().putString(MODE,"ask").commit();
    for(int i=0;i<2;i++){
      call("cobraOpenFilePicker",4173,"application/zip",ZIP_TYPES,false);
      Intent file=target(next());assertEquals("*/*",file.getType());assertArrayEquals(ZIP_TYPES,file.getStringArrayExtra(Intent.EXTRA_MIME_TYPES));
      assertNull("Ask no longer opens System-versus-Files source sheet",CobraNavigationUiTest.get(a,"mCobraActionSheet"));
      assertEquals("ask",prefs.getString(MODE,""));
    }
  }

  @Test public void unsetPreferenceDefaultsToRealAppChooserWithoutWritingPreference()throws Exception{
    prefs.edit().remove(MODE).commit();call("openCobraUiPackagePicker");target(next());assertFalse(prefs.contains(MODE));
  }

  @Test public void invalidPreferenceSafelyAsksWithoutChangingSavedValue()throws Exception{
    prefs.edit().putString(MODE,"unrecognized").commit();call("openCobraUiPackagePicker");target(next());assertEquals("unrecognized",prefs.getString(MODE,""));
  }

  @Test public void actualThemeInstallRowRoutesThroughAskAndLeavesPlaybackUntouched()throws Exception{
    prefs.edit().putString(MODE,"ask").commit();
    Object player=CobraNavigationUiTest.get(a,"mPlayer"),channel=CobraNavigationUiTest.get(a,"mPlaying");
    int trackWrites=f.fake.parameterWrites;
    call("showCobraVisualThemePicker");f.ui.measure(a,412,915);
    View row=a.getWindow().getDecorView().findViewWithTag("cobra_theme_install");assertNotNull(row);assertTrue(row.performClick());
    org.robolectric.shadows.ShadowActivity.IntentForResult launch=Shadows.shadowOf(a).getNextStartedActivityForResult();
    assertEquals(4173,launch.requestCode);Intent file=target(launch.intent);
    assertEquals("*/*",file.getType());assertArrayEquals(ZIP_TYPES,file.getStringArrayExtra(Intent.EXTRA_MIME_TYPES));
    assertNull(CobraNavigationUiTest.get(a,"mCobraActionSheet"));
    assertSame(player,CobraNavigationUiTest.get(a,"mPlayer"));assertSame(channel,CobraNavigationUiTest.get(a,"mPlaying"));
    assertEquals(trackWrites,f.fake.parameterWrites);
  }

  @Test public void explicitSystemSelectionKeepsDocumentContractAndPersistableGrant()throws Exception{
    prefs.edit().putString(MODE,"system").commit();
    call("cobraOpenFilePicker",4172,"*/*",new String[]{"video/*","audio/*"},true);
    Intent file=next();assertEquals(Intent.ACTION_OPEN_DOCUMENT,file.getAction());assertTrue(file.hasCategory(Intent.CATEGORY_OPENABLE));
    assertTrue((file.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);assertTrue((file.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)!=0);
    assertArrayEquals(new String[]{"video/*","audio/*"},file.getStringArrayExtra(Intent.EXTRA_MIME_TYPES));assertEquals("system",prefs.getString(MODE,""));
  }

  @Test public void systemThemeImportKeepsZipAlternativesWithoutRequestingPersistentAccess()throws Exception{
    prefs.edit().putString(MODE,"system").commit();call("openCobraUiPackagePicker");Intent file=next();
    assertEquals(Intent.ACTION_OPEN_DOCUMENT,file.getAction());assertEquals("*/*",file.getType());assertArrayEquals(ZIP_TYPES,file.getStringArrayExtra(Intent.EXTRA_MIME_TYPES));
    assertEquals(0,file.getFlags()&Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
  }

  @Test public void savedFilesAppSelectionStillUsesChooserAndDoesNotClaimDurableAccess()throws Exception{
    prefs.edit().putString(MODE,"apps").commit();call("cobraOpenFilePicker",4172,"*/*",new String[]{"video/*","audio/*"},true);
    target(next());assertEquals("apps",prefs.getString(MODE,""));
  }

  @Test public void primaryTypeIsPreservedWhenThereAreNoMimeAlternatives()throws Exception{
    prefs.edit().putString(MODE,"ask").commit();call("cobraOpenFilePicker",4173,"application/zip",new String[0],false);
    Intent file=target(next());assertEquals("application/zip",file.getType());assertFalse(file.hasExtra(Intent.EXTRA_MIME_TYPES));
  }

  @Test public void pickerCancellationAndEmptyResultsPreserveThemePreferencesAndPlayer()throws Exception{
    prefs.edit().putString(MODE,"ask").putString("cobra_appearance_mode","oled").commit();
    Map<String,?> before=new HashMap<>(prefs.getAll());String pointer=CobraVisualTheme.readPointer(a).toString();
    Object player=CobraNavigationUiTest.get(a,"mPlayer"),channel=CobraNavigationUiTest.get(a,"mPlaying");
    call("onActivityResult",4173,Activity.RESULT_CANCELED,new Intent().setData(Uri.parse("content://picker/cancelled-theme.zip")));
    call("onActivityResult",4173,Activity.RESULT_OK,(Intent)null);
    call("onActivityResult",4173,Activity.RESULT_OK,new Intent());
    assertEquals(before,prefs.getAll());assertEquals(pointer,CobraVisualTheme.readPointer(a).toString());
    assertSame(player,CobraNavigationUiTest.get(a,"mPlayer"));assertSame(channel,CobraNavigationUiTest.get(a,"mPlaying"));
  }

  @Test public void settingsCopyExplainsActualAppChoiceAndProviderDistinction()throws Exception{
    prefs.edit().putString(MODE,"apps").commit();call("showCobraFilePickerPicker");f.ui.measure(a,412,915);
    assertNotNull(f.text(f.root(),"Choose a compatible file app for each request"));
    assertNotNull(f.text(f.root(),"Browse document providers through Android Storage Access Framework"));
    assertNull(f.text(f.root(),"Choose System or Files app whenever a file is requested"));
  }
}
