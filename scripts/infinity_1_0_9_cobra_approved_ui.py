#!/usr/bin/env python3
"""Approved Cobra Live UI contract.

Presentation/interaction-only transform applied after Candidate 2 device parity.
Keeps provider, EPG, DVR, playback and Infinity ownership contracts intact.
"""
from __future__ import annotations


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"approved Cobra UI {label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch(java: str) -> str:
    # Touch is action-first on phones. D-pad focus remains available, but a touch
    # must not be consumed merely to focus a control before its click fires.
    java = once(
        java,
        "    button.setFocusableInTouchMode(true);\n",
        "    button.setFocusableInTouchMode(false);\n",
        "single-tap action controls",
    )

    # The old permanent rail becomes an on-demand navigation drawer. Hiding the
    # rail removes it from LinearLayout measurement, returning its full width to
    # the channel browser on portrait/fold cover displays.
    java = once(
        java,
        "    mRoot.addView(mRail, new LinearLayout.LayoutParams(\n        railWidth, LinearLayout.LayoutParams.MATCH_PARENT));\n",
        "    mRoot.addView(mRail, new LinearLayout.LayoutParams(\n        railWidth, LinearLayout.LayoutParams.MATCH_PARENT));\n"
        "    mRail.setVisibility(View.GONE);\n",
        "collapsed navigation drawer",
    )
    java = once(
        java,
        "    mHeader.setTypeface(null, Typeface.BOLD);\n    mHeader.setLetterSpacing(0.04f);\n",
        "    mHeader.setTypeface(null, Typeface.BOLD);\n"
        "    mHeader.setLetterSpacing(0.04f);\n"
        "    mHeader.setText(\"☰  COBRA • LIVE TV\");\n"
        "    mHeader.setOnClickListener(v -> toggleCobraDrawer());\n",
        "drawer hamburger header",
    )
    java = once(
        java,
        "  private void addRail(String label, View.OnClickListener listener) {\n",
        "  private void toggleCobraDrawer() {\n"
        "    if (mRail == null) return;\n"
        "    boolean opening = mRail.getVisibility() != View.VISIBLE;\n"
        "    mRail.setVisibility(opening ? View.VISIBLE : View.GONE);\n"
        "    if (opening) mRail.bringToFront();\n"
        "  }\n\n"
        "  private void closeCobraDrawer() {\n"
        "    if (mRail != null) mRail.setVisibility(View.GONE);\n"
        "  }\n\n"
        "  private void addRail(String label, View.OnClickListener listener) {\n",
        "drawer helpers",
    )
    java = once(
        java,
        "    button.setOnClickListener(listener);\n    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(mTheme.railItemHeight));\n",
        "    button.setOnClickListener(v -> { closeCobraDrawer(); listener.onClick(v); });\n"
        "    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(\n"
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(mTheme.railItemHeight));\n",
        "drawer closes after navigation",
    )
    java = once(
        java,
        "    mHeader.setText(title);\n  }\n",
        "    mHeader.setText(\"☰  \" + title);\n  }\n",
        "persistent drawer affordance",
    )

    # Give portrait browsing the screen: categories stay compact while the
    # channel list receives the remaining height and full stage width.
    java = once(
        java,
        "              LinearLayout.LayoutParams.MATCH_PARENT, dp(116))\n",
        "              LinearLayout.LayoutParams.MATCH_PARENT, dp(82))\n",
        "portrait category strip height",
    )

    # Player: keep one clean primary control row. Secondary playback controls
    # move to an explicit settings drawer rather than permanently covering video.
    java = once(
        java,
        "    Button guide = action(\"GUIDE\");\n    Button record = action(\"● REC\");\n    Button multi = action(\"▦\");\n    Button next = action(\"▶\");\n",
        "    Button guide = action(\"GUIDE\");\n"
        "    Button record = action(\"● REC\");\n"
        "    Button multi = action(\"▦\");\n"
        "    Button next = action(\"▶\");\n"
        "    Button settings = action(\"⚙\");\n",
        "player settings action",
    )
    java = once(
        java,
        "    next.setOnClickListener(v -> stepChannel(1));\n    for (Button button : new Button[]{prev, favorite, guide, record, multi, next}) {\n",
        "    next.setOnClickListener(v -> stepChannel(1));\n"
        "    settings.setOnClickListener(v -> showPlayerSettingsDrawer());\n"
        "    for (Button button : new Button[]{prev, favorite, record, multi, next, settings}) {\n",
        "minimal player primary row",
    )
    java = once(
        java,
        "    mPlayerChrome.addView(row2, new LinearLayout.LayoutParams(-1, dp(52)));\n",
        "    row2.setVisibility(View.GONE);\n"
        "    mPlayerChrome.addView(row2, new LinearLayout.LayoutParams(-1, 0));\n",
        "hide legacy secondary row",
    )
    java = once(
        java,
        "  private void startSinglePlayer(String url) {\n",
        '''  private void showPlayerSettingsDrawer() {
    if (mPlayerOverlay == null) return;
    View old = mPlayerOverlay.findViewWithTag("player_settings_drawer");
    if (old != null) { mPlayerOverlay.removeView(old); return; }
    LinearLayout drawer = new LinearLayout(this);
    drawer.setTag("player_settings_drawer");
    drawer.setOrientation(LinearLayout.VERTICAL);
    drawer.setPadding(dp(14), dp(18), dp(14), dp(18));
    drawer.setBackground(surface(cobraAlpha(mTheme.rail, 246), 24, mTheme.line, 1));
    TextView title = text("PLAYER SETTINGS", mTheme.text, 18, Gravity.CENTER_VERTICAL | Gravity.LEFT);
    title.setTypeface(null, Typeface.BOLD);
    drawer.addView(title, new LinearLayout.LayoutParams(-1, dp(58)));
    Button audio = action("Audio / Subtitles");
    Button fit = action("Fit / Crop");
    Button cast = action("Cast / Route");
    Button guide = action("Guide");
    Button multi = action("Multi-View");
    Button close = action("Close Player");
    audio.setOnClickListener(v -> showTrackChooser());
    fit.setOnClickListener(v -> cycleAspectMode());
    cast.setOnClickListener(v -> openCastSettings());
    guide.setOnClickListener(v -> { closePlayer(); showGuide(); });
    multi.setOnClickListener(v -> beginMultiView());
    close.setOnClickListener(v -> closePlayer());
    for (Button item : new Button[]{audio, fit, cast, guide, multi, close}) {
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(mTheme.touchTarget));
      p.bottomMargin = dp(8);
      drawer.addView(item, p);
    }
    int width = dp(isCompact() ? 286 : 340);
    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(width, -1, Gravity.RIGHT);
    params.setMargins(0, dp(14), dp(14), dp(14));
    mPlayerOverlay.addView(drawer, params);
    drawer.bringToFront();
  }

  private void startSinglePlayer(String url) {
''',
        "player settings drawer",
    )

    # Multi-View: selected tile can be promoted to Single View, or removed.
    # Removing from a 2-up view naturally returns the remaining feed to single.
    java = once(
        java,
        "    Button exit = action(\"✕\");\n    exit.setOnClickListener(v -> releaseMulti());\n",
        "    Button single = action(\"SINGLE\");\n"
        "    single.setOnClickListener(v -> multiToSingle());\n"
        "    mMultiChrome.addView(single, new LinearLayout.LayoutParams(0, dp(48), 1));\n"
        "    Button remove = action(\"REMOVE\");\n"
        "    remove.setOnClickListener(v -> removeSelectedMultiTile());\n"
        "    mMultiChrome.addView(remove, new LinearLayout.LayoutParams(0, dp(48), 1));\n"
        "    Button exit = action(\"✕\");\n"
        "    exit.setOnClickListener(v -> releaseMulti());\n",
        "Multi-View management controls",
    )
    java = once(
        java,
        "  private void showMultiChromeTemporarily() {\n",
        '''  private void multiToSingle() {
    if (mMultiChannels == null || mMultiChannels.length == 0) return;
    int selected = Math.max(0, Math.min(mAudioTile, mMultiChannels.length - 1));
    Channel keep = mMultiChannels[selected];
    mReflowingMulti = true;
    releaseMulti();
    mReflowingMulti = false;
    playChannel(keep);
  }

  private void removeSelectedMultiTile() {
    if (mMultiChannels == null || mMultiChannels.length < 2) return;
    int selected = Math.max(0, Math.min(mAudioTile, mMultiChannels.length - 1));
    ArrayList<Channel> remaining = new ArrayList<>();
    for (int i = 0; i < mMultiChannels.length; i++) {
      if (i != selected && mMultiChannels[i] != null) remaining.add(mMultiChannels[i]);
    }
    mReflowingMulti = true;
    releaseMulti();
    mReflowingMulti = false;
    if (remaining.size() == 1) playChannel(remaining.get(0));
    else if (remaining.size() >= 2) openMultiView(remaining);
  }

  private void showMultiChromeTemporarily() {
''',
        "Multi-View reduce helpers",
    )
    return java


def verify(java: str) -> None:
    required = (
        "mRail.setVisibility(View.GONE)",
        "toggleCobraDrawer()",
        'mHeader.setText("☰  " + title)',
        "button.setFocusableInTouchMode(false)",
        "showPlayerSettingsDrawer()",
        'setTag("player_settings_drawer")',
        "multiToSingle()",
        "removeSelectedMultiTile()",
        'Button single = action("SINGLE")',
        'Button remove = action("REMOVE")',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("approved Cobra UI contract missing: " + token)
