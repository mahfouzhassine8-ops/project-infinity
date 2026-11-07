# Search consistency release gate — native owner handoff (2026-11-07)

**Status:** REQUIRED CONTRACT — NOT IMPLEMENTED. This is a review handoff, not an approved memory/synchronization patch, host PASS, APK, or installer. Do not ship an unfinished Search variant.

## Frozen identities
- Protected correction checkpoint: `86d5b5e2b65acb878632d407c3a3a07dd1af3b6d` — do not modify or reset.
- Unified Infinity Search candidate branch: `work/infinity-search-unified-native-candidate-20261107` (host run 42363351875, 9/9 passed before this document).
- Separate native keyboard candidate: `92bb6ecbb21c14f62f40555ba2aaef198e3847e2` — unchanged by this handoff.
- Installed APK462 / skin 1.0.5.268 / Command Center 0.3.5.61 remain untouched.

## Why the common validator still blocks release
- The owner-provided physical trace documented 31 successful WatchNixtoons2 rows and 2 successful The Crew rows being discarded after a provider settings-file metadata change. This proves original provider capability, *not* the identity or semantics of every writer.
- Controlled settings matrix run [42362290378](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42362290378) reproduces a representative false rejection: a harmless synthetic bookkeeping write changed the settings file and rejected 31 synthetic rows. It also confirms the current validator rejects a meaningful change and an observed ABA example.
- Actual source: `repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py`, notably `_query_file_stamp`, `_query_signature`, `_provider_result`, `_leased_directory`. Explicit single-provider Search now reaches the same common collector, so the false rejection can affect both modes.

## Safety boundary
A change in a settings file's dev/inode/size/mtime/ctime proves mutation, not meaning. Comparing only final XML cannot detect a meaningful intermediate change restored to original bytes (ABA). Kodi Python `OnSettingsChanged` callbacks do NOT cover arbitrary direct filesystem writers and are not a complete global request-scoped journal.

Therefore a safe non-fail-closed exception requires one of:
1. A verified immutable *effective search-configuration snapshot* used by every relevant provider settings read for that native request, covering native addon settings APIs and direct filesystem reads, with unchanged source/config/dependency authorization; **or**
2. A complete, ordered, request-bound writer/semantic-change provenance contract that **proves** every relevant writer (including external direct-file paths) is included, distinguishes harmless keys, and exposes loss/gaps rather than guessing.

Both are hypotheses to investigate, not preapproved implementations. If neither can be proven complete in the current Kodi/Android environment, remain fail closed and report the settings-safe-acceptance requirement as unresolved. Do not assume a special-case named provider's searchHistory is sufficient or generalizable.

## Mandatory acceptance cases
- No settings mutation: accept original native results and destinations.
- Proven harmless bookkeeping update: accept original legitimate rows, with no second provider RPC or retry.
- Meaningful config modification: reject stale rows.
- A → B → A meaningful edit, even if final bytes match: reject.
- Unobserved external writer / missed event / journal overflow or gap / source mismatch / profile switch: reject, never mark fully observed.
- Disabled provider, changed route/source/dependencies, cancellation, native RPC lease conflict, missing profile, expired cache and shutdown transition: preserve current fail-closed semantics.
- Search All and individually selected provider both use the one Infinity result publisher, but each provider executes its own verified native search.
- One provider's incompatible update or failure cannot suppress unrelated providers.

## Separate native and integration owners
- GPT-6.1's keyboard candidate reproduced host ASan use-after-free and compiled the ARM64 keyboard translation unit but **does not** resolve the graphics origin-stack race. The graphics query/response contract must also account for checkpoint failure/cancellation; do not patch by borrowing a stack pointer across `SendGUIMessage` or assume `Pump` always drains.
- Search integration owner keeps the current strict validator until a reliable native consistency primitive exists, then tests it on an isolated branch.
- One coordinated protected release only after complete engine/link, native crash fixes, Search consistency, source/signer/recovery verification, and one Fold acceptance session. No partial installer, source-only ZIP, or repeated phone crash diagnostics.

**Required next native deliverable:** an evidence-backed feasibility verdict and, if feasible, exact API/ownership contract and focused tests covering direct-file writes and ABA; otherwise state the impossibility clearly. Do not present a generic settings-event callback as complete provenance.
