"""Correction-specific actual DEX source boundaries, not an Android acceptance result."""
import os
from pathlib import Path
import unittest
import coordinator_dex as correction
from module_dex import methods


class CoordinatorDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(os.environ['INFINITY_COORDINATOR_SMALI']).read_text()

    def test_actual_success_dispatch_moves_to_worker_and_failure_ui_stays_exact(self):
        before=methods(self.source);changed=correction.patch(self.source);after=methods(changed)
        self.assertEqual(before.keys(),after.keys())
        old_success,old_failure=before[correction.METHOD].split('    :catch_0\n',1)
        success,failure=after[correction.METHOD].split('    :catch_0\n',1)
        self.assertEqual(failure,old_failure)
        self.assertEqual(success.replace(correction.WORKER,correction.FIELD).replace(correction.EXECUTE,correction.POST),old_success)
        self.assertIn('InfinityCheckpointReceipt;->atomic',success)
        self.assertIn('ExternalSyntheticLambda38;',success)
        for name in before:
            if name!=correction.METHOD:self.assertEqual(before[name],after[name])
        self.assertEqual(changed.replace(after[correction.METHOD],before[correction.METHOD]),self.source)

    def test_unknown_modified_and_double_patched_sources_are_refused(self):
        for text in (self.source+'\n',self.source.replace('completion_receipt_failed','unknown_receipt_failed'),correction.patch(self.source)):
            with self.subTest(digest=correction.sha(text.encode())):
                with self.assertRaises(ValueError):correction.patch(text)

    def test_gui_guard_final_receipt_authority_and_lifecycle_are_retained(self):
        folder=Path(os.environ['INFINITY_COORDINATOR_SMALI']).parent
        receipt=(folder/'InfinityCheckpointReceipt.smali').read_text()
        self.assertIn('const-string v4, "write on GUI thread"',receipt)
        self.assertIn('Landroid/os/Looper;->myLooper()',receipt)
        changed=correction.patch(self.source)
        before=methods(self.source);after=methods(changed)
        protected=[n for n in before if any(s in n for s in ('finishCoordinatorProcess','lambda$checkOwner$16','retireConfirmedClosedKodiTask','end()','deadline()'))]
        self.assertGreaterEqual(len(protected),6)
        for name in protected:self.assertEqual(before[name],after[name])
        self.assertIn('coordinator_termination_authorized',changed)
        self.assertIn('InfinityJavaWriteBarrier;->whileAuthorized',changed)


if __name__=='__main__':unittest.main(verbosity=2)
