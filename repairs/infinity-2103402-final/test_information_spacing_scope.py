"""Information textbox sizing without modifying text, actions or scroll interface."""
import ast
import os
import unittest
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
from information_spacing_scope import transform,PREIMAGE_SHA256

BASE=os.environ.get('INFINITY_SIGNED_CC35_ZIP','')
MEMBER='script.infinity.commandcenter/information.py'

def baseline():
    if not BASE:raise RuntimeError('Exact signed CC ZIP required')
    with ZipFile(BASE) as z:return z.read(MEMBER)

def functions(code):
    tree=ast.parse(code)
    defs=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('geometry','_estimated_synopsis_height')]
    scope={}
    exec(compile(ast.Module(body=defs,type_ignores=[]),'<optionb>', 'exec'),scope)
    return scope

class InformationSpacingTest(unittest.TestCase):
    def test_scope_and_overlay(self):
        old=baseline()
        self.assertEqual(sha256(old).hexdigest(),PREIMAGE_SHA256)
        new=transform(old)
        self.assertEqual((Path(__file__).parent/'overlay/script.infinity.commandcenter/information.py').read_bytes(),new)
        self.assertIn(b"self.getControl(126).setText(view['synopsis'] if view['synopsis'] else 'No synopsis is available for this title.')",new)

    def test_short_plot_reduces_reserved_space_long_plot_still_scrolls(self):
        original=functions(baseline())['geometry']
        after=functions(transform(baseline()))['geometry']
        short="With a bounty on his head, Vision must confront his nature and resist Ultron's influence to survive."
        old=original(1080,2400,1080,2400,details=True)
        new=after(1080,2400,1080,2400,details=True,synopsis=short)
        self.assertLess(new['height'],old['height']-250)
        self.assertEqual(old['controls'][101][2],new['controls'][101][2])
        self.assertEqual(old['controls'][102][2],new['controls'][102][2])
        self.assertGreater(new['controls'][126][3],0)
        self.assertGreater(new['bars'][127][3],0)
        long=after(1080,2400,1080,2400,details=True,synopsis='A long sentence about a story. '*400)
        self.assertEqual(long['height'],old['height'])
        self.assertEqual(long['controls'][126][3],old['controls'][126][3])

    def test_small_window_bounded_and_no_exception(self):
        geo=functions(transform(baseline()))['geometry']
        for w,h in [(720,1280),(1080,1100),(1280,720),(540,1200)]:
            for text in ['', 'short', 'Many characters '*200]:
                d=geo(w,h,w,h,details=True,synopsis=text)
                self.assertGreater(d['height'],0)
                self.assertLessEqual(d['height'],h)
                self.assertGreater(d['controls'][126][3],0)

    def test_mutated_baseline_rejected(self):
        with self.assertRaises(ValueError):transform(baseline()+b'#changed')

if __name__=='__main__':
    unittest.main()
