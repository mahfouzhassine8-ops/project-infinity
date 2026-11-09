"""Only the corrected publisher-version/local-transport-name boundary."""
import ast
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent


class TransportName(unittest.TestCase):
    def test_existing_publisher_versions_and_hashes_survive_safe_local_names(self):
        tree = ast.parse((HERE / 'verify_tracking_install_inputs.py').read_text())
        prepare = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'prepare')
        names = [node for node in ast.walk(prepare) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'name' for target in node.targets)]
        append = [node for node in ast.walk(prepare) if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and
                  isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name) and
                  node.value.func.value.id == 'dependencies' and node.value.func.attr == 'append']
        self.assertEqual(len(names), 1); self.assertEqual(len(append), 1)
        code = compile(ast.Module(body=[names[0], append[0]], type_ignores=[]), 'selected_transport_assignment', 'exec', optimize=1)
        pins = json.loads((HERE / 'TRACKING-DEPENDENCY-PINS.json').read_text())
        by_id = {row['addon']: row for row in pins['archives']}
        generated = []
        for index, aid in enumerate(pins['installation_order']):
            row = by_id[aid]; original = dict(row)
            ns = dict(index=index, aid=aid, row=row, dependencies=[])
            exec(code, ns)
            result = ns['dependencies'][0]
            self.assertRegex(result['archive'], r'^[A-Za-z0-9._-]+\.zip$')
            self.assertEqual(result['version'], original['version'])
            self.assertEqual(result['sha256'], original['sha256'])
            self.assertEqual(row, original)
            generated.append(result)
        six = next(row for row in generated if row['addon'] == 'script.module.six')
        self.assertEqual(six['version'], '1.16.0+matrix.1')
        self.assertEqual(six['archive'], '05-script.module.six-1.16.0-matrix.1.zip')
        self.assertEqual(len(generated), 8)
        self.assertEqual(len({row['archive'] for row in generated}), 8)


if __name__ == '__main__': unittest.main(verbosity=2)
