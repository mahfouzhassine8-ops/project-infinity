# Infinity — File-writing integrity / independent Essential-First Close

**Status:** experimental source correction; source-level/native host regression passed, full signed 2103384 and Fold approval PENDING. Original locked TEST4, installed TEST3/2103383 and user data unchanged.

## Ground truth: actual physical Galaxy Fold
- Diagnostic: `Infinity-Diagnostics-20261017-212726.zip`, close approximately 2.2s.
- `CHECKPOINT_FAILED`; `checkpoint_saved=false`; no termination authorization.
- 3 `vfs_write_exception` failures, writer `plugin.video.thecrew:service.py`, native writer id 8, with no failed-path provenance. `vfs_mkdir_exception` was independently reported as `protected_write_rejected_before_mutation` (advisory).
- Prior TMDb/The Crew `sqlite_write_failed` errors remain advisory by original contract but uncommitted SQLite transactions and protected writes are still fatal.
- Original `python_services` is NOT a required essential owner; opaque failed-write classification in the shared ledger made `native_admission` fail. The Crew is not made essential, deleted, downgraded, or marked successfully saved.

## Correctness contract
1. Preserve the existing **single Essential-First shutdown coordinator**. No second Android app, no second player, no force-stop path, and no new shutdown owner.
2. Preserve 2103383's installer-stage missing-parent durability correction, Fold OnJobComplete deadlock fix, watched bridge, touch fixes, player, PiP, skin, Rails, and user data.
3. A VFS write error is eligible for optional treatment only if the **actual same-writer/same-thread live native `vfs.write` lease** was bound to that canonical destination before reporting the exception. A Python-supplied string or provider name alone can never confer optionality.
4. At the final checkpoint, re-evaluate the *exact* failed destination **and all other paths inventoried for that writer** against real trusted profile roots and aliases. All must be optional. Any protected settings, Command Center, databases, other essential user state, symlink, forged path, or unknown target retains a fatal blocker.
5. Active protected operations, pending SQLite transactions, unflushed buffers, unobserved writers and unknown native side effects retain their own independent blockers even when a separate optional VFS write failed.
6. The original native `Fail` remains sticky, with **no global `vfs_write_exception` advisory waiver**. Optionality is proved in `EssentialWritesLocked` at checkpoint time. Unverified cases retain existing failure behavior. No raw path is serialized by this new receipt.
7. Physical Fold Close+reopen and retained data must verify any future candidate. A passing host/native/packager check is not a physical shutdown pass.

## Audited file-writing families and treatment

| Operation family | Current contract |
|---|---|
| Kodi VFS File.write returns failure or raises | Candidate: exact native lease + all writer paths optional required for optional error handling; otherwise fatal |
| Kodi VFS File.close/flush fails | Retain fatal/dirty state unless proven already handled by the prior bounded private buffer contract |
| Kodi VFS open/rename/copy/delete/mkdir/mkdirs/rmdir errors | Existing fail-closed checks retained; no path-by-name waivers |
| OS open/rename/replace/delete/truncate and raw write/writev/pwrite/ftruncate/etc. | Existing native observer/write-admission/real descriptor checks retained |
| Python buffered flush/close and layered buffers | Bounded inventoried private-only handling retained; pending essential buffers still block |
| SQLite writes/commit/ATTACH/VFS and native DBs | Existing independent DB durability and transaction barriers retained |
| Native child or opaque native-extension output | Existing identity, wait and fail-closed barriers retained |
| Rejected writes before mutation due to closed admission | Existing advisory diagnostic retained; existing dirty data still requires its own durable proof |

## Regression coverage

Full actual-header compilation plus scenarios: optional Crew-style write, unscoped error, forged native destination, wrong VFS operation, essential Command Center file, provider `settings.xml`, pending protected transaction, unflushed protected buffer, active protected operation, alias to essential state, unrelated VFS close error, and writer touching both optional and essential destinations. Any failure makes source CI RED.

Source: `repairs/full-system-20261017/write_error_scope_patch.py`, native test `test_native_scoped_vfs_error.cpp`, runner `test_write_error_scope.py`, native producer `write_error_native_ci.py`.

This fixes a specific demonstrated classification gap **without promising universal correctness for every third-party addon**. Future undocumented errors remain fail-closed until provenance supports narrower handling. The independent physical 25-second owner/startup checkpoint remains an open issue and may still require further work.
