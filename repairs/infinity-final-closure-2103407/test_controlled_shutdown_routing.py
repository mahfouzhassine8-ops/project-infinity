"""Only controlled-case wiring and actual refusal predicate coverage; not device proof."""
import ast
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import android17_shutdown_probe as probe
import unsafe_control as control


class ControlledShutdownRoutingTests(unittest.TestCase):
    def test_positive_three_cycles_and_all_proof_checks_are_preserved(self):
        source=Path(probe.__file__).read_text()
        self.assertIn("controlled=EXPECTED['scenario']=='integrated-native-image-and-unsafe'",source)
        self.assertIn('cycles=range(1) if controlled else range(3)',source)
        for required in ('verify_receipt(receipt,owner)','time.monotonic()+35','verify_records(before,after)',
                         "require(not entry['after_processes']",'PRAGMA integrity_check',
                         'native_image_control.run(transport,owner,args.out)',
                         'unsafe_control.run(transport,owner,args.out)'):
            self.assertIn(required,source)
        self.assertLess(source.index('native_image_control.run'),source.index('for cycle in cycles:'))
        self.assertGreater(source.index('unsafe_control.run'),source.index('entry.update(passed=True,reopened_owner'))

    def test_controlled_close_requires_real_marker_child_and_exact_negative_receipt(self):
        source=Path(control.__file__).read_text();tree=ast.parse(source)
        run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        body=ast.get_source_segment(source,run)
        for required in ("marker==CONTENTS","ready.get('child_scope_readonly') is False", "'/proc/'+str(ready['child_pid'])",
                         'verify_refusal(receipt,owner', 'time.monotonic()+35',"before.get(bucket)==after.get(bucket)"):
            self.assertIn(required,body)
        for forbidden in ('killProcess','force-stop','uninstall','pm clear','os.kill','communicate('):self.assertNotIn(forbidden,body)


if __name__=='__main__':unittest.main(verbosity=2)
