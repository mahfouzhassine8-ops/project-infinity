#!/usr/bin/env python3
"""Reject stale native identities while checking the current reviewed tag."""
from pathlib import Path
import tempfile
import unittest
from native_ci import verify_engine_identity


class EngineIdentityTest(unittest.TestCase):
    def test_current_tag_and_feature_checks(self):
        with tempfile.TemporaryDirectory() as work:
            source = Path(work)
            header = source / 'xbmc/platform/android/activity/InfinityShutdownTrace.h'
            header.parent.mkdir(parents=True)
            tag = 'infinity-checkpoint-python-retirement-batch-2103352-v1'
            header.write_text('constexpr const char* ENGINE_TAG = "' + tag + '";\n')
            features = [b'SAFE_TO_TERMINATE', b'infinityRequestPersistenceCheckpoint',
                        b'infinityAuthorizeCheckpointTermination', b'CHECKPOINT_FAILED',
                        tag.encode(), b'scripts.target_before_join',
                        b'scripts.target_before_nonblocking_stop', b'os_tid.%u.stage.%s',
                        b'interpreter_retirement_receipt_limit', b'nonpersistent:ambient-glass', b'PIL._imaging',
                        b'python_bytecode_cache_boundary_rename', b'direct_sqlite_connect_observed',
                        b'full_blocker_inventory_v1', b'python_retirement_batch_v1']
            self.assertEqual(verify_engine_identity(source, b'\0'.join(features)), tag)
            stale = b'\0'.join(features).replace(tag.encode(), b'infinity-shutdown-2103334-v1')
            with self.assertRaises(ValueError):
                verify_engine_identity(source, stale)
            for missing in features:
                with self.assertRaises(ValueError):
                    verify_engine_identity(source, b'\0'.join(x for x in features if x != missing))
            header.write_text(header.read_text() * 2)
            with self.assertRaises(ValueError):
                verify_engine_identity(source, b'\0'.join(features))


if __name__ == '__main__':
    unittest.main()
