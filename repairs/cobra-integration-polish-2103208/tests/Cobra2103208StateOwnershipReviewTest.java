package com.projectinfinity.kodi;

import android.app.Application;
import android.view.View;
import android.widget.TextView;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Focused regressions from the final read-only presentation review. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103208StateOwnershipReviewTest {
  @Test public void quickPeekFavoriteGlyphMatchesSelectionOnOpenAndEachToggle()throws Exception {
    Cobra2103208QuickPeekLayoutTest f=new Cobra2103208QuickPeekLayoutTest();
    try {
      f.before();f.open();View favorite=f.f.tag("cobra-quick-peek-favorite");
      for(int i=0;i<3;i++) {
        boolean selected=favorite.isSelected();
        assertEquals(selected?"favorite_on":"favorite",CobraNavigationUiTest.get(favorite,"glyph"));
        assertEquals(selected?"Remove from favorites":"Add to favorites",favorite.getContentDescription());
        assertTrue(favorite.performClick());assertEquals(!selected,favorite.isSelected());
      }
      assertEquals(favorite.isSelected()?"favorite_on":"favorite",CobraNavigationUiTest.get(favorite,"glyph"));
      assertTrue(f.main.commands.isEmpty());
    } finally { f.after(); }
  }

  @Test public void guideDetailsRefreshCannotOverrideCentralizedStatusVisibility()throws Exception {
    Cobra2103208PresentationUiTest f=new Cobra2103208PresentationUiTest();
    try {
      f.before();assertNotNull(f.get("mCobraModeEyebrow"));assertNotNull(f.get("mCobraModeLayout"));
      TextView label=(TextView)f.tag("cobra_preview_label");assertNotNull(label);
      // A hidden, sanitized legacy label must stay hidden even without a READY player.
      f.put("mCobraPreviewPlayer",null);label.setText("");label.setVisibility(View.GONE);
      f.call("cobraRefreshModeDetails");assertEquals(View.GONE,label.getVisibility());
      // Conversely, READY alone cannot hide a status chosen by the state owner.
      Cobra2103208PresentationUiTest.TransportSpy spy=f.preview();
      label.setText("Paused");label.setVisibility(View.VISIBLE);
      f.call("cobraRefreshModeDetails");assertEquals(View.VISIBLE,label.getVisibility());
      assertEquals("Paused",label.getText().toString());assertTrue(spy.writes.isEmpty());
    } finally { f.after(); }
  }
}
