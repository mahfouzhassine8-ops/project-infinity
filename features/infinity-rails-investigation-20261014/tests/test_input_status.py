import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'addons/script.infinity.rails/resources'))
from lib.input_status import classify, collect, keymaps


class InputStatusTests(unittest.TestCase):
    def test_inactive_home_not_failure_even_with_stale_failed_flag(self):
        self.assertEqual(classify(False, True, 'true', '', 0, ''), 'HOME_INACTIVE_NOT_SAMPLED')
    def test_hidden_mode_not_failure(self):
        self.assertEqual(classify(True, False, 'true', '', 0, ''), 'CONTROL_INACTIVE_NOT_SAMPLED')
    def test_dynamic_item_wins_over_stale_failure(self):
        self.assertEqual(classify(True, True, 'true', '', 1, 'true'), 'DYNAMIC_ITEM_OBSERVED')
    def test_explicit_failure_is_separate(self):
        self.assertEqual(classify(True, True, 'true', '', 10, ''), 'HELPER_REPORTED_FAILURE')
    def test_unset_is_not_failure(self):
        self.assertEqual(classify(True, True, '', '', None, ''), 'CONTROL_DATA_UNAVAILABLE')
    def test_zero_items_is_not_failure(self):
        self.assertEqual(classify(True, True, '', '', 0, ''), 'EMPTY_UNCONFIRMED')
    def test_ready_empty_is_not_failure(self):
        self.assertEqual(classify(True, True, '', 'true', 0, ''), 'READY_BUT_EMPTY_UNCONFIRMED')
    def test_static_item_reported(self):
        self.assertEqual(classify(True, True, '', '', 1, ''), 'NON_DYNAMIC_ITEM_OBSERVED')

    def capture(self, window, dialog):
        class Addon:
            def __init__(self, aid): self.aid = aid
            def getAddonInfo(self, key): return {'id': self.aid, 'version': '0.2.3', 'path': '/installed'}.get(key, '')
        class Window:
            def getProperty(self, key): return ''
            def getFocusId(self): return 9200
        queried = []
        def label(key):
            queried.append(key)
            return {'Container(9000).ListItem.Property(section)': 'movies',
                    'Container(9200).NumItems': '1',
                    'Container(9200).ListItem.Property(Infinity.Rails.Item)': 'true',
                    'Container(9200).ListItem.Property(Infinity.Rails.Key)': 'c:plugin.video.test',
                    'Container(9200).ListItem.Property(Addon.ID)': 'plugin.video.test'}.get(key, '')
        with tempfile.TemporaryDirectory() as tmp:
            before = list(Path(tmp).iterdir())
            result = collect(types.SimpleNamespace(getInfoLabel=label, getCondVisibility=lambda s: '(9200)' in s),
                             types.SimpleNamespace(Addon=Addon),
                             types.SimpleNamespace(getCurrentWindowId=lambda: window, getCurrentWindowDialogId=lambda: dialog, Window=lambda _: Window()),
                             types.SimpleNamespace(translatePath=lambda _: tmp))
            self.assertEqual(before, list(Path(tmp).iterdir()))
        return result, queried

    def test_program_window_does_not_query_home_labels(self):
        result, queried = self.capture(10001, 0)
        self.assertEqual(queried, [])
        self.assertEqual(result['sampling'], 'HOME_INACTIVE_NOT_SAMPLED')
    def test_modal_dialog_does_not_query_home_labels(self):
        result, queried = self.capture(10000, 12000)
        self.assertEqual(queried, [])
        self.assertEqual(result['sampling'], 'HOME_INACTIVE_NOT_SAMPLED')
    def test_home_captures_identity_only_for_visible_control(self):
        result, queried = self.capture(10000, 0)
        self.assertEqual(result['helper']['version'], '0.2.3')
        self.assertEqual(result['focus'], 9200)
        self.assertEqual(result['controls'][0]['properties']['Addon.ID'], 'plugin.video.test')
        self.assertEqual(result['controls'][0]['state'], 'DYNAMIC_ITEM_OBSERVED')
        self.assertFalse(any('8820' in q for q in queried))
    def test_actual_kodi_no_modal_sentinel(self):
        result, queried = self.capture(10000, 9999)
        self.assertEqual(result['sampling'], 'HOME_ACTIVE')
        self.assertEqual(result['focus'], 9200)
        self.assertTrue(queried)
    def test_keymaps_reports_override_without_modification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'gen.xml'
            raw = '<keymap><Home><touch><longpress>ActivateWindow(ContextMenu)</longpress></touch></Home></keymap>'
            path.write_text(raw)
            result = keymaps(types.SimpleNamespace(translatePath=lambda _: tmp))
            self.assertEqual(result[0]['mappings'][0]['action'], 'ActivateWindow(ContextMenu)')
            self.assertEqual(path.read_text(), raw)
    def test_bad_xml_is_reported_without_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'broken.xml').write_text('<keymap>')
            result = keymaps(types.SimpleNamespace(translatePath=lambda _: tmp))
            self.assertEqual(result[0]['state'], 'ParseError')

if __name__ == '__main__': unittest.main()
