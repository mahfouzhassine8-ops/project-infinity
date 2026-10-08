# SPDX-License-Identifier: GPL-2.0-or-later
"""Resident Command Center participant for the native Android checkpoint API.

Only the native owner may authorize engine termination. All receipts here are
scoped to Command Center JSON state and the named shutdown transaction.
"""
from contextlib import contextmanager
from functools import wraps
import json
import math
import os
from pathlib import Path
import threading
import time

from persistence_participant import (AdmissionClosed, EngineOwner, FILES,
                                     OperationResult, PersistenceError,
                                     PersistenceParticipant, durable_json)

API = 1
ADDON_VERSION = "0.3.5.19"
_stores = {}
_stores_lock = threading.RLock()


def read_protocol(path):
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError:
        return None
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise PersistenceError("checkpoint protocol is not a JSON object")
    return value


def store_for(profile):
    profile = Path(profile).resolve()
    with _stores_lock:
        cached = _stores.get(str(profile))
        if cached is not None:
            return cached
        owner_path = profile / ".android-checkpoint" / "engine.json"
        engine = read_protocol(owner_path)
        if engine is None:
            return None  # Legacy startup remains usable; no participant receipt can exist.
        if type(engine.get("schema")) is not int or engine.get("schema") != API or \
                type(engine.get("native_api")) is not int or engine.get("native_api") != API or \
                type(engine.get("pid")) is not int or engine.get("pid") != os.getpid():
            raise PersistenceError("native checkpoint engine identity/API mismatch")
        owner = EngineOwner(engine["pid"], engine["owner"])
        previous = engine.get("previous_owner")
        prior = EngineOwner(previous["pid"], previous["token"]) if previous else None
        store = PersistenceParticipant(profile, owner)
        store.bind_engine(expected_previous_owner=prior)
        _stores[str(profile)] = store
        return store


@contextmanager
def write_scope(profile, session=None):
    store = store_for(profile)
    if store is None:
        yield
    else:
        with store.transaction(session):
            yield


def serialized_profile(profile_provider):
    def decorator(function):
        @wraps(function)
        def guarded(*args, **kwargs):
            with write_scope(profile_provider(*args, **kwargs)):
                return function(*args, **kwargs)
        return guarded
    return decorator


