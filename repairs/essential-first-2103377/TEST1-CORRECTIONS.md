# TEST1 shutdown correction evidence

The actual TEST1 export reports CHECKPOINT_FAILED at `native_databases`, no
consumed termination authorization and no confirmed process death. First-party
callbacks and required jobs finished. Later settings, profiles and favourites
did not. Twenty-five blocking script warnings plus one native path warning
made the early database barrier wait until the existing deadline.

## Save admission and final authorization

`InfinityDatabaseBarrier::ReadLocked` now counts live protected operations,
dirty buffers and transactions for admission to essential save stages. It no
longer confuses historical coverage warnings with live database transactions.
Those warnings remain mandatory blockers in `SealEssentialWrites` and final
native authorization. No warning is fabricated as a successful save.

The compiled production coordinator regression verifies that settings,
profiles and favourites complete despite a historical warning, then final
authorization fails with that warning. Separate cases verify that active
protected writes and transactions still prevent unsafe save admission.

## Corrected production paths

- SQLite VFS observes actual main, ATTACH, URI, journal and WAL destinations,
  including transactions opened before Close. Tests commit protected
  transactions before sealing and reject writes afterward. Parent processes
  reopen the databases after actual host child death and check rows/integrity.
- CPython native entry hooks cover cached functions, existing file objects,
  raw/buffered/text writes, filesystem namespace changes and native Pillow
  encoder writes. Native descriptors cannot be spoofed through `fileno()`.
  Descriptor replacement and rename races keep active operations protected.
- The private SQLite inventory cursor disables only its own row factory;
  provider connection and result behaviour remain unchanged. A custom row
  factory reproduces the old inventory failure and now passes. The TEST1
  export does not contain IAGL's underlying exception, so device resolution
  remains unconfirmed.
- Successfully closing an observed buffer retires its original tracked
  identity without looking up the already-closed descriptor. This was
  reproduced by the unchanged Command Center durable save callback.
- Native pre-mutation admission rejections use a dedicated PermissionError
  subtype. They propagate to callers and remain diagnostic. Genuine failed
  saves, unknown capabilities, existing dirty buffers and transactions still
  block authorization. No failed essential participant receipt is waived.
- Invalid native POSIX descriptors return the original error before entering
  path verification. Valid writes and directory mutations hold real leases.
- The locked ambient image is verified against the existing audited binary
  hash `a876a76abe4faea63046953579899b0b7a67572722c2ed92331e41fcd1475684`.
  Thirteen exact entry points used by the locked script are bounded memory
  operations, mailbox reads or anonymous memfd creation. No image, ambient
  source, script, playback or skin behaviour is changed. Changed bytes,
  wrong locations, symlinks and unlisted symbols fail the contract test.

The ambient audit reuses the locked source archive
`repairs/infinity-ambient-surface-2103284/payload.*.b64` (archive SHA-256
`df30f27c3d8be9857a2e9a7f92471eac83cc7cf022a05b394211c1652eee42ad`).
The reviewed source hashes are `ambient.cpp`
`6146607a295ec451e5fab1c666f5b60b4530f83e11e59cea16bf859558f050d6`
and `surface_frames.cpp`
`b58e4ef088c729c9eb54da0f913aab51061b84d8d28d0c48bc7b1fcae22aa752`.
The host verifies the exact ARM64 image's contract; it does not execute that
ARM64 image or claim on-device ambient regression acceptance.

## Verification boundary

Evidence in `evidence/runtime/` covers 34 production CPython cases, 8 SQLite
cases, 13 coordinator cases and compiled native/Android receipt agreement.
The indefinitely waiting optional Python worker is still alive when host
authorization succeeds. Essential failures remain denied. No extra optional
wait, watchdog, interpreter destruction or fabricated receipt was introduced.

The old complete ARM64 build passed at `56fca5a`, run `38799103180`.
It is not evidence that these newer corrections compile. The updated workflow
repeats the actual native/Python tests and full build using locked preimages.

Remaining safety evidence: the TEST1 export lacks call-site details sufficient
to establish that every reported Seren/Continuity failure is resolved; real
Android engine and guard-process death, data-preserving reopening and physical
Fold acceptance are unverified. The guard's `stopSelf()` is not evidence that
its containing process died. Unknown writes remain fail-closed. No new APK is
declared safe or locked by these host results. Optional unfinished private
writes can lose data or be corrupted; recovery is not assumed.
