#!/usr/bin/env python3
"""Cobra 2103152 player reboot + lock + continuity polish.

Presentation-shell only, layered strictly on the locked 2103151 source stack.
Reboots the fullscreen player layout, adds a real input-blocking player lock,
keeps guide-preview playback alive across Cobra navigation, and preserves every
existing Multi-View player when adding/reflowing screens. Kodi/native playback,
renderer, rotation, lifecycle and Infinity handoff ownership remain untouched.
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


def remove_preview_stop(text: str, signature: str) -> str:
    a, b = span(text, signature)
    block = text[a:b]
    block = block.replace("    stopCobraPreview();\n", "", 1)
    block = block.replace("    stopCobraPreview(); ", "    ", 1)
    return text[:a] + block + text[b:]


def patch(java: str) -> str:
    state_anchor = '  private boolean mCobraMultiPickerAdding = false;\n'
    if java.count(state_anchor) != 1:
        raise RuntimeError("2103151 state anchor missing")
    java = java.replace(
        state_anchor,
        state_anchor
        + '  private String mCobraPreviewSessionKey = "";\n'
        + '  private boolean mCobraPlayerLocked = false;\n'
        + '  private FrameLayout mCobraPlayerLockOverlay;\n'
        + '  private Button mCobraPlayerUnlockButton;\n'
        + '  private final Runnable mHideCobraUnlockButton = () -> {\n'
        + '    if (mCobraPlayerUnlockButton != null && mCobraPlayerLocked)\n'
        + '      mCobraPlayerUnlockButton.setVisibility(View.GONE);\n'
        + '  };\n'
        + '  private ExoPlayer[] mCobraMultiCarryPlayers;\n'
        + '  private Channel[] mCobraMultiCarryChannels;\n'
        + '  private String mCobraMultiCarryAudioChannelId = "";\n'
        + '  private int mCobraMultiReplaceIndex = -1;\n',
        1,
    )

    # Keep the same preview player alive while the guide/category UI is rebuilt.
    for sig in (
        "  private void showCobraTvHub() {",
        "  private void showCobraMobileView() {",
        "  private void showGuideGrid() {",
        "  private void showGuideCompact() {",
        "  private void showGuideCards() {",
        "  private void showGuideFocus() {",
    ):
        java = remove_preview_stop(java, sig)

    preview_panel = r'''  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {
    final ExoPlayer existingPlayer = mCobraPreviewPlayer;
    final TextureView existingTexture = mCobraPreviewTexture;
    final String existingKey = mCobraPreviewSessionKey;

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
    badge.setBackground(surface(Color.argb(176, 3, 7, 12), 13,
        Color.argb(58, 255, 255, 255), 1));
    FrameLayout.LayoutParams badgeP =
        new FrameLayout.LayoutParams(-2, dp(32), Gravity.TOP | Gravity.RIGHT);
    badgeP.setMargins(dp(10), dp(10), dp(10), 0);
    host.addView(badge, badgeP);

    if (channel != null) {
      LinearLayout controls = new LinearLayout(this);
      controls.setGravity(Gravity.CENTER);
      controls.setPadding(dp(8), dp(5), dp(8), dp(5));
      controls.setBackgroundColor(Color.argb(180, 3, 7, 12));
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
      for (Button button : new Button[]{fullscreen, playPause, favorite, captions, volume, more})
        controls.addView(button, new LinearLayout.LayoutParams(0, dp(44), 1));
      host.addView(controls, new FrameLayout.LayoutParams(-1, dp(54), Gravity.BOTTOM));
    }

    host.setOnClickListener(v -> {
      Channel active = mGuidePreviewChannel;
      if (active != null) promoteCobraPreviewToFullscreen(active);
    });

    if (channel != null) host.post(() -> {
      String key = cobraChannelKey(channel);
      if (existingPlayer != null && existingPlayer == mCobraPreviewPlayer
          && key.equals(existingKey)) {
        try { if (existingTexture != null) existingPlayer.clearVideoTextureView(existingTexture); }
        catch (Exception ignored) {}
        try { existingPlayer.setVideoTextureView(mCobraPreviewTexture); }
        catch (Exception ignored) {}
        existingPlayer.setVolume(mCobraPreviewMuted ? 0f : 1f);
        mCobraPreviewSessionKey = key;
        setCobraPreviewLabel("LIVE  •  " + channel.name);
        updateCobraPreviewPlayPause();
        updateCobraPreviewDetails();
      } else if (mCobraTransferPlayer != null && key.equals(mCobraTransferKey)) {
        ExoPlayer transfer = mCobraTransferPlayer;
        mCobraTransferPlayer = null;
        mCobraTransferKey = "";
        mCobraPreviewPlayer = transfer;
        mCobraPreviewSessionKey = key;
        try { transfer.setVideoTextureView(mCobraPreviewTexture); } catch (Exception ignored) {}
        transfer.setVolume(mCobraPreviewMuted ? 0f : 1f);
        setCobraPreviewLabel("LIVE  •  " + channel.name);
        updateCobraPreviewPlayPause();
        updateCobraPreviewDetails();
      } else {
        releaseCobraTransferPlayer();
        startCobraPreview(channel);
      }
    });
    return host;
  }'''
    java = replace_method(java, "  private FrameLayout cobraPreviewPanel(Channel channel, boolean guide) {",
                          preview_panel)

    a, b = span(java, "  private void startCobraPreview(Channel channel) {")
    block = java[a:b]
    anchor = "      mCobraPreviewPlayer = preview;\n"
    if anchor not in block:
        raise RuntimeError("preview player assignment missing")
    block = block.replace(anchor, anchor + "      mCobraPreviewSessionKey = cobraChannelKey(channel);\n", 1)
    java = java[:a] + block + java[b:]

    a, b = span(java, "  private void promoteCobraPreviewToFullscreen(Channel channel) {")
    block = java[a:b]
    anchor = "    mCobraPreviewPlayer = null;\n"
    if anchor in block:
        block = block.replace(anchor, anchor + '    mCobraPreviewSessionKey = "";\n', 1)
    java = java[:a] + block + java[b:]

    player_helpers = r'''  private void showCobraPlayerUnlockAffordance() {
    if (!mCobraPlayerLocked || mCobraPlayerUnlockButton == null) return;
    mCobraPlayerUnlockButton.setVisibility(View.VISIBLE);
    mCobraPlayerUnlockButton.setAlpha(0f);
    mCobraPlayerUnlockButton.setScaleX(.94f);
    mCobraPlayerUnlockButton.setScaleY(.94f);
    mCobraPlayerUnlockButton.animate().alpha(1f).scaleX(1f).scaleY(1f)
        .setDuration(150L).start();
    mMain.removeCallbacks(mHideCobraUnlockButton);
    mMain.postDelayed(mHideCobraUnlockButton, 3000L);
  }

  private void ensureCobraPlayerLockOverlay() {
    if (mPlayerOverlay == null) return;
    if (mCobraPlayerLockOverlay != null) {
      mCobraPlayerLockOverlay.bringToFront();
      return;
    }
    FrameLayout guard = new FrameLayout(this);
    guard.setClickable(true);
    guard.setFocusable(true);
    guard.setFocusableInTouchMode(true);
    guard.setBackgroundColor(Color.TRANSPARENT);
    guard.setContentDescription("Player controls locked");
    mCobraPlayerLockOverlay = guard;

    Button unlock = cobraVideoButton("🔒  CONTROLS LOCKED", "Unlock player controls");
    unlock.setTextSize(12);
    unlock.setTag("cobra_player_unlock");
    unlock.setOnClickListener(v -> unlockCobraPlayer());
    mCobraPlayerUnlockButton = unlock;
    FrameLayout.LayoutParams unlockP = new FrameLayout.LayoutParams(
        dp(214), dp(50), Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
    unlockP.setMargins(0, 0, 0, dp(34));
    guard.addView(unlock, unlockP);
    guard.setOnClickListener(v -> showCobraPlayerUnlockAffordance());
    guard.setOnKeyListener((v, keyCode, event) -> {
      if (event.getAction() == KeyEvent.ACTION_DOWN) {
        showCobraPlayerUnlockAffordance();
        return true;
      }
      return false;
    });
    mPlayerOverlay.addView(guard, new FrameLayout.LayoutParams(-1, -1));
    guard.bringToFront();
    guard.requestFocus();
  }

  private void lockCobraPlayer() {
    if (mPlayerOverlay == null) return;
    mCobraPlayerLocked = true;
    if (mPlayerChrome != null) mPlayerChrome.setVisibility(View.GONE);
    ensureCobraPlayerLockOverlay();
    showCobraPlayerUnlockAffordance();
  }

  private void unlockCobraPlayer() {
    clearCobraPlayerLockState(true);
  }

  private void clearCobraPlayerLockState(boolean revealChrome) {
    mCobraPlayerLocked = false;
    mMain.removeCallbacks(mHideCobraUnlockButton);
    if (mCobraPlayerLockOverlay != null) {
      android.view.ViewParent parent = mCobraPlayerLockOverlay.getParent();
      if (parent instanceof android.view.ViewGroup)
        ((android.view.ViewGroup) parent).removeView(mCobraPlayerLockOverlay);
    }
    mCobraPlayerLockOverlay = null;
    mCobraPlayerUnlockButton = null;
    if (revealChrome && mPlayerOverlay != null) showPlayerChromeTemporarily();
  }

  private String cobraPlayerNow(Channel channel) {
    ProgramPair pair = channel == null ? null : programFor(channel);
    if (pair != null && pair.now != null && !pair.now.isEmpty()) return pair.now;
    return channel == null ? "Live TV" : channel.group;
  }

  private String cobraPlayerNext(Channel channel) {
    ProgramPair pair = channel == null ? null : programFor(channel);
    if (pair != null && pair.next != null && !pair.next.isEmpty()) return "NEXT  •  " + pair.next;
    return providerBadge(channel);
  }

  private void toggleCobraPlayerPlayPause() {
    if (mPlayer == null || mCobraPlayerLocked) return;
    if (mPlayer.isPlaying() || mPlayer.getPlayWhenReady()) mPlayer.pause();
    else mPlayer.play();
    updateCobraPlayerPlayPause();
    showPlayerChromeTemporarily();
  }'''
    java = replace_method(java, "  private void toggleCobraPlayerPlayPause() {", player_helpers)

    player_overlay = r'''  private void openPlayerOverlay(Channel channel) {
    clearCobraPlayerLockState(false);
    FrameLayout decor = (FrameLayout) getWindow().getDecorView();
    mPlayerOverlay = new FrameLayout(this);
    mPlayerOverlay.setBackgroundColor(Color.BLACK);
    mPlayerOverlay.setFocusable(true);
    mPlayerOverlay.setFocusableInTouchMode(true);

    mPlayerTexture = new TextureView(this);
    mAspectMode = mPrefs.getInt(COBRA_ASPECT_MODE, 0);
    mPlayerOverlay.addView(mPlayerTexture, new FrameLayout.LayoutParams(-1, -1));

    mPlayerChrome = new LinearLayout(this);
    mPlayerChrome.setTag("cobra_player_reboot_chrome");
    mPlayerChrome.setOrientation(LinearLayout.VERTICAL);
    mPlayerChrome.setPadding(dp(14), dp(18), dp(14), dp(8));
    android.graphics.drawable.GradientDrawable playerFade =
        new android.graphics.drawable.GradientDrawable(
            android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
            new int[]{Color.TRANSPARENT, Color.argb(150, 0, 0, 0), Color.argb(242, 0, 0, 0)});
    mPlayerChrome.setBackground(playerFade);

    LinearLayout infoRow = new LinearLayout(this);
    infoRow.setGravity(Gravity.BOTTOM | Gravity.CENTER_VERTICAL);
    LinearLayout copy = new LinearLayout(this);
    copy.setOrientation(LinearLayout.VERTICAL);
    copy.setGravity(Gravity.BOTTOM);
    TextView channelName = text(channel.name, Color.WHITE, isPortrait() ? 15 : 17,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    channelName.setTypeface(null, Typeface.BOLD);
    TextView now = text(cobraPlayerNow(channel), Color.WHITE, isPortrait() ? 12 : 13,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    TextView next = text(cobraPlayerNext(channel), Color.rgb(190, 200, 212), 10,
        Gravity.LEFT | Gravity.CENTER_VERTICAL);
    copy.addView(channelName, new LinearLayout.LayoutParams(-1, dp(24)));
    copy.addView(now, new LinearLayout.LayoutParams(-1, dp(22)));
    copy.addView(next, new LinearLayout.LayoutParams(-1, dp(20)));

    TextView state = text("CONNECTING", Color.WHITE, 10, Gravity.CENTER);
    state.setTag("player_state");
    state.setPadding(dp(10), dp(3), dp(10), dp(3));
    state.setBackground(surface(Color.argb(180, 6, 10, 16), 13,
        Color.argb(70, 255, 255, 255), 1));
    infoRow.addView(copy, new LinearLayout.LayoutParams(0, dp(68), 1));
    LinearLayout.LayoutParams stateP = new LinearLayout.LayoutParams(dp(88), dp(34));
    stateP.leftMargin = dp(10);
    infoRow.addView(state, stateP);
    mPlayerChrome.addView(infoRow, new LinearLayout.LayoutParams(-1, dp(70)));

    LinearLayout controls = new LinearLayout(this);
    controls.setGravity(Gravity.CENTER);
    Button prev = cobraVideoButton("‹", "Previous channel");
    Button favorite = cobraVideoButton(mFavorites.contains(channel.id) ? "♥" : "♡", "Favorite");
    Button playPause = cobraVideoButton("▶", "Play or pause");
    playPause.setTag("cobra_player_play_pause");
    Button nextChannel = cobraVideoButton("›", "Next channel");
    Button aspect = cobraVideoButton("▣", "Aspect / Display");
    Button multi = cobraVideoButton("▦", "Multi-View");
    Button lock = cobraVideoButton("🔒", "Lock player controls");
    Button more = cobraVideoButton("⋮", "More player controls");

    prev.setOnClickListener(v -> stepChannel(-1));
    favorite.setOnClickListener(v -> {
      toggleFavorite(channel);
      favorite.setText(mFavorites.contains(channel.id) ? "♥" : "♡");
    });
    playPause.setOnClickListener(v -> toggleCobraPlayerPlayPause());
    nextChannel.setOnClickListener(v -> stepChannel(1));
    aspect.setOnClickListener(v -> showCobraAspectPicker());
    multi.setOnClickListener(v -> beginMultiView());
    lock.setOnClickListener(v -> lockCobraPlayer());
    more.setOnClickListener(v -> showPlayerSettingsDrawer());

    Button[] buttons = new Button[]{prev, favorite, playPause, nextChannel, aspect, multi, lock, more};
    for (Button button : buttons) {
      button.setMinWidth(0);
      button.setMinimumWidth(0);
      button.setBackground(surface(Color.argb(150, 12, 18, 26), 22,
          Color.argb(66, 255, 255, 255), 1));
      LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(44), 1);
      p.leftMargin = dp(2);
      p.rightMargin = dp(2);
      controls.addView(button, p);
    }
    playPause.setTextSize(16);
    mPlayerChrome.addView(controls, new LinearLayout.LayoutParams(-1, dp(50)));

    int chromeHeight = isPortrait() ? 158 : 140;
    FrameLayout.LayoutParams chromeP = new FrameLayout.LayoutParams(-1, dp(chromeHeight), Gravity.BOTTOM);
    mPlayerOverlay.addView(mPlayerChrome, chromeP);
    mPlayerOverlay.setOnClickListener(v -> {
      if (mCobraPlayerLocked) { showCobraPlayerUnlockAffordance(); return; }
      if (!closePlayerSettingsDrawer() && mCobraMultiPicker == null) togglePlayerChrome();
    });
    mPlayerOverlay.setOnKeyListener((v, keyCode, event) -> {
      if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
      if (mCobraPlayerLocked) { showCobraPlayerUnlockAffordance(); return true; }
      if (keyCode == KeyEvent.KEYCODE_DPAD_UP || keyCode == KeyEvent.KEYCODE_DPAD_DOWN
          || keyCode == KeyEvent.KEYCODE_DPAD_CENTER) showPlayerChromeTemporarily();
      return false;
    });
    decor.addView(mPlayerOverlay, new FrameLayout.LayoutParams(-1, -1));
    updateCobraPlayerPlayPause();
    playPause.requestFocus();
    scheduleChromeHide();
    mFeatures.writeHealth("player", sourceIdForChannel(channel), channel.id,
        "connecting", "", mPlaybackRetryCount, 0, -1,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
  }'''
    java = replace_method(java, "  private void openPlayerOverlay(Channel channel) {", player_overlay)

    # Lock takes precedence over Back and is hidden from PiP.
    a, b = span(java, "  @Override\n  public void onBackPressed() {")
    back = java[a:b]
    brace = back.find("{")
    back = back[:brace + 1] + (
        '\n    if (mCobraPlayerLocked && mPlayerOverlay != null) {'
        '\n      showCobraPlayerUnlockAffordance(); return;'
        '\n    }') + back[brace + 1:]
    java = java[:a] + back + java[b:]

    a, b = span(java, "  private void closePlayer() {")
    close = java[a:b]
    brace = close.find("{")
    close = close[:brace + 1] + "\n    clearCobraPlayerLockState(false);" + close[brace + 1:]
    java = java[:a] + close + java[b:]

    a, b = span(java, "  public void onPictureInPictureModeChanged(boolean inPictureInPictureMode, Configuration configuration) {")
    pip = java[a:b]
    anchor = "    mInPictureInPicture = inPictureInPictureMode;\n"
    if anchor not in pip:
        raise RuntimeError("PiP mode state anchor missing")
    pip = pip.replace(anchor, anchor
        + "    if (mCobraPlayerLockOverlay != null)\n"
        + "      mCobraPlayerLockOverlay.setVisibility(inPictureInPictureMode ? View.GONE\n"
        + "          : (mCobraPlayerLocked ? View.VISIBLE : View.GONE));\n", 1)
    java = java[:a] + pip + java[b:]

    # Session-preserving Multi-View reflow. Existing players are detached from old
    # textures and attached to the new tile geometry instead of stop/release/reload.
    multi_block = r'''  private void rebuildCobraMultiPreservingSessions(
      ArrayList<Channel> next, String releaseChannelId) {
    if (mMultiChannels == null || mMultiPlayers == null) return;
    mCobraMultiCarryPlayers = mMultiPlayers;
    mCobraMultiCarryChannels = mMultiChannels;
    if (mAudioTile >= 0 && mAudioTile < mMultiChannels.length
        && mMultiChannels[mAudioTile] != null)
      mCobraMultiCarryAudioChannelId = mMultiChannels[mAudioTile].id;
    else mCobraMultiCarryAudioChannelId = "";

    for (int i = 0; i < mCobraMultiCarryPlayers.length; i++) {
      ExoPlayer player = mCobraMultiCarryPlayers[i];
      if (player == null) continue;
      try {
        if (mMultiTextures != null && i < mMultiTextures.length && mMultiTextures[i] != null)
          player.clearVideoTextureView(mMultiTextures[i]);
      } catch (Exception ignored) {}
      if (releaseChannelId != null && !releaseChannelId.isEmpty()
          && mCobraMultiCarryChannels != null && i < mCobraMultiCarryChannels.length
          && mCobraMultiCarryChannels[i] != null
          && releaseChannelId.equals(mCobraMultiCarryChannels[i].id)) {
        try { player.stop(); } catch (Exception ignored) {}
        try { player.release(); } catch (Exception ignored) {}
        mCobraMultiCarryPlayers[i] = null;
      }
    }

    if (mMultiOverlay != null) {
      android.view.ViewParent parent = mMultiOverlay.getParent();
      if (parent instanceof android.view.ViewGroup)
        ((android.view.ViewGroup) parent).removeView(mMultiOverlay);
    }
    mMultiOverlay = null;
    mMultiChrome = null;
    mMain.removeCallbacks(mHideMultiChrome);
    mMultiPlayers = null;
    mMultiTextures = null;
    mMultiChannels = null;
    mReflowingMulti = true;
    openMultiView(next);
    mReflowingMulti = false;
  }

  private void addCobraMultiTileClean(Channel channel) {
    if (channel == null || mMultiChannels == null) return;
    ArrayList<Channel> next = new ArrayList<>();
    for (Channel existing : mMultiChannels) if (existing != null) next.add(existing);
    if (next.size() >= 4) { toast("Multi-View supports up to 4 screens"); return; }
    for (Channel existing : next)
      if (existing.id.equals(channel.id)) { toast("That channel is already open"); return; }
    next.add(channel);
    rebuildCobraMultiPreservingSessions(next, "");
  }

  private void replaceCobraMultiTileClean(int index, Channel channel) {
    if (channel == null || mMultiChannels == null || index < 0 || index >= mMultiChannels.length) return;
    for (int i = 0; i < mMultiChannels.length; i++)
      if (i != index && mMultiChannels[i] != null && mMultiChannels[i].id.equals(channel.id)) {
        toast("That channel is already open"); return;
      }
    String oldId = mMultiChannels[index] == null ? "" : mMultiChannels[index].id;
    ArrayList<Channel> next = new ArrayList<>();
    for (int i = 0; i < mMultiChannels.length; i++)
      next.add(i == index ? channel : mMultiChannels[i]);
    rebuildCobraMultiPreservingSessions(next, oldId);
  }

  private void removeCobraMultiTileClean(int index) {
    if (mMultiChannels == null || index < 0 || index >= mMultiChannels.length) return;
    if (mMultiChannels.length <= 2) {
      int remaining = index == 0 ? 1 : 0;
      setMultiAudio(remaining);
      multiToSingle();
      return;
    }
    String oldId = mMultiChannels[index] == null ? "" : mMultiChannels[index].id;
    ArrayList<Channel> next = new ArrayList<>();
    for (int i = 0; i < mMultiChannels.length; i++)
      if (i != index && mMultiChannels[i] != null) next.add(mMultiChannels[i]);
    rebuildCobraMultiPreservingSessions(next, oldId);
  }

  private void showCobraMultiTileActions(int index) {
    if (mMultiChannels == null || index < 0 || index >= mMultiChannels.length) return;
    Channel channel = mMultiChannels[index];
    String[] actions = {
        "Use Audio Here", "Change Channel", "Add Screen",
        "Fullscreen This", "Remove Screen", "Close Multi-View"
    };
    new AlertDialog.Builder(this)
        .setTitle(channel == null ? "Multi-View" : channel.name)
        .setItems(actions, (dialog, which) -> {
          if (which == 0) setMultiAudio(index);
          else if (which == 1) {
            mCobraMultiReplaceIndex = index;
            showCobraMultiPicker(true);
          } else if (which == 2) {
            if (mMultiChannels.length >= 4) toast("Multi-View already has 4 screens");
            else { mCobraMultiReplaceIndex = -1; showCobraMultiPicker(true); }
          } else if (which == 3) {
            setMultiAudio(index);
            multiToSingle();
          } else if (which == 4) removeCobraMultiTileClean(index);
          else releaseMulti();
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private void openMultiView(List<Channel> channels) {
    if (channels == null || channels.size() < 2) {
      toast("Choose at least two channels");
      return;
    }

    boolean preserving = mCobraMultiCarryPlayers != null && mCobraMultiCarryChannels != null;
    if (!preserving) {
      mCobraCarryPlayer = null;
      mCobraCarryChannel = null;
      if (mPlayer != null && mPlaying != null
          && channels.get(0) != null && channels.get(0).id.equals(mPlaying.id)) {
        clearCobraPlayerLockState(false);
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
      } else closePlayer();
      releaseMulti();
    }

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

    decor.addView(mMultiOverlay, new FrameLayout.LayoutParams(-1, -1));
    int owner = 0;
    if (!mCobraMultiCarryAudioChannelId.isEmpty()) {
      for (int i = 0; i < mMultiChannels.length; i++)
        if (mMultiChannels[i] != null && mCobraMultiCarryAudioChannelId.equals(mMultiChannels[i].id)) owner = i;
    }
    setMultiAudio(owner);
    configureCobraPip(false);
    if (mDeviceBridge != null) mDeviceBridge.onPlaybackChanged("multiview-start");
    mFeatures.writeHealth("multiview", "", "", "ready", "", 0, count, owner,
        mRecordingSession.isEmpty() ? "idle" : "recording", "ready");
    mCobraMultiCarryPlayers = null;
    mCobraMultiCarryChannels = null;
    mCobraMultiCarryAudioChannelId = "";
  }'''
    java = replace_method(java, "  private void openMultiView(List<Channel> channels) {", multi_block)

    multi_tile = r'''  private FrameLayout createMultiTile(int index) {
    FrameLayout tile = new FrameLayout(this);
    tile.setFocusable(true);
    tile.setFocusableInTouchMode(false);
    tile.setContentDescription(mMultiChannels[index].name);
    TextureView texture = new TextureView(this);
    mMultiTextures[index] = texture;
    tile.addView(texture, new FrameLayout.LayoutParams(-1, -1));
    tile.setOnClickListener(v -> setMultiAudio(index));
    tile.setOnLongClickListener(v -> { showCobraMultiTileActions(index); return true; });
    tile.setOnFocusChangeListener((v, focused) -> { if (focused) setMultiAudio(index); });

    if (mCobraMultiCarryPlayers != null && mCobraMultiCarryChannels != null) {
      for (int j = 0; j < mCobraMultiCarryPlayers.length; j++) {
        ExoPlayer carry = mCobraMultiCarryPlayers[j];
        Channel prior = j < mCobraMultiCarryChannels.length ? mCobraMultiCarryChannels[j] : null;
        if (carry != null && prior != null && prior.id.equals(mMultiChannels[index].id)) {
          mCobraMultiCarryPlayers[j] = null;
          mMultiPlayers[index] = carry;
          try { carry.setVideoTextureView(texture); } catch (Exception ignored) {}
          carry.play();
          return tile;
        }
      }
    }

    if (index == 0 && mCobraCarryPlayer != null && mCobraCarryChannel != null
        && mCobraCarryChannel.id.equals(mMultiChannels[index].id)) {
      ExoPlayer carry = mCobraCarryPlayer;
      mCobraCarryPlayer = null;
      mCobraCarryChannel = null;
      mMultiPlayers[index] = carry;
      try { carry.setVideoTextureView(texture); } catch (Exception ignored) {}
      carry.play();
      return tile;
    }

    try {
      ExoPlayer player = buildPlayer(texture, mMultiChannels[index], index == 0);
      mMultiPlayers[index] = player;
      player.addListener(new Player.Listener() {
        @Override public void onPlayerError(PlaybackException error) {
          toast("Stream error • " + mMultiChannels[index].name);
        }
      });
      player.setMediaItem(mediaItem(mMultiChannels[index].primaryUrl));
      player.prepare();
      player.play();
    } catch (Exception error) {
      toast("Unable to open • " + mMultiChannels[index].name);
    }
    return tile;
  }'''
    java = replace_method(java, "  private FrameLayout createMultiTile(int index) {", multi_tile)

    select_multi = r'''  private void selectCobraMultiChannel(Channel channel) {
    if (channel == null) return;
    if (mCobraMultiPickerAdding && mMultiChannels != null) {
      int replaceIndex = mCobraMultiReplaceIndex;
      closeCobraMultiPicker(true);
      mCobraMultiReplaceIndex = -1;
      if (replaceIndex >= 0) replaceCobraMultiTileClean(replaceIndex, channel);
      else addCobraMultiTileClean(channel);
      return;
    }

    Channel current = mPlaying;
    if (current == null || mPlayer == null) {
      closeCobraMultiPicker(false);
      toast("Play a channel first, then open Multi-View");
      return;
    }
    if (current.id.equals(channel.id)) { toast("Choose a different channel"); return; }
    ArrayList<Channel> chosen = new ArrayList<>();
    chosen.add(current);
    chosen.add(channel);
    closeCobraMultiPicker(true);
    openMultiView(chosen);
  }'''
    java = replace_method(java, "  private void selectCobraMultiChannel(Channel channel) {", select_multi)

    a, b = span(java, "  private void showCobraMultiPicker(boolean adding) {")
    picker = java[a:b]
    old = 'TextView title = text(adding ? "ADD MULTI-VIEW SCREEN" : "MULTI-VIEW • PICK SECOND SCREEN",\n'
    if old in picker:
        picker = picker.replace(old,
            'TextView title = text(mCobraMultiReplaceIndex >= 0 ? "CHANGE MULTI-VIEW SCREEN"\n'
            '        : (adding ? "ADD MULTI-VIEW SCREEN" : "MULTI-VIEW • PICK SECOND SCREEN"),\n', 1)
    java = java[:a] + picker + java[b:]

    a, b = span(java, "  private boolean closeCobraMultiPicker(boolean keepVideoDocked) {")
    close_picker = java[a:b]
    anchor = "    mCobraMultiPickerAdding = false;\n"
    if anchor in close_picker:
        close_picker = close_picker.replace(anchor,
            anchor + "    if (!keepVideoDocked) mCobraMultiReplaceIndex = -1;\n", 1)
    java = java[:a] + close_picker + java[b:]

    a, b = span(java, "  protected void onDestroy() {")
    destroy = java[a:b]
    brace = destroy.find("{")
    destroy = destroy[:brace + 1] + "\n    mMain.removeCallbacks(mHideCobraUnlockButton);" + destroy[brace + 1:]
    java = java[:a] + destroy + java[b:]

    return java


def verify(java: str) -> None:
    required = (
        'cobra_player_reboot_chrome',
        'GradientDrawable.Orientation.TOP_BOTTOM',
        'cobraPlayerNow(channel)',
        'cobraPlayerNext(channel)',
        'cobraVideoButton("🔒", "Lock player controls")',
        'Player controls locked',
        'showCobraPlayerUnlockAffordance()',
        'mHideCobraUnlockButton',
        'if (mCobraPlayerLocked && mPlayerOverlay != null)',
        'mCobraPreviewSessionKey',
        'existingPlayer.setVideoTextureView(mCobraPreviewTexture)',
        'rebuildCobraMultiPreservingSessions(',
        'mCobraMultiCarryPlayers',
        'showCobraMultiTileActions(index)',
        'Change Channel',
        'Fullscreen This',
        'carry.setVideoTextureView(texture)',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("2103152 reboot contract missing: " + token)
    for sig in (
        "  private void openPlayerOverlay(Channel channel) {",
        "  private FrameLayout createMultiTile(int index) {",
        "  private void openMultiView(List<Channel> channels) {",
        "  private void selectCobraMultiChannel(Channel channel) {",
    ):
        if java.count(sig) != 1:
            raise RuntimeError("duplicate/missing method: " + sig.strip())
    if 'action("A1")' in java or 'Button add = action("+ ADD")' in java:
        raise RuntimeError("permanent Multi-View chrome from 2103151 remains")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: Cobra 2103152 full player reboot + lock + continuity polish applied")


if __name__ == "__main__":
    main()
