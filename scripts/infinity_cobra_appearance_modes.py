#!/usr/bin/env python3
"""Add Cobra Light, Dark, True OLED Black and Follow System appearance modes.

Android presentation-shell only. This pass runs after the modern Mobile/TV
presentation transform and changes presentation colors/settings only. Kodi
native, renderer, playback/provider ownership, rotation/Fold,
background/resume and Infinity handoff remain protected.

The selected mode is stored in Cobra profile preferences. Built-in palettes
make every mode usable without an external package; optional matching palettes
inside cobra-theme.json override those built-ins so later color tuning remains
ZIP-driven without another APK build.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Appearance {label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def patch(java: str) -> str:
    # The modern mobile pass owns this state anchor, so appearance support is
    # guaranteed to be layered after 2103147 rather than onto an older shell.
    java = once(
        java,
        '  private static final String COBRA_CUSTOM_GROUP_PREFIX = "cobra_custom_group|";\n',
        '  private static final String COBRA_CUSTOM_GROUP_PREFIX = "cobra_custom_group|";\n'
        '  private static final String COBRA_APPEARANCE_MODE = "cobra_appearance_mode";\n'
        '  private long mCobraPaletteSourceStamp = Long.MIN_VALUE;\n'
        '  private JSONObject mCobraPaletteCache;\n',
        "state",
    )

    # Put Appearance directly in Cobra Settings alongside the existing Guide
    # view control. It is intentionally not hidden in the theme ZIP installer.
    controls_old = (
        '    Button guideView = action("GUIDE VIEW  •  " + cobraGuideViewLabel());\n'
        '    guideView.setOnClickListener(v -> showCobraGuideViewPicker(false));\n\n'
        '    TextView uiState = text(activeCobraUiLabel(), mTheme.accentSoft, 13,\n'
    )
    controls_new = (
        '    Button guideView = action("GUIDE VIEW  •  " + cobraGuideViewLabel());\n'
        '    guideView.setOnClickListener(v -> showCobraGuideViewPicker(false));\n\n'
        '    Button appearance = action("APPEARANCE  •  " + cobraAppearanceLabel());\n'
        '    appearance.setOnClickListener(v -> showCobraAppearancePicker());\n\n'
        '    TextView uiState = text(activeCobraUiLabel(), mTheme.accentSoft, 13,\n'
    )
    java = once(java, controls_old, controls_new, "settings control")

    list_old = (
        '    list.addView(guideView, new LinearLayout.LayoutParams(\n'
        '        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n'
        '    list.addView(uiState, new LinearLayout.LayoutParams(\n'
    )
    list_new = (
        '    list.addView(guideView, new LinearLayout.LayoutParams(\n'
        '        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n'
        '    list.addView(appearance, new LinearLayout.LayoutParams(\n'
        '        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n'
        '    list.addView(uiState, new LinearLayout.LayoutParams(\n'
    )
    java = once(java, list_old, list_new, "settings list")

    helpers = r'''  private String cobraStoredAppearanceMode() {
    String value = mPrefs == null ? "dark" : mPrefs.getString(COBRA_APPEARANCE_MODE, "dark");
    if ("system".equals(value) || "light".equals(value)
        || "dark".equals(value) || "oled".equals(value)) return value;
    return "dark";
  }

  private String cobraEffectiveAppearanceMode() {
    String stored = cobraStoredAppearanceMode();
    if (!"system".equals(stored)) return stored;
    int night = getResources().getConfiguration().uiMode
        & android.content.res.Configuration.UI_MODE_NIGHT_MASK;
    return night == android.content.res.Configuration.UI_MODE_NIGHT_YES ? "dark" : "light";
  }

  private String cobraAppearanceLabel() {
    String stored = cobraStoredAppearanceMode();
    if ("system".equals(stored))
      return "FOLLOW SYSTEM  •  " + ("dark".equals(cobraEffectiveAppearanceMode()) ? "DARK" : "LIGHT");
    if ("light".equals(stored)) return "LIGHT";
    if ("oled".equals(stored)) return "TRUE OLED BLACK";
    return "DARK";
  }

  private void showCobraAppearancePicker() {
    final String[] labels = {"Follow System", "Light", "Dark", "True OLED Black"};
    final String[] values = {"system", "light", "dark", "oled"};
    String current = cobraStoredAppearanceMode();
    int checked = 2;
    for (int i = 0; i < values.length; i++) if (values[i].equals(current)) checked = i;
    new AlertDialog.Builder(this)
        .setTitle("Cobra Appearance")
        .setSingleChoiceItems(labels, checked, (dialog, which) -> {
          mPrefs.edit().putString(COBRA_APPEARANCE_MODE, values[which]).apply();
          mCobraPaletteSourceStamp = Long.MIN_VALUE;
          mCobraPaletteCache = null;
          dialog.dismiss();
          // Settings navigation has already stopped inline preview. Never tear
          // down active fullscreen/Multi-View playback merely for a color mode.
          if (mPlayerOverlay != null || mMultiOverlay != null) {
            toast("Appearance will apply when you leave playback");
            return;
          }
          mTheme = Theme.load(this);
          buildShell();
          showSettings();
          toast("Cobra appearance • " + cobraAppearanceLabel());
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private JSONObject cobraAppearancePalette(String mode) {
    try {
      File external = getExternalFilesDir(null);
      if (external == null) return null;
      File file = new File(external,
          ".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json");
      if (!file.isFile() || file.length() <= 0 || file.length() > 131072) return null;
      long stamp = file.lastModified() ^ file.length();
      if (stamp != mCobraPaletteSourceStamp) {
        mCobraPaletteSourceStamp = stamp;
        mCobraPaletteCache = null;
        JSONObject root = new JSONObject(readText(new java.io.FileInputStream(file)));
        if (root.optInt("schema", 0) >= 1 && root.optInt("schema", 0) <= 2)
          mCobraPaletteCache = root.optJSONObject("palettes");
      }
      return mCobraPaletteCache == null ? null : mCobraPaletteCache.optJSONObject(mode);
    } catch (Exception ignored) {
      return null;
    }
  }

  private int cobraBuiltInAppearanceColor(String mode, String key, int fallback) {
    if ("light".equals(mode)) {
      if ("background".equals(key)) return android.graphics.Color.rgb(245, 247, 251);
      if ("rail".equals(key)) return android.graphics.Color.rgb(255, 255, 255);
      if ("panel".equals(key)) return android.graphics.Color.rgb(255, 255, 255);
      if ("panel2".equals(key)) return android.graphics.Color.rgb(234, 240, 246);
      if ("focus".equals(key)) return android.graphics.Color.rgb(11, 99, 206);
      if ("accent".equals(key)) return android.graphics.Color.rgb(11, 127, 219);
      if ("accent_soft".equals(key)) return android.graphics.Color.rgb(42, 139, 216);
      if ("text".equals(key)) return android.graphics.Color.rgb(16, 23, 34);
      if ("muted".equals(key)) return android.graphics.Color.rgb(95, 111, 128);
      if ("line".equals(key)) return android.graphics.Color.rgb(203, 214, 226);
    } else if ("oled".equals(mode)) {
      if ("background".equals(key)) return android.graphics.Color.BLACK;
      if ("rail".equals(key)) return android.graphics.Color.BLACK;
      if ("panel".equals(key)) return android.graphics.Color.rgb(5, 5, 5);
      if ("panel2".equals(key)) return android.graphics.Color.rgb(10, 10, 10);
      if ("focus".equals(key)) return android.graphics.Color.rgb(9, 95, 216);
      if ("accent".equals(key)) return android.graphics.Color.rgb(36, 183, 255);
      if ("accent_soft".equals(key)) return android.graphics.Color.rgb(123, 214, 255);
      if ("text".equals(key)) return android.graphics.Color.WHITE;
      if ("muted".equals(key)) return android.graphics.Color.rgb(168, 183, 198);
      if ("line".equals(key)) return android.graphics.Color.rgb(29, 39, 48);
    }
    // Dark intentionally falls back to Theme.load(), preserving the current
    // Cobra palette when no ZIP palette override is installed.
    return fallback;
  }

  private int cobraThemeColor(String key, int fallback) {
    String mode = cobraEffectiveAppearanceMode();
    JSONObject palette = cobraAppearancePalette(mode);
    if (palette != null) {
      String encoded = palette.optString(key, "");
      if (encoded != null && !encoded.isEmpty()) {
        try { return android.graphics.Color.parseColor(encoded); }
        catch (IllegalArgumentException ignored) {}
      }
    }
    return cobraBuiltInAppearanceColor(mode, key, fallback);
  }

'''
    java = once(
        java,
        "  private boolean closeCobraExperienceDrawer() {\n",
        helpers + "  private boolean closeCobraExperienceDrawer() {\n",
        "helpers",
    )

    # Route only visual color tokens through the appearance resolver. Geometry,
    # motion, touch targets and player behavior remain the existing Runtime-v3
    # contracts. The replacement runs once per field so the fallback expression
    # inside the inserted call is not recursively rewritten.
    fields = (
        ("accentSoft", "accent_soft"),
        ("background", "background"),
        ("panel2", "panel2"),
        ("accent", "accent"),
        ("focus", "focus"),
        ("muted", "muted"),
        ("panel", "panel"),
        ("rail", "rail"),
        ("text", "text"),
        ("line", "line"),
    )
    counts = {}
    for field, key in fields:
        pattern = rf"\bmTheme\.{field}\b"
        replacement = f'cobraThemeColor("{key}", mTheme.{field})'
        java, count = re.subn(pattern, replacement, java)
        if count < 1:
            raise RuntimeError(f"Appearance color token missing: mTheme.{field}")
        counts[field] = count

    return java


def verify(java: str) -> None:
    required = (
        'COBRA_APPEARANCE_MODE = "cobra_appearance_mode"',
        'APPEARANCE  •  " + cobraAppearanceLabel()',
        'showCobraAppearancePicker()',
        '"Follow System", "Light", "Dark", "True OLED Black"',
        'cobraEffectiveAppearanceMode()',
        'cobraAppearancePalette(String mode)',
        'optJSONObject("palettes")',
        'cobraThemeColor("background", mTheme.background)',
        'cobraThemeColor("text", mTheme.text)',
        'cobraThemeColor("accent", mTheme.accent)',
        'cobraThemeColor("line", mTheme.line)',
        'mGuidePreviewArmed',
        'setTag("cobra_experience_drawer")',
        'moveTaskToBack(true);',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Appearance contract missing: " + token)
    # Video readability is explicitly protected: the modern mini-player keeps
    # a true black video host and translucent black control chrome in Light mode.
    for token in ('host.setBackground(surface(Color.BLACK', 'controls.setBackgroundColor(Color.argb(158, 0, 0, 0))'):
        if token not in java:
            raise RuntimeError("Appearance video-overlay protection missing: " + token)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra Follow System / Light / Dark / True OLED Black appearance runtime applied")


if __name__ == "__main__":
    main()
