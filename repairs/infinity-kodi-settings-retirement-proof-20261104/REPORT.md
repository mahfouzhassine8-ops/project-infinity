# Settings-owner retirement safety proof — 2026-11-04

The selected safety tests completed, but **normal-runtime retirement is not yet demonstrated safe using the existing metadata**. No production-ready source patch is proposed. Two deliberately unsafe retirement rules lost an unresolved settings obligation in the host fixture; the preserved checkpoint correctly blocks that obligation when the owner remains retained.

This continues measurement checkpoint `7ea3f0b99f553e2a788ed520a9f0628783f23b6a`. The earlier 24-run measurement and 21 repair tests were preserved, not repeated. Work is isolated on `work/infinity-kodi-settings-retirement-proof-20261104`. No protected source, APK, signing identity, user data or recovery lock changed.

## What was tested

Sixteen preselected host cases ran once. They use exact extracted `Addon.cpp` registry and `CheckpointLoadedAddonSettings` bodies, exact `CXBMCTinyXML::SaveFile`, and unchanged production POSIX checkpoint-file helpers. Synthetic settings/XML peers supply opaque bytes. Ordinary writes, checkpoint fsync/rename and read-back use real temporary host files. File/directory fsync faults are injected only into the host executable.

The coordinator's admission and persisting-thread state are supplied peers. These tests execute the **settings shutdown participant**, not full Kodi shutdown, Android lifecycle, power-loss recovery or physical Fold acceptance. No real profile, setting value, credential or media data was used. Output contains case names and results, not fixture payloads or user data.

All 16 expected outcomes were observed: **13 preservation cases and 3 counterexample witnesses**. This must not be reported as “16 retirement-fix tests passed.” No retirement fix was applied.

| Selected case | Observed result |
|---|---|
| Successful save | Owner and pending obligation remain until a successful settings checkpoint; file and directory sync occur before release. |
| Two successful owners for one path | Both remain retained before checkpoint; the latest pending payload is preserved and the completed helper releases the owners. |
| Failed ordinary save | No confirmed generation is created; dirty owner and pending bytes survive; the checkpoint helper can persist them later. |
| Pending operation | Denied admission leaves owner, pending bytes and file unchanged. A separately admitted helper call persists the pending payload. |
| Mutation after confirmed save | Existing generation does not change. A later conflicting owner causes checkpoint failure; neither unresolved owner is silently discarded. |
| Mutation after snapshot, before confirmation | Confirmation can record the older snapshot while the tree has newer values. The retained tree makes the later conflict visible. |
| Repeated mutations | Checkpoint writes the latest mutation; a live externally owned tree can mutate and become dirty again after a successful helper checkpoint. |
| Unknown loaded baseline | Checkpoint fails and retains the owner. |
| Serialization failure | Checkpoint fails and retains the owner and pending save. |
| Derived serializer changes | A registered serializer can produce changes outside the base setting bytes; the unchanged checkpoint discovers and persists them. |
| File fsync failure | Checkpoint fails, original file remains and the owner/pending record survive; explicit helper retry succeeds. |
| Directory fsync failure after rename | New bytes can be visible while durability is unacknowledged; checkpoint fails and retains the obligation. Explicit helper retry succeeds. |
| Wrong phase or denied admission | No settings checkpoint succeeds and no obligation is released. |
| Reordered confirmations | Confirmation generations can disagree with file-write order; a later checkpoint writes the latest confirmation's pending bytes. |
| Generation + apparent sole ownership retirement | **Unsafe:** dropping the older dirty owner hides an unsaved conflict and lets the helper report success. |
| Mutation-time generation invalidation alone | **Unsafe:** a stale later confirmation overwrites the invalidation, allowing the same lost-obligation outcome. |

Retries in the two I/O fault cases test this helper's retained obligations. They do not clear the production coordinator's failure latch, authorize process termination or fabricate a complete shutdown receipt.

## Ownership and persistence findings

`CheckpointAddonTree` has a weak settings reference, a strong `dirtyOwner`, a raw manager identity, a loaded-byte baseline, a committed generation and a serializer callback. A normal add-on object also owns its settings through `m_settings`. `g_checkpointAddonSaves` retains a strong owner plus bytes for the pending save at each path. The checkpoint takes additional strong snapshot references while it examines owners.

`TrackCreatedAddonTree` prunes expired clean entries. `MarkAddonSettingsManagerDirty` pins the owner. `ConfirmAddonSave` rebases only the matching owner and increments a **confirmation counter**; it does not record the revision serialized or invalidate that counter on a later mutation. Thus neither a nonzero generation, an older generation, nor an apparent `use_count()==1` proves that the tree contains no unresolved changes.

An ordinary `doc.SaveFile` success is not the final persistence receipt. Outside checkpoint persistence, `CXBMCTinyXML::SaveFile` follows the ordinary open/write/flush path. The settings participant must still verify and persist pending bytes with the protected file and directory durability checks. Memory retirement and durability acknowledgement must remain separate decisions.

The source coordinator closes ordinary mutation admission only after required work drains and `activeWrites == 0`, then enters `PERSISTING`. Completion of the add-on settings participant additionally requires the helper's true result and no new persistence failure. Those source gates remain unchanged. The host phase peer does not independently validate the entire coordinator or Android's shutdown sequence.

