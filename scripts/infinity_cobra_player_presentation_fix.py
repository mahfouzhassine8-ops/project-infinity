#!/usr/bin/env python3
"""Repair Cobra player-settings dismissal and Fit/Crop presentation behavior.

Android presentation-shell only. This patch deliberately avoids Kodi native,
renderer ownership, provider playback, rotation, Fold, background/resume and
Infinity handoff contracts.
"""
from __future__ import annotations

import argparse
from pathlib import Path

LIVE = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Cobra player presentation {label}: expected exactly one match, found {count}"
        )
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"Cobra player presentation {label}: start marker missing")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"Cobra player presentation {label}: end marker missing")
    return text[:a] + replacement + text[b:]


def patch(java: str) -> str:
    if "import androidx.media3.common.VideoSize;\n" not in java:
        java = once(
            java,
            "import androidx.media3.common.Player;\n",
            "import androidx.media3.common.Player;\n"
            "import androidx.media3.common.VideoSize;\n",
            "VideoSize import",
        )

    java = once(
        java,
        "    if (mPlayerOverlay != null) {\n"
        "      closePlayer();\n"
        "      return;\n"
        "    }\n",
        "    if (mPlayerOverlay != null) {\n"
        "      if (closePlayerSettingsDrawer()) return;\n"
        "      closePlayer();\n"
        "      return;\n"
        "    }\n",
        "Back dismisses drawer first",
    )

    java = once(
        java,
        "    View old = mPlayerOverlay.findViewWithTag(\"player_settings_drawer\");\n"
        "    if (old != null) { mPlayerOverlay.removeView(old); return; }\n",
        "    if (closePlayerSettingsDrawer()) return;\n",
        "drawer toggle uses dismiss helper",
    )

    java = once(
        java,
        "    drawer.setTag(\"player_settings_drawer\");\n"
        "    drawer.setOrientation(LinearLayout.VERTICAL);\n",
        "    drawer.setTag(\"player_settings_drawer\");\n"
        "    drawer.setClickable(true);\n"
        "    drawer.setFocusable(true);\n"
        "    drawer.setOrientation(LinearLayout.VERTICAL);\n",
        "drawer consumes inside taps",
    )

    java = once(
        java,
        "    TextView title = text(\"PLAYER SETTINGS\", mTheme.text, 18, Gravity.CENTER_VERTICAL | Gravity.LEFT);\n"
        "    title.setTypeface(null, Typeface.BOLD);\n"
        "    drawer.addView(title, new LinearLayout.LayoutParams(-1, dp(58)));\n",
        "    LinearLayout drawerHeader = new LinearLayout(this);\n"
        "    drawerHeader.setGravity(Gravity.CENTER_VERTICAL);\n"
        "    TextView title = text(\"PLAYER SETTINGS\", mTheme.text, 18, Gravity.CENTER_VERTICAL | Gravity.LEFT);\n"
        "    title.setTypeface(null, Typeface.BOLD);\n"
        "    Button dismiss = action(\"✕\");\n"
        "    dismiss.setContentDescription(\"Close player settings\");\n"
        "    dismiss.setOnClickListener(v -> closePlayerSettingsDrawer());\n"
        "    drawerHeader.addView(title, new LinearLayout.LayoutParams(0, dp(58), 1));\n"
        "    drawerHeader.addView(dismiss, new LinearLayout.LayoutParams(dp(58), dp(58)));\n"
        "    drawer.addView(drawerHeader, new LinearLayout.LayoutParams(-1, dp(58)));\n",
        "drawer header close control",
    )

    java = once(
        java,
        "    mPlayerOverlay.setOnClickListener(v -> togglePlayerChrome());\n",
        "    mPlayerOverlay.setOnClickListener(v -> {\n"
        "      if (!closePlayerSettingsDrawer()) togglePlayerChrome();\n"
        "    });\n",
        "outside tap dismisses drawer",
    )

    dismiss_helper = r'''  private boolean closePlayerSettingsDrawer() {
    if (mPlayerOverlay == null) return false;
    View drawer = mPlayerOverlay.findViewWithTag("player_settings_drawer");
    if (drawer == null) return false;
    mPlayerOverlay.removeView(drawer);
    return true;
  }

'''
    java = once(
        java,
        "  private void showPlayerSettingsDrawer() {\n",
        dismiss_helper + "  private void showPlayerSettingsDrawer() {\n",
        "drawer dismiss helper",
    )

    aspect_method = r'''  private void cycleAspectMode() {
    if (mPlayer == null || mPlayerTexture == null) return;
    mAspectMode = (mAspectMode + 1) % 2;
    // Keep the decoder in the predictable fit mode. Crop/Fill is performed by
    // the TextureView itself so devices cannot silently ignore codec crop mode.
    mPlayer.setVideoScalingMode(C.VIDEO_SCALING_MODE_SCALE_TO_FIT);
    applyCobraAspectTransform();
    toast(mAspectMode == 0 ? "Fit" : "Crop / Fill");
  }

  private void applyCobraAspectTransform() {
    if (mPlayerTexture == null) return;
    if (mAspectMode == 0) {
      mPlayerTexture.setScaleX(1f);
      mPlayerTexture.setScaleY(1f);
      return;
    }
    if (mPlayer == null) return;
    VideoSize size = mPlayer.getVideoSize();
    int videoWidth = size.width;
    int videoHeight = size.height;
    int viewWidth = mPlayerTexture.getWidth();
    int viewHeight = mPlayerTexture.getHeight();
    if (videoWidth <= 0 || videoHeight <= 0 || viewWidth <= 0 || viewHeight <= 0) return;
    float pixelRatio = size.pixelWidthHeightRatio > 0f ? size.pixelWidthHeightRatio : 1f;
    float videoAspect = (videoWidth * pixelRatio) / (float) videoHeight;
    float viewAspect = viewWidth / (float) viewHeight;
    if (videoAspect <= 0f || viewAspect <= 0f) return;
    float zoom = videoAspect > viewAspect
        ? videoAspect / viewAspect
        : viewAspect / videoAspect;
    zoom = Math.max(1f, Math.min(zoom, 4f));
    mPlayerTexture.setPivotX(viewWidth / 2f);
    mPlayerTexture.setPivotY(viewHeight / 2f);
    mPlayerTexture.setScaleX(zoom);
    mPlayerTexture.setScaleY(zoom);
  }

'''
    java = replace_between(
        java,
        "  private void cycleAspectMode() {\n",
        "  private void openCastSettings() {\n",
        aspect_method + "  private void openCastSettings() {\n",
        "deterministic Fit/Crop implementation",
    )

    java = once(
        java,
        "      mPlayer.addListener(new Player.Listener() {\n"
        "        @Override\n"
        "        public void onPlaybackStateChanged(int playbackState) {\n",
        "      mPlayer.addListener(new Player.Listener() {\n"
        "        @Override\n"
        "        public void onVideoSizeChanged(VideoSize videoSize) {\n"
        "          if (mPlayerTexture != null) mPlayerTexture.post(() -> applyCobraAspectTransform());\n"
        "        }\n\n"
        "        @Override\n"
        "        public void onPlaybackStateChanged(int playbackState) {\n",
        "video-size transform callback",
    )

    return java


