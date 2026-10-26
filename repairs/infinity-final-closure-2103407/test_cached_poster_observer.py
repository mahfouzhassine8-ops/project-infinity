import ast
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cached_poster_observer as poster


class CachedPosterTests(unittest.TestCase):
    def test_actual_png_decode_four_colours_and_geometry_reject_placeholder_or_wrong_order(self):
        value=poster.inspect(poster.png())
        self.assertTrue(value['actual_surface_bitmap_verified'])
        self.assertEqual([r['pixels'] for r in value['regions']],[15000]*4)
        for order in ((0,0,0,0),(3,2,1,0),(0,2,1,3)):
            self.assertIsNone(poster.inspect(poster.png(order=order)))
        for raw in (b'not a screenshot',poster.png(8,8)):
            with self.assertRaises(ValueError):poster.inspect(raw)

    def test_fresh_file_hash_readback_and_saved_art_source_are_real(self):
        with tempfile.TemporaryDirectory() as temp:
            files={};events=[]
            def shell(*args):
                events.append(args)
                if args[-1] in files:raise RuntimeError('Existing file')
            def adb(*args,binary=False):
                if args[0]=='push':files[str(args[2])]=Path(args[1]).read_bytes();return 'pushed'
                self.assertTrue(binary);return files[str(args[2])]
            device=SimpleNamespace(PROFILE='/fresh-profile',shell=shell,adb=adb)
            state=dict(items={'a':{'position':60,'source':'unchanged'}})
            proof=poster.stage(device,SimpleNamespace(out=Path(temp)),state)
            self.assertEqual(proof['sha256'],hashlib.sha256(files['/fresh-profile/'+poster.NAME]).hexdigest())
            self.assertEqual(state['items']['a']['poster'],poster.URI)
            self.assertEqual(state['items']['a']['source'],'unchanged')
            with self.assertRaises(RuntimeError):poster.stage(device,SimpleNamespace(out=Path(temp)),state)

    def test_capture_retains_original_deadline_and_observer_never_generates_runtime_art(self):
        with tempfile.TemporaryDirectory() as temp:
            calls=[];device=SimpleNamespace(adb=lambda *a,**k:calls.append(a))
            with patch.object(poster.time,'monotonic',return_value=30):
                with self.assertRaises(AssertionError):poster.observe(device,Path(temp),0,20)
            self.assertEqual(calls,[])
        tree=ast.parse(Path(poster.__file__).read_text())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='observe')
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='png' for n in ast.walk(node)))
        card=Path(poster.__file__).with_name('stress_resume_card.py').read_text()
        self.assertIn('began,began+20',card)


if __name__=='__main__':unittest.main(verbosity=2)
