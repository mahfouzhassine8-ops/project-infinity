#!/usr/bin/env python3
"""Modernize Cobra mobile/TV presentation on top of Runtime-v3 structural views.

Android presentation-shell only. This pass does not touch Kodi C/C++, renderer,
provider/playback ownership, rotation/Fold, background/resume or Infinity handoff.
It implements the device-tested UX corrections requested after 2103146:
- popup navigation drawer with Search/TV/Movies/Shows/Recordings/My List
- mini-player-first channel selection; second activation promotes fullscreen
- mini-player overlay controls
- Favorites in the TV category hub
- category -> filtered TV grid with preview preserved
- long-press sheet with Schedule Recording / Group / Share / EPG / Hide
"""
from __future__ import annotations

import argparse
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Mobile modernization {label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"Mobile modernization {label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"Mobile modernization {label}: end marker missing")
    return text[:a] + replacement + text[b:]


def patch(java: str) -> str:
    java = once(
        java,
        "  private boolean mCobraPreviewTriedFallback = false;\n",
        "  private boolean mCobraPreviewTriedFallback = false;\n"
        "  private boolean mGuidePreviewArmed = false;\n"
        "  private boolean mCobraPreviewMuted = false;\n"
        "  private boolean mCobraPreviewCaptions = false;\n"
        '  private static final String COBRA_HIDDEN_CHANNELS = "cobra_hidden_channels";\n'
        '  private static final String COBRA_CUSTOM_GROUP_PREFIX = "cobra_custom_group|";\n',
        "preview interaction state",
    )

    drawer = r'''  private boolean closeCobraExperienceDrawer() {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    View old = decor.findViewWithTag("cobra_experience_drawer");
    if (old == null) return false;
    decor.removeView(old);
    return true;
  }

  private void addCobraDrawerAction(LinearLayout list, String label, View.OnClickListener listener) {
    Button button = action(label);
    button.setAllCaps(false);
    button.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
    button.setOnClickListener(v -> { closeCobraExperienceDrawer(); listener.onClick(v); });
    LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(64));
    p.bottomMargin = dp(7);
    list.addView(button, p);
  }

  private void toggleCobraDrawer() {
    if (closeCobraExperienceDrawer()) return;
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    FrameLayout shield = new FrameLayout(this);
    shield.setTag("cobra_experience_drawer");
    shield.setClickable(true);
    shield.setBackgroundColor(Color.argb(142, 0, 0, 0));
    shield.setOnClickListener(v -> closeCobraExperienceDrawer());

    LinearLayout drawer = new LinearLayout(this);
    drawer.setOrientation(LinearLayout.VERTICAL);
    drawer.setClickable(true);
    drawer.setPadding(dp(18), dp(24), dp(18), dp(18));
    drawer.setBackground(surface(cobraAlpha(mTheme.rail, 252), 28, mTheme.line, 1));

    TextView brand = text("COBRA LIVE", mTheme.accentSoft, 15,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    brand.setTypeface(null, Typeface.BOLD);
    drawer.addView(brand, new LinearLayout.LayoutParams(-1, dp(52)));

    addCobraDrawerAction(drawer, "SEARCH", v -> { stopCobraPreview(); showSearch(); });
    addCobraDrawerAction(drawer, "TV", v -> {
      mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
      showCobraTvHub();
    });
    addCobraDrawerAction(drawer, "MOVIES", v -> { stopCobraPreview(); showMovies(); });
    addCobraDrawerAction(drawer, "SHOWS", v -> { stopCobraPreview(); showSeries(); });
    addCobraDrawerAction(drawer, "RECORDINGS", v -> { stopCobraPreview(); showRecordings(); });
    addCobraDrawerAction(drawer, "MY LIST", v -> {
      mCategory = "FAVORITES";
      mGuidePreviewArmed = false;
      mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
      showGuideGrid();
    });

    View spacer = new View(this);
    drawer.addView(spacer, new LinearLayout.LayoutParams(-1, 0, 1));
    LinearLayout footer = new LinearLayout(this);
    footer.setGravity(Gravity.CENTER_VERTICAL);
    Button settings = action("⚙  SETTINGS");
    Button infinity = action("∞  INFINITY");
    settings.setOnClickListener(v -> { closeCobraExperienceDrawer(); stopCobraPreview(); showSettings(); });
    infinity.setOnClickListener(v -> { closeCobraExperienceDrawer(); stopCobraPreview(); returnToInfinity(); });
    footer.addView(settings, new LinearLayout.LayoutParams(0, dp(58), 1));
    LinearLayout.LayoutParams inf = new LinearLayout.LayoutParams(0, dp(58), 1);
    inf.leftMargin = dp(8); footer.addView(infinity, inf);
    drawer.addView(footer, new LinearLayout.LayoutParams(-1, dp(62)));

    int width = Math.min(dp(360), Math.max(dp(286),
        getResources().getDisplayMetrics().widthPixels - dp(46)));
    FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(width, -1, Gravity.LEFT);
    p.setMargins(dp(12), dp(12), 0, dp(12));
    shield.addView(drawer, p);
    decor.addView(shield, new FrameLayout.LayoutParams(-1, -1));
    drawer.bringToFront();
  }

  private void closeCobraDrawer() {
    closeCobraExperienceDrawer();
    if (mRail != null) mRail.setVisibility(View.GONE);
  }

'''
    java = replace_between(
        java,
        "  private void toggleCobraDrawer() {\n",
        "  private void addRail(String label, View.OnClickListener listener) {\n",
        drawer,
        "popup experience drawer",
    )

    java = once(
        java,
        "  private void ensureCobraPreviewSelection(ArrayList<Channel> channels) {\n"
        "    if (mGuidePreviewChannel != null || channels.isEmpty()) return;\n"
        "    mGuidePreviewChannel = channels.get(0);\n"
        "    mGuidePreviewKey = sourceIdForChannel(mGuidePreviewChannel) + \"|\" + mGuidePreviewChannel.id;\n"
        "  }\n",
        "  private void ensureCobraPreviewSelection(ArrayList<Channel> channels) {\n"
        "    if (mGuidePreviewChannel != null || channels.isEmpty()) return;\n"
        "    mGuidePreviewChannel = channels.get(0);\n"
        "    mGuidePreviewKey = sourceIdForChannel(mGuidePreviewChannel) + \"|\" + mGuidePreviewChannel.id;\n"
        "    mGuidePreviewArmed = false;\n"
        "  }\n",
        "auto preview is not armed for fullscreen",
    )

    preview = r'''  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {
    stopCobraPreview();
    FrameLayout host = new FrameLayout(this);
    mCobraPreviewHost = host;
    host.setBackground(surface(Color.BLACK, 22, mTheme.line, 1));
    host.setClickable(true);

    mCobraPreviewTexture = new TextureView(this);
    host.addView(mCobraPreviewTexture, new FrameLayout.LayoutParams(-1, -1));

    TextView badge = text(channel == null ? "SELECT A CHANNEL" : channel.name,
        Color.WHITE, 12, Gravity.RIGHT | Gravity.CENTER_VERTICAL);
    badge.setTag("cobra_preview_label");
    badge.setPadding(dp(12), dp(4), dp(12), dp(4));
    badge.setBackgroundColor(Color.argb(148, 0, 0, 0));
    FrameLayout.LayoutParams badgeP = new FrameLayout.LayoutParams(-2, dp(36), Gravity.TOP | Gravity.RIGHT);
    badgeP.setMargins(dp(10), dp(10), dp(10), 0);
    host.addView(badge, badgeP);

    if (channel != null) {
      LinearLayout controls = new LinearLayout(this);
      controls.setGravity(Gravity.CENTER);
      controls.setPadding(dp(10), dp(4), dp(10), dp(4));
      controls.setBackgroundColor(Color.argb(158, 0, 0, 0));
      Button fullscreen = action("⛶");
      Button favorite = action(mFavorites.contains(channel.id) ? "♥" : "♡");
      Button schedule = action("◷");
      Button captions = action("CC");
      Button volume = action(mCobraPreviewMuted ? "MUTE" : "VOL");
      Button more = action("⋮");
      fullscreen.setContentDescription("Fullscreen");
      favorite.setContentDescription("Favorite");
      schedule.setContentDescription("Schedule recording");
      captions.setContentDescription("Closed captions");
      volume.setContentDescription("Volume");
      more.setContentDescription("More channel actions");
      fullscreen.setOnClickListener(v -> promoteCobraPreviewToFullscreen(channel));
      favorite.setOnClickListener(v -> {
        toggleFavorite(channel);
        favorite.setText(mFavorites.contains(channel.id) ? "♥" : "♡");
      });
      schedule.setOnClickListener(v -> showCobraScheduleRecording(channel));
      captions.setOnClickListener(v -> toggleCobraPreviewCaptions());
      volume.setOnClickListener(v -> {
        toggleCobraPreviewMute();
        volume.setText(mCobraPreviewMuted ? "MUTE" : "VOL");
      });
      more.setOnClickListener(v -> showCobraChannelActions(channel));
      for (Button b : new Button[]{fullscreen, favorite, schedule, captions, volume, more}) {
        b.setAllCaps(false);
        b.setTextSize(13);
        controls.addView(b, new LinearLayout.LayoutParams(0, dp(48), 1));
      }
      FrameLayout.LayoutParams cp = new FrameLayout.LayoutParams(-1, dp(56), Gravity.BOTTOM);
      host.addView(controls, cp);
    }

    host.setOnClickListener(v -> {
      if (mGuidePreviewChannel != null) promoteCobraPreviewToFullscreen(mGuidePreviewChannel);
    });
    if (channel != null) host.post(() -> startCobraPreview(channel));
    return host;
  }

  private void toggleCobraPreviewMute() {
    mCobraPreviewMuted = !mCobraPreviewMuted;
    if (mCobraPreviewPlayer != null) mCobraPreviewPlayer.setVolume(mCobraPreviewMuted ? 0f : 1f);
  }

  private void toggleCobraPreviewCaptions() {
    mCobraPreviewCaptions = !mCobraPreviewCaptions;
    if (mCobraPreviewPlayer == null) return;
    try {
      mCobraPreviewPlayer.setTrackSelectionParameters(
          mCobraPreviewPlayer.getTrackSelectionParameters().buildUpon()
              .setTrackTypeDisabled(androidx.media3.common.C.TRACK_TYPE_TEXT,
                  !mCobraPreviewCaptions)
              .build());
      toast(mCobraPreviewCaptions ? "Captions on when available" : "Captions off");
    } catch (Exception ignored) {
      toast("Captions are not available on this stream");
    }
  }

  private View cobraPreviewDetails(Channel channel) {
    LinearLayout info = new LinearLayout(this);
    info.setOrientation(LinearLayout.VERTICAL);
    info.setPadding(dp(4), dp(8), dp(4), dp(8));
    if (channel == null) {
      info.addView(text("Choose a channel to begin", mTheme.muted, 14,
          Gravity.LEFT | Gravity.CENTER_VERTICAL), new LinearLayout.LayoutParams(-1, dp(52)));
      return info;
    }
    LinearLayout titleRow = new LinearLayout(this);
    titleRow.setGravity(Gravity.CENTER_VERTICAL);
    TextView title = text(channel.name, mTheme.text, 18, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    title.setTypeface(null, Typeface.BOLD);
    Button epg = action("VIEW CHANNEL EPG");
    epg.setOnClickListener(v -> showProgramGuide(channel));
    titleRow.addView(title, new LinearLayout.LayoutParams(0, dp(48), 1));
    titleRow.addView(epg, new LinearLayout.LayoutParams(dp(176), dp(46)));
    info.addView(titleRow, new LinearLayout.LayoutParams(-1, dp(50)));
    ProgramPair pair = programFor(channel);
    String now = pair != null && pair.now != null && !pair.now.isEmpty()
        ? "Now  •  " + pair.now : providerBadge(channel) + "  •  " + channel.group;
    info.addView(text(now, mTheme.muted, 14, Gravity.LEFT | Gravity.CENTER_VERTICAL),
        new LinearLayout.LayoutParams(-1, dp(38)));
    return info;
  }

'''
    java = replace_between(
        java,
        "  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {\n",
        "  private void setCobraPreviewLabel(String value) {\n",
        preview,
        "modern mini player",
    )

    java = once(
        java,
        "      preview.setMediaItem(mediaItem(channel.primaryUrl));\n"
        "      preview.prepare(); preview.play();\n",
        "      preview.setVolume(mCobraPreviewMuted ? 0f : 1f);\n"
        "      preview.setMediaItem(mediaItem(channel.primaryUrl));\n"
        "      preview.prepare(); preview.play();\n",
        "preview mute state",
    )

    helpers = r'''  private String cobraChannelKey(Channel channel) {
    return sourceIdForChannel(channel) + "|" + channel.id;
  }

  private boolean isCobraHidden(Channel channel) {
    Set<String> hidden = mPrefs.getStringSet(COBRA_HIDDEN_CHANNELS, new HashSet<String>());
    return hidden != null && hidden.contains(cobraChannelKey(channel));
  }

  private void hideCobraChannel(Channel channel) {
    Set<String> old = mPrefs.getStringSet(COBRA_HIDDEN_CHANNELS, new HashSet<String>());
    HashSet<String> next = new HashSet<>();
    if (old != null) next.addAll(old);
    next.add(cobraChannelKey(channel));
    mPrefs.edit().putStringSet(COBRA_HIDDEN_CHANNELS, next).apply();
    if (channel == mGuidePreviewChannel) {
      stopCobraPreview();
      mGuidePreviewChannel = null;
      mGuidePreviewKey = "";
      mGuidePreviewArmed = false;
    }
    toast("Channel hidden");
    showCobraPrimaryView();
  }

  private String cobraCustomGroup(Channel channel) {
    return mPrefs.getString(COBRA_CUSTOM_GROUP_PREFIX + cobraChannelKey(channel), "");
  }

  private ArrayList<String> cobraCustomGroups() {
    HashSet<String> found = new HashSet<>();
    for (Map.Entry<String, ?> entry : mPrefs.getAll().entrySet()) {
      if (!entry.getKey().startsWith(COBRA_CUSTOM_GROUP_PREFIX)) continue;
      Object value = entry.getValue();
      if (value instanceof String && !((String) value).trim().isEmpty())
        found.add(((String) value).trim());
    }
    ArrayList<String> groups = new ArrayList<>(found);
    Collections.sort(groups, String.CASE_INSENSITIVE_ORDER);
    return groups;
  }

  private ArrayList<Channel> cobraChannelsForCurrentView() {
    String requested = mCategory == null ? "ALL" : mCategory;
    boolean favorites = "FAVORITES".equals(requested);
    boolean custom = requested.startsWith("MY:");
    if (favorites || custom) mCategory = "ALL";
    ArrayList<Channel> source = new ArrayList<>(filteredChannels(favorites, false));
    mCategory = requested;
    ArrayList<Channel> result = new ArrayList<>();
    String customName = custom ? requested.substring(3) : "";
    for (Channel channel : source) {
      if (isCobraHidden(channel)) continue;
      if (custom && !customName.equals(cobraCustomGroup(channel))) continue;
      result.add(channel);
    }
    return result;
  }

  private void showCobraAddToGroup(Channel channel) {
    final android.widget.EditText input = new android.widget.EditText(this);
    input.setHint("Group name");
    input.setSingleLine(true);
    input.setText(cobraCustomGroup(channel));
    new AlertDialog.Builder(this)
        .setTitle("Add to group")
        .setMessage(channel.name)
        .setView(input)
        .setPositiveButton("Save", (d, which) -> {
          String name = input.getText() == null ? "" : input.getText().toString().trim();
          String key = COBRA_CUSTOM_GROUP_PREFIX + cobraChannelKey(channel);
          if (name.isEmpty()) mPrefs.edit().remove(key).apply();
          else mPrefs.edit().putString(key, name).apply();
          toast(name.isEmpty() ? "Removed from custom group" : "Added to " + name);
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private void shareCobraChannel(Channel channel) {
    try {
      Intent send = new Intent(Intent.ACTION_SEND);
      send.setType("text/plain");
      send.putExtra(Intent.EXTRA_SUBJECT, channel.name);
      send.putExtra(Intent.EXTRA_TEXT, channel.name + "\n" + channel.primaryUrl);
      startActivity(Intent.createChooser(send, "Share channel"));
    } catch (Exception error) {
      toast("Sharing is not available on this device");
    }
  }

  private void showCobraScheduleRecording(Channel channel) {
    String key = sourceIdForChannel(channel) + "|" + channel.epgId;
    ArrayList<GuideProgram> programs = mGuidePrograms.get(key);
    if (programs == null || programs.isEmpty()) {
      toast("No guide data available to schedule");
      return;
    }
    long now = System.currentTimeMillis();
    ArrayList<GuideProgram> future = new ArrayList<>();
    for (GuideProgram p : programs) if (p.stop > now) future.add(p);
    if (future.isEmpty()) {
      toast("No upcoming programmes to schedule");
      return;
    }
    String[] labels = new String[future.size()];
    for (int i = 0; i < future.size(); i++)
      labels[i] = formatTime(future.get(i).start) + "  •  " + future.get(i).title;
    new AlertDialog.Builder(this)
        .setTitle("Schedule recording • " + channel.name)
        .setItems(labels, (d, which) -> {
          GuideProgram p = future.get(which);
          mFeatures.scheduleRecording(channel.primaryUrl, p.title, channel.headers,
              Math.max(now + 1000, p.start), p.stop, sourceIdForChannel(channel), channel.id);
          toast("Recording scheduled");
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private void selectCobraCategory(String value) {
    mCategory = value;
    mGuidePreviewArmed = false;
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
    showGuideGrid();
  }

  private void showCobraTvHub() {
    stopCobraPreview();
    clearStage("COBRA • TV");
    ArrayList<Channel> all = new ArrayList<>(filteredChannels(false, false));
    ensureCobraPreviewSelection(all);
    if (mUi.guidePreviewPlayer) {
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(mUi.guidePreviewHeightDp)));
      mStage.addView(cobraPreviewDetails(mGuidePreviewChannel),
          new LinearLayout.LayoutParams(-1, dp(92)));
    }
    TextView heading = text("FAVORITES & CATEGORIES", mTheme.text, 17,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    heading.setTypeface(null, Typeface.BOLD);
    mStage.addView(heading, new LinearLayout.LayoutParams(-1, dp(52)));

    ScrollView scroll = new ScrollView(this);
    LinearLayout list = new LinearLayout(this);
    list.setOrientation(LinearLayout.VERTICAL);
    Button favorites = action("★  FAVORITES");
    favorites.setOnClickListener(v -> selectCobraCategory("FAVORITES"));
    list.addView(favorites, new LinearLayout.LayoutParams(-1, dp(64)));
    Button allButton = action("ALL CHANNELS");
    allButton.setOnClickListener(v -> selectCobraCategory("ALL"));
    LinearLayout.LayoutParams allP = new LinearLayout.LayoutParams(-1, dp(64)); allP.topMargin = dp(6);
    list.addView(allButton, allP);
    ArrayList<String> categories = categoriesForCurrentChannels();
    for (String group : categories) {
      if (group == null || group.isEmpty() || "ALL".equals(group)) continue;
      final String category = group;
      Button button = action(category);
      button.setAllCaps(false);
      button.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      button.setOnClickListener(v -> selectCobraCategory(category));
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(62)); p.topMargin = dp(6);
      list.addView(button, p);
    }
    for (String group : cobraCustomGroups()) {
      final String value = "MY:" + group;
      Button button = action("MY GROUP  •  " + group);
      button.setAllCaps(false);
      button.setOnClickListener(v -> selectCobraCategory(value));
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(62)); p.topMargin = dp(6);
      list.addView(button, p);
    }
    scroll.addView(list);
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

'''
    java = once(
        java,
        "  private String mobileGuideSummary(Channel channel) {\n",
        helpers + "  private String mobileGuideSummary(Channel channel) {\n",
        "category/share/schedule helpers",
    )

    mobile = r'''  private void showCobraMobileView() {
    stopCobraPreview();
    clearStage("COBRA • MOBILE");
    ArrayList<Channel> visible = cobraChannelsForCurrentView();
    ensureCobraPreviewSelection(visible);

    LinearLayout root = new LinearLayout(this);
    root.setOrientation(LinearLayout.VERTICAL);
    if (mUi.mobilePreviewFirst) {
      root.addView(cobraPreviewPanel(mGuidePreviewChannel, false),
          new LinearLayout.LayoutParams(-1, dp(mUi.mobilePreviewHeightDp)));
      root.addView(cobraPreviewDetails(mGuidePreviewChannel),
          new LinearLayout.LayoutParams(-1, dp(92)));
    }

    LinearLayout tools = new LinearLayout(this);
    tools.setGravity(Gravity.CENTER_VERTICAL);
    Button categories = action("CATEGORIES  •  " +
        (mCategory == null || "ALL".equals(mCategory) ? "ALL" : mCategory.replace("MY:", "")) + "   ▾");
    Button search = action("⌕  SEARCH");
    categories.setOnClickListener(v -> showCobraTvHub());
    search.setOnClickListener(v -> { stopCobraPreview(); showSearch(); });
    tools.addView(categories, new LinearLayout.LayoutParams(0, dp(58), 1.45f));
    LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(0, dp(58), .75f); sp.leftMargin = dp(8);
    tools.addView(search, sp);
    root.addView(tools, new LinearLayout.LayoutParams(-1, dp(62)));

    TextView listTitle = text("CHANNELS", mTheme.muted, 12, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    listTitle.setLetterSpacing(.12f);
    root.addView(listTitle, new LinearLayout.LayoutParams(-1, dp(40)));

    ScrollView scroll = new ScrollView(this);
    LinearLayout rows = new LinearLayout(this);
    rows.setOrientation(LinearLayout.VERTICAL);
    for (Channel channel : visible) {
      final Channel item = channel;
      Button row = action(channel.name + "\n" + mobileGuideSummary(channel));
      row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      row.setAllCaps(false);
      row.setOnClickListener(v -> selectGuidePreview(item));
      row.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1,
          dp(Math.max(64, mUi.mobileChannelRowHeightDp)));
      p.bottomMargin = dp(3);
      rows.addView(row, p);
    }
    if (visible.isEmpty()) {
      rows.addView(text("No channels in this view", mTheme.muted, 15, Gravity.CENTER),
          new LinearLayout.LayoutParams(-1, dp(120)));
    }
    scroll.addView(rows);
    root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
    mStage.addView(root, new LinearLayout.LayoutParams(-1, 0, 1));
  }

'''
    java = replace_between(
        java,
        "  private void showCobraMobileView() {\n",
        "  private boolean closeCobraChannelActions() {\n",
        mobile,
        "modern mobile view",
    )

    sheet = r'''  private void showCobraChannelActions(Channel channel) {
    if (!mUi.mobileLongPressContext) { toggleFavorite(channel); return; }
    closeCobraChannelActions();
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    FrameLayout shield = new FrameLayout(this);
    shield.setTag("cobra_channel_actions");
    shield.setClickable(true);
    shield.setBackgroundColor(Color.argb(132, 0, 0, 0));
    shield.setOnClickListener(v -> closeCobraChannelActions());

    LinearLayout sheet = new LinearLayout(this);
    sheet.setOrientation(LinearLayout.VERTICAL);
    sheet.setClickable(true);
    sheet.setPadding(dp(18), dp(14), dp(18), dp(20));
    sheet.setBackground(surface(cobraAlpha(mTheme.panel, 252), 28, mTheme.line, 1));
    TextView title = text(channel.name, mTheme.text, 18, Gravity.CENTER);
    title.setTypeface(null, Typeface.BOLD);
    sheet.addView(title, new LinearLayout.LayoutParams(-1, dp(58)));

    boolean favorite = mFavorites.contains(channel.id);
    addCobraSheetAction(sheet,
        favorite ? "♥  Remove from Favorites" : "♡  Add to Favorites", v -> {
          toggleFavorite(channel); showCobraPrimaryView();
        });
    addCobraSheetAction(sheet, "◷  Schedule Recording", v -> showCobraScheduleRecording(channel));
    addCobraSheetAction(sheet, "☆  Add to Group", v -> showCobraAddToGroup(channel));
    addCobraSheetAction(sheet, "⇧  Share to a Friend", v -> shareCobraChannel(channel));
    addCobraSheetAction(sheet, "▤  View Channel EPG", v -> showProgramGuide(channel));
    addCobraSheetAction(sheet, "⊘  Hide Channel", v -> hideCobraChannel(channel));

    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM);
    params.setMargins(dp(8), dp(12), dp(8), dp(8));
    shield.addView(sheet, params);
    decor.addView(shield, new FrameLayout.LayoutParams(-1, -1));
    sheet.bringToFront();
  }

'''
    java = replace_between(
        java,
        "  private void showCobraChannelActions(Channel channel) {\n",
        "  private void selectGuidePreview(Channel channel) {\n",
        sheet,
        "long press action sheet",
    )

    java = replace_between(
        java,
        "  private void selectGuidePreview(Channel channel) {\n",
        "  private String guideTitleAt(Channel channel, long instant) {\n",
        r'''  private void selectGuidePreview(Channel channel) {
    String key = cobraChannelKey(channel);
    if (key.equals(mGuidePreviewKey) && mGuidePreviewChannel != null
        && mGuidePreviewArmed && mUi.guideSecondActivationFullscreen) {
      promoteCobraPreviewToFullscreen(channel);
      return;
    }
    mGuidePreviewChannel = channel;
    mGuidePreviewKey = key;
    mGuidePreviewArmed = true;
    if (!mUi.guideFirstActivationPreview) {
      promoteCobraPreviewToFullscreen(channel);
      return;
    }
    showCobraPrimaryView();
  }

''',
        "first tap preview second tap fullscreen",
    )

    guide = r'''  private void showGuideGrid() {
    stopCobraPreview();
    clearStage("COBRA • TV GUIDE");
    mPrefs.edit().putString(COBRA_PRIMARY_VIEW, "guide").apply();
    ArrayList<Channel> visible = cobraChannelsForCurrentView();
    ensureCobraPreviewSelection(visible);

    if (mUi.guidePreviewPlayer) {
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(mUi.guidePreviewHeightDp)));
      mStage.addView(cobraPreviewDetails(mGuidePreviewChannel),
          new LinearLayout.LayoutParams(-1, dp(92)));
    }

    LinearLayout bar = new LinearLayout(this);
    bar.setGravity(Gravity.CENTER_VERTICAL);
    Button categories = action("‹  CATEGORIES");
    categories.setOnClickListener(v -> showCobraTvHub());
    String categoryLabel = mCategory == null || "ALL".equals(mCategory)
        ? "ALL CHANNELS" : ("FAVORITES".equals(mCategory) ? "★ FAVORITES" : mCategory.replace("MY:", "MY GROUP • "));
    TextView current = text(categoryLabel, mTheme.text, 15, Gravity.CENTER_VERTICAL | Gravity.LEFT);
    current.setTypeface(null, Typeface.BOLD);
    bar.addView(categories, new LinearLayout.LayoutParams(dp(150), dp(54)));
    bar.addView(current, new LinearLayout.LayoutParams(0, dp(54), 1));
    mStage.addView(bar, new LinearLayout.LayoutParams(-1, dp(58)));

    if (visible.isEmpty()) {
      mStage.addView(text("No channels in " + categoryLabel, mTheme.muted, 15, Gravity.CENTER),
          new LinearLayout.LayoutParams(-1, 0, 1));
      return;
    }

    long now = System.currentTimeMillis();
    long slot = now - (now % 1800000L);
    SimpleDateFormat clock = new SimpleDateFormat("h:mm a", Locale.US);
    LinearLayout grid = new LinearLayout(this);
    grid.setOrientation(LinearLayout.VERTICAL);
    LinearLayout header = new LinearLayout(this);
    header.setGravity(Gravity.CENTER_VERTICAL);
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
      LinearLayout row = new LinearLayout(this);
      row.setGravity(Gravity.CENTER_VERTICAL);
      Button channelCell = action(String.format(Locale.US, "%03d  %s", number++, channel.name));
      channelCell.setAllCaps(false);
      channelCell.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      channelCell.setOnClickListener(v -> selectGuidePreview(item));
      channelCell.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
      row.addView(channelCell,
          new LinearLayout.LayoutParams(dp(mUi.guideChannelWidthDp), dp(mUi.guideRowHeightDp)));
      for (int i = 0; i < 3; i++) {
        final long when = slot + i * 1800000L;
        Button program = action(guideTitleAt(item, when));
        program.setAllCaps(false);
        program.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
        program.setOnClickListener(v -> selectGuidePreview(item));
        program.setOnLongClickListener(v -> { showCobraChannelActions(item); return true; });
        row.addView(program,
            new LinearLayout.LayoutParams(dp(mUi.guideProgramWidthDp), dp(mUi.guideRowHeightDp)));
      }
      LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(-2, dp(mUi.guideRowHeightDp));
      rp.bottomMargin = dp(3);
      grid.addView(row, rp);
    }

    android.widget.HorizontalScrollView horizontal = new android.widget.HorizontalScrollView(this);
    horizontal.setFillViewport(true);
    horizontal.addView(grid);
    ScrollView vertical = new ScrollView(this);
    vertical.addView(horizontal);
    mStage.addView(vertical, new LinearLayout.LayoutParams(-1, 0, 1));
  }

'''
    java = replace_between(
        java,
        "  private void showGuideGrid() {\n",
        "  private void showGuideCompact() {\n",
        guide,
        "category filtered guide grid",
    )

    # Closing overlays via Back remains layered above the terminal task-exit behavior.
    java = once(
        java,
        "  @Override\n  public void onBackPressed() {\n    if (closeCobraChannelActions()) return;\n",
        "  @Override\n  public void onBackPressed() {\n"
        "    if (closeCobraChannelActions()) return;\n"
        "    if (closeCobraExperienceDrawer()) return;\n",
        "drawer back dismissal",
    )
    return java


def verify(java: str) -> None:
    required = (
        'setTag("cobra_experience_drawer")',
        'addCobraDrawerAction(drawer, "SEARCH"',
        'addCobraDrawerAction(drawer, "TV"',
        'addCobraDrawerAction(drawer, "MOVIES"',
        'addCobraDrawerAction(drawer, "SHOWS"',
        'addCobraDrawerAction(drawer, "RECORDINGS"',
        'addCobraDrawerAction(drawer, "MY LIST"',
        'setContentDescription("Schedule recording")',
        'showCobraScheduleRecording(channel)',
        'Schedule Recording',
        'Add to Group',
        'Share to a Friend',
        'View Channel EPG',
        'Hide Channel',
        'FAVORITES & CATEGORIES',
        'mGuidePreviewArmed',
        'mGuidePreviewArmed && mUi.guideSecondActivationFullscreen',
        'cobraPreviewDetails(mGuidePreviewChannel)',
        'toggleCobraPreviewCaptions()',
        'toggleCobraPreviewMute()',
        'closeCobraExperienceDrawer()) return;',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Modern mobile contract missing: " + token)
    forbidden = (
        '"●  Record Channel"',
        '"■  Stop Recording"',
        '"ⓘ  Channel Information"',
        '"◈  Source Information"',
    )
    for token in forbidden:
        if token in java:
            raise RuntimeError("Legacy long-press action remains: " + token)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: modern Cobra mobile + category grid + mini-player interaction applied")


if __name__ == "__main__":
    main()