class ResidentCheckpoint:
    def __init__(self, profile, player, experience, stability, api):
        self.profile = Path(profile)
        self.player, self.experience, self.stability, self.api = player, experience, stability, api
        self.control = self.profile / ".android-checkpoint"
        self.store = None
        self.session = None
        self.snapshot = None
        self.writer = None
        self.operations = []
        self.events = []
        self.drain_seen = False
        self.phase = "IDLE"
        self._lock = threading.RLock()

    def _identity(self):
        return {"schema": API, "pid": os.getpid(), "owner": self.store.owner.token,
                "session": self.session}

    def _response(self, status, error=None):
        response = dict(self._identity(), status=status, operations=list(self.operations),
                        participant="command-center-json", global_safe_to_terminate=False)
        if error:
            response["error"] = str(error)[:240]
        durable_json(self.control / "response.json", response)

    def _operation(self, name, function):
        started = time.monotonic()
        try:
            result = function()
        except Exception:
            self.operations.append({"name": name, "ok": False,
                                    "elapsed_ms": round((time.monotonic() - started) * 1000, 3)})
            raise
        self.operations.append({"name": name, "ok": True,
                                "elapsed_ms": round((time.monotonic() - started) * 1000, 3)})
        return result

    def register(self):
        if self.store is not None:
            return True
        if self.api["version"]() != ADDON_VERSION:
            raise PersistenceError("unsupported installed Command Center version")
        store = store_for(self.profile)
        if store is None:
            return False
        self.store = store
        durable_json(self.control / "active.json", dict(self._identity(), status="ACTIVE",
            addon_version=ADDON_VERSION, participant_api=API,
            required_files=sorted(FILES)))
        return True

    def record_event(self, kind):
        with self._lock:
            if self.session is None:
                return False
            self.events.append(kind)
            return True

    def notification(self, sender, method, data):
        if sender != "Infinity" or method != "Other.InfinityCheckpointDrain":
            return
        try:
            marker = json.loads(data) if isinstance(data, str) else data
            with self._lock:
                if self.session and all(marker.get(k) == v for k, v in self._identity().items()
                                        if k != "schema"):
                    self.drain_seen = True
        except (ValueError, TypeError, AttributeError):
            return

    def _matches(self, request):
        return type(request.get("schema")) is int and request.get("schema") == API and type(request.get("pid")) is int and \
            request.get("pid") == os.getpid() and request.get("owner") == self.store.owner.token

    def _capture(self):
        player = self.player
        playing, video = bool(player.isPlaying()), bool(player.isPlayingVideo())
        live = bool(self.api["live"]())
        snapshot = {"playing": playing, "video": video, "live": live,
                    "entry": None, "position": None, "duration": None}
        props = self.api["player_properties"]() if video else None
        if video and self.api["enabled"]("playback_memory_enabled", True):
            if not isinstance(props, dict) or not props:
                raise PersistenceError("final audio/subtitle state unavailable")
            player.last_props = props
        if not playing and player.cw_item and player.cw_key and self.api["enabled"]("continue_watching_enabled", True):
            # The native ended callback may already have released the clock but
            # still be queued for this Python interpreter. Preserve identity so
            # the FIFO drain can commit watched state without fabricating time.
            snapshot.update(entry=dict(player.cw_item), key=player.cw_key)
        if video and not live and self.api["enabled"]("continue_watching_enabled", True):
            duration = float(player.getTotalTime())
            if duration == 0.0 and isinstance(props, dict) and props.get('canseek') is False:
                snapshot.update(live=True, resume_exclusion='unseekable-without-duration')
            else:
                if not player.cw_item:
                    player._arm_continue()
                if not player.cw_item or not player.cw_key:
                    raise PersistenceError("active video has no verified Resume Hub identity")
                position = float(player.getTime())
                if not math.isfinite(position) or not math.isfinite(duration) or position < 0 or duration <= 0:
                    raise PersistenceError("active video final player clock unavailable")
                snapshot.update(entry=dict(player.cw_item), key=player.cw_key,
                                position=position, duration=duration)
        return snapshot

    def _drain_kodi_sync(self):
        with self.store.authorized_session(self.session):
            if not self.api["hub"].flush_kodi_sync(self.profile, preserve_playcount=True):
                raise PersistenceError("required Kodi watched-state update failed")

    def _persist_progress(self, completed=False):
        snapshot = self.snapshot
        entry = snapshot.get("entry")
        if not entry:
            return
        hub = self.api["hub"]
        key, position, duration = snapshot["key"], snapshot["position"], snapshot["duration"]
        if position is None or duration is None:
            if not completed:
                return
            # Actual completion is sufficient evidence for watched state. Use
            # existing duration only as metadata; never invent a final clock.
            prior = hub.load(self.profile).get('items', {}).get(key, {})
            position = float(prior.get('position') or 0.0)
            duration = float(prior.get('duration') or 0.0)
        with self.store.transaction(self.session):
            data = hub.load(self.profile)
            percent = position / duration * 100.0 if duration > 0 else 0.0
            if completed or percent >= 95.0:
                # A periodic >=95% save or an earlier ended event may already
                # have marked this playback. Never increment it twice at exit.
                if not hub.is_watched(data, key):
                    final = dict(entry, position=round(position, 3), duration=round(duration, 3))
                    data, watched = hub.mark_watched_data(data, key, final, completed=True)
                    hub.queue_kodi_sync(data, watched, True)
                    hub.save(self.profile, data, self.api["publish"])
                else:
                    watched = data["watched"][key]
            elif position >= 30.0 and duration >= 120.0 and percent >= 1.0:
                final = dict(entry, position=round(position, 3), duration=round(duration, 3),
                             percentage=round(percent, 2))
                previous = data.setdefault("items", {}).get(key, {})
                if any(previous.get(name) != value for name, value in final.items()):
                    final['updated'] = int(time.time())
                    data['items'][key] = final
                    hub.save(self.profile, data, self.api["publish"])

    def _prepare(self, request):
        session = request.get("session")
        with self.api["progress_lock"]:
            with self._lock:
                self.writer = self.store.begin_checkpoint(session)
                self.session = session
                self.phase = "PERSISTING"
        self.snapshot = self._operation("capture_final_playback", self._capture)
        self.store._stage(session, "capture_final_playback", OperationResult(True))
        self._operation("persist_final_playback", self._persist_progress)
        self._operation("drain_kodi_watched", self._drain_kodi_sync)
        with self.store.transaction(session):
            self._operation("persist_playback_selections", self.player.persist)
            self._operation("capture_browsing_session", self.experience.shutdown)
        self.store._stage(session, "persist_final_playback", OperationResult(True))
        self.phase = "PLAYBACK_CHECKPOINTED"
        self._response(self.phase)

    def _finalize(self, request):
        if request.get("player_freeze_complete") is not True:
            raise PersistenceError("native player freeze has not completed")
        with self._lock:
            if not self.drain_seen:
                return
            events = list(self.events)
        if "started" in events:
            raise PersistenceError("new playback crossed native shutdown admission fence")
        if self.snapshot.get('entry') and self.snapshot.get('position') is None and \
                any(event in ('stopped', 'error') for event in events) and 'ended' not in events:
            raise PersistenceError('final Resume Hub clock unavailable for pending playback stop')
        self.store._stage(self.session, "freeze_playback", OperationResult(True))
        self._operation("drain_required_events", lambda: self._persist_progress(completed=True)
                        if "ended" in events else None)
        self._operation("drain_final_kodi_watched", self._drain_kodi_sync)
        self.store._stage(self.session, "drain_required_events", OperationResult(True))
        with self.store.transaction(self.session):
            self._operation("persist_clean_stop", self.stability.clean_stop)
        self.store._stage(self.session, "persist_session", OperationResult(True))
        receipt = self.store._seal(self.session)
        self.phase = "PARTICIPANT_COMPLETE"
        self._response(self.phase)
        return receipt

    def poll(self):
        """Returns True when normal service work must remain parked."""
        try:
            if not self.register():
                return False
            request = read_protocol(self.control / "request.json")
            if not request or not self._matches(request):
                return self.session is not None
            phase = request.get("phase")
            if self.session is None and phase == "PREPARE":
                self._prepare(request)
            elif request.get("session") == self.session and phase == "FINALIZE" and self.phase == "PLAYBACK_CHECKPOINTED":
                self._finalize(request)
            elif request.get("session") == self.session and phase == "CANCEL":
                raise PersistenceError("native checkpoint transaction revoked")
            return self.session is not None
        except Exception as error:
            if self.session and self.store:
                self.phase = "CHECKPOINT_FAILED"
                try:
                    self.store.fail_checkpoint(self.session)
                except Exception:
                    pass
                try:
                    self._response(self.phase, error)
                except Exception:
                    pass
            self.api["log"]("Android checkpoint failed: " + type(error).__name__ + ": " + str(error))
            return self.session is not None
