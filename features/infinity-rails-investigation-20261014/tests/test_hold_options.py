"""Exact native identity delivery and dismissal; legacy launch/storage tests retained."""
import unittest
from unittest.mock import patch
from test_runtime_rc5 import RuntimeTests, runtime


class HoldOptionsTests(RuntimeTests):
    # Do not inherit/recount the historical tests as new cases.
    def setUp(self):
        super().setUp()
        self.gui.getCurrentWindowId=lambda:10000
        self.gui.getCurrentWindowDialogId=lambda:9999
        self.info['Container(9000).ListItem.Property(section)']='tvshows'
        self.row={'addon_id':'plugin.video.fixture','label':'Fixture','key':'c:plugin.video.fixture','custom':True}

    def test_hold_delivers_exact_identity_and_open(self):
        self.answers=[0]
        with patch.object(runtime,'selected_card',return_value=self.row) as resolve, patch.object(runtime,'card_action') as action:
            runtime.main(['options','tvshows',self.row['key'],self.row['addon_id']])
        resolve.assert_called_once_with('tvshows',self.row['key'])
        action.assert_called_once_with('open','tvshows',self.row['key'])
        self.assertNotIn('Infinity.Rails.OptionsActive',self.properties)

    def test_hold_cancel_does_not_launch(self):
        self.answers=[-1]
        with patch.object(runtime,'selected_card',return_value=self.row), patch.object(runtime,'card_action') as action:
            runtime.options('tvshows',self.row['key'],self.row['addon_id'])
        action.assert_not_called()
        self.assertNotIn('Infinity.Rails.OptionsActive',self.properties)

    def test_hold_rejects_stale_addon_identity(self):
        with patch.object(runtime,'selected_card',return_value=self.row), self.assertRaises(runtime.RailError):
            runtime.options('tvshows',self.row['key'],'plugin.video.other')
        self.assertNotIn('Infinity.Rails.OptionsActive',self.properties)

    def test_hold_queued_after_navigation_is_ignored(self):
        self.info['Container(9000).ListItem.Property(section)']='movies'
        with patch.object(runtime,'selected_card') as resolve:
            runtime.options('tvshows',self.row['key'],self.row['addon_id'])
        resolve.assert_not_called()

    def test_hold_does_not_open_over_another_modal(self):
        self.gui.getCurrentWindowDialogId=lambda:13000
        with patch.object(runtime,'selected_card') as resolve:
            runtime.options('tvshows',self.row['key'],self.row['addon_id'])
        resolve.assert_not_called()

    def test_hold_exception_clears_menu_guard(self):
        with patch.object(runtime,'selected_card',return_value=self.row), patch.object(runtime,'select',side_effect=RuntimeError('dialog error')), self.assertRaises(RuntimeError):
            runtime.options('tvshows',self.row['key'],self.row['addon_id'])
        self.assertNotIn('Infinity.Rails.OptionsActive',self.properties)

    def test_hold_directory_opt_in_keeps_launch_target(self):
        self.plugin('tvshows')
        for url,item,folder in self.listing:
            self.assertEqual(item.props['Infinity.Rails.HoldVersion'],'1')
            self.assertTrue(folder)
            self.assertTrue(url.startswith('plugin://'))


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(HoldOptionsTests(name) for name in HoldOptionsTests.__dict__ if name.startswith('test_'))
