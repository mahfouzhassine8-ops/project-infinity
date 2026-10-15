# Infinity 2103369 — cancelled-script receipt candidate

Separate, unlocked candidate based on locked 2103368 commit `18a2c4225661608235e44c57769426b6e08cbe47`. It does not replace or modify the locked 2103368 or protected 2103365 artifacts. Standalone Health Center 2.5.20 remains a separate installed update.

## Evidence and repaired behavior

`Infinity-Diagnostics-20261011-200525.zip`, SHA-256 `a1763f04400fa49d6f4f4a98bd8cf11ce48ad7ae426a54dcf4e2748f6b64ba15`, reports PID 27748/session `8d0b1a8d-b1f5-4991-9c3e-b6da0ae672ce`, `CHECKPOINT_FAILED` after 25166 ms. The sole pending script is invocation 54, `plugin.program.iagl:addon.py`, with `foreign_invoker_finished_without_persistence_receipt`. Native trace has cancellation and interpreter finalization but no `python.bytecode_returned`. Four of 17 owners confirmed before the failure. This is incomplete shutdown proof, not evidence of 13 independent save failures or data loss.

The 2103368 source admits a persistence obligation before script launch, but attaches the persistence observer only after the cancellation check and successful script-file open. Cancellation before bytecode can therefore end the interpreter without an observer or checked retirement receipt. The regression reproduces that gap using the actual production observer and ledger under real CPython.

2103369 moves the same observer attachment before the cancellation/file-open gate, after interpreter initialization. Ordinary execution, observer finalization, durable boundary verification and actual interpreter retirement retain their existing authority. It introduces no cancellation waiver, add-on whitelist, forced termination, shortened deadline or assumed success. Pending transactions, opaque native writers and observer failures remain blocked.

The only native overlay changes are `PythonInvoker.cpp` and the candidate constant in `InfinityShutdownTrace.h`. The only Android overlay change is the matching trace constant in `InfinityHealthExport.java.in`. Ledger, observer implementation, coordinator, all 17 owners, Command Center, Resume Hub, skin and code assets remain unchanged. CI compares every Android instruction against 2103368, allowing only exporter/build identity constants, and compares the final payload and manifest against the exact signed 2103368 APK.

## Validation boundaries

The seven targeted host cases cover cancellation before bytecode, missing script file, ordinary read-only work, verified filesystem write, open SQLite transaction, opaque writer and observer failure. Inherited observer, writer lifetime, source, full native/Android compilation, signer, packaging and immediate-parent preservation gates must pass before delivery. A host test does not establish Android timing or physical acceptance.

Fold acceptance must reproduce opening/backing out of IAGL followed by normal Close, including rapid cancellation. Confirm all 17 owners, a fresh successful checkpoint, the checked script retirement receipt, process termination only after authorization, and successful relaunch with settings/watched history intact. Repeat ordinary playback/stop/Close and intentionally interrupted operations. Any remaining unverified writer must still report a failed checkpoint with original evidence preserved. Do not lock this candidate before physical acceptance.
