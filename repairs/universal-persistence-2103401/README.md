# Infinity universal persistence repair — RC8, not release accepted

Protected baseline: **2103400**. Experimental input: **2103401**. The candidate
retains version code 2103401; identify it by its complete APK hash. Physical Fold
and real installed-provider acceptance remain outstanding. No release, merge or
permanent-resolution claim is made.

## Problem and correction

The physical Fold recorded The Crew calling VFS write with None. Kodi rejects
that argument with TypeError before reaching native write. Infinity's observer
also misclassified this verified conversion rejection as uncertain mutation.
The candidate preserves the original exception and records only verified
no-mutation evidence. It never counts that failed call as a successful save.
The reason the provider supplied None is not established.

The same generic rules apply to current and unknown add-ons. Existing native
invocation/interpreter/worker ownership and admission remain decisive. Profile
settings, history and databases are mandatory; provider identity does not prove
recoverability. Writable VFS opens retain close obligations. Verified clean
buffered handles can retire without admitting new payload. Descriptor inspection
preserves POSIX locks, and missing namespaces require actual observed operations
plus checked surviving-directory durability. SQLite recovery retains original
exceptions while actual pending transactions and writer retirement decide safety.

A separate Android completion-receipt race was reproduced against the original
signed DEX. The shared AtomicFile reader can delete the writer's live stage.
Six calls belonging to Infinity Close now use a dedicated writer with exclusive
staging, checked fsync/rename and exact identity/content readback. The shared
protocol, original writer and installer remain unchanged.

Unknown operations, opaque external writers, unresolved transactions, uncertain
namespace effects and failed durability checks remain visible blockers. No
provider-name exemption, unfamiliar-provider quarantine, service disable, GUI
wait or arbitrary interpreter termination is introduced.

## Exact change boundary

- Five native input files change; the other 9,399 are independently verified.
- The native source delta is [NATIVE-SOURCE.patch](NATIVE-SOURCE.patch).
- The Java source equivalent is [JAVA-SOURCE.patch](JAVA-SOURCE.patch); the new
  helper is [InfinityCheckpointReceipt.java](InfinityCheckpointReceipt.java).
- Input-relative APK differences are libkodi.so, the crash recorder's bounded
  engine-hash field, classes.dex and three signature members. All other members
  remain identical. DEX verification preserves every original class/field except
  six coordinator call targets, and checks the two added helper classes.
- Cobra classes/assets, existing shared infrastructure, providers, playback, PiP,
  UI, Search, Option B and visual assets receive no changes from this repair.

The input already differed from protected 2103400. Those pre-existing differences
and the cumulative baseline delta are recorded separately; they are not hidden
or attributed to this repair.

## Evidence and acceptance boundary

The native implementation passes **310 production-source host cases**, including
five identities: Crew, Umbrella, Seren, POV and an invented future provider.
These cases exercise the generic implementation, not the real providers' code.
Full ARM64 compilation, permanent v1/v2/v3 signing and downloaded source/APK/DEX
preservation checks pass. Android17 ART passes 100 concurrent receipt writes and
six refusal controls; the unchanged original writer fails the same race control.

The final installed **Android17 matrix passes all five modes**. The safe profile
completed three Close/reopen cycles and a fourth startup; independent downloaded
receipts and read-only file/database audits pass. Every Close completed all 16
mandatory owners and verified engine death, VFS/file contents, database integrity,
settings and favorites. Unresolved transaction, opaque-writer and lost-dirty-file
controls retain the engine and withhold authorization.

Earlier failures remain recorded. A first-profile startup crash in an unchanged
native constructor is unexplained and unwaived. Another investigation found the
test fixture put VFS writes in assertions removed by optimized Python. The final
fixture performs every action/check explicitly and captures actual readbacks;
the device reports optimization level 1. Twelve fixture-integrity controls also
pass at optimization 0/1/2. No runtime change was required for that fixture defect.

See [QUALIFICATION.md](QUALIFICATION.md) for exact source/build identities, all
rejected candidates, test limits, member hashes, immutable workflow artifacts and
current Android results. Read-only independent auditors are `audit_artifact.py`,
`audit_receipt.py` and `audit_android.py`.

[FOLD-ACCEPTANCE.md](FOLD-ACCEPTANCE.md) defines the remaining physical gate using
the existing profile and real providers. Resume Hub, watched history, provider
settings, playback and reliable physical Close/reopen must be demonstrated before
final acceptance. `physical_fold_verified` and `final_lock` remain false.
