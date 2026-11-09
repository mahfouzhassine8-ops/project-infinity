"""Selected new service-boundary guards; no app, signer or tracker suite.

Execute the unchanged action_loading source with its actual original source
loader and code objects. The host SDK double adds a Python traceback frame;
remove only that double's frame to model the recorded native C++ SDK throw.
No installed first-party loader, runtime module or sys.modules is modified.
"""
import ast
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'reference/script.infinity.commandcenter'
RELATIVE = 'script.infinity.commandcenter/action_loading.py'
PIN = '8b758bba6eabd7a051213834c136a81d52c6af819ff9c6d7d1f456a45be4474f'


class Window:
    def __init__(self, fail_write=False): self.fail_write = fail_write
    def getProperty(self, key):
        if key in ('Infinity.Experience', 'Infinity.NativeExperience'): return 'infinity'
        if key.endswith('FrameControls'): return '|50|'
        return ''
    def getFocusId(self): return 50
    def setProperty(self, *args):
        if self.fail_write: raise RuntimeError('Window id does not exist')
    def clearProperty(self, *args): pass


class Survival(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('host_original_module_contract', REFERENCE / 'module_contract.py')
        self.original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.original)
        self.current_calls, self.messages, self.fail_current = [], [], False
        def current():
            self.current_calls.append(True)
            if self.fail_current: raise RuntimeError('Authenticated generation retired')
        self.contract = SimpleNamespace(root=REFERENCE.parent, files={RELATIVE: PIN}, current=current)
        raw = (REFERENCE / 'action_loading.py').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PIN)
        loader = self.original._SourceLoader(self.contract, str(REFERENCE / 'action_loading.py'), raw)
        module_spec = importlib.util.spec_from_loader('host_unchanged_loading_owner', loader)
        self.owner = importlib.util.module_from_spec(module_spec)
        loader.exec_module(self.owner)
        self.current_calls.clear()
        source = HERE / 'overlay/script.infinity.commandcenter/service.py'
        nodes = [node for node in ast.parse(source.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == '_tick_loading_observer']
        self.assertEqual(len(nodes), 1)
        namespace = dict(_infinity_contract=self.contract, _infinity_contract_module=self.original, log=self.messages.append)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec', optimize=1), namespace)
        self.tick = namespace['_tick_loading_observer']

    def sdk(self, fail='frame', message='Window id does not exist', fail_write=False):
        home, content = Window(fail_write), Window()
        def window(identifier):
            if (fail == 'home' and identifier == 10000) or (fail == 'frame' and identifier == 13000):
                raise RuntimeError(message)
            return home if identifier == 10000 else content
        gui = SimpleNamespace(Window=window, getCurrentWindowId=lambda: 10025, getCurrentWindowDialogId=lambda: 13000)
        xbmc = SimpleNamespace(Monitor=object, getSkinDir=lambda: 'skin.infinity.diggz',
                              getInfoLabel=lambda value: '', getCondVisibility=lambda value: False)
        return xbmc, gui

    def native_throw_monitor(self, operation):
        def tick(foreground=True):
            try:
                return operation(foreground)
            except RuntimeError as error:
                traceback = error.__traceback__
                while traceback.tb_next is not None:
                    if traceback.tb_frame.f_globals is self.owner.__dict__:
                        traceback.tb_next = None  # Strip host-only Python SDK double.
                        break
                    traceback = traceback.tb_next
                raise
        return SimpleNamespace(tick=tick)

    def test_normal_forwarding_preserves_foreground_and_return_value(self):
        flags = []
        monitor = SimpleNamespace(tick=lambda foreground=True: flags.append(foreground) or 'unchanged-result')
        self.assertEqual(self.tick(monitor, self.owner), 'unchanged-result')
        self.assertEqual(self.tick(monitor, self.owner, foreground=False), 'unchanged-result')
        self.assertEqual(flags, [True, False])
        self.assertEqual(self.messages, [])

    def test_recorded_exact_context_read_defers_and_loop_continues(self):
        xbmc, gui = self.sdk()
        monitor = self.native_throw_monitor(lambda foreground: self.owner._context(xbmc, gui, foreground))
        loop = ['original-player-poll']
        self.tick(monitor, self.owner)
        loop.append('remaining-original-loop')
        self.assertEqual(loop, ['original-player-poll', 'remaining-original-loop'])
        self.assertEqual(len(self.current_calls), 1)
        self.assertEqual(self.messages, ['Loading presentation deferred: observed window retired'])

    def test_other_message_and_same_code_other_read_rethrow(self):
        for options in (dict(message='Other RuntimeError'), dict(fail='home')):
            with self.subTest(options=options):
                xbmc, gui = self.sdk(**options)
                monitor = self.native_throw_monitor(lambda foreground: self.owner._context(xbmc, gui, foreground))
                with self.assertRaises(RuntimeError): self.tick(monitor, self.owner)
        self.assertEqual(self.messages, [])

    def test_same_message_wrong_code_and_later_original_tick_rethrow(self):
        def wrong_site(foreground=True): raise RuntimeError('Window id does not exist')
        with self.assertRaises(RuntimeError): self.tick(SimpleNamespace(tick=wrong_site), self.owner)
        xbmc, gui = self.sdk(fail=None, fail_write=True)
        original_monitor = self.owner.make_monitor(xbmc, gui)
        monitor = self.native_throw_monitor(lambda foreground: original_monitor.tick(foreground=foreground))
        with self.assertRaises(RuntimeError): self.tick(monitor, self.owner)
        self.assertEqual(self.messages, [])

    def test_untrusted_loader_or_changed_authenticated_pin_rethrow(self):
        xbmc, gui = self.sdk()
        monitor = self.native_throw_monitor(lambda foreground: self.owner._context(xbmc, gui, foreground))
        original_loader = self.owner.__loader__
        self.owner.__loader__ = object()
        with self.assertRaises(RuntimeError): self.tick(monitor, self.owner)
        self.owner.__loader__ = original_loader
        self.contract.files[RELATIVE] = 'changed-source-pin'
        with self.assertRaises(RuntimeError): self.tick(monitor, self.owner)
        self.assertEqual(self.messages, [])

    def test_retired_authenticated_generation_is_not_deferred(self):
        xbmc, gui = self.sdk()
        monitor = self.native_throw_monitor(lambda foreground: self.owner._context(xbmc, gui, foreground))
        self.fail_current = True
        with self.assertRaisesRegex(RuntimeError, 'Authenticated generation retired'): self.tick(monitor, self.owner)
        self.assertEqual(self.messages, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