def verify(java: str) -> None:
    required = (
        "closePlayerSettingsDrawer()",
        'dismiss.setContentDescription("Close player settings")',
        'drawer.setClickable(true)',
        "if (!closePlayerSettingsDrawer()) togglePlayerChrome()",
        "if (closePlayerSettingsDrawer()) return;",
        "applyCobraAspectTransform()",
        "public void onVideoSizeChanged(VideoSize videoSize)",
        "mPlayerTexture.setScaleX(zoom)",
        "mPlayerTexture.setScaleY(zoom)",
        "VIDEO_SCALING_MODE_SCALE_TO_FIT",
        'toast(mAspectMode == 0 ? "Fit" : "Crop / Fill")',
    )
    for token in required:
        if token not in java:
            raise RuntimeError("Cobra player presentation contract missing: " + token)

    # We intentionally remove the decoder-only crop path because it was not
    # visibly effective on the target device.
    if "VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING" in java:
        raise RuntimeError("Legacy decoder-only crop path still present")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    live = args.source.resolve() / LIVE
    java = live.read_text(encoding="utf-8")
    java = patch(java)
    verify(java)
    live.write_text(java, encoding="utf-8")
    print("PASS: player drawer dismissal + deterministic Fit/Crop presentation repair applied")


if __name__ == "__main__":
    main()
