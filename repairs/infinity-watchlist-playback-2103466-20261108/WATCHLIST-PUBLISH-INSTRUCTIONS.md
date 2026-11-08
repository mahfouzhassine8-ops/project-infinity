# Root publication transport integration — fragment only

`WATCHLIST-PUBLISH-JOB.yml` is an append-only proposed job for the existing
combined workflow (`397702717`). Root may append it under that workflow's
`jobs:` map and add the manual `publish-watchlist` operation choice. No old job,
signer, registry, runtime source or task Python file is changed by this draft.
The job has contents write plus read-only Actions access, and no signer secrets.

Do not create a placeholder publication request. After the exact selected
Android run succeeds, commit `PUBLICATION-REQUEST.json` with this schema, replacing
every example value with actual producer metadata:

```json
{
  "schema": 1,
  "operation": "publish-watchlist-engineering-prerelease",
  "repository": "mahfouzhassine8-ops/project-infinity",
  "publication": true,
  "prerelease": true,
  "accepted_pointer_updated": false,
  "signed_pair_request_sha256": "EXACT_SHA256_OF_COMMITTED_SIGNED_PAIR_REQUEST_JSON",
  "android": {
    "run_id": 1,
    "source_commit": "EXACT40HEX_SELECTED_ANDROID_HEAD",
    "workflow_id": 1,
    "artifact": {
      "id": 1,
      "name": "Infinity-Watchlist-Selected-Android-EXACTRUN-NOT-FOLD-ACCEPTANCE",
      "digest": "sha256:EXACT64HEX_ZIP_SHA",
      "size_in_bytes": 1
    }
  },
  "release_tag": "infinity-2103468-watchlist-fold-pending",
  "release_title": "Infinity 2103468 Watchlist — Fold acceptance pending"
}
```

`android.workflow_id` must be the real existing identity returned by
`actions/workflows/infinity-saved-navigation-android.yml`, not a new workflow.
`SIGNED-PAIR-REQUEST.json` uses the existing `ANDROID-WORKFLOW-LAUNCH.md` schema;
candidate/recovery producer runs may differ. Freeze the publication fragment
before the forward-recovery authority/workflow source registration, following
the existing separate canonical67 → 68 → 69 registration sequence.

Admission authenticates the selected Android run/branch/source/workflow and its
successful named feature job; compares frozen workflow/request/harness/runtime
source bytes at that exact commit; verifies the Android artifact's whole ZIP
SHA and size plus safe paths; and requires its exact PASS status. The required
case set comes from the ten literal `passed()` calls in the frozen harness AST,
with no missing, duplicate or non-PASS case. Nine narrative scope entries are
not treated as a ten-case result. Synthetic media, unmodified provider code,
no provider account, Fold NOT_RUN, shutdown NOT_SELECTED and acceptance false
are explicit report checks.

The staged Android `ANDROID-INPUTS.json` must identify the same baseline66,
candidate68 and recovery69 hashes as the committed signed-pair request. Both
published APKs are downloaded again from their exact successful original
combined-workflow producer archives, checking GitHub metadata, whole ZIP digest,
size, build-receipt source/version/hash/certificate and actual SDK certificate.
Only byte-identical original-signed APKs are copied into the release payload.

The job assembles two APKs, `ENGINEERING-EVIDENCE.zip`, installation/forward-
recovery instructions, `DOWNLOADS.json` and `SHA256SUMS`. It first creates a draft
prerelease, uploads the payload, verifies each API asset's SHA/size, and generates
download links from verified asset responses. It then uploads/verifies manifest
and checksums and publishes the prerelease with `make_latest: false`. Existing
tags/releases are never replaced. A failed pre-publication upload remains draft;
the job does not silently overwrite assets, bypass a gate or expose a partial
release. Root owns any explicit cleanup/retry after inspecting such a failure.

The published title/body/instructions clearly retain Fold acceptance pending and
synthetic-media engineering scope. No accepted pointer, signer key or APK byte
is changed. `WATCHLIST-PUBLICATION-RECEIPT.json`, `DOWNLOADS.json` and the gate
are also retained as workflow evidence. The local upload-host 401 issue is
avoided by executing upload on the existing GitHub runner with its scoped token.

Only YAML/embedded-Python static parsing is performed for this draft. No workflow,
publication, runtime test, build or signing command has run as part of it. Root
must review the fragment before integration and execute only after Android PASS.
