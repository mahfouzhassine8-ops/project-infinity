# SPDX-License-Identifier: GPL-2.0-or-later
"""Command Center checked JSON writer used by the resident checkpoint service.

All CC writers must use this gate before its receipt is meaningful. This module
never stops Python, sends Kodi Quit, kills a process, or grants SAFE_TO_TERMINATE.
Native settings/database and other add-on owners require separate barriers.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from typing import Callable


FILES = frozenset(("continue-watching.json", "playback-memory.json", "session.json",
                   "boot-history.json", "boot-marker.json"))
TOKEN = re.compile(r"[A-Za-z0-9_-]{16,128}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
STAGES = ("capture_final_playback", "persist_final_playback", "freeze_playback",
          "drain_required_events", "persist_session")
STATE_KEYS = frozenset(("schema", "owner", "phase", "session", "generation",
                        "committed_generation", "pending", "proofs", "stages"))


class PersistenceError(RuntimeError):
    pass


class AdmissionClosed(PersistenceError):
    pass


def _valid_token(value):
    return isinstance(value, str) and TOKEN.fullmatch(value) is not None


def _validate_state(state):
    """Reject parseable journal damage before it can weaken the barrier."""
    def require(condition, reason):
        if not condition:
            raise PersistenceError("invalid participant journal: " + reason)
    require(isinstance(state, dict) and set(state) == STATE_KEYS, "schema fields")
    require(type(state["schema"]) is int and state["schema"] == 1, "schema version")
    owner = state["owner"]
    require(isinstance(owner, dict) and set(owner) == {"pid", "token"}, "owner fields")
    require(type(owner["pid"]) is int and owner["pid"] > 0 and _valid_token(owner["token"]),
            "owner identity")
    phase = state["phase"]
    require(isinstance(phase, str) and phase in ("ACTIVE", "FENCED", "FAILED", "PARTICIPANT_COMPLETE"),
            "phase")
    generation, committed = state["generation"], state["committed_generation"]
    require(type(generation) is int and type(committed) is int and
            0 <= committed <= generation and generation - committed <= 1, "generation counters")
    pending = state["pending"]
    require(pending is None or isinstance(pending, str) and pending in FILES, "pending file")
    require((pending is None and generation == committed) or
            (pending is not None and generation == committed + 1), "pending generation")
    proofs = state["proofs"]
    require(isinstance(proofs, dict) and set(proofs) == FILES, "complete required file proofs")
    require(all(value is None or isinstance(value, str) and DIGEST.fullmatch(value)
                for value in proofs.values()), "proof digest")
    stages = state["stages"]
    require(isinstance(stages, list) and len(stages) <= len(STAGES) and
            stages == list(STAGES[:len(stages)]), "ordered stage prefix")
    if phase == "ACTIVE":
        require(state["session"] is None and not stages, "active phase session/stages")
    else:
        require(_valid_token(state["session"]), "checkpoint session")
    if phase == "PARTICIPANT_COMPLETE":
        require(pending is None and stages == list(STAGES), "completed barrier invariants")


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _read(path):
    # A malformed/unreadable file must never become an empty/default state.
    if path.is_symlink():
        raise PersistenceError("symlink is not a managed persistence file")
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, None
    def invalid_constant(value):
        raise ValueError("non-finite JSON value: " + value)
    data = json.loads(raw, parse_constant=invalid_constant)
    if not isinstance(data, dict):
        raise PersistenceError("managed JSON must be an object")
    return data, raw


def _sync_directory(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_json(path, value):
    """Checked write: unique temporary file, fsync, rename, directory fsync."""
    if path.is_symlink():
        raise PersistenceError("refusing to replace symlink")
    payload = _json_bytes(value)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EngineOwner:
    pid: int
    token: str

    def __post_init__(self):
        if type(self.pid) is not int or self.pid <= 0 or not _valid_token(self.token):
            raise ValueError("positive engine PID and unique owner token required")


@dataclass(frozen=True)
class OperationResult:
    ok: bool
    detail: str = ""


class PersistenceParticipant:
    def __init__(self, profile, owner: EngineOwner, lock_timeout=5.0):
        self.profile = Path(profile).resolve(strict=True)
        self.owner = owner
        self._observed_generation = -1
        self._failed_sessions = set()
        self._thread_gate = threading.RLock()
        self._local = threading.local()
        self.lock_timeout = float(lock_timeout)
        if not self.profile.is_dir() or self.lock_timeout <= 0:
            raise ValueError("existing profile directory and positive lock timeout required")
        self.control = self.profile / ".android-checkpoint"
        if self.control.is_symlink():
            raise PersistenceError("control directory must not be a symlink")
        try:
            self.control.mkdir(mode=0o700)
            _sync_directory(self.profile)
        except FileExistsError:
            if not self.control.is_dir():
                raise PersistenceError("control path is not a directory")
        self.state_path = self.control / "participant.json"

    @contextmanager
    def _gate(self):
        if not self._thread_gate.acquire(timeout=self.lock_timeout):
            raise PersistenceError("participant thread writer did not drain")
        if getattr(self._local, "gate_depth", 0):
            self._local.gate_depth += 1
            try:
                yield
            finally:
                self._local.gate_depth -= 1
                self._thread_gate.release()
            return
        try:
            with self._os_gate():
                self._local.gate_depth = 1
                try:
                    yield
                finally:
                    self._local.gate_depth = 0
        finally:
            self._thread_gate.release()

    @contextmanager
    def _os_gate(self):
        fd = os.open(str(self.control / "write.lock"),
                     os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        deadline = time.monotonic() + self.lock_timeout
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise PersistenceError("persistence writer did not drain before deadline")
                    time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    @contextmanager
    def transaction(self, session=None):
        """Existing Kodi callbacks may nest checked JSON operations in one RMW gate."""
        session = session if session is not None else getattr(self._local, "session", None)
        with self._gate():
            self._admit(self._state(), session)
            prior = getattr(self._local, "session", None)
            self._local.session = session
            try:
                yield
            finally:
                self._local.session = prior

    def read(self, name, default):
        if name not in FILES:
            raise ValueError("managed filename required")
        with self._gate():
            state = self._state()
            data, raw = _read(self.profile / name)
            digest = hashlib.sha256(raw).hexdigest() if raw is not None else None
            if digest != state["proofs"][name]:
                raise PersistenceError("writer bypassed participant gate: " + name)
            return copy.deepcopy(default if data is None else data)

    @contextmanager
    def authorized_session(self, session):
        """Permit resident checkpoint writes while keeping Kodi RPC outside flock."""
        with self._gate():
            self._admit(self._state(), session)
        prior = getattr(self._local, "session", None)
        self._local.session = session
        try:
            yield
        finally:
            self._local.session = prior

    def _state(self):
        state, _ = _read(self.state_path)
        _validate_state(state)
        if state["owner"] != asdict(self.owner):
            raise PersistenceError("participant owner is unbound or does not match engine")
        if state["generation"] < self._observed_generation:
            raise PersistenceError("participant generation regressed during this engine session")
        self._observed_generation = state["generation"]
        return state

    def _persist_state(self, state):
        _validate_state(state)
        if state["owner"] != asdict(self.owner) or state["generation"] < self._observed_generation:
            raise PersistenceError("refusing mismatched owner or regressed generation")
        durable_json(self.state_path, state)
        self._observed_generation = state["generation"]

    def bind_engine(self, expected_previous_owner=None):
        """Startup only. Caller must prove old engine death before owner replacement.

        expected_previous_owner is an explicit compare-and-swap guard, never a
        substitute for the Android coordinator's PID/start-token death check.
        Rebinding the same engine cannot reopen a failed or fenced transaction.
        """
        with self._gate():
            prior, _ = _read(self.state_path)
            if prior is not None:
                _validate_state(prior)
                if prior["owner"] == asdict(self.owner):
                    self._state()  # Validate monotonicity even when merely reusing an owner.
                    return
                if expected_previous_owner is None or prior["owner"] != asdict(expected_previous_owner):
                    raise PersistenceError("existing engine owner has not been explicitly retired")
            proofs = {}
            for name in sorted(FILES):
                _, raw = _read(self.profile / name)
                if raw is not None:
                    fd = os.open(str(self.profile / name), os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                proofs[name] = hashlib.sha256(raw).hexdigest() if raw is not None else None
            _sync_directory(self.profile)
            self._persist_state({"schema": 1, "owner": asdict(self.owner), "phase": "ACTIVE",
                                 "session": None, "generation": 0, "committed_generation": 0,
                                 "pending": None, "proofs": proofs, "stages": []})

    def _admit(self, state, session):
        if session in self._failed_sessions or state["session"] in self._failed_sessions:
            raise AdmissionClosed("checkpoint session was revoked locally")
        if session is None:
            if state["phase"] != "ACTIVE":
                raise AdmissionClosed("normal writes are fenced for shutdown")
        elif state["phase"] != "FENCED" or state["session"] != session:
            raise AdmissionClosed("checkpoint session is stale, failed, or already sealed")
        if state["pending"] is not None or state["generation"] != state["committed_generation"]:
            raise PersistenceError("uncommitted generation requires explicit recovery")

    def update(self, name, default, mutate: Callable, session=None):
        """Hold the OS gate across read + pure mutation + complete durable commit.

        mutate must not call Kodi, block for UI, or re-enter this participant.
        Dialog input and RPC preparation belong outside this critical section.
        """
        session = session if session is not None else getattr(self._local, "session", None)
        if name not in FILES or not isinstance(default, dict):
            raise ValueError("managed filename and object default required")
        with self._gate():
            state = self._state()
            self._admit(state, session)
            before, raw = _read(self.profile / name)
            digest = hashlib.sha256(raw).hexdigest() if raw is not None else None
            if digest != state["proofs"][name]:
                raise PersistenceError("writer bypassed participant gate: " + name)
            result = mutate(copy.deepcopy(default if before is None else before))
            if not isinstance(result, dict):
                raise PersistenceError("mutation must return complete JSON object")
            _json_bytes(result)  # Reject unserializable or non-finite values before intent.
            if before is not None and _json_bytes(before) == _json_bytes(result):
                return copy.deepcopy(result)
            state["generation"] += 1
            state["pending"] = name
            self._persist_state(state)  # Write intent before target can change.
            digest = durable_json(self.profile / name, result)
            state["proofs"][name] = digest
            state["committed_generation"] = state["generation"]
            state["pending"] = None
            self._persist_state(state)
            return copy.deepcopy(result)

    def begin_checkpoint(self, session):
        if not _valid_token(session):
            raise ValueError("unique checkpoint session token required")
        with self._gate():
            state = self._state()
            self._admit(state, None)
            if session in self._failed_sessions:
                raise AdmissionClosed("checkpoint session was revoked locally")
            state.update(phase="FENCED", session=session, stages=[])
            self._persist_state(state)
        return CheckpointWriter(self, session)

    def remove(self, name, session=None):
        """Durably remove a managed marker under the same generation protocol."""
        session = session if session is not None else getattr(self._local, "session", None)
        if name not in FILES:
            raise ValueError("managed filename required")
        with self._gate():
            state = self._state()
            self._admit(state, session)
            _, raw = _read(self.profile / name)
            digest = hashlib.sha256(raw).hexdigest() if raw is not None else None
            if digest != state["proofs"][name]:
                raise PersistenceError("writer bypassed participant gate: " + name)
            if raw is None:
                return
            state["generation"] += 1
            state["pending"] = name
            self._persist_state(state)
            (self.profile / name).unlink()
            _sync_directory(self.profile)
            state["proofs"][name] = None
            state["committed_generation"] = state["generation"]
            state["pending"] = None
            self._persist_state(state)

    def _stage(self, session, stage, result):
        if not isinstance(result, OperationResult) or result.ok is not True:
            raise PersistenceError(stage + " did not return a checked success")
        with self._gate():
            state = self._state()
            self._admit(state, session)
            if len(state["stages"]) >= len(STAGES) or STAGES[len(state["stages"])] != stage:
                raise PersistenceError("checkpoint playback stage ordering violation")
            state["stages"].append(stage)
            self._persist_state(state)

    def fail_checkpoint(self, session):
        if not _valid_token(session):
            raise ValueError("valid checkpoint session token required")
        # Poison before lock acquisition or disk I/O: a failed FAILED marker may
        # never allow this live participant to resume the revoked transaction.
        # Other interpreters require the coordinator to revoke the owner/session
        # independently; an unwritable file cannot communicate cancellation.
        self._failed_sessions.add(session)
        with self._gate():
            state = self._state()
            if state["session"] != session or state["phase"] not in ("FENCED", "FAILED"):
                raise PersistenceError("cannot fail a different/sealed session")
            state["phase"] = "FAILED"
            self._persist_state(state)

    def _seal(self, session):
        with self._gate():
            state = self._state()
            self._admit(state, session)
            if state["stages"] != list(STAGES):
                raise PersistenceError("required persistence stage missing")
            for name in sorted(FILES):
                expected = state["proofs"][name]
                _, raw = _read(self.profile / name)
                actual = hashlib.sha256(raw).hexdigest() if raw is not None else None
                if actual != expected:
                    raise PersistenceError("unfenced state changed during checkpoint: " + name)
            state["phase"] = "PARTICIPANT_COMPLETE"
            self._persist_state(state)
            if session in self._failed_sessions:
                raise AdmissionClosed("checkpoint session was revoked while sealing")
            return {"status": "PARTICIPANT_COMPLETE", "participant": "command-center-json",
                    "owner": asdict(self.owner), "session": session,
                    "generation": state["generation"], "files": copy.deepcopy(state["proofs"]),
                    "global_safe_to_terminate": False}

    def checkpoint(self, session, hooks):
        """Enlist existing service; no Python abort or callback thread joins.

        Hooks run without holding flock. Required event handlers receive this
        transaction's writer. Each hook must return OperationResult after checked
        work, including explicit successful no-op if no playback/state is dirty.
        Capture returns (OperationResult, immutable caller-owned snapshot).
        Final resume is committed while the native-frozen player clock remains
        available; the freeze hook confirms the native owner proof.
        Drain must preserve ended/watched callbacks and confirm Kodi playcount
        RPC outcomes; other native DB/settings owners remain the native barrier.
        """
        writer = self.begin_checkpoint(session)
        try:
            captured, snapshot = hooks.capture_final_playback()
            self._stage(session, "capture_final_playback", captured)
            self._stage(session, "persist_final_playback", hooks.persist_final_playback(snapshot, writer))
            self._stage(session, "freeze_playback", hooks.freeze_playback())
            self._stage(session, "drain_required_events", hooks.drain_required_events(writer))
            self._stage(session, "persist_session", hooks.persist_session(writer))
            return self._seal(session)
        except Exception:
            # Failure remains fenced even if a disk error prevents recording FAILED.
            try:
                self.fail_checkpoint(session)
            except Exception:
                pass
            raise


class CheckpointWriter:
    """Session-scoped writes; this object cannot remove the admission fence."""
    def __init__(self, participant, session):
        self._participant, self._session = participant, session

    def update(self, name, default, mutate):
        return self._participant.update(name, default, mutate, self._session)

    def remove(self, name):
        return self._participant.remove(name, self._session)
