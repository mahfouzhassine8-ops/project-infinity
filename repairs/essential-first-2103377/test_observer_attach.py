#!/usr/bin/env python3
"""Negative control: exercise the unchanged shipped observer with real SQLite.

The add-on's primary connection is private. ATTACH targets shared protected
data, which must not become optional solely because of the primary path.
"""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "repairs/android-checkpoint-shutdown/writers/observer.py"

def run():
    spec = importlib.util.spec_from_file_location("locked_observer", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_connect = sqlite3.connect
    failures, touches = [], []
    with tempfile.TemporaryDirectory(prefix="essential-attach-") as folder:
        private = Path(folder) / "private-cache.db"
        shared = Path(folder) / "protected-library.db"
        with original_connect(shared) as db:
            db.execute("CREATE TABLE history(position)")
        observer = module.Observer(lambda reason, *detail: failures.append(reason),
                                   lambda path, kind: touches.append((str(path), kind)))
        try:
            db = sqlite3.connect(private)
            db.execute("ATTACH DATABASE ? AS protected", (str(shared),))
            db.execute("INSERT INTO protected.history VALUES(321)")
            db.commit()
            db.close()
            assert observer.finish()
        finally:
            for owner, name, original, replacement in reversed(observer.originals):
                setattr(owner, name, original)
        with original_connect(shared) as db:
            assert db.execute("SELECT position FROM history").fetchall() == [(321,)]
        assert (str(private), "sqlite") in touches
        assert not any(path == str(shared) for path, _ in touches)
        assert not failures, failures
    return {
        "outcome": "REPRODUCED_UNSAFE_OPTIONAL_CLASSIFICATION_GAP",
        "unchanged_observer_tracked_primary_database": True,
        "shared_attached_database_modified": True,
        "shared_attached_database_recorded": False,
        "observer_reported_failure": False,
        "production_fix_verified": False,
    }

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
