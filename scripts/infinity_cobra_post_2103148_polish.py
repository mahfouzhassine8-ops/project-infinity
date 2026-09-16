#!/usr/bin/env python3
"""Post-2103148 Cobra polish pass.

Presentation-shell only. Keeps the locked 2103148 native engine bytes untouched.

Repairs:
- push-content Cobra drawer with collapse control
- drawer View Mode and Power surfaces
- internal Back navigation (Settings no longer exits to Android)
- four genuinely distinct Guide renderers
- player readability across appearance modes
- player LIVE/status chrome hides with player controls/PiP
- expanded Aspect / Display modes
- Xtream subscription expiration/status summary in Settings
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def method_end(text: str, start: int) -> int:
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError("method opening brace missing")
    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if c == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if c == "*" and n == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote is not None:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
            i += 1
            continue
        if c == "/" and n == "/":
            line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            block_comment = True
            i += 2
            continue
        if c in ('"', "'"):
            quote = c
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise RuntimeError("method closing brace missing")


def span(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    if start < 0:
        raise RuntimeError("missing method: " + signature.strip())
    if text.find(signature, start + 1) >= 0:
        raise RuntimeError("duplicate method: " + signature.strip())
    return start, method_end(text, start)


def replace_method(text: str, signature: str, replacement: str) -> str:
    a, b = span(text, signature)
    return text[:a] + replacement.rstrip() + "\n" + text[b:]


def inject_after_signature(text: str, signature: str, addition: str) -> str:
    a, b = span(text, signature)
    block = text[a:b]
    brace = block.find("{")
    if brace < 0:
        raise RuntimeError("method brace missing: " + signature.strip())
    block = block[: brace + 1] + "\n" + addition.rstrip() + "\n" + block[brace + 1 :]
    return text[:a] + block + text[b:]


def inject_if_present(text: str, signature: str, addition: str) -> str:
    if signature not in text:
        return text
    return inject_after_signature(text, signature, addition)


def patch(java: str) -> str:
    anchor = '  private JSONObject mCobraPaletteCache;\n'
    if java.count(anchor) != 1:
        raise RuntimeError("2103148 appearance state anchor missing")
    java = java.replace(
        anchor,
        anchor
        + '  private static final String COBRA_ASPECT_MODE = "cobra_player_aspect_mode";\n'
        + '  private static final String COBRA_SUBSCRIPTION_PREFIX = "cobra_subscription|";\n'
        + '  private String mCobraInternalScreen = "root";\n'
        + '  private boolean mCobraDrawerShifted = false;\n',
        1,
    )

    close_drawer = r'''  private boolean closeCobraExperienceDrawer() {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    View old = decor.findViewWithTag("cobra_experience_drawer");
    boolean hadDrawer = old != null || mCobraDrawerShifted;
    if (old != null) decor.removeView(old);
    if (mCobraDrawerShifted) animateCobraDrawerShift(0f);
    return hadDrawer;
  }'''
    java = replace_method(java, "  private boolean closeCobraExperienceDrawer() {", close_drawer)

    a = java.find("  private void addCobraDrawerAction(LinearLayout list, String label, View.OnClickListener listener) {")
    b = java.find("  private void addRail(String label, View.OnClickListener listener) {", a)
    if a < 0 or b < 0:
        raise RuntimeError("drawer region markers missing")
    drawer_region = r'''  private void animateCobraDrawerShift(float translation) {
    if (mStage != null)
      mStage.animate().translationX(translation).setDuration(190L).start();
    if (mHeader != null)
      mHeader.animate().translationX(translation).setDuration(190L).start();
    mCobraDrawerShifted = translation != 0f;
  }

  private void addCobraDrawerAction(LinearLayout list, String label, View.OnClickListener listener) {
    Button button = action(label);
    button.setAllCaps(false);
    button.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
    button.setOnClickListener(v -> {
      closeCobraExperienceDrawer();
      listener.onClick(v);
    });
    LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(60));
    p.bottomMargin = dp(5);
    list.addView(button, p);
  }

  private boolean closeCobraPowerMenu() {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    View old = decor.findViewWithTag("cobra_power_menu");
    if (old == null) return false;
    decor.removeView(old);
    return true;
  }

  private void showCobraPowerMenu() {
    closeCobraPowerMenu();
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    FrameLayout shield = new FrameLayout(this);
    shield.setTag("cobra_power_menu");
    shield.setClickable(true);
    shield.setBackgroundColor(Color.argb(118, 0, 0, 0));
    shield.setOnClickListener(v -> closeCobraPowerMenu());

    LinearLayout sheet = new LinearLayout(this);
    sheet.setOrientation(LinearLayout.VERTICAL);
    sheet.setClickable(true);
    sheet.setPadding(dp(18), dp(14), dp(18), dp(18));
    sheet.setBackground(surface(
        cobraThemeColor("panel", mTheme.panel), 28,
        cobraThemeColor("line", mTheme.line), 1));

    TextView title = text("POWER", cobraThemeColor("text", mTheme.text),
        18, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    title.setTypeface(null, Typeface.BOLD);
    sheet.addView(title, new LinearLayout.LayoutParams(-1, dp(52)));

    Button switchInfinity = action("∞  Switch to Infinity");
    Button exit = action("⏻  Exit Infinity");
    Button cancel = action("Cancel");
    switchInfinity.setOnClickListener(v -> {
      closeCobraPowerMenu();
      stopCobraPreview();
      if (mPlayerOverlay != null) closePlayer();
      releaseMulti();
      returnToInfinity();
    });
    exit.setOnClickListener(v -> {
      closeCobraPowerMenu();
      stopCobraPreview();
      if (mPlayerOverlay != null) closePlayer();
      releaseMulti();
      finishAndRemoveTask();
    });
    cancel.setOnClickListener(v -> closeCobraPowerMenu());

    for (Button button : new Button[]{switchInfinity, exit, cancel}) {
      button.setAllCaps(false);
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(60));
      p.bottomMargin = dp(6);
      sheet.addView(button, p);
    }

    FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM);
    p.setMargins(dp(10), dp(10), dp(10), dp(10));
    shield.addView(sheet, p);
    decor.addView(shield, new FrameLayout.LayoutParams(-1, -1));
    sheet.bringToFront();
  }

  private boolean closeCobraViewModeMenu() {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    View old = decor.findViewWithTag("cobra_view_mode_menu");
    if (old == null) return false;
    decor.removeView(old);
    return true;
  }

  private void applyCobraGuideViewMode(String value) {
    mPrefs.edit().putString(GUIDE_VIEW_MODE, value)
        .putString(COBRA_PRIMARY_VIEW, "guide").apply();
    mCobraInternalScreen = "root";
    showGuide();
  }

  private void addCobraViewModeAction(
      LinearLayout sheet, String mode, String title, String description) {
    boolean active = mode.equals(cobraGuideViewMode());
    Button button = action((active ? "●  " : "○  ") + title + "\n" + description);
    button.setAllCaps(false);
    button.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
    button.setOnClickListener(v -> {
      closeCobraViewModeMenu();
      applyCobraGuideViewMode(mode);
    });
    LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(78));
    p.bottomMargin = dp(6);
    sheet.addView(button, p);
  }

  private void showCobraViewModeMenu() {
    closeCobraViewModeMenu();
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    FrameLayout shield = new FrameLayout(this);
    shield.setTag("cobra_view_mode_menu");
    shield.setClickable(true);
    shield.setBackgroundColor(Color.argb(112, 0, 0, 0));
    shield.setOnClickListener(v -> closeCobraViewModeMenu());

    LinearLayout sheet = new LinearLayout(this);
    sheet.setOrientation(LinearLayout.VERTICAL);
    sheet.setClickable(true);
    sheet.setPadding(dp(16), dp(14), dp(16), dp(18));
    sheet.setBackground(surface(
        cobraThemeColor("panel", mTheme.panel), 28,
        cobraThemeColor("line", mTheme.line), 1));

    TextView title = text("VIEW MODE", cobraThemeColor("text", mTheme.text),
        18, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    title.setTypeface(null, Typeface.BOLD);
    sheet.addView(title, new LinearLayout.LayoutParams(-1, dp(52)));

    addCobraViewModeAction(sheet, "grid", "TV Grid",
        "Timeline guide with channel and programme columns");
    addCobraViewModeAction(sheet, "compact", "Compact",
        "Dense channel list for fast browsing");
    addCobraViewModeAction(sheet, "cards", "Cards",
        "Touch-first programme cards and larger information");
    addCobraViewModeAction(sheet, "focus", "Focus",
        "Large preview with a focused channel strip");

    Button cancel = action("Cancel");
    cancel.setOnClickListener(v -> closeCobraViewModeMenu());
    sheet.addView(cancel, new LinearLayout.LayoutParams(-1, dp(56)));

    FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM);
    p.setMargins(dp(10), dp(10), dp(10), dp(10));
    shield.addView(sheet, p);
    decor.addView(shield, new FrameLayout.LayoutParams(-1, -1));
    sheet.bringToFront();
  }

  private void toggleCobraDrawer() {
    if (closeCobraExperienceDrawer()) return;

    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    int screen = getResources().getDisplayMetrics().widthPixels;
    int width = Math.min(dp(320), Math.max(dp(260), Math.round(screen * 0.78f)));

    FrameLayout shield = new FrameLayout(this);
    shield.setTag("cobra_experience_drawer");
    shield.setClickable(true);
    shield.setBackgroundColor(Color.argb(44, 0, 0, 0));
    shield.setOnClickListener(v -> closeCobraExperienceDrawer());

    LinearLayout drawer = new LinearLayout(this);
    drawer.setOrientation(LinearLayout.VERTICAL);
    drawer.setClickable(true);
    drawer.setPadding(dp(14), dp(12), dp(14), dp(14));
    drawer.setBackground(surface(
        cobraThemeColor("rail", mTheme.rail), 0,
        cobraThemeColor("line", mTheme.line), 1));

    LinearLayout header = new LinearLayout(this);
    header.setGravity(Gravity.CENTER_VERTICAL);
    Button collapse = action("‹");
    collapse.setContentDescription("Collapse Cobra drawer");
    collapse.setOnClickListener(v -> closeCobraExperienceDrawer());
    TextView brand = text("COBRA", cobraThemeColor("accent_soft", mTheme.accentSoft),
        16, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    brand.setTypeface(null, Typeface.BOLD);
    header.addView(collapse, new LinearLayout.LayoutParams(dp(54), dp(54)));
    header.addView(brand, new LinearLayout.LayoutParams(0, dp(54), 1));
    drawer.addView(header, new LinearLayout.LayoutParams(-1, dp(58)));

    ScrollView menuScroll = new ScrollView(this);
    LinearLayout menu = new LinearLayout(this);
    menu.setOrientation(LinearLayout.VERTICAL);

    addCobraDrawerAction(menu, "SEARCH", v -> {
      stopCobraPreview(); mCobraInternalScreen = "internal"; showSearch();
    });
    addCobraDrawerAction(menu, "TV", v -> {
      mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
      mCobraInternalScreen = "root";
      showCobraTvHub();
    });
    addCobraDrawerAction(menu, "MOVIES", v -> {
      stopCobraPreview(); mCobraInternalScreen = "internal"; showMovies();
    });
    addCobraDrawerAction(menu, "SHOWS", v -> {
      stopCobraPreview(); mCobraInternalScreen = "internal"; showSeries();
    });
    addCobraDrawerAction(menu, "RECORDINGS", v -> {
      stopCobraPreview(); mCobraInternalScreen = "internal"; showRecordings();
    });
    addCobraDrawerAction(menu, "MY LIST", v -> {
      stopCobraPreview(); mCobraInternalScreen = "internal"; showWatchlist();
    });
    addCobraDrawerAction(menu, "VIEW MODE  •  " + cobraGuideViewLabel(),
        v -> showCobraViewModeMenu());

    menuScroll.addView(menu);
    drawer.addView(menuScroll, new LinearLayout.LayoutParams(-1, 0, 1));

    LinearLayout footer = new LinearLayout(this);
    footer.setGravity(Gravity.CENTER_VERTICAL);
    Button settings = action("⚙  SETTINGS");
    Button power = action("⏻  POWER");
    settings.setOnClickListener(v -> {
      closeCobraExperienceDrawer();
      stopCobraPreview();
      mCobraInternalScreen = "internal";
      showSettings();
    });
    power.setOnClickListener(v -> {
      closeCobraExperienceDrawer();
      showCobraPowerMenu();
    });
    footer.addView(settings, new LinearLayout.LayoutParams(0, dp(58), 1));
    LinearLayout.LayoutParams pp = new LinearLayout.LayoutParams(0, dp(58), 1);
    pp.leftMargin = dp(8);
    footer.addView(power, pp);
    drawer.addView(footer, new LinearLayout.LayoutParams(-1, dp(62)));

    FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(width, -1, Gravity.LEFT);
    shield.addView(drawer, p);
    decor.addView(shield, new FrameLayout.LayoutParams(-1, -1));
    drawer.bringToFront();
    animateCobraDrawerShift(width);
  }

  private void closeCobraDrawer() {
    closeCobraExperienceDrawer();
    if (mRail != null) mRail.setVisibility(View.GONE);
  }
'''
    java = java[:a] + drawer_region.rstrip() + "\n\n" + java[b:]

    java = replace_method(java, "  private void showGuide() {", r'''  private void showGuide() {
    String mode = cobraGuideViewMode();
    if ("compact".equals(mode)) showGuideCompact();
    else if ("cards".equals(mode)) showGuideCards();
    else if ("focus".equals(mode)) showGuideFocus();
    else showGuideGrid();
  }''')

    java = replace_method(java, "  private void showCobraPrimaryView() {", r'''  private void showCobraPrimaryView() {
    if ("guide".equals(cobraPrimaryView())) showGuide();
    else showCobraMobileView();
  }''')

    java = replace_method(java, "  private void selectCobraCategory(String value) {", r'''  private void selectCobraCategory(String value) {
    mCategory = value;
    mGuidePreviewArmed = false;
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
    mCobraInternalScreen = "root";
    showGuide();
  }''')

    java = inject_after_signature(java, "  private void showGuideGrid() {", '    mCobraInternalScreen = "root";')

    compact = r'''  private void showGuideCompact() {
    stopCobraPreview();
    clearStage("COBRA • COMPACT");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
    mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView();
    ensureCobraPreviewSelection(visible);
    if (mUi.guidePreviewPlayer) {
      int previewHeight = Math.max(124, mUi.guidePreviewHeightDp / 2);
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(previewHeight)));
    }
    LinearLayout head = new LinearLayout(this);
    head.setGravity(Gravity.CENTER_VERTICAL);
    Button categories = action("‹  CATEGORIES");
    categories.setOnClickListener(v -> showCobraTvHub());
    String label = mCategory == null || "ALL".equals(mCategory)
        ? "ALL CHANNELS" : mCategory.replace("MY:", "MY GROUP • ");
    TextView mode = text("COMPACT  •  " + label,
        cobraThemeColor("muted", mTheme.muted), 12, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    head.addView(categories, new LinearLayout.LayoutParams(dp(148), dp(52)));
    head.addView(mode, new LinearLayout.LayoutParams(0, dp(52), 1));
    mStage.addView(head, new LinearLayout.LayoutParams(-1, dp(54)));
    ScrollView scroll = new ScrollView(this);
    LinearLayout list = new LinearLayout(this);
    list.setOrientation(LinearLayout.VERTICAL);
    int number = 1;
    for (Channel channel : visible) {
      final Channel item = channel;
      ProgramPair pair = programFor(channel);
      String now = pair != null && pair.now != null && !pair.now.isEmpty() ? pair.now : "No guide data";
      Button row = action(String.format(Locale.US, "%03d  %s  •  %s", number++, channel.name, now));
      row.setAllCaps(false); row.setTextSize(12); row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      row.setOnClickListener(v -> selectGuidePreview(item));
      row.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(50)); p.bottomMargin = dp(2); list.addView(row, p);
    }
    scroll.addView(list);
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }'''
    java = replace_method(java, "  private void showGuideCompact() {", compact)

    cards = r'''  private void showGuideCards() {
    stopCobraPreview();
    clearStage("COBRA • CARDS");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
    mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView();
    ensureCobraPreviewSelection(visible);
    if (mUi.guidePreviewPlayer) {
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(Math.max(190, mUi.guidePreviewHeightDp))));
      mStage.addView(cobraPreviewDetails(mGuidePreviewChannel), new LinearLayout.LayoutParams(-1, dp(92)));
    }
    LinearLayout head = new LinearLayout(this); head.setGravity(Gravity.CENTER_VERTICAL);
    Button categories = action("‹  CATEGORIES"); categories.setOnClickListener(v -> showCobraTvHub());
    TextView title = text("CARDS  •  TOUCH BROWSE", cobraThemeColor("accent_soft", mTheme.accentSoft), 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL); title.setTypeface(null, Typeface.BOLD);
    head.addView(categories, new LinearLayout.LayoutParams(dp(148), dp(54)));
    head.addView(title, new LinearLayout.LayoutParams(0, dp(54), 1));
    mStage.addView(head, new LinearLayout.LayoutParams(-1, dp(56)));
    ScrollView scroll = new ScrollView(this);
    LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); list.setPadding(dp(4), dp(4), dp(4), dp(8));
    for (Channel channel : visible) {
      final Channel item = channel; ProgramPair pair = programFor(channel);
      String now = pair != null && pair.now != null && !pair.now.isEmpty() ? pair.now : "No guide data";
      String next = pair != null && pair.next != null && !pair.next.isEmpty() ? pair.next : "—";
      Button card = action(channel.name + "\nNOW  •  " + now + "\nNEXT •  " + next);
      card.setAllCaps(false); card.setTextSize(14); card.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      card.setPadding(dp(18), dp(10), dp(18), dp(10));
      card.setOnClickListener(v -> selectGuidePreview(item));
      card.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(112)); p.bottomMargin = dp(10); list.addView(card, p);
    }
    scroll.addView(list);
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }'''
    focus = r'''  private void showGuideFocus() {
    stopCobraPreview();
    clearStage("COBRA • FOCUS");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
    mCobraInternalScreen = "root";
    ArrayList<Channel> visible = cobraChannelsForCurrentView();
    ensureCobraPreviewSelection(visible);
    LinearLayout top = new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL);
    Button categories = action("‹  CATEGORIES"); categories.setOnClickListener(v -> showCobraTvHub());
    TextView title = text("FOCUS", cobraThemeColor("accent_soft", mTheme.accentSoft), 15,
        Gravity.LEFT | Gravity.CENTER_VERTICAL); title.setTypeface(null, Typeface.BOLD);
    top.addView(categories, new LinearLayout.LayoutParams(dp(148), dp(52)));
    top.addView(title, new LinearLayout.LayoutParams(0, dp(52), 1));
    mStage.addView(top, new LinearLayout.LayoutParams(-1, dp(54)));
    if (mUi.guidePreviewPlayer) {
      int previewHeight = Math.max(250, mUi.guidePreviewHeightDp + 72);
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true), new LinearLayout.LayoutParams(-1, dp(previewHeight)));
      mStage.addView(cobraPreviewDetails(mGuidePreviewChannel), new LinearLayout.LayoutParams(-1, dp(104)));
    }
    android.widget.HorizontalScrollView strip = new android.widget.HorizontalScrollView(this);
    LinearLayout row = new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setPadding(dp(4), dp(4), dp(4), dp(4));
    for (Channel channel : visible) {
      final Channel item = channel; ProgramPair pair = programFor(channel);
      String now = pair != null && pair.now != null && !pair.now.isEmpty() ? pair.now : "No guide data";
      Button channelButton = action(channel.name + "\n" + now);
      channelButton.setAllCaps(false); channelButton.setTextSize(12); channelButton.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      channelButton.setOnClickListener(v -> selectGuidePreview(item));
      channelButton.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(dp(190), dp(86)); p.rightMargin = dp(8); row.addView(channelButton, p);
    }
    strip.addView(row);
    mStage.addView(strip, new LinearLayout.LayoutParams(-1, dp(96)));
  }'''
    focus_start, _ = span(java, "  private void showGuideFocus() {")
    java = java[:focus_start] + cards + "\n\n" + java[focus_start:]
    java = replace_method(java, "  private void showGuideFocus() {", focus)

    for sig in ("  private void showCobraMobileView() {", "  private void showCobraTvHub() {"):
        java = inject_if_present(java, sig, '    mCobraInternalScreen = "root";')
    for sig in (
        "  private void showSettings() {", "  private void showSearch() {", "  private void showMovies() {",
        "  private void showSeries() {", "  private void showRecordings() {", "  private void showWatchlist() {",
        "  private void showSources() {", "  private void showProfiles() {", "  private void showDiscover() {",
        "  private void showContinueWatching() {",
    ):
        java = inject_if_present(java, sig, '    mCobraInternalScreen = "internal";')

    back = r'''  @Override
  public void onBackPressed() {
    if (closeCobraPowerMenu()) return;
    if (closeCobraViewModeMenu()) return;
    if (closeCobraChannelActions()) return;
    if (closeCobraExperienceDrawer()) return;
    if (mPlayerOverlay != null) {
      if (closePlayerSettingsDrawer()) return;
      closeFullscreenToCobraView();
      return;
    }
    if (mMultiOverlay != null) { releaseMulti(); return; }
    if (!"root".equals(mCobraInternalScreen)) { showCobraPrimaryView(); return; }
    moveTaskToBack(true);
  }'''
    java = replace_method(java, "  @Override\n  public void onBackPressed() {", back)

    a, b = span(java, "  private void showPlayerSettingsDrawer() {")
    settings_drawer = java[a:b]
    settings_drawer, n = re.subn(
        r'drawer\.setBackground\(surface\([^;]+;',
        'drawer.setBackground(surface(Color.rgb(9, 15, 22), 24, Color.rgb(55, 68, 82), 1));',
        settings_drawer, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError("player drawer background anchor missing")
    settings_drawer, n = re.subn(
        r'TextView title = text\("PLAYER SETTINGS",[^,]+, 18,',
        'TextView title = text("PLAYER SETTINGS", Color.WHITE, 18,',
        settings_drawer, count=1)
    if n != 1:
        raise RuntimeError("player drawer title anchor missing")
    if 'fit.setOnClickListener(v -> cycleAspectMode());' not in settings_drawer:
        raise RuntimeError("aspect button listener anchor missing")
    settings_drawer = settings_drawer.replace(
        'fit.setOnClickListener(v -> cycleAspectMode());',
        'fit.setText("Aspect / Display");\n    fit.setOnClickListener(v -> showCobraAspectPicker());', 1)
    loop_anchor = "    for (Button item : mUi.orderSettingsActions("
    if loop_anchor not in settings_drawer:
        loop_anchor = "    for (Button item : new Button[]{"
    idx = settings_drawer.find(loop_anchor)
    if idx < 0:
        raise RuntimeError("player settings button loop missing")
    style = '''    for (Button chromeButton : new Button[]{audio, fit, cast, source, guide, multi, close}) {
      chromeButton.setTextColor(Color.WHITE);
      chromeButton.setBackground(surface(Color.rgb(20, 28, 38), 18, Color.rgb(55, 68, 82), 1));
    }
'''
    settings_drawer = settings_drawer[:idx] + style + settings_drawer[idx:]
    java = java[:a] + settings_drawer + java[b:]

    a, b = span(java, "  private void openPlayerOverlay(Channel channel) {")
    overlay = java[a:b]
    if 'mPlayerOverlay.addView(state, stateParams);' not in overlay:
        raise RuntimeError("player state overlay anchor missing")
    overlay = overlay.replace('    mPlayerOverlay.addView(state, stateParams);\n', '', 1)
    chrome_anchor = '    mPlayerChrome.setBackgroundColor(Color.argb(215, 4, 6, 10));\n'
    if chrome_anchor not in overlay:
        raise RuntimeError("player chrome anchor missing")
    overlay = overlay.replace(chrome_anchor, chrome_anchor
        + '    state.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);\n'
        + '    state.setBackgroundColor(Color.TRANSPARENT);\n'
        + '    mPlayerChrome.addView(state, new LinearLayout.LayoutParams(-1, dp(34)));\n', 1)
    texture_anchor = '    mPlayerTexture = new TextureView(this);\n'
    if texture_anchor in overlay:
        overlay = overlay.replace(texture_anchor, texture_anchor + '    mAspectMode = mPrefs.getInt(COBRA_ASPECT_MODE, 0);\n', 1)
    java = java[:a] + overlay + java[b:]

    aspect = r'''  private String cobraAspectLabel(int mode) {
    switch (mode) {
      case 1: return "Crop / Fill";
      case 2: return "16:9";
      case 3: return "4:3";
      case 4: return "Zoom 1.25x";
      case 5: return "Zoom 1.50x";
      case 6: return "Zoom 2.00x";
      default: return "Best Fit";
    }
  }

  private void showCobraAspectPicker() {
    if (mPlayer == null || mPlayerTexture == null) return;
    final String[] labels = {"Best Fit", "Crop / Fill", "16:9", "4:3", "Zoom 1.25x", "Zoom 1.50x", "Zoom 2.00x"};
    int checked = Math.max(0, Math.min(mAspectMode, labels.length - 1));
    new AlertDialog.Builder(this).setTitle("Aspect / Display")
        .setSingleChoiceItems(labels, checked, (dialog, which) -> {
          mAspectMode = which;
          mPrefs.edit().putInt(COBRA_ASPECT_MODE, which).apply();
          applyCobraAspectTransform();
          dialog.dismiss();
          toast("Display mode • " + cobraAspectLabel(which));
        }).setNegativeButton("Cancel", null).show();
  }

  private void cycleAspectMode() { showCobraAspectPicker(); }

  private void applyCobraAspectTransform() {
    if (mPlayerTexture == null) return;
    mPlayerTexture.setScaleX(1f); mPlayerTexture.setScaleY(1f);
    if (mPlayer != null) mPlayer.setVideoScalingMode(C.VIDEO_SCALING_MODE_SCALE_TO_FIT);
    if (mAspectMode == 0 || mPlayer == null) return;
    VideoSize size = mPlayer.getVideoSize();
    int videoWidth = size.width, videoHeight = size.height;
    int viewWidth = mPlayerTexture.getWidth(), viewHeight = mPlayerTexture.getHeight();
    if (videoWidth <= 0 || videoHeight <= 0 || viewWidth <= 0 || viewHeight <= 0) return;
    float pixelRatio = size.pixelWidthHeightRatio > 0f ? size.pixelWidthHeightRatio : 1f;
    float videoAspect = (videoWidth * pixelRatio) / (float) videoHeight;
    float viewAspect = viewWidth / (float) viewHeight;
    if (videoAspect <= 0f || viewAspect <= 0f) return;
    float sx = 1f, sy = 1f;
    if (mAspectMode == 1) {
      float zoom = videoAspect > viewAspect ? videoAspect / viewAspect : viewAspect / videoAspect;
      zoom = Math.max(1f, Math.min(zoom, 4f)); sx = zoom; sy = zoom;
    } else if (mAspectMode == 2) sx = Math.max(0.5f, Math.min((16f / 9f) / videoAspect, 2f));
    else if (mAspectMode == 3) sx = Math.max(0.5f, Math.min((4f / 3f) / videoAspect, 2f));
    else if (mAspectMode == 4) sx = sy = 1.25f;
    else if (mAspectMode == 5) sx = sy = 1.50f;
    else if (mAspectMode == 6) sx = sy = 2.00f;
    mPlayerTexture.setPivotX(viewWidth / 2f); mPlayerTexture.setPivotY(viewHeight / 2f);
    mPlayerTexture.setScaleX(sx); mPlayerTexture.setScaleY(sy);
  }'''
    java = replace_method(java, "  private void cycleAspectMode() {", aspect)
    if java.count("  private void applyCobraAspectTransform() {") > 1:
        first = java.find("  private void applyCobraAspectTransform() {")
        second = java.find("  private void applyCobraAspectTransform() {", first + 1)
        end = method_end(java, second)
        java = java[:second] + java[end:]

    subscription_helpers = r'''  private String cobraSubscriptionCacheKey(LiveSource source) {
    return COBRA_SUBSCRIPTION_PREFIX + (source == null ? "" : source.id);
  }

  private String cobraSubscriptionCachedLabel() {
    LiveSource source = mActiveSource;
    if (source == null) return "SUBSCRIPTION • No active source";
    if (!"xtream".equals(source.type)) return "SUBSCRIPTION • Expiration not provided by this source type";
    return mPrefs.getString(cobraSubscriptionCacheKey(source), "SUBSCRIPTION • Checking account status…");
  }

  private String cobraSubscriptionLabel(JSONObject user) {
    String status = user == null ? "" : user.optString("status", "");
    String expRaw = user == null ? "" : user.optString("exp_date", "");
    String active = user == null ? "" : user.optString("active_cons", "");
    String max = user == null ? "" : user.optString("max_connections", "");
    String expiry = "Not provided"; String remaining = "";
    try {
      long seconds = Long.parseLong(expRaw);
      if (seconds > 0L) {
        long millis = seconds * 1000L;
        expiry = new SimpleDateFormat("MMM d, yyyy", Locale.US).format(new Date(millis));
        long days = Math.max(0L, (millis - System.currentTimeMillis() + 86399999L) / 86400000L);
        remaining = "\nDays remaining • " + days;
      }
    } catch (Exception ignored) {}
    StringBuilder out = new StringBuilder("SUBSCRIPTION");
    if (!status.isEmpty()) out.append(" • ").append(status.toUpperCase(Locale.US));
    out.append("\nExpires • ").append(expiry).append(remaining);
    if (!active.isEmpty() || !max.isEmpty()) out.append("\nConnections • ")
        .append(active.isEmpty() ? "?" : active).append(" / ").append(max.isEmpty() ? "?" : max);
    return out.toString();
  }

  private void refreshCobraSubscriptionStatus() {
    final LiveSource source = mActiveSource;
    if (source == null || !"xtream".equals(source.type)) return;
    submitCobraIo(() -> {
      try {
        String url = source.server + "/player_api.php?username=" + enc(source.username) + "&password=" + enc(source.password);
        JSONObject root = new JSONObject(httpGet(url));
        JSONObject user = root.optJSONObject("user_info");
        final String label = user == null ? "SUBSCRIPTION • Provider did not return account status" : cobraSubscriptionLabel(user);
        mPrefs.edit().putString(cobraSubscriptionCacheKey(source), label).apply();
        publishCobraUi(() -> {
          View view = mStage == null ? null : mStage.findViewWithTag("cobra_subscription_status");
          if (view instanceof TextView) ((TextView) view).setText(label);
        });
      } catch (Exception error) {
        final String label = "SUBSCRIPTION • Status unavailable";
        publishCobraUi(() -> {
          View view = mStage == null ? null : mStage.findViewWithTag("cobra_subscription_status");
          if (view instanceof TextView) ((TextView) view).setText(label);
        });
      }
    });
  }

'''
    a, b = span(java, "  private void showSettings() {")
    settings = java[a:b]
    settings = re.sub(
        r'\s*list\.addView\(guideView, new LinearLayout\.LayoutParams\(\s*LinearLayout\.LayoutParams\.MATCH_PARENT, dp\(56\)\)\);\n',
        "\n", settings, count=1)
    theme_anchor = "    TextView themeInfo = text("
    if theme_anchor not in settings:
        raise RuntimeError("Settings theme info anchor missing")
    settings = settings.replace(theme_anchor,
        '    TextView subscriptionStatus = text(cobraSubscriptionCachedLabel(),\n'
        '        cobraThemeColor("accent_soft", mTheme.accentSoft), 13,\n'
        '        Gravity.LEFT | Gravity.CENTER_VERTICAL);\n'
        '    subscriptionStatus.setTag("cobra_subscription_status");\n\n' + theme_anchor, 1)
    add_theme = "    list.addView(themeInfo, new LinearLayout.LayoutParams("
    if add_theme not in settings:
        raise RuntimeError("Settings themeInfo list anchor missing")
    settings = settings.replace(add_theme,
        '    list.addView(subscriptionStatus, new LinearLayout.LayoutParams(\n'
        '        LinearLayout.LayoutParams.MATCH_PARENT, dp(86)));\n' + add_theme, 1)
    close = settings.rfind("}")
    settings = settings[:close] + "    refreshCobraSubscriptionStatus();\n  " + settings[close:]
    java = java[:a] + settings + java[b:]

    helper_anchor = "  private void openCobraUiPackagePicker() {"
    if helper_anchor not in java:
        raise RuntimeError("frontend helper anchor missing")
    java = java.replace(helper_anchor, subscription_helpers + helper_anchor, 1)
    return java


def verify(java: str) -> None:
    required = (
        'setContentDescription("Collapse Cobra drawer")',
        'VIEW MODE  •  " + cobraGuideViewLabel()',
        'Button power = action("⏻  POWER")',
        'setTag("cobra_power_menu")',
        'finishAndRemoveTask()',
        'showGuideCards()',
        'COBRA • COMPACT', 'COBRA • CARDS', 'COBRA • FOCUS',
        'if (!"root".equals(mCobraInternalScreen))', 'moveTaskToBack(true);',
        'fit.setText("Aspect / Display")', '"Best Fit", "Crop / Fill", "16:9", "4:3"',
        'COBRA_ASPECT_MODE', 'mPlayerChrome.addView(state',
        'drawer.setBackground(surface(Color.rgb(9, 15, 22)',
        'COBRA_SUBSCRIPTION_PREFIX', 'player_api.php?username=', 'Expires • ',
        'setTag("cobra_subscription_status")',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Post-2103148 polish contract missing: " + token)
    if java.count("  private void showGuideCards() {") != 1:
        raise RuntimeError("Cards renderer duplicated")
    if java.count("  private void applyCobraAspectTransform() {") != 1:
        raise RuntimeError("Aspect transform duplicated")
    start = java.find("  private void showSettings() {")
    end = java.find("  private void editCustomEpg()", start)
    if start >= 0 and end > start and 'list.addView(guideView, new LinearLayout.LayoutParams(' in java[start:end]:
        raise RuntimeError("Guide View control still visible in Settings")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: post-2103148 Cobra drawer/back/view/player/subscription polish applied")


if __name__ == "__main__":
    main()
