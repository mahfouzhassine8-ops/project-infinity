#!/usr/bin/env python3
"""Mirror Infinity's accepted Android/foldable device contracts into Cobra.

Infinity and Cobra live in one APK but use different Activities. Android PiP,
window/fold callbacks, orientation ownership and preferred display modes are
Activity-scoped, so Cobra must explicitly join the same contracts already used
by Infinity Main. This layer is applied after the Candidate 2 feature transform
and deliberately does not alter Kodi's native renderer/player ownership.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER_TEMPLATE = ROOT / "patches/infinity-cobra-v2/InfinityCobraDeviceBridge.java.in"
HELPER_REL = Path("tools/android/packaging/xbmc/src/InfinityCobraDeviceBridge.java.in")
LIVE_REL = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
MANIFEST_REL = Path("tools/android/packaging/xbmc/AndroidManifest.xml.in")
INSTALL_REL = Path("cmake/scripts/android/Install.cmake")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"{label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"{label}: end marker missing")
    return text[:a] + replacement + text[b:]


def patch_activity(java: str) -> str:
    java = once(
        java,
        "import android.app.Activity;\n",
        "import android.app.Activity;\nimport android.app.PictureInPictureParams;\n",
        "Cobra PiP import",
    )
    java = once(
        java,
        "import android.os.Bundle;\n",
        "import android.os.Build;\nimport android.os.Bundle;\n",
        "Cobra Build import",
    )
    java = once(
        java,
        "import android.util.Xml;\n",
        "import android.util.Rational;\nimport android.util.Xml;\n",
        "Cobra Rational import",
    )

    java = once(
        java,
        "  private Theme mTheme;\n",
        "  private Theme mTheme;\n"
        "  private InfinityCobraDeviceBridge mDeviceBridge;\n"
        "  private boolean mInPictureInPicture = false;\n"
        "  private boolean mPausedForBackground = false;\n"
        "  private boolean mRebuildShellAfterPlayer = false;\n"
        "  private boolean mReflowingMulti = false;\n"
        "  private LinearLayout mMultiChrome;\n"
        "  private final Runnable mHideMultiChrome = () -> {\n"
        "    if (mMultiChrome != null) mMultiChrome.setVisibility(View.GONE);\n"
        "  };\n",
        "Cobra device parity fields",
    )

    java = once(
        java,
        "    mFeatures = new InfinityCobraFeatureRuntime(this);\n"
        "    mTheme = Theme.load(this);\n",
        "    mFeatures = new InfinityCobraFeatureRuntime(this);\n"
        "    mTheme = Theme.load(this);\n"
        "    mDeviceBridge = new InfinityCobraDeviceBridge(this, () -> hasCobraVideo());\n"
        "    configureCobraPip(false);\n",
        "Cobra device bridge init",
    )

    java = once(
        java,
        "    mMain.removeCallbacks(mProgressTicker);\n"
        "    releaseSinglePlayer();\n",
        "    mMain.removeCallbacks(mProgressTicker);\n"
        "    mMain.removeCallbacks(mHideMultiChrome);\n"
        "    if (mDeviceBridge != null) mDeviceBridge.close();\n"
        "    releaseSinglePlayer();\n",
        "Cobra device bridge destroy",
    )

    lifecycle = r'''  @Override
  public void onConfigurationChanged(Configuration configuration) {
    super.onConfigurationChanged(configuration);
    mTheme = Theme.load(this);
    if (mDeviceBridge != null) mDeviceBridge.onWindowChanged("configuration");

    if (mMultiOverlay != null && mMultiChannels != null && mMultiChannels.length >= 2) {
      ArrayList<Channel> snapshot = new ArrayList<>();
      for (Channel channel : mMultiChannels) if (channel != null) snapshot.add(channel);
      int owner = mAudioTile;
      mRebuildShellAfterPlayer = true;
      mReflowingMulti = true;
      releaseMulti();
      if (snapshot.size() >= 2) {
        openMultiView(snapshot);
        setMultiAudio(Math.min(owner, snapshot.size() - 1));
      }
      mReflowingMulti = false;
      return;
    }

    if (mPlayerOverlay != null && mPlayer != null) {
      mRebuildShellAfterPlayer = true;
      mPlayerOverlay.requestLayout();
      if (mPlayerTexture != null) mPlayerTexture.requestLayout();
      configureCobraPip(true);
      return;
    }

    buildShell();
    if (mChannels.isEmpty()) {
      if (mSources.isEmpty()) showWelcome(); else loadAllEnabledSources(false);
    } else {
      showLiveHome();
    }
  }

  @Override
  protected void onResume() {
    super.onResume();
    if (mDeviceBridge != null) mDeviceBridge.onResume();
    resumeCobraAfterBackground();
    configureCobraPip(hasCobraVideo() && mMultiOverlay == null);
  }

  @Override
  protected void onPause() {
    if (mDeviceBridge != null) mDeviceBridge.onPause();
    super.onPause();
  }

  @Override
  protected void onStop() {
    if (!isCobraInPictureInPicture() && hasCobraVideo()) pauseCobraForBackground();
    super.onStop();
  }

  @Override
  protected void onUserLeaveHint() {
    super.onUserLeaveHint();
    if (hasCobraVideo()) enterCobraPictureInPicture();
  }

  @Override
  public void onPictureInPictureModeChanged(boolean inPictureInPictureMode, Configuration configuration) {
    super.onPictureInPictureModeChanged(inPictureInPictureMode, configuration);
    mInPictureInPicture = inPictureInPictureMode;
    if (mPlayerChrome != null) {
      mPlayerChrome.setVisibility(inPictureInPictureMode ? View.GONE : View.VISIBLE);
    }
    if (mMultiChrome != null) mMultiChrome.setVisibility(View.GONE);
    if (!inPictureInPictureMode) showPlayerChromeTemporarily();
    if (mDeviceBridge != null) mDeviceBridge.onWindowChanged("picture-in-picture");
  }

  @Override
  public void onMultiWindowModeChanged(boolean inMultiWindowMode, Configuration configuration) {
    super.onMultiWindowModeChanged(inMultiWindowMode, configuration);
    if (mDeviceBridge != null) mDeviceBridge.onWindowChanged("multi-window");
  }

'''
    java = replace_between(
        java,
        "  @Override\n  public void onConfigurationChanged(Configuration configuration) {\n",
        "  @Override\n  protected void onActivityResult(",
        lifecycle,
        "Cobra fold/PiP lifecycle",
    )

    responsive = r'''  private boolean isCompact() {
    if (mDeviceBridge != null) return mDeviceBridge.widthClass() == 0;
    int widthDp = Math.round(
        getResources().getDisplayMetrics().widthPixels /
        getResources().getDisplayMetrics().density);
    return widthDp < 600;
  }

  private boolean isMedium() {
    if (mDeviceBridge != null) return mDeviceBridge.widthClass() == 1;
    int widthDp = Math.round(
        getResources().getDisplayMetrics().widthPixels /
        getResources().getDisplayMetrics().density);
    return widthDp >= 600 && widthDp < 840;
  }

'''
    java = replace_between(
        java,
        "  private boolean isCompact() {\n",
        "  private boolean isPortrait() {\n",
        responsive,
        "Cobra 600/840 responsive classes",
    )
    java = once(
        java,
        "    int railWidth = isCompact() ? dp(108) : dp(156);\n",
        "    int railWidth = isCompact() ? dp(104) : isMedium() ? dp(132) : dp(156);\n",
        "Cobra responsive rail width",
    )

    java = once(
        java,
        "        public void onPlaybackStateChanged(int playbackState) {\n"
        "          if (state == null) return;\n",
        "        public void onPlaybackStateChanged(int playbackState) {\n"
        "          configureCobraPip(playbackState != Player.STATE_IDLE && playbackState != Player.STATE_ENDED);\n"
        "          if (mDeviceBridge != null) mDeviceBridge.onPlaybackChanged(\"player-state-\" + playbackState);\n"
        "          if (state == null) return;\n",
        "Cobra playback device callback",
    )

    old_multi_bar_start = "    LinearLayout bar = new LinearLayout(this); bar.setGravity(Gravity.CENTER); bar.setPadding(dp(8), dp(5), dp(8), dp(5));\n"
    old_multi_bar_end = "    decor.addView(mMultiOverlay, new FrameLayout.LayoutParams(-1, -1));\n"
    multi_chrome = r'''    mMultiChrome = new LinearLayout(this);
    mMultiChrome.setGravity(Gravity.CENTER);
    mMultiChrome.setPadding(dp(8), dp(5), dp(8), dp(5));
    mMultiChrome.setBackground(surface(Color.argb(224, 8, 10, 15), 18, mTheme.line, 1));
    for (int i = 0; i < count; i++) {
      final int index = i;
      Button audio = action("AUDIO " + (i + 1));
      audio.setOnClickListener(v -> { setMultiAudio(index); showMultiChromeTemporarily(); });
      mMultiChrome.addView(audio, new LinearLayout.LayoutParams(0, dp(48), 1));
    }
    Button exit = action("✕");
    exit.setOnClickListener(v -> releaseMulti());
    mMultiChrome.addView(exit, new LinearLayout.LayoutParams(dp(64), dp(48)));
    FrameLayout.LayoutParams multiChromeParams = new FrameLayout.LayoutParams(-1, dp(58), Gravity.BOTTOM);
    multiChromeParams.setMargins(dp(18), 0, dp(18), dp(18));
    mMultiOverlay.addView(mMultiChrome, multiChromeParams);
    mMultiOverlay.setOnClickListener(v -> showMultiChromeTemporarily());
'''
    java = replace_between(
        java,
        old_multi_bar_start,
        old_multi_bar_end,
        multi_chrome,
        "Cobra auto-hide Multi-View chrome",
    )
    java = once(
        java,
        "    decor.addView(mMultiOverlay, new FrameLayout.LayoutParams(-1, -1));\n"
        "    setMultiAudio(0);\n",
        "    decor.addView(mMultiOverlay, new FrameLayout.LayoutParams(-1, -1));\n"
        "    setMultiAudio(0);\n"
        "    configureCobraPip(false);\n"
        "    showMultiChromeTemporarily();\n"
        "    if (mDeviceBridge != null) mDeviceBridge.onPlaybackChanged(\"multiview-start\");\n",
        "Cobra Multi-View device callback",
    )
    java = once(
        java,
        "    tile.setOnClickListener(v -> setMultiAudio(index)); tile.setOnFocusChangeListener((v, focused) -> { if (focused) setMultiAudio(index); });\n",
        "    tile.setOnClickListener(v -> { setMultiAudio(index); showMultiChromeTemporarily(); });\n"
        "    tile.setOnFocusChangeListener((v, focused) -> { if (focused) setMultiAudio(index); });\n",
        "Cobra Multi-View touch chrome",
    )

    multi_helpers = r'''  private void showMultiChromeTemporarily() {
    if (mMultiChrome == null) return;
    mMultiChrome.setVisibility(View.VISIBLE);
    mMain.removeCallbacks(mHideMultiChrome);
    mMain.postDelayed(mHideMultiChrome, 3200L);
  }

'''
    java = once(
        java,
        "  private void setMultiAudio(int index) {\n",
        multi_helpers + "  private void setMultiAudio(int index) {\n",
        "Cobra Multi-View chrome helper",
    )

    java = once(
        java,
        "    mMultiOverlay = null;\n  }\n\n  private String sourceIdForChannel(Channel channel) {\n",
        "    mMultiOverlay = null;\n"
        "    mMultiChrome = null;\n"
        "    mMain.removeCallbacks(mHideMultiChrome);\n"
        "    configureCobraPip(false);\n"
        "    if (mDeviceBridge != null) mDeviceBridge.onPlaybackChanged(\"multiview-stop\");\n"
        "    if (!mReflowingMulti) rebuildCobraShellIfNeeded();\n"
        "  }\n\n  private String sourceIdForChannel(Channel channel) {\n",
        "Cobra Multi-View cleanup",
    )

    java = once(
        java,
        "    mPlaybackRetryCount = 0;\n  }\n\n  private void stepChannel(int delta) {\n",
        "    mPlaybackRetryCount = 0;\n"
        "    configureCobraPip(false);\n"
        "    if (mDeviceBridge != null) mDeviceBridge.onPlaybackChanged(\"player-close\");\n"
        "    if (!mReflowingMulti) rebuildCobraShellIfNeeded();\n"
        "  }\n\n  private void stepChannel(int delta) {\n",
        "Cobra player cleanup parity",
    )

    device_helpers = r'''  private boolean hasCobraVideo() {
    if (mPlayer != null) {
      int state = mPlayer.getPlaybackState();
      if (state != Player.STATE_IDLE && state != Player.STATE_ENDED) return true;
    }
    if (mMultiPlayers != null) {
      for (ExoPlayer player : mMultiPlayers) {
        if (player == null) continue;
        int state = player.getPlaybackState();
        if (state != Player.STATE_IDLE && state != Player.STATE_ENDED) return true;
      }
    }
    return false;
  }

  private PictureInPictureParams cobraPipParams(boolean autoEnter) {
    if (Build.VERSION.SDK_INT < 26) return null;
    PictureInPictureParams.Builder builder = new PictureInPictureParams.Builder()
        .setAspectRatio(new Rational(16, 9));
    if (Build.VERSION.SDK_INT >= 31) {
      builder.setAutoEnterEnabled(autoEnter);
      builder.setSeamlessResizeEnabled(true);
    }
    return builder.build();
  }

  private void configureCobraPip(boolean autoEnter) {
    if (Build.VERSION.SDK_INT < 26 || isFinishing()) return;
    try {
      PictureInPictureParams params = cobraPipParams(autoEnter && mMultiOverlay == null);
      if (params != null) setPictureInPictureParams(params);
    } catch (IllegalStateException | IllegalArgumentException ignored) {}
  }

  private boolean isCobraInPictureInPicture() {
    if (mInPictureInPicture) return true;
    if (Build.VERSION.SDK_INT < 26) return false;
    try { return isInPictureInPictureMode(); }
    catch (IllegalStateException ignored) { return false; }
  }

  private void enterCobraPictureInPicture() {
    if (!hasCobraVideo()) return;
    if (Build.VERSION.SDK_INT < 26) { pauseCobraForBackground(); return; }

    if (mMultiOverlay != null && mMultiChannels != null && mMultiChannels.length > 0) {
      int owner = Math.max(0, Math.min(mAudioTile, mMultiChannels.length - 1));
      Channel selected = mMultiChannels[owner];
      mReflowingMulti = true;
      releaseMulti();
      if (selected != null) playChannel(selected);
      mReflowingMulti = false;
    }

    try {
      PictureInPictureParams params = cobraPipParams(false);
      boolean entered = params != null && enterPictureInPictureMode(params);
      if (!entered) pauseCobraForBackground();
    } catch (IllegalStateException | IllegalArgumentException error) {
      pauseCobraForBackground();
    }
  }

  private void pauseCobraForBackground() {
    boolean pausedAny = false;
    if (mPlayer != null) {
      try { if (mPlayer.isPlaying()) { mPlayer.pause(); pausedAny = true; } } catch (Exception ignored) {}
    }
    if (mMultiPlayers != null) {
      for (ExoPlayer player : mMultiPlayers) {
        if (player == null) continue;
        try { if (player.isPlaying()) { player.pause(); pausedAny = true; } } catch (Exception ignored) {}
      }
    }
    mPausedForBackground = pausedAny;
  }

  private void resumeCobraAfterBackground() {
    if (!mPausedForBackground || isCobraInPictureInPicture()) return;
    mPausedForBackground = false;
    if (mPlayer != null) try { mPlayer.play(); } catch (Exception ignored) {}
    if (mMultiPlayers != null) {
      for (ExoPlayer player : mMultiPlayers) if (player != null) try { player.play(); } catch (Exception ignored) {}
    }
  }

  private void rebuildCobraShellIfNeeded() {
    if (!mRebuildShellAfterPlayer || mReflowingMulti || isFinishing()) return;
    mRebuildShellAfterPlayer = false;
    mTheme = Theme.load(this);
    buildShell();
    if (mSources.isEmpty()) showWelcome();
    else if (mChannels.isEmpty()) loadAllEnabledSources(false);
    else showLiveHome();
  }

'''
    java = once(
        java,
        "  private void returnToInfinity() {\n",
        device_helpers + "  private void returnToInfinity() {\n",
        "Cobra device helper methods",
    )
    return java


def patch_manifest(manifest: str) -> str:
    match = re.search(
        r'(?P<indent>\s*)<activity\s*\n\s*android:name="\.InfinityLiveActivity"(?P<body>.*?)(?P<close>>)',
        manifest,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError("Cobra manifest Activity declaration missing")
    block = match.group(0)
    if 'android:supportsPictureInPicture="true"' not in block:
        block = block.replace(
            'android:name=".InfinityLiveActivity"',
            'android:name=".InfinityLiveActivity"\n'
            '            android:resizeableActivity="true"\n'
            '            android:supportsPictureInPicture="true"',
            1,
        )
    config = re.search(r'android:configChanges="([^"]+)"', block)
    if config:
        values = config.group(1).split("|")
        for token in ("density", "fontScale", "layoutDirection", "locale", "uiMode"):
            if token not in values:
                values.append(token)
        block = block[:config.start(1)] + "|".join(values) + block[config.end(1):]
    manifest = manifest[:match.start()] + block + manifest[match.end():]
    if 'android.supports_size_changes' not in manifest:
        activity_marker = re.search(r'\s*<activity\s*\n\s*android:name="\.InfinityLiveActivity"', manifest)
        if not activity_marker:
            raise RuntimeError("Cobra manifest Activity marker missing after PiP patch")
        metadata = (
            '\n        <meta-data android:name="android.supports_size_changes" '
            'android:value="true" />\n'
        )
        manifest = manifest[:activity_marker.start()] + metadata + manifest[activity_marker.start():]
    return manifest


def patch_install(text: str) -> str:
    if "src/InfinityCobraDeviceBridge.java" in text:
        return text
    anchor = "                  src/InfinityCobraFeatureRuntime.java\n"
    if anchor not in text:
        raise RuntimeError("Cobra device helper Install.cmake anchor missing")
    return text.replace(
        anchor,
        anchor + "                  src/InfinityCobraDeviceBridge.java\n",
        1,
    )


def verify_activity(java: str) -> None:
    for token in (
        "InfinityCobraDeviceBridge mDeviceBridge",
        "enterPictureInPictureMode",
        "onPictureInPictureModeChanged",
        "onMultiWindowModeChanged",
        "onUserLeaveHint",
        "cobraPipParams",
        "pauseCobraForBackground",
        "mMultiChrome",
        "showMultiChromeTemporarily",
        "widthDp < 600",
        "widthDp >= 600 && widthDp < 840",
    ):
        if token not in java:
            raise RuntimeError("Cobra device parity Activity contract missing: " + token)
    forbidden = "mMultiOverlay.addView(bar, new FrameLayout.LayoutParams(-1, dp(60), Gravity.TOP))"
    if forbidden in java:
        raise RuntimeError("Permanent Multi-View top bar survived device parity pass")


def verify_source(source: Path) -> None:
    source = source.resolve()
    live = (source / LIVE_REL).read_text(encoding="utf-8")
    manifest = (source / MANIFEST_REL).read_text(encoding="utf-8")
    install = (source / INSTALL_REL).read_text(encoding="utf-8")
    helper = source / HELPER_REL
    verify_activity(live)
    for token in (
        'android:name=".InfinityLiveActivity"',
        'android:supportsPictureInPicture="true"',
        'android:resizeableActivity="true"',
        'android.supports_size_changes',
        'density',
        'uiMode',
    ):
        if token not in manifest:
            raise RuntimeError("Cobra device parity manifest contract missing: " + token)
    if not helper.is_file() or "src/InfinityCobraDeviceBridge.java" not in install:
        raise RuntimeError("Cobra device parity helper is not installed")
    helper_text = helper.read_text(encoding="utf-8")
    for token in (
        'infinity_player_rotation',
        'SCREEN_ORIENTATION_FULL_SENSOR',
        '.kodi/userdata/addon_data/service.infinity.refresh',
        'preferredDisplayModeId',
        'android.hardware.sensor.hinge_angle',
        'fold-cover',
        'fold-inner',
        'widthDp < 600',
        'widthDp < 840',
        'owner", "cobra',
    ):
        if token not in helper_text:
            raise RuntimeError("Cobra device parity bridge contract missing: " + token)


def apply_source(source: Path, receipt: Path | None = None) -> None:
    source = source.resolve()
    if not HELPER_TEMPLATE.is_file():
        raise FileNotFoundError(HELPER_TEMPLATE)
    target = source / HELPER_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HELPER_TEMPLATE, target)

    live = source / LIVE_REL
    manifest = source / MANIFEST_REL
    install = source / INSTALL_REL
    live.write_text(patch_activity(live.read_text(encoding="utf-8")), encoding="utf-8")
    manifest.write_text(patch_manifest(manifest.read_text(encoding="utf-8")), encoding="utf-8")
    install.write_text(patch_install(install.read_text(encoding="utf-8")), encoding="utf-8")
    verify_source(source)

    if receipt is not None and receipt.is_file():
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data.update({
            "cobra_device_parity": "infinity-android-parity-v1",
            "cobra_pip": True,
            "cobra_fold_reflow": True,
            "cobra_multi_window": True,
            "cobra_rotation_shared_with_infinity": True,
            "cobra_refresh_policy_shared_with_infinity": True,
            "cobra_width_classes_dp": [600, 840],
            "cobra_multiview_auto_hide_chrome": True,
        })
        files = data.setdefault("files", {})
        for rel in (LIVE_REL, MANIFEST_REL, INSTALL_REL, HELPER_REL):
            files.setdefault(str(rel), {})["after"] = sha(source / rel)
        receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: Cobra joined Infinity fold/PiP/rotation/refresh device contracts")
