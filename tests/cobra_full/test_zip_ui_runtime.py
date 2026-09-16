#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import infinity_1_0_9_cobra_zip_ui_runtime_matcher_fix as matcher_fix


class CobraZipUiRuntimeMatcherTests(unittest.TestCase):
    def test_post_parity_navigation_width_matcher(self) -> None:
        source = (
            "before\n"
            "    int railWidth = isCompact() ? dp(104) : isMedium() ? dp(132) : dp(156);\n"
            "after\n"
        )
        replacement = (
            '    int railWidth = "drawer".equals(mUi.navigationMode)\n'
            "        ? dp(isPortrait() ? mUi.drawerPortraitWidthDp : mUi.drawerLandscapeWidthDp)\n"
            "        : (isCompact() ? dp(104) : isMedium() ? dp(132) : dp(156));"
        )
        result = matcher_fix._replace_navigation_width(source, replacement)
        self.assertIn("mUi.drawerPortraitWidthDp", result)
        self.assertNotIn(
            "int railWidth = isCompact() ? dp(104) : isMedium() ? dp(132) : dp(156);",
            result,
        )

    def test_default_ui_package_preserves_candidate2_destinations_and_player(self) -> None:
        ui = json.loads(
            (ROOT / "addons/script.infinity.cobra.theme/resources/cobra-ui.json").read_text(
                encoding="utf-8"
            )
        )
        destinations = set(ui["navigation"]["destinations"])
        for destination in (
            "live", "guide", "movies", "series", "recordings", "favorites",
            "search", "multiview", "discover", "sources", "settings", "infinity",
        ):
            self.assertIn(destination, destinations)

        primary = ui["player"]["primary_actions"]
        self.assertNotIn("guide", primary)
        self.assertEqual(
            primary,
            ["previous", "favorite", "record", "multiview", "next"],
        )

        settings = ui["player"]["settings_actions"]
        self.assertIn("guide", settings)
        self.assertIn("multiview", settings)
        self.assertIn("source", settings)


if __name__ == "__main__":
    unittest.main()
