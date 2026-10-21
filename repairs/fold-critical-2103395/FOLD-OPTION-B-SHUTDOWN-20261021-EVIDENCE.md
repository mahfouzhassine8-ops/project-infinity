# Infinity 2103395 — physical Fold Option B and Essential-First Close findings

**Status: evidence preserved; both features FAILED acceptance. No code change or final LOCK.**

**Baseline:** Signed experimental Infinity 2103395, source commit `f1d32c1bc74c61d4166780eec34f59c349204dc9`, successful run `39555495053`. Preserve 2103395, all matching ZIPs, user data, and every other working behavior. **Cobra must not be touched.**

## A. Option B: first confirmed visual opening, still FAIL

**Evidence:** user-provided `Kodi_Diagnostics_20261021T081050Z-b2eaf1f9.zip`, Option B diagnostic v0.1.0, and physical Compact Home screenshot of **Union County (2026)** popup (`19260.jpg`). The user explicitly reports that long-pressing most other posters in the same top release rail does not open Option B.

Previously reviewed diagnostic trace summary (verify raw records when available):
- A Compact Movies long-press on control `8801`, index `3`, reached native proof/posted, Python received/captured and `popup.shown`; subsequently cancelled.
- Current-session traces counted 15 long-press dispatch events, 14 native poster hits accepted, 11 `native.validate: provider_or_metadata_mismatch` rejection events, and 3 popup openings. These are **trace event counts**, not 15 distinct attempts.
- The user's screenshot independently confirms **Option B actually rendered for Union County**. This proves a path can succeed; it does not prove all items, TV Shows, Normal Mode or full design acceptance.
- The native rejection `provider_or_metadata_mismatch` is the primary investigation lead. Compare an accepted Union County list item with one rejected item in the **same rail**, including provider URI type, Kodi item properties, metadata, selected index/focus and identity proof. Find the exact failing condition. Preserve identity validation and playback routes; do not bypass checks or invent metadata.
- The screenshot confirms the popup is **not the user-approved locked Option B design**. Current modal is tall/narrow, has substantial empty upper space, title/year/metadata/thumbnail/plot are awkwardly distributed, synopsis is cramped, and action labels **Favorite** and **More Info** are visibly truncated.
- The exact approved design remains `repairs/design-approvals/INFINITY-HOME-POSTER-LONGPRESS-OPTION-B-LOCKED.md`: compact centered rounded glass modal, poster on left, real metadata and wrapped synopsis on right, proper balanced spacing, all four complete buttons **Play → Trailer → Favorite → More Info**, original Infinity palette (Light/Dark/True OLED/Night Cinema as applicable), correct responsive safe area. Do not substitute a new mockup or redesign other Home controls.
- **Scope only:** Normal Movies `8101`, Normal TV `8102`, Compact Movies `8801`, Compact TV `8802`. Cinema and Two-Pane are expressly excluded. Native Kodi and Rails context menus remain unchanged elsewhere.
- For diagnosis, reuse the existing `InfinityTouch` trace and v0.1.0 Option B diagnostic. Compare actual successful and rejected events before further implementation; instrument a missing rejection stage only if required. User has physically confirmed one success but **overall Option B remains FAILED**, now after six attempts.

### Required Option B acceptance
1. Both Normal and Compact, Movies and TV Shows, every eligible top featured poster (including representative provider/metadata variants).
2. Correct poster identity, no accidental playback, preserved scroll/focus and original provider route.
3. User-approved Option B appearance **bite-for-bite** with readable full action labels and content, both Fold displays.
4. Test before ZIP updates, after each matching ZIP and after normal Close/reopen; prove active installed source identity, not version string alone.
5. No host-test-only declaration of success; actual Fold verification and user visual approval required.

## B. Essential-First shutdown: 2103395 physical FAIL

**Evidence:** `Infinity-Diagnostics-20261021-035652.zip` (user-supplied physical Fold).

Previously reviewed coordinator receipt (recheck source when available):
- PID `17393`; checkpoint duration ~`25.09 s`; phase `CHECKPOINT_FAILED`.
- `checkpoint_deadline_exceeded; owner proof incomplete`.
- Essential checkpoint **not** confirmed safe; exit authorization **not** consumed; process termination **not** confirmed by receipt. No evidence of data loss, but no proof of full durable save.
- Participant registration identified Command Center `0.3.5.25`, matching the installed-code inventory in this captured session. **Do not repeat the earlier 0.3.5.23-vs-0.3.5.24 mismatch as the current proven cause.**
- Receipt reported 15 incomplete essential checkpoint blockers, largely consequences of the same checkpoint failure rather than 15 independent root causes.
- Python-services owner reported `pending_writer:unidentified:infinity_native_ambient.py`; the ambient module is a **lead, not a proven root cause**.
- Seven services remained pending around six seconds into Close. Separate Trakt Python interpreter retirement continued after deadline; do not confuse service retirement with essential durability.
- Previously recurring The Crew VFS exceptions remain a separate investigation; do not assume they explain this particular timeout.

### Ambient Home linkage to investigate, not presume
The user reports that Off/Subtle/Immersive selection now avoids the previous generic error but does **not visibly alter** Home; Ambient Home previously worked. Compare the last known working version's setting publisher, `infinity_native_ambient.py`, Home XML/render layer and optional-writer lifecycle with 2103395. Determine if a regression disconnected setting from rendering and whether its writer participates in the checkpoint hang. No blanket disable/removal or unverified writer exemption.

### Required shutdown acceptance
1. Trace exact owner proof, writer registration, native write classification, checkpoint barrier and pending-service lifetimes.
2. Determine if ambient module is a protected writer, optional writer with proven isolation, or unrelated observer. Distinguish persistence write vs stale readback vs actual visual effect.
3. Correct proven cause with smallest scoped change. **Do not** increase the deadline, bypass protected writes, mark incomplete owners saved, disable The Crew or force termination to obtain a green receipt.
4. Validate actual safe Close, exit authorization, process death, reopen and protected user data integrity on Fold. Compare a successful baseline under equivalent conditions.
5. Health Center should report setting persisted, engine received mode, renderer applied effect, optional writer lifecycle, and actual shutdown dependency separately; do not claim these are already captured if missing.

## C. Protected scope and remaining issues
- The user reports **all other 2103395 functionality tested so far is satisfactory**, with Option B and shutdown as the two remaining failures. Preserve that successful state; do not restart seven-workstream repairs.
- Preserve original native engine provenance, permanent signing, installed matching ZIPs, Rails, UI Repair, Watched Bridge, Command Center, Health Center, Infinity Trakt, Search, Light/Dark/OLED, PiP, playback and all user databases.
- **Cobra completely untouched.**
- New corrective implementation must produce a signed install-over experimental APK and exact individual ZIPs only after cause-based repairs; no final LOCK until physical Fold acceptance.

**This document is an evidence checkpoint, not a claim of implementation, runtime correction or device pass.**
