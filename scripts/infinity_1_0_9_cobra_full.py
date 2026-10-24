#!/usr/bin/env python3
"""Build Infinity 1.0.9 Cobra Full Feature Candidate 2.

Candidate 2 layers independently authored DVR, multi-provider, VOD, profiles,
reminders, catch-up, 2-4 feed Multi-View and redacted Health Center contracts
on the accepted Candidate 1 rollback baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import infinity_1_0_9_cobra_legit as base
import infinity_1_0_8_deep_rebrand as deep

ROOT = Path(__file__).resolve().parents[1]
PATCH_DIR = ROOT / "patches/infinity-cobra-v2"
FEATURE = PATCH_DIR / "InfinityCobraFeatureRuntime.java.in"
RECORDING = PATCH_DIR / "InfinityCobraRecordingService.java.in"
REMINDER = PATCH_DIR / "InfinityCobraReminderReceiver.java.in"
BOOT = PATCH_DIR / "InfinityCobraBootReceiver.java.in"
THEME = ROOT / "addons/script.infinity.cobra.theme/resources/cobra-theme.json"

RELEASE = "1.0.9-Cobra-Full-Feature-Candidate-2"
VERSION_CODE = 2103134

GRADLE = base.GRADLE
MANIFEST = base.MANIFEST
SPLASH = base.SPLASH
LIVE_ACTIVITY = base.LIVE_ACTIVITY
INSTALL = Path("cmake/scripts/android/Install.cmake")
SRC = Path("tools/android/packaging/xbmc/src")
HELPERS = {
    FEATURE: SRC / "InfinityCobraFeatureRuntime.java.in",
    RECORDING: SRC / "InfinityCobraRecordingService.java.in",
    REMINDER: SRC / "InfinityCobraReminderReceiver.java.in",
    BOOT: SRC / "InfinityCobraBootReceiver.java.in",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    return once(text, anchor, anchor + addition, label)


def replace_block(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"{label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"{label}: end marker missing")
    return text[:a] + replacement + text[b:]


def configure_deep() -> None:
    deep.RELEASE = RELEASE
    deep.VERSION_CODE = VERSION_CODE


def patch_activity(java: str) -> str:
    java = insert_after(
        java,
        "import android.os.Looper;\n",
        "import android.provider.Settings;\n"
        "import android.webkit.WebView;\n"
        "import android.webkit.WebViewClient;\n"
        "import android.widget.CheckBox;\n",
        "Candidate 2 Android imports",
    )
    java = insert_after(
        java,
        "import androidx.media3.common.Player;\n",
        "import androidx.media3.common.Format;\n"
        "import androidx.media3.common.TrackSelectionOverride;\n"
        "import androidx.media3.common.Tracks;\n",
        "Candidate 2 Media3 track imports",
    )
    java = insert_after(
        java,
        "import androidx.media3.exoplayer.DefaultRenderersFactory;\n",
        "import androidx.media3.exoplayer.DefaultLoadControl;\n",
        "Candidate 2 load-control import",
    )

    java = insert_after(
        java,
        "  private final Handler mMain = new Handler(Looper.getMainLooper());\n",
        "\n"
        "  private InfinityCobraFeatureRuntime mFeatures;\n"
        "  private final Map<String, ArrayList<GuideProgram>> mGuidePrograms = new HashMap<>();\n"
        "  private final Set<String> mArchiveChannels = new HashSet<>();\n"
        "  private String mRecordingSession = \"\";\n"
        "  private String mPlayingVodKey = \"\";\n"
        "  private String mPlayingVodTitle = \"\";\n"
        "  private long mPendingResumeMs = 0L;\n"
        "  private int mPlaybackRetryCount = 0;\n"
        "  private int mAspectMode = 0;\n"
        "  private static final int REQUEST_LOCAL_MEDIA = 4172;\n"
        "  private final Runnable mProgressTicker = new Runnable() {\n"
        "    @Override public void run() {\n"
        "      saveVodProgress();\n"
        "      if (mPlayer != null && !mPlayingVodKey.isEmpty()) mMain.postDelayed(this, 10000);\n"
        "    }\n"
        "  };\n",
        "Candidate 2 runtime fields",
    )

    java = insert_after(
        java,
        "    mPrefs = getSharedPreferences(PREFS, MODE_PRIVATE);\n",
        "    mFeatures = new InfinityCobraFeatureRuntime(this);\n",
        "Candidate 2 feature runtime init",
    )
    java = java.replace("      loadActiveSource(true);", "      loadAllEnabledSources(true);", 1)

    old_rails = '''    addRail("LIVE TV", v -> showLiveHome());
    addRail("GUIDE", v -> showGuide());
    addRail("FAVORITES", v -> showFavorites());
    addRail("RECENTS", v -> showRecents());
    addRail("SEARCH", v -> showSearch());
    addRail("MULTI-VIEW", v -> beginMultiView());
    addRail("SOURCES", v -> showSources());
    addRail("SETTINGS", v -> showSettings());
'''
    new_rails = '''    addRail("LIVE TV", v -> showLiveHome());
    addRail("GUIDE", v -> showGuide());
    addRail("MOVIES", v -> showMovies());
    addRail("SERIES", v -> showSeries());
    addRail("RECORDINGS", v -> showRecordings());
    addRail("FAVORITES", v -> showFavorites());
    addRail("SEARCH", v -> showSearch());
    addRail("MULTI-VIEW", v -> beginMultiView());
    addRail("DISCOVER", v -> showDiscover());
    addRail("SOURCES", v -> showSources());
    addRail("SETTINGS", v -> showSettings());
'''
    java = once(java, old_rails, new_rails, "Candidate 2 navigation rail")

    java = insert_after(
        java,
        "    button.setFocusable(true);\n",
        "    button.setFocusableInTouchMode(true);\n"
        "    button.setMinHeight(dp(48));\n"
        "    button.setMinWidth(dp(48));\n"
        "    button.setStateListAnimator(null);\n",
        "Candidate 2 touch target",
    )

    load_all = r'''  private void loadAllEnabledSources(boolean showBusy) {
    if (mSources.isEmpty()) {
      showWelcome();
      return;
    }
    if (showBusy) {
      clearStage("COBRA • LIVE TV");
      status("Loading enabled TV sources…");
      mStage.addView(text("BUILDING YOUR LIVE LIBRARY…", mTheme.muted, 16, Gravity.CENTER),
          new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
    }
    final ArrayList<LiveSource> enabled = new ArrayList<>();
    for (LiveSource source : mSources) {
      if (mFeatures.sourceEnabled(source.id)) enabled.add(source);
    }
    if (enabled.isEmpty()) {
      status("No sources enabled");
      showSources();
      return;
    }
    mIo.execute(() -> {
      ArrayList<Channel> merged = new ArrayList<>();
      ArrayList<String> failures = new ArrayList<>();
      for (LiveSource source : enabled) {
        try {
          LoadResult result = loadSource(source, false);
          merged.addAll(result.channels);
        } catch (LiveException e) {
          failures.add(source.name + ": " + e.userMessage);
        }
      }
      runOnUiThread(() -> {
        mChannels.clear();
        mChannels.addAll(merged);
        if (mActiveSource == null || !mFeatures.sourceEnabled(mActiveSource.id)) {
          mActiveSource = enabled.get(0);
        }
        if (merged.isEmpty()) {
          clearStage("COBRA • SOURCE ERROR");
          status("No enabled source could load");
          String message = failures.isEmpty() ? "No playable channels were returned." :
              android.text.TextUtils.join("\n\n", failures);
          mStage.addView(text(message, mTheme.text, 15, Gravity.CENTER),
              new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
          return;
        }
        mCategory = "ALL";
        mSearch = "";
        status(merged.size() + " channels • " + enabled.size() + " enabled source" +
            (enabled.size() == 1 ? "" : "s"));
        showLiveHome();
        for (LiveSource source : enabled) loadGuideAsync(source);
        mFeatures.writeHealth("live", mActiveSource == null ? "" : mActiveSource.id,
            "", "ready", failures.isEmpty() ? "" : failures.get(0), 0, 0, -1, "idle", "loading");
      });
    });
  }

'''
    java = once(java, "  private void loadActiveSource(boolean showBusy) {\n",
                load_all + "  private void loadActiveSource(boolean showBusy) {\n",
                "Candidate 2 multi-provider loader")

    java = java.replace(
        "          applyLoadResult(result);\n          showLiveHome();\n          loadGuideAsync(source);",
        "          applyLoadResult(result);\n          showLiveHome();\n          loadGuideAsync(source);\n"
        "          mFeatures.writeHealth(\"live\", source.id, \"\", \"ready\", \"\", 0, 0, -1, \"idle\", \"loading\");",
        1,
    )

    java = java.replace(
        "          object.optString(\"stream_icon\", \"\"),\n          primary,\n          fallback,\n          Collections.emptyMap()));",
        "          object.optString(\"stream_icon\", \"\"),\n          primary,\n          fallback,\n          Collections.emptyMap()));\n"
        "      if (object.optInt(\"tv_archive\", 0) == 1 || object.optInt(\"tv_archive_duration\", 0) > 0)\n"
        "        mArchiveChannels.add(source.id + \":\" + id);",
        1,
    )

    java = java.replace(
        "        Map<String, ProgramPair> parsed = parseXmlTv(xml);\n",
        "        Map<String, ProgramPair> parsed = parseXmlTv(xml);\n"
        "        Map<String, ArrayList<GuideProgram>> programmes = parseXmlTvPrograms(xml);\n",
        1,
    )
    java = java.replace(
        "          mGuide.clear();\n          mGuide.putAll(parsed);\n",
        "          for (Map.Entry<String, ProgramPair> entry : parsed.entrySet())\n"
        "            mGuide.put(source.id + \"|\" + entry.getKey(), entry.getValue());\n"
        "          for (Map.Entry<String, ArrayList<GuideProgram>> entry : programmes.entrySet())\n"
        "            mGuidePrograms.put(source.id + \"|\" + entry.getKey(), entry.getValue());\n",
        1,
    )
    java = java.replace(
        "    return mGuide.get(channel.epgId);",
        "    return mGuide.get(sourceIdForChannel(channel) + \"|\" + channel.epgId);",
        1,
    )

    old_label = '''    } else {
      label.append("\\n     ").append(channel.group);
    }
    row.setText(label.toString());
    row.setOnClickListener(v -> playChannel(channel));
    row.setOnLongClickListener(v -> {
      toggleFavorite(channel);
      return true;
    });
'''
    new_label = '''    } else {
      label.append("\\n     ").append(providerBadge(channel)).append("  •  ").append(channel.group);
    }
    row.setText(label.toString());
    row.setOnClickListener(v -> playChannel(channel));
    row.setOnLongClickListener(v -> {
      if (guideMode) showProgramGuide(channel); else toggleFavorite(channel);
      return true;
    });
'''
    java = once(java, old_label, new_label, "Candidate 2 provider badge + guide detail")

    java = insert_after(
        java,
        "    for (Channel channel : mChannels) {\n",
        "      if (mFeatures.looksAdult(channel.group) || mFeatures.looksAdult(channel.name)) continue;\n",
        "Candidate 2 parental live filter",
    )

    source_actions = r'''  private void showSourceActions(LiveSource source) {
    JSONObject meta = mFeatures.sourceMeta(source.id);
    boolean enabled = meta.optBoolean("enabled", true);
    String[] choices = new String[]{
        enabled ? "Disable playlist" : "Enable playlist",
        "Make active",
        "Edit",
        "Test connection",
        "Change colour",
        "Change icon",
        "Remove"
    };
    new AlertDialog.Builder(this)
        .setTitle(mFeatures.sourceIcon(source.id) + "  " + source.name)
        .setItems(choices, (dialog, which) -> {
          if (which == 0) {
            mFeatures.setSourceMeta(source.id, !enabled,
                mFeatures.sourceColor(source.id), mFeatures.sourceIcon(source.id));
            loadAllEnabledSources(true);
          } else if (which == 1) {
            mActiveSource = source;
            mPrefs.edit().putString(ACTIVE_SOURCE, source.id).apply();
            showLiveHome();
          } else if (which == 2) {
            if ("xtream".equals(source.type)) showXtreamEditor(source); else showM3uEditor(source);
          } else if (which == 3) {
            LiveSource previous = mActiveSource;
            mActiveSource = source;
            loadActiveSource(true);
            if (previous != source) mPrefs.edit().putString(ACTIVE_SOURCE, source.id).apply();
          } else if (which == 4) {
            cycleSourceColour(source);
          } else if (which == 5) {
            cycleSourceIcon(source);
          } else {
            confirmRemoveSource(source);
          }
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private void cycleSourceColour(LiveSource source) {
    String[] colors = {"#FF4059", "#41D3FF", "#A96BFF", "#38D996", "#FFB74D", "#F7F7F7"};
    String current = mFeatures.sourceColor(source.id);
    int index = 0;
    for (int i = 0; i < colors.length; i++) if (colors[i].equalsIgnoreCase(current)) index = i;
    mFeatures.setSourceMeta(source.id, mFeatures.sourceEnabled(source.id),
        colors[(index + 1) % colors.length], mFeatures.sourceIcon(source.id));
    showSources();
  }

  private void cycleSourceIcon(LiveSource source) {
    String[] icons = {"◈", "◆", "●", "▣", "★", "⚡"};
    String current = mFeatures.sourceIcon(source.id);
    int index = 0;
    for (int i = 0; i < icons.length; i++) if (icons[i].equals(current)) index = i;
    mFeatures.setSourceMeta(source.id, mFeatures.sourceEnabled(source.id),
        mFeatures.sourceColor(source.id), icons[(index + 1) % icons.length]);
    showSources();
  }

'''
    java = replace_block(
        java,
        "  private void showSourceActions(LiveSource source) {\n",
        "  private void confirmRemoveSource(LiveSource source) {\n",
        source_actions,
        "Candidate 2 source actions",
    )

    java = java.replace(
        "          } else {\n            loadActiveSource(true);\n          }",
        "          } else {\n            loadAllEnabledSources(true);\n          }",
        1,
    )

    settings_extra = r'''
    Button allSources = action("REFRESH ALL ENABLED SOURCES");
    allSources.setOnClickListener(v -> loadAllEnabledSources(true));

    Button profiles = action("PROFILES & PARENTAL CONTROLS");
    profiles.setOnClickListener(v -> showProfiles());

    Button health = action("COBRA HEALTH SNAPSHOT");
    health.setOnClickListener(v -> showError("Cobra diagnostics (redacted)", mFeatures.healthSnapshot()));
'''
    java = once(java,
        "    Button refresh = action(\"REFRESH CURRENT SOURCE\");\n    refresh.setOnClickListener(v -> loadActiveSource(true));\n",
        "    Button refresh = action(\"REFRESH CURRENT SOURCE\");\n    refresh.setOnClickListener(v -> loadActiveSource(true));\n" + settings_extra,
        "Candidate 2 settings actions")
    java = java.replace(
        "    list.addView(refresh, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n",
        "    list.addView(refresh, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n"
        "    list.addView(allSources, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n"
        "    list.addView(profiles, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n"
        "    list.addView(health, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n",
        1,
    )

    player_overlay = r'''  private void openPlayerOverlay(Channel channel) {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mPlayerOverlay = new FrameLayout(this);
    mPlayerOverlay.setBackgroundColor(Color.BLACK);
    mPlayerOverlay.setFocusable(true);
    mPlayerOverlay.setFocusableInTouchMode(true);

    mPlayerTexture = new TextureView(this);
    mPlayerOverlay.addView(mPlayerTexture, new FrameLayout.LayoutParams(-1, -1));

    TextView state = text("CONNECTING", Color.WHITE, 13, Gravity.TOP | Gravity.RIGHT);
    state.setTag("player_state");
    FrameLayout.LayoutParams stateParams = new FrameLayout.LayoutParams(dp(190), dp(48), Gravity.TOP | Gravity.RIGHT);
    stateParams.setMargins(0, dp(20), dp(20), 0);
    mPlayerOverlay.addView(state, stateParams);

    mPlayerChrome = new LinearLayout(this);
    mPlayerChrome.setOrientation(LinearLayout.VERTICAL);
    mPlayerChrome.setPadding(dp(8), dp(6), dp(8), dp(6));
    mPlayerChrome.setBackgroundColor(Color.argb(215, 4, 6, 10));

    TextView info = text("◈  " + channel.name + "\\n" + providerBadge(channel) + "  •  " + channel.group,
        Color.WHITE, isCompact() ? 14 : 17, Gravity.CENTER_VERTICAL);
    info.setTypeface(null, Typeface.BOLD);
    mPlayerChrome.addView(info, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));

    LinearLayout row1 = new LinearLayout(this);
    row1.setGravity(Gravity.CENTER);
    Button prev = action("◀");
    Button favorite = action("★");
    Button guide = action("GUIDE");
    Button record = action("● REC");
    Button multi = action("▦");
    Button next = action("▶");
    prev.setOnClickListener(v -> stepChannel(-1));
    favorite.setOnClickListener(v -> toggleFavorite(channel));
    guide.setOnClickListener(v -> { closePlayer(); showGuide(); });
    record.setOnClickListener(v -> toggleRecording(channel));
    multi.setOnClickListener(v -> beginMultiView());
    next.setOnClickListener(v -> stepChannel(1));
    for (Button button : new Button[]{prev, favorite, guide, record, multi, next})
      row1.addView(button, new LinearLayout.LayoutParams(0, dp(48), 1));
    mPlayerChrome.addView(row1, new LinearLayout.LayoutParams(-1, dp(52)));

    LinearLayout row2 = new LinearLayout(this);
    row2.setGravity(Gravity.CENTER);
    Button tracks = action("AUDIO / SUBS");
    Button aspect = action("FIT / CROP");
    Button cast = action("CAST / ROUTE");
    Button close = action("✕ CLOSE");
    tracks.setOnClickListener(v -> showTrackChooser());
    aspect.setOnClickListener(v -> cycleAspectMode());
    cast.setOnClickListener(v -> openCastSettings());
    close.setOnClickListener(v -> closePlayer());
    for (Button button : new Button[]{tracks, aspect, cast, close})
      row2.addView(button, new LinearLayout.LayoutParams(0, dp(48), 1));
    mPlayerChrome.addView(row2, new LinearLayout.LayoutParams(-1, dp(52)));

    FrameLayout.LayoutParams chromeParams = new FrameLayout.LayoutParams(-1, dp(isCompact() ? 188 : 202), Gravity.BOTTOM);
    mPlayerOverlay.addView(mPlayerChrome, chromeParams);
    mPlayerOverlay.setOnClickListener(v -> togglePlayerChrome());
    mPlayerOverlay.setOnKeyListener((v, keyCode, event) -> {
      if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
      if (keyCode == KeyEvent.KEYCODE_DPAD_UP || keyCode == KeyEvent.KEYCODE_DPAD_DOWN
          || keyCode == KeyEvent.KEYCODE_DPAD_CENTER) showPlayerChromeTemporarily();
      return false;
    });
    decor.addView(mPlayerOverlay, new FrameLayout.LayoutParams(-1, -1));
    row1.requestFocus();
    scheduleChromeHide();
    mFeatures.writeHealth("player", sourceIdForChannel(channel), channel.id,
        "connecting", "", mPlaybackRetryCount, 0, -1,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
  }

'''
    java = replace_block(
        java,
        "  private void openPlayerOverlay(Channel channel) {\n",
        "  private void startSinglePlayer(String url) {\n",
        player_overlay,
        "Candidate 2 player chrome",
    )

    java = java.replace(
        "          if (playbackState == Player.STATE_BUFFERING) state.setText(\"BUFFERING\");\n"
        "          else if (playbackState == Player.STATE_READY) state.setText(\"LIVE\");\n"
        "          else if (playbackState == Player.STATE_ENDED) state.setText(\"ENDED\");",
        "          if (playbackState == Player.STATE_BUFFERING) state.setText(\"BUFFERING\");\n"
        "          else if (playbackState == Player.STATE_READY) {\n"
        "            state.setText(mPlayingVodKey.isEmpty() ? \"LIVE\" : \"PLAYING\");\n"
        "            if (mPendingResumeMs > 0 && mPlayer != null) { mPlayer.seekTo(mPendingResumeMs); mPendingResumeMs = 0; }\n"
        "            mMain.removeCallbacks(mProgressTicker);\n"
        "            if (!mPlayingVodKey.isEmpty()) mMain.postDelayed(mProgressTicker, 10000);\n"
        "          } else if (playbackState == Player.STATE_ENDED) state.setText(\"ENDED\");\n"
        "          if (mPlaying != null) mFeatures.writeHealth(\"player\", sourceIdForChannel(mPlaying), mPlaying.id,\n"
        "              playbackState == Player.STATE_BUFFERING ? \"buffering\" : playbackState == Player.STATE_READY ? \"ready\" : \"other\",\n"
        "              \"\", mPlaybackRetryCount, 0, -1, mRecordingSession.isEmpty() ? \"idle\" : \"recording\", \"ready\");",
        1,
    )
    java = java.replace(
        "            mTriedFallback = true;\n",
        "            mTriedFallback = true;\n            mPlaybackRetryCount++;\n",
        1,
    )
    java = java.replace(
        "          showPlayerError(error);",
        "          if (mPlaying != null) mFeatures.writeHealth(\"player\", sourceIdForChannel(mPlaying), mPlaying.id,\n"
        "              \"error\", error == null ? \"UNKNOWN\" : error.getErrorCodeName(), mPlaybackRetryCount, 0, -1,\n"
        "              mRecordingSession.isEmpty() ? \"idle\" : \"recording\", \"ready\");\n"
        "          showPlayerError(error);",
        1,
    )

    player_builder = r'''  private ExoPlayer buildPlayer(TextureView texture, Channel channel, boolean audible) {
    DefaultHttpDataSource.Factory http = new DefaultHttpDataSource.Factory()
        .setAllowCrossProtocolRedirects(true)
        .setConnectTimeoutMs(15000)
        .setReadTimeoutMs(30000)
        .setUserAgent("Infinity Cobra/2.0");
    if (channel.headers != null && !channel.headers.isEmpty()) http.setDefaultRequestProperties(channel.headers);
    DefaultDataSource.Factory data = new DefaultDataSource.Factory(this, http);
    DefaultRenderersFactory renderers = new DefaultRenderersFactory(this).setEnableDecoderFallback(true);
    DefaultLoadControl loadControl = new DefaultLoadControl.Builder()
        .setBufferDurationsMs(15000, 180000, 2500, 5000)
        .setPrioritizeTimeOverSizeThresholds(true)
        .build();
    ExoPlayer player = new ExoPlayer.Builder(this, renderers)
        .setMediaSourceFactory(new DefaultMediaSourceFactory(data))
        .setLoadControl(loadControl)
        .build();
    player.setAudioAttributes(new AudioAttributes.Builder()
        .setUsage(C.USAGE_MEDIA).setContentType(C.AUDIO_CONTENT_TYPE_MOVIE).build(), false);
    player.setHandleAudioBecomingNoisy(true);
    player.setVideoTextureView(texture);
    player.setVolume(audible ? 1f : 0f);
    return player;
  }

'''
    java = replace_block(
        java,
        "  private ExoPlayer buildPlayer(\n",
        "  private MediaItem mediaItem(String url) {\n",
        player_builder,
        "Candidate 2 buffered player",
    )

    java = java.replace(
        "  private void closePlayer() {\n    releaseSinglePlayer();",
        "  private void closePlayer() {\n    saveVodProgress();\n    mMain.removeCallbacks(mProgressTicker);\n    releaseSinglePlayer();",
        1,
    )
    java = java.replace(
        "    mPlayingIndex = -1;\n  }",
        "    mPlayingIndex = -1;\n    mPlayingVodKey = \"\";\n    mPlayingVodTitle = \"\";\n    mPendingResumeMs = 0L;\n    mPlaybackRetryCount = 0;\n  }",
        1,
    )

    multi_and_features = MULTI_AND_FEATURE_METHODS
    java = replace_block(
        java,
        "  private void beginMultiView() {\n",
        "  private void toggleFavorite(Channel channel) {\n",
        multi_and_features,
        "Candidate 2 feature methods",
    )

    java = java.replace(
        "    mPrefs.edit().putStringSet(FAVORITES, new HashSet<>(mFavorites)).apply();",
        "    mPrefs.edit().putStringSet(mFeatures.profileKey(FAVORITES), new HashSet<>(mFavorites)).apply();",
        1,
    )
    java = java.replace(
        "    mPrefs.edit().putString(RECENTS, array.toString()).apply();",
        "    mPrefs.edit().putString(mFeatures.profileKey(RECENTS), array.toString()).apply();",
        1,
    )
    java = java.replace(
        "    Set<String> favorites = mPrefs.getStringSet(FAVORITES, Collections.emptySet());",
        "    Set<String> favorites = mPrefs.getStringSet(mFeatures.profileKey(FAVORITES), Collections.emptySet());",
        1,
    )
    java = java.replace(
        "      JSONArray recent = new JSONArray(mPrefs.getString(RECENTS, \"[]\"));",
        "      JSONArray recent = new JSONArray(mPrefs.getString(mFeatures.profileKey(RECENTS), \"[]\"));",
        1,
    )

    java = insert_after(
        java,
        "  @Override\n  public void onBackPressed() {\n",
        "",
        "Candidate 2 back anchor",
    )
    activity_result = r'''
  @Override
  protected void onActivityResult(int requestCode, int resultCode, Intent data) {
    super.onActivityResult(requestCode, resultCode, data);
    if (requestCode != REQUEST_LOCAL_MEDIA || resultCode != RESULT_OK || data == null || data.getData() == null) return;
    Uri uri = data.getData();
    try {
      getContentResolver().takePersistableUriPermission(uri,
          data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION));
    } catch (Exception ignored) {}
    Channel local = new Channel("local:" + Integer.toHexString(uri.toString().hashCode()),
        "My File", "Local media", "", "", uri.toString(), "", Collections.emptyMap());
    playChannel(local);
  }

'''
    java = once(java, "  @Override\n  public void onBackPressed() {\n", activity_result + "  @Override\n  public void onBackPressed() {\n",
                "Candidate 2 local-media callback")

    inner = r'''  private static final class GuideProgram {
    String channel = "";
    String title = "";
    String description = "";
    long start = 0L;
    long stop = 0L;
  }

  private static final class VodItem {
    final String sourceId;
    final String id;
    final String title;
    final String category;
    final String icon;
    final String extension;
    final boolean series;
    VodItem(String sourceId, String id, String title, String category, String icon,
            String extension, boolean series) {
      this.sourceId = sourceId; this.id = id; this.title = title; this.category = category;
      this.icon = icon; this.extension = extension; this.series = series;
    }
  }

  private static final class TrackChoice {
    final Tracks.Group group;
    final int index;
    final String label;
    TrackChoice(Tracks.Group group, int index, String label) {
      this.group = group; this.index = index; this.label = label;
    }
  }

'''
    java = once(java, "  private static final class LiveException extends Exception {\n",
                inner + "  private static final class LiveException extends Exception {\n",
                "Candidate 2 inner models")

    java = java.replace(
        "    int guideRowHeight = 94;",
        "    int guideRowHeight = 94;\n    int touchTarget = 52;\n    int railItemHeight = 48;\n    int motionMs = 160;",
        1,
    )
    java = java.replace(
        "        theme.guideRowHeight = clamp(\n            root.optInt(\"guide_row_height\", theme.guideRowHeight), 70, 132);",
        "        theme.guideRowHeight = clamp(\n            root.optInt(\"guide_row_height\", theme.guideRowHeight), 70, 132);\n"
        "        theme.touchTarget = clamp(root.optInt(\"touch_target\", theme.touchTarget), 48, 80);\n"
        "        theme.railItemHeight = clamp(root.optInt(\"rail_item_height\", theme.railItemHeight), 42, 70);\n"
        "        theme.motionMs = clamp(root.optInt(\"motion_ms\", theme.motionMs), 80, 320);",
        1,
    )
    java = java.replace(
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(isCompact() ? 48 : 52));",
        "        LinearLayout.LayoutParams.MATCH_PARENT, dp(mTheme.railItemHeight));",
        1,
    )
    return java


MULTI_AND_FEATURE_METHODS = r'''  private void beginMultiView() {
    if (mChannels.size() < 2) { toast("Multi-View needs at least two channels"); return; }
    new AlertDialog.Builder(this)
        .setTitle("Multi-View")
        .setItems(new String[]{"2 screens", "3 screens", "4 screens"}, (dialog, which) -> chooseMultiChannels(which + 2))
        .setNegativeButton("Cancel", null)
        .show();
  }

  private void chooseMultiChannels(int count) {
    ArrayList<Channel> options = new ArrayList<>(filteredChannels(false, false));
    if (options.size() < count) { toast("Not enough channels for " + count + " screens"); return; }
    final boolean[] checked = new boolean[options.size()];
    final int[] selected = {0};
    if (mPlaying != null) {
      int index = options.indexOf(mPlaying);
      if (index >= 0) { checked[index] = true; selected[0] = 1; }
    }
    String[] names = new String[options.size()];
    for (int i = 0; i < options.size(); i++) names[i] = providerBadge(options.get(i)) + "  •  " + options.get(i).name;
    AlertDialog dialog = new AlertDialog.Builder(this)
        .setTitle("Choose " + count + " channels")
        .setMultiChoiceItems(names, checked, (d, which, isChecked) -> {
          if (isChecked) {
            if (selected[0] >= count) { ((AlertDialog) d).getListView().setItemChecked(which, false); checked[which] = false; toast("Maximum " + count + " channels"); }
            else { checked[which] = true; selected[0]++; }
          } else { checked[which] = false; selected[0] = Math.max(0, selected[0] - 1); }
        })
        .setPositiveButton("OPEN", null)
        .setNegativeButton("Cancel", null)
        .create();
    dialog.setOnShowListener(ignore -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
      ArrayList<Channel> chosen = new ArrayList<>();
      for (int i = 0; i < checked.length; i++) if (checked[i]) chosen.add(options.get(i));
      if (chosen.size() != count) { toast("Choose exactly " + count + " channels"); return; }
      dialog.dismiss(); openMultiView(chosen);
    }));
    dialog.show();
  }

  private void openMultiView(List<Channel> channels) {
    closePlayer(); releaseMulti();
    int count = Math.min(4, Math.max(2, channels.size()));
    mMultiChannels = channels.subList(0, count).toArray(new Channel[0]);
    mMultiPlayers = new ExoPlayer[count]; mMultiTextures = new TextureView[count]; mAudioTile = 0;
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mMultiOverlay = new FrameLayout(this); mMultiOverlay.setBackgroundColor(Color.BLACK);
    LinearLayout stack = new LinearLayout(this); stack.setOrientation(LinearLayout.VERTICAL);
    mMultiOverlay.addView(stack, new FrameLayout.LayoutParams(-1, -1));
    if (isPortrait()) {
      for (int i = 0; i < count; i++) stack.addView(createMultiTile(i), new LinearLayout.LayoutParams(-1, 0, 1));
    } else {
      int rows = count <= 2 ? 1 : 2;
      for (int rowIndex = 0; rowIndex < rows; rowIndex++) {
        LinearLayout row = new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL);
        int start = rowIndex * 2; int end = Math.min(count, start + (rows == 1 ? count : 2));
        for (int i = start; i < end; i++) row.addView(createMultiTile(i), new LinearLayout.LayoutParams(0, -1, 1));
        stack.addView(row, new LinearLayout.LayoutParams(-1, 0, 1));
      }
    }
    LinearLayout bar = new LinearLayout(this); bar.setGravity(Gravity.CENTER); bar.setPadding(dp(8), dp(5), dp(8), dp(5));
    bar.setBackgroundColor(Color.argb(220, 4, 6, 10));
    for (int i = 0; i < count; i++) {
      final int index = i; Button audio = action("AUDIO " + (i + 1)); audio.setOnClickListener(v -> setMultiAudio(index));
      bar.addView(audio, new LinearLayout.LayoutParams(0, dp(48), 1));
    }
    Button exit = action("✕"); exit.setOnClickListener(v -> releaseMulti());
    bar.addView(exit, new LinearLayout.LayoutParams(dp(64), dp(48)));
    mMultiOverlay.addView(bar, new FrameLayout.LayoutParams(-1, dp(60), Gravity.TOP));
    decor.addView(mMultiOverlay, new FrameLayout.LayoutParams(-1, -1));
    setMultiAudio(0);
    mFeatures.writeHealth("multiview", "", "", "ready", "", 0, count, 0,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
  }

  private FrameLayout createMultiTile(int index) {
    FrameLayout tile = new FrameLayout(this); tile.setFocusable(true); tile.setFocusableInTouchMode(true);
    TextureView texture = new TextureView(this); mMultiTextures[index] = texture;
    tile.addView(texture, new FrameLayout.LayoutParams(-1, -1));
    TextView label = text(mMultiChannels[index].name + (index == 0 ? "  •  AUDIO" : ""), Color.WHITE, 13, Gravity.CENTER_VERTICAL);
    label.setTag("multi_label_" + index); label.setBackgroundColor(Color.argb(185, 4, 6, 10));
    tile.addView(label, new FrameLayout.LayoutParams(-1, dp(44), Gravity.BOTTOM));
    tile.setOnClickListener(v -> setMultiAudio(index)); tile.setOnFocusChangeListener((v, focused) -> { if (focused) setMultiAudio(index); });
    try {
      ExoPlayer player = buildPlayer(texture, mMultiChannels[index], index == 0); mMultiPlayers[index] = player;
      player.addListener(new Player.Listener() {
        @Override public void onPlayerError(PlaybackException error) { label.setText(mMultiChannels[index].name + "  •  ERROR " + error.getErrorCodeName()); }
      });
      player.setMediaItem(mediaItem(mMultiChannels[index].primaryUrl)); player.prepare(); player.play();
    } catch (Exception e) { label.setText(mMultiChannels[index].name + "  •  ERROR"); }
    return tile;
  }

  private void setMultiAudio(int index) {
    if (mMultiPlayers == null || index < 0 || index >= mMultiPlayers.length) return;
    mAudioTile = index;
    for (int i = 0; i < mMultiPlayers.length; i++) {
      if (mMultiPlayers[i] != null) mMultiPlayers[i].setVolume(i == index ? 1f : 0f);
      if (mMultiOverlay != null) {
        View view = mMultiOverlay.findViewWithTag("multi_label_" + i);
        if (view instanceof TextView && mMultiChannels != null) ((TextView) view).setText(mMultiChannels[i].name + (i == index ? "  •  AUDIO" : ""));
      }
    }
    mFeatures.writeHealth("multiview", "", "", "ready", "", 0, mMultiPlayers.length, index,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
  }

  private void releaseMulti() {
    if (mMultiPlayers != null) for (int i = 0; i < mMultiPlayers.length; i++) {
      ExoPlayer player = mMultiPlayers[i]; if (player == null) continue;
      try { if (mMultiTextures != null && mMultiTextures[i] != null) player.clearVideoTextureView(mMultiTextures[i]); } catch (Exception ignored) {}
      try { player.stop(); } catch (Exception ignored) {} try { player.release(); } catch (Exception ignored) {}
    }
    mMultiPlayers = null; mMultiTextures = null; mMultiChannels = null;
    if (mMultiOverlay != null) try { ((FrameLayout) getWindow().getDecorView()).removeView(mMultiOverlay); } catch (Exception ignored) {}
    mMultiOverlay = null;
  }

  private String sourceIdForChannel(Channel channel) {
    if (channel == null || channel.id == null) return "";
    for (LiveSource source : mSources) if (channel.id.startsWith(source.id + ":")) return source.id;
    return "";
  }

  private LiveSource sourceForChannel(Channel channel) {
    String id = sourceIdForChannel(channel); for (LiveSource source : mSources) if (source.id.equals(id)) return source; return null;
  }

  private LiveSource sourceById(String id) { for (LiveSource source : mSources) if (source.id.equals(id)) return source; return null; }

  private String providerBadge(Channel channel) {
    LiveSource source = sourceForChannel(channel); if (source == null) return "LOCAL";
    return mFeatures.sourceIcon(source.id) + " " + source.name;
  }

  private void toggleRecording(Channel channel) {
    if (!mRecordingSession.isEmpty()) { mFeatures.stopRecording(mRecordingSession); mRecordingSession = ""; toast("Recording stop requested"); return; }
    new AlertDialog.Builder(this).setTitle("Record " + channel.name)
        .setItems(new String[]{"30 minutes", "1 hour", "2 hours", "4 hours", "Until I stop it"}, (d, which) -> {
          long[] durations = {30, 60, 120, 240, 0}; long endAt = durations[which] == 0 ? 0 : System.currentTimeMillis() + durations[which] * 60000L;
          mRecordingSession = mFeatures.startRecording(channel.primaryUrl, channel.name, channel.headers, endAt,
              sourceIdForChannel(channel), channel.id);
          if (mRecordingSession.isEmpty()) showError("Recording not started", "At least 256 MB of free recording space is required.");
          else toast("Recording started");
        }).setNegativeButton("Cancel", null).show();
  }

  private void showRecordings() {
    clearStage("COBRA • RECORDINGS"); status("Recordings and scheduled DVR");
    ScrollView scroll = new ScrollView(this); LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); scroll.addView(list);
    JSONArray recordings = mFeatures.recordings();
    for (int i = 0; i < recordings.length(); i++) {
      JSONObject item = recordings.optJSONObject(i); if (item == null) continue;
      String path = item.optString("path"); String name = item.optString("name");
      Button row = action("▶  " + name + "\\n     " + formatBytes(item.optLong("size"))); row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      row.setOnClickListener(v -> playLocalPath(path, name));
      row.setOnLongClickListener(v -> { showRecordingActions(path, name); return true; });
      list.addView(row, new LinearLayout.LayoutParams(-1, dp(66)));
    }
    JSONArray schedules = mFeatures.schedules();
    if (schedules.length() > 0) list.addView(text("SCHEDULED", mTheme.accent, 13, Gravity.LEFT), new LinearLayout.LayoutParams(-1, dp(44)));
    for (int i = 0; i < schedules.length(); i++) {
      JSONObject item = schedules.optJSONObject(i); if (item == null) continue;
      String id = item.optString("id"); Button row = action("◷  " + item.optString("name") + "\\n     " + formatTime(item.optLong("start_at")));
      row.setOnLongClickListener(v -> { mFeatures.removeSchedule(id); showRecordings(); return true; });
      list.addView(row, new LinearLayout.LayoutParams(-1, dp(66)));
    }
    if (recordings.length() == 0 && schedules.length() == 0) list.addView(text("No recordings yet. Record live or schedule one from Guide.", mTheme.muted, 15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, dp(140)));
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void showRecordingActions(String path, String name) {
    new AlertDialog.Builder(this).setTitle(name).setItems(new String[]{"Play", "Rename", "Delete"}, (d, which) -> {
      if (which == 0) playLocalPath(path, name);
      else if (which == 1) { EditText input = field("New name", InputType.TYPE_CLASS_TEXT); input.setText(name); new AlertDialog.Builder(this).setTitle("Rename recording").setView(input).setPositiveButton("RENAME", (x, w) -> { mFeatures.renameRecording(path, input.getText().toString()); showRecordings(); }).setNegativeButton("Cancel", null).show(); }
      else new AlertDialog.Builder(this).setTitle("Delete recording?").setMessage(name).setPositiveButton("DELETE", (x, w) -> { mFeatures.deleteRecording(path); showRecordings(); }).setNegativeButton("Cancel", null).show();
    }).show();
  }

  private void playLocalPath(String path, String name) {
    Channel local = new Channel("recording:" + Integer.toHexString(path.hashCode()), name, "Recording", "", "",
        Uri.fromFile(new File(path)).toString(), "", Collections.emptyMap()); playChannel(local);
  }

  private String formatBytes(long bytes) { if (bytes < 1024 * 1024) return (bytes / 1024) + " KB"; if (bytes < 1024L * 1024L * 1024L) return (bytes / (1024 * 1024)) + " MB"; return String.format(Locale.US, "%.1f GB", bytes / (1024d * 1024d * 1024d)); }
  private String formatTime(long millis) { return new SimpleDateFormat("EEE MMM d • h:mm a", Locale.US).format(new Date(millis)); }

  private Map<String, ArrayList<GuideProgram>> parseXmlTvPrograms(String xml) throws Exception {
    Map<String, ArrayList<GuideProgram>> result = new HashMap<>(); XmlPullParser parser = Xml.newPullParser(); parser.setInput(new java.io.StringReader(xml));
    long now = System.currentTimeMillis(); long min = now - 8L * 86400000L; long max = now + 8L * 86400000L;
    int event = parser.getEventType(); GuideProgram current = null; String textTag = "";
    while (event != XmlPullParser.END_DOCUMENT) {
      if (event == XmlPullParser.START_TAG) {
        String tag = parser.getName();
        if ("programme".equals(tag)) { current = new GuideProgram(); current.channel = parser.getAttributeValue(null, "channel"); current.start = parseXmlTvTime(parser.getAttributeValue(null, "start")); current.stop = parseXmlTvTime(parser.getAttributeValue(null, "stop")); }
        else if (current != null && ("title".equals(tag) || "desc".equals(tag))) textTag = tag;
      } else if (event == XmlPullParser.TEXT && current != null) {
        if ("title".equals(textTag)) current.title += parser.getText(); else if ("desc".equals(textTag)) current.description += parser.getText();
      } else if (event == XmlPullParser.END_TAG) {
        String tag = parser.getName(); if ("title".equals(tag) || "desc".equals(tag)) textTag = "";
        else if ("programme".equals(tag) && current != null) { if (current.channel != null && current.stop >= min && current.start <= max) result.computeIfAbsent(current.channel, k -> new ArrayList<>()).add(current); current = null; textTag = ""; }
      }
      event = parser.next();
    }
    for (ArrayList<GuideProgram> list : result.values()) list.sort((a, b) -> Long.compare(a.start, b.start));
    return result;
  }

  private void showProgramGuide(Channel channel) {
    String key = sourceIdForChannel(channel) + "|" + channel.epgId; ArrayList<GuideProgram> programs = mGuidePrograms.get(key);
    if (programs == null || programs.isEmpty()) { toast("No detailed guide data for this channel"); return; }
    String[] labels = new String[programs.size()]; for (int i = 0; i < programs.size(); i++) labels[i] = formatTime(programs.get(i).start) + "  •  " + programs.get(i).title;
    new AlertDialog.Builder(this).setTitle(channel.name + " • Guide").setItems(labels, (d, which) -> showProgramActions(channel, programs.get(which))).setNegativeButton("Close", null).show();
  }

  private void showProgramActions(Channel channel, GuideProgram program) {
    long now = System.currentTimeMillis(); boolean future = program.start > now; boolean past = program.stop < now; boolean archive = mArchiveChannels.contains(channel.id);
    ArrayList<String> actions = new ArrayList<>(); actions.add("Play live"); if (future) { actions.add("Remind me"); actions.add("Record programme"); } if (past && archive) actions.add("Play catch-up");
    String[] labels = actions.toArray(new String[0]);
    new AlertDialog.Builder(this).setTitle(program.title).setMessage(program.description).setItems(labels, (d, which) -> {
      String action = labels[which]; if ("Play live".equals(action)) playChannel(channel);
      else if ("Remind me".equals(action)) { mFeatures.addReminder(sourceIdForChannel(channel), channel.id, program.title, Math.max(now + 1000, program.start - 60000)); toast("Reminder set"); }
      else if ("Record programme".equals(action)) { mFeatures.scheduleRecording(channel.primaryUrl, program.title, channel.headers, Math.max(now + 1000, program.start), program.stop, sourceIdForChannel(channel), channel.id); toast("Recording scheduled"); }
      else playCatchup(channel, program);
    }).setNegativeButton("Close", null).show();
  }

  private void playCatchup(Channel channel, GuideProgram program) {
    LiveSource source = sourceForChannel(channel); if (source == null || !"xtream".equals(source.type)) { toast("Catch-up is not available for this source"); return; }
    try {
      String streamId = channel.id.substring((source.id + ":").length()); if (streamId.contains(":")) streamId = streamId.substring(0, streamId.indexOf(':'));
      long minutes = Math.max(1, (program.stop - program.start) / 60000L); SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd:HH-mm", Locale.US); String start = f.format(new Date(program.start));
      String primary = source.server + "/timeshift.php?username=" + enc(source.username) + "&password=" + enc(source.password) + "&stream=" + enc(streamId) + "&start=" + enc(start) + "&duration=" + minutes;
      String fallback = source.server + "/timeshift/" + encPath(source.username) + "/" + encPath(source.password) + "/" + minutes + "/" + encPath(start) + "/" + encPath(streamId) + ".ts";
      Channel archive = new Channel(channel.id + ":catchup:" + program.start, program.title, "Catch-up • " + channel.name, channel.epgId, channel.icon, primary, fallback, channel.headers); playChannel(archive);
    } catch (Exception e) { showError("Catch-up", "Could not build the provider catch-up request."); }
  }

  private void showMovies() { showVodLibrary(false); }
  private void showSeries() { showVodLibrary(true); }

  private void showVodLibrary(boolean series) {
    clearStage(series ? "COBRA • SERIES" : "COBRA • MOVIES"); status("Loading enabled provider libraries…");
    mIo.execute(() -> {
      ArrayList<VodItem> items = new ArrayList<>(); ArrayList<String> failures = new ArrayList<>();
      for (LiveSource source : mSources) {
        if (!mFeatures.sourceEnabled(source.id) || !"xtream".equals(source.type)) continue;
        try {
          Map<String, String> cats = new HashMap<>(); JSONArray categories = new JSONArray(httpGet(xtreamUrl(source, series ? "get_series_categories" : "get_vod_categories")));
          for (int i = 0; i < categories.length(); i++) { JSONObject c = categories.optJSONObject(i); if (c != null) cats.put(c.optString("category_id"), c.optString("category_name", "Other")); }
          JSONArray streams = new JSONArray(httpGet(xtreamUrl(source, series ? "get_series" : "get_vod_streams")));
          for (int i = 0; i < streams.length() && items.size() < 10000; i++) {
            JSONObject o = streams.optJSONObject(i); if (o == null) continue; String id = o.optString(series ? "series_id" : "stream_id", ""); if (id.isEmpty()) continue;
            String title = o.optString("name", series ? "Series" : "Movie"); String cat = cats.get(o.optString("category_id", "")); if (cat == null) cat = "Other";
            if (mFeatures.looksAdult(cat) || mFeatures.looksAdult(title)) continue;
            items.add(new VodItem(source.id, id, title, cat, o.optString(series ? "cover" : "stream_icon", ""), sanitizeExtension(o.optString("container_extension", "mp4")), series));
          }
        } catch (Exception e) { failures.add(source.name + ": " + e.getClass().getSimpleName()); }
      }
      runOnUiThread(() -> renderVodItems(items, series, failures));
    });
  }

  private void renderVodItems(ArrayList<VodItem> items, boolean series, ArrayList<String> failures) {
    clearStage(series ? "COBRA • SERIES" : "COBRA • MOVIES"); status(items.size() + " titles across enabled providers");
    ScrollView scroll = new ScrollView(this); LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); scroll.addView(list);
    Button search = action("SEARCH " + (series ? "SERIES" : "MOVIES")); search.setOnClickListener(v -> searchVod(items, series)); list.addView(search, new LinearLayout.LayoutParams(-1, dp(54)));
    for (VodItem item : items) addVodRow(list, item);
    if (items.isEmpty()) list.addView(text(failures.isEmpty() ? "No titles returned by enabled Xtream providers." : android.text.TextUtils.join("\n", failures), mTheme.muted, 15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, dp(140)));
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void addVodRow(LinearLayout list, VodItem item) {
    LiveSource source = sourceById(item.sourceId); String provider = source == null ? "Provider" : mFeatures.sourceIcon(source.id) + " " + source.name;
    Button row = action(item.title + "\\n     " + provider + "  •  " + item.category); row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
    row.setOnClickListener(v -> { if (item.series) openSeries(item); else playMovie(item); });
    row.setOnLongClickListener(v -> { toggleWatchlist(item); return true; }); list.addView(row, new LinearLayout.LayoutParams(-1, dp(70)));
  }

  private void searchVod(ArrayList<VodItem> items, boolean series) {
    EditText input = field("Search", InputType.TYPE_CLASS_TEXT); new AlertDialog.Builder(this).setTitle("Search").setView(input).setPositiveButton("SEARCH", (d, w) -> {
      String needle = input.getText().toString().trim().toLowerCase(Locale.US); ArrayList<VodItem> filtered = new ArrayList<>(); for (VodItem item : items) if (item.title.toLowerCase(Locale.US).contains(needle) || item.category.toLowerCase(Locale.US).contains(needle)) filtered.add(item); renderVodItems(filtered, series, new ArrayList<>());
    }).setNegativeButton("Cancel", null).show();
  }

  private void playMovie(VodItem item) {
    LiveSource source = sourceById(item.sourceId); if (source == null) return;
    String url = source.server + "/movie/" + encPath(source.username) + "/" + encPath(source.password) + "/" + encPath(item.id) + "." + item.extension;
    playVodUrl(item, url, "Movie");
  }

  private void openSeries(VodItem item) {
    LiveSource source = sourceById(item.sourceId); if (source == null) return; status("Loading episodes…");
    mIo.execute(() -> {
      ArrayList<VodItem> episodes = new ArrayList<>();
      try {
        JSONObject info = new JSONObject(httpGet(xtreamUrl(source, "get_series_info") + "&series_id=" + enc(item.id))); Object raw = info.opt("episodes");
        if (raw instanceof JSONObject) {
          JSONObject seasons = (JSONObject) raw; java.util.Iterator<String> keys = seasons.keys(); while (keys.hasNext()) { String season = keys.next(); JSONArray list = seasons.optJSONArray(season); if (list == null) continue; for (int i = 0; i < list.length(); i++) { JSONObject e = list.optJSONObject(i); if (e == null) continue; String eid = e.optString("id", ""); if (eid.isEmpty()) continue; String title = e.optString("title", "Episode " + (i + 1)); episodes.add(new VodItem(source.id, eid, "S" + season + " • " + title, item.title, "", sanitizeExtension(e.optString("container_extension", "mp4")), false)); } }
        } else if (raw instanceof JSONArray) {
          JSONArray list = (JSONArray) raw; for (int i = 0; i < list.length(); i++) { JSONObject e = list.optJSONObject(i); if (e == null) continue; String eid = e.optString("id", ""); if (!eid.isEmpty()) episodes.add(new VodItem(source.id, eid, e.optString("title", "Episode " + (i + 1)), item.title, "", sanitizeExtension(e.optString("container_extension", "mp4")), false)); }
        }
      } catch (Exception e) { runOnUiThread(() -> showError("Series", "Could not load episodes from this provider.")); return; }
      runOnUiThread(() -> {
        if (episodes.isEmpty()) { showError("Series", "Provider returned no episodes."); return; }
        String[] labels = new String[episodes.size()]; for (int i = 0; i < episodes.size(); i++) labels[i] = episodes.get(i).title;
        new AlertDialog.Builder(this).setTitle(item.title).setItems(labels, (d, which) -> { VodItem ep = episodes.get(which); String url = source.server + "/series/" + encPath(source.username) + "/" + encPath(source.password) + "/" + encPath(ep.id) + "." + ep.extension; playVodUrl(ep, url, item.title); }).setNegativeButton("Close", null).show();
      });
    });
  }

  private void playVodUrl(VodItem item, String url, String group) {
    mPlayingVodKey = item.sourceId + ":" + item.id; mPlayingVodTitle = item.title; mPendingResumeMs = mPrefs.getLong(mFeatures.profileKey("resume:" + mPlayingVodKey), 0L);
    Channel media = new Channel("vod:" + mPlayingVodKey, item.title, group + " • " + (sourceById(item.sourceId) == null ? "Provider" : sourceById(item.sourceId).name), "", item.icon, url, "", Collections.emptyMap()); playChannel(media);
  }

  private void saveVodProgress() {
    if (mPlayer == null || mPlayingVodKey.isEmpty()) return; try { long pos = mPlayer.getCurrentPosition(); long dur = mPlayer.getDuration(); SharedPreferences.Editor editor = mPrefs.edit(); if (dur > 0 && pos > dur * 0.92) editor.remove(mFeatures.profileKey("resume:" + mPlayingVodKey)); else if (pos > 5000) editor.putLong(mFeatures.profileKey("resume:" + mPlayingVodKey), pos); editor.apply(); } catch (Exception ignored) {}
  }

  private void toggleWatchlist(VodItem item) {
    String key = mFeatures.profileKey("watchlist"); JSONArray src; try { src = new JSONArray(mPrefs.getString(key, "[]")); } catch (Exception e) { src = new JSONArray(); }
    JSONArray dst = new JSONArray(); boolean found = false; for (int i = 0; i < src.length(); i++) { JSONObject o = src.optJSONObject(i); if (o == null) continue; if (item.sourceId.equals(o.optString("source")) && item.id.equals(o.optString("id"))) found = true; else dst.put(o); }
    if (!found) { JSONObject o = new JSONObject(); try { o.put("source", item.sourceId); o.put("id", item.id); o.put("title", item.title); o.put("category", item.category); o.put("extension", item.extension); o.put("series", item.series); dst.put(o); } catch (Exception ignored) {} }
    mPrefs.edit().putString(key, dst.toString()).apply(); toast(found ? "Removed from My List" : "Added to My List");
  }

  private void showWatchlist() {
    ArrayList<VodItem> items = new ArrayList<>(); try { JSONArray list = new JSONArray(mPrefs.getString(mFeatures.profileKey("watchlist"), "[]")); for (int i = 0; i < list.length(); i++) { JSONObject o = list.optJSONObject(i); if (o != null) items.add(new VodItem(o.optString("source"), o.optString("id"), o.optString("title"), o.optString("category"), "", o.optString("extension", "mp4"), o.optBoolean("series", false))); } } catch (Exception ignored) {}
    renderVodItems(items, false, new ArrayList<>()); mHeader.setText("COBRA • MY LIST");
  }

  private void showContinueWatching() {
    clearStage("COBRA • CONTINUE WATCHING"); status("Resume positions are stored per profile");
    mStage.addView(text("Continue Watching is populated as you play provider Movies and Series. Open Movies/Series to resume a title from its saved position.", mTheme.muted, 15, Gravity.CENTER), new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void showTrackChooser() {
    if (mPlayer == null) return; ArrayList<TrackChoice> choices = new ArrayList<>();
    for (Tracks.Group group : mPlayer.getCurrentTracks().getGroups()) {
      if (group.getType() != C.TRACK_TYPE_AUDIO && group.getType() != C.TRACK_TYPE_TEXT) continue;
      for (int i = 0; i < group.length; i++) if (group.isTrackSupported(i)) { Format f = group.getTrackFormat(i); String kind = group.getType() == C.TRACK_TYPE_AUDIO ? "Audio" : "Subtitles"; String label = kind + " • " + (f.label == null ? (f.language == null ? "Track " + (i + 1) : f.language) : f.label); choices.add(new TrackChoice(group, i, label)); }
    }
    if (choices.isEmpty()) { toast("No selectable audio/subtitle tracks"); return; }
    String[] labels = new String[choices.size()]; for (int i = 0; i < choices.size(); i++) labels[i] = choices.get(i).label;
    new AlertDialog.Builder(this).setTitle("Audio / Subtitles").setItems(labels, (d, which) -> { TrackChoice c = choices.get(which); TrackSelectionOverride override = new TrackSelectionOverride(c.group.getMediaTrackGroup(), c.index); mPlayer.setTrackSelectionParameters(mPlayer.getTrackSelectionParameters().buildUpon().setOverrideForType(override).build()); }).setNegativeButton("Close", null).show();
  }

  private void cycleAspectMode() {
    if (mPlayer == null) return; mAspectMode = (mAspectMode + 1) % 2; mPlayer.setVideoScalingMode(mAspectMode == 0 ? C.VIDEO_SCALING_MODE_SCALE_TO_FIT : C.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING); toast(mAspectMode == 0 ? "Fit" : "Crop / Fill");
  }

  private void openCastSettings() {
    try { startActivity(new Intent(Settings.ACTION_CAST_SETTINGS)); } catch (Exception e) { toast("No system Cast/route panel available on this device"); }
  }

  private void showProfiles() {
    clearStage("COBRA • PROFILES"); status("Local profiles • PIN and adult-category controls"); LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL);
    Button add = action("+ ADD PROFILE"); add.setOnClickListener(v -> createProfileDialog()); list.addView(add, new LinearLayout.LayoutParams(-1, dp(56)));
    JSONArray profiles = mFeatures.profiles(); for (int i = 0; i < profiles.length(); i++) { JSONObject p = profiles.optJSONObject(i); if (p == null) continue; String id = p.optString("id"); Button row = action((id.equals(mFeatures.activeProfileId()) ? "●  " : "○  ") + p.optString("name") + (p.optBoolean("adult_locked") ? "  •  Adult locked" : "")); row.setOnClickListener(v -> selectProfileDialog(p)); list.addView(row, new LinearLayout.LayoutParams(-1, dp(58))); }
    mStage.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void createProfileDialog() {
    LinearLayout form = new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(16), dp(8), dp(16), dp(4)); EditText name = field("Profile name", InputType.TYPE_CLASS_TEXT); EditText pin = field("PIN (optional)", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD); CheckBox adult = new CheckBox(this); adult.setText("Hide / lock adult categories"); adult.setTextColor(mTheme.text); adult.setChecked(true); form.addView(name, new LinearLayout.LayoutParams(-1, dp(54))); form.addView(pin, new LinearLayout.LayoutParams(-1, dp(54))); form.addView(adult, new LinearLayout.LayoutParams(-1, dp(54)));
    new AlertDialog.Builder(this).setTitle("Add profile").setView(form).setPositiveButton("ADD", (d, w) -> { String id = mFeatures.createProfile(name.getText().toString(), pin.getText().toString(), adult.isChecked()); if (!id.isEmpty()) { mFeatures.unlockAndSelectProfile(id, pin.getText().toString()); reloadProfileCollections(); showProfiles(); } }).setNegativeButton("Cancel", null).show();
  }

  private void selectProfileDialog(JSONObject profile) {
    EditText pin = field("PIN", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD); new AlertDialog.Builder(this).setTitle("Switch to " + profile.optString("name")).setView(profile.optString("pin_hash", "").isEmpty() ? null : pin).setPositiveButton("SWITCH", (d, w) -> { if (!mFeatures.unlockAndSelectProfile(profile.optString("id"), pin.getText().toString())) { showError("Profile", "Incorrect PIN"); return; } reloadProfileCollections(); showProfiles(); }).setNegativeButton("Cancel", null).show();
  }

  private void reloadProfileCollections() {
    mFavorites.clear(); Set<String> favorites = mPrefs.getStringSet(mFeatures.profileKey(FAVORITES), Collections.emptySet()); if (favorites != null) mFavorites.addAll(favorites); mRecents.clear(); try { JSONArray recent = new JSONArray(mPrefs.getString(mFeatures.profileKey(RECENTS), "[]")); for (int i = 0; i < recent.length(); i++) { String id = recent.optString(i, ""); if (!id.isEmpty()) mRecents.add(id); } } catch (Exception ignored) {}
  }

  private void showDiscover() {
    clearStage("COBRA • DISCOVER"); status("Infinity-owned living-room extras • fast module surface"); ScrollView scroll = new ScrollView(this); LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); scroll.addView(list);
    String[] labels = {"CONTINUE WATCHING", "MY LIST", "MY FILES", "WORLD CLOCK", "NEWS", "WEATHER", "RADIO", "PODCASTS", "AUDIOBOOKS", "RECIPES", "SPORTS", "NASA", "WORD OF THE DAY", "AMBIENT"};
    for (String label : labels) { Button b = action(label); b.setOnClickListener(v -> openDiscoverModule(label)); list.addView(b, new LinearLayout.LayoutParams(-1, dp(54))); }
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void openDiscoverModule(String label) {
    if ("CONTINUE WATCHING".equals(label)) { showContinueWatching(); return; } if ("MY LIST".equals(label)) { showWatchlist(); return; } if ("MY FILES".equals(label)) { openDocumentPicker(); return; } if ("WORLD CLOCK".equals(label)) { showWorldClock(); return; } if ("AMBIENT".equals(label)) { showAmbient(); return; }
    String url = "https://www.google.com/"; if ("NEWS".equals(label)) url = "https://news.google.com/"; else if ("WEATHER".equals(label)) url = "https://forecast.weather.gov/"; else if ("RADIO".equals(label)) url = "https://www.radio-browser.info/"; else if ("PODCASTS".equals(label)) url = "https://podcasts.apple.com/us/browse"; else if ("AUDIOBOOKS".equals(label)) url = "https://librivox.org/"; else if ("RECIPES".equals(label)) url = "https://www.themealdb.com/"; else if ("SPORTS".equals(label)) url = "https://www.espn.com/"; else if ("NASA".equals(label)) url = "https://apod.nasa.gov/apod/"; else if ("WORD OF THE DAY".equals(label)) url = "https://www.merriam-webster.com/word-of-the-day"; showWebModule(label, url);
  }

  private void showWebModule(String title, String url) {
    clearStage("COBRA • " + title); status("Web module • Back returns to Discover"); WebView web = new WebView(this); web.setWebViewClient(new WebViewClient()); web.getSettings().setJavaScriptEnabled(false); web.getSettings().setDomStorageEnabled(false); web.loadUrl(url); mStage.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void openDocumentPicker() {
    Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT); intent.addCategory(Intent.CATEGORY_OPENABLE); intent.setType("*/*"); intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"video/*", "audio/*"}); intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION); startActivityForResult(intent, REQUEST_LOCAL_MEDIA);
  }

  private void showWorldClock() {
    clearStage("COBRA • WORLD CLOCK"); status("Current time zones"); LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); String[] zones = {"America/Detroit", "America/New_York", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Dubai", "Asia/Tokyo", "Australia/Sydney"}; for (String zone : zones) { SimpleDateFormat f = new SimpleDateFormat("EEE h:mm a", Locale.US); f.setTimeZone(TimeZone.getTimeZone(zone)); list.addView(text(zone.replace('_', ' ') + "   " + f.format(new Date()), mTheme.text, 16, Gravity.LEFT | Gravity.CENTER_VERTICAL), new LinearLayout.LayoutParams(-1, dp(52))); } mStage.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));
  }

  private void showAmbient() {
    clearStage("COBRA • AMBIENT"); status("Press Back to leave Ambient"); TextView ambient = text("∞\\n\\nINFINITY COBRA\\n\\n" + new SimpleDateFormat("h:mm a", Locale.US).format(new Date()), mTheme.muted, 28, Gravity.CENTER); ambient.setBackgroundColor(Color.BLACK); mStage.addView(ambient, new LinearLayout.LayoutParams(-1, 0, 1));
  }

'''


def source_phase(source: Path, receipt: Path) -> None:
    source = source.resolve()
    for path in HELPERS:
        if not path.is_file():
            raise FileNotFoundError(path)
    base.source_phase(source, receipt)

    gradle = source / GRADLE
    manifest = source / MANIFEST
    install = source / INSTALL
    live = source / LIVE_ACTIVITY

    text = gradle.read_text(encoding="utf-8")
    text = once(text, f"versionCode {base.VERSION_CODE}", f"versionCode {VERSION_CODE}", "Candidate 2 versionCode")
    text = once(text, f'versionName "{base.RELEASE}"', f'versionName "{RELEASE}"', "Candidate 2 versionName")
    gradle.write_text(text, encoding="utf-8")

    for src, rel in HELPERS.items():
        target = source / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(src.read_bytes())

    text = install.read_text(encoding="utf-8")
    anchor = "                  src/InfinityLiveActivity.java\n"
    addition = (
        "                  src/InfinityCobraFeatureRuntime.java\n"
        "                  src/InfinityCobraRecordingService.java\n"
        "                  src/InfinityCobraReminderReceiver.java\n"
        "                  src/InfinityCobraBootReceiver.java\n"
    )
    if "src/InfinityCobraFeatureRuntime.java" not in text:
        text = once(text, anchor, anchor + addition, "Candidate 2 helper Java install")
    install.write_text(text, encoding="utf-8")

    text = manifest.read_text(encoding="utf-8")
    permission_anchor = '<uses-permission android:name="android.permission.INTERNET" />\n'
    permissions = (
        '<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />\n'
        '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />\n'
        '<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\n'
        '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\n'
    )
    if 'android.permission.FOREGROUND_SERVICE_DATA_SYNC' not in text:
        text = once(text, permission_anchor, permission_anchor + permissions, "Candidate 2 DVR permissions")
    components = '''        <service
            android:name=".InfinityCobraRecordingService"
            android:exported="false"
            android:foregroundServiceType="dataSync" />
        <receiver android:name=".InfinityCobraReminderReceiver" android:exported="false" />
        <receiver android:name=".InfinityCobraBootReceiver" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
            </intent-filter>
        </receiver>

'''
    if 'android:name=".InfinityCobraRecordingService"' not in text:
        text = once(text, '        <receiver android:name=".XBMCBroadcastReceiver"\n', components + '        <receiver android:name=".XBMCBroadcastReceiver"\n', "Candidate 2 manifest components")
    manifest.write_text(text, encoding="utf-8")

    java = patch_activity(live.read_text(encoding="utf-8"))
    live.write_text(java, encoding="utf-8")

    verify_source(source)
    data = json.loads(receipt.read_text(encoding="utf-8"))
    data.update({
        "release": RELEASE,
        "version_code": VERSION_CODE,
        "cobra_runtime": "full-feature-v2",
        "multi_provider": True,
        "multiview_max_feeds": 4,
        "simultaneous_audio_owners": 1,
        "dvr_foreground_service": True,
        "dvr_hls_segments": True,
        "record_from_guide": True,
        "programme_reminders": True,
        "catchup_archive": True,
        "vod_movies": True,
        "vod_series": True,
        "continue_watching": True,
        "profiles_parental": True,
        "my_files": True,
        "cast_route_handoff": True,
        "health_center_redacted_bridge": True,
        "theme_zip_updatable": True,
        "kodi_application_player_changed": False,
        "kodi_renderer_changed": False,
        "runtime_tested": False,
    })
    files = data.setdefault("files", {})
    for rel in (GRADLE, MANIFEST, INSTALL, LIVE_ACTIVITY, *HELPERS.values()):
        files.setdefault(str(rel), {})["after"] = sha(source / rel)
    receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Infinity Cobra Full Feature Candidate 2 installed in source tree")


def verify_source(source: Path) -> None:
    source = source.resolve()
    gradle = (source / GRADLE).read_text(encoding="utf-8")
    manifest = (source / MANIFEST).read_text(encoding="utf-8")
    install = (source / INSTALL).read_text(encoding="utf-8")
    java = (source / LIVE_ACTIVITY).read_text(encoding="utf-8")
    if f"versionCode {VERSION_CODE}" not in gradle or f'versionName "{RELEASE}"' not in gradle:
        raise RuntimeError("Candidate 2 identity missing")
    if manifest.count('<category android:name="android.intent.category.LAUNCHER" />') != 1 or "InfinityLiveLauncher" in manifest:
        raise RuntimeError("Candidate 2 must preserve one launcher")
    for needle in (
        'android:name=".InfinityCobraRecordingService"',
        'android.permission.FOREGROUND_SERVICE_DATA_SYNC',
        'android.permission.RECEIVE_BOOT_COMPLETED',
    ):
        if needle not in manifest:
            raise RuntimeError("Candidate 2 manifest contract missing: " + needle)
    for name in ("InfinityCobraFeatureRuntime", "InfinityCobraRecordingService", "InfinityCobraReminderReceiver", "InfinityCobraBootReceiver"):
        if f"src/{name}.java" not in install or not (source / SRC / f"{name}.java.in").is_file():
            raise RuntimeError("Candidate 2 helper missing: " + name)
    required = (
        "showMovies()", "showSeries()", "showRecordings()", "showDiscover()", "showProfiles()",
        "get_vod_streams", "get_series_info", "get_series_categories", "get_vod_categories",
        "parseXmlTvPrograms", "scheduleRecording", "addReminder", "playCatchup", "timeshift.php",
        "4 screens", "openMultiView(List<Channel>", "setMultiAudio", "mFeatures.profileKey(FAVORITES)",
        "showTrackChooser", "TrackSelectionOverride", "VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING",
        "setBufferDurationsMs(15000, 180000", "Settings.ACTION_CAST_SETTINGS", "ACTION_OPEN_DOCUMENT",
        "mFeatures.writeHealth", "InfinityCobraFeatureRuntime", "InfinityCobraRecordingService",
        ".kodi/addons/script.infinity.cobra.theme/resources/cobra-theme.json",
    )
    for needle in required:
        if needle not in java:
            raise RuntimeError("Candidate 2 live contract missing: " + needle)
    forbidden = ("CobraTV_", "com.cobratv", "libmpv", "android.media.MediaPlayer", "new MediaPlayer(")
    combined = java + "\n" + "\n".join((source / rel).read_text(encoding="utf-8") for rel in HELPERS.values())
    for needle in forbidden:
        if needle in combined:
            raise RuntimeError("Forbidden copied/legacy owner: " + needle)
    if "redact(" not in (source / (SRC / "InfinityCobraFeatureRuntime.java.in")).read_text(encoding="utf-8"):
        raise RuntimeError("Health redaction missing")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("source"); p.add_argument("--source", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-source"); p.add_argument("--source", type=Path, required=True)
    p = sub.add_parser("apk"); p.add_argument("--input", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-apk"); p.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "source": source_phase(args.source, args.receipt)
    elif args.cmd == "verify-source": verify_source(args.source); print("PASS: Cobra Full Feature Candidate 2 source verification")
    elif args.cmd == "apk": configure_deep(); deep.apk_phase(args.input, args.output, args.receipt)
    else: configure_deep(); deep.verify_apk(args.apk); print("PASS: Cobra Full Feature Candidate 2 APK branding verification")


if __name__ == "__main__":
    main()
