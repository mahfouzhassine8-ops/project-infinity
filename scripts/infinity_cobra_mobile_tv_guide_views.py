#!/usr/bin/env python3
"""Implement the locked Cobra Mobile + TV Guide structural runtime.

Android presentation-runtime only. Kodi native, renderer, provider/playback
ownership, rotation/Fold ownership, background/resume and Infinity handoff stay
protected. This bridge teaches Runtime v3 how to consume the structural view
portion of cobra-ui.json while reusing Cobra's existing Media3 player builder.
"""
from __future__ import annotations

import argparse
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Mobile/Guide {label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"Mobile/Guide {label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"Mobile/Guide {label}: end marker missing")
    return text[:a] + replacement + text[b:]


def patch(java: str) -> str:
    java = once(
        java,
        '  private static final String GUIDE_VIEW_MODE = "guide_view_mode";\n',
        '  private static final String GUIDE_VIEW_MODE = "guide_view_mode";\n'
        '  private static final String COBRA_PRIMARY_VIEW = "cobra_primary_view";\n'
        '  private Channel mGuidePreviewChannel;\n'
        '  private String mGuidePreviewKey = "";\n'
        '  private ExoPlayer mCobraPreviewPlayer;\n'
        '  private TextureView mCobraPreviewTexture;\n'
        '  private FrameLayout mCobraPreviewHost;\n'
        '  private boolean mCobraPreviewTriedFallback = false;\n',
        "view + preview state",
    )

    # Mobile and TV Guide are experiences, so expose them in the hamburger menu,
    # not buried in Settings.
    java = once(
        java,
        '    addRail("LIVE TV", v -> showLiveHome());\n    addRail("GUIDE", v -> showGuide());\n',
        '    addRail("MOBILE VIEW", v -> {\n'
        '      mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "mobile").apply();\n'
        '      showCobraMobileView();\n'
        '    });\n'
        '    addRail("TV GUIDE", v -> {\n'
        '      mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();\n'
        '      showGuideGrid();\n'
        '    });\n',
        "main menu destinations",
    )

    # Any automatic return to the legacy channel browser should instead respect
    # the selected structural experience.
    java = java.replace("showLiveHome();", "showCobraPrimaryView();")

    # Stop inline playback when navigating away, and clear restoration state for
    # destinations that are not one of the two Live experiences.
    java = once(
        java,
        '    button.setOnClickListener(v -> { closeCobraDrawer(); listener.onClick(v); });\n',
        '    button.setOnClickListener(v -> {\n'
        '      closeCobraDrawer();\n'
        '      stopCobraPreview();\n'
        '      if (!"MOBILE VIEW".equals(label) && !"TV GUIDE".equals(label)) {\n'
        '        mGuidePreviewChannel = null; mGuidePreviewKey = "";\n'
        '      }\n'
        '      listener.onClick(v);\n'
        '    });\n',
        "navigation preview ownership",
    )

    # Runtime-v3 structural fields. Defaults keep the shell useful even before a
    # 1.3.x ZIP is installed; a valid ZIP can then tune them without another APK.
    java = once(
        java,
        '    int multiMaximumTiles = 4;\n',
        '    int multiMaximumTiles = 4;\n\n'
        '    String defaultPrimaryView = "mobile";\n'
        '    boolean mobilePreviewFirst = true;\n'
        '    boolean mobileBottomNavigation = true;\n'
        '    boolean mobileLongPressContext = true;\n'
        '    int mobilePreviewHeightDp = 220;\n'
        '    int mobileChannelRowHeightDp = 78;\n'
        '    boolean guidePreviewPlayer = true;\n'
        '    boolean guideFirstActivationPreview = true;\n'
        '    boolean guideSecondActivationFullscreen = true;\n'
        '    int guidePreviewHeightDp = 196;\n'
        '    int guideChannelWidthDp = 128;\n'
        '    int guideProgramWidthDp = 210;\n'
        '    int guideRowHeightDp = 68;\n'
        '    int guideHeaderHeightDp = 54;\n',
        "UiContract structural fields",
    )

    structural_parser = r'''        JSONObject views = root.optJSONObject("views");
        if (views != null) {
          String defaultView = views.optString("default", ui.defaultPrimaryView);
          if ("mobile".equals(defaultView) || "tv_guide".equals(defaultView))
            ui.defaultPrimaryView = "tv_guide".equals(defaultView) ? "guide" : "mobile";
          JSONObject mobile = views.optJSONObject("mobile");
          if (mobile != null) {
            ui.mobilePreviewFirst = mobile.optBoolean("preview_first", ui.mobilePreviewFirst);
            ui.mobileBottomNavigation = mobile.optBoolean("bottom_navigation", ui.mobileBottomNavigation);
            ui.mobileLongPressContext = "context_sheet".equals(
                mobile.optString("channel_long_press_action", "context_sheet"));
            ui.mobileChannelRowHeightDp = clamp(
                mobile.optInt("channel_row_height_dp", ui.mobileChannelRowHeightDp), 56, 132);
          }
          JSONObject guide = views.optJSONObject("tv_guide");
          if (guide != null) {
            ui.guidePreviewPlayer = guide.optBoolean("preview_player", ui.guidePreviewPlayer);
            ui.guideFirstActivationPreview = "preview".equals(
                guide.optString("first_activation", "preview"));
            ui.guideSecondActivationFullscreen = "fullscreen".equals(
                guide.optString("second_activation", "fullscreen"));
          }
        }

        JSONObject presentation = root.optJSONObject("presentation");
        if (presentation != null) {
          ui.mobilePreviewHeightDp = clamp(
              presentation.optInt("mobile_preview_height_dp", ui.mobilePreviewHeightDp), 140, 420);
          ui.guidePreviewHeightDp = clamp(
              presentation.optInt("guide_preview_height_dp", ui.guidePreviewHeightDp), 120, 360);
          ui.guideChannelWidthDp = clamp(
              presentation.optInt("guide_channel_width_dp", ui.guideChannelWidthDp), 96, 260);
          ui.guideProgramWidthDp = clamp(
              presentation.optInt("guide_program_width_dp", ui.guideProgramWidthDp), 140, 360);
          ui.guideRowHeightDp = clamp(
              presentation.optInt("guide_row_height_dp", ui.guideRowHeightDp), 54, 120);
          ui.guideHeaderHeightDp = clamp(
              presentation.optInt("guide_header_height_dp", ui.guideHeaderHeightDp), 44, 90);
        }
'''
    java = once(java, "        return ui;\n", structural_parser + "        return ui;\n", "UiContract structural parser")

    helpers = r'''  private String cobraPrimaryView() {
    String fallback = mUi == null ? "mobile" : mUi.defaultPrimaryView;
    String value = mPrefs.getString(COBRA_PRIMARY_VIEW, fallback);
    return "guide".equals(value) ? "guide" : "mobile";
  }

  private void showCobraPrimaryView() {
    if ("guide".equals(cobraPrimaryView())) showGuideGrid();
    else showCobraMobileView();
  }

  private void ensureCobraPreviewSelection(ArrayList<Channel> channels) {
    if (mGuidePreviewChannel != null || channels.isEmpty()) return;
    mGuidePreviewChannel = channels.get(0);
    mGuidePreviewKey = sourceIdForChannel(mGuidePreviewChannel) + "|" + mGuidePreviewChannel.id;
  }

  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {
    stopCobraPreview();
    FrameLayout host = new FrameLayout(this);
    mCobraPreviewHost = host;
    host.setBackground(surface(Color.BLACK, 22, mTheme.line, 1));
    host.setClickable(true);

    mCobraPreviewTexture = new TextureView(this);
    host.addView(mCobraPreviewTexture, new FrameLayout.LayoutParams(-1, -1));

    TextView label = text(channel == null ? "SELECT A CHANNEL TO PREVIEW" :
        "PREVIEW  •  " + channel.name, Color.WHITE, 13, Gravity.LEFT | Gravity.BOTTOM);
    label.setTag("cobra_preview_label");
    label.setPadding(dp(14), dp(8), dp(14), dp(8));
    label.setBackgroundColor(Color.argb(150, 0, 0, 0));
    host.addView(label, new FrameLayout.LayoutParams(-1, dp(48), Gravity.BOTTOM));

    host.setOnClickListener(v -> {
      if (mGuidePreviewChannel != null) promoteCobraPreviewToFullscreen(mGuidePreviewChannel);
    });
    if (channel != null) host.post(() -> startCobraPreview(channel));
    return host;
  }

  private void setCobraPreviewLabel(String value) {
    if (mCobraPreviewHost == null) return;
    View label = mCobraPreviewHost.findViewWithTag("cobra_preview_label");
    if (label instanceof TextView) ((TextView) label).setText(value);
  }

  private void startCobraPreview(Channel channel) {
    if (channel == null || mCobraPreviewTexture == null || channel.primaryUrl == null
        || channel.primaryUrl.isEmpty()) return;
    stopCobraPreviewPlayerOnly();
    try {
      mCobraPreviewTriedFallback = false;
      ExoPlayer preview = buildPlayer(mCobraPreviewTexture, channel, true);
      mCobraPreviewPlayer = preview;
      preview.addListener(new Player.Listener() {
        @Override public void onPlaybackStateChanged(int playbackState) {
          if (preview != mCobraPreviewPlayer) return;
          if (playbackState == Player.STATE_BUFFERING) setCobraPreviewLabel("BUFFERING  •  " + channel.name);
          else if (playbackState == Player.STATE_READY) setCobraPreviewLabel("LIVE PREVIEW  •  " + channel.name + "  •  TAP VIDEO FOR FULLSCREEN");
        }
        @Override public void onPlayerError(PlaybackException error) {
          if (preview != mCobraPreviewPlayer) return;
          if (!mCobraPreviewTriedFallback && channel.fallbackUrl != null
              && !channel.fallbackUrl.isEmpty() && !channel.fallbackUrl.equals(channel.primaryUrl)) {
            mCobraPreviewTriedFallback = true;
            preview.setMediaItem(mediaItem(channel.fallbackUrl)); preview.prepare(); preview.play();
            return;
          }
          setCobraPreviewLabel("PREVIEW ERROR  •  " + channel.name);
        }
      });
      preview.setMediaItem(mediaItem(channel.primaryUrl));
      preview.prepare(); preview.play();
    } catch (Exception error) {
      setCobraPreviewLabel("PREVIEW UNAVAILABLE  •  " + channel.name);
    }
  }

  private void stopCobraPreviewPlayerOnly() {
    ExoPlayer preview = mCobraPreviewPlayer;
    mCobraPreviewPlayer = null;
    if (preview == null) return;
    try { if (mCobraPreviewTexture != null) preview.clearVideoTextureView(mCobraPreviewTexture); } catch (Exception ignored) {}
    try { preview.stop(); } catch (Exception ignored) {}
    try { preview.release(); } catch (Exception ignored) {}
  }

  private void stopCobraPreview() {
    stopCobraPreviewPlayerOnly();
    mCobraPreviewTexture = null;
    mCobraPreviewHost = null;
  }

  private void promoteCobraPreviewToFullscreen(Channel channel) {
    stopCobraPreview();
    playChannel(channel);
  }

  private void closeFullscreenToCobraView() {
    closePlayer();
    if (mGuidePreviewChannel != null) showCobraPrimaryView();
  }

  private String mobileGuideSummary(Channel channel) {
    ProgramPair pair = programFor(channel);
    if (pair == null || pair.now == null || pair.now.isEmpty())
      return providerBadge(channel) + "  •  " + channel.group;
    return "NOW  •  " + pair.now;
  }

  private void showCobraMobileView() {
    stopCobraPreview();
    clearStage("COBRA • MOBILE");
    ArrayList<Channel> visible = new ArrayList<>(filteredChannels(false, false));
    ensureCobraPreviewSelection(visible);

    LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
    TextView heading = text("MOBILE VIEW", mTheme.text, 20, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    heading.setTypeface(null, Typeface.BOLD);
    root.addView(heading, new LinearLayout.LayoutParams(-1, dp(50)));

    if (mUi.mobilePreviewFirst) {
      root.addView(cobraPreviewPanel(mGuidePreviewChannel, false),
          new LinearLayout.LayoutParams(-1, dp(mUi.mobilePreviewHeightDp)));
    }

    Button category = action("CATEGORY  •  " + mCategory + "   ▾");
    category.setOnClickListener(v -> showCobraCategoryPicker("COBRA • MOBILE", false, false, false));
    root.addView(category, new LinearLayout.LayoutParams(-1, dp(56)));

    ScrollView scroll = new ScrollView(this);
    LinearLayout rows = new LinearLayout(this); rows.setOrientation(LinearLayout.VERTICAL);
    for (Channel channel : visible) {
      final Channel item = channel;
      Button row = action(channel.name + "\n" + mobileGuideSummary(channel));
      row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL); row.setAllCaps(false);
      row.setOnClickListener(v -> selectGuidePreview(item));
      row.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(mUi.mobileChannelRowHeightDp));
      p.bottomMargin = dp(6); rows.addView(row, p);
    }
    scroll.addView(rows); root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

    if (mUi.mobileBottomNavigation) {
      LinearLayout nav = new LinearLayout(this); nav.setGravity(Gravity.CENTER);
      Button live = action("LIVE");
      Button guide = action("TV GUIDE");
      Button favorites = action("FAVORITES");
      Button search = action("SEARCH");
      live.setOnClickListener(v -> showCobraMobileView());
      guide.setOnClickListener(v -> { mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply(); showGuideGrid(); });
      favorites.setOnClickListener(v -> { stopCobraPreview(); mGuidePreviewChannel=null; mGuidePreviewKey=""; showFavorites(); });
      search.setOnClickListener(v -> { stopCobraPreview(); mGuidePreviewChannel=null; mGuidePreviewKey=""; showSearch(); });
      for (Button b : new Button[]{live, guide, favorites, search}) nav.addView(b, new LinearLayout.LayoutParams(0, dp(58), 1));
      root.addView(nav, new LinearLayout.LayoutParams(-1, dp(62)));
    }
    mStage.addView(root, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private boolean closeCobraChannelActions() {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    View old = decor.findViewWithTag("cobra_channel_actions");
    if (old == null) return false;
    decor.removeView(old); return true;
  }

  private void addCobraSheetAction(LinearLayout sheet, String label, View.OnClickListener listener) {
    Button button = action(label); button.setAllCaps(false); button.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
    button.setOnClickListener(v -> { closeCobraChannelActions(); listener.onClick(v); });
    LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(58)); p.bottomMargin = dp(5); sheet.addView(button, p);
  }

  private void showCobraChannelActions(Channel channel) {
    if (!mUi.mobileLongPressContext) { toggleFavorite(channel); return; }
    closeCobraChannelActions();
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    FrameLayout shield = new FrameLayout(this); shield.setTag("cobra_channel_actions");
    shield.setClickable(true); shield.setBackgroundColor(Color.argb(118, 0, 0, 0));
    shield.setOnClickListener(v -> closeCobraChannelActions());

    LinearLayout sheet = new LinearLayout(this); sheet.setOrientation(LinearLayout.VERTICAL);
    sheet.setClickable(true); sheet.setPadding(dp(16), dp(12), dp(16), dp(18));
    sheet.setBackground(surface(cobraAlpha(mTheme.panel, 250), 26, mTheme.line, 1));
    TextView title = text(channel.name, mTheme.text, 18, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    title.setTypeface(null, Typeface.BOLD); sheet.addView(title, new LinearLayout.LayoutParams(-1, dp(54)));

    boolean favorite = mFavorites.contains(channel.id);
    addCobraSheetAction(sheet, favorite ? "★  Remove from Favorites" : "☆  Add to Favorites", v -> {
      toggleFavorite(channel); showCobraPrimaryView();
    });
    addCobraSheetAction(sheet, mRecordingSession.isEmpty() ? "●  Record Channel" : "■  Stop Recording", v -> toggleRecording(channel));
    addCobraSheetAction(sheet, "▤  View Channel Guide", v -> showProgramGuide(channel));
    addCobraSheetAction(sheet, "ⓘ  Channel Information", v -> {
      ProgramPair pair = programFor(channel);
      String detail = channel.name + "\n" + channel.group;
      if (pair != null && pair.now != null && !pair.now.isEmpty()) detail += "\n\nNow • " + pair.now;
      if (pair != null && pair.next != null && !pair.next.isEmpty()) detail += "\nNext • " + pair.next;
      showError("Channel information", detail);
    });
    addCobraSheetAction(sheet, "◈  Source Information", v -> showError("Source information", providerBadge(channel)));
    addCobraSheetAction(sheet, "Close", v -> {});

    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM);
    params.setMargins(dp(12), dp(12), dp(12), dp(12)); shield.addView(sheet, params);
    decor.addView(shield, new FrameLayout.LayoutParams(-1, -1)); sheet.bringToFront();
  }

  private void selectGuidePreview(Channel channel) {
    String key = sourceIdForChannel(channel) + "|" + channel.id;
    if (key.equals(mGuidePreviewKey) && mGuidePreviewChannel != null
        && mUi.guideSecondActivationFullscreen) {
      promoteCobraPreviewToFullscreen(channel); return;
    }
    mGuidePreviewChannel = channel; mGuidePreviewKey = key;
    if (!mUi.guideFirstActivationPreview) { promoteCobraPreviewToFullscreen(channel); return; }
    showCobraPrimaryView();
  }

  private String guideTitleAt(Channel channel, long instant) {
    ArrayList<GuideProgram> programs = mGuidePrograms.get(sourceIdForChannel(channel) + "|" + channel.epgId);
    if (programs != null) for (GuideProgram p : programs)
      if (p.start <= instant && p.stop > instant) return p.title == null || p.title.isEmpty() ? "Programme" : p.title;
    ProgramPair pair = programFor(channel);
    return pair != null && pair.now != null && !pair.now.isEmpty() ? pair.now : "No guide data";
  }

'''
    java = once(java, "  private void showGuide() {\n", helpers + "  private void showGuide() {\n", "structural helpers")

    # Replace the pseudo NOW/NEXT table with a true time-axis grid and exposed
    # preview. Programme cells select preview; selecting the same channel again
    # promotes the same stream fullscreen.
    guide_grid = r'''  private void showGuideGrid() {
    stopCobraPreview();
    clearStage("COBRA • TV GUIDE");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
    ArrayList<Channel> visible = new ArrayList<>(filteredChannels(false, false));
    ensureCobraPreviewSelection(visible);
    status("TV Guide • tap once to preview • tap selected channel again for fullscreen • hold for channel menu");

    if (mUi.guidePreviewPlayer) {
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(mUi.guidePreviewHeightDp)));
    }
    mStage.addView(cobraGuideToolbar("TV GRID"), new LinearLayout.LayoutParams(-1, dp(60)));

    long now = System.currentTimeMillis();
    long slot = now - (now % 1800000L);
    SimpleDateFormat clock = new SimpleDateFormat("h:mm a", Locale.US);
    LinearLayout grid = new LinearLayout(this); grid.setOrientation(LinearLayout.VERTICAL);
    LinearLayout header = new LinearLayout(this); header.setGravity(Gravity.CENTER_VERTICAL);
    header.setBackground(surface(cobraAlpha(mTheme.panel, 238), 14, mTheme.line, 1));
    header.addView(text("CHANNEL", mTheme.muted, 12, Gravity.LEFT | Gravity.CENTER_VERTICAL),
        new LinearLayout.LayoutParams(dp(mUi.guideChannelWidthDp), dp(mUi.guideHeaderHeightDp)));
    for (int i = 0; i < 3; i++) {
      String title = (i == 0 ? "NOW  •  " : "") + clock.format(new Date(slot + i * 1800000L));
      header.addView(text(title, i == 0 ? mTheme.accentSoft : mTheme.muted, 12, Gravity.CENTER),
          new LinearLayout.LayoutParams(dp(mUi.guideProgramWidthDp), dp(mUi.guideHeaderHeightDp)));
    }
    grid.addView(header);

    int number = 1;
    for (Channel channel : visible) {
      final Channel item = channel;
      LinearLayout row = new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL);
      Button channelCell = action(String.format(Locale.US, "%03d  %s", number++, channel.name));
      channelCell.setAllCaps(false); channelCell.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      channelCell.setOnClickListener(v -> selectGuidePreview(item));
      channelCell.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
      row.addView(channelCell, new LinearLayout.LayoutParams(dp(mUi.guideChannelWidthDp), dp(mUi.guideRowHeightDp)));
      for (int i = 0; i < 3; i++) {
        final long when = slot + i * 1800000L;
        Button program = action(guideTitleAt(item, when));
        program.setAllCaps(false); program.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
        program.setOnClickListener(v -> selectGuidePreview(item));
        program.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
        row.addView(program, new LinearLayout.LayoutParams(dp(mUi.guideProgramWidthDp), dp(mUi.guideRowHeightDp)));
      }
      LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(-2, dp(mUi.guideRowHeightDp)); rp.bottomMargin = dp(4); grid.addView(row, rp);
    }

    android.widget.HorizontalScrollView horizontal = new android.widget.HorizontalScrollView(this);
    horizontal.setFillViewport(true); horizontal.addView(grid);
    ScrollView vertical = new ScrollView(this); vertical.addView(horizontal);
    mStage.addView(vertical, new LinearLayout.LayoutParams(-1, 0, 1));
  }

'''
    java = replace_between(java, "  private void showGuideGrid() {\n", "  private void showGuideCompact() {\n",
                           guide_grid, "TV Guide grid")

    # Long-press must be useful everywhere a legacy browser can still be reached.
    legacy_long = '''    row.setOnLongClickListener(v -> {
      if (guideMode) showProgramGuide(channel); else toggleFavorite(channel);
      return true;
    });
'''
    if legacy_long in java:
        java = java.replace(legacy_long,
            '''    row.setOnLongClickListener(v -> {
      showCobraChannelActions(channel);
      return true;
    });
''', 1)

    # Installing a UI ZIP should reveal the changed experience immediately.
    java = java.replace("          buildShell();\n          showSettings();\n          toast(\"Cobra UI package installed\");",
                        "          stopCobraPreview();\n          buildShell();\n          showCobraPrimaryView();\n          toast(\"Cobra UI package installed\");", 1)

    # Fullscreen exit restores the inline preview when fullscreen was promoted
    # from Mobile/Guide; other player flows keep their existing exit behavior.
    java = once(
        java,
        "    if (mPlayerOverlay != null) {\n      if (closePlayerSettingsDrawer()) return;\n      closePlayer();\n      return;\n    }\n",
        "    if (mPlayerOverlay != null) {\n      if (closePlayerSettingsDrawer()) return;\n      closeFullscreenToCobraView();\n      return;\n    }\n",
        "fullscreen back restore",
    )
    java = java.replace("close.setOnClickListener(v -> closePlayer());",
                        "close.setOnClickListener(v -> closeFullscreenToCobraView());")

    java = once(java, "  @Override\n  public void onBackPressed() {\n",
                "  @Override\n  public void onBackPressed() {\n    if (closeCobraChannelActions()) return;\n",
                "bottom-sheet back dismissal")
    return java


def verify(java: str) -> None:
    required = (
        'addRail("MOBILE VIEW"',
        'addRail("TV GUIDE"',
        "mCobraPreviewPlayer",
        "cobraPreviewPanel(",
        "LIVE PREVIEW",
        "TAP VIDEO FOR FULLSCREEN",
        'setTag("cobra_channel_actions")',
        "showCobraChannelActions(item)",
        "guideTitleAt(item, when)",
        "HorizontalScrollView",
        "guideFirstActivationPreview",
        "guideSecondActivationFullscreen",
        "mobilePreviewHeightDp",
        "showCobraPrimaryView();\n          toast(\"Cobra UI package installed\")",
        "closeFullscreenToCobraView()",
        "if (closeCobraChannelActions()) return;",
        "COBRA_UI_RUNTIME = 3",
        "closePlayerSettingsDrawer()",
        "Crop / Fill",
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Missing Mobile/Guide contract: " + token)
    if java.count("  private void showGuideCompact() {") != 1:
        raise RuntimeError("TV Guide replacement duplicated showGuideCompact boundary")
    if 'COBRA VIEW  •  ' in java:
        raise RuntimeError("Primary Mobile/TV Guide selector is still buried in Settings")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra Mobile/TV Guide main-menu + exposed preview + long-press sheet runtime applied")


if __name__ == "__main__":
    main()
