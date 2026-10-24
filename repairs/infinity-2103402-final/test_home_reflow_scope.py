"""Scope/behavior checks against exact signed CC35. Requires baseline ZIP environment."""
import ast
import hashlib
import os
import unittest
from pathlib import Path
from zipfile import ZipFile
from home_reflow_scope import BEFORE, AFTER, PREIMAGE_SHA256, transform

BASE = os.environ.get("INFINITY_SIGNED_CC35_ZIP", "")
MEMBER = 'script.infinity.commandcenter/service.py'

def baseline():
    if not BASE:
        raise RuntimeError("INFINITY_SIGNED_CC35_ZIP must be exact signed baseline")
    with ZipFile(BASE) as z:
        return z.read(MEMBER)

def controller_source(data):
    tree = ast.parse(data)
    node = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'DisplayReflowController')
    return compile(ast.Module(body=[node], type_ignores=[]), '<DisplayReflowController>', 'exec')

class HomeReflowTests(unittest.TestCase):
    def test_exact_scope_and_overlay(self):
        raw = baseline()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PREIMAGE_SHA256)
        self.assertEqual(raw.count(BEFORE), 1)
        revised = transform(raw)
        self.assertEqual(revised.count(AFTER), 1)
        self.assertEqual(revised.replace(AFTER, BEFORE, 1), raw)
        self.assertEqual((Path(__file__).parent / "overlay/script.infinity.commandcenter/service.py").read_bytes(), revised)

    def test_reject_modified_preimage(self):
        with self.assertRaises(ValueError):
            transform(baseline().replace(b'Infinity', b'Changed!', 1))

    def test_native_owner_keeps_widget_revision(self):
        revised = transform(baseline())
        state = {'signature':('ready','2','fold','full','portrait','540','1200','false','false','540','1200','portrait'),
                 'prop':{'Infinity.NativeReflowOwner':'app-v1'}, 'sets':{}, 'bumped':0}
        def prop(key, default=''):
            return state['prop'].get(key, default)
        def set_(key, value):
            state['sets'][key] = str(value)
        def bump():
            state['bumped'] += 1
        class FakeXbmc:
            def getSkinDir(self):
                return 'skin.infinity.diggz'
            def executebuiltin(self, cmd):
                raise AssertionError('No native-owned ReloadSkin')
        scope = {'_prop':prop, '_set':set_, '_display_signature':lambda:state['signature'],
                 '_display_signature_valid':lambda sig:bool(sig),
                 '_widget_signature':lambda sig:tuple(sig[i] for i in (2,3,4,5,6,7,8,9,10)),
                 '_bump_widget_revision':bump, 'xbmc':FakeXbmc(),
                 'DISPLAY_REFLOW_DEBOUNCE_SEC':0.55, 'DISPLAY_REFLOW_COOLDOWN_SEC':1.50}
        exec(controller_source(revised), scope)
        controller = scope['DisplayReflowController']()
        controller._publish_signature = lambda *args:None
        controller.tick(10.0)
        first = controller.widget_signature
        state['signature'] = ('ready','3','fold','full','landscape','1200','540','false','false','1200','540','landscape')
        controller.tick(11.0)
        self.assertNotEqual(first, controller.widget_signature)
        self.assertEqual(state['bumped'], 0)
        self.assertEqual(state['sets']['Infinity.ResponsiveReflow.State'], 'native-owned')
        self.assertEqual(state['sets']['Infinity.ResponsiveReflow.Enabled'], 'false')

    def test_legacy_fallback_unchanged(self):
        before = ast.parse(baseline())
        after = ast.parse(transform(baseline()))
        def apply(source):
            cl = next(x for x in source.body if isinstance(x, ast.ClassDef) and x.name == 'DisplayReflowController')
            return ast.dump(next(x for x in cl.body if isinstance(x, ast.FunctionDef) and x.name == '_apply'))
        self.assertEqual(apply(before), apply(after))
        self.assertIn("xbmc.executebuiltin('ReloadSkin()')", transform(baseline()).decode())

if __name__ == '__main__':
    unittest.main()
