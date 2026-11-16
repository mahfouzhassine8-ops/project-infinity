# Infinity 2103502 — owner-authorized two-crash stability correction in active six-repair pass

**Owner authorization:** November 16, 2026. The owner expressly requests that **both** new abnormal exits be investigated **and fixed** in the work Codex is currently doing, rather than left as read-only diagnostics. This is a **narrow, incident-specific scope amendment to the existing six-repair pass, not a general seventh repair or permission to modify unrelated behavior**.

**Read-only evidence:** [CRASH-TRIAGE-20261116-045337.md](CRASH-TRIAGE-20261116-045337.md) from the private `Infinity-Diagnostics-20261116-045337.zip`. Never commit or publish raw device logs, watch history, private provider URLs, or original tombstones.

**Protected baseline:** Exact original-signed `2103502`, APK SHA-256 `f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28`; Cobra `2103445` and every unrelated feature, data file, action, renderer, Cast, Silent Mode and VideoOSD control are strictly unchanged.

## Two independently tracked crash cases — evidence, not assumed cause

**A. Stop-adjacent crash, ~04:40:41 EST, PID17519.**
- Owner recalls pressing **Stop** during movie playback, then an abnormal exit; the complete action sequence is uncertain.
- Android history records native abort, status 6. The matched protobuf tombstone contains `Pure virtual function called!`, `__cxa_pure_virtual`, `jni::CJNIMainActivity::_infinityGetState`, `Main.infinityPublishWindowSnapshot`, `InfinityCoreBridge.publishWindow`, `InfinityCoreBridge.attach`, `Main.onCreate`.
- **Do not blame the Stop handler without evidence.** Trace the real native object lifetime and dispatch during Android activity creation/re-entry and any associated playback-stop transition. Discriminate an object destroyed during Stop, stale/half-initialized interface, asynchronous attach versus a separate startup failure.

**B. Mark-Watched-adjacent crash, ~04:53:13 EST, PID17845.**
- Owner reports using **Mark Watched** on a movie immediately before the exit.
- Native snapshot `crash/native-crash-last.txt` shows signal 11 / SIGSEGV, TID22465, exit status139; there is **no matching full tombstone or fault-stack capture** for this process in the supplied ZIP.
- Trace native watched-state/context command invocation, metadata and player-lifecycle callbacks, protection/checkpoint state, user selection and any recently retired UI owner. **Do not claim a watched-state write succeeded or was lost**. Read-only check any supported receipt before contemplating correction.
- The snapshot's `native_engine_sha256=704834f42e49a2eea0a36ad41b5f79345f5e4108dcd339213899ea3c6ff045a0` differs from signed502's authenticated native engine `ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7`; first verify trace producer identity and exact mapped binary/build IDs before symbolication or assigning a 502 code defect.

## Mandatory work order for Codex + Astra

1. **Preserve evidence and 502:** Snapshot existing crash triage, exact source and producer provenance. No reset, cache clear, data migration, fake tests, unbounded reproduction, provider rewrites, or previous-core rebase.
2. **Differentiate failure owners:** Correlate PID/UTC/local timestamp, tombstone native module symbol offsets and Java/JNI lifecycle for incident A; for B, acknowledge absent full stack and seek bounded existing/private evidence or a single justified targeted repro. Do not infer common cause from the proximity of Stop/Mark Watched.
3. **Fix only a proven defect:** If a narrowly scoped lifetime, virtual-dispatch, registration/retirement, watched-action or native observer flaw is demonstrated, implement the smallest fix to its actual first-party owner. Astra independently reviews causality and preservation before and after patch. Preserve existing Stop/Mark Watched semantics and user tracking.
4. **Acceptance tests:** Focused native lifecycle regression including activity attach/re-entry and playback Stop; focused watched-action regression including mark/unmark and correct one-time persistence; no crash/hang/abnormal exit; verified profile, native gate, and data integrity; critical Android class, ABI, existing Video Lock and Cast functionality protected. Successful host checks are not physical Fold acceptance.
5. **Integration:** Add passing, reviewed crash corrections to the SAME future `2103502`-derived **six-repair combined original-signed QA APK** and matching forward recovery. **No partial diagnostic installer or claim of completion before all scoped release gates.** Physical owner test only after integrated candidate is ready.

## Authorization boundary (important)

This explicit owner request authorizes **these two concrete crash investigations and their minimal proven corrections**, even if a necessary first-party lifecycle owner is not otherwise covered by item 1, 3 or 4. It **does not** reopen whole-app Stop behavior, watched data semantics, Kodi/native engine redesign or unrelated code. A third defect, broader redesign or additional file outside a demonstrably necessary dependency requires fresh owner approval.

**Status:** `OWNER_AUTHORIZED_AUDIT_AND_REPAIR`; both root causes unproven; production correction **NOT YET IMPLEMENTED**; existing work continues in parallel. Link back to the reviewed triage. Never represent this markdown checkpoint as a fixed APK.
