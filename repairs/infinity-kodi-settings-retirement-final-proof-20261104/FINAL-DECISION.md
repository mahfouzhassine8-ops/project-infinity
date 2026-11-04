# Final settings-retirement proof — BLOCKED

**Decision: retain the existing checkpoint behavior. Do not enable early native-owner retirement or apply a production patch.**

This bounded pass continued from `8c54e2cf3bbe98ec4512721802d1011a73c82eb2`. It implemented an isolated revision/save-token protocol and completed the 20 preselected cases: 19 synthetic contract cases plus one source-bound native mutation-coverage witness. The contract cases passed. The native witness demonstrated a coverage gap, so the production safety gate did not pass. No further expansion or test loop is underway.

No production source, native engine, APK, user data, signing identity or recovery lock changed. Preview 2103451, Cobra and the existing Kodi checkpoint protections remain untouched.

## What the isolated implementation establishes

`contract.hpp` implements a host-only protocol with real C++ mutexes, shared/weak ownership and destructor callbacks. Its payloads and write/receipt outcomes are synthetic. It is not integrated with Kodi and is not a production patch.

| Obligation | Isolated implementation and observed result | Native status |
|---|---|---|
| Snapshot/save identity | Tokens bind owner, operation, snapshot revision and captured payload. Foreign or replayed confirmations are rejected. | Native `ConfirmAddonSave` API remains unchanged. |
| Later changes | Mutations advance revision before changing the encapsulated payload. Confirmation rejects a changed revision and preserves the owner. | Complete native mutation coverage is not established; the source witness fails this prerequisite. |
| Same-path ordering | A per-path lease covers capture, simulated write and confirmation. A second thread cannot obtain that path's lease while the first is active. Separate paths remain independent. | Native per-add-on locks remain unchanged; no per-path lease was installed. |
| Failed/pending work | Failed, abandoned and active tokens retain owners. Conflicting revisions, unknown coverage, missing replacement data and durability failures block retirement. | Existing failure/checkpoint behavior is retained; prior source-bound persistence evidence is reused. |
| Guarded retirement | Only a fully covered, unchanged confirmed owner superseded by a newer confirmed same-path payload can lose its registry pin. Pending durability data remain owned and unacknowledged. | No real owner was certified or retired by this prototype. |
| Destruction and callbacks | Retired strong references are moved out of the registry lock before destruction. A destructor re-entered the registry successfully. A weak-reference acquisition at detachment preserved the weak entry and a later mutation re-pinned the owner. | Native callback and lock integration is not certified by this host model. |

The prototype's `CertifiedSynthetic` coverage state is deliberately restricted to the encapsulated fixture. It must not be assigned to real add-on owners by assumption. Unknown coverage blocks retirement. `TryBegin` reports an unavailable lease as deferral; it does not implement or authorize a native retry, dropped request or UI wait policy.

The model preserves a replacement payload with `requiresDurability=true` after successful old-owner retirement. It does not claim that an ordinary save is durable or complete a checkpoint participant. If the replacement data are missing, or a durability failure is unresolved, it refuses retirement. These are protocol outcomes, not new disk-fsync measurements; the previous 16-case source-bound checkpoint evidence remains unchanged.

## Concrete native coverage blocker

The witness compiles unchanged bodies from the protected source for:

- `CAddon::UpdateSetting`
- `CAddonSettings::AddSetting(string)`
- `AddSettingWithoutDefinition` and its initialization helpers
- `CSettingsManager::AddSetting` for a section/category/group
- `CSettingString::SetDefault`, `SetValue` and inline `FromString`

The surrounding peers supply an already initialized/loaded manager, simple valid string settings, containers, and an observable value-change callback. No real settings or providers are read.

Observed sequence:

1. Updating an undefined key inserts one populated setting; value-change notifications remain **0**.
2. Changing that existing key produces **1** notification, confirming the callback observation works.
3. Updating another undefined key inserts a second populated setting; notifications remain **1**, with a new-key notification delta of **0**.

