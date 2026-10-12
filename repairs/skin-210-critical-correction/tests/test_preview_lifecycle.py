import builtins
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / 'skin-209-preview-polish'
sys.path.insert(0, str(OLD / 'tests'))
import test_controller as inherited


class ControllerTests(inherited.ControllerTests):
    """Run the seven original behavior cases on the new controller unchanged.

The adapter now supplies Kodi.LOGINFO and can inject initialization/import faults.
No actual Kodi renderer or device touch event is simulated by this class.
"""
    def drive(self, path, policy, folder=False, argv=None, fault=None):
        self.make()
        parent = inherited.Parent(self.directory if folder else self.archive, folder)
        commands, logs = [], []
        def execute(command, wait=False):
            self.assertTrue(wait)
            self.assertEqual(parent.getProperty('Infinity.FilePreview.AcceptNonce'), '7')
            commands.append(command)
        xbmc = types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz', LOGINFO=1, LOGWARNING=2,
                                    executebuiltin=execute, log=lambda *args: logs.append(args),
                                    Monitor=lambda: types.SimpleNamespace(abortRequested=lambda: False))
        gui = types.SimpleNamespace(WindowXMLDialog=inherited.FakeWindow, Window=lambda owner: parent)
        vfs = types.SimpleNamespace(translatePath=lambda value: str(self.directory) if value == 'special://skin' else value)
        inherited.FakeWindow.instances = []; inherited.FakeWindow.policy = policy
        spec = importlib.util.spec_from_file_location('candidate_preview_lifecycle', path)
        module = importlib.util.module_from_spec(spec)
        importer = builtins.__import__
        def import_with_fault(name, *args, **kwargs):
            if fault == 'import' and name == 'infinity_zip_metadata':
                raise ModuleNotFoundError('Injected missing preview dependency')
            return importer(name, *args, **kwargs)
        original_control = inherited.FakeWindow.getControl
        def get_control(dialog, control):
            if fault == 'control' and control == 80:
                raise KeyError('Injected missing Install control')
            return original_control(dialog, control)
        original_modal = inherited.FakeWindow.doModal
        def modal(dialog):
            if fault == 'modal':
                dialog.onInit()
                raise RuntimeError('Injected modal callback failure')
            return original_modal(dialog)
        with patch.dict(sys.modules, {'xbmc': xbmc, 'xbmcgui': gui, 'xbmcvfs': vfs}), \
                patch.object(sys, 'argv', argv or ['preview.py', '75662']), \
                patch('builtins.__import__', side_effect=import_with_fault), \
                patch.object(inherited.FakeWindow, 'getControl', get_control), \
                patch.object(inherited.FakeWindow, 'doModal', modal):
            spec.loader.exec_module(module)
            module.main()
        return parent, commands, inherited.FakeWindow.instances, logs

    def run_controller(self, policy, folder=False, argv=None):
        parent, commands, instances, _ = self.drive(HERE.parent / 'runtime/infinity_file_preview.py', policy, folder, argv)
        for dialog in instances:
            self.assertTrue(dialog.closed.is_set())
            self.assertTrue(dialog.worker is None or not dialog.worker.is_alive())
            self.assertTrue(dialog.check_worker is None or not dialog.check_worker.is_alive())
        return parent, commands, instances

    def test_missing_controls_close_modal_instead_of_leaving_empty_window(self):
        old, commands, dialogs, _ = self.drive(OLD / 'delta/resources/lib/infinity_file_preview.py', lambda dialog: None, fault='control')
        self.assertFalse(dialogs[0].closed.is_set(), 'Negative control must reproduce absent cleanup')
        parent, commands, dialogs, _ = self.drive(HERE.parent / 'runtime/infinity_file_preview.py', lambda dialog: None, fault='control')
        self.assertTrue(dialogs[0].closed.is_set())
        self.assertEqual(commands, [])
        self.assertEqual(parent.getProperty('Infinity.FilePreview.Active'), '')

    def test_modal_exception_cancels_worker_and_returns_picker(self):
        parent, commands, dialogs, _ = self.drive(HERE.parent / 'runtime/infinity_file_preview.py', lambda dialog: None, fault='modal')
        self.assertTrue(dialogs[0].closed.is_set())
        self.assertFalse(dialogs[0].worker.is_alive())
        self.assertEqual(parent.getProperty('Infinity.FilePreview.Active'), '')
        self.assertEqual(parent.focus, 450)
        self.assertEqual(commands, [])

    def test_import_exception_releases_native_request(self):
        with self.assertRaises(ModuleNotFoundError):
            self.drive(OLD / 'delta/resources/lib/infinity_file_preview.py', lambda dialog: None, fault='import')
        parent, commands, dialogs, logs = self.drive(HERE.parent / 'runtime/infinity_file_preview.py', lambda dialog: None, fault='import')
        self.assertEqual((commands, dialogs), ([], []))
        self.assertEqual(parent.getProperty('Infinity.FilePreview.Active'), '')
        self.assertEqual(parent.getProperty('Infinity.FilePreview.Nonce'), '')
        self.assertTrue(any('metadata-modules' in args[0] for args in logs))


if __name__ == '__main__':
    unittest.main(verbosity=2)
