"""Focused defensive model checks. Synthetic witnesses are not native proof."""
import copy
import hashlib
from pathlib import Path
import unittest

from settings_proof_contract import decision, safety_matrix

BEFORE=("dev", "inode", 108, 100, 100)
AFTER=("dev", "inode", 144, 200, 200)
REQ=hashlib.sha256(b"synthetic-nonprivate-request-token").hexdigest()


def modeled_native_witness():
    return dict(schema=1, request_digest=REQ,
                start_stamp=BEFORE, end_stamp=AFTER,
                native_owner_verified=True, complete_coverage=True,
                all_direct_file_writers_observed=True,
                observer_continuous=True,native_request_completed=True,
                source_pins_rechecked=True,event_gap=False,overflow=False,
                foreign_or_unattributed_write=False, shutdown_transition=False,
                first_revision=100,last_revision=102,events=[
                    dict(revision=101,source="native_kodi_settings",
                         semantic_impact="bookkeeping_only",
                         verified_durable_write=True),
                    dict(revision=102,source="native_kodi_settings",
                         semantic_impact="bookkeeping_only",
                         verified_durable_write=True),
                ])


class NativeProofContract(unittest.TestCase):
    def test_stable_settings_need_no_new_provenance(self):
        self.assertEqual(decision(BEFORE,BEFORE),(True,"unchanged_settings"))

    def test_missing_or_unreadable_file_never_accepted(self):
        self.assertFalse(decision(None,AFTER)[0])
        self.assertFalse(decision(BEFORE,None)[0])

    def test_unverified_real_world_write_fails_closed(self):
        self.assertEqual(decision(BEFORE,AFTER,expected_request=REQ),
                         (False,"no_native_witness"))

    def test_benign_proof_only_conditional_example_accepts(self):
        # A manufactured witness is NOT proof on the real Fold.
        self.assertEqual(decision(BEFORE,AFTER,native_witness=modeled_native_witness(),
                                  expected_request=REQ),(True,"proven_bookkeeping_only"))

    def test_meaningful_mid_request_change_rejects(self):
        w=modeled_native_witness()
        w["events"][0]["semantic_impact"]="config_change"
        self.assertEqual(decision(BEFORE,AFTER,native_witness=w,expected_request=REQ)[0],False)

    def test_intermediate_a_b_a_rejects_even_with_benign_last_event(self):
        w=modeled_native_witness()
        w["events"][0]["semantic_impact"]="config_change"
        w["events"][1]["semantic_impact"]="bookkeeping_only"
        self.assertEqual(decision(BEFORE,AFTER,native_witness=w,expected_request=REQ)[0],False)

    def test_unknown_semantics_reject(self):
        w=modeled_native_witness()
        w["events"][0]["semantic_impact"]="unknown"
        self.assertFalse(decision(BEFORE,AFTER,native_witness=w,expected_request=REQ)[0])

    def test_foreign_direct_file_writer_is_not_ignored(self):
        w=modeled_native_witness()
        w["foreign_or_unattributed_write"]=True
        self.assertEqual(decision(BEFORE,AFTER,native_witness=w,expected_request=REQ)[1],
                         "unattributed_writer")

    def test_direct_file_write_without_proof_refused(self):
        w=modeled_native_witness()
        w["events"][0]["source"]="unverified_direct_file_writer"
        self.assertEqual(decision(BEFORE,AFTER,native_witness=w,expected_request=REQ)[1],
                         "unverified_writer")

    def test_declared_gap_or_overflow_rejected(self):
        for field,value in (("event_gap",True),("overflow",True),
                            ("observer_continuous",False),
                            ("all_direct_file_writers_observed",False)):
            with self.subTest(field=field):
                w=modeled_native_witness();w[field]=value
                self.assertFalse(decision(BEFORE,AFTER,native_witness=w,
                                          expected_request=REQ)[0])

    def test_wrong_request_and_file_stamp_rejected(self):
        for update in ({"request_digest": "0"*64},
                       {"start_stamp":("unexpected",)},
                       {"end_stamp":("unexpected",)}):
            with self.subTest(update=update):
                w=modeled_native_witness();w.update(update)
                self.assertFalse(decision(BEFORE,AFTER,native_witness=w,
                                          expected_request=REQ)[0])

    def test_missing_or_reordered_generations_rejected(self):
        for update in ({"events": []},{"last_revision": 104},
                       {"events":[modeled_native_witness()["events"][1]]},
                       {"first_revision": 0}):
            with self.subTest(update=str(update)[:50]):
                w=modeled_native_witness();w.update(update)
                self.assertFalse(decision(BEFORE,AFTER,native_witness=w,
                                          expected_request=REQ)[0])

    def test_native_or_durable_evidence_requirement_cannot_be_defaulted(self):
        for key in ("native_owner_verified", "complete_coverage",
                    "native_request_completed", "source_pins_rechecked"):
            with self.subTest(key=key):
                w=modeled_native_witness();w[key]=False
                self.assertFalse(decision(BEFORE,AFTER,native_witness=w,
                                          expected_request=REQ)[0])
        w=modeled_native_witness()
        w["events"][0]["verified_durable_write"]=False
        self.assertFalse(decision(BEFORE,AFTER,native_witness=w,expected_request=REQ)[0])

    def test_shutdown_transition_refused(self):
        w=modeled_native_witness();w["shutdown_transition"]=True
        self.assertEqual(decision(BEFORE,AFTER,native_witness=w,expected_request=REQ)[1],
                         "shutdown_transition")

    def test_model_is_not_production_fix(self):
        x=safety_matrix()
        self.assertTrue(x["no_shipped_search_change"])
        self.assertFalse(x["real_native_evidence_producer"])
        self.assertFalse(x["all_direct_file_writers_observed_on_android"])

if __name__=="__main__":
    unittest.main(verbosity=2)
