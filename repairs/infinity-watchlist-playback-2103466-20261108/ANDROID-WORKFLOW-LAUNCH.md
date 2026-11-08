# Selected Android workflow launch contract

Use the existing `.github/workflows/infinity-saved-navigation-android.yml` workflow and its existing workflow identity. The added feature choice is `watchlist-playback-android`; the sole added job is `selected_watchlist`. The only prior-job edit excludes that new choice from the generic `android17` runner. All old choices and every other prior workflow byte remain unchanged.

No app execution is admitted until root commits `SIGNED-PAIR-REQUEST.json` in this task directory after the original combined workflow signs both new inputs. Do not commit placeholder IDs or hashes. Its schema is:

```json
{
  "schema": 1,
  "operation": "verify-watchlist-signed468-forward469",
  "repository": "mahfouzhassine8-ops/project-infinity",
  "certificate_sha256": "d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7",
  "runtime_source_pins_sha256": "SHA256_OF_RUNTIME_SOURCE_PINS_JSON",
  "android_request_sha256": "SHA256_OF_ANDROID_REQUEST_JSON",
  "harness_host_result_sha256": "SHA256_OF_ANDROID_HARNESS_HOST_RESULT_JSON",
  "inputs": {
    "baseline": {
      "version_code": 2103466,
      "run_id": 42462319257,
      "source_commit": "EXACT40HEX_SIGNING_RUN_HEAD",
      "workflow_id": 397702717,
      "artifact": {"id": 13609794621, "name": "EXACT_ARTIFACT_NAME", "digest": "sha256:EXACT_ARCHIVE_SHA256", "size_in_bytes": 1},
      "apk_sha256": "d366e4b8aadba8484768cfcc0d362c2fc8e0181d78123ea77e04af4f028a3135",
      "apk_path": "Infinity-2103466-Combined-Original-Signer.apk",
      "receipt_path": "BUILD-RECEIPT.json"
    },
    "candidate": {
      "version_code": 2103468,
      "run_id": 0,
      "source_commit": "EXACT40HEX_SIGNING_RUN_HEAD",
      "workflow_id": 397702717,
      "artifact": {"id": 0, "name": "EXACT_SIGNED68_ARTIFACT_NAME", "digest": "sha256:EXACT_ARCHIVE_SHA256", "size_in_bytes": 1},
      "apk_sha256": "EXACT_SIGNED68_APK_SHA256",
      "apk_path": "Infinity-2103468-Combined-Original-Signer.apk",
      "receipt_path": "BUILD-RECEIPT.json"
    },
    "recovery": {
      "version_code": 2103469,
      "run_id": 0,
      "source_commit": "EXACT40HEX_SIGNING_RUN_HEAD",
      "workflow_id": 397702717,
      "artifact": {"id": 0, "name": "EXACT_SIGNED69_ARTIFACT_NAME", "digest": "sha256:EXACT_ARCHIVE_SHA256", "size_in_bytes": 1},
      "apk_sha256": "EXACT_SIGNED69_APK_SHA256",
      "apk_path": "Infinity-2103469-Combined-Original-Signer.apk",
      "receipt_path": "BUILD-RECEIPT.json"
    }
  }
}
```

Paths are relative to each downloaded artifact; use the actual subdirectory if its archive has one. Run IDs, source commits, artifact names/digests/sizes and APK hashes must come from the completed successful original signing producer and its unchanged receipts. Candidate and recovery may originate in separate successful runs. The signed inputs must come from workflow397702717, `.github/workflows/infinity-combined-release.yml`; candidate/recovery must use the authorized corrective branch and an ancestor of the verification source. No new signer or workflow identity is introduced.

After root commits that request and all reviewed orchestration, dispatch the existing workflow on the corrective branch, passing its exact current40hex commit as `source_ref`:

```sh
gh workflow run infinity-saved-navigation-android.yml \
  --repo mahfouzhassine8-ops/project-infinity \
  --ref work/infinity-watchlist-phase-b-20261108 \
  -f source_ref=EXACT40HEX_VERIFICATION_COMMIT \
  -f feature=watchlist-playback-android \
  -f authorization='Owner-authorized selected Infinity Watchlist playback/install-over/persistence/forward-recovery cases; no shutdown acceptance'
```

The existing `candidate_build` input has no role in this operation; exact inputs come exclusively from the committed pair request. The job verifies the existing feature workflow identity, request and harness/source pins, every producer run/source/workflow, all three artifact metadata records, actual downloaded ZIP SHA256 digests, signed APK hashes, source/version/certificate receipts, compiled candidate/native66 recovery bytes, actual candidate Python bytes and SDK APK signatures before the selected fixture is installed. Missing or failed producer evidence stops before app execution.

The task's source-only owner export is copied byte-for-byte from the retained input (SHA256 `e14b1e9c8441e78ce5c930dea8c7a5885053011d531df9ec51377fcb18298b65`). Staging reuses the12 exact pinned dependency archives and real POV/U sources. API37.0 Google APIs x86_64, stock ARM translation,4KiB and fresh emulator safeguards reuse the passing selected Search infrastructure. `prepare_android_emulator.py` is SDK installation infrastructure only; no shutdown runner is invoked.

Only `verify_watchlist_android.py` runs the selected app journey. Evidence records synthetic AIO/MP4 status, real SDK player events, actual native selected-item receipts and PID liveness. The workflow uploads logs, screenshots and admission/runtime evidence, not a public release. Fold acceptance and shutdown acceptance remain outside this operation. The workflow timeout is75minutes and cannot convert a failed source/network/provider/runtime observation into PASS.

No task Python/native file changed for this orchestration. The five harness files and their existing host receipt remain frozen. The job fragment in `ANDROID-WATCHLIST-JOB.yml` exactly matches the appended workflow job. Only source-only routing, inline admission and infrastructure orchestration checks are selected locally; no application or CI run is dispatched by this change.
