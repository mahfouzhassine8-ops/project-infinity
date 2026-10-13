"""Run every inherited preview case on211; add geometry and compact-data cases."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RECIPE = HERE.parent
PREVIOUS = RECIPE.parent / 'skin-210-critical-correction'
OLD = RECIPE.parent / 'skin-209-preview-polish'
sys.path[:0] = [str(RECIPE / 'runtime'), str(PREVIOUS / 'tests'), str(OLD / 'tests')]
import test_preview_lifecycle as previous
import test_controller as fixtures
from infinity_preview_geometry import layout


class CompactControllerTests(previous.ControllerTests):
    """Original test methods remain unchanged; only the Kodi API adapter grows."""
    def drive(self, path, policy, folder=False, argv=None, fault=None):
        if path == PREVIOUS / 'runtime/infinity_file_preview.py':
            path = RECIPE / 'runtime/infinity_file_preview.py'
        original = fixtures.FakeWindow.getControl
        def control(dialog, control_id):
            if control_id == 1:
                def apply(animations):
                    dialog.props['test.animations'] = animations
                return types.SimpleNamespace(setAnimations=apply)
            return original(dialog, control_id)
        def width(dialog):
            if fault == 'geometry':
                raise RuntimeError('Injected geometry API failure')
            return 1080
        with patch.object(fixtures.FakeWindow, 'getControl', control), \
                patch.object(fixtures.FakeWindow, 'getWidth', width, create=True), \
                patch.object(fixtures.FakeWindow, 'getHeight', lambda self: 2400, create=True):
            return super().drive(path, policy, folder, argv, fault)

    def test_compact_uses_actual_metadata_and_preserves_zip_glyph(self):
        def policy(dialog):
            metadata = dialog.session.metadata
            self.assertEqual(dialog.props['Preview.Title'], metadata.name)
            self.assertEqual(dialog.props['Preview.Subtitle'], metadata.addon_id)
            self.assertIn(metadata.version, dialog.props['Preview.Summary'])
            self.assertEqual(dialog.props['Preview.Status'], '')
            self.assertEqual(dialog.getControl(20).text, '')
            self.assertEqual(dialog.getControl(10).image, '')
            self.assertEqual(dialog.props['Preview.LayoutReady'], 'true')
            dialog.onClick(81)
        self.run_controller(policy)

    def test_close_x_uses_same_cancel_and_selection_restore(self):
        parent, commands, _ = self.run_controller(lambda dialog: dialog.onClick(82))
        self.assertEqual(parent.focus, 450)
        self.assertEqual(commands, [])

    def test_geometry_failure_closes_and_releases_request(self):
        parent, commands, dialogs, _ = self.drive(RECIPE / 'runtime/infinity_file_preview.py', lambda dialog: None, fault='geometry')
        self.assertTrue(dialogs[0].closed.is_set())
        self.assertIsNone(dialogs[0].worker)
        self.assertEqual(parent.getProperty('Infinity.FilePreview.Active'), '')
        self.assertEqual(commands, [])

    def test_changed_file_confirmation_retains_visible_warning(self):
        import copy
        import time
        def policy(dialog):
            changed = copy.copy(dialog.session.metadata)
            changed.fingerprint = (*changed.fingerprint[:-1], changed.fingerprint[-1] + 1)
            with patch.object(dialog, 'read_metadata', return_value=changed):
                dialog.onClick(80)
                dialog.check_worker.join(timeout=3)
            self.assertFalse(dialog.accepted)
            self.assertEqual(dialog.session.state, 'ready')
            self.assertIn('This file changed', dialog.props['Preview.Status'])
            self.assertIn('This file changed', dialog.getControl(20).text)
            dialog.onClick(81)
        _, commands, _ = self.run_controller(policy)
        self.assertEqual(commands, [])

    def test_geometry_reflows_without_new_worker_or_nonce(self):
        def policy(dialog):
            worker, nonce = dialog.worker, dialog.nonce
            old = dialog.props['test.animations']
            dialog.parent.setProperty('Infinity.NativeWidthDp', '900')
            dialog.parent.setProperty('Infinity.NativeHeightDp', '720')
            dialog.update_geometry()
            self.assertNotEqual(old, dialog.props['test.animations'])
            self.assertIs(worker, dialog.worker)
            self.assertEqual(nonce, dialog.nonce)
            dialog.onClick(81)
        self.run_controller(policy)

    def test_repeated_open_cancel_leaves_no_workers_or_request(self):
        for number in range(30):
            parent, commands, dialogs = self.run_controller(lambda dialog: dialog.onClick(81 if number % 2 else 82))
            self.assertEqual(commands, [])
            self.assertEqual(parent.getProperty('Infinity.FilePreview.Active'), '')
            self.assertFalse(dialogs[0].worker.is_alive())

    def test_incomplete_native_resize_keeps_last_complete_transform(self):
        def policy(dialog):
            old = dialog.props['test.animations']
            dialog.parent.setProperty('Infinity.NativeReady', 'false')
            dialog.parent.setProperty('Infinity.NativeWidthDp', '900')
            dialog.update_geometry()
            self.assertEqual(old, dialog.props['test.animations'])
            dialog.parent.setProperty('Infinity.NativeHeightDp', '720')
            dialog.parent.setProperty('Infinity.NativeReady', 'true')
            dialog.parent.setProperty('Infinity.NativeDisplayRevision', '8')
            dialog.update_geometry()
            self.assertNotEqual(old, dialog.props['test.animations'])
            dialog.onClick(81)
        self.run_controller(policy)

    def test_interleaved_native_revision_cannot_apply_mixed_bounds(self):
        def policy(dialog):
            old = dialog.props['test.animations']
            original = dialog.parent.getProperty
            seen = [0]
            def read(name):
                if name == 'Infinity.NativeDisplayRevision':
                    seen[0] += 1
                    return str(seen[0])
                if name == 'Infinity.NativeWidthDp': return '900'
                if name == 'Infinity.NativeHeightDp': return '720'
                return original(name)
            with patch.object(dialog.parent, 'getProperty', side_effect=read):
                dialog.update_geometry()
            self.assertEqual(old, dialog.props['test.animations'])
            dialog.onClick(81)
        self.run_controller(policy)

    def test_stale_nonce_during_confirm_cannot_install(self):
        def policy(dialog):
            dialog.parent.setProperty('Infinity.FilePreview.Nonce', '8')
            dialog.onClick(80)
            self.assertFalse(dialog.accepted)
            dialog.onClick(81)
        parent, commands, _ = self.run_controller(policy)
        self.assertEqual(commands, [])
        self.assertEqual(parent.getProperty('Infinity.FilePreview.Nonce'), '8')


class GeometryTests(unittest.TestCase):
    def test_cover_inner_landscape_split_and_float(self):
        for width, height in [(384,854),(800,720),(854,384),(360,720),(420,300),(280,320)]:
            with self.subTest(width=width,height=height):
                g = layout(1080,2400,width,height)
                expected = min(340, width - 24, (height - 24)*340/220)
                self.assertAlmostEqual(g['width_dp'],expected)
                self.assertAlmostEqual(g['left']*2+g['width'],1080)
                self.assertAlmostEqual(g['top']*2+g['height'],2400)
                self.assertGreaterEqual(g['left'],0)
                self.assertGreaterEqual(g['top'],0)

    def test_random_bounds_are_centered_and_inside_usable_area(self):
        import random
        rng = random.Random(211)
        for _ in range(1000):
            dw,dh = rng.uniform(80,1800),rng.uniform(80,1800)
            lw,lh = rng.uniform(300,4000),rng.uniform(300,4000)
            g = layout(lw,lh,dw,dh)
            self.assertLessEqual(g['width'],lw)
            self.assertLessEqual(g['height'],lh)
            self.assertLessEqual(g['width_dp'],340)
            self.assertLessEqual(g['height_dp'],220)
            self.assertGreater(g['fit'],0)

    def test_missing_native_dp_is_explicit_approximation(self):
        for w,h in [('',None),('NaN','100'),('100','Infinity'),('4000','3000')]:
            g = layout(1080,2400,w,h)
            self.assertFalse(g['dp_verified'])
            self.assertEqual(g['width_dp'],340)

    def test_invalid_window_bounds_fail_before_display(self):
        for w,h in [(0,1080),(-1,100),('NaN',100),(100,float('inf'))]:
            with self.assertRaises(ValueError):
                layout(w,h,384,854)


if __name__ == '__main__':
    unittest.main(verbosity=2)
