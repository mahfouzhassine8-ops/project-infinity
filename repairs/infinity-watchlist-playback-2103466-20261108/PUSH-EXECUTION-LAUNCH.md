# Existing-workflow push execution — no new workflow or signer

The existing Git transport remains usable while local GitHub dispatch API
credentials are expired. Root can review/commit the corrected selected harness,
its host receipt and exact request in one normal commit, then push the existing
phase-B branch. This orchestration does not rebuild or alter signed APKs 68/69.

## Selected Android retry

The existing feature workflow admits a push only on
`work/infinity-watchlist-phase-b-20261108` touching this task's
`ANDROID-EXECUTION-REQUEST.json`, with commit message beginning exactly
`Verify Watchlist468:`. Its selected job checks out `github.sha` when no manual
source input exists and requires this source-bound request:

```json
{
  "schema": 1,
  "operation": "verify-watchlist-signed468-forward469",
  "feature": "watchlist-playback-android",
  "owner_authorization_commit": "8e83bcb8374dec0ccc646cbe02c3c4249395ba8c",
  "application_tests": true,
  "shutdown_tests": false,
  "signed_pair_request_sha256": "EXACT_CURRENT_SIGNED_PAIR_REQUEST_SHA256",
  "android_request_sha256": "EXACT_CURRENT_ANDROID_REQUEST_SHA256",
  "runtime_source_pins_sha256": "EXACT_CURRENT_RUNTIME_SOURCE_PINS_SHA256",
  "harness_host_result_sha256": "EXACT_CORRECTED_HARNESS_HOST_RECEIPT_SHA256"
}
```

Do not commit placeholder hashes. Generate the real request after the native
agent freezes the corrected selected harness and its passing host receipt.
Update the signed-pair request's existing harness-host-receipt hash to that same
receipt; its exact APK/archive/signing-producer identities remain unchanged.
The new execution request's signed-pair hash then binds that reviewed request.
An optional reviewed attempt/reason field may distinguish a necessary retry.

The inline push guard verifies the original owner document at the explicit
authorization commit and every request hash. Existing full source/harness pins,
workflow identity, archive metadata/SHA, original certificate, actual APK/native/
module bytes and selected feature checks still execute. All ten actual cases
remain required; prior partial/failure evidence is retained.

The generic android17 job explicitly excludes only phase-B pushes, preserving
its old manual routes. Every other old feature job and manual input is unchanged.
The selected emulator action step has a 45-minute limit inside its 75-minute job,
leaving time for the existing always-artifact upload after bounded failure.
The native agent owns the separately reviewed harness/RPC/disposal correction.

## Engineering publication after actual Android PASS

The existing sole combined workflow admits publication on the same branch only
when `PUBLICATION-REQUEST.json` changes and the message begins exactly
`Publish Watchlist468:`. Existing manual `publish-watchlist` remains available.
Use the already documented actual-PASS publication request schema; all ten-case,
tested-APK, archive, receipt, original SDK certificate and API asset-hash gates
remain unchanged. Fold acceptance remains pending. No key-bearing or preparation
job is admitted by either new push route, and no accepted pointer is updated.

Only focused static routing/source-guard checks ran for this orchestration;
see `PUSH-ROUTING-HOST-RESULT.json`. No application/workflow was run, no commit or
push was issued, and no runtime/APK/authority/signing source changed here.
