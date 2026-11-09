"""Only the new exact manual-route normalization refusal control."""
import ast
import hashlib
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKFLOW = '.github/workflows/infinity-saved-navigation-android.yml'


class RouteShape(unittest.TestCase):
    def test_only_exact_reviewed_manual_addition_normalizes(self):
        tree = ast.parse((HERE / 'admit_tracking_android.py').read_text())
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('require', 'workflow_shape')]
        self.assertEqual({node.name for node in nodes}, {'require', 'workflow_shape'})
        current = (ROOT / WORKFLOW).read_text()
        observed = [current]
        class ReadOnlyRoot:
            def __truediv__(self, path):
                if path != WORKFLOW: raise RuntimeError('Unselected source read')
                return SimpleNamespace(read_text=lambda: observed[0])
        ns = dict(ROOT=ReadOnlyRoot(), WORKFLOW=WORKFLOW, hashlib=hashlib, re=re,
            WORKFLOW_SHAPE_BASE='9d64ffb84404036ce6e02d6cb160fb004a029b33',
            git=lambda *args: subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=30))
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'admit_tracking_android.py', 'exec', optimize=1), ns)
        check = ns['workflow_shape']; check()
        historical = subprocess.check_output(['git', '-C', str(ROOT), 'show', '0245abf5e4a10d490bd38677b118e873c01e5504:' + WORKFLOW], text=True)
        marker = '  tracking_signed_install_android:\n'
        prefix, job = current.split(marker)
        normalized = prefix.replace(', tracking-signed-install-android]', ']', 1).replace(" && inputs.feature != 'tracking-signed-install-android'", '', 1)
        self.assertEqual(normalized, historical)
        observed[0] = historical; check()
        variants = [
            prefix + marker + job.replace("github.event_name == 'workflow_dispatch'", "github.event_name == 'push'", 1),
            current.replace(" && inputs.feature != 'tracking-signed-install-android'", '', 1),
            current.replace(', tracking-signed-install-android]', ']', 1),
            current.replace('name: Unchanged signed69 stock API36 startup qualification only', 'name: Altered preexisting job', 1),
        ]
        for changed in variants:
            observed[0] = changed
            with self.assertRaises(RuntimeError): check()


if __name__ == '__main__': unittest.main(verbosity=2)
