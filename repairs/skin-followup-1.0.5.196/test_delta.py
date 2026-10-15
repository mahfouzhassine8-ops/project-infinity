#!/usr/bin/env python3
"""Source/geometry contracts only; these do not render Kodi or test a device."""
from copy import deepcopy
from collections import Counter
import unittest
from lxml import etree as E
from delta import BEFORE, AFTER, EDITS, FIXTURE_SHA256, fixtures, repair, sha

ORIGINAL = fixtures()
CANDIDATE = repair(ORIGINAL)
SIZES = [
    (1080, 2520), (2520, 1080), (1560, 1560), (1080, 1920), (1920, 1080),
    (1080, 1600), (1600, 1080), (880, 1280), (1280, 880), (720, 960), (960, 720),
    (720, 720), (720, 600), (600, 720), (600, 600), (1920, 600),
]
# A changing sequence, not just static endpoints. It models XML bounds; it does
# not prove live native resize or fold-event delivery on a phone.
RESIZE_SEQUENCE = [(1080, 2520), (880, 1280), (720, 960), (600, 600),
                   (1560, 1560), (1920, 1080), (2520, 1080), (1080, 2520)]


def xml(name, candidate=True):
    return E.fromstring((CANDIDATE if candidate else ORIGINAL)["unified/" + name])


def control(root, id):
    result = root.xpath('.//control[@id="%s"]' % id)
    if len(result) != 1:
        raise AssertionError("Missing or duplicated control " + str(id))
    return result[0]


def value(text, parent):
    return float(text[:-1]) * parent / 100 if text.endswith("%") else float(text)


def panel_bounds(root, w, h):
    panel = control(root, 1198888)
    return (value(panel.findtext("left"), w), value(panel.findtext("top"), h),
            min(value(panel.findtext("width"), w), value(panel.find("width").get("max"), w)),
            min(value(panel.findtext("height"), h), value(panel.find("height").get("max"), h)))


def row_offsets(root):
    rows = control(root, 1198899)
    gap, y = float(rows.findtext("itemgap")), 0
    result = []
    for group in rows.findall("control"):
        height = float(group.findtext("height"))
        result.append((group, y, y + height))
        y += height + gap
    return result


