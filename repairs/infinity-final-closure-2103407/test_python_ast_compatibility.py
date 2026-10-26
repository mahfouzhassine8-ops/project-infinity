"""Python3.11 device/CI and3.12 host signatures agree without generic-syntax admission."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import unittest
import review_exact_sources
import structural_search

ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('ast_capabilities',ROOT/'isolated-python/provider_capabilities.py')
cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)


class PythonAstCompatibilityTests(unittest.TestCase):
    def test_golden_python311_executable_shape_matches_all_three_reviewers(self):
        raw=b'def dispatch(query):\n    """Documentation."""\n    return query\n'
        expected="Module(body=[FunctionDef(name='dispatch', args=arguments(posonlyargs=[], args=[arg(arg='query')], kwonlyargs=[], kw_defaults=[], defaults=[]), body=[Return(value=Name(id='query', ctx=Load()))], decorator_list=[])], type_ignores=[])"
        digest=hashlib.sha256(expected.encode()).hexdigest()
        self.assertEqual(review_exact_sources.fingerprint(raw,''),digest)
        self.assertEqual(cap._digest(ast.parse(raw)),digest)
        self.assertEqual(structural_search.reviewed_shape(ast.parse(raw)),digest)
        self.assertNotEqual(review_exact_sources.fingerprint(raw,'',python312=True),digest)

    def test_nonempty_python312_type_parameters_do_not_gain_a_reviewed_shape(self):
        node=ast.parse('def dispatch(query):\n    return query\n')
        function=node.body[0];function.type_params=[ast.Name(id='UnreviewedGeneric',ctx=ast.Load())]
        function._fields=tuple(k for k in function._fields if k!='type_params')+('type_params',)
        with self.assertRaises(ValueError):cap._digest(node)
        with self.assertRaises(structural_search.Unverified):structural_search.reviewed_shape(node)


if __name__=='__main__':unittest.main(verbosity=2)
