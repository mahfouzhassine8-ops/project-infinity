#!/usr/bin/env python3
"""Cobra 2103151 player / recent / Multi-View polish.

Android presentation-shell only. Applied after the locked 2103150 transform.
Keeps Kodi/native libraries untouched while adding successful Recently Played,
play/pause, wider/custom display transforms, cleaner chrome, and a category-
driven Multi-View picker that keeps the current stream alive.
"""
from __future__ import annotations

import argparse
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


def patch(java: str) -> str:
    state_anchor = '  private String mCobraTransferKey = "";\n'
    if java.count(state_anchor) != 1:
        raise RuntimeError("2103150 transfer state anchor missing")
    java = java.replace(
        state_anchor,
        state_anchor
        + '  private static final String COBRA_LAST_GOOD_CHANNEL = "cobra_last_good_channel";\n'
        + '  private static final String COBRA_CUSTOM_ASPECT_X = "cobra_custom_aspect_x";\n'
        + '  private static final String COBRA_CUSTOM_ASPECT_Y = "cobra_custom_aspect_y";\n'
        + '  private FrameLayout mCobraMultiPicker;\n'
        + '  private ExoPlayer mCobraCarryPlayer;\n'
        + '  private Channel mCobraCarryChannel;\n'
        + '  private boolean mCobraMultiPickerAdding = false;\n',
        1,
    )

    preview_block = r"""  private void markCobraPlaybackReady(Channel channel) {
    if (channel == null || channel.id == null || channel.id.isEmpty()) return;
    mPrefs.edit().putString(COBRA_LAST_GOOD_CHANNEL, channel.id).apply();
    addRecent(channel);
  }

  private Channel cobraLastGoodChannel(ArrayList<Channel> visible) {
    if (visible == null || visible.isEmpty()) return null;
    String saved = mPrefs.getString(COBRA_LAST_GOOD_CHANNEL, "");
    if (!saved.isEmpty()) {
      Channel found = findChannel(saved);
      if (found != null && visible.contains(found)) return found;
    }
    for (String id : mRecents) {
      Channel found = findChannel(id);
      if (found != null && visible.contains(found)) return found;
    }
    return null;
  }

  private void toggleCobraPreviewPlayPause() {
    ExoPlayer player = mCobraPreviewPlayer;
    if (player == null) return;
    if (player.isPlaying() || player.getPlayWhenReady()) player.pause();
    else player.play();
    updateCobraPreviewPlayPause();
  }

  private void updateCobraPreviewPlayPause() {
    if (mCobraPreviewHost == null) return;
    View view = mCobraPreviewHost.findViewWithTag("cobra_preview_play_pause");
    if (!(view instanceof Button)) return;
    boolean playing = mCobraPreviewPlayer != null
        && (mCobraPreviewPlayer.isPlaying() || mCobraPreviewPlayer.getPlayWhenReady());
    ((Button) view).setText(playing ? "❚❚" : "▶");
    view.setContentDescription(playing ? "Pause" : "Play");
  }

  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {
    stopCobraPreview();
    FrameLayout host = new FrameLayout(this);
    mCobraPreviewHost = host;
    host.setTag("cobra_preview_host");
    host.setBackground(surface(Color.BLACK, 22, Color.rgb(34, 44, 56), 1));
    host.setClickable(true);

    mCobraPreviewTexture = new TextureView(this);
    host.addView(mCobraPreviewTexture, new FrameLayout.LayoutParams(-1, -1));

    TextView badge = text(channel == null ? "SELECT A CHANNEL" : "LIVE  •  " + channel.name,
        Color.WHITE, 11, Gravity.RIGHT | Gravity.CENTER_VERTICAL);
    badge.setTag("cobra_preview_label");
    badge.setPadding(dp(10), dp(3), dp(10), dp(3));
    badge.setBackground(surface(Color.argb(180, 3, 7, 12), 13,
        Color.argb(60, 255, 255, 255), 1));
    FrameLayout.LayoutParams badgeP =
        new FrameLayout.LayoutParams(-2, dp(32), Gravity.TOP | Gravity.RIGHT);
    badgeP.setMargins(dp(10), dp(10), dp(10), 0);
    host.addView(badge, badgeP);

    if (channel != null) {
      LinearLayout controls = new LinearLayout(this);
      controls.setGravity(Gravity.CENTER);
      controls.setPadding(dp(8), dp(5), dp(8), dp(5));
      controls.setBackgroundColor(Color.argb(188, 3, 7, 12));
      Button fullscreen = cobraVideoButton("⛶", "Fullscreen");
      Button playPause = cobraVideoButton("❚❚", "Pause");
      playPause.setTag("cobra_preview_play_pause");
      Button favorite = cobraVideoButton(
          mFavorites.contains(channel.id) ? "♥" : "♡", "Favorite");
      favorite.setTag("cobra_preview_favorite");
      Button captions = cobraVideoButton("CC", "Closed captions");
      Button volume = cobraVideoButton(mCobraPreviewMuted ? "MUTE" : "VOL", "Volume");
      Button more = cobraVideoButton("⋮", "More channel actions");

      fullscreen.setOnClickListener(v -> {
        Channel active = mGuidePreviewChannel;
        if (active != null) promoteCobraPreviewToFullscreen(active);
      });
      playPause.setOnClickListener(v -> toggleCobraPreviewPlayPause());
      favorite.setOnClickListener(v -> {
        Channel active = mGuidePreviewChannel;
        if (active == null) return;
        toggleFavorite(active);
        favorite.setText(mFavorites.contains(active.id) ? "♥" : "♡");
      });
      captions.setOnClickListener(v -> toggleCobraPreviewCaptions());
      volume.setOnClickListener(v -> {
        toggleCobraPreviewMute();
        volume.setText(mCobraPreviewMuted ? "MUTE" : "VOL");
      });
      more.setOnClickListener(v -> {
        Channel active = mGuidePreviewChannel;
        if (active != null) showCobraChannelActions(active);
      });

      for (Button button :
          new Button[]{fullscreen, playPause, favorite, captions, volume, more})
        controls.addView(button, new LinearLayout.LayoutParams(0, dp(44), 1));
      host.addView(controls, new FrameLayout.LayoutParams(-1, dp(54), Gravity.BOTTOM));
    }

    host.setOnClickListener(v -> {
      Channel active = mGuidePreviewChannel;
      if (active != null) promoteCobraPreviewToFullscreen(active);
    });
    if (channel != null) host.post(() -> {
      String key = cobraChannelKey(channel);
      if (mCobraTransferPlayer != null && key.equals(mCobraTransferKey)) {
        ExoPlayer transfer = mCobraTransferPlayer;
        mCobraTransferPlayer = null;
        mCobraTransferKey = "";
        mCobraPreviewPlayer = transfer;
        try { transfer.setVideoTextureView(mCobraPreviewTexture); } catch (Exception ignored) {}
        transfer.setVolume(mCobraPreviewMuted ? 0f : 1f);
        setCobraPreviewLabel("LIVE PREVIEW  •  " + channel.name);
        updateCobraPreviewPlayPause();
        updateCobraPreviewDetails();
      } else {
        releaseCobraTransferPlayer();
        startCobraPreview(channel);
      }
    });
    return host;
  }"""
    java = replace_method(
        java, "  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {",
        preview_block)

    start_preview = r"""  private void startCobraPreview(Channel channel) {
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
          if (playbackState == Player.STATE_BUFFERING) {
            setCobraPreviewLabel("BUFFERING  •  " + channel.name);
          } else if (playbackState == Player.STATE_READY) {
            setCobraPreviewLabel("LIVE  •  " + channel.name);
            markCobraPlaybackReady(channel);
          }
          updateCobraPreviewPlayPause();
        }

        @Override public void onIsPlayingChanged(boolean isPlaying) {
          if (preview == mCobraPreviewPlayer) updateCobraPreviewPlayPause();
        }

        @Override public void onPlayerError(PlaybackException error) {
          if (preview != mCobraPreviewPlayer) return;
          if (!mCobraPreviewTriedFallback && channel.fallbackUrl != null
              && !channel.fallbackUrl.isEmpty()
              && !channel.fallbackUrl.equals(channel.primaryUrl)) {
            mCobraPreviewTriedFallback = true;
            preview.setMediaItem(mediaItem(channel.fallbackUrl));
            preview.prepare();
            preview.play();
            return;
          }
          setCobraPreviewLabel("PREVIEW ERROR  •  " + channel.name);
          updateCobraPreviewPlayPause();
        }
      });
      preview.setVolume(mCobraPreviewMuted ? 0f : 1f);
      preview.setMediaItem(mediaItem(channel.primaryUrl));
      preview.prepare();
      preview.play();
      updateCobraPreviewPlayPause();
    } catch (Exception error) {
      setCobraPreviewLabel("PREVIEW UNAVAILABLE  •  " + channel.name);
      updateCobraPreviewPlayPause();
    }
  }"""
    java = replace_method(java, "  private void startCobraPreview(Channel channel) {", start_preview)

    ensure = r"""  private void ensureCobraPreviewSelection(ArrayList<Channel> channels) {
    if (mGuidePreviewChannel != null || channels == null || channels.isEmpty()) return;
    Channel recent = cobraLastGoodChannel(channels);
    mGuidePreviewChannel = recent == null ? channels.get(0) : recent;
    mGuidePreviewKey = sourceIdForChannel(mGuidePreviewChannel) + "|" + mGuidePreviewChannel.id;
    mGuidePreviewArmed = false;
  }"""
    java = replace_method(java, "  private void ensureCobraPreviewSelection(ArrayList<Channel> channels) {", ensure)

    channels_for_view = r"""  private ArrayList<Channel> cobraChannelsForCurrentView() {
    String requested = mCategory == null ? "ALL" : mCategory;
    boolean favorites = "FAVORITES".equals(requested);
    boolean recent = "RECENT".equals(requested);
    boolean custom = requested.startsWith("MY:");
    if (favorites || recent || custom) mCategory = "ALL";
    ArrayList<Channel> source = new ArrayList<>(
        recent ? filteredChannels(false, true) : filteredChannels(favorites, false));
    mCategory = requested;
    ArrayList<Channel> result = new ArrayList<>();
    String customName = custom ? requested.substring(3) : "";
    for (Channel channel : source) {
      if (isCobraHidden(channel)) continue;
      if (custom && !customName.equals(cobraCustomGroup(channel))) continue;
      result.add(channel);
    }
    return result;
  }"""
    java = replace_method(java, "  private ArrayList<Channel> cobraChannelsForCurrentView() {",
                          channels_for_view)

    tv_hub = r"""  private void showCobraTvHub() {
    stopCobraPreview();
    clearStage("COBRA • TV");
    mCobraInternalScreen = "root";
    String previousCategory = mCategory;
    mCategory = "ALL";
    ArrayList<Channel> all = cobraChannelsForCurrentView();
    mCategory = previousCategory;
    ensureCobraPreviewSelection(all);

    if (mUi.guidePreviewPlayer) {
      mStage.addView(cobraPreviewPanel(mGuidePreviewChannel, true),
          new LinearLayout.LayoutParams(-1, dp(cobraPreviewHeight(false))));
      mStage.addView(cobraPreviewDetails(mGuidePreviewChannel),
          new LinearLayout.LayoutParams(-1, dp(82)));
    }

    TextView heading = text("YOUR CHANNELS", cobraThemeColor("text", mTheme.text), 16,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    heading.setTypeface(null, Typeface.BOLD);
    mStage.addView(heading, new LinearLayout.LayoutParams(-1, dp(42)));

    LinearLayout tabs = new LinearLayout(this);
    tabs.setGravity(Gravity.CENTER_VERTICAL);
    Button favorites = action("★  FAVORITES");
    Button recent = action("◷  RECENTLY PLAYED");
    favorites.setOnClickListener(v -> selectCobraCategory("FAVORITES"));
    recent.setOnClickListener(v -> selectCobraCategory("RECENT"));
    tabs.addView(favorites, new LinearLayout.LayoutParams(0, dp(54), 1));
    LinearLayout.LayoutParams recentP = new LinearLayout.LayoutParams(0, dp(54), 1);
    recentP.leftMargin = dp(8);
    tabs.addView(recent, recentP);
    mStage.addView(tabs, new LinearLayout.LayoutParams(-1, dp(58)));

    Button allButton = action("ALL CHANNELS");
    allButton.setOnClickListener(v -> selectCobraCategory("ALL"));
    mStage.addView(allButton, new LinearLayout.LayoutParams(-1, dp(56)));

    TextView categoriesTitle = text("CATEGORIES",
        cobraThemeColor("muted", mTheme.muted), 11,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    categoriesTitle.setLetterSpacing(.12f);
    mStage.addView(categoriesTitle, new LinearLayout.LayoutParams(-1, dp(38)));

    ScrollView scroll = new ScrollView(this);
    LinearLayout list = new LinearLayout(this);
    list.setOrientation(LinearLayout.VERTICAL);
    ArrayList<String> categories = categoriesForCurrentChannels();
    for (String group : categories) {
      if (group == null || group.isEmpty() || "ALL".equals(group)) continue;
      final String category = group;
      Button button = action(category);
      button.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
      button.setOnClickListener(v -> selectCobraCategory(category));
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(58));
      p.bottomMargin = dp(5);
      list.addView(button, p);
    }
    for (String group : cobraCustomGroups()) {
      final String value = "MY:" + group;
      Button button = action("MY GROUP  •  " + group);
      button.setOnClickListener(v -> selectCobraCategory(value));
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(58));
      p.bottomMargin = dp(5);
      list.addView(button, p);
    }
    scroll.addView(list);
    mStage.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
  }"""
    java = replace_method(java, "  private void showCobraTvHub() {", tv_hub)

    # Failed taps must not pollute Recently Played. Only STATE_READY does.
    for sig in ("  private void playChannel(Channel channel) {",
                "  private void promoteCobraPreviewToFullscreen(Channel channel) {"):
        a, b = span(java, sig)
        block = java[a:b]
        block = block.replace("    addRecent(channel);\n", "", 1)
        java = java[:a] + block + java[b:]

    # Direct fullscreen playback also marks a successful recent channel.
    a, b = span(java, "  private void startSinglePlayer(String url) {")
    block = java[a:b]
    marker = '          else if (playbackState == Player.STATE_READY) {\n'
    if marker not in block:
        raise RuntimeError("fullscreen ready-state anchor missing")
    block = block.replace(
        marker,
        marker + '            if (mPlaying != null) markCobraPlaybackReady(mPlaying);\n'
        + '            updateCobraPlayerPlayPause();\n',
        1,
    )
    java = java[:a] + block + java[b:]

    # Session-reuse fullscreen listener gets the same success semantics.
    a, b = span(java, "  private void promoteCobraPreviewToFullscreen(Channel channel) {")
    block = java[a:b]
    old = '        else if (playbackState == Player.STATE_READY) state.setText("LIVE");\n'
    if old in block:
        block = block.replace(
            old,
            '        else if (playbackState == Player.STATE_READY) {\n'
            '          state.setText("LIVE");\n'
            '          if (mPlaying != null) markCobraPlaybackReady(mPlaying);\n'
            '          updateCobraPlayerPlayPause();\n'
            '        }\n',
            1,
        )
    java = java[:a] + block + java[b:]

    aspect_label = r"""  private String cobraAspectLabel(int mode) {
    switch (mode) {
      case 1: return "Crop / Fill";
      case 2: return "16:9";
      case 3: return "4:3";
      case 4: return "Wide 1.10x";
      case 5: return "Wide 1.25x";
      case 6: return "Wide 1.40x";
      case 7: return "Short + Wide";
      case 8: return "Zoom 1.25x";
      case 9: return "Zoom 1.50x";
      case 10: return "Zoom 2.00x";
      case 11: return "Custom Width / Height";
      default: return "Best Fit";
    }
  }"""
    java = replace_method(java, "  private String cobraAspectLabel(int mode) {", aspect_label)

    aspect_picker = r"""  private void showCobraAspectPicker() {
    if (mPlayer == null || mPlayerTexture == null) return;
    final String[] labels = {
        "Best Fit", "Crop / Fill", "16:9", "4:3",
        "Wide 1.10x", "Wide 1.25x", "Wide 1.40x", "Short + Wide",
        "Zoom 1.25x", "Zoom 1.50x", "Zoom 2.00x", "Custom Width / Height…"
    };
    int checked = Math.max(0, Math.min(mAspectMode, labels.length - 1));
    new AlertDialog.Builder(this)
        .setTitle("Aspect / Display")
        .setSingleChoiceItems(labels, checked, (dialog, which) -> {
          mAspectMode = which;
          mPrefs.edit().putInt(COBRA_ASPECT_MODE, which).apply();
          applyCobraAspectTransform();
          dialog.dismiss();
          if (which == 11) showCobraCustomAspectEditor();
          else toast("Display mode • " + cobraAspectLabel(which));
        })
        .setNegativeButton("Cancel", null)
        .show();
  }"""
    java = replace_method(java, "  private void showCobraAspectPicker() {", aspect_picker)

    custom_and_cycle = r"""  private void showCobraCustomAspectEditor() {
    if (mPlayerTexture == null) return;
    float x = Math.max(.55f, Math.min(1.80f,
        mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X, 1.15f)));
    float y = Math.max(.55f, Math.min(1.80f,
        mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y, .92f)));
    final String[] actions = {
        "Width +5%", "Width -5%", "Height +5%", "Height -5%",
        "Wider + Shorter", "Reset 100% × 100%"
    };
    new AlertDialog.Builder(this)
        .setTitle(String.format(Locale.US, "Custom Display • W %.0f%%  H %.0f%%", x * 100f, y * 100f))
        .setItems(actions, (dialog, which) -> {
          float nextX = x, nextY = y;
          if (which == 0) nextX += .05f;
          else if (which == 1) nextX -= .05f;
          else if (which == 2) nextY += .05f;
          else if (which == 3) nextY -= .05f;
          else if (which == 4) { nextX += .05f; nextY -= .05f; }
          else { nextX = 1f; nextY = 1f; }
          nextX = Math.max(.55f, Math.min(1.80f, nextX));
          nextY = Math.max(.55f, Math.min(1.80f, nextY));
          mAspectMode = 11;
          mPrefs.edit().putInt(COBRA_ASPECT_MODE, 11)
              .putFloat(COBRA_CUSTOM_ASPECT_X, nextX)
              .putFloat(COBRA_CUSTOM_ASPECT_Y, nextY).apply();
          applyCobraAspectTransform();
          mMain.post(() -> showCobraCustomAspectEditor());
        })
        .setNegativeButton("Done", null)
        .show();
  }

  private void cycleAspectMode() { showCobraAspectPicker(); }"""
    java = replace_method(java, "  private void cycleAspectMode() {", custom_and_cycle)

    aspect_transform = r"""  private void applyCobraAspectTransform() {
    if (mPlayerTexture == null) return;
    mPlayerTexture.setTranslationX(0f);
    mPlayerTexture.setTranslationY(0f);
    mPlayerTexture.setScaleX(1f);
    mPlayerTexture.setScaleY(1f);
    if (mPlayer != null)
      mPlayer.setVideoScalingMode(C.VIDEO_SCALING_MODE_SCALE_TO_FIT);
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
      float zoom = videoAspect > viewAspect
          ? videoAspect / viewAspect : viewAspect / videoAspect;
      zoom = Math.max(1f, Math.min(zoom, 4f));
      sx = zoom; sy = zoom;
    } else if (mAspectMode == 2) {
      sx = Math.max(.55f, Math.min((16f / 9f) / videoAspect, 2.2f));
    } else if (mAspectMode == 3) {
      sx = Math.max(.55f, Math.min((4f / 3f) / videoAspect, 2.2f));
    } else if (mAspectMode == 4) sx = 1.10f;
    else if (mAspectMode == 5) sx = 1.25f;
    else if (mAspectMode == 6) sx = 1.40f;
    else if (mAspectMode == 7) { sx = 1.24f; sy = .84f; }
    else if (mAspectMode == 8) sx = sy = 1.25f;
    else if (mAspectMode == 9) sx = sy = 1.50f;
    else if (mAspectMode == 10) sx = sy = 2.00f;
    else if (mAspectMode == 11) {
      sx = Math.max(.55f, Math.min(1.80f,
          mPrefs.getFloat(COBRA_CUSTOM_ASPECT_X, 1.15f)));
      sy = Math.max(.55f, Math.min(1.80f,
          mPrefs.getFloat(COBRA_CUSTOM_ASPECT_Y, .92f)));
    }

    mPlayerTexture.setPivotX(viewWidth / 2f);
    mPlayerTexture.setPivotY(viewHeight / 2f);
    mPlayerTexture.setScaleX(sx);
    mPlayerTexture.setScaleY(sy);
  }"""
    java = replace_method(java, "  private void applyCobraAspectTransform() {", aspect_transform)

    player_overlay = r"""  private void updateCobraPlayerPlayPause() {
    if (mPlayerOverlay == null) return;
    View view = mPlayerOverlay.findViewWithTag("cobra_player_play_pause");
    if (!(view instanceof Button)) return;
    boolean playing = mPlayer != null && (mPlayer.isPlaying() || mPlayer.getPlayWhenReady());
    ((Button) view).setText(playing ? "❚❚" : "▶");
    view.setContentDescription(playing ? "Pause" : "Play");
  }

  private void toggleCobraPlayerPlayPause() {
    if (mPlayer == null) return;
    if (mPlayer.isPlaying() || mPlayer.getPlayWhenReady()) mPlayer.pause();
    else mPlayer.play();
    updateCobraPlayerPlayPause();
    showPlayerChromeTemporarily();
  }

  private void openPlayerOverlay(Channel channel) {
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mPlayerOverlay = new FrameLayout(this);
    mPlayerOverlay.setBackgroundColor(Color.BLACK);
    mPlayerOverlay.setFocusable(true);
    mPlayerOverlay.setFocusableInTouchMode(true);

    mPlayerTexture = new TextureView(this);
    mAspectMode = mPrefs.getInt(COBRA_ASPECT_MODE, 0);
    mPlayerOverlay.addView(mPlayerTexture, new FrameLayout.LayoutParams(-1, -1));

    mPlayerChrome = new LinearLayout(this);
    mPlayerChrome.setOrientation(LinearLayout.VERTICAL);
    mPlayerChrome.setPadding(dp(8), dp(4), dp(8), dp(5));
    mPlayerChrome.setBackgroundColor(Color.argb(206, 2, 6, 11));

    LinearLayout infoRow = new LinearLayout(this);
    infoRow.setGravity(Gravity.CENTER_VERTICAL);
    TextView info = text(channel.name + "  •  " + providerBadge(channel),
        Color.WHITE, isPortrait() ? 12 : 14, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    info.setTypeface(null, Typeface.BOLD);
    Button aspect = cobraVideoButton("▣", "Aspect / Display");
    aspect.setOnClickListener(v -> showCobraAspectPicker());
    TextView state = text("CONNECTING", Color.WHITE, 10,
        Gravity.RIGHT | Gravity.CENTER_VERTICAL);
    state.setTag("player_state");
    state.setBackgroundColor(Color.TRANSPARENT);
    infoRow.addView(info, new LinearLayout.LayoutParams(0, dp(36), 1));
    infoRow.addView(aspect, new LinearLayout.LayoutParams(dp(48), dp(36)));
    infoRow.addView(state, new LinearLayout.LayoutParams(dp(86), dp(36)));
    mPlayerChrome.addView(infoRow, new LinearLayout.LayoutParams(-1, dp(38)));

    LinearLayout controls = new LinearLayout(this);
    controls.setGravity(Gravity.CENTER);
    Button prev = cobraVideoButton("◀", "Previous channel");
    Button favorite = cobraVideoButton("★", "Favorite");
    Button playPause = cobraVideoButton("▶", "Play");
    playPause.setTag("cobra_player_play_pause");
    Button multi = cobraVideoButton("▦", "Multi-View");
    Button next = cobraVideoButton("▶|", "Next channel");
    Button settings = cobraVideoButton("⚙", "Player settings");

    prev.setOnClickListener(v -> stepChannel(-1));
    favorite.setOnClickListener(v -> toggleFavorite(channel));
    playPause.setOnClickListener(v -> toggleCobraPlayerPlayPause());
    multi.setOnClickListener(v -> beginMultiView());
    next.setOnClickListener(v -> stepChannel(1));
    settings.setOnClickListener(v -> showPlayerSettingsDrawer());

    for (Button button : new Button[]{prev, favorite, playPause, multi, next, settings}) {
      button.setMinWidth(0);
      button.setMinimumWidth(0);
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(42), 1);
      p.leftMargin = dp(2);
      p.rightMargin = dp(2);
      controls.addView(button, p);
    }
    mPlayerChrome.addView(controls, new LinearLayout.LayoutParams(-1, dp(46)));

    FrameLayout.LayoutParams chromeParams =
        new FrameLayout.LayoutParams(-1, dp(86), Gravity.BOTTOM);
    chromeParams.setMargins(dp(8), 0, dp(8), dp(8));
    mPlayerOverlay.addView(mPlayerChrome, chromeParams);
    mPlayerOverlay.setOnClickListener(v -> {
      if (!closePlayerSettingsDrawer() && mCobraMultiPicker == null)
        togglePlayerChrome();
    });
    mPlayerOverlay.setOnKeyListener((v, keyCode, event) -> {
      if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
      if (keyCode == KeyEvent.KEYCODE_DPAD_UP || keyCode == KeyEvent.KEYCODE_DPAD_DOWN
          || keyCode == KeyEvent.KEYCODE_DPAD_CENTER) showPlayerChromeTemporarily();
      return false;
    });
    decor.addView(mPlayerOverlay, new FrameLayout.LayoutParams(-1, -1));
    updateCobraPlayerPlayPause();
    scheduleChromeHide();
    mFeatures.writeHealth("player", sourceIdForChannel(channel), channel.id,
        "connecting", "", mPlaybackRetryCount, 0, -1,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
  }"""
    java = replace_method(java, "  private void openPlayerOverlay(Channel channel) {", player_overlay)

    # Keep Record available, but move it to the secondary player settings sheet.
    a, b = span(java, "  private void showPlayerSettingsDrawer() {")
    block = java[a:b]
    if '    Button guide = action("Guide");\n' in block and 'Button record = action("Record / Stop Recording");' not in block:
        block = block.replace(
            '    Button guide = action("Guide");\n',
            '    Button record = action("Record / Stop Recording");\n'
            '    Button guide = action("Guide");\n',
            1,
        )
        listener_anchor = '    cast.setOnClickListener(v -> openCastSettings());\n'
        if listener_anchor in block:
            block = block.replace(
                listener_anchor,
                listener_anchor
                + '    record.setOnClickListener(v -> { if (mPlaying != null) toggleRecording(mPlaying); });\n',
                1,
            )
        style_anchor = '    for (Button chromeButton : new Button[]{audio, fit, cast, source, guide, multi, close}) {\n'
        if style_anchor in block:
            block = block.replace(
                style_anchor,
                '    record.setTextColor(Color.WHITE);\n'
                '    record.setBackground(surface(Color.rgb(20, 28, 38), 18, Color.rgb(55, 68, 82), 1));\n'
                '    LinearLayout.LayoutParams recordParams = new LinearLayout.LayoutParams(-1, dp(mTheme.touchTarget));\n'
                '    recordParams.bottomMargin = dp(8);\n'
                '    drawer.addView(record, recordParams);\n'
                + style_anchor,
                1,
            )
    java = java[:a] + block + java[b:]

    multi_helpers = r"""  private ArrayList<Channel> cobraMultiChannels(String filter) {
    ArrayList<Channel> out = new ArrayList<>();
    if ("RECENT".equals(filter)) {
      for (String id : mRecents) {
        Channel channel = findChannel(id);
        if (channel != null && !isCobraHidden(channel)
            && (mPlaying == null || !channel.id.equals(mPlaying.id)))
          out.add(channel);
      }
      return out;
    }
    for (Channel channel : mChannels) {
      if (channel == null || isCobraHidden(channel)) continue;
      if (mFeatures.looksAdult(channel.group) || mFeatures.looksAdult(channel.name)) continue;
      if (mPlaying != null && channel.id.equals(mPlaying.id)) continue;
      if ("FAVORITES".equals(filter) && !mFavorites.contains(channel.id)) continue;
      if (filter != null && filter.startsWith("GROUP:")
          && !filter.substring(6).equals(channel.group)) continue;
      out.add(channel);
    }
    return out;
  }

  private void restoreCobraVideoAfterMultiPicker() {
    if (mPlayerTexture == null) return;
    mPlayerTexture.animate().cancel();
    mPlayerTexture.setTranslationX(0f);
    mPlayerTexture.setTranslationY(0f);
    applyCobraAspectTransform();
    if (mPlayerChrome != null) showPlayerChromeTemporarily();
  }

  private boolean closeCobraMultiPicker(boolean keepVideoDocked) {
    if (mCobraMultiPicker == null) return false;
    android.view.ViewParent parent = mCobraMultiPicker.getParent();
    if (parent instanceof android.view.ViewGroup)
      ((android.view.ViewGroup) parent).removeView(mCobraMultiPicker);
    mCobraMultiPicker = null;
    if (!keepVideoDocked && !mCobraMultiPickerAdding) restoreCobraVideoAfterMultiPicker();
    mCobraMultiPickerAdding = false;
    return true;
  }

  private android.widget.BaseAdapter cobraMultiChannelAdapter(
      final ArrayList<Channel> channels) {
    return new android.widget.BaseAdapter() {
      @Override public int getCount() { return channels.size(); }
      @Override public Channel getItem(int position) { return channels.get(position); }
      @Override public long getItemId(int position) { return position; }
      @Override public View getView(
          int position, View convertView, android.view.ViewGroup parent) {
        Button row = convertView instanceof Button ? (Button) convertView : action("");
        Channel channel = channels.get(position);
        ProgramPair pair = programFor(channel);
        String now = pair != null && pair.now != null && !pair.now.isEmpty()
            ? pair.now : channel.group;
        row.setText(channel.name + "\n" + now);
        row.setTextSize(12);
        row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
        row.setAllCaps(false);
        row.setFocusable(!cobraTouchFirstDevice());
        row.setOnClickListener(v -> selectCobraMultiChannel(channel));
        row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(64)));
        return row;
      }
    };
  }

  private void renderCobraMultiPicker(String filter) {
    if (mCobraMultiPicker == null) return;
    View raw = mCobraMultiPicker.findViewWithTag("cobra_multi_picker_list");
    if (!(raw instanceof android.widget.ListView)) return;
    android.widget.ListView list = (android.widget.ListView) raw;
    if ("CATEGORIES".equals(filter)) {
      ArrayList<String> groups = categoriesForCurrentChannels();
      list.setAdapter(new android.widget.BaseAdapter() {
        @Override public int getCount() { return groups.size(); }
        @Override public String getItem(int position) { return groups.get(position); }
        @Override public long getItemId(int position) { return position; }
        @Override public View getView(
            int position, View convertView, android.view.ViewGroup parent) {
          Button row = convertView instanceof Button ? (Button) convertView : action("");
          String group = groups.get(position);
          row.setText(group);
          row.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
          row.setOnClickListener(v -> renderCobraMultiPicker("GROUP:" + group));
          row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(58)));
          return row;
        }
      });
      return;
    }
    ArrayList<Channel> channels = cobraMultiChannels(filter);
    list.setAdapter(cobraMultiChannelAdapter(channels));
  }

  private void showCobraMultiPicker(boolean adding) {
    android.view.ViewGroup parent = adding ? mMultiOverlay : mPlayerOverlay;
    if (parent == null) return;
    closeCobraMultiPicker(false);
    mCobraMultiPickerAdding = adding;

    if (!adding && mPlayerTexture != null) {
      if (mPlayerChrome != null) mPlayerChrome.setVisibility(View.GONE);
      int width = getResources().getDisplayMetrics().widthPixels;
      int height = getResources().getDisplayMetrics().heightPixels;
      if (isPortrait()) {
        mPlayerTexture.animate().scaleX(.94f).scaleY(.50f)
            .translationY(-height * .21f).setDuration(180L).start();
      } else {
        mPlayerTexture.animate().scaleX(.58f).scaleY(.88f)
            .translationX(-width * .20f).setDuration(180L).start();
      }
    }

    FrameLayout panel = new FrameLayout(this);
    panel.setTag("cobra_multi_picker");
    mCobraMultiPicker = panel;
    panel.setBackground(surface(Color.rgb(7, 12, 18), 24, Color.rgb(48, 62, 78), 1));

    LinearLayout content = new LinearLayout(this);
    content.setOrientation(LinearLayout.VERTICAL);
    content.setPadding(dp(12), dp(10), dp(12), dp(12));
    panel.addView(content, new FrameLayout.LayoutParams(-1, -1));

    LinearLayout header = new LinearLayout(this);
    header.setGravity(Gravity.CENTER_VERTICAL);
    TextView title = text(adding ? "ADD MULTI-VIEW SCREEN" : "MULTI-VIEW • PICK SECOND SCREEN",
        Color.WHITE, 14, Gravity.LEFT | Gravity.CENTER_VERTICAL);
    title.setTypeface(null, Typeface.BOLD);
    Button cancel = cobraVideoButton("✕", "Cancel");
    cancel.setOnClickListener(v -> closeCobraMultiPicker(false));
    header.addView(title, new LinearLayout.LayoutParams(0, dp(42), 1));
    header.addView(cancel, new LinearLayout.LayoutParams(dp(46), dp(40)));
    content.addView(header, new LinearLayout.LayoutParams(-1, dp(44)));

    LinearLayout tabs = new LinearLayout(this);
    Button favorites = action("★");
    Button recent = action("RECENT");
    Button all = action("ALL");
    Button categories = action("CATEGORIES");
    favorites.setContentDescription("Favorites");
    recent.setContentDescription("Recently Played");
    favorites.setOnClickListener(v -> renderCobraMultiPicker("FAVORITES"));
    recent.setOnClickListener(v -> renderCobraMultiPicker("RECENT"));
    all.setOnClickListener(v -> renderCobraMultiPicker("ALL"));
    categories.setOnClickListener(v -> renderCobraMultiPicker("CATEGORIES"));
    tabs.addView(favorites, new LinearLayout.LayoutParams(0, dp(46), .65f));
    tabs.addView(recent, new LinearLayout.LayoutParams(0, dp(46), 1f));
    tabs.addView(all, new LinearLayout.LayoutParams(0, dp(46), .65f));
    tabs.addView(categories, new LinearLayout.LayoutParams(0, dp(46), 1.15f));
    content.addView(tabs, new LinearLayout.LayoutParams(-1, dp(50)));

    android.widget.ListView list = new android.widget.ListView(this);
    list.setTag("cobra_multi_picker_list");
    list.setDividerHeight(dp(3));
    list.setSelector(android.R.color.transparent);
    list.setFastScrollEnabled(true);
    content.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));

    FrameLayout.LayoutParams params;
    if (adding) {
      int width = isPortrait() ? -1 : Math.min(dp(420),
          Math.round(getResources().getDisplayMetrics().widthPixels * .42f));
      int height = isPortrait()
          ? Math.round(getResources().getDisplayMetrics().heightPixels * .56f) : -1;
      params = new FrameLayout.LayoutParams(width, height,
          isPortrait() ? Gravity.BOTTOM : Gravity.RIGHT);
      params.setMargins(dp(8), dp(8), dp(8), dp(8));
    } else if (isPortrait()) {
      params = new FrameLayout.LayoutParams(-1,
          Math.round(getResources().getDisplayMetrics().heightPixels * .55f),
          Gravity.BOTTOM);
      params.setMargins(dp(8), 0, dp(8), dp(8));
    } else {
      params = new FrameLayout.LayoutParams(
          Math.round(getResources().getDisplayMetrics().widthPixels * .42f),
          -1, Gravity.RIGHT);
      params.setMargins(0, dp(8), dp(8), dp(8));
    }
    parent.addView(panel, params);
    panel.bringToFront();

    if (!mRecents.isEmpty()) renderCobraMultiPicker("RECENT");
    else if (!mFavorites.isEmpty()) renderCobraMultiPicker("FAVORITES");
    else renderCobraMultiPicker("ALL");
  }

  private void selectCobraMultiChannel(Channel channel) {
    if (channel == null) return;
    if (mCobraMultiPickerAdding && mMultiChannels != null) {
      ArrayList<Channel> next = new ArrayList<>();
      for (Channel existing : mMultiChannels)
        if (existing != null) next.add(existing);
      for (Channel existing : next)
        if (existing.id.equals(channel.id)) { toast("That channel is already open"); return; }
      if (next.size() >= 4) { toast("Multi-View supports up to 4 screens"); return; }
      next.add(channel);
      closeCobraMultiPicker(true);
      mReflowingMulti = true;
      releaseMulti();
      mReflowingMulti = false;
      openMultiView(next);
      return;
    }

    Channel current = mPlaying;
    if (current == null || mPlayer == null) {
      closeCobraMultiPicker(false);
      toast("Play a channel first, then open Multi-View");
      return;
    }
    ArrayList<Channel> chosen = new ArrayList<>();
    chosen.add(current);
    chosen.add(channel);
    closeCobraMultiPicker(true);
    openMultiView(chosen);
  }"""

    begin_multi = multi_helpers + r"""
  private void beginMultiView() {
    if (mMultiOverlay != null && mMultiChannels != null) {
      if (mMultiChannels.length >= 4) {
        toast("Multi-View already has 4 screens");
        return;
      }
      showCobraMultiPicker(true);
      return;
    }
    if (mPlayer == null || mPlaying == null) {
      toast("Play a channel first, then tap Multi-View");
      return;
    }
    if (mChannels.size() < 2) {
      toast("Multi-View needs another available channel");
      return;
    }
    showCobraMultiPicker(false);
  }"""
    java = replace_method(java, "  private void beginMultiView() {", begin_multi)

    choose_multi = r"""  private void chooseMultiChannels(int count) {
    if (mPlayer != null && mPlaying != null) {
      showCobraMultiPicker(false);
      return;
    }
    toast("Play a channel first, then tap Multi-View");
  }"""
    java = replace_method(java, "  private void chooseMultiChannels(int count) {", choose_multi)

    open_multi = r"""  private void openMultiView(List<Channel> channels) {
    if (channels == null || channels.size() < 2) {
      toast("Choose at least two channels");
      return;
    }

    mCobraCarryPlayer = null;
    mCobraCarryChannel = null;
    if (mPlayer != null && mPlaying != null
        && channels.get(0) != null && channels.get(0).id.equals(mPlaying.id)) {
      mCobraCarryPlayer = mPlayer;
      mCobraCarryChannel = mPlaying;
      mPlayer = null;
      try { if (mPlayerTexture != null) mCobraCarryPlayer.clearVideoTextureView(mPlayerTexture); }
      catch (Exception ignored) {}
      if (mPlayerOverlay != null) try {
        ((FrameLayout) getWindow().getDecorView()).removeView(mPlayerOverlay);
      } catch (Exception ignored) {}
      mPlayerOverlay = null;
      mPlayerTexture = null;
      mPlayerChrome = null;
      mPlaying = null;
      mPlayingIndex = -1;
    } else {
      closePlayer();
    }

    releaseMulti();
    int count = Math.min(4, Math.max(2, channels.size()));
    mMultiChannels = channels.subList(0, count).toArray(new Channel[0]);
    mMultiPlayers = new ExoPlayer[count];
    mMultiTextures = new TextureView[count];
    mAudioTile = 0;

    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mMultiOverlay = new FrameLayout(this);
    mMultiOverlay.setBackgroundColor(Color.BLACK);
    LinearLayout stack = new LinearLayout(this);
    stack.setOrientation(LinearLayout.VERTICAL);
    mMultiOverlay.addView(stack, new FrameLayout.LayoutParams(-1, -1));

    if (isPortrait()) {
      for (int i = 0; i < count; i++)
        stack.addView(createMultiTile(i), new LinearLayout.LayoutParams(-1, 0, 1));
    } else {
      int rows = count <= 2 ? 1 : 2;
      for (int rowIndex = 0; rowIndex < rows; rowIndex++) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        int start = rowIndex * 2;
        int end = Math.min(count, start + (rows == 1 ? count : 2));
        for (int i = start; i < end; i++)
          row.addView(createMultiTile(i), new LinearLayout.LayoutParams(0, -1, 1));
        stack.addView(row, new LinearLayout.LayoutParams(-1, 0, 1));
      }
    }

    mMultiChrome = new LinearLayout(this);
    mMultiChrome.setGravity(Gravity.CENTER);
    mMultiChrome.setPadding(dp(7), dp(4), dp(7), dp(4));
    mMultiChrome.setBackground(surface(Color.argb(218, 4, 8, 13), 18,
        Color.rgb(48, 62, 78), 1));

    for (int i = 0; i < count; i++) {
      final int index = i;
      Button audio = action("A" + (i + 1));
      audio.setContentDescription("Use audio from screen " + (i + 1));
      audio.setOnClickListener(v -> {
        setMultiAudio(index);
        showMultiChromeTemporarily();
      });
      mMultiChrome.addView(audio, new LinearLayout.LayoutParams(0, dp(44), 1));
    }

    if (count < 4) {
      Button add = action("+ ADD");
      add.setOnClickListener(v -> showCobraMultiPicker(true));
      mMultiChrome.addView(add, new LinearLayout.LayoutParams(0, dp(44), 1.2f));
    }
    Button single = action("SINGLE");
    single.setOnClickListener(v -> multiToSingle());
    mMultiChrome.addView(single, new LinearLayout.LayoutParams(0, dp(44), 1.15f));
    Button remove = action("REMOVE");
    remove.setOnClickListener(v -> removeSelectedMultiTile());
    mMultiChrome.addView(remove, new LinearLayout.LayoutParams(0, dp(44), 1.15f));
    Button exit = action("✕");
    exit.setOnClickListener(v -> releaseMulti());
    mMultiChrome.addView(exit, new LinearLayout.LayoutParams(dp(54), dp(44)));

    FrameLayout.LayoutParams chrome =
        new FrameLayout.LayoutParams(-1, dp(54), Gravity.BOTTOM);
    chrome.setMargins(dp(10), 0, dp(10), dp(10));
    mMultiOverlay.addView(mMultiChrome, chrome);
    mMultiOverlay.setOnClickListener(v -> showMultiChromeTemporarily());

    decor.addView(mMultiOverlay, new FrameLayout.LayoutParams(-1, -1));
    setMultiAudio(0);
    configureCobraPip(false);
    showMultiChromeTemporarily();
    if (mDeviceBridge != null) mDeviceBridge.onPlaybackChanged("multiview-start");
    mFeatures.writeHealth("multiview", "", "", "ready", "", 0, count, 0,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
  }"""
    java = replace_method(java, "  private void openMultiView(List<Channel> channels) {", open_multi)

    create_tile = r"""  private FrameLayout createMultiTile(int index) {
    FrameLayout tile = new FrameLayout(this);
    tile.setFocusable(true);
    tile.setFocusableInTouchMode(false);
    TextureView texture = new TextureView(this);
    mMultiTextures[index] = texture;
    tile.addView(texture, new FrameLayout.LayoutParams(-1, -1));

    TextView label = text(mMultiChannels[index].name
        + (index == 0 ? "  •  AUDIO" : ""), Color.WHITE, 12,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    label.setTag("multi_label_" + index);
    label.setPadding(dp(10), dp(4), dp(10), dp(4));
    label.setBackgroundColor(Color.argb(168, 2, 6, 11));
    tile.addView(label, new FrameLayout.LayoutParams(-1, dp(40), Gravity.BOTTOM));
    tile.setOnClickListener(v -> {
      setMultiAudio(index);
      showMultiChromeTemporarily();
    });
    tile.setOnFocusChangeListener((v, focused) -> {
      if (focused) setMultiAudio(index);
    });

    if (index == 0 && mCobraCarryPlayer != null && mCobraCarryChannel != null
        && mCobraCarryChannel.id.equals(mMultiChannels[index].id)) {
      ExoPlayer carry = mCobraCarryPlayer;
      mCobraCarryPlayer = null;
      mCobraCarryChannel = null;
      mMultiPlayers[index] = carry;
      try { carry.setVideoTextureView(texture); } catch (Exception ignored) {}
      carry.setVolume(1f);
      return tile;
    }

    try {
      ExoPlayer player = buildPlayer(texture, mMultiChannels[index], index == 0);
      mMultiPlayers[index] = player;
      player.addListener(new Player.Listener() {
        @Override public void onPlayerError(PlaybackException error) {
          label.setText(mMultiChannels[index].name + "  •  ERROR");
        }
      });
      player.setMediaItem(mediaItem(mMultiChannels[index].primaryUrl));
      player.prepare();
      player.play();
    } catch (Exception error) {
      label.setText(mMultiChannels[index].name + "  •  ERROR");
    }
    return tile;
  }"""
    java = replace_method(java, "  private FrameLayout createMultiTile(int index) {", create_tile)

    # Back dismisses the Multi-View picker before leaving player or Multi-View.
    a, b = span(java, "  @Override\n  public void onBackPressed() {")
    back = java[a:b]
    brace = back.find("{")
    insert = '\n    if (mCobraMultiPicker != null) { closeCobraMultiPicker(false); return; }'
    back = back[:brace + 1] + insert + back[brace + 1:]
    java = java[:a] + back + java[b:]

    # Cleanup transient picker/carry player on destruction.
    a, b = span(java, "  protected void onDestroy() {")
    destroy = java[a:b]
    brace = destroy.find("{")
    addition = (
        '\n    closeCobraMultiPicker(true);'
        '\n    if (mCobraCarryPlayer != null) {'
        '\n      try { mCobraCarryPlayer.stop(); } catch (Exception ignored) {}'
        '\n      try { mCobraCarryPlayer.release(); } catch (Exception ignored) {}'
        '\n      mCobraCarryPlayer = null; mCobraCarryChannel = null;'
        '\n    }'
    )
    destroy = destroy[:brace + 1] + addition + destroy[brace + 1:]
    java = java[:a] + destroy + java[b:]

    return java


