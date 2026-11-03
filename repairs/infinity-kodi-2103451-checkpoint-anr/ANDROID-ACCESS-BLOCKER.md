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

## Supported options investigated after native compilation

The user explicitly confirms there is no verified self-hosted ARM64 runner label
and the Samsung Fold is not connected. Do not invent a runner or expose the
phone's debugging port publicly.

The managed environment was rechecked: running/connected with no configured
capabilities, cloud identities or secret bindings. `adb`, `gcloud` and
`tailscale` are absent. The enforced network configuration has no VPN, no
automatic Tailscale access, and empty permitted TCP domains/IP ranges. Ordinary
HTTPS access is not an authorized ADB connection.

- Firebase Test Lab is a supported service with physical and Arm virtual device
  options. Its official CLI documentation requires authenticated Google Cloud
  access and a configured Firebase project. Models and supported OS versions
  must be selected from the actual authorized catalog. No project/identity is
  configured here, and Android17/API37 availability has not been established.
  No device/model/ABI or account permission is invented. No paid service or
  new project was provisioned, and no credentials were requested.
  Source: https://firebase.google.com/docs/test-lab/android/command-line
- Android's official wireless ADB workflow requires an authorized paired
  workstation/device connection, ordinarily on the same wireless network,
  using a QR/pairing code and `adb pair`. The remote Fold is not attached or
  paired to this workspace, and no approved network path is configured. A
  user-controlled paired workstation/runner or properly authorized environment
  connection would be needed. No port scan, guessed address, unapproved tunnel
  or access-control workaround was attempted.
  Source: https://developer.android.com/tools/adb

Both official pages were fetched/read successfully through the existing HTTPS
proxy on2026-11-03. These are supported options, not newly available test targets.
The next action is to arrange an authorized device-farm project/identity with a
verified native ARM64/API-compatible catalog entry, or a legitimate connected
ARM64 Android device/runner. Signing credentials are not needed for this access
step. Until then Android verification remains BLOCKED and no successor is signed.
