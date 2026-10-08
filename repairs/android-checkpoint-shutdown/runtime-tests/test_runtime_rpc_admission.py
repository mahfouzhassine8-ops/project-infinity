#!/usr/bin/env python3
"""Two host processes exercise actual CC mutations/RPC admission over one profile.

Kodi Python interpreters share an engine PID. Each child supplies that same PID
to the identity API while retaining separate OS processes and real flock locks.
The JSON-RPC double uses a shared SQLite database and explicit coordination.
"""
import argparse
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
import time
from unittest import mock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    test_path = Path(__file__).with_name("test_runtime_checkpoint.py")
    original = sys.argv
    sys.argv = [str(test_path), "--runtime", str(args.runtime.resolve(strict=True))]
    try:
        spec = importlib.util.spec_from_file_location("rpc_runtime_fixture", test_path)
        fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture)
    finally:
        sys.argv = original
    case = fixture.RuntimeTests()
    case.setUp()
    children = []
    try:
        database = case.profile / "rpc-double.db"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE watched (playcount INTEGER NOT NULL)")
            connection.execute("INSERT INTO watched VALUES(1)")
        entry = {"key": fixture.KEY, "media": "movie", "dbid": 42,
                 "title": "Movie", "duration": 900.0, "position": 417.125}
        with fixture.common.persistence_scope():
            data = {"schema": 2, "items": {fixture.KEY: entry}}
            fixture.hub.queue_kodi_sync(data, entry, False)
            fixture.hub.save(case.profile, data)

        context = multiprocessing.get_context("fork")
        entered, release, attempted, acquired, completed = [context.Event() for _ in range(5)]
        results = context.Queue()
        engine_pid = os.getpid()

        def rpc(raw, delay=False, suppress_write=False):
            request = json.loads(raw)
            method = request["method"]
            if method.startswith("VideoLibrary.Set"):
                if delay:
                    entered.set()
                    if not release.wait(6):
                        raise RuntimeError("RPC release deadline exceeded")
                if not suppress_write:
                    with sqlite3.connect(database, timeout=2) as connection:
                        connection.execute("UPDATE watched SET playcount=?",
                                           (request["params"]["playcount"],))
                return json.dumps({"result": "OK"})
            with sqlite3.connect(database, timeout=2) as connection:
                count = connection.execute("SELECT playcount FROM watched").fetchone()[0]
            key = "episodedetails" if method.endswith("EpisodeDetails") else "moviedetails"
            return json.dumps({"result": {key: {"playcount": count}}})

        def old_client():
            actual_pid = os.getpid()
            fixture.runtime._stores.clear()
            sets = []
            def old_rpc(raw):
                if json.loads(raw)["method"].startswith("VideoLibrary.Set"):
                    sets.append(raw)
                return rpc(raw, delay=True)
            with mock.patch.object(fixture.runtime.os, "getpid", return_value=engine_pid):
                fixture.xbmc.executeJSONRPC = old_rpc
                try:
                    assert fixture.hub.flush_kodi_sync(case.profile)
                except fixture.runtime.AdmissionClosed:
                    # The resident may fence between operations, after A's
                    # RPC+ack releases the gate and before this next iteration.
                    # plugin.mutate handles this same expected rejection.
                    pass
                assert sum(json.loads(raw)["params"]["playcount"] == 0 for raw in sets) == 1, \
                    "old client replayed the obsolete operation after yielding admission"
            results.put(("old", actual_pid))

        def new_client_and_checkpoint():
            actual_pid = os.getpid()
            fixture.runtime._stores.clear()
            with mock.patch.object(fixture.runtime.os, "getpid", return_value=engine_pid):
                fixture.xbmc.executeJSONRPC = rpc
                attempted.set()
                with fixture.common.persistence_scope():
                    acquired.set()
                    changed, _ = fixture.plugin._mutate_locked("mark-watched", fixture.KEY, "")
                    assert changed
                store = fixture.runtime.store_for(case.profile)
                store.begin_checkpoint(fixture.SESSION)
                with store.authorized_session(fixture.SESSION):
                    assert fixture.hub.flush_kodi_sync(case.profile, preserve_playcount=True)
                completed.set()
            results.put(("new", actual_pid))

        old = context.Process(target=old_client)
        new = context.Process(target=new_client_and_checkpoint)
        children = [old, new]
        old.start()
        assert entered.wait(5), "old RPC was not reached"
        new.start()
        assert attempted.wait(5), "new client was not admitted to test"
        time.sleep(0.15)
        assert not acquired.is_set(), "new mutation crossed the older in-flight RPC lease"
        assert not completed.is_set(), "checkpoint overtook an admitted RPC"
        release.set()
        for child in children:
            child.join(8)
            assert not child.is_alive() and child.exitcode == 0, "client failed or deadlocked"
        identities = [results.get(timeout=2), results.get(timeout=2)]
        assert len({pid for _, pid in identities}) == 2
        data = fixture.hub.load(case.profile)
        with sqlite3.connect(database) as connection:
            count = connection.execute("SELECT playcount FROM watched").fetchone()[0]
        assert count == 1 and fixture.KEY in data["watched"] and not data.get("pending_kodi_sync")
        assert completed.is_set()
        print("PASS two_actual_processes_old_rpc_new_mutation_checkpoint_order_and_real_flock")
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(2)
        case.tearDown()

    # A nominal OK response with a failed write must not consume its durable op.
    case = fixture.RuntimeTests()
    case.setUp()
    try:
        entry = {"key": fixture.KEY, "media": "movie", "dbid": 42, "title": "Movie"}
        with fixture.common.persistence_scope():
            data = {"schema": 2, "items": {fixture.KEY: entry}}
            fixture.hub.queue_kodi_sync(data, entry, True)
            fixture.hub.save(case.profile, data)
        def failed_write(raw):
            method = json.loads(raw)["method"]
            return json.dumps({"result": "OK"} if method.startswith("VideoLibrary.Set") else
                              {"result": {"moviedetails": {"playcount": 0}}})
        fixture.xbmc.executeJSONRPC = failed_write
        assert fixture.hub.flush_kodi_sync(case.profile) is False
        assert fixture.hub.load(case.profile)["pending_kodi_sync"]
        fixture.xbmc.executeJSONRPC = lambda raw: json.dumps({"result": {}})
        assert fixture.hub.flush_kodi_sync(case.profile) is False
        assert fixture.hub.load(case.profile)["pending_kodi_sync"]
        print("PASS failed_readback_and_malformed_ack_keep_required_operation_for_retry")
    finally:
        fixture.xbmc.executeJSONRPC = fixture.rpc
        case.tearDown()


if __name__ == "__main__":
    main()
