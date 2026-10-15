"""Exact conditional reference parser: missing, stale and mismatched mirrors."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('health_reference', ROOT / 'system-stability-2103366/health/overlay/khc_lifecycle.py')
health = importlib.util.module_from_spec(spec); spec.loader.exec_module(health)
RECEIPT = json.loads((ROOT / 'system-stability-2103366/protected-close-fixture.json').read_text())


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.home = self.root / '.kodi'; self.home.mkdir()
    def write(self, row=RECEIPT, **changes):
        raw = json.dumps(row, separators=(',', ':')).encode()
        (self.root / 'infinity-checkpoint-close.json').write_bytes(raw)
        now = int(time.time() * 1000)
        metadata = dict(schema=1, read_only=True, source='private-coordinator-receipt',
                        receipt_sha256=hashlib.sha256(raw).hexdigest(), captured_epoch_ms=now,
                        source_modified_epoch_ms=now, collector_pid=123, publication='coordinator_write',
                        session=row.get('session', ''), receipt_pid=row.get('pid', 0), phase=row.get('phase', ''))
        metadata.update(changes)
        (self.root / 'infinity-checkpoint-mirror.json').write_text(json.dumps(metadata))
    def test_matched_bridge_keeps_current_health_unverified(self):
        self.write(); result = health.read_checkpoint(str(self.home))
        self.assertEqual(result['state'], 'RESOLVED'); self.assertEqual(result['evidence_scope'], 'previous_close')
        self.assertEqual(result['current_process_health'], 'UNVERIFIED')
        self.assertEqual(result['freshness'], 'CURRENT_PUBLICATION')
    def test_startup_and_aged_receipts_are_saved_evidence(self):
        for changes in (dict(publication='startup_snapshot'), dict(captured_epoch_ms=int(time.time()*1000)-172800000)):
            self.write(**changes); self.assertEqual(health.read_checkpoint(str(self.home))['freshness'], 'SAVED_RECEIPT')
    def test_old_success_cannot_hide_new_failed_attempt(self):
        self.write(); failed = copy.deepcopy(RECEIPT); failed['phase'] = 'CHECKPOINT_FAILED'; failed['error'] = 'required owner still dirty'
        (self.root / 'infinity-checkpoint-close.json').write_text(json.dumps(failed))
        self.assertEqual(health.read_checkpoint(str(self.home))['state'], 'UNVERIFIED')
        self.write(failed); result = health.read_checkpoint(str(self.home))
        self.assertEqual(result['state'], 'ACTIVE'); self.assertTrue(result['active'])
    def test_unavailable_corrupt_and_linked_provenance_fail_closed(self):
        self.assertEqual(health.read_checkpoint(str(self.home))['state'], 'UNAVAILABLE')
        for changes in (dict(receipt_sha256='0'*64), dict(session='other'), dict(schema=True),
                        dict(captured_epoch_ms=True), dict(captured_epoch_ms=int(time.time()*1000)+120000)):
            self.write(**changes); self.assertEqual(health.read_checkpoint(str(self.home))['state'], 'UNVERIFIED')
        self.write(); path = self.root / 'infinity-checkpoint-mirror.json'; path.unlink()
        elsewhere = self.root / 'other.json'; elsewhere.write_text('{}'); path.symlink_to(elsewhere)
        self.assertEqual(health.read_checkpoint(str(self.home))['state'], 'UNVERIFIED')


if __name__ == '__main__': unittest.main(verbosity=2)
