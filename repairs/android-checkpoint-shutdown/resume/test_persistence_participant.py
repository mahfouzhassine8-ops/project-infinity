# SPDX-License-Identifier: GPL-2.0-or-later
import copy
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock

import persistence_participant as participant
from persistence_participant import (AdmissionClosed, EngineOwner, OperationResult,
                                     PersistenceError, PersistenceParticipant)


OWNER = EngineOwner(120, "engine-owner-token-123456")
SESSION = "checkpoint-session-123456"
OK = OperationResult(True)


def concurrent_writer(profile, count):
    store = PersistenceParticipant(profile, OWNER)
    for _ in range(count):
        def increment(data):
            time.sleep(0.001)  # Force overlapping readers if flock is narrowed.
            data["count"] = data.get("count", 0) + 1
            return data
        store.update("continue-watching.json", {}, increment)


class Hooks:
    def __init__(self, store):
        self.store = store
        self.events = []

    def capture_final_playback(self):
        self.events.append("capture")
        return OK, {"position": 417.125, "duration": 900.0, "key": "movie"}

    def persist_final_playback(self, snapshot, writer):
        self.events.append("persist")
        writer.update("continue-watching.json", {}, lambda data: dict(data, items={"movie": snapshot}))
        return OK

    def stop_playback(self):
        self.events.append("stop")
        saved = json.loads((self.store.profile / "continue-watching.json").read_text())
        if saved["items"]["movie"]["position"] != 417.125:
            return OperationResult(False, "player stopped before final position committed")
        return OK

    def drain_required_events(self, writer):
        self.events.append("drain")
        return OK

    def persist_session(self, writer):
        self.events.append("session")
        writer.update("session.json", {}, lambda data: dict(data, window=10000))
        writer.remove("boot-marker.json")
        return OK


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.profile = Path(self.temporary.name)
        self.store = PersistenceParticipant(self.profile, OWNER)
        self.store.bind_engine()

    def tearDown(self):
        self.temporary.cleanup()

    def state(self):
        return json.loads(self.store.state_path.read_text())

    def test_cross_interpreter_read_modify_write_loses_no_updates(self):
        context = multiprocessing.get_context("spawn")
        processes = [context.Process(target=concurrent_writer, args=(str(self.profile), 12)) for _ in range(3)]
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=15)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
                self.fail("writer deadlocked")
            self.assertEqual(process.exitcode, 0)
        self.assertEqual(json.loads((self.profile / "continue-watching.json").read_text())["count"], 36)
        self.assertEqual(self.state()["generation"], self.state()["committed_generation"])

    def test_checkpoint_commits_final_position_before_stopping_and_fences(self):
        self.store.update("boot-marker.json", {}, lambda data: {"stage": "ready"})
        hooks = Hooks(self.store)
        receipt = self.store.checkpoint(SESSION, hooks)
        self.assertEqual(hooks.events, ["capture", "persist", "stop", "drain", "session"])
        self.assertEqual(receipt["owner"], {"pid": OWNER.pid, "token": OWNER.token})
        self.assertEqual(receipt["session"], SESSION)
        self.assertFalse(receipt["global_safe_to_terminate"])
        self.assertFalse((self.profile / "boot-marker.json").exists())
        with self.assertRaises(AdmissionClosed):
            self.store.update("session.json", {}, lambda data: {})
        with self.assertRaises(AdmissionClosed):
            self.store.begin_checkpoint("another-checkpoint-123456")

    def test_required_ended_event_can_remove_resume_and_preserve_history(self):
        hooks = Hooks(self.store)
        def ended(writer):
            def transition(data):
                entry = data["items"].pop("movie")
                data["watched"] = {"movie": dict(entry, watched=True, play_count=1)}
                return data
            writer.update("continue-watching.json", {}, transition)
            return OK
        hooks.drain_required_events = ended
        self.store.checkpoint(SESSION, hooks)
        data = json.loads((self.profile / "continue-watching.json").read_text())
        self.assertEqual(data["items"], {})
        self.assertEqual(data["watched"]["movie"]["play_count"], 1)

    def test_failure_never_reopens_admission_or_returns_receipt(self):
        hooks = Hooks(self.store)
        hooks.drain_required_events = lambda writer: OperationResult(False, "Kodi playcount RPC failed")
        with self.assertRaisesRegex(PersistenceError, "drain_required_events"):
            self.store.checkpoint(SESSION, hooks)
        self.assertEqual(self.state()["phase"], "FAILED")
        self.store.bind_engine()  # Same-engine rebind must not defeat the fence.
        with self.assertRaises(AdmissionClosed):
            self.store.update("session.json", {}, lambda data: data)

    def test_unchecked_truthy_hook_is_not_success(self):
        hooks = Hooks(self.store)
        hooks.stop_playback = lambda: "success"
        with self.assertRaisesRegex(PersistenceError, "checked success"):
            self.store.checkpoint(SESSION, hooks)
        self.assertEqual(self.state()["phase"], "FAILED")

    def test_directory_fsync_failure_leaves_uncommitted_generation(self):
        real_sync = participant._sync_directory
        def fail_target_directory(path):
            if path == self.profile:
                raise OSError("injected directory sync failure")
            real_sync(path)
        with mock.patch.object(participant, "_sync_directory", side_effect=fail_target_directory):
            with self.assertRaises(OSError):
                self.store.update("continue-watching.json", {}, lambda data: {"items": {"movie": 42}})
        self.assertEqual(self.state()["pending"], "continue-watching.json")
        self.assertGreater(self.state()["generation"], self.state()["committed_generation"])
        with self.assertRaisesRegex(PersistenceError, "uncommitted generation"):
            self.store.begin_checkpoint(SESSION)

    def test_invalid_json_is_not_replaced_with_default(self):
        file = self.profile / "continue-watching.json"
        file.write_bytes(b'{"items": BROKEN')
        with self.assertRaises(ValueError):
            self.store.update(file.name, {}, lambda data: {})
        self.assertEqual(file.read_bytes(), b'{"items": BROKEN')

    def test_nonparticipant_write_detected_before_receipt(self):
        hooks = Hooks(self.store)
        original = hooks.persist_session
        def bypass(writer):
            result = original(writer)
            (self.profile / "continue-watching.json").write_text('{"outside": true}')
            return result
        hooks.persist_session = bypass
        with self.assertRaisesRegex(PersistenceError, "unfenced state"):
            self.store.checkpoint(SESSION, hooks)
        self.assertEqual(self.state()["phase"], "FAILED")

    def test_noop_does_not_dirty_generation(self):
        self.store.update("session.json", {}, lambda data: {"window": 10000})
        generation = self.state()["generation"]
        self.store.update("session.json", {}, lambda data: data)
        self.assertEqual(self.state()["generation"], generation)

    def test_wrong_pid_owner_and_stale_session_cannot_write(self):
        writer = self.store.begin_checkpoint(SESSION)
        stranger = PersistenceParticipant(self.profile, EngineOwner(999, "different-owner-12345678"))
        with self.assertRaises(PersistenceError):
            stranger.bind_engine()
        with self.assertRaises(PersistenceError):
            stranger.update("session.json", {}, lambda data: {})
        self.store.fail_checkpoint(SESSION)
        with self.assertRaises(AdmissionClosed):
            writer.update("session.json", {}, lambda data: {})

    def test_lock_deadline_fails_without_cutting_off_active_writer(self):
        import fcntl
        fd = os.open(str(self.store.control / "write.lock"), os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            store = PersistenceParticipant(self.profile, OWNER, lock_timeout=0.03)
            with self.assertRaisesRegex(PersistenceError, "did not drain"):
                store.begin_checkpoint(SESSION)
            self.assertEqual(self.state()["phase"], "ACTIVE")
        finally:
            os.close(fd)

    def test_omitted_required_file_proof_never_completes(self):
        hooks = Hooks(self.store)
        original = hooks.persist_session
        def damage_journal(writer):
            result = original(writer)
            state = self.state()
            del state["proofs"]["continue-watching.json"]
            participant.durable_json(self.store.state_path, state)
            return result
        hooks.persist_session = damage_journal
        with self.assertRaises(PersistenceError):
            self.store.checkpoint(SESSION, hooks)
        self.assertNotEqual(self.state()["phase"], "PARTICIPANT_COMPLETE")

    def test_failed_failure_marker_poison_stops_same_live_transaction(self):
        hooks = Hooks(self.store)
        entered, resume = threading.Event(), threading.Event()
        capture = hooks.capture_final_playback
        def blocked_capture():
            entered.set()
            if not resume.wait(3):
                raise RuntimeError("test capture wait timed out")
            return capture()
        hooks.capture_final_playback = blocked_capture
        result = {}
        def checkpoint():
            try:
                result["receipt"] = self.store.checkpoint(SESSION, hooks)
            except Exception as error:
                result["error"] = error
        original_persist = self.store._persist_state
        def fail_failed_marker(state):
            if state["phase"] == "FAILED":
                raise OSError("injected failure marker write error")
            return original_persist(state)
        with mock.patch.object(self.store, "_persist_state", side_effect=fail_failed_marker):
            worker = threading.Thread(target=checkpoint)
            worker.start()
            try:
                self.assertTrue(entered.wait(3))
                with self.assertRaises(OSError):
                    self.store.fail_checkpoint(SESSION)
            finally:
                resume.set()
                worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
        self.assertNotIn("receipt", result)
        self.assertIsInstance(result.get("error"), PersistenceError)

    def test_parseable_corrupt_journal_rejected_by_read_bind_and_checkpoint(self):
        original = self.state()
        def field(name, value):
            def apply(state):
                state[name] = value
            return apply
        def owner_field(name, value):
            return lambda state: state["owner"].update({name: value})
        cases = [
            ("missing-top-field", lambda state: state.pop("proofs")),
            ("extra-top-field", field("unexpected", True)),
            ("bool-schema", field("schema", True)),
            ("null-owner", field("owner", None)),
            ("extra-owner-field", owner_field("old_pid", 50)),
            ("bool-pid", owner_field("pid", True)),
            ("negative-pid", owner_field("pid", -10)),
            ("invalid-owner-token", owner_field("token", [])),
            ("unknown-phase", field("phase", "SAVED")),
            ("numeric-phase", field("phase", 1)),
            ("active-session", field("session", SESSION)),
            ("missing-fenced-session", field("phase", "FENCED")),
            ("missing-file-proof", lambda state: state["proofs"].pop("continue-watching.json")),
            ("extra-file-proof", lambda state: state["proofs"].update({"not-managed.json": None})),
            ("invalid-proof-type", lambda state: state["proofs"].update({"session.json": 12})),
            ("invalid-proof-hash", lambda state: state["proofs"].update({"session.json": "F" * 64})),
            ("bool-generation", field("generation", True)),
            ("negative-generation", field("generation", -1)),
            ("bool-committed-generation", field("committed_generation", False)),
            ("future-commit", field("committed_generation", 1)),
            ("generation-gap", field("generation", 2)),
            ("missing-pending", field("generation", 1)),
            ("unknown-pending", field("pending", "not-managed.json")),
            ("pending-without-dirty-generation", field("pending", "session.json")),
            ("stage-order", field("stages", ["stop_playback"])),
            ("non-list-stages", field("stages", "")),
            ("active-has-stage", field("stages", ["capture_final_playback"])),
            ("premature-complete", lambda state: state.update(phase="PARTICIPANT_COMPLETE", session=SESSION)),
            ("complete-has-pending", lambda state: state.update(
                phase="PARTICIPANT_COMPLETE", session=SESSION, stages=list(participant.STAGES),
                generation=1, pending="session.json")),
            ("empty-state", lambda state: state.clear()),
        ]
        for name, damage in cases:
            with self.subTest(name=name):
                state = copy.deepcopy(original)
                damage(state)
                participant.durable_json(self.store.state_path, state)
                before = self.store.state_path.read_bytes()
                for action in (self.store._state, self.store.bind_engine,
                               lambda: self.store.begin_checkpoint(SESSION)):
                    with self.assertRaises(PersistenceError):
                        action()
                    self.assertEqual(self.store.state_path.read_bytes(), before)

    def test_live_generation_cannot_regress_to_older_valid_journal(self):
        old = self.state()
        self.store.update("session.json", {}, lambda state: {"window": 10000})
        participant.durable_json(self.store.state_path, old)
        with self.assertRaisesRegex(PersistenceError, "regressed"):
            self.store._state()
        with self.assertRaisesRegex(PersistenceError, "regressed"):
            self.store.bind_engine()


if __name__ == "__main__":
    unittest.main()
