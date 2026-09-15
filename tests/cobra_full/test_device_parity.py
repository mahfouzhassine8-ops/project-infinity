from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import infinity_1_0_9_cobra_device_parity as device
import infinity_1_0_9_cobra_full_runner as runner


class CobraDeviceParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = (ROOT / "patches/infinity-cobra/InfinityLiveActivity.java.in").read_text(encoding="utf-8")
        cls.java = runner.transform_for_fast_test(base)
        cls.bridge = (ROOT / "patches/infinity-cobra-v2/InfinityCobraDeviceBridge.java.in").read_text(encoding="utf-8")

    def test_real_picture_in_picture_contract(self):
        for token in (
            "PictureInPictureParams",
            "enterPictureInPictureMode",
            "onUserLeaveHint",
            "onPictureInPictureModeChanged",
            "setAutoEnterEnabled",
            "setSeamlessResizeEnabled",
            "pauseCobraForBackground",
            "resumeCobraAfterBackground",
        ):
            self.assertIn(token, self.java)

    def test_pip_failure_never_leaves_ghost_audio(self):
        self.assertIn("boolean entered = params != null && enterPictureInPictureMode(params);", self.java)
        self.assertIn("if (!entered) pauseCobraForBackground();", self.java)
        self.assertIn("if (!isCobraInPictureInPicture() && hasCobraVideo()) pauseCobraForBackground();", self.java)
        self.assertIn("mPausedForBackground", self.java)

    def test_multiview_pip_collapses_to_audio_owner(self):
        for token in (
            "int owner = Math.max(0, Math.min(mAudioTile, mMultiChannels.length - 1));",
            "Channel selected = mMultiChannels[owner];",
            "releaseMulti();",
            "if (selected != null) playChannel(selected);",
        ):
            self.assertIn(token, self.java)

    def test_fold_and_multiwindow_contract(self):
        for token in (
            "onConfigurationChanged",
            "onMultiWindowModeChanged",
            "mRebuildShellAfterPlayer",
            "mReflowingMulti",
            "mPlayerOverlay.requestLayout()",
            "widthDp < 600",
            "widthDp >= 600 && widthDp < 840",
        ):
            self.assertIn(token, self.java)
        for token in ("android.hardware.sensor.hinge_angle", "fold-cover", "fold-inner"):
            self.assertIn(token, self.bridge)

    def test_fold_reflow_preserves_multiview_audio_owner(self):
        for token in (
            "int owner = mAudioTile;",
            "openMultiView(snapshot);",
            "setMultiAudio(Math.min(owner, snapshot.size() - 1));",
        ):
            self.assertIn(token, self.java)

    def test_infinity_rotation_and_refresh_policy_are_shared(self):
        for token in (
            "infinity_player_rotation",
            "SCREEN_ORIENTATION_FULL_SENSOR",
            ".kodi/userdata/addon_data/service.infinity.refresh",
            "preferredDisplayModeId",
            "yield-to-video",
            "respectBatterySaver",
            "thermalProtection",
            "constrainedWindow()",
            'props.setProperty("owner", "cobra")',
        ):
            self.assertIn(token, self.bridge)

    def test_multiview_controls_are_transient_not_permanent_top_bar(self):
        self.assertIn("mMultiChrome", self.java)
        self.assertIn("showMultiChromeTemporarily", self.java)
        self.assertIn("mMain.postDelayed(mHideMultiChrome, 3200L);", self.java)
        self.assertIn("Gravity.BOTTOM", self.java)
        self.assertNotIn(
            "mMultiOverlay.addView(bar, new FrameLayout.LayoutParams(-1, dp(60), Gravity.TOP))",
            self.java,
        )

    def test_manifest_patch_adds_activity_level_pip_and_resize(self):
        manifest = '''<manifest><application>\n        <activity\n            android:name=".InfinityLiveActivity"\n            android:configChanges="orientation|screenSize"\n            android:exported="true">\n        </activity>\n</application></manifest>'''
        patched = device.patch_manifest(manifest)
        self.assertIn('android:supportsPictureInPicture="true"', patched)
        self.assertIn('android:resizeableActivity="true"', patched)
        self.assertIn('android.supports_size_changes', patched)
        for token in ("density", "fontScale", "layoutDirection", "locale", "uiMode"):
            self.assertIn(token, patched)


if __name__ == "__main__":
    unittest.main()
