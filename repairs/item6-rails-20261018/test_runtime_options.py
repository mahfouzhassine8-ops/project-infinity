#!/usr/bin/env python3
"""#6: preserve actual Rails .026 Home Movie/TV hold -> exact options dispatch."""
import argparse
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

class RailOptionsRoute(unittest.TestCase):
    ROOT=None
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(cls.ROOT/'resources'))
        from lib import runtime,mocha
        cls.runtime=runtime
        cls.mocha=mocha

    def setUp(self):
        self.row=dict(addon_id='plugin.video.fixture',key='c:plugin.video.fixture',
                      label='Fixture',custom=True)
        self.props={}
        self.home=types.SimpleNamespace(
            getProperty=lambda k:self.props.get(k,''),
            setProperty=lambda k,v:self.props.__setitem__(k,v),
            clearProperty=lambda k:self.props.pop(k,None))
        self.gui=types.SimpleNamespace(getCurrentWindowId=lambda:10000,
            getCurrentWindowDialogId=lambda:9999,Window=lambda id:self.home)
        self.xbmc=types.SimpleNamespace(getInfoLabel=lambda k:
            'movies' if k=='Container(9000).ListItem.Property(section)' else '',
            log=lambda *a:None,LOGINFO=1)
        monitor=types.SimpleNamespace(abortRequested=lambda:False)
        self.patchers=[
            mock.patch.object(self.runtime,'setup',return_value=(self.xbmc,None,self.gui,None,self.ROOT,self.ROOT,monitor)),
            mock.patch.object(self.runtime,'need_candidate',return_value=True),
            mock.patch.object(self.runtime,'selected_card',return_value=self.row),
            mock.patch.object(self.runtime,'has_settings',return_value=True),
            mock.patch.object(self.runtime,'card_action'),
            mock.patch.object(self.mocha,'rail_options',return_value='move')]
        self.calls=[p.start() for p in self.patchers]

    def tearDown(self):
        for p in reversed(self.patchers):p.stop()

    def test_movie_first_hold_targets_selected_addon(self):
        self.runtime.options('movies',self.row['key'],self.row['addon_id'])
        self.calls[-1].assert_called_once_with(self.row,'movies',True,self.ROOT)
        self.calls[-2].assert_called_once_with('move','movies',self.row['key'])
        self.assertNotIn('Infinity.Rails.OptionsActive',self.props)

    def test_tv_cancel_never_launches_or_modifies_store(self):
        self.xbmc.getInfoLabel=lambda k:'tvshows'
        self.calls[-1].return_value='cancel'
        self.runtime.options('tvshows',self.row['key'],self.row['addon_id'])
        self.calls[-1].assert_called_once_with(self.row,'tvshows',True,self.ROOT)
        self.calls[-2].assert_not_called()
        self.assertNotIn('Infinity.Rails.OptionsActive',self.props)

    def test_wrong_held_card_identity_rejected(self):
        with self.assertRaises(self.runtime.RailError):
            self.runtime.options('movies',self.row['key'],'plugin.video.other')
        self.calls[-1].assert_not_called()
        self.calls[-2].assert_not_called()

    def test_foreign_windows_modals_and_duplicate_popup_are_noop(self):
        self.gui.getCurrentWindowId=lambda:9999
        self.runtime.options('movies',self.row['key'],self.row['addon_id'])
        self.gui.getCurrentWindowId=lambda:10000
        self.gui.getCurrentWindowDialogId=lambda:13000
        self.runtime.options('movies',self.row['key'],self.row['addon_id'])
        self.gui.getCurrentWindowDialogId=lambda:9999
        self.props['Infinity.Rails.OptionsActive']='true'
        self.runtime.options('movies',self.row['key'],self.row['addon_id'])
        self.calls[-1].assert_not_called()
        self.calls[-2].assert_not_called()

    def test_popup_exception_clears_active_guard(self):
        self.calls[-1].side_effect=RuntimeError('Kodi dialog fixture failed')
        with self.assertRaisesRegex(RuntimeError,'Kodi dialog fixture failed'):
            self.runtime.options('movies',self.row['key'],self.row['addon_id'])
        self.assertNotIn('Infinity.Rails.OptionsActive',self.props)
        self.calls[-2].assert_not_called()

def run_tests(rails):
    RailOptionsRoute.ROOT=Path(rails)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(RailOptionsRoute)
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--extracted-original-helper',type=Path,required=True)
    a=p.parse_args();run_tests(a.extracted_original_helper)