The source mechanism is specific: the creation helper calls `SetDefault(value)`, which initializes the new setting's current value. The manager registers the setting without invoking `OnSettingChanged`. `CAddon::UpdateSetting` then calls `FromString(value)`, which reaches `SetValue`; its equal-value early return produces no change notification. The new setting is present in the group returned to the current XML serializer.

Consequently, a revision counter incremented only from the normal dirty/value-change callback can remain unchanged while serialized state changes. This is a source-bound, loaded-owner route, not merely an invented model operation. The test establishes the route with simple peers; it does not identify a historical add-on, reproduce the Fold crash, or measure its occurrence frequency.

The isolated guard correctly tracks value, default, insertion and removal operations when callers use its encapsulated API. That does not prove native callers use the same guard. The native witness is the decisive distinction. A fully integrated revision design would need to cover this route and other structural/default/derived-state changes, and prove the real mutation/snapshot locking boundary. Those guarantees were not supplied by the existing `Addon.cpp` callback contract.

## Result matrix

| Selected group | Cases | Outcome |
|---|---:|---|
| Snapshot binding, stale/duplicate/foreign confirmation | 5 | Expected rejection/preservation behavior observed in the prototype |
| Same-path exclusion and separate-path independence | 2 | Expected ordering observed; one deterministic two-thread contention check |
| Failed, pending, conflicting, durability, missing-data and unknown-coverage obligations | 6 | Unsafe retirement refused in the prototype |
| Guarded mutation categories | 1 | Value/default/insertion/removal each invalidated an earlier snapshot in the encapsulated payload |
| Destruction, external ownership and weak reacquisition | 3 | Outside-lock destruction and ownership preservation observed |
| Abandonment and revision overflow | 2 | Obligations retained; no wrapped revision accepted for retirement |
| Native undefined-setting insertion | 1 | **Coverage gap demonstrated; production gate BLOCKED** |

All 20 cases ran once after preparation. The first source-preparation attempt located `FromString` in the implementation file; its actual inline definition in `Setting.h` was then bound before either host compile or any test. Both host binaries compiled without diagnostics. No case, old measurement, old safety suite or Android run was repeated.

These finite cases support the stated protocol invariants under the fixture's complete mutation and ownership assumptions. They are not an exhaustive proof over all native callbacks, an Android runtime result or physical Fold acceptance.

## Production correction and stop decision

**Exact production correction delivered: none.** There is no safe-to-apply `.patch` in this checkpoint. The isolated source is evidence for the protocol only and must not be compiled into the application.

The demonstrated native coverage gap prevents proving that an apparently confirmed revision has no newer unresolved settings. Enabling early retirement before closing it could repeat the lost-obligation counterexamples from `8c54e2cf`. The per-path lease and destructor checks also lack a reviewed native integration that preserves existing save/callback behavior.

This is a source-contract blocker, not merely a missing Android device. Passing Android scenarios would not justify ignoring a reachable untracked mutation. A future production proposal would first need complete native mutation coverage and lock/order integration for its explicitly eligible owner class, with all other owners remaining retained. That would be a separate scoped decision; this final pass does not continue into a shared-settings rewrite, additional instrumentation, new workers, extra serialization or another build.

The existing safe checkpoint behavior is retained: unknown, failed and conflicting obligations remain covered, verified persistence requirements are unchanged, and no owner is released by the isolated prototype in the real application.

## Preservation and evidence

- All **9,411** restored native source files still match the preserved source map.
- The primary branch/worktree and its pre-existing untracked files are unchanged.
- Checkpoints `7ea3f0b9` and `8c54e2cf` remain unchanged and clean.
- Two host fixture binaries were compiled. No Kodi engine or APK was built, signed, installed, released or locked.
- No settings values, credentials, user databases, media or private diagnostics were accessed or logged.
- No full shutdown, playback, Android or physical-device test was performed under this pass. Prior evidence was preserved.

`SELECTED-TESTS.json` records the bounds and decision gate before execution. `evidence/RESULTS.json` contains every result. `evidence/SOURCE-BINDING.json` identifies the exact native bodies and peers. `evidence/PRESERVATION.json` records the preservation check. The report and isolated source are saved on the separate final-proof branch.