class DrawerDelta(unittest.TestCase):
    def test_01_exact_baseline_fixture_hashes(self):
        self.assertEqual({n: sha(b) for n, b in ORIGINAL.items()}, FIXTURE_SHA256)

    def test_02_exact_two_file_delta(self):
        self.assertEqual({n for n in ORIGINAL if CANDIDATE[n] != ORIGINAL[n]}, set(BEFORE))
        self.assertEqual({n: sha(CANDIDATE[n]) for n in AFTER}, AFTER)

    def test_03_wrong_preimage_is_rejected(self):
        broken = dict(ORIGINAL)
        broken["unified/Home.xml"] += b"\n"
        with self.assertRaisesRegex(RuntimeError, "preimage"):
            repair(broken)

    def test_04_all_fixture_xml_parses(self):
        for payload in CANDIDATE.values():
            E.fromstring(payload)

    def test_05_home_changes_only_the_two_focus_textures(self):
        before, after = xml("Home.xml", False), xml("Home.xml")
        old_button, new_button = control(before, 9090), control(after, 9090)
        for tag in ["texturefocus", "texturenofocus"]:
            new_button.replace(new_button.find(tag), deepcopy(old_button.find(tag)))
        self.assertEqual(E.tostring(before), E.tostring(after))

    def test_06_drawer_changes_only_height_animation_and_theme_id(self):
        before, after = xml("Custom_1198_InfinityNav.xml", False), xml("Custom_1198_InfinityNav.xml")
        old_panel, new_panel = control(before, 1198888), control(after, 1198888)
        new_panel.replace(new_panel.find("height"), deepcopy(old_panel.find("height")))
        for old, new in zip(old_panel.findall("animation"), new_panel.findall("animation")):
            new.attrib.clear()
            new.attrib.update(old.attrib)
        theme = control(after, 1198310)
        theme.set("id", "1198305")
        marker = theme.getparent().find('control[@type="image"]/visible')
        self.assertEqual(marker.text, "Control.HasFocus(1198310)")
        marker.text = "Control.HasFocus(1198305)"
        self.assertEqual(E.tostring(before), E.tostring(after))

    def test_07_first_view_ends_at_power(self):
        root = xml("Custom_1198_InfinityNav.xml")
        rows, panel = control(root, 1198899), control(root, 1198888)
        power = next(end for group, start, end in row_offsets(root)
                     if group.find('control[@id="1198304"]') is not None)
        self.assertEqual(power, 900)
        self.assertEqual(float(panel.find("height").get("max")),
                         float(rows.findtext("top")) + power + float(rows.findtext("bottom")))

    def test_08_explore_starts_below_initial_viewport(self):
        root = xml("Custom_1198_InfinityNav.xml")
        rows = control(root, 1198899)
        explore = next(start for group, start, end in row_offsets(root)
                       if group.find('control/label') is not None and
                       group.findtext('control/label') == "EXPLORE")
        self.assertEqual(explore, 906)
        for w, h in SIZES + RESIZE_SEQUENCE:
            with self.subTest(w=w, h=h):
                _, _, pw, ph = panel_bounds(root, w, h)
                viewport = ph - float(rows.findtext("top")) - float(rows.findtext("bottom"))
                self.assertGreaterEqual(explore, viewport)
                self.assertGreater(viewport, 0)

    def test_09_panel_remains_in_bounds_during_resize(self):
        root = xml("Custom_1198_InfinityNav.xml")
        for w, h in SIZES + RESIZE_SEQUENCE:
            with self.subTest(w=w, h=h):
                x, y, pw, ph = panel_bounds(root, w, h)
                self.assertGreater(pw, 0)
                self.assertGreater(ph, 0)
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + pw, w)
                self.assertLessEqual(y + ph, h)

    def test_10_all_rows_remain_scrollable_and_present(self):
        root = xml("Custom_1198_InfinityNav.xml")
        rows = control(root, 1198899)
        self.assertEqual(rows.findtext("orientation"), "vertical")
        self.assertEqual(rows.findtext("usecontrolcoords"), "false")
        self.assertEqual(rows.findtext("scrolltime"), "180")
        self.assertGreater(row_offsets(root)[-1][2], 900)
        before = control(xml("Custom_1198_InfinityNav.xml", False), 1198899)
        for old_group, new_group in zip(before.findall("control"), rows.findall("control")):
            old_button = old_group.find('control[@type="button"]')
            new_button = new_group.find('control[@type="button"]')
            if old_button is None:
                self.assertIsNone(new_button)
            else:
                self.assertEqual(old_button.findtext("label"), new_button.findtext("label"))
                self.assertEqual([n.text for n in old_button.findall("onclick")],
                                 [n.text for n in new_button.findall("onclick")])

    def test_11_ui_theme_directly_precedes_power(self):
        root = xml("Custom_1198_InfinityNav.xml")
        ids = [b.get("id") for b in control(root, 1198899).xpath('./control/control[@type="button"]')]
        self.assertEqual(ids[ids.index("1198310") + 1], "1198304")
        self.assertEqual(control(root, 1198310).findtext("label"), "UI Theme")
        self.assertFalse(root.xpath('.//label[text()="More options"]'))

    def test_12_movie_tv_and_power_routes_are_unchanged(self):
        root = xml("Custom_1198_InfinityNav.xml")
        for id, expected in [(1198102, "ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=movies,return)"),
                             (1198103, "ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=tv,return)"),
                             (1198304, "ActivateWindow(shutdownmenu)"),
                             (1198310, "ActivateWindow(InterfaceSettings)"),
                             (1198305, "ActivateWindow(1192)")]:
            self.assertIn(expected, [a.text for a in control(root, id).findall("onclick")])

    def test_13_every_drawer_button_matches_its_row_surface(self):
        root = xml("Custom_1198_InfinityNav.xml")
        for button in control(root, 1198899).xpath('./control/control[@type="button"]'):
            with self.subTest(id=button.get("id")):
                self.assertEqual(button.findtext("left"), "0")
                self.assertEqual(button.findtext("top"), "0")
                self.assertEqual(button.findtext("width"), "100%")
                self.assertEqual(button.findtext("height"), button.getparent().findtext("height"))
                self.assertIsNone(button.find("hitrect"))

    def test_14_close_back_and_touch_focus_return_are_retained(self):
        root = xml("Custom_1198_InfinityNav.xml")
        self.assertEqual(root.findtext("onback"), "Dialog.Close(1198)")
        self.assertIn("ClearProperty(Infinity.DrawerOpen,home)", [n.text for n in root.findall("onunload")])
        self.assertIn("SetFocus(9000)", [n.text for n in root.findall("onunload")])
        self.assertEqual([n.text for n in control(xml("Home.xml"), 9090).findall("onclick")],
                         ["SetFocus(9000)", "ActivateWindow(1198)"])

    def test_15_capsule_geometry_and_artwork_are_retained(self):
        old, new = control(xml("Home.xml", False), 19080), control(xml("Home.xml"), 19080)
        for tag in ["left", "top", "width", "height"]:
            self.assertEqual(old.findtext(tag), new.findtext(tag))
        self.assertEqual(new.findtext("width"), "78")
        self.assertEqual(new.findtext("height"), "122")
        self.assertEqual(old.xpath('./control[@type="image"]/texture/text()'),
                         new.xpath('./control[@type="image"]/texture/text()'))

    def test_16_rest_is_transparent_and_focus_is_outline_only(self):
        button = control(xml("Home.xml"), 9090)
        self.assertEqual(button.findtext("texturenofocus"), "infinity_reference/slider_transparent.png")
        self.assertEqual(button.findtext("texturefocus"), "infinity_polish/focus_rim.png")
        self.assertEqual(button.find("texturefocus").get("colordiffuse"), "$VAR[InfinityGlassFocus]")
        self.assertNotIn("field.png", E.tostring(button).decode())

    def test_17_light_dark_oled_focus_and_text_palettes_are_retained(self):
        variables = xml("IncludesVariables.xml")
        for name in ["InfinityGlassFocus", "InfinityGlassTextPrimary", "InfinityDrawerPanel", "InfinityDrawerScrim"]:
            vals = variables.find('variable[@name="' + name + '"]').findall("value")
            self.assertTrue(any(",light)" in v.get("condition", "") for v in vals))
            self.assertTrue(any(",OLED)" in v.get("condition", "") for v in vals))
            self.assertTrue(any(v.get("condition") is None for v in vals))
        for val in variables.find('variable[@name="InfinityGlassFocus"]').findall("value"):
            self.assertEqual(val.text[:2], "FF")
            rgb = [int(val.text[n:n+2], 16) for n in [2, 4, 6]]
            self.assertGreater(rgb[2], rgb[0])
            self.assertNotEqual(rgb, [255, 255, 255])

    def test_18_unfold_contract_is_top_anchored_and_motion_policy_preserved(self):
        panel = control(xml("Custom_1198_InfinityNav.xml"), 1198888)
        animations = panel.findall("animation")
        self.assertEqual([a.text for a in animations], ["WindowOpen", "WindowClose"])
        self.assertEqual(animations[0].get("start"), "11.47,11.62")
        self.assertEqual(animations[1].get("end"), "11.47,11.62")
        self.assertAlmostEqual(78 / 680 * 100, 11.47, places=2)
        self.assertAlmostEqual(122 / 1050 * 100, 11.62, places=2)
        for animation in animations:
            self.assertEqual(animation.get("center"), "0,0")
            self.assertEqual(animation.get("effect"), "zoom")
            self.assertIn("Infinity.OptionalMotionAllowed", animation.get("condition"))
        self.assertFalse(panel.xpath('./animation[@effect="slide"]'))

    def test_19_theme_and_performance_have_unique_ids_and_focus_markers(self):
        root = xml("Custom_1198_InfinityNav.xml")
        counts = Counter(n.get("id") for n in root.xpath('.//control[@id]'))
        self.assertEqual({id: n for id, n in counts.items() if n > 1}, {})
        for id, label in [(1198310, "UI Theme"), (1198305, "Performance & refresh")]:
            button = control(root, id)
            self.assertEqual(button.findtext("label"), label)
            markers = button.getparent().xpath('./control[@type="image"]/visible/text()')
            self.assertEqual(markers, ["Control.HasFocus(%s)" % id])


if __name__ == "__main__":
    unittest.main(verbosity=2)
