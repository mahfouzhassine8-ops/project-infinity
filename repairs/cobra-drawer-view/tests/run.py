#!/usr/bin/env python3
"""Fail-closed source tests plus executable Java callback tests using UI doubles."""
from pathlib import Path
import argparse
import importlib.util
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('drawer_patch', ROOT / 'apply.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASELINE = b''


def member(source: str, name: str) -> str:
    # These selected members contain no braces inside comments or string literals.
    found = re.search(r'^  private [^\n;=]*?\b' + name + r'\s*\(', source, re.M)
    if not found:
        raise ValueError('Missing production member: ' + name)
    begin = source.index('{', found.start())
    depth = 1
    for end in range(begin + 1, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if depth == 0:
            return source[found.start():end + 1]
    raise ValueError('Unclosed member: ' + name)


class DrawerTests(unittest.TestCase):
    def test_single_replacement_and_all_other_bytes_preserved(self):
        after = module.patch(BASELINE)
        old, new = module.OLD.encode(), module.NEW.encode()
        index = BASELINE.index(old)
        self.assertEqual(after[:index], BASELINE[:index])
        self.assertEqual(after[index+len(new):], BASELINE[index+len(old):])
        self.assertEqual(after.count(b'"cobra_drawer_view"'), 1)
        drawer = member(after.decode(), 'toggleCobraDrawer')
        self.assertNotIn('VIEW MODES', drawer)
        self.assertNotIn('CobraModeLayout.MODES', drawer)
        self.assertIn('"View"', drawer)
        self.assertNotIn('cobraSwitchMode(', drawer)

    def test_existing_chooser_switch_and_sheet_helpers_are_identical(self):
        after = module.patch(BASELINE).decode()
        for name in ('showCobraViewModeMenu','cobraSwitchMode','cobraSheetRow',
                     'cobraOpenSheet','closeCobraActionSheet','closeCobraExperienceDrawer'):
            self.assertEqual(member(BASELINE.decode(), name), member(after, name))

    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):
            module.patch(BASELINE + b'\n')

    def test_reapplication_rejected(self):
        with self.assertRaises(ValueError):
            module.patch(module.patch(BASELINE))

    def test_preparation_preserves_input_and_exact_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source.java.in'; source.write_bytes(BASELINE)
            output = root / 'candidate' / 'InfinityLiveActivity.java.in'
            report = module.prepare(source, output, root / 'rollback')
            self.assertEqual(source.read_bytes(), BASELINE)
            self.assertEqual((root/'rollback/InfinityLiveActivity-2103157.java.in').read_bytes(),BASELINE)
            self.assertEqual(output.read_bytes(), module.patch(BASELINE))
            self.assertFalse(report['apk_built'])
            self.assertFalse(report['device_verified'])
            self.assertFalse(report['official'])

    def test_refuses_input_overwrite_and_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; source.write_bytes(BASELINE)
            with self.assertRaises(ValueError): module.prepare(source,source,root/'rollback')
            output=root/'existing'; output.write_text('leave this alone')
            with self.assertRaises(ValueError): module.prepare(source,output,root/'rollback')
            self.assertEqual(output.read_text(),'leave this alone')
            self.assertFalse((root/'rollback').exists())

    def test_invalid_preimage_creates_no_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; source.write_bytes(BASELINE+b'x')
            with self.assertRaises(ValueError): module.prepare(source,root/'output',root/'rollback')
            self.assertFalse((root/'rollback').exists())
            self.assertFalse((root/'output').exists())

    def test_real_row_and_chooser_callbacks_on_host(self):
        after = module.patch(BASELINE).decode()
        drawer = member(after, 'toggleCobraDrawer')
        begin = drawer.index('    // Drawer navigation stays compact;')
        end = drawer.index('    cobraDrawerDestination(items,"more","Settings"', begin)
        java=(ROOT/'tests/host.java.in').read_text().replace('@@DRAWER@@',drawer[begin:end])
        for token,name in (('ROW','cobraSheetRow'),('CHOOSER','showCobraViewModeMenu'),
                           ('SWITCH','cobraSwitchMode'),('NAME','cobraModeName')):
            java=java.replace('@@'+token+'@@',member(after,name))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'DrawerViewHost.java').write_text(java)
            subprocess.run(['javac','-encoding','UTF-8','-d',str(root),str(root/'DrawerViewHost.java')],check=True)
            subprocess.run(['java','-cp',str(root),'DrawerViewHost'],check=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    args=parser.parse_args(); BASELINE=args.baseline.read_bytes()
    unittest.main(argv=['drawer-view-tests'],verbosity=2)