## Counterexamples that block the simple repair

**A newer owner does not cancel an older unsaved change.** Owner A saves, then changes again without saving. Owner B subsequently saves to the same path. A still has an older nonzero generation and, after external references drop, only its dirty pin. The existing checkpoint sees A's differing values and B's pending values and reports a conflict. The test-only generation/reference-count retirement rule destroys A; the same checkpoint then reports success. The user's unresolved setting has disappeared from the obligation inventory.

**Resetting the generation on mutation is insufficient.** A save serializes snapshot R. A mutation occurs before that save's confirmation. Clearing the generation at mutation time does not help: the later confirmation reinstates a nonzero generation for R. Retirement needs a revision bound to the actual serialized snapshot, not a flag overwritten by any successful completion.

**Confirmation order is not necessarily file-write order.** The selected deterministic schedule was A writes, B writes, B confirms, A confirms. A then has the higher generation although the file contains B. The checkpoint later uses A's pending bytes. `CAddon::SaveSettings` holds a per-add-on settings mutex; distinct owners for the same path do not share that mutex. This is a source-permitted ordering hazard, not evidence that the schedule occurred on the Fold. It also does not establish which overlapping operation the product intends to win. That ordering contract must be explicit before a generation can certify supersession.

## Mutation coverage is not yet sufficient for a revision-only patch

The ordinary value-change callback is not a complete certificate for all serialized state. Source inspection shows on-the-fly setting insertion and definitions/default handling separate from `OnSettingChanged`. Derived `CSkinInfo::SettingsToXML` serializes its own boolean/string collections. A counter added only to `MarkAddonSettingsManagerDirty` would therefore need an explicit coverage boundary; it cannot be presumed to cover every settings owner.

Settings and manager callbacks also have lifetimes beyond the simple registry count. A reference-count sample is not a writer fence or a guarantee against concurrent weak-reference acquisition. Any future retirement must preserve weak registration for still-live owners, preserve re-pinning on mutation, and release last strong references outside the registry mutex so destruction/callbacks do not create a new lock dependency. These are proof requirements, not changes implemented here.

## Proven safe boundary and proposed correction boundary

The **existing sealed settings checkpoint** is the demonstrated release boundary under its admission/quiescence preconditions: every required owner can be examined, unknown baselines and conflicts block, every required file/directory operation succeeds, and no new persistence error is ignored. Fault cases show that a merely visible rename or ordinary save is insufficient. That existing release behavior is preserved.

Earlier, runtime retirement of a superseded owner would require all of the following evidence simultaneously:

1. Exact owner/profile/instance identity and known serialization coverage.
2. A mutation revision bound to the saved snapshot, unchanged afterward, including structural and derived state within the eligible owner's coverage.
3. No pending/failed operation or in-flight callback that can still alter or save the old owner.
4. A newer, checked successful same-path commit under an explicit ordering contract, with no ambiguous generation or completion order.
5. Retained immutable pending bytes and all metadata needed for final checkpoint durability; no receipt is invented by retirement.
6. No lost external ownership or future dirty notification, and safe destruction outside registry/settings locks.

The present ledger cannot establish all six. The exact proposed production code change at this checkpoint is therefore **none**: no `.patch` is marked safe to apply. Providing a reference-clearing patch now would violate the failed safety proof.

[RETIREMENT-CONTRACT.md](RETIREMENT-CONTRACT.md) specifies the smallest proposed implementation boundary and exact intended responsibilities for a later, independently reviewed patch: snapshot revision/save tokens in `Addon.cpp`, complete mutation-coverage certification, same-path save ordering, and a narrowly gated retirement helper. Unknown/derived/uncovered owners remain retained. The checkpoint validator, file durability helpers and shutdown authorizer remain untouched. This is repair preparation, not a claim that those inputs or a production implementation already exist.

## Remaining verification before implementation or release

- Prove a complete mutation/lifetime contract for the specifically eligible owner class; unresolved routes must stay ineligible.
- Demonstrate snapshot revision and same-path ordering with interleavings, failed/superseded saves and structural/derived changes. A successful model alone cannot certify missing native hooks.
- Review lock ordering and last-owner destruction against actual settings callbacks; avoid holding the registry mutex across serialization, I/O or destruction.
- Once a safe draft exists under separate implementation authority, run these same selected cases against exact candidate bodies and verify the counterexample rules are rejected, without weakening checkpoint errors.
- Then obtain authorized Android execution for actual add-on save/return and shutdown/reopen, with file/directory failure handling and physical Fold acceptance reported separately. No compatible device was attached for this task.

No memory-stability improvement or historical Scudo root cause is claimed. The earlier host retention measurement remains valid, but safe retirement requires more evidence than accumulation alone.

## Preservation and saved evidence

All 9,411 restored native source files still match the preserved source map. The primary branch and existing untracked work are unchanged. Measurement checkpoint `7ea3f0b9` remains unchanged. Preview, Cobra, all APKs and recovery locks were untouched. There was one host-fixture compile, no Kodi engine/APK rebuild, no sign/install/release/lock and no broader shutdown suite.

The selected plan, source hashes, all case results, compilation record and preservation checks are saved under `evidence/`. One harmless unused-function warning comes from extracting the unchanged `TrackAddonDeletion` helper; that unselected helper was not invoked. The previous measurement was not rerun.
