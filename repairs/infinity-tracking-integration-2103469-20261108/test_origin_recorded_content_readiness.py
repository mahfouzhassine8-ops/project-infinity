"""One selected pure readiness guard using immutable actual run42591104063.

No installed records, SDK doubles, app execution, provider calls or navigation
changes. The populated ambiguity is a counterfactual negative GUI state only.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
RECORDED = Path('/workspace/scratch/tracking-origin-42591104063/files/tracking-android-results')
PINS = {'observer-003-snapshot.json': '1cba1d0b9691072a54316857793480abe7862a67df5d13e6b1b8a033fe5846ae',
        'observer-014-snapshot.json': '7e3648e844f6c5fe2c50ae3c53aa954cc55cf0bc6cf1ebbad8e94116c4c8433e'}


def require(value, label):
    if not value: raise RuntimeError(label)


def recorded(name):
    raw = (RECORDED / name).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PINS[name], 'EXACT_IMMUTABLE_ACTUAL_SNAPSHOT_REQUIRED')
    value = json.loads(raw)
    require(value['passed'] is True, 'ACTUAL_SUCCESSFUL_OBSERVER_READ_REQUIRED')
    return value['result']


class ActualReadiness(unittest.TestCase):
    def test_actual_empty_transient_waits_settled_reads_and_populated_ambiguity_refuses(self):
        source = HERE / 'verify_tracking_android.py'
        nodes = [node for node in ast.parse(source.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'content_rows']
        self.assertEqual(len(nodes), 1)
        namespace = dict(base=SimpleNamespace(require=require))
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec', optimize=1), namespace)
        content_rows = namespace['content_rows']
        empty, settled = recorded('observer-003-snapshot.json'), recorded('observer-014-snapshot.json')
        self.assertEqual(empty['controls'], {})
        self.assertTrue(empty['visible_controls']['500'] and empty['visible_controls']['65051'])
        self.assertEqual(content_rows(empty, optional=True), [])
        with self.assertRaisesRegex(RuntimeError, 'AMBIGUOUS_VISIBLE_PRIMARY_CONTENT_CONTROLS_REJECTED'):
            content_rows(empty)
        rows = content_rows(settled, optional=True)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row['control'] == 65051 for row in rows))
        self.assertEqual(rows[2]['label'], "Queen's Blade")
        populated_ambiguity = copy.deepcopy(empty)
        populated_ambiguity['controls'] = copy.deepcopy(settled['controls'])
        with self.assertRaisesRegex(RuntimeError, 'AMBIGUOUS_VISIBLE_PRIMARY_CONTENT_CONTROLS_REJECTED'):
            content_rows(populated_ambiguity, optional=True)


if __name__ == '__main__':
    print('verify_tracking_android.py', hashlib.sha256((HERE / 'verify_tracking_android.py').read_bytes()).hexdigest(), flush=True)
    unittest.main(verbosity=2)
