"""Focused, offline icon-resource exception checks; no app/shutdown execution."""
import unittest
from pathlib import Path
import struct
import resources as icon


def originals():
    return {name: (icon.HERE/"reference"/Path(name).name).read_bytes() for name in icon.BASELINE_SHA256}


class IconResourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = originals()
        cls.changed = icon.expected_resources(cls.before)
        cls.candidate = cls.before | cls.changed

    def test_two_ids_only_and_correct_day_night_paths_at_all_existing_configurations(self):
        old, _ = icon.table_entries(self.before[icon.TABLE])
        new, _ = icon.table_entries(self.changed[icon.TABLE])
        self.assertEqual(14, len(new)-len(old))
        self.assertEqual({k: v for k, v in old.items() if k[0] not in icon.ICON_IDS},
                         {k: v for k, v in new.items() if k[0] not in icon.ICON_IDS})
        for (rid, config), (name, value) in old.items():
            if rid not in icon.ICON_IDS: continue
            self.assertEqual(3, value[0])
            mode = bytearray(config); mode[29] = 0x20
            self.assertEqual((name, value), new[rid, bytes(mode)])
            day = new[rid, config]
            self.assertEqual(name, day[0])
            self.assertIn(day[1][1], icon.NEW_PATHS)
            self.assertNotEqual(value, day[1])

    def test_dark_originals_and_existing_resource_names_preserved(self):
        report = icon.verify_resources(self.candidate, self.before)
        self.assertEqual("PASS_EXACT_ICON_ONLY_TABLE_TRANSFORM", report["status"])
        self.assertEqual(0, report["new_resource_ids"])
        for path, sha in icon.BASELINE_SHA256.items():
            if path != icon.TABLE:
                self.assertEqual(sha, icon.digest(self.candidate[path]))

    def test_existing_adaptive_foreground_and_monochrome_silhouettes_identical(self):
        a = icon.png_rgba(self.before[icon.FOREGROUND_PATH])
        b = icon.png_rgba(self.before[icon.MONO_PATH])
        self.assertEqual((432, 432), a[:2]); self.assertEqual(a[:2], b[:2])
        self.assertEqual(a[2][3::4], b[2][3::4])
        self.assertTrue(all(v == 255 for i, v in enumerate(b[2]) if i % 4 != 3))

    def test_legacy_white_black_and_exact_original_tile_alpha(self):
        for density, (qualifier, size) in icon.DENSITIES.items():
            old = icon.png_rgba(self.before[icon.LEGACY_PATHS[density][0]])
            day = icon.png_rgba(self.changed["res/infinity_launcher_light_"+qualifier+".png"])
            self.assertEqual((size, size), day[:2]); self.assertEqual(old[2][3::4], day[2][3::4])
            pixels = list(zip(day[2][0::4], day[2][1::4], day[2][2::4]))
            self.assertTrue(all(r == g == b for r, g, b in pixels))
            self.assertIn((255,255,255), pixels)
            # A subpixel-resampled48px mask need not land on an alpha255
            # source pixel. Require near-black ink rather than changing the
            # approved alpha to force one artificially opaque destination.
            self.assertLessEqual(min(r for r, g, b in pixels), 8)

    def test_adaptive_bitmap_is_original_mask_tinted_black_on_white(self):
        for sdk in (26, 33):
            data = self.changed["res/infinity_launcher_light_v"+str(sdk)+".xml"]
            strings = []; starts = []
            for p, typ, head, size in icon.chunks(data, 8, len(data)):
                if typ == 1: strings = icon.string_pool(data, p)
                if typ == 0x102:
                    e = p+head; name = strings[struct.unpack_from("<I", data, e+4)[0]]
                    start, stride, count = struct.unpack_from("<HHH", data, e+8); attrs = {}
                    for i in range(count):
                        at = e+start+i*stride
                        attr = strings[struct.unpack_from("<I", data, at+4)[0]]
                        attrs[attr] = (data[at+15], struct.unpack_from("<I", data, at+16)[0])
                    starts.append((name, attrs))
            self.assertIn(("background", {"drawable": (0x1C, 0xFFFFFFFF)}), starts)
            self.assertIn(("bitmap", {"src": (1, icon.MONO_ID), "tint": (0x1C, 0xFF000000)}), starts)
            self.assertEqual(sdk == 33, any(n == "monochrome" for n, _ in starts))

    def test_no_platform_png_encoder_or_timestamp_dependency(self):
        for path, data in self.changed.items():
            if path.endswith(".png"):
                w, h, rgba = icon.png_rgba(data)
                self.assertEqual(data, icon.png_encode(w, h, rgba))

    def test_reject_changed_dark_asset(self):
        bad = dict(self.candidate); bad[icon.FOREGROUND_PATH] += b"different"
        with self.assertRaisesRegex(ValueError, "Original dark/source asset changed"):
            icon.verify_resources(bad, self.before)

    def test_reject_changed_non_icon_table_entry_or_missing_light_member(self):
        bad = dict(self.candidate); table = bytearray(bad[icon.TABLE]); table[-1] ^= 1; bad[icon.TABLE] = bytes(table)
        with self.assertRaisesRegex(ValueError, "Unexpected light/table resource output"):
            icon.verify_resources(bad, self.before)
        bad = dict(self.candidate); bad.pop(next(iter(icon.NEW_PATHS)))
        with self.assertRaisesRegex(ValueError, "Unexpected light/table resource output"):
            icon.verify_resources(bad, self.before)

    def test_reject_unpinned_original_table(self):
        bad = dict(self.before); bad[icon.TABLE] += b"changed"
        with self.assertRaisesRegex(ValueError, "Original launcher input mismatch"):
            icon.expected_resources(bad)


if __name__ == "__main__": unittest.main()
