#!/usr/bin/env python3
"""Cobra UI Runtime v3.

Turns the approved Cobra presentation layer into a declarative ZIP-driven
runtime. This transform is intentionally presentation-only: it does not alter
rotation, Fold/window ownership, background/resume, renderer, provider/player
or Infinity handoff lifecycle contracts.
"""
from __future__ import annotations


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Cobra UI runtime {label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


UI_CLASS = r'''  private static final class CobraUi {
    static final int RUNTIME_VERSION = 3;
    String fingerprint = "defaults";
    String navigationMode = "drawer";
    boolean navigationCollapsedByDefault = true;
    boolean navigationAutoCollapse = true;
    int navigationPortraitWidthDp = 286;
    int navigationLandscapeWidthDp = 320;
    final ArrayList<String> navigationDestinations = names(
        "live", "guide", "recordings", "favorites", "search", "discover",
        "sources", "settings", "infinity");

    int portraitCategoryHeightDp = 58;
    int portraitChannelRowHeightDp = 78;
    int landscapeCategoryWidthDp = 224;
    int landscapeChannelRowHeightDp = 72;

    boolean singleTapActivate = true;
    boolean touchFocusFirst = false;
    int touchTargetDp = 56;
    int pressedFeedbackMs = 90;

    String playerChrome = "compact_bottom_bar";
    int playerAutoHideMs = 3200;
    String playerSettingsMode = "drawer";
    String playerSettingsEdge = "right";
    int playerSettingsWidthPercent = 86;
    ArrayList<String> playerPrimaryActions = names(
        "previous", "favorite", "guide", "record", "multiview", "next", "settings");
    ArrayList<String> playerSettingsActions = names(
        "tracks", "subtitles", "aspect", "cast", "source", "guide", "multiview", "close");

    boolean multiAllowRemoveTile = true;
    boolean multiAllowReturnToSingle = true;
    boolean multiKeepSelectedOnSingle = true;
    boolean multiReflowAfterRemove = true;
    int multiMinimumTiles = 1;
    int multiMaximumTiles = 4;

    int compactMaxDp = 599;
    int mediumMaxDp = 839;

    boolean drawerMode() {
      return "drawer".equals(navigationMode);
    }

    boolean destinationEnabled(String label) {
      if (navigationDestinations.isEmpty()) return true;
      String value = label == null ? "" : label.toLowerCase(Locale.US);
      String key = value;
      if (value.contains("live")) key = "live";
      else if (value.contains("guide")) key = "guide";
      else if (value.contains("record")) key = "recordings";
      else if (value.contains("favorite")) key = "favorites";
      else if (value.contains("search")) key = "search";
      else if (value.contains("discover")) key = "discover";
      else if (value.contains("source")) key = "sources";
      else if (value.contains("setting")) key = "settings";
      else if (value.contains("infinity")) key = "infinity";
      return navigationDestinations.contains(key);
    }

    static CobraUi load(Context context) {
      CobraUi fallback = new CobraUi();
      SharedPreferences prefs = context.getSharedPreferences(
          "infinity_cobra_ui_runtime", Context.MODE_PRIVATE);
      File external = context.getExternalFilesDir(null);
      String raw = "";
      if (external != null) {
        File file = new File(external,
            ".kodi/addons/script.infinity.cobra.theme/resources/cobra-ui.json");
        raw = read(file);
      }
      CobraUi parsed = parse(raw);
      if (parsed != null) {
        prefs.edit().putString("last_good_ui", raw).apply();
        return parsed;
      }
      parsed = parse(prefs.getString("last_good_ui", ""));
      return parsed == null ? fallback : parsed;
    }

    private static String read(File file) {
      if (file == null || !file.isFile() || file.length() <= 0 || file.length() > 131072) return "";
      try (InputStream in = new java.io.FileInputStream(file);
           ByteArrayOutputStream out = new ByteArrayOutputStream()) {
        byte[] buffer = new byte[4096];
        int count;
        while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
        return new String(out.toByteArray(), StandardCharsets.UTF_8);
      } catch (Exception ignored) {
        return "";
      }
    }

    private static CobraUi parse(String raw) {
      if (raw == null || raw.trim().isEmpty()) return null;
      try {
        JSONObject root = new JSONObject(raw);
        if (root.optInt("schema", -1) != 1) return null;
        JSONObject runtime = root.optJSONObject("runtime");
        if (runtime == null || !"cobra-live-only".equals(runtime.optString("scope", ""))) return null;
        int minimum = runtime.optInt("minimum_runtime", Integer.MAX_VALUE);
        if (minimum < 1 || minimum > RUNTIME_VERSION) return null;

        JSONObject protectedContracts = root.optJSONObject("protected_contracts");
        if (protectedContracts == null) return null;
        for (String key : new String[]{
            "rotation", "fold", "background_resume", "renderer",
            "provider_playback", "infinity_handoff"}) {
          if (!"native".equals(protectedContracts.optString(key, ""))) return null;
        }

        CobraUi ui = new CobraUi();
        ui.fingerprint = Integer.toHexString(raw.hashCode());

        JSONObject nav = root.optJSONObject("navigation");
        if (nav != null) {
          String mode = nav.optString("mode", ui.navigationMode);
          if ("drawer".equals(mode) || "rail".equals(mode) || "compact_rail".equals(mode)) {
            ui.navigationMode = mode;
          }
          ui.navigationCollapsedByDefault = nav.optBoolean(
              "collapsed_by_default", ui.navigationCollapsedByDefault);
          ui.navigationAutoCollapse = nav.optBoolean(
              "auto_collapse_after_action", ui.navigationAutoCollapse);
          ui.navigationPortraitWidthDp = clamp(
              nav.optInt("portrait_width_dp", ui.navigationPortraitWidthDp), 180, 420);
          ui.navigationLandscapeWidthDp = clamp(
              nav.optInt("landscape_width_dp", ui.navigationLandscapeWidthDp), 180, 480);
          replaceNames(ui.navigationDestinations, nav.optJSONArray("destinations"),
              names("live", "guide", "recordings", "favorites", "search", "discover",
                  "sources", "settings", "infinity"));
        }

        JSONObject browser = root.optJSONObject("live_browser");
        if (browser != null) {
          JSONObject portrait = browser.optJSONObject("portrait");
          if (portrait != null) {
            ui.portraitCategoryHeightDp = clamp(
                portrait.optInt("category_height_dp", ui.portraitCategoryHeightDp), 44, 180);
            ui.portraitChannelRowHeightDp = clamp(
                portrait.optInt("channel_row_height_dp", ui.portraitChannelRowHeightDp), 52, 120);
          }
          JSONObject landscape = browser.optJSONObject("landscape");
          if (landscape != null) {
            ui.landscapeCategoryWidthDp = clamp(
                landscape.optInt("category_width_dp", ui.landscapeCategoryWidthDp), 120, 360);
            ui.landscapeChannelRowHeightDp = clamp(
                landscape.optInt("channel_row_height_dp", ui.landscapeChannelRowHeightDp), 48, 110);
          }
        }

        JSONObject touch = root.optJSONObject("touch");
        if (touch != null) {
          ui.singleTapActivate = touch.optBoolean("single_tap_activate", ui.singleTapActivate);
          ui.touchFocusFirst = touch.optBoolean("touch_focus_first", ui.touchFocusFirst);
          ui.touchTargetDp = clamp(touch.optInt("minimum_target_dp", ui.touchTargetDp), 48, 88);
          ui.pressedFeedbackMs = clamp(
              touch.optInt("pressed_feedback_ms", ui.pressedFeedbackMs), 40, 280);
        }

        JSONObject player = root.optJSONObject("player");
        if (player != null) {
          ui.playerChrome = player.optString("chrome", ui.playerChrome);
          ui.playerAutoHideMs = clamp(
              player.optInt("auto_hide_ms", ui.playerAutoHideMs), 1200, 12000);
          ui.playerSettingsMode = player.optString("settings_mode", ui.playerSettingsMode);
          String edge = player.optString("settings_edge", ui.playerSettingsEdge);
          if ("left".equals(edge) || "right".equals(edge)) ui.playerSettingsEdge = edge;
          ui.playerSettingsWidthPercent = clamp(
              player.optInt("settings_width_percent", ui.playerSettingsWidthPercent), 45, 96);
          ui.playerPrimaryActions = validatedNames(
              player.optJSONArray("primary_actions"),
              names("previous", "favorite", "guide", "record", "multiview", "next", "settings"),
              names("previous", "favorite", "guide", "record", "multiview", "next", "settings"));
          ui.playerSettingsActions = validatedNames(
              player.optJSONArray("settings_actions"),
              names("tracks", "subtitles", "aspect", "cast", "source", "guide", "multiview", "close"),
              names("tracks", "subtitles", "aspect", "cast", "source", "guide", "multiview", "close"));
        }

        JSONObject multi = root.optJSONObject("multiview");
        if (multi != null) {
          ui.multiAllowRemoveTile = multi.optBoolean("allow_remove_tile", ui.multiAllowRemoveTile);
          ui.multiAllowReturnToSingle = multi.optBoolean(
              "allow_return_to_single", ui.multiAllowReturnToSingle);
          ui.multiKeepSelectedOnSingle = multi.optBoolean(
              "single_view_keeps_selected_tile", ui.multiKeepSelectedOnSingle);
          ui.multiReflowAfterRemove = multi.optBoolean(
              "reflow_after_remove", ui.multiReflowAfterRemove);
          ui.multiMinimumTiles = clamp(multi.optInt("minimum_tiles", ui.multiMinimumTiles), 1, 4);
          ui.multiMaximumTiles = clamp(multi.optInt("maximum_tiles", ui.multiMaximumTiles),
              ui.multiMinimumTiles, 4);
        }

        JSONObject responsive = root.optJSONObject("responsive");
        if (responsive != null) {
          ui.compactMaxDp = clamp(responsive.optInt("compact_max_dp", ui.compactMaxDp), 420, 700);
          ui.mediumMaxDp = clamp(responsive.optInt("medium_max_dp", ui.mediumMaxDp),
              ui.compactMaxDp + 1, 1100);
        }
        return ui;
      } catch (Exception ignored) {
        return null;
      }
    }

    private static ArrayList<String> names(String... values) {
      ArrayList<String> result = new ArrayList<>();
      Collections.addAll(result, values);
      return result;
    }

    private static void replaceNames(
        ArrayList<String> target, JSONArray source, ArrayList<String> allowed) {
      if (source == null) return;
      ArrayList<String> parsed = validatedNames(source, target, allowed);
      target.clear();
      target.addAll(parsed);
    }

    private static ArrayList<String> validatedNames(
        JSONArray source, ArrayList<String> fallback, ArrayList<String> allowed) {
      if (source == null) return new ArrayList<>(fallback);
      ArrayList<String> result = new ArrayList<>();
      for (int i = 0; i < source.length(); i++) {
        String value = source.optString(i, "").trim().toLowerCase(Locale.US);
        if (!value.isEmpty() && allowed.contains(value) && !result.contains(value)) result.add(value);
      }
      return result.isEmpty() ? new ArrayList<>(fallback) : result;
    }

    private static int clamp(int value, int min, int max) {
      return Math.max(min, Math.min(max, value));
    }
  }

'''


def patch(java: str) -> str:
    java = once(
        java,
        "  private Theme mTheme;\n",
        "  private Theme mTheme;\n  private CobraUi mUi;\n",
        "runtime field",
    )
    java = once(
        java,
        "    mTheme = Theme.load(this);\n    mDeviceBridge = new InfinityCobraDeviceBridge(this, () -> hasCobraVideo());\n",
        "    mTheme = Theme.load(this);\n"
        "    mUi = CobraUi.load(this);\n"
        "    mDeviceBridge = new InfinityCobraDeviceBridge(this, () -> hasCobraVideo());\n",
        "runtime load",
    )

    java = once(
        java,
        "    button.setFocusableInTouchMode(false);\n",
        "    button.setFocusableInTouchMode(mUi != null && mUi.touchFocusFirst);\n",
        "ZIP-driven touch focus",
    )
    java = once(
        java,
        "    button.setMinHeight(dp(mTheme.touchTarget));\n",
        "    button.setMinHeight(dp(Math.max(mTheme.touchTarget, mUi == null ? 56 : mUi.touchTargetDp)));\n",
        "ZIP-driven touch target",
    )

    java = once(
        java,
        "    int railWidth = isCompact() ? dp(104) : isMedium() ? dp(144) : dp(176);\n",
        "    int railWidth = dp(mUi == null ? (isCompact() ? 104 : isMedium() ? 144 : 176)\n"
        "        : (isPortrait() ? mUi.navigationPortraitWidthDp : mUi.navigationLandscapeWidthDp));\n",
        "ZIP-driven navigation width",
    )
    java = once(
        java,
        "    mRail.setVisibility(View.GONE);\n",
        "    mRail.setVisibility(mUi != null && (!mUi.drawerMode() || !mUi.navigationCollapsedByDefault)\n"
        "        ? View.VISIBLE : View.GONE);\n",
        "ZIP-driven drawer default",
    )
    java = once(
        java,
        '    mHeader.setText("☰  COBRA • LIVE TV");\n    mHeader.setOnClickListener(v -> toggleCobraDrawer());\n',
        '    mHeader.setText((mUi != null && mUi.drawerMode() ? "☰  " : "") + "COBRA • LIVE TV");\n'
        '    mHeader.setOnClickListener(mUi != null && mUi.drawerMode()\n'
        '        ? v -> toggleCobraDrawer() : null);\n',
        "ZIP-driven drawer affordance",
    )
    java = once(
        java,
        '''  private void toggleCobraDrawer() {
    if (mRail == null) return;
    boolean opening = mRail.getVisibility() != View.VISIBLE;
    mRail.setVisibility(opening ? View.VISIBLE : View.GONE);
    if (opening) mRail.bringToFront();
  }

  private void closeCobraDrawer() {
    if (mRail != null) mRail.setVisibility(View.GONE);
  }
''',
        '''  private void toggleCobraDrawer() {
    if (mRail == null || mUi == null || !mUi.drawerMode()) return;
    boolean opening = mRail.getVisibility() != View.VISIBLE;
    mRail.setVisibility(opening ? View.VISIBLE : View.GONE);
    if (opening) mRail.bringToFront();
  }

  private void closeCobraDrawer() {
    if (mRail != null && mUi != null && mUi.drawerMode()) mRail.setVisibility(View.GONE);
  }
''',
        "runtime drawer behavior",
    )
    java = once(
        java,
        "  private void addRail(String label, View.OnClickListener listener) {\n    Button button = action(label);\n",
        "  private void addRail(String label, View.OnClickListener listener) {\n"
        "    if (mUi != null && !mUi.destinationEnabled(label)) return;\n"
        "    Button button = action(label);\n",
        "ZIP-driven destinations",
    )
    java = once(
        java,
        "    button.setOnClickListener(v -> { closeCobraDrawer(); listener.onClick(v); });\n",
        "    button.setOnClickListener(v -> {\n"
        "      if (mUi == null || mUi.navigationAutoCollapse) closeCobraDrawer();\n"
        "      listener.onClick(v);\n"
        "    });\n",
        "ZIP-driven drawer auto-collapse",
    )
    java = once(
        java,
        '    mHeader.setText("☰  " + title);\n  }\n',
        '    mHeader.setText((mUi != null && mUi.drawerMode() ? "☰  " : "") + title);\n  }\n',
        "ZIP-driven header affordance",
    )

    java = once(
        java,
        "              LinearLayout.LayoutParams.MATCH_PARENT, dp(82))\n",
        "              LinearLayout.LayoutParams.MATCH_PARENT, dp(mUi == null ? 82 : mUi.portraitCategoryHeightDp))\n",
        "ZIP-driven portrait categories",
    )
    java = once(
        java,
        "          dp(guideMode ? mTheme.guideRowHeight : mTheme.rowHeight));\n",
        "          dp(guideMode ? mTheme.guideRowHeight\n"
        "              : (mUi == null ? mTheme.rowHeight\n"
        "                  : (isPortrait() ? mUi.portraitChannelRowHeightDp : mUi.landscapeChannelRowHeightDp)));\n",
        "ZIP-driven channel rows",
    )

    java = once(
        java,
        '''    for (Button button : new Button[]{prev, favorite, record, multi, next, settings}) {
      LinearLayout.LayoutParams playerActionParams = new LinearLayout.LayoutParams(0, dp(48), 1);
      playerActionParams.setMargins(dp(3), 0, dp(3), 0);
      row1.addView(button, playerActionParams);
    }
''',
        '''    LinkedHashMap<String, Button> primaryButtons = new LinkedHashMap<>();
    primaryButtons.put("previous", prev);
    primaryButtons.put("favorite", favorite);
    primaryButtons.put("guide", guide);
    primaryButtons.put("record", record);
    primaryButtons.put("multiview", multi);
    primaryButtons.put("next", next);
    primaryButtons.put("settings", settings);
    ArrayList<String> primaryOrder = mUi == null
        ? CobraUi.names("previous", "favorite", "record", "multiview", "next", "settings")
        : mUi.playerPrimaryActions;
    for (String actionName : primaryOrder) {
      Button button = primaryButtons.get(actionName);
      if (button == null) continue;
      LinearLayout.LayoutParams playerActionParams = new LinearLayout.LayoutParams(0, dp(48), 1);
      playerActionParams.setMargins(dp(3), 0, dp(3), 0);
      row1.addView(button, playerActionParams);
    }
''',
        "ZIP-driven primary player controls",
    )
    java = once(
        java,
        '''    for (Button item : new Button[]{audio, fit, cast, guide, multi, close}) {
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(mTheme.touchTarget));
      p.bottomMargin = dp(8);
      drawer.addView(item, p);
    }
    int width = dp(isCompact() ? 286 : 340);
    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(width, -1, Gravity.RIGHT);
''',
        '''    LinkedHashMap<String, Button> settingsButtons = new LinkedHashMap<>();
    settingsButtons.put("tracks", audio);
    settingsButtons.put("subtitles", audio);
    settingsButtons.put("aspect", fit);
    settingsButtons.put("cast", cast);
    settingsButtons.put("guide", guide);
    settingsButtons.put("multiview", multi);
    settingsButtons.put("close", close);
    ArrayList<String> settingsOrder = mUi == null
        ? CobraUi.names("tracks", "aspect", "cast", "guide", "multiview", "close")
        : mUi.playerSettingsActions;
    HashSet<Button> addedSettings = new HashSet<>();
    for (String actionName : settingsOrder) {
      Button item = settingsButtons.get(actionName);
      if (item == null || addedSettings.contains(item)) continue;
      addedSettings.add(item);
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1,
          dp(Math.max(mTheme.touchTarget, mUi == null ? 56 : mUi.touchTargetDp)));
      p.bottomMargin = dp(8);
      drawer.addView(item, p);
    }
    int screenWidth = getResources().getDisplayMetrics().widthPixels;
    int width = mUi == null ? dp(isCompact() ? 286 : 340)
        : Math.max(dp(240), Math.round(screenWidth * (mUi.playerSettingsWidthPercent / 100f)));
    int settingsGravity = mUi != null && "left".equals(mUi.playerSettingsEdge)
        ? Gravity.LEFT : Gravity.RIGHT;
    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(width, -1, settingsGravity);
''',
        "ZIP-driven player settings drawer",
    )

    java = once(
        java,
        '''    Button single = action("SINGLE");
    single.setOnClickListener(v -> multiToSingle());
    mMultiChrome.addView(single, new LinearLayout.LayoutParams(0, dp(48), 1));
    Button remove = action("REMOVE");
    remove.setOnClickListener(v -> removeSelectedMultiTile());
    mMultiChrome.addView(remove, new LinearLayout.LayoutParams(0, dp(48), 1));
''',
        '''    if (mUi == null || mUi.multiAllowReturnToSingle) {
      Button single = action("SINGLE");
      single.setOnClickListener(v -> multiToSingle());
      mMultiChrome.addView(single, new LinearLayout.LayoutParams(0, dp(48), 1));
    }
    if (mUi == null || mUi.multiAllowRemoveTile) {
      Button remove = action("REMOVE");
      remove.setOnClickListener(v -> removeSelectedMultiTile());
      mMultiChrome.addView(remove, new LinearLayout.LayoutParams(0, dp(48), 1));
    }
''',
        "ZIP-driven MultiView controls",
    )

    java = once(
        java,
        '''    Button reloadTheme = action("RELOAD COBRA UI THEME");
    reloadTheme.setOnClickListener(v -> {
      mTheme = Theme.load(this);
      buildShell();
      showLiveHome();
      toast("Cobra theme reloaded");
    });
''',
        '''    Button reloadTheme = action("RELOAD COBRA UI PACKAGE");
    reloadTheme.setOnClickListener(v -> {
      mTheme = Theme.load(this);
      mUi = CobraUi.load(this);
      buildShell();
      showLiveHome();
      toast("Cobra UI package reloaded");
    });
''',
        "runtime reload control",
    )

    java = once(
        java,
        "  private static final class Theme {\n",
        UI_CLASS + "  private static final class Theme {\n",
        "runtime class",
    )
    return java


def verify(java: str) -> None:
    required = (
        "private static final class CobraUi",
        "static final int RUNTIME_VERSION = 3",
        "last_good_ui",
        "mUi = CobraUi.load(this)",
        "mUi.playerPrimaryActions",
        "mUi.playerSettingsActions",
        "mUi.portraitChannelRowHeightDp",
        "mUi.multiAllowRemoveTile",
        "RELOAD COBRA UI PACKAGE",
        '"background_resume", "renderer"',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra UI runtime contract missing: " + token)
    # Native ownership must remain outside this transform. These callbacks are
    # not authored or replaced here; runtime behavior is presentation-only.
    if "InfinityExtendedBackgroundService" not in java:
        raise RuntimeError("Cobra UI runtime integration lost background/resume service linkage")
    if "InfinityCobraDeviceBridge" not in java:
        raise RuntimeError("Cobra UI runtime integration lost rotation/Fold device bridge")
