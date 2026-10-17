"""Fail-closed native Infinity Essential-First receipt checks, not Kodi defaults."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import infinity_full_stack_close as app


class NativeInfinityCloseProof(unittest.TestCase):
    def setUp(self):
        self.owner = {"owner": "owner-1", "pid": 4242, "phase": "RUNNING"}
        self.receipt = {
            "phase": "COMPLETE", "owner": "owner-1", "pid": 4242,
            "checkpoint_saved": True, "authorization_consumed": True,
            "process_death_confirmed": True,
            "exit_policy": "essential_first_process_exit_v1",
            "native_receipt": {
                "owners": list(range(17)), "essential_owners": list(range(16)),
                "essential_writes_sealed": True, "essential_writes_durable": True,
                "essential_write_blockers": [],
            }
        }

    def test_actual_infinity_essential_first_receipt_accepts_only_correct_owner(self):
        verdict = app.validate_receipt(self.receipt, self.owner)
        self.assertTrue(verdict["essential_writes_durable"])
        self.assertFalse(verdict["whole_package_death_verified"])
        self.assertFalse(verdict["reopened_skin_preserved"])

    def test_stock_kodi_or_unknown_shutdown_policy_cannot_pass(self):
        self.receipt["exit_policy"] = "standard_kodi_quit"
        with self.assertRaisesRegex(RuntimeError, "Infinity Essential-First"):
            app.validate_receipt(self.receipt, self.owner)

    def test_unrelated_native_owner_cannot_pass(self):
        self.owner["owner"] = "owner-2"
        with self.assertRaisesRegex(RuntimeError, "different native Infinity"):
            app.validate_receipt(self.receipt, self.owner)

    def test_failed_checkpoint_keeps_failure(self):
        self.receipt.update(phase="CHECKPOINT_FAILED",
                            error="native_admission: checkpoint_deadline_exceeded; owner proof incomplete")
        with self.assertRaisesRegex(RuntimeError, "checkpoint_deadline_exceeded"):
            app.validate_receipt(self.receipt, self.owner)

    def test_missing_proof_does_not_turn_green(self):
        for field in ("checkpoint_saved", "authorization_consumed", "process_death_confirmed"):
            with self.subTest(field=field):
                self.receipt[field] = False
                with self.assertRaisesRegex(RuntimeError, "missing essential shutdown proof"):
                    app.validate_receipt(self.receipt, self.owner)
                self.receipt[field] = True

    def test_essential_owners_must_be_complete(self):
        self.receipt["native_receipt"]["essential_owners"].pop()
        with self.assertRaisesRegex(RuntimeError, "owner proof incomplete"):
            app.validate_receipt(self.receipt, self.owner)

    def test_blocked_essential_write_must_fail(self):
        self.receipt["native_receipt"]["essential_write_blockers"] = ["sqlite-pending"]
        with self.assertRaisesRegex(RuntimeError, "essential write blockers"):
            app.validate_receipt(self.receipt, self.owner)


if __name__ == "__main__":
    unittest.main(verbosity=2)
