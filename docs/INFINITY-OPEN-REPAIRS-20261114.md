# Infinity — Open Repair List (2026-11-14)

This is a **tracking record only**, not authorization to modify production source, sign an APK, or update any release pointer. Preserve original files, source hashes, signing identity, user data, Cobra, and everything outside a separately authorized repair scope.

## Active non-Cast priority — November 15, 2026

**Casting status: ON HOLD / NOT VERIFIED.** The owner could not complete a proper current casting test because expected receiver choices were absent. Do not mark casting repaired, failed, or accepted; no new Cast test, patch, signing, or provider-discovery change is authorized in this workstream. Preserve existing Cast candidates and recovery.

**New regression reported November 15:** the owner reports the intermittent *empty shell* has returned. Prior known symptom: navigation/skin render, but provider/Health Center Python actions do not reliably initialize. **Do not claim a new APK or a particular installation caused it without verified version and process-specific evidence.**

**Work these issues independently, in this order:**

1. **EMPTY-SHELL-05:** Read-only native/Python startup and invocation-admission comparison against signed 2103486, the last physically tested build without recurrence; check whether a failed Close leaves the same process with admission closed, or new Python work stalls during interpreter initialization. Preserve current profiles and storage.
2. **MOVIE-CONTINUE-04:** Protect the current saved movie state; compare authoritative `continue-watching.json` records, active profile, hidden flags, projection and source recovery read-only. The fallback dialog offering Seren does *not* itself prove saved records were deleted. No destructive migration or playback-history manipulation.
3. **SHUTDOWN-01:** Investigate TMDb Helper SQLite transactions and Playlist Browser buffer flush `ValueError` as separate pending writer paths. Resolve durability and owner retirement without weakening checkpoint safeguards, then prove real exit.
4. **SEARCH-WATCHLIST-02:** Trace the missing Infinity Trakt action on aggregated Otaku search results into the existing first-party Watchlist menu. Fix universally, not by modifying individual providers or inventing IDs.

**Release discipline:** one isolated defect-specific diff at a time; no combined speculative build. Verify frozen production/member hashes and original signing continuity only after a proven fix. Cobra, Cast, UI/skins, personal data, search engines, playback tracking, native engine and everything outside the active defect boundary stay untouched.

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

## CAST-DISCOVERY-03 — Previously visible video Cast devices missing from selector

- **Status:** DEFERRED / NOT VERIFIED; reported November 15, 2026. Current user screenshot displays only one device in Infinity's Cast to Device dialog, while two parental-household devices are known to the owner and were expected to be listed.
- **Evidence:** User screenshot of the Cast chooser while a movie is playing. This demonstrates current UI device omission, not proof that missing devices are disconnected, Cast-capable right now, or unavailable in another app.
- **Source trace:** Existing Cast Java `InfinityCastSession.updateDevices()` filters Android `MediaRouter.getRoutes()` by `route.isEnabled()`, `!route.isDefault()`, `route.matchesSelector(selector)`, successful `CastDevice.getFromBundle(route.getExtras())`, and `CAPABILITY_VIDEO_OUT`. Selector is built for Google's Default Media Receiver. Discovery uses `CALLBACK_FLAG_REQUEST_DISCOVERY` while dialog is attached and stops on detach. Dialog renders only `cast.devices`.
- **Required read-only diagnosis:** Compare raw current `MediaRouter` route count, filtered device count, and sanitized *rejection reasons*, without recording local IPs or user-defined device labels; check discovery callback lifecycle, Android network permission, active Wi-Fi/VPN/SSID isolation, Cast receiver app compatibility and whether other Cast apps can see those devices under the same connection. Avoid assuming the newer Dolby native remux module affected Java discovery (its reported build left all six DEX files unchanged).
- **Scope:** Make the existing selector reflect all genuinely compatible available receivers; do not add unsupported devices, bypass video capability checks, use YouTube proprietary receivers, add DIAL, or change Cobra.
- **Acceptance:** All known compatible, reachable receivers appear in the Infinity chooser on the same network, with device additions/removals updating dynamically and no loss of existing successful routes. No media playback test is required just to investigate list visibility.

## MOVIE-CONTINUE-04 — Movies Continue Playing saved cards missing; recovery safeguard shown

