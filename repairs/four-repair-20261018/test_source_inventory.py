"""The build inventory must never waive changed/deleted protected inputs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ui_inventory_test', HERE / 'native_ci.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

class SourceInventoryTests(unittest.TestCase):
    def test_generated_files_are_enumerated_without_changing_source_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            driver.OUT = Path(temp)
            expected = {'xbmc/core.cpp': 'original', 'CMakeLists.txt': 'reviewed'}
            actual = dict(expected, **{'tools/depends/Makefile': 'generated'})
            driver.verify_post_build(actual, expected)
            result = json.loads((driver.OUT / 'POST-BUILD-SOURCE-INVENTORY.json').read_text())
            self.assertEqual(result['actual'], actual)
            self.assertEqual(result['changed_or_missing_reviewed'], [])
            self.assertEqual(result['build_generated_additions'], {'tools/depends/Makefile': 'generated'})
            for invalid in (dict(actual, **{'xbmc/core.cpp': 'wrong'}),
                            {k:v for k,v in actual.items() if k != 'CMakeLists.txt'}):
                with self.assertRaises(AssertionError):
                    driver.verify_post_build(invalid, expected)

if __name__ == '__main__': unittest.main(verbosity=2)
