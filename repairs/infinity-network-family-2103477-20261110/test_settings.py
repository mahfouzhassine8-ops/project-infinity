"""Focused menu/persistence contract checks; Kodi runtime remains a separate gate."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('network_connections',
    HERE / 'overlay/script.infinity.commandcenter/network_connections.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Settings(unittest.TestCase):
    def run_menu(self, pick, value='', skin='skin.infinity.diggz', save=True):
        settings = {'network_family': value, 'unrelated': 'preserved'}
        writes = []
        def set_value(owner, key, new):
            writes.append((owner, key, new))
            if save:
                settings[key] = new
            return save
        dialog = Mock()
        choose = Mock(return_value=pick)
        addon = types.SimpleNamespace(getSetting=lambda key: settings.get(key, ''))
        with patch.dict(sys.modules, {
                'xbmc': types.SimpleNamespace(getSkinDir=lambda: skin),
                'xbmcaddon': types.SimpleNamespace(Addon=lambda owner: addon),
                'xbmcgui': types.SimpleNamespace(Dialog=lambda: dialog),
                'common': types.SimpleNamespace(addon_set_setting=set_value),
                'infinity_settings': types.SimpleNamespace(choose=choose)}):
            module.open_connections()
        return settings, writes, dialog, choose

    def test_missing_or_corrupt_default_is_auto(self):
        for value in ['', None, 'unknown', 'IPv4']:
            self.assertEqual(module.normalized(value), 'auto')

    def test_each_selection_uses_only_existing_setting_owner(self):
        for index, value in enumerate(module.MODES):
            state, writes, dialog, _ = self.run_menu(index)
            self.assertEqual(writes, [(module.OWNER, module.KEY, value)])
            self.assertEqual(state, {'network_family': value, 'unrelated': 'preserved'})
            dialog.notification.assert_called_once()

    def test_existing_selection_is_reloaded_for_menu_focus(self):
        _, writes, _, choose = self.run_menu(-1, 'ipv6')
        self.assertFalse(writes)
        self.assertEqual(choose.call_args.args[2], 2)

    def test_back_writes_nothing(self):
        self.assertFalse(self.run_menu(-1)[1])

    def test_coverage_does_not_change_setting(self):
        _, writes, dialog, _ = self.run_menu(3)
        self.assertFalse(writes)
        dialog.textviewer.assert_called_once()

    def test_save_failure_is_reported(self):
        _, _, dialog, _ = self.run_menu(2, save=False)
        dialog.ok.assert_called_once()
        dialog.notification.assert_not_called()

    def test_other_skin_is_unaffected(self):
        _, writes, dialog, choose = self.run_menu(2, skin='skin.estuary')
        self.assertFalse(writes)
        choose.assert_not_called()
        dialog.notification.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
