from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import khc_causal as causal
import native94


class CausalReport(unittest.TestCase):
    def report(self, reason, detail='', blocking=True):
        return causal.build({'coordinator-receipt.json': dict(pid=42, session='real-session',
            phase='CHECKPOINT_FAILED', error='native_admission: unverified_protected_writer:plugin.video.thecrew:service.py:'+reason,
            updated_epoch_ms=1000, last_native_status={'script_persistence':{'blockers':[
                dict(reason=reason,detail=detail,blocking=blocking,writer='plugin.video.thecrew:service.py')]}})})

    def test_vfs_cause_is_visible_and_not_excused(self):
        report=self.report('vfs_write_exception','exception=OSError;errno=28;stack=service.py:16:save')
        row=next(x for x in report['timeline'] if x['operation']=='vfs_write_exception')
        self.assertEqual(row['role'],'failure')
        self.assertEqual(row['component'],'plugin.video.thecrew')
        self.assertIn('errno=28',row['error_context'])
        self.assertIn('service.py:16:save',row['error_context'])
        self.assertFalse(report['termination_authority'])

    def test_sqlite_advisory_is_not_promoted_to_cause(self):
        report=self.report('sqlite_write_failed','exception=OperationalError;sqlite_code=1;verb=ALTER',False)
        row=next(x for x in report['timeline'] if x['operation']=='sqlite_write_failed')
        self.assertEqual(row['role'],'advisory')
        self.assertIn('verb=ALTER',row['error_context'])

    def test_python_service_and_missing_stack_are_explicit(self):
        report=self.report('uncaught_script_failure_before_persistence_receipt','exception=RuntimeError;stack=<missing>')
        self.assertIn('exception=RuntimeError',causal.text(report))
        self.assertIn('stack=<missing>',causal.text(report))
        report=self.report('vfs_write_exception')
        self.assertIn('Original exception type',causal.text(report))

    def test_private_data_is_not_copied_into_tree(self):
        report=self.report('vfs_write_exception',
            'exception=OSError;errno=5;token=secret;path=/private/account/title;message=Personal Movie https://private/?token=secret')
        text=json.dumps(report)
        for word in ('Personal Movie','/private/account','secret','https://private'):
            self.assertNotIn(word,text)

    def test_input_limit_and_read_only_collection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'native.jsonl'
            raw=(json.dumps(dict(event='python.error',outcome='exception',pid=42))+'\n').encode()*20000
            p.write_bytes(raw);before=p.read_bytes()
            report=causal.collect([root])
            self.assertLessEqual(len(report['timeline']),causal.MAX_EVENTS)
            self.assertEqual(before,p.read_bytes())
            self.assertEqual([x.name for x in root.iterdir()],['native.jsonl'])

    def test_source_backed_exception_capture_preserves_original(self):
        # Exercise the patched production Observer.error method without
        # installing any process-wide I/O hooks in the host test interpreter.
        source=Path(os.environ['INFINITY_2103393_NATIVE'])/native94.OBSERVER
        import ast
        raw=native94.observer_detail(source.read_bytes()).decode()
        raw=raw.split('R\"infinity_source(',1)[1].rsplit(')infinity_source\";',1)[0]
        tree=ast.parse(raw)
        cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Observer')
        method=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='error')
        import sys
        ns={'sys':sys}
        exec(compile(ast.Module(body=[method],type_ignores=[]),'actual_observer.py','exec'),ns)
        rows=[]
        from types import SimpleNamespace
        observed=SimpleNamespace(closed_error=None,protect=None,fail=lambda *args:rows.append(args))
        original=OSError(28,'private title and token must not appear')
        try:
            raise original
        except OSError as caught:
            ns['error'](observed,'vfs_write_exception')
            self.assertIs(sys.exc_info()[1],original)
            self.assertIs(caught,original)
        self.assertEqual(rows[0][0],'vfs_write_exception')
        self.assertIn('exception=OSError;errno=28',rows[0][1])
        self.assertNotIn('private title',rows[0][1])


if __name__=='__main__':unittest.main()
