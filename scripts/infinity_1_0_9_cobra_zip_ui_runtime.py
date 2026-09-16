#!/usr/bin/env python3
'''Install Cobra UI runtime v3 into the generated Android presentation activity.

This transform runs after the approved Candidate 2 UI transform. It only changes
InfinityLiveActivity presentation code. It does not modify Kodi C/C++, renderer,
rotation ownership, background/resume ownership, provider logic, or playback
engine code.

Runtime v3 reads:
  .kodi/addons/script.infinity.cobra.theme/resources/cobra-ui.json
and keeps cobra-theme.json as the visual-token source. A package update can
therefore change supported Cobra layout/presentation structure without another
native Kodi build.
'''
from __future__ import annotations

import re


RUNTIME = 3
UI_PATH = ".kodi/addons/script.infinity.cobra.theme/resources/cobra-ui.json"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Cobra ZIP UI runtime {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(
            f"Cobra ZIP UI runtime {label}: expected exactly one match, found {count}"
        )
    return text


def patch(java: str) -> str:
    java = once(
        java,
        "  private Theme mTheme;\n",
        "  private static final int COBRA_UI_RUNTIME = 3;\n"
        "  private Theme mTheme;\n"
        "  private UiContract mUi;\n",
        "runtime fields",
    )

    count = java.count("    mTheme = Theme.load(this);\n")
    if count < 2:
        raise RuntimeError(
            f"Cobra ZIP UI runtime load hooks: expected at least two theme loads, found {count}"
        )
    java = java.replace(
        "    mTheme = Theme.load(this);\n",
        "    mTheme = Theme.load(this);\n"
        "    mUi = UiContract.load(this);\n",
    )

    java = once(
        java,
        "    resumeCobraAfterBackground();\n",
        "    resumeCobraAfterBackground();\n"
        "    reloadCobraUiIfChanged();\n",
        "resume hot reload hook",
    )

    java = once(
        java,
        "    button.setFocusableInTouchMode(false);\n",
        "    button.setFocusableInTouchMode(!mUi.singleTapActivate);\n"
        "    button.setFocusable(mUi.dpadFocusEnabled);\n"
        "    button.setMinHeight(dp(Math.max(mTheme.touchTarget, mUi.minimumTargetDp)));\n"
        "    button.setMinWidth(dp(Math.max(mTheme.touchTarget, mUi.minimumTargetDp)));\n",
        "touch policy",
    )

    java = regex_once(
        java,
        r"^    int railWidth = isCompact\(\) \? dp\(104\) : isMedium\(\) \? dp\(132\) : dp\(156\);$",
        '    int railWidth = "drawer".equals(mUi.navigationMode)\n'
        "        ? dp(isPortrait() ? mUi.drawerPortraitWidthDp : mUi.drawerLandscapeWidthDp)\n"
        "        : (isCompact() ? dp(104) : isMedium() ? dp(132) : dp(156));",
        "navigation width",
    )
    java = once(
        java,
        "    mRail.setVisibility(View.GONE);\n",
        '    mRail.setVisibility("drawer".equals(mUi.navigationMode) && mUi.collapsedByDefault\n'
        "        ? View.GONE : View.VISIBLE);\n",
        "navigation initial visibility",
    )
    java = once(
        java,
        '    mHeader.setText("☰  COBRA • LIVE TV");\n',
        '    mHeader.setText("drawer".equals(mUi.navigationMode)\n'
        '        ? "☰  COBRA • LIVE TV" : "COBRA • LIVE TV");\n',
        "navigation initial header",
    )
    java = once(
        java,
        "    mHeader.setOnClickListener(v -> toggleCobraDrawer());\n",
        '    mHeader.setOnClickListener(v -> { if ("drawer".equals(mUi.navigationMode)) toggleCobraDrawer(); });\n',
        "navigation header action",
    )
    java = once(
        java,
        "  private void toggleCobraDrawer() {\n"
        "    if (mRail == null) return;\n",
        "  private void toggleCobraDrawer() {\n"
        '    if (mRail == null || !"drawer".equals(mUi.navigationMode)) return;\n',
        "drawer mode guard",
    )
    java = once(
        java,
        "  private void closeCobraDrawer() {\n"
        "    if (mRail != null) mRail.setVisibility(View.GONE);\n"
        "  }\n",
        "  private void closeCobraDrawer() {\n"
        '    if (mRail != null && "drawer".equals(mUi.navigationMode) && mUi.autoCollapseAfterAction)\n'
        "      mRail.setVisibility(View.GONE);\n"
        "  }\n",
        "drawer auto collapse",
    )
    java = once(
        java,
        '    mHeader.setText("☰  " + title);\n',
        '    mHeader.setText("drawer".equals(mUi.navigationMode) ? "☰  " + title : title);\n',
        "drawer title",
    )

    java = once(
        java,
        "  private void addRail(String label, View.OnClickListener listener) {\n"
        "    Button button = action(label);\n",
        "  private void addRail(String label, View.OnClickListener listener) {\n"
        "    if (!mUi.destinationEnabled(label)) return;\n"
        "    Button button = action(label);\n",
        "navigation destinations",
    )
    java = once(
        java,
        '    Button infinity = action("∞  INFINITY");\n',
        '    Button infinity = action("∞  INFINITY");\n'
        '    infinity.setVisibility(mUi.destinationEnabled("INFINITY") ? View.VISIBLE : View.GONE);\n',
        "Infinity destination visibility",
    )

    java = once(
        java,
        "              LinearLayout.LayoutParams.MATCH_PARENT, dp(82))\n",
        "              LinearLayout.LayoutParams.MATCH_PARENT, dp(mUi.portraitCategoryHeightDp))\n",
        "portrait category height",
    )
    java = once(
        java,
        "          dp(guideMode ? mTheme.guideRowHeight : mTheme.rowHeight)));\n",
        "          dp(guideMode ? mTheme.guideRowHeight\n"
        "              : mUi.channelRowHeight(isPortrait(), mTheme.rowHeight))));\n",
        "channel row height",
    )

    java = once(
        java,
        "    for (Button button : new Button[]{prev, favorite, record, multi, next, settings}) {\n",
        "    for (Button button : mUi.orderPlayerActions(\n"
        "        prev, favorite, guide, record, multi, next, settings)) {\n",
        "player action order",
    )

    java = once(
        java,
        '    Button cast = action("Cast / Route");\n'
        '    Button guide = action("Guide");\n',
        '    Button cast = action("Cast / Route");\n'
        '    Button source = action("Source");\n'
        '    Button guide = action("Guide");\n',
        "player source action",
    )
    java = once(
        java,
        "    cast.setOnClickListener(v -> openCastSettings());\n"
        "    guide.setOnClickListener(v -> { closePlayer(); showGuide(); });\n",
        "    cast.setOnClickListener(v -> openCastSettings());\n"
        "    source.setOnClickListener(v -> { closePlayer(); showSources(); });\n"
        "    guide.setOnClickListener(v -> { closePlayer(); showGuide(); });\n",
        "player source handler",
    )
    java = once(
        java,
        "    for (Button item : new Button[]{audio, fit, cast, guide, multi, close}) {\n",
        "    for (Button item : mUi.orderSettingsActions(\n"
        "        audio, fit, cast, source, guide, multi, close)) {\n",
        "settings action order",
    )
    java = once(
        java,
        "    int width = dp(isCompact() ? 286 : 340);\n"
        "    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(width, -1, Gravity.RIGHT);\n",
        "    int width = Math.max(dp(240), Math.round(\n"
        "        getResources().getDisplayMetrics().widthPixels * (mUi.playerSettingsWidthPercent / 100f)));\n"
        "    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(\n"
        "        width, -1, mUi.playerSettingsGravity());\n",
        "settings drawer geometry",
    )

    java = once(
        java,
        "    mMultiChrome.addView(single, new LinearLayout.LayoutParams(0, dp(48), 1));\n",
        "    if (mUi.multiAllowReturnToSingle)\n"
        "      mMultiChrome.addView(single, new LinearLayout.LayoutParams(0, dp(48), 1));\n",
        "Multi-View single control",
    )
    java = once(
        java,
        "    mMultiChrome.addView(remove, new LinearLayout.LayoutParams(0, dp(48), 1));\n",
        "    if (mUi.multiAllowRemoveTile)\n"
        "      mMultiChrome.addView(remove, new LinearLayout.LayoutParams(0, dp(48), 1));\n",
        "Multi-View remove control",
    )

    java = java.replace(
        '        ".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json\\n\\n" +\n'
        '        "That file can be changed by a small add-on ZIP without rebuilding the APK.",',
        '        ".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json\\n" +\n'
        '        ".kodi/addons/script.infinity.cobra.theme/resources/cobra-ui.json\\n\\n" +\n'
        '        "Those files can be changed by a small Cobra UI ZIP without rebuilding Kodi.",',
        1,
    )

    helpers = r'''  private void reloadCobraUiIfChanged() {
    long stamp = UiContract.sourceStamp(this);
    if (mUi != null && stamp == mUi.sourceStamp) return;
    UiContract next = UiContract.load(this);
    Theme nextTheme = Theme.load(this);
    mUi = next;
    mTheme = nextTheme;
    // Never tear down active playback merely for a UI-package update. Player
    // and Multi-View geometry will pick up the contract when next constructed.
    if (mPlayerOverlay != null || mMultiOverlay != null) return;
    buildShell();
    if (mChannels.isEmpty()) {
      if (mSources.isEmpty()) showWelcome(); else loadAllEnabledSources(false);
    } else {
      showLiveHome();
    }
  }

'''
    java = once(
        java,
        "  private boolean hasCobraVideo() {\n",
        helpers + "  private boolean hasCobraVideo() {\n",
        "hot reload helper",
    )

    ui_class = r'''  private static final class UiContract {
    String navigationMode = "drawer";
    boolean collapsedByDefault = true;
    boolean autoCollapseAfterAction = true;
    int drawerPortraitWidthDp = 286;
    int drawerLandscapeWidthDp = 320;

    int portraitCategoryHeightDp = 58;
    int portraitChannelRowHeightDp = 78;
    int landscapeChannelRowHeightDp = 72;

    boolean singleTapActivate = true;
    boolean dpadFocusEnabled = true;
    int minimumTargetDp = 56;
    int pressedFeedbackMs = 90;

    String playerSettingsMode = "drawer";
    String playerSettingsEdge = "right";
    int playerSettingsWidthPercent = 86;
    int playerAutoHideMs = 3200;
    final ArrayList<String> playerPrimaryActions = new ArrayList<>();
    final ArrayList<String> playerSettingsActions = new ArrayList<>();

    boolean multiAllowRemoveTile = true;
    boolean multiAllowReturnToSingle = true;
    int multiMinimumTiles = 1;
    int multiMaximumTiles = 4;

    long sourceStamp = 0L;
    private final Set<String> mDestinations = new HashSet<>();

    UiContract() {
      Collections.addAll(playerPrimaryActions,
          "previous", "favorite", "guide", "record", "multiview", "next");
      Collections.addAll(playerSettingsActions,
          "tracks", "subtitles", "aspect", "cast", "source", "close");
    }

    static UiContract load(Context context) {
      UiContract defaults = new UiContract();
      defaults.sourceStamp = sourceStamp(context);
      File external = context.getExternalFilesDir(null);
      if (external == null) return defaults;
      File file = new File(external,
          ".kodi/addons/script.infinity.cobra.theme/resources/cobra-ui.json");
      if (!file.isFile() || file.length() <= 0 || file.length() > 131072) return defaults;

      try {
        byte[] data;
        try (InputStream in = new java.io.FileInputStream(file);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
          byte[] buffer = new byte[8192];
          int n;
          while ((n = in.read(buffer)) >= 0) out.write(buffer, 0, n);
          data = out.toByteArray();
        }

        JSONObject root = new JSONObject(new String(data, StandardCharsets.UTF_8));
        if (root.optInt("schema", 0) != 1) return defaults;

        JSONObject runtime = root.optJSONObject("runtime");
        if (runtime == null
            || runtime.optInt("minimum_runtime", Integer.MAX_VALUE) > COBRA_UI_RUNTIME
            || !"cobra-live-only".equals(runtime.optString("scope", ""))) {
          return defaults;
        }

        JSONObject protectedContracts = root.optJSONObject("protected_contracts");
        if (!ownsOnlyPresentation(protectedContracts)) return defaults;

        UiContract ui = new UiContract();
        ui.sourceStamp = defaults.sourceStamp;

        JSONObject nav = root.optJSONObject("navigation");
        if (nav != null) {
          String mode = nav.optString("mode", ui.navigationMode);
          if ("drawer".equals(mode) || "rail".equals(mode) || "compact_rail".equals(mode))
            ui.navigationMode = mode;
          ui.collapsedByDefault = nav.optBoolean("collapsed_by_default", ui.collapsedByDefault);
          ui.autoCollapseAfterAction =
              nav.optBoolean("auto_collapse_after_action", ui.autoCollapseAfterAction);
          ui.drawerPortraitWidthDp =
              clamp(nav.optInt("portrait_width_dp", ui.drawerPortraitWidthDp), 220, 520);
          ui.drawerLandscapeWidthDp =
              clamp(nav.optInt("landscape_width_dp", ui.drawerLandscapeWidthDp), 240, 600);
          JSONArray destinations = nav.optJSONArray("destinations");
          if (destinations != null) appendStrings(destinations, ui.mDestinations);
        }

        JSONObject browser = root.optJSONObject("live_browser");
        if (browser != null) {
          JSONObject portrait = browser.optJSONObject("portrait");
          if (portrait != null) {
            ui.portraitCategoryHeightDp = clamp(
                portrait.optInt("category_height_dp", ui.portraitCategoryHeightDp), 40, 160);
            ui.portraitChannelRowHeightDp = clamp(
                portrait.optInt("channel_row_height_dp", ui.portraitChannelRowHeightDp), 48, 140);
          }
          JSONObject landscape = browser.optJSONObject("landscape");
          if (landscape != null) {
            ui.landscapeChannelRowHeightDp = clamp(
                landscape.optInt("channel_row_height_dp", ui.landscapeChannelRowHeightDp), 48, 140);
          }
        }

        JSONObject touch = root.optJSONObject("touch");
        if (touch != null) {
          ui.singleTapActivate = touch.optBoolean("single_tap_activate", ui.singleTapActivate);
          ui.dpadFocusEnabled = touch.optBoolean("dpad_focus_enabled", ui.dpadFocusEnabled);
          ui.minimumTargetDp = clamp(touch.optInt("minimum_target_dp", ui.minimumTargetDp), 44, 96);
          ui.pressedFeedbackMs = clamp(touch.optInt("pressed_feedback_ms", ui.pressedFeedbackMs), 0, 600);
        }

        JSONObject player = root.optJSONObject("player");
        if (player != null) {
          ui.playerSettingsMode = player.optString("settings_mode", ui.playerSettingsMode);
          String edge = player.optString("settings_edge", ui.playerSettingsEdge);
          if ("left".equals(edge) || "right".equals(edge)) ui.playerSettingsEdge = edge;
          ui.playerSettingsWidthPercent = clamp(
              player.optInt("settings_width_percent", ui.playerSettingsWidthPercent), 45, 96);
          ui.playerAutoHideMs = clamp(player.optInt("auto_hide_ms", ui.playerAutoHideMs), 800, 15000);
          replaceStrings(player.optJSONArray("primary_actions"), ui.playerPrimaryActions);
          replaceStrings(player.optJSONArray("settings_actions"), ui.playerSettingsActions);
        }

        JSONObject multi = root.optJSONObject("multiview");
        if (multi != null) {
          ui.multiAllowRemoveTile = multi.optBoolean("allow_remove_tile", ui.multiAllowRemoveTile);
          ui.multiAllowReturnToSingle = multi.optBoolean("allow_return_to_single", ui.multiAllowReturnToSingle);
          ui.multiMinimumTiles = clamp(multi.optInt("minimum_tiles", ui.multiMinimumTiles), 1, 4);
          ui.multiMaximumTiles = clamp(multi.optInt("maximum_tiles", ui.multiMaximumTiles), ui.multiMinimumTiles, 4);
        }
        return ui;
      } catch (Exception ignored) {
        return defaults;
      }
    }

    boolean destinationEnabled(String label) {
      if (mDestinations.isEmpty()) return true;
      String id = label == null ? "" : label.toLowerCase(Locale.US)
          .replace("∞", "").trim().replace(" ", "").replace("-", "");
      if ("livetv".equals(id)) id = "live";
      return mDestinations.contains(id);
    }

    int channelRowHeight(boolean portrait, int fallback) {
      int value = portrait ? portraitChannelRowHeightDp : landscapeChannelRowHeightDp;
      return value > 0 ? value : fallback;
    }

    int playerSettingsGravity() {
      return "left".equals(playerSettingsEdge) ? Gravity.LEFT : Gravity.RIGHT;
    }

    List<Button> orderPlayerActions(
        Button previous, Button favorite, Button guide, Button record,
        Button multi, Button next, Button settings) {
      Map<String, Button> available = new LinkedHashMap<>();
      available.put("previous", previous);
      available.put("favorite", favorite);
      available.put("guide", guide);
      available.put("record", record);
      available.put("multiview", multi);
      available.put("next", next);
      available.put("settings", settings);
      ArrayList<Button> result = new ArrayList<>();
      for (String key : playerPrimaryActions) addUnique(result, available.get(key));
      if ("drawer".equals(playerSettingsMode)) addUnique(result, settings);
      if (result.isEmpty()) Collections.addAll(result, previous, favorite, record, multi, next, settings);
      return result;
    }

    List<Button> orderSettingsActions(
        Button tracks, Button aspect, Button cast, Button source,
        Button guide, Button multi, Button close) {
      Map<String, Button> available = new LinkedHashMap<>();
      available.put("tracks", tracks);
      available.put("subtitles", tracks);
      available.put("audio", tracks);
      available.put("aspect", aspect);
      available.put("cast", cast);
      available.put("source", source);
      available.put("guide", guide);
      available.put("multiview", multi);
      available.put("close", close);
      ArrayList<Button> result = new ArrayList<>();
      for (String key : playerSettingsActions) addUnique(result, available.get(key));
      if (result.isEmpty()) Collections.addAll(result, tracks, aspect, cast, source, close);
      return result;
    }

    private static void addUnique(List<Button> out, Button button) {
      if (button != null && !out.contains(button)) out.add(button);
    }

    private static void appendStrings(JSONArray array, Set<String> target) {
      for (int i = 0; i < array.length(); i++) {
        String value = array.optString(i, "").toLowerCase(Locale.US).trim();
        if (!value.isEmpty()) target.add(value.replace(" ", "").replace("-", ""));
      }
    }

    private static void replaceStrings(JSONArray array, List<String> target) {
      if (array == null) return;
      ArrayList<String> next = new ArrayList<>();
      for (int i = 0; i < array.length(); i++) {
        String value = array.optString(i, "").toLowerCase(Locale.US).trim();
        if (!value.isEmpty() && !next.contains(value)) next.add(value);
      }
      if (!next.isEmpty()) {
        target.clear();
        target.addAll(next);
      }
    }

    private static boolean ownsOnlyPresentation(JSONObject contracts) {
      if (contracts == null) return false;
      for (String key : new String[]{
          "rotation", "fold", "background_resume", "renderer",
          "provider_playback", "infinity_handoff"}) {
        if (!"native".equals(contracts.optString(key, ""))) return false;
      }
      return true;
    }

    static long sourceStamp(Context context) {
      File external = context.getExternalFilesDir(null);
      if (external == null) return 0L;
      File ui = new File(external, ".kodi/addons/script.infinity.cobra.theme/resources/cobra-ui.json");
      File theme = new File(external, ".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json");
      long a = ui.isFile() ? ui.lastModified() ^ ui.length() : 0L;
      long b = theme.isFile() ? theme.lastModified() ^ theme.length() : 0L;
      return a ^ Long.rotateLeft(b, 17);
    }

    private static int clamp(int value, int low, int high) {
      return Math.max(low, Math.min(high, value));
    }
  }

'''
    java = once(
        java,
        "  private static final class Theme {\n",
        ui_class + "  private static final class Theme {\n",
        "UiContract parser",
    )
    return java


def verify(java: str) -> None:
    required = (
        "private static final int COBRA_UI_RUNTIME = 3",
        "private UiContract mUi;",
        "mUi = UiContract.load(this);",
        "reloadCobraUiIfChanged();",
        UI_PATH,
        "mUi.destinationEnabled(label)",
        "mUi.portraitCategoryHeightDp",
        "mUi.channelRowHeight(isPortrait(), mTheme.rowHeight)",
        "mUi.orderPlayerActions(",
        "mUi.orderSettingsActions(",
        "mUi.playerSettingsWidthPercent",
        "mUi.multiAllowReturnToSingle",
        "mUi.multiAllowRemoveTile",
        '"native".equals(contracts.optString(key, ""))',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra ZIP UI runtime contract missing: " + token)
