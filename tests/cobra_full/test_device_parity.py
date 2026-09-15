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
            "pauseCobraForBackground",
        ):
            self.assertIn(token, self.java)

    def test_fold_and_multiwindow_contract(self):
        for token in (
            "onConfigurationChanged",
            "onMultiWindowModeChanged",
            "mRebuildShellAfterPlayer",
            "mReflowingMulti",
            "widthDp < 600",
            "widthDp >= 600 && widthDp < 840",
        ):
            self.assertIn(token, self.java)
        for token in ("android.hardware.sensor.hinge_angle", "fold-cover", "fold-inner"):
            self.assertIn(token, self.bridge)

    def test_infinity_rotation_and_refresh_policy_are_shared(self):
        for token in (
            "infinity_player_rotation",
            "SCREEN_ORIENTATION_FULL_SENSOR",
            ".kodi/userdata/addon_data/service.infinity.refresh",
            "preferredDisplayModeId",
            "yield-to-video",
            'props.setProperty("owner", "cobra")',
        ):
            self.assertIn(token, self.bridge)

    def test_multiview_controls_are_transient_not_permanent_top_bar(self):
        self.assertIn("mMultiChrome", self.java)
        self.assertIn("showMultiChromeTemporarily", self.java)
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
        self.assertIn("density", patched)
        self.assertIn("uiMode", patched)


if __name__ == "__main__":
    unittest.main()
