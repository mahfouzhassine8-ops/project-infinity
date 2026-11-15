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

## SEARCH-WATCHLIST-02 — Infinity Search result does not expose existing Infinity Trakt / Watchlist action

- **Status:** OPEN — user-reported screenshot on November 14, 2026; underlying code cause not yet demonstrated.
- **Priority:** High for the Search → Save to Watchlist user journey.
- **User observation:** In **Infinity Search — TV Shows**, **Otaku — 1 results** returned **From Overshadowed to Overpowered: Second Reincarnation of a Talentless Sage** (2026). The selected aggregate result showed title, poster, and synopsis; long-press opened **Open in Otaku** and **Information** only, without the expected **Infinity Trakt** / **Add to Watchlist** popup. The screenshot does not show the installed APK version and cannot establish whether a verified cross-provider media identifier was present.
- **Preserved expectation:** Ordinary TV Shows search → long press → **Infinity Trakt** → Add to Watchlist → title visible under **Infinity TV → Watchlist**. Saving is not playback and must never create progress, watched, history, or Next Episode records.
- **Narrow source clue (not root-cause proof):** Existing Command Center `plugin.py` from the watchlist playback branch has `_menu_rows()` and `show_item_menu()` supporting an **Add to Watchlist** action for a valid selected entry. An older registered native `Infinity Trakt` Kodi context entry also exists separately. The screenshot shows the aggregated Search's **Open in Otaku / Information** actions instead. Determine whether the normalized aggregate item fails to expose the existing context entry, lacks validated media identity/type, or invokes a separate menu path; **do not assume provider search itself failed**.
- **Investigation:** Trace the selected Search result's exact ListItem, native `kodi.context.item` visibility, provider opening action and first-party Watchlist menu. Preserve source URL, media kind, verified IDs and selection/token across the Search display/long-press seam when available. If identity is ambiguous or unavailable, keep existing safe behavior and show a truthful path to verify/resolve; never invent IDs or match by title alone.
- **Required regression coverage:** Otaku single-result TV title; known good native TV provider result; a regular movie; repeated Search, long press, focus and cancel; typed identity with verified IDs and missing-ID cases; Add to Watchlist duplicate-safe and no fake playback. The provider's own native search and player navigation must remain unchanged.
- **Strict scope:** Universal **Infinity Search to existing first-party Watchlist menu** integration, not an Otaku-specific workaround. Do not edit Otaku or other providers, Trakt storage semantics, playback tracking/resume, search engines, unrelated UI, shutdown, Cast, Cobra, or signing/release pointers without separate approval.
- **Acceptance:** A recognized TV title from aggregated Infinity Search can use the existing Infinity Trakt popup and be saved into the existing Infinity TV Watchlist without changing provider search results or creating playback history. Evidence-backed minimal code fix, focused tests and preservation proof before any signed update.

**Record provenance:** User-submitted screenshot `22513.jpg`; no runtime log or exact installed version supplied with this screenshot. A visible missing action is established; a specific implementation defect is **not yet proved**.

## Other workstreams

Casting is separately tracked in existing Cast branches and is **not changed or authorized** by SHUTDOWN-01.
