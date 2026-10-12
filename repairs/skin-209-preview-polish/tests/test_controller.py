import importlib.util
from pathlib import Path
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch

import test_metadata as fixtures

LIB = Path(__file__).resolve().parents[1] / 'delta/resources/lib'


class Control:
    def __init__(self):
        self.enabled = True
        self.text = ''
        self.image = ''
    def setEnabled(self, value):
        self.enabled = value
    def setText(self, value):
        self.text = value
    def setImage(self, value, useCache=True):
        self.image = value


class Parent:
    def __init__(self, path, folder=False):
        self.props = {'Infinity.FilePreview.Path': str(path), 'Infinity.FilePreview.Label': path.name,
                      'Infinity.FilePreview.Folder': 'true' if folder else 'false',
                      'Infinity.FilePreview.Size': '0', 'Infinity.FilePreview.Nonce': '7',
                      'Infinity.FilePreview.Active': 'true', 'Infinity.FilePreview.OptIn': 'v1',
                      'Infinity.FilePreview.NativeVersion': 'v1'}
        self.focus = None
    def getProperty(self, name):
        return self.props.get(name, '')
    def setProperty(self, name, value):
        self.props[name] = value
    def clearProperty(self, name):
        self.props.pop(name, None)
    def setFocusId(self, control):
        self.focus = control


class FakeWindow:
    policy = None
    instances = []
    def __new__(cls, *args, **kwargs):
        result = object.__new__(cls)
        result.controls = {key: Control() for key in (10, 20, 30, 70, 80, 81, 82)}
        result.props = {}
        result.closed = threading.Event()
        result.focus = None
        FakeWindow.instances.append(result)
        return result
    def setProperty(self, name, value):
        self.props[name] = value
    def getControl(self, control):
        return self.controls[control]
    def setFocusId(self, control):
        self.focus = control
    def close(self):
        self.closed.set()
    def doModal(self):
        self.onInit()
        end = time.monotonic() + 6
        while self.session.state == 'loading' and time.monotonic() < end:
            time.sleep(0.01)
        if self.session.state == 'loading':
            raise AssertionError('Metadata worker did not complete')
        FakeWindow.policy(self)
        if not self.closed.wait(6):
            self.session.cancel()
            self.close()
            raise AssertionError('Dialog failed to close')


class ControllerTests(unittest.TestCase):
    setUp = fixtures.MetadataTests.setUp
    tearDown = fixtures.MetadataTests.tearDown
    make = fixtures.MetadataTests.make
    # Reuse only the archive fixture setup, not the parent suite's test methods.
    def run_controller(self, policy, folder=False, argv=None):
        self.make()
        parent = Parent(self.directory if folder else self.archive, folder)
        commands = []
        def execute(command, wait=False):
            self.assertTrue(wait)
            self.assertEqual(parent.getProperty('Infinity.FilePreview.AcceptNonce'), '7')
            commands.append(command)
        xbmc = types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz',
                                    executebuiltin=execute, log=lambda *args: None, LOGWARNING=2,
                                    Monitor=lambda: types.SimpleNamespace(abortRequested=lambda: False))
        xbmcgui = types.SimpleNamespace(WindowXMLDialog=FakeWindow, Window=lambda owner: parent)
        vfs = types.SimpleNamespace(translatePath=lambda value: str(self.directory) if value == 'special://skin' else value)
        FakeWindow.instances = []
        FakeWindow.policy = policy
        spec = importlib.util.spec_from_file_location('preview_controller_test', LIB / 'infinity_file_preview.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'xbmc': xbmc, 'xbmcgui': xbmcgui, 'xbmcvfs': vfs}), patch.object(sys, 'argv', argv or ['preview.py', '75662']):
            spec.loader.exec_module(module)
            module.main()
        for dialog in FakeWindow.instances:
            self.assertTrue(dialog.closed.is_set())
            self.assertFalse(dialog.worker.is_alive())
            self.assertTrue(dialog.check_worker is None or not dialog.check_worker.is_alive())
        return parent, commands, FakeWindow.instances

    def test_ui_cancel_returns_selection_without_install(self):
        parent, commands, instances = self.run_controller(lambda dialog: dialog.onClick(81))
        self.assertEqual(commands, [])
        self.assertEqual(parent.focus, 450)
        self.assertEqual(parent.getProperty('Infinity.FilePreview.Nonce'), '')
        self.assertEqual(instances[0].focus, 81)

    def test_ui_back_returns_selection_without_install(self):
        parent, commands, _ = self.run_controller(lambda dialog: dialog.onAction(types.SimpleNamespace(getId=lambda: 92)))
        self.assertEqual(commands, [])
        self.assertEqual(parent.focus, 450)

    def test_ui_explicit_install_uses_exact_native_instance(self):
        _, commands, instances = self.run_controller(lambda dialog: dialog.onClick(80))
        self.assertEqual(commands, ['SendClick(75662,9411)'])
        self.assertTrue(instances[0].accepted)

    def test_ui_folder_has_no_install(self):
        def policy(dialog):
            self.assertFalse(dialog.getControl(80).enabled)
            dialog.onClick(80)
            self.assertEqual(dialog.session.state, 'ready')
            dialog.onClick(81)
        _, commands, _ = self.run_controller(policy, folder=True)
        self.assertEqual(commands, [])

    def test_owner_closed_disposes_orphan_preview(self):
        def policy(dialog):
            dialog.parent.clearProperty('Infinity.FilePreview.Nonce')
        _, commands, _ = self.run_controller(policy)
        self.assertEqual(commands, [])

    def test_foreign_window_is_rejected(self):
        _, commands, instances = self.run_controller(lambda dialog: dialog.onClick(81), argv=['preview.py', '10000'])
        self.assertEqual(instances, [])
        self.assertEqual(commands, [])

    def test_duplicate_install_click_only_creates_one_confirmation(self):
        def policy(dialog):
            dialog.onClick(80)
            dialog.onClick(80)
        _, commands, _ = self.run_controller(policy)
        self.assertEqual(len(commands), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
