package com.projectinfinity.kodi;

/** One existing launch preference; no chooser, player, Main or exit operation. */
public final class InfinityAskEveryTimeActivity extends android.app.Activity {
  @Override public void onCreate(android.os.Bundle saved) {
    super.onCreate(saved);
    try {
      if (!"com.projectinfinity.kodi.action.ASK_EVERY_TIME".equals(getIntent().getAction())) return;
      android.content.SharedPreferences preferences =
          InfinityJavaPersistence.preferences(this, "infinity_experience", MODE_PRIVATE);
      // Same authoritative key and persistence wrapper used by the existing
      // Cobra/chooser action. Synchronous commit includes its existing durable
      // flush/readback and write admission. No independent preference is added.
      boolean committed = preferences.edit().remove("default").commit();
      boolean enabled = committed && !preferences.contains("default");
      android.widget.Toast.makeText(this,
          enabled ? "Ask every time enabled" : "Ask every time could not be saved",
          android.widget.Toast.LENGTH_SHORT).show();
    } catch (RuntimeException unavailable) {
      android.widget.Toast.makeText(this, "Ask every time could not be saved",
          android.widget.Toast.LENGTH_SHORT).show();
    } finally {
      // This NoDisplay helper finishes in onCreate, never displaying a screen
      // or finishing the current Infinity activity/session.
      finish();
    }
  }
}
