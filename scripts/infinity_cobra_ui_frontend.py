#!/usr/bin/env python3
"""Add the user-facing Cobra Runtime v3 UI package frontend.

Presentation-shell only. This patch adds a safe UI ZIP picker/installer, active UI
status, four Guide presentation modes, and a usable portrait category picker.
It deliberately uses RC3's guarded async helpers and does not touch Kodi native,
renderer, playback/provider ownership, rotation, Fold, or background ownership.
"""
from __future__ import annotations

import argparse
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Cobra UI frontend {label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch(java: str) -> str:
    java = once(
        java,
        "  private static final int REQUEST_LOCAL_MEDIA = 4172;\n",
        "  private static final int REQUEST_LOCAL_MEDIA = 4172;\n"
        "  private static final int REQUEST_COBRA_UI_PACKAGE = 4173;\n"
        '  private static final String GUIDE_VIEW_MODE = "guide_view_mode";\n',
        "request fields",
    )

    java = once(
        java,
        "    super.onActivityResult(requestCode, resultCode, data);\n"
        "    if (requestCode != REQUEST_LOCAL_MEDIA || resultCode != RESULT_OK || data == null || data.getData() == null) return;\n",
        "    super.onActivityResult(requestCode, resultCode, data);\n"
        "    if (requestCode == REQUEST_COBRA_UI_PACKAGE) {\n"
        "      if (resultCode == RESULT_OK && data != null && data.getData() != null)\n"
        "        installCobraUiPackage(data.getData());\n"
        "      return;\n"
        "    }\n"
        "    if (requestCode != REQUEST_LOCAL_MEDIA || resultCode != RESULT_OK || data == null || data.getData() == null) return;\n",
        "UI package result dispatch",
    )

    java = once(
        java,
        "  private void showGuide() {\n"
        "    showChannelBrowser(\"COBRA • GUIDE\", true, false, false);\n"
        "  }\n",
        "  private void showGuide() {\n"
        "    String mode = cobraGuideViewMode();\n"
        "    if (\"compact\".equals(mode)) showGuideCompact();\n"
        "    else if (\"cards\".equals(mode)) showChannelBrowser(\"COBRA • GUIDE\", true, false, false);\n"
        "    else if (\"focus\".equals(mode)) showGuideFocus();\n"
        "    else showGuideGrid();\n"
        "  }\n",
        "Guide mode dispatch",
    )

    java = once(
        java,
        "    if (!recentsOnly) {\n"
        "      ScrollView groupsScroll = new ScrollView(this);\n",
        "    if (!recentsOnly && isPortrait()) {\n"
        "      Button categoryPicker = action(\"CATEGORY  •  \" + mCategory + \"   ▾\");\n"
        "      categoryPicker.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);\n"
        "      categoryPicker.setOnClickListener(v -> showCobraCategoryPicker(\n"
        "          title, guideMode, favoritesOnly, recentsOnly));\n"
        "      LinearLayout.LayoutParams categoryPickerParams = new LinearLayout.LayoutParams(\n"
        "          LinearLayout.LayoutParams.MATCH_PARENT, dp(Math.max(56, mUi.portraitCategoryHeightDp)));\n"
        "      categoryPickerParams.bottomMargin = dp(8);\n"
        "      content.addView(categoryPicker, categoryPickerParams);\n"
        "    } else if (!recentsOnly) {\n"
        "      ScrollView groupsScroll = new ScrollView(this);\n",
        "portrait category selector",
    )

    java = once(
        java,
        '    Button reloadTheme = action("RELOAD COBRA UI THEME");\n',
        '    Button installUi = action("INSTALL COBRA UI PACKAGE");\n'
        '    installUi.setOnClickListener(v -> openCobraUiPackagePicker());\n\n'
        '    Button guideView = action("GUIDE VIEW  •  " + cobraGuideViewLabel());\n'
        '    guideView.setOnClickListener(v -> showCobraGuideViewPicker(false));\n\n'
        '    TextView uiState = text(activeCobraUiLabel(), mTheme.accentSoft, 13,\n'
        '        Gravity.LEFT | Gravity.CENTER_VERTICAL);\n\n'
        '    Button reloadTheme = action("RELOAD COBRA UI THEME");\n',
        "settings UI controls",
    )

    java = once(
        java,
        '      toast("Cobra theme reloaded");\n',
        '      toast("Cobra UI reloaded");\n',
        "reload wording",
    )

    java = once(
        java,
        "    list.addView(chooser, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n",
        "    list.addView(chooser, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n"
        "    list.addView(installUi, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(60)));\n"
        "    list.addView(guideView, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n"
        "    list.addView(uiState, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(48)));\n",
        "settings list controls",
    )

    settings_tail = (
        "    list.addView(themeInfo, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(160)));\n\n"
        "    mStage.addView(list, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));\n"
    )
    settings_tail_new = (
        "    list.addView(themeInfo, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(160)));\n\n"
        "    ScrollView settingsScroll = new ScrollView(this);\n"
        "    settingsScroll.addView(list);\n"
        "    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));\n"
    )
    java = once(java, settings_tail, settings_tail_new, "scrollable settings")

    helpers = r'''  private void openCobraUiPackagePicker() {
    Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
    intent.addCategory(Intent.CATEGORY_OPENABLE);
    intent.setType("application/zip");
    intent.putExtra(Intent.EXTRA_MIME_TYPES,
        new String[]{"application/zip", "application/x-zip-compressed", "application/octet-stream"});
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
    startActivityForResult(intent, REQUEST_COBRA_UI_PACKAGE);
  }

  private void installCobraUiPackage(Uri uri) {
    status("Installing Cobra UI package…");
    if (!submitCobraIo(() -> {
      try {
        Map<String, byte[]> files = new HashMap<>();
        int total = 0;
        try (InputStream raw = getContentResolver().openInputStream(uri);
             java.util.zip.ZipInputStream zip = new java.util.zip.ZipInputStream(raw)) {
          if (raw == null) throw new IllegalArgumentException("Could not open selected ZIP");
          java.util.zip.ZipEntry entry;
          while ((entry = zip.getNextEntry()) != null) {
            if (entry.isDirectory()) continue;
            String name = entry.getName().replace('\\', '/');
            if (name.startsWith("/") || name.contains("../") || name.contains("/.."))
              throw new IllegalArgumentException("Unsafe ZIP path");
            if (!name.startsWith("script.infinity.cobra.theme/")) continue;
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int n;
            while ((n = zip.read(buffer)) >= 0) {
              total += n;
              if (total > 16 * 1024 * 1024)
                throw new IllegalArgumentException("Cobra UI package is too large");
              out.write(buffer, 0, n);
            }
            files.put(name, out.toByteArray());
          }
        }

        String addonKey = "script.infinity.cobra.theme/addon.xml";
        String themeKey = "script.infinity.cobra.theme/resources/cobra-theme.json";
        String uiKey = "script.infinity.cobra.theme/resources/cobra-ui.json";
        if (!files.containsKey(addonKey) || !files.containsKey(themeKey) || !files.containsKey(uiKey))
          throw new IllegalArgumentException("ZIP is not a complete Cobra UI package");

        JSONObject ui = new JSONObject(new String(files.get(uiKey), StandardCharsets.UTF_8));
        if (ui.optInt("schema", 0) != 1)
          throw new IllegalArgumentException("Unsupported Cobra UI schema");
        JSONObject runtime = ui.optJSONObject("runtime");
        if (runtime == null || runtime.optInt("minimum_runtime", Integer.MAX_VALUE) > COBRA_UI_RUNTIME
            || !"cobra-live-only".equals(runtime.optString("scope", "")))
          throw new IllegalArgumentException("UI package is not compatible with this Cobra runtime");
        JSONObject contracts = ui.optJSONObject("protected_contracts");
        if (contracts == null) throw new IllegalArgumentException("Protected contracts are missing");
        for (String key : new String[]{"rotation", "fold", "background_resume", "renderer",
            "provider_playback", "infinity_handoff"}) {
          if (!"native".equals(contracts.optString(key, "")))
            throw new IllegalArgumentException("UI package attempted to own protected contract: " + key);
        }
        JSONObject theme = new JSONObject(new String(files.get(themeKey), StandardCharsets.UTF_8));
        if (theme.optInt("schema", 0) < 1 || theme.optInt("schema", 0) > 2)
          throw new IllegalArgumentException("Unsupported Cobra theme schema");

        File external = getExternalFilesDir(null);
        if (external == null) throw new IllegalStateException("External app storage unavailable");
        File addons = new File(external, ".kodi/addons");
        if (!addons.isDirectory() && !addons.mkdirs())
          throw new IllegalStateException("Could not create Cobra add-on directory");
        File target = new File(addons, "script.infinity.cobra.theme");
        File stage = new File(addons, ".cobra-ui-stage");
        File backup = new File(addons, ".cobra-ui-backup");
        deleteCobraUiTree(stage);
        deleteCobraUiTree(backup);
        if (!stage.mkdirs()) throw new IllegalStateException("Could not stage Cobra UI package");
        String prefix = "script.infinity.cobra.theme/";
        for (Map.Entry<String, byte[]> item : files.entrySet()) {
          String relative = item.getKey().substring(prefix.length());
          File staged = new File(stage, relative);
          File parent = staged.getParentFile();
          if (parent != null && !parent.isDirectory() && !parent.mkdirs())
            throw new IllegalStateException("Could not stage Cobra UI package directory");
          writeCobraUiBytes(staged, item.getValue());
        }

        boolean hadTarget = target.exists();
        if (hadTarget && !target.renameTo(backup))
          throw new IllegalStateException("Could not preserve previous Cobra UI package");
        if (!stage.renameTo(target)) {
          if (hadTarget) backup.renameTo(target);
          throw new IllegalStateException("Could not activate Cobra UI package");
        }
        deleteCobraUiTree(backup);

        publishCobraUi(() -> {
          mUi = UiContract.load(this);
          mTheme = Theme.load(this);
          buildShell();
          showSettings();
          toast("Cobra UI package installed");
        });
      } catch (Exception error) {
        publishCobraUi(() -> showError("Cobra UI package",
            "Install failed: " + (error.getMessage() == null
                ? error.getClass().getSimpleName() : error.getMessage())));
      }
    })) {
      toast("Cobra is closing; UI package was not installed");
    }
  }

  private void writeCobraUiBytes(File file, byte[] data) throws Exception {
    try (java.io.FileOutputStream out = new java.io.FileOutputStream(file)) {
      out.write(data);
      out.getFD().sync();
    }
  }

  private void deleteCobraUiTree(File file) {
    if (file == null || !file.exists()) return;
    if (file.isDirectory()) {
      File[] children = file.listFiles();
      if (children != null) for (File child : children) deleteCobraUiTree(child);
    }
    file.delete();
  }

  private String activeCobraUiLabel() {
    try {
      File external = getExternalFilesDir(null);
      if (external == null) return "ACTIVE UI  •  APK DEFAULT  •  RUNTIME 3";
      File addon = new File(external,
          ".kodi/addons/script.infinity.cobra.theme/addon.xml");
      if (!addon.isFile()) return "ACTIVE UI  •  APK DEFAULT  •  RUNTIME 3";
      String xml = readText(new java.io.FileInputStream(addon));
      Matcher match = Pattern.compile("version\\s*=\\s*\\\"([^\\\"]+)\\\"").matcher(xml);
      String version = match.find() ? match.group(1) : "external";
      return "ACTIVE UI  •  " + version + "  •  RUNTIME 3";
    } catch (Exception ignored) {
      return "ACTIVE UI  •  EXTERNAL PACKAGE  •  RUNTIME 3";
    }
  }

  private String cobraGuideViewMode() {
    String value = mPrefs.getString(GUIDE_VIEW_MODE, "grid");
    if ("grid".equals(value) || "compact".equals(value)
        || "cards".equals(value) || "focus".equals(value)) return value;
    return "grid";
  }

  private String cobraGuideViewLabel() {
    String mode = cobraGuideViewMode();
    if ("compact".equals(mode)) return "COMPACT";
    if ("cards".equals(mode)) return "CARDS";
    if ("focus".equals(mode)) return "FOCUS";
    return "TV GRID";
  }

  private void showCobraGuideViewPicker(boolean returnToGuide) {
    String[] labels = {"TV Grid", "Compact", "Cards", "Focus"};
    String[] values = {"grid", "compact", "cards", "focus"};
    int checked = 0;
    String current = cobraGuideViewMode();
    for (int i = 0; i < values.length; i++) if (values[i].equals(current)) checked = i;
    new AlertDialog.Builder(this)
        .setTitle("Cobra Guide view")
        .setSingleChoiceItems(labels, checked, (dialog, which) -> {
          mPrefs.edit().putString(GUIDE_VIEW_MODE, values[which]).apply();
          dialog.dismiss();
          if (returnToGuide) showGuide(); else showSettings();
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private void showCobraCategoryPicker(
      String title, boolean guideMode, boolean favoritesOnly, boolean recentsOnly) {
    ArrayList<String> categories = categoriesForCurrentChannels();
    String[] labels = categories.toArray(new String[0]);
    int checked = Math.max(0, categories.indexOf(mCategory));
    new AlertDialog.Builder(this)
        .setTitle("Choose category")
        .setSingleChoiceItems(labels, checked, (dialog, which) -> {
          mCategory = categories.get(which);
          dialog.dismiss();
          showChannelBrowser(title, guideMode, favoritesOnly, recentsOnly);
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private LinearLayout cobraGuideToolbar(String label) {
    LinearLayout bar = new LinearLayout(this);
    bar.setGravity(Gravity.CENTER_VERTICAL);
    Button category = action("CATEGORY  •  " + mCategory + "   ▾");
    category.setOnClickListener(v -> {
      ArrayList<String> categories = categoriesForCurrentChannels();
      String[] labels = categories.toArray(new String[0]);
      int checked = Math.max(0, categories.indexOf(mCategory));
      new AlertDialog.Builder(this).setTitle("Choose category")
          .setSingleChoiceItems(labels, checked, (dialog, which) -> {
            mCategory = categories.get(which); dialog.dismiss(); showGuide();
          }).setNegativeButton("Cancel", null).show();
    });
    Button mode = action(label + "   ▾");
    mode.setOnClickListener(v -> showCobraGuideViewPicker(true));
    LinearLayout.LayoutParams left = new LinearLayout.LayoutParams(0, dp(56), 1);
    left.rightMargin = dp(6);
    bar.addView(category, left);
    bar.addView(mode, new LinearLayout.LayoutParams(0, dp(56), 1));
    return bar;
  }

  private void showGuideGrid() {
    clearStage("COBRA • GUIDE");
    status("TV Grid • long-press a row for programme actions");
    mStage.addView(cobraGuideToolbar("TV GRID"),
        new LinearLayout.LayoutParams(-1, dp(62)));
    ScrollView scroll = new ScrollView(this);
    LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL);
    scroll.addView(list);
    LinearLayout header = new LinearLayout(this);
    header.setBackground(surface(cobraAlpha(mTheme.panel, 224), 16, mTheme.line, 1));
    header.addView(text("CHANNEL", mTheme.muted, 12, Gravity.LEFT | Gravity.CENTER_VERTICAL),
        new LinearLayout.LayoutParams(0, dp(42), 0.42f));
    header.addView(text("NOW", mTheme.muted, 12, Gravity.LEFT | Gravity.CENTER_VERTICAL),
        new LinearLayout.LayoutParams(0, dp(42), 0.29f));
    header.addView(text("NEXT", mTheme.muted, 12, Gravity.LEFT | Gravity.CENTER_VERTICAL),
        new LinearLayout.LayoutParams(0, dp(42), 0.29f));
    list.addView(header);
    int number = 1;
    for (Channel channel : filteredChannels(false, false)) {
      final Channel item = channel;
      ProgramPair pair = programFor(channel);
      LinearLayout row = new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL);
      row.setPadding(dp(8), dp(4), dp(8), dp(4));
      row.setBackground(focusSurface(cobraAlpha(mTheme.panel2, 218), cobraAlpha(mTheme.focus, 244), 16));
      Button channelCell = action(String.format(Locale.US, "%03d  %s", number++, channel.name));
      channelCell.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      channelCell.setOnClickListener(v -> playChannel(item));
      channelCell.setOnLongClickListener(v -> { showProgramGuide(item); return true; });
      String now = pair != null && !pair.now.isEmpty() ? pair.now : "No guide data";
      String next = pair != null && !pair.next.isEmpty() ? pair.next : "—";
      TextView nowCell = text(now, mTheme.text, 12, Gravity.LEFT | Gravity.CENTER_VERTICAL);
      TextView nextCell = text(next, mTheme.muted, 12, Gravity.LEFT | Gravity.CENTER_VERTICAL);
      nowCell.setOnClickListener(v -> showProgramGuide(item));
      nextCell.setOnClickListener(v -> showProgramGuide(item));
      row.addView(channelCell, new LinearLayout.LayoutParams(0, dp(78), 0.42f));
      row.addView(nowCell, new LinearLayout.LayoutParams(0, dp(78), 0.29f));
      row.addView(nextCell, new LinearLayout.LayoutParams(0, dp(78), 0.29f));
      LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(-1, dp(82));
      rowParams.bottomMargin = dp(5); list.addView(row, rowParams);
    }
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void showGuideCompact() {
    clearStage("COBRA • GUIDE");
    status("Compact Guide • tap to watch • long-press for details");
    mStage.addView(cobraGuideToolbar("COMPACT"),
        new LinearLayout.LayoutParams(-1, dp(62)));
    ScrollView scroll = new ScrollView(this);
    LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); scroll.addView(list);
    int number = 1;
    for (Channel channel : filteredChannels(false, false)) {
      final Channel item = channel; ProgramPair pair = programFor(channel);
      String now = pair != null && !pair.now.isEmpty() ? pair.now : "No guide data";
      Button row = action(String.format(Locale.US, "%03d  %s   •   %s", number++, channel.name, now));
      row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL); row.setTextSize(12);
      row.setOnClickListener(v -> playChannel(item));
      row.setOnLongClickListener(v -> { showProgramGuide(item); return true; });
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(58)); p.bottomMargin = dp(4); list.addView(row, p);
    }
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void showGuideFocus() {
    clearStage("COBRA • GUIDE");
    status("Focus Guide • larger programme cards");
    mStage.addView(cobraGuideToolbar("FOCUS"),
        new LinearLayout.LayoutParams(-1, dp(62)));
    ScrollView scroll = new ScrollView(this);
    LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); scroll.addView(list);
    int number = 1;
    for (Channel channel : filteredChannels(false, false)) {
      final Channel item = channel; ProgramPair pair = programFor(channel);
      String now = pair != null && !pair.now.isEmpty() ? pair.now : "No guide data";
      String next = pair != null && !pair.next.isEmpty() ? pair.next : "—";
      Button row = action(String.format(Locale.US, "%03d  %s\\nNOW  •  %s\\nNEXT •  %s",
          number++, channel.name, now, next));
      row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL); row.setTextSize(14);
      row.setOnClickListener(v -> playChannel(item));
      row.setOnLongClickListener(v -> { showProgramGuide(item); return true; });
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(112)); p.bottomMargin = dp(8); list.addView(row, p);
    }
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

'''
    java = once(java, "  private void playChannel(Channel channel) {\n",
                helpers + "  private void playChannel(Channel channel) {\n",
                "frontend helpers")
    return java


def verify(java: str) -> None:
    required = (
        "REQUEST_COBRA_UI_PACKAGE = 4173",
        "INSTALL COBRA UI PACKAGE",
        "activeCobraUiLabel()",
        "showCobraGuideViewPicker(false)",
        "showGuideGrid()",
        "showGuideCompact()",
        "showGuideFocus()",
        '"TV Grid"',
        "CATEGORY  •  ",
        "installCobraUiPackage(data.getData())",
        "submitCobraIo(() ->",
        "publishCobraUi(() ->",
        "script.infinity.cobra.theme/resources/cobra-ui.json",
        "Cobra UI package attempted to own protected contract",
        "ScrollView settingsScroll",
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra UI frontend contract missing: " + token)
    if "mIo.execute(() ->" in java[java.find("private void installCobraUiPackage"):java.find("private void playChannel")]:
        raise RuntimeError("Cobra UI installer bypassed RC3 guarded async executor")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra UI installer + category picker + 4 Guide modes applied")


if __name__ == "__main__":
    main()
