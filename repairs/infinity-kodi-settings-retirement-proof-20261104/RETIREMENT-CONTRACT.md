# Proposed settings-owner retirement contract — NOT an implementation patch

Status: **ordinary-runtime retirement is blocked by missing evidence inputs.** No production edit is approved by this document. The earlier exact code and all durability safeguards remain authoritative.

## Intended minimum source responsibilities

| Location | Proposed responsibility | Current missing proof |
|---|---|---|
| `Addon.cpp::CheckpointAddonTree` | Store an owner mutation revision, the revision bound to its last confirmed serialization, and whether its serializer/mutation coverage is certified. | Existing `committedGeneration` is only confirmation order and survives later changes. |
| `Addon.cpp::CAddon::SaveSettings` | Start an owner/path-bound save token before serialization; close it only for that snapshot's checked save. Preserve failure tokens/obligations. Establish same-path order for the complete relevant write/confirm interval. | Per-owner locking alone does not order distinct owners of the same path. A revision captured only after serialization misses the demonstrated race. |
| `Addon.cpp::TrackAddonSave` / `ConfirmAddonSave` | Bind pending bytes and confirmation to that exact token/revision. Do not relabel a newer mutation as saved. Preserve final durability work. | Current API receives only owner, path and document. It does not carry snapshot revision or operation identity. |
| Mutation entry points | Advance revision for every change that can affect the eligible serialized owner, including structure and defaults, or mark that owner permanently ineligible for early retirement. | `MarkAddonSettingsManagerDirty` alone has incomplete coverage. Exact additional hooks must be established before selecting native files for a patch. |
| New `Addon.cpp` retirement helper | Retire only a proved superseded, quiescent owner with no unresolved revision/save and with the replacement persistence obligation intact. Keep the weak entry for a still-live owner. Destroy released strong references outside the registry mutex. | Owner/callback lifetime, coverage and ordered commit evidence are not available yet. |

Do not change `CheckpointLoadedAddonSettings`, its conflict/baseline checks, `SaveCheckpointXml`, fsync/rename/metadata checks, coordinator sealing, failure latches or termination authorization merely to make retirement easier. No new XML serialization, worker, polling timer, memory cap or cache purge is proposed.

## Eligibility predicate — specification only

The following uses **proof facts that do not yet exist in the production API**. It must not be copied into native code using guessed values or a reference count as a substitute.

```text
retain unless owner identity and serialized-state coverage are certified
retain unless the exact serialized snapshot has a checked successful save
retain unless current revision equals that snapshot's confirmed revision
retain while any mutation/save/callback obligation is unresolved
retain unless a newer same-path commit is proved under the defined ordering rule
retain unless the replacement pending bytes and final durability obligation remain owned
retain unless weak/external ownership and destruction are safe under the established lock order
otherwise transfer the retired strong reference to destruction outside the registry lock
```

A failed or unsupported proof must keep the owner. A successful memory retirement is **not** a durable-save receipt. It must not set a participant complete, reset a failure, erase a conflict, authorize termination or cause a pending newer write to disappear.

## Required focused tests for a future actual draft

Reuse the completed sixteen-case evidence as baseline. Candidate-specific tests must show that generation-only and generation-invalidation-only counterexamples cannot retire their unresolved owners; the confirmation-order witness must either be prevented by a reviewed ordering mechanism or remain explicitly ineligible.

Add only tests for the final new contract: structural mutation without a normal value-change callback, snapshot mutation before/after capture, overlapping same-path owners, save failure at each relevant completion boundary, live callback ownership, and release/destructor lock ordering. Failed and unknown cases must retain their obligations. Checkpoint I/O failure must retain pending bytes even after rename visibility. Unchanged application tests are not automatically selected.

The current host evidence does not justify a production patch, Android acceptance, an APK build or release. The next smallest action is to establish the missing snapshot revision and writer-order contract for one eligible owner path; no broad settings rewrite is authorized or recommended.