def verify(java: str) -> None:
    required = (
        'COBRA_LAST_GOOD_CHANNEL = "cobra_last_good_channel"',
        'RECENTLY PLAYED',
        'markCobraPlaybackReady(channel)',
        'cobra_preview_play_pause',
        'toggleCobraPreviewPlayPause()',
        'Wide 1.40x',
        'Short + Wide',
        'Custom Width / Height',
        'COBRA_CUSTOM_ASPECT_X',
        'COBRA_CUSTOM_ASPECT_Y',
        'cobra_player_play_pause',
        'new FrameLayout.LayoutParams(-1, dp(86), Gravity.BOTTOM)',
        'MULTI-VIEW • PICK SECOND SCREEN',
        'renderCobraMultiPicker("FAVORITES")',
        'renderCobraMultiPicker("RECENT")',
        'renderCobraMultiPicker("CATEGORIES")',
        'mCobraCarryPlayer',
        'carry.setVideoTextureView(texture)',
        'Button add = action("+ ADD")',
        'Play a channel first, then tap Multi-View',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("2103151 player/multiview contract missing: " + token)
    if 'Not enough channels for ' in java:
        raise RuntimeError("legacy filtered Multi-View failure remains")
    if java.count("  private void beginMultiView() {") != 1:
        raise RuntimeError("beginMultiView duplicate")
    if java.count("  private void showCobraAspectPicker() {") != 1:
        raise RuntimeError("aspect picker duplicate")
    if java.count("  private void openPlayerOverlay(Channel channel) {") != 1:
        raise RuntimeError("player overlay duplicate")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra 2103151 recent/play-pause/aspect/Multi-View polish applied")


if __name__ == "__main__":
    main()
