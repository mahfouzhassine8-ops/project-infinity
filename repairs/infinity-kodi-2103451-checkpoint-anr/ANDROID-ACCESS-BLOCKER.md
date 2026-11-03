# Required Android runtime gate — no substitute PASS

Native build inputs and exact signed451 are restored. Build run41729462691 is
separate from behavioral verification and has no signing/application step.

No compatible Android runtime is currently confirmed:

- Local executor: x86_64, no adb/emulator or exposed KVM.
- Read-only Actions capability receipt: x86_64 host, adb/KVM present, no installed
  image/emulator executable at observation time. This is not native ARM access.
- Repository self-hosted runner inventory returned403 `Resource not accessible
  by integration`. No alternate credential or access-control bypass was tried.
- No Android/device connector is exposed in the active tool inventory.

The historical API37.1 OS-backcompat route did start Kodi in run40407451498.
Later run40726662543 used that same image family, native bridge SHA and both
compatibility property values, but the exact native SHA still faulted in
`talloc_lib_init+60` before Kodi/Python. This earlier success does not justify
another unchanged trial. See the retained
`repairs/infinity-only-performance-2103425/runtime/OUTCOME.md` and its byte-bound
JSON receipts. The constructor issue is not a demonstrated P0 checkpoint fault,
and no native allocator/auxv/constructor or timeout workaround is authorized.

The required next input is an existing authorized, supported ARM64 Android
runner/device connection (or its exact runner label from the repository owner).
The owner can also arrange properly scoped runner-inventory access through the
connected integration, but no signing credentials should be transferred.
If no such target exists, the mandatory Android scenarios remain BLOCKED.

Neither compilation nor the host peers prove actual CVideoDatabase callback
completion, successful/rejected native checkpoint receipts, Android
surfaceDestroyed behavior, ANR clearance, playback continuity or physical Fold
acceptance. Preserve the independent selected test boundaries in AGENTS.md.
Do not make a shutdown run a CI dependency of compilation/signing or label a
blocked gate PASS. No successor is signed/delivered until the user-required
verification gates are satisfied; no automatic lock is authorized.
