# Infinity — Open Repair List (2026-11-14)

This is a **tracking record only**, not authorization to modify production source, sign an APK, or update any release pointer. Preserve original files, source hashes, signing identity, user data, Cobra, and everything outside a separately authorized repair scope.

## SHUTDOWN-01 — Exit checkpoint fails with unresolved Python/SQLite persistence

- **Status:** OPEN — investigated from existing diagnostics; repair not implemented
- **Priority:** High (blocks a verified safe application exit)
- **Source:** User-supplied `Infinity-Diagnostics-20261114-214040.zip` (November 14, 2026 evening capture). Do not publish raw diagnostics, device details, private paths or source URLs.
- **Observed shutdown:** `CHECKPOINT_FAILED` after **25,228 ms**; coordinator error `native_admission: checkpoint_deadline_exceeded; owner proof incomplete`.
- **Identified writer failures:**
  1. `plugin.video.playlistbrowser:service_entry.py` — `buffer_flush_failed`, `exception=ValueError` in buffered-write/cleanup observation. `python_services` reported `pending_writer`.
  2. `plugin.video.themoviedb.helper:service.py` — `sqlite_collected_with_pending_transaction` and `sqlite_pending_transaction_at_retirement`.
  3. `plugin.video.themoviedb.helper:script.py` — `sqlite_pending_transaction_at_retirement`.
  4. A protected SQLite WAL write transaction associated with TMDb Helper's `ItemQueries.db` remained unverified.
- **Coordinator state:** `essential_writes_durable=false`, `essential_writes_sealed=false`; **11 owner-verification blockers** in the final inventory. `active_native_writers=0` is **not** proof of persistence completion, and the 11 owner blockers are **not 11 proven active writers**.
- **Exit proof:** `process_death_confirmed=false` and `whole_package_death_confirmed=false`. `kodi-process-state.json` reporting `live=false` is not itself evidence of OS process death.
- **Uncertainty:** The logs identify the failed write/retirement paths, but do **not** prove that TMDb Helper alone caused the full deadline, prove user data loss, or isolate a single code-level defect. Historical shutdown records must not be attributed to a particular installed versionCode without producer provenance.

### Required targeted investigation (for Codex when authorized)

- Find the cause and lifecycle owner of Playlist Browser's `ValueError` during buffer flush and of TMDb Helper's pending SQLite transactions during service/script retirement.
- Trace checkpoint generation/lease ownership and durability acknowledgments through `python_services`, `native_databases`, and `native_admission`. Distinguish a real active writer from a stale or unverified retirement receipt.
- Ensure commits/rollbacks and flush completion are **safely verified** before owner release; **never weaken essential-write guards, discard pending writes, force-kill, or falsely report clean exit**.
- Select the smallest evidence-backed shutdown-only correction, with focused concurrency/SQLite tests, owner-retirement proofs, preservation checks and a real Android exit/process-death verification; no unrelated broad refactor.

### Hard preservation limits

**Cobra untouched. Cast untouched.** All other Infinity playback, providers, Watchlist/tracking, search, UI, skin, networking, user settings, personal data and native components outside a later authorized defect-specific repair remain unchanged.

### Acceptance / exit criteria

- Playlist Browser buffered-write flush has a verified success or safe failure/rollback outcome.
- TMDb Helper's relevant SQLite connections and transactions have verified completion or safely handled abort and clean retirement.
- Shutdown checkpoint returns an authenticated durable success, **not** a fabricated completion; owner inventory reconciles without unresolved essential writes.
- Android reports actual app/process exit; safe relaunch and data integrity verified.
- One candidate only after source cause and focused gates pass; preserve original signing continuity and an appropriate forward recovery.

**Record provenance:** Derived from the above November 14 diagnostic archive; no new phone test requested by this list update.

## Other workstreams

Casting is separately tracked in existing Cast branches and is **not changed or authorized** by SHUTDOWN-01.
