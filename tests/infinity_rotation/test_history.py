"""Corrupt diagnostic history must neither crash startup nor invent a crash loop."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'addons/service.infinity.compat'))
for name in ('xbmc', 'xbmcaddon', 'xbmcgui', 'xbmcvfs'):
    sys.modules[name] = MagicMock()
spec = importlib.util.spec_from_file_location('compat_service', ROOT / 'addons/service.infinity.compat/service.py')
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class Addon:
    def __init__(self):
        self.values = {}
    def getSetting(self, key):
        return self.values.get(key, '')
    def setSetting(self, key, value):
        self.values[key] = value


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addon = Addon()

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def test_wrong_json_shapes_are_recovered(self):
        for value in ([], 'broken', 1, None, {'unclean_starts': '123', 'auto_safe_activations': 'broken'}):
            with self.subTest(value=value):
                self.write('startup-history.json', value)
                self.write('startup-marker.json', [])
                self.assertEqual(service.register_start(self.root, self.addon), (False, 0, 3))
                service.mark_stable(self.root)

    def test_future_and_invalid_timestamps_do_not_force_safe_mode(self):
        now = int(service.time.time())
        self.write('startup-history.json', {'unclean_starts': [None, {}, 'bad', True, -1, now + 99999], 'auto_safe_activations': None})
        self.write('startup-marker.json', {'timestamp': now + 99999})
        self.assertEqual(service.register_start(self.root, self.addon), (False, 0, 3))
        self.assertNotEqual(self.addon.getSetting('compat_mode'), 'safe')

    def test_real_recent_unclean_starts_still_trigger_safe_mode(self):
        now = int(service.time.time())
        self.write('startup-history.json', {'unclean_starts': [now - 60, now - 30], 'auto_safe_activations': 2})
        self.write('startup-marker.json', {'timestamp': now - 10})
        self.assertEqual(service.register_start(self.root, self.addon), (True, 3, 3))
        self.assertEqual(self.addon.getSetting('compat_mode'), 'safe')
        self.assertEqual(json.loads((self.root / 'startup-history.json').read_text())['auto_safe_activations'], 3)

    def test_stale_history_expires_and_clean_start_is_not_counted(self):
        self.write('startup-history.json', {'unclean_starts': [int(service.time.time()) - 1000]})
        self.assertEqual(service.register_start(self.root, self.addon), (False, 0, 3))


if __name__ == '__main__':
    unittest.main()
