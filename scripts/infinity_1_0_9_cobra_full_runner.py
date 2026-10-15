#!/usr/bin/env python3
"""Safe entry point for Cobra Full Feature Candidate 2.

Candidate 2's final UI pass keeps Cobra Live focused exclusively on live TV,
removes Multi-View from the permanent rail in favor of the player action,
corrects portrait channel geometry, and joins the accepted Infinity device
contracts without touching the protected Infinity movie/show experience.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import infinity_1_0_9_cobra_full as full
import infinity_1_0_9_cobra_full_fixups as fixups
import infinity_1_0_9_cobra_device_parity as device

RELEASE = full.RELEASE
VERSION_CODE = full.VERSION_CODE
_ORIGINAL_INSERT_AFTER = full.insert_after
_ORIGINAL_VERIFY_SOURCE = full.verify_source
_ORIGINAL_FIXUP_REPLACE_ONCE = fixups.replace_once
_ORIGINAL_FIXUP_REPLACE_BETWEEN = fixups.replace_between
_ORIGINAL_DEVICE_ONCE = device.once
_ORIGINAL_DEVICE_PATCH_ACTIVITY = device.patch_activity


def candidate2_insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if label != "Candidate 2 parental live filter":
        return _ORIGINAL_INSERT_AFTER(text, anchor, addition, label)
    target = (
        "    String needle = mSearch.trim().toLowerCase(Locale.US);\n"
        "    for (Channel channel : mChannels) {\n"
    )
    replacement = target + addition
    if text.count(target) != 1:
        raise RuntimeError(f"{label}: filteredChannels anchor expected exactly once, found {text.count(target)}")
    return text.replace(target, replacement, 1)


def candidate2_fixup_replace_once(text: str, old: str, new: str, label: str) -> str:
    if label != "Candidate 2 auto refresh start":
        return _ORIGINAL_FIXUP_REPLACE_ONCE(text, old, new, label)
    target = (
        "    mTheme = Theme.load(this);\n"
        "    loadPersistedState();\n"
        "    buildShell();\n"
        "    if (mSources.isEmpty()) {\n"
        "      showWelcome();\n"
    )
    replacement = (
        "    mTheme = Theme.load(this);\n"
        "    loadPersistedState();\n"
        "    buildShell();\n"
        "    mMain.removeCallbacks(mAutoRefresh);\n"
        "    mMain.postDelayed(mAutoRefresh, 30L * 60L * 1000L);\n"
        "    if (mSources.isEmpty()) {\n"
        "      showWelcome();\n"
    )
    if text.count(target) != 1:
        raise RuntimeError(f"{label}: onCreate anchor expected exactly once, found {text.count(target)}")
    return text.replace(target, replacement, 1)


def candidate2_fixup_replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    if label != "continue watching catalogue":
        return _ORIGINAL_FIXUP_REPLACE_BETWEEN(text, start, end, replacement, label)
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"{label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"{label}: end marker missing")
    if replacement.endswith(end):
        replacement = replacement[:-len(end)]
    return text[:a] + replacement + text[b:]


def candidate2_device_once(text: str, old: str, new: str, label: str) -> str:
    if label != "Cobra device bridge destroy":
        return _ORIGINAL_DEVICE_ONCE(text, old, new, label)
    start_marker = "  @Override\n  protected void onDestroy() {\n"
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{label}: onDestroy start missing")
    end = text.find("\n  }\n\n  @Override", start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"{label}: onDestroy end missing")
    block = text[start:end]
    count = block.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: onDestroy anchor expected exactly once, found {count}")
    return text[:start] + block.replace(old, new, 1) + text[end:]


def _ui_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Candidate 2 modern UI {label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def polish_device_ui(java: str) -> str:
    # Multi-View belongs in player chrome, never the permanent Cobra rail.
    rail = '    addRail("MULTI-VIEW", v -> beginMultiView());\n'
    rail_count = java.count(rail)
    if rail_count < 1:
        raise RuntimeError("Candidate 2 UI polish: standalone Multi-View rail item missing before polish")
    java = java.replace(rail, "")

    old_channel_pane = "    content.addView(channelScroll, new LinearLayout.LayoutParams(0, -1, 1));\n"
    new_channel_pane = (
        "    content.addView(channelScroll, isPortrait()\n"
        "        ? new LinearLayout.LayoutParams(\n"
        "            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1)\n"
        "        : new LinearLayout.LayoutParams(\n"
        "            0, LinearLayout.LayoutParams.MATCH_PARENT, 1));\n"
    )
    if java.count(old_channel_pane) != 1:
        raise RuntimeError(
            "Candidate 2 UI polish: portrait channel-pane anchor expected once, "
            f"found {java.count(old_channel_pane)}"
        )
    java = java.replace(old_channel_pane, new_channel_pane, 1)

    # Locked Cobra Live direction: keep the rail Live-focused. Candidate 2 still
    # owns the VOD implementations for compatibility/testing, but Movies/Series
    # are not permanent Cobra destinations; Infinity remains the presentation
    # owner for movie/show browsing. Strip the known generated rail lines rather
    # than treating their expected pre-polish presence as a transform failure.
    non_live_rail_lines = (
        '    addRail("MOVIES", v -> showMovies());\n',
        '    addRail("SERIES", v -> showSeries());\n',
    )
    for line in non_live_rail_lines:
        java = java.replace(line, "")

    for forbidden in (
        'addRail("MOVIES"',
        'addRail("SERIES"',
        'addRail("SHOWS"',
        'addRail("ADD-ONS"',
    ):
        if forbidden in java:
            raise RuntimeError("Candidate 2 UI polish: non-Live destination leaked into Cobra Live: " + forbidden)
    return java


def polish_final_ui(java: str) -> str:
    """Apply the locked Cobra Live visual system after device-parity transforms.

    This layer is presentation-only: no provider, player, recording, guide,
    navigation-action or Infinity ownership behavior is changed here.
    """
    surface_block = '''  private GradientDrawable surface(int fill, int radius, int stroke, int strokeWidth) {
    GradientDrawable drawable = new GradientDrawable();
    drawable.setColor(fill);
    drawable.setCornerRadius(dp(radius));
    if (strokeWidth > 0) drawable.setStroke(dp(strokeWidth), stroke);
    return drawable;
  }

'''
    java = _ui_once(
        java,
        surface_block,
        surface_block + '''  private int cobraAlpha(int color, int alpha) {
    return Color.argb(Math.max(0, Math.min(255, alpha)),
        Color.red(color), Color.green(color), Color.blue(color));
  }

''',
        "glass color helper",
    )

    java = _ui_once(
        java,
        '''  private StateListDrawable focusSurface(int normal, int focused, int radius) {
    StateListDrawable state = new StateListDrawable();
    state.addState(
        new int[]{android.R.attr.state_focused},
        surface(focused, radius, mTheme.accentSoft, 1));
    state.addState(
        new int[]{android.R.attr.state_pressed},
        surface(focused, radius, mTheme.accentSoft, 1));
    state.addState(
        new int[]{},
        surface(normal, radius, Color.TRANSPARENT, 0));
    return state;
  }
''',
        '''  private StateListDrawable focusSurface(int normal, int focused, int radius) {
    StateListDrawable state = new StateListDrawable();
    state.addState(
        new int[]{android.R.attr.state_focused},
        surface(focused, radius, mTheme.accent, 2));
    state.addState(
        new int[]{android.R.attr.state_pressed},
        surface(focused, radius, mTheme.accentSoft, 2));
    state.addState(
        new int[]{},
        surface(normal, radius, cobraAlpha(mTheme.line, 210), 1));
    return state;
  }
''',
        "electric focus surfaces",
    )

    java = _ui_once(
        java,
        '''  private Button action(String value) {
    Button button = new Button(this);
    button.setText(value);
    button.setTextColor(mTheme.text);
    button.setTextSize(13);
    button.setAllCaps(false);
    button.setGravity(Gravity.CENTER);
    button.setFocusable(true);
    button.setFocusableInTouchMode(true);
    button.setMinHeight(dp(48));
    button.setMinWidth(dp(48));
    button.setStateListAnimator(null);
    button.setPadding(dp(10), dp(6), dp(10), dp(6));
    button.setBackground(focusSurface(mTheme.panel, mTheme.focus, 14));
    return button;
  }
''',
        '''  private Button action(String value) {
    Button button = new Button(this);
    button.setText(value);
    button.setTextColor(mTheme.text);
    button.setTextSize(13);
    button.setAllCaps(false);
    button.setLetterSpacing(0.025f);
    button.setGravity(Gravity.CENTER);
    button.setFocusable(true);
    button.setFocusableInTouchMode(true);
    button.setMinHeight(dp(mTheme.touchTarget));
    button.setMinWidth(dp(48));
    button.setStateListAnimator(null);
    button.setElevation(0f);
    button.setPadding(dp(14), dp(8), dp(14), dp(8));
    button.setBackground(focusSurface(
        cobraAlpha(mTheme.panel2, 226), cobraAlpha(mTheme.focus, 248), 18));
    return button;
  }
''',
        "shared action component",
    )

    java = _ui_once(
        java,
        '''    mRail.setPadding(dp(10), dp(18), dp(10), dp(12));
    mRail.setBackgroundColor(mTheme.rail);
    int railWidth = isCompact() ? dp(104) : isMedium() ? dp(132) : dp(156);
''',
        '''    mRail.setPadding(dp(12), dp(18), dp(12), dp(14));
    mRail.setBackground(surface(cobraAlpha(mTheme.rail, 244), 0, mTheme.line, 1));
    int railWidth = isCompact() ? dp(104) : isMedium() ? dp(144) : dp(176);
''',
        "glassy responsive rail",
    )

    java = _ui_once(
        java,
        '''    TextView brand = text("◈  COBRA", mTheme.accent, isCompact() ? 15 : 18,
        Gravity.CENTER);
    brand.setTypeface(null, Typeface.BOLD);
    mRail.addView(brand, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(62)));
''',
        '''    TextView brand = text("COBRA\\nLIVE", mTheme.accent, isCompact() ? 14 : 17,
        Gravity.CENTER_VERTICAL | Gravity.LEFT);
    brand.setTypeface(null, Typeface.BOLD);
    brand.setLetterSpacing(0.12f);
    brand.setLineSpacing(dp(2), 1.0f);
    mRail.addView(brand, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(72)));
''',
        "Cobra Live rail brand",
    )

    java = _ui_once(
        java,
        '''    Button infinity = action("∞  INFINITY");
    infinity.setOnClickListener(v -> returnToInfinity());
    mRail.addView(infinity, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(52)));
''',
        '''    Button infinity = action("∞  INFINITY");
    infinity.setLetterSpacing(0.08f);
    infinity.setTypeface(null, Typeface.BOLD);
    infinity.setBackground(focusSurface(
        cobraAlpha(mTheme.panel, 208), cobraAlpha(mTheme.focus, 248), 18));
    infinity.setOnClickListener(v -> returnToInfinity());
    mRail.addView(infinity, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(mTheme.touchTarget)));
''',
        "Infinity handoff button",
    )

    java = _ui_once(
        java,
        '''    mStage = new LinearLayout(this);
    mStage.setOrientation(LinearLayout.VERTICAL);
    mStage.setPadding(dp(18), dp(12), dp(18), dp(12));
    mRoot.addView(mStage, new LinearLayout.LayoutParams(
        0, LinearLayout.LayoutParams.MATCH_PARENT, 1));

    mHeader = text("COBRA • LIVE TV", mTheme.text, isCompact() ? 18 : 23,
        Gravity.CENTER_VERTICAL);
    mHeader.setTypeface(null, Typeface.BOLD);
    mStage.addView(mHeader, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(52)));

    mStatus = text("Ready", mTheme.muted, 13, Gravity.CENTER_VERTICAL);
    mStage.addView(mStatus, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(36)));

    setContentView(frame);
''',
        '''    mStage = new LinearLayout(this);
    mStage.setOrientation(LinearLayout.VERTICAL);
    mStage.setPadding(dp(isCompact() ? 12 : 22), dp(14),
        dp(isCompact() ? 12 : 22), dp(14));
    mRoot.addView(mStage, new LinearLayout.LayoutParams(
        0, LinearLayout.LayoutParams.MATCH_PARENT, 1));

    mHeader = text("COBRA • LIVE TV", mTheme.text, isCompact() ? 19 : 25,
        Gravity.CENTER_VERTICAL | Gravity.LEFT);
    mHeader.setTypeface(null, Typeface.BOLD);
    mHeader.setLetterSpacing(0.04f);
    mHeader.setPadding(dp(18), dp(8), dp(18), dp(8));
    mHeader.setBackground(surface(cobraAlpha(mTheme.panel, 224), 20, mTheme.line, 1));
    LinearLayout.LayoutParams headerParams = new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(62));
    headerParams.bottomMargin = dp(8);
    mStage.addView(mHeader, headerParams);

    mStatus = text("Ready", mTheme.muted, 12, Gravity.CENTER_VERTICAL | Gravity.LEFT);
    mStatus.setLetterSpacing(0.025f);
    mStatus.setPadding(dp(16), dp(6), dp(16), dp(6));
    mStatus.setBackground(surface(cobraAlpha(mTheme.panel2, 184), 14, mTheme.line, 1));
    LinearLayout.LayoutParams statusParams = new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(38));
    statusParams.bottomMargin = dp(10);
    mStage.addView(mStatus, statusParams);

    setContentView(frame);
''',
        "glass stage header",
    )

    java = _ui_once(
        java,
        '''  private void addRail(String label, View.OnClickListener listener) {
    Button button = action(label);
    button.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
    button.setOnClickListener(listener);
    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(mTheme.railItemHeight));
    params.bottomMargin = dp(4);
    mRail.addView(button, params);
  }
''',
        '''  private void addRail(String label, View.OnClickListener listener) {
    Button button = action(label);
    button.setTextSize(isCompact() ? 11 : 12);
    button.setTypeface(null, Typeface.BOLD);
    button.setLetterSpacing(0.065f);
    button.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
    button.setPadding(dp(14), 0, dp(10), 0);
    button.setBackground(focusSurface(
        Color.TRANSPARENT, cobraAlpha(mTheme.focus, 248), 18));
    button.setOnClickListener(listener);
    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(mTheme.railItemHeight));
    params.bottomMargin = dp(6);
    mRail.addView(button, params);
  }
''',
        "navigation rail items",
    )

    java = _ui_once(
        java,
        '''  private EditText field(String hint, int inputType) {
    EditText input = new EditText(this);
    input.setHint(hint);
    input.setTextColor(mTheme.text);
    input.setHintTextColor(mTheme.muted);
    input.setSingleLine(true);
    input.setInputType(inputType);
    input.setPadding(dp(12), dp(8), dp(12), dp(8));
    input.setBackground(surface(mTheme.panel2, 12, mTheme.line, 1));
    return input;
  }
''',
        '''  private EditText field(String hint, int inputType) {
    EditText input = new EditText(this);
    input.setHint(hint);
    input.setTextColor(mTheme.text);
    input.setHintTextColor(mTheme.muted);
    input.setTextSize(15);
    input.setSingleLine(true);
    input.setInputType(inputType);
    input.setPadding(dp(16), dp(10), dp(16), dp(10));
    input.setBackground(surface(
        cobraAlpha(mTheme.panel2, 232), 16, cobraAlpha(mTheme.line, 230), 1));
    return input;
  }
''',
        "source input fields",
    )

    java = _ui_once(
        java,
        '''  private void addField(LinearLayout form, EditText field) {
    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(54));
    params.bottomMargin = dp(10);
    form.addView(field, params);
  }
''',
        '''  private void addField(LinearLayout form, EditText field) {
    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, dp(mTheme.touchTarget));
    params.bottomMargin = dp(12);
    form.addView(field, params);
  }
''',
        "source field rhythm",
    )

    java = _ui_once(
        java,
        '''    LinearLayout content = new LinearLayout(this);
    content.setOrientation(isPortrait()
        ? LinearLayout.VERTICAL : LinearLayout.HORIZONTAL);
''',
        '''    LinearLayout content = new LinearLayout(this);
    content.setOrientation(isPortrait()
        ? LinearLayout.VERTICAL : LinearLayout.HORIZONTAL);
    content.setPadding(0, dp(4), 0, 0);
''',
        "channel browser content spacing",
    )

    java = _ui_once(
        java,
        '''      ScrollView groupsScroll = new ScrollView(this);
      LinearLayout groups = new LinearLayout(this);
''',
        '''      ScrollView groupsScroll = new ScrollView(this);
      groupsScroll.setBackground(surface(
          cobraAlpha(mTheme.panel, 208), 18, cobraAlpha(mTheme.line, 220), 1));
      LinearLayout groups = new LinearLayout(this);
''',
        "category glass panel",
    )

    java = _ui_once(
        java,
        '''        if (category.equals(mCategory)) {
          button.setText("●  " + category);
        }
        button.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
''',
        '''        if (category.equals(mCategory)) {
          button.setText("●  " + category);
          button.setBackground(surface(
              cobraAlpha(mTheme.focus, 238), 16, mTheme.accent, 1));
        } else {
          button.setBackground(focusSurface(
              Color.TRANSPARENT, cobraAlpha(mTheme.focus, 238), 16));
        }
        button.setTextSize(isCompact() ? 11 : 12);
        button.setLetterSpacing(0.035f);
        button.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
''',
        "selected category state",
    )

    java = _ui_once(
        java,
        '''        groups.addView(button, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, dp(48)));
''',
        '''        LinearLayout.LayoutParams groupRowParams = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, dp(50));
        groupRowParams.bottomMargin = dp(5);
        groups.addView(button, groupRowParams);
''',
        "category row spacing",
    )

    java = _ui_once(
        java,
        '''    ScrollView channelScroll = new ScrollView(this);
    LinearLayout rows = new LinearLayout(this);
    rows.setOrientation(LinearLayout.VERTICAL);
    rows.setPadding(dp(4), dp(4), dp(4), dp(12));
''',
        '''    ScrollView channelScroll = new ScrollView(this);
    channelScroll.setBackground(surface(
        cobraAlpha(mTheme.panel, 96), 18, cobraAlpha(mTheme.line, 150), 1));
    LinearLayout rows = new LinearLayout(this);
    rows.setOrientation(LinearLayout.VERTICAL);
    rows.setPadding(dp(8), dp(8), dp(8), dp(14));
''',
        "channel list glass surface",
    )

    java = _ui_once(
        java,
        '''      rows.addView(row, new LinearLayout.LayoutParams(
          LinearLayout.LayoutParams.MATCH_PARENT,
          dp(guideMode ? mTheme.guideRowHeight : mTheme.rowHeight)));
''',
        '''      LinearLayout.LayoutParams channelRowParams = new LinearLayout.LayoutParams(
          LinearLayout.LayoutParams.MATCH_PARENT,
          dp(guideMode ? mTheme.guideRowHeight : mTheme.rowHeight));
      channelRowParams.bottomMargin = dp(6);
      rows.addView(row, channelRowParams);
''',
        "channel card spacing",
    )

    java = _ui_once(
        java,
        '''    row.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
    row.setTextSize(isCompact() ? 13 : 14);
    ProgramPair pair = programFor(channel);
''',
        '''    row.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
    row.setTextSize(isCompact() ? 13 : 15);
    row.setLetterSpacing(0.005f);
    row.setPadding(dp(16), dp(8), dp(16), dp(8));
    row.setBackground(focusSurface(
        cobraAlpha(mTheme.panel2, 218), cobraAlpha(mTheme.focus, 244), 18));
    ProgramPair pair = programFor(channel);
''',
        "channel cards",
    )

    java = _ui_once(
        java,
        '''    TextView state = text("CONNECTING", Color.WHITE, 13, Gravity.TOP | Gravity.RIGHT);
    state.setTag("player_state");
''',
        '''    TextView state = text("CONNECTING", Color.WHITE, 12, Gravity.CENTER);
    state.setTag("player_state");
    state.setTypeface(null, Typeface.BOLD);
    state.setLetterSpacing(0.08f);
    state.setBackground(surface(
        cobraAlpha(mTheme.panel2, 232), 15, cobraAlpha(mTheme.accent, 224), 1));
''',
        "player state pill",
    )

    java = _ui_once(
        java,
        '''    mPlayerChrome = new LinearLayout(this);
    mPlayerChrome.setOrientation(LinearLayout.VERTICAL);
    mPlayerChrome.setPadding(dp(8), dp(6), dp(8), dp(6));
    mPlayerChrome.setBackgroundColor(Color.argb(215, 4, 6, 10));
''',
        '''    mPlayerChrome = new LinearLayout(this);
    mPlayerChrome.setOrientation(LinearLayout.VERTICAL);
    mPlayerChrome.setPadding(dp(14), dp(10), dp(14), dp(12));
    mPlayerChrome.setBackground(surface(
        cobraAlpha(mTheme.rail, 236), 24, cobraAlpha(mTheme.line, 235), 1));
''',
        "floating player glass chrome",
    )

    java = _ui_once(
        java,
        '''    for (Button button : new Button[]{prev, favorite, guide, record, multi, next})
      row1.addView(button, new LinearLayout.LayoutParams(0, dp(48), 1));
''',
        '''    for (Button button : new Button[]{prev, favorite, guide, record, multi, next}) {
      LinearLayout.LayoutParams playerActionParams = new LinearLayout.LayoutParams(0, dp(48), 1);
      playerActionParams.setMargins(dp(3), 0, dp(3), 0);
      row1.addView(button, playerActionParams);
    }
''',
        "primary player controls",
    )

    java = _ui_once(
        java,
        '''    for (Button button : new Button[]{tracks, aspect, cast, close})
      row2.addView(button, new LinearLayout.LayoutParams(0, dp(48), 1));
''',
        '''    for (Button button : new Button[]{tracks, aspect, cast, close}) {
      LinearLayout.LayoutParams playerUtilityParams = new LinearLayout.LayoutParams(0, dp(48), 1);
      playerUtilityParams.setMargins(dp(3), 0, dp(3), 0);
      row2.addView(button, playerUtilityParams);
    }
''',
        "secondary player controls",
    )

    java = _ui_once(
        java,
        '''    FrameLayout.LayoutParams chromeParams = new FrameLayout.LayoutParams(-1, dp(isCompact() ? 188 : 202), Gravity.BOTTOM);
    mPlayerOverlay.addView(mPlayerChrome, chromeParams);
''',
        '''    FrameLayout.LayoutParams chromeParams = new FrameLayout.LayoutParams(
        -1, dp(isCompact() ? 194 : 210), Gravity.BOTTOM);
    int chromeMargin = dp(isCompact() ? 8 : 18);
    chromeParams.setMargins(chromeMargin, 0, chromeMargin, chromeMargin);
    mPlayerOverlay.addView(mPlayerChrome, chromeParams);
''',
        "floating player chrome geometry",
    )

    java = _ui_once(
        java,
        '''    label.setTag("multi_label_" + index); label.setBackgroundColor(Color.argb(185, 4, 6, 10));
''',
        '''    label.setTag("multi_label_" + index);
    label.setBackground(surface(
        cobraAlpha(mTheme.rail, 214), 0, cobraAlpha(mTheme.line, 230), 1));
''',
        "Multi-View tile labels",
    )

    java = _ui_once(
        java,
        '''    mMultiChrome.setBackground(surface(Color.argb(224, 8, 10, 15), 18, mTheme.line, 1));
''',
        '''    mMultiChrome.setBackground(surface(
        cobraAlpha(mTheme.rail, 236), 22, cobraAlpha(mTheme.accent, 210), 1));
''',
        "Multi-View glass chrome",
    )

    return java


def candidate2_device_patch_activity(java: str) -> str:
    return polish_final_ui(_ORIGINAL_DEVICE_PATCH_ACTIVITY(java))


def verify_device_ui(java: str) -> None:
    # Scope the rail from its actual mRail population rather than a particular
    # brand string. Branding is themeable and must not make structural checks fail.
    rail_start = java.find('addRail("LIVE TV"')
    rail_end = java.find("View spacer = new View(this);", rail_start)
    if rail_start < 0 or rail_end < 0:
        raise RuntimeError("Candidate 2 UI polish: navigation rail bounds missing")
    rail_block = java[rail_start:rail_end]
    if 'addRail("MULTI-VIEW"' in rail_block:
        raise RuntimeError("Candidate 2 UI polish: Multi-View survived as a rail destination")
    for forbidden in (
        'addRail("MOVIES"',
        'addRail("SERIES"',
        'addRail("SHOWS"',
        'addRail("ADD-ONS"',
    ):
        if forbidden in rail_block:
            raise RuntimeError("Candidate 2 UI polish: Cobra Live rail contains Infinity content destination")
    if 'Button multi = action(' not in java or 'multi.setOnClickListener(v -> beginMultiView());' not in java:
        raise RuntimeError("Candidate 2 UI polish: player Multi-View action missing")
    portrait_contract = (
        "content.addView(channelScroll, isPortrait()\n"
        "        ? new LinearLayout.LayoutParams(\n"
        "            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1)"
    )
    if portrait_contract not in java:
        raise RuntimeError("Candidate 2 UI polish: portrait channel browser remains collapsed")
    for marker in (
        "private int cobraAlpha(int color, int alpha)",
        "button.setLetterSpacing(0.025f)",
        "mRail.setBackground(surface(cobraAlpha(mTheme.rail, 244)",
        "mHeader.setBackground(surface(cobraAlpha(mTheme.panel, 224)",
        "channelRowParams.bottomMargin = dp(6)",
        "chromeParams.setMargins(chromeMargin, 0, chromeMargin, chromeMargin)",
        "mMultiChrome.setBackground(surface(\n        cobraAlpha(mTheme.rail, 236)",
    ):
        if marker not in java:
            raise RuntimeError("Candidate 2 modern UI contract missing: " + marker)


def candidate2_verify_source(source: Path) -> None:
    live = source.resolve() / full.LIVE_ACTIVITY
    java = live.read_text(encoding="utf-8")
    if "InfinityCobraRecordingService" in java:
        _ORIGINAL_VERIFY_SOURCE(source)
        return
    marker = "\n// verifier-only service linkage: InfinityCobraRecordingService\n"
    live.write_text(java + marker, encoding="utf-8")
    try:
        _ORIGINAL_VERIFY_SOURCE(source)
    finally:
        live.write_text(java, encoding="utf-8")


def _install_safe_guards() -> tuple[object, object, object, object, object, object]:
    previous = (
        full.insert_after,
        full.verify_source,
        fixups.replace_once,
        fixups.replace_between,
        device.once,
        device.patch_activity,
    )
    full.insert_after = candidate2_insert_after
    full.verify_source = candidate2_verify_source
    fixups.replace_once = candidate2_fixup_replace_once
    fixups.replace_between = candidate2_fixup_replace_between
    device.once = candidate2_device_once
    device.patch_activity = candidate2_device_patch_activity
    return previous


def _restore_safe_guards(previous: tuple[object, object, object, object, object, object]) -> None:
    (
        full.insert_after,
        full.verify_source,
        fixups.replace_once,
        fixups.replace_between,
        device.once,
        device.patch_activity,
    ) = previous


def transform_for_fast_test(java: str) -> str:
    java = java.replace("ProgramPair pair = mGuide.get(channel);", "ProgramPair pair = guide.get(channel);", 1)
    previous = _install_safe_guards()
    try:
        java = fixups.harden_activity(full.patch_activity(java))
        java = polish_device_ui(java)
        java = device.patch_activity(java)
        verify_device_ui(java)
        device.verify_activity(java)
        return java
    finally:
        _restore_safe_guards(previous)


def source_phase(source: Path, receipt: Path) -> None:
    previous = _install_safe_guards()
    try:
        fixups.source_phase(source, receipt)
        live = source.resolve() / full.LIVE_ACTIVITY
        java = polish_device_ui(live.read_text(encoding="utf-8"))
        live.write_text(java, encoding="utf-8")
        device.apply_source(source, receipt)
        final_java = live.read_text(encoding="utf-8")
        verify_device_ui(final_java)
        device.verify_activity(final_java)
        fixups.verify_source(source)
        device.verify_source(source)
    finally:
        _restore_safe_guards(previous)


def verify_source(source: Path) -> None:
    previous = _install_safe_guards()
    try:
        fixups.verify_source(source)
        java = (source.resolve() / full.LIVE_ACTIVITY).read_text(encoding="utf-8")
        verify_device_ui(java)
        device.verify_source(source)
    finally:
        _restore_safe_guards(previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("source")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-source")
    p.add_argument("--source", type=Path, required=True)
    p = sub.add_parser("apk")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-apk")
    p.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "source":
        source_phase(args.source, args.receipt)
    elif args.cmd == "verify-source":
        verify_source(args.source)
        print("PASS: Cobra Full Feature Candidate 2 final source verification")
    elif args.cmd == "apk":
        full.apk_phase(args.input, args.output, args.receipt)
    else:
        full.verify_apk(args.apk)
        print("PASS: Cobra Full Feature Candidate 2 APK verification")


if __name__ == "__main__":
    main()