- **Status:** OPEN; reported November 15, 2026. The user says previously available movie saved entries disappeared from the Movies Continue Playing view and the existing fail-safe/recovery appeared. **Do not label records deleted without inspecting the authoritative save state.**
- **Current source contract:** `resume_hub.py` names `continue-watching.json` as the sole local saved progress/list store. `load_view()` uses checked participant/engine signatures and the shared read; `_entries_projection(data, 'movie', 'items')` filters by media and `resume_visible(data,key)`, which tests `resume_hidden`, then groups identical verified identities. `plugin.py` provides a saved-navigation recovery path and an explicit 'This source is unavailable or has expired … Resume Hub kept your local state' safeguard for unavailable saved source.
- **Unknowns to discriminate:** (1) authoritative `items` data absent/corrupt, (2) display-projection/cache/active-profile mismatch, (3) `resume_hidden` flags and watched/completed behavior, (4) expired provider route showing fallback while progress still exists, (5) incomplete checkpoint/durable write reconciliation given independent ongoing SHUTDOWN-01.
- **Non-destructive investigation:** Inspect original state and checkpoint participant receipts **read-only**, record media-specific raw `items` counts, display projections, hidden flags, profile identifier and view revision, source recovery availability and provenance. Confirm whether movie Resume and Home/Movies Continue disagree for the same original record. Back up only to private secure location before any authorized mutation; never publish account/profile data, record URLs, or contents of the private store. **Do not uninstall, clear data, Start Fresh, rewrite/rebuild saved JSON, migrate, silently unhide or fabricate history**.
- **Expected result:** Previously saved unfinished movies remain visible in Movies Continue Playing when eligible, their exact resume positions preserved. Unavailable source shows safe recovery options without deleting saved metadata or fabricating a replacement source. Completed/explicitly hidden movies remain correctly excluded.
- **Hard lock:** Keep existing playback tracker, Home/UI skin and all unrelated TV/Movies, Search, Cast, shutdown and Cobra untouched until the exact defect boundary is proven. No speculative APK.

## EMPTY-SHELL-05 — Skin works but Python features / add-ons fail to initialize

- **Status:** OPEN — recurrence reported by owner November 15, 2026. Latest precise APK version and process-specific trace **not established** in this report. The report alone does not show a cause.
- **Severity:** High; a functional startup failure can make verification of Search, provider results, saved movies and Health Center misleading.
- **User's earlier defined symptom:** Kodi/Infinity skin and navigation remain responsive, but provider and Python-driven features do not finish loading (previous examples: Umbrella slow/no results, Health Center unavailable). This is **not** the rejected Infinity Search v268 empty-directory workaround and must not be collapsed into a Search-only defect.
- **Comparison pin:** original-signed **2103486** had an owner Fold test with no empty-shell recurrence and normal Close, so it is a **known working comparison**, not authorization to downgrade, install recovery or overwrite current data. The earlier 2103483 first-start success did not prove multi-launch acceptance.
- **Source evidence worth correlating, not a confirmed current root cause:** `repairs/infinity-functional-startup-2103482-20261111/FINDINGS.md` documents that `CScriptInvocationManager`'s startup/shutdown admission flags may refuse new scripts after a failed checkpoint, while `AddonBuiltins.cpp::RunScript()` returns zero even when dispatch is refused; a visible skin does not verify Python readiness. A distinct inherited Core library-staging loop caused 233 historical namespace-denied load attempts; prior evidence **did not** prove it caused the owner's empty shell. The source also records a separate, narrowly reproduced CPython `Py_NewInterpreter` NULL-return GIL cleanup flaw, but there was **no owner-device stack** identifying it as the physical cause.
- **Key comparison with SHUTDOWN-01:** If Exit's essential checkpoint fails and the same process survives, determine whether the interpreter/manager admission gate remains closed or stuck. Conversely establish whether the new symptom occurred after an actual fresh PID. Never claim shutdown caused this recurrence without matching process IDs, session timestamps and native invocation-stage events.
- **Non-destructive diagnosis:** Compare authorized currently installed APK/source, process PID/generation, startup/close admission flags, fresh `RunScript` request ID/result, Python invoker dispatch/lock/GIL/interpreter/bytecode-entry stages, Health Center request, provider callback and safe optional-service writer state with signed 2103486. Use existing logs first. If latest runtime evidence is absent, report the specific missing proof instead of inventing it. Do not publish user credentials, URLs or private dumps.
- **Preserve:** current user profiles, saved movie state and Watchlist, essential durability guards and writer leases, Cobra, Cast, navigation/skin, Trakt, provider logic, other working Infinity components. **No uninstall, clear data, blind restore, force-kill, service disable, Core allowlist, unsafe admission bypass, speculative APK or multiple phone retests.**
- **Acceptance:** Existing UI + Health Center + representative real provider actions work on fresh launch and normal same-profile relaunch; normal verified Close and PID exit; independent focused tests and strict old/new payload comparison. Any release requires separate sign-off after evidence-backed, minimal correction.

## Other workstreams

Casting is separately tracked in existing Cast branches and is **not changed or authorized** by SHUTDOWN-01.
