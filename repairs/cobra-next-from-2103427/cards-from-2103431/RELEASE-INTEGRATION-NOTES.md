# One reviewed 2103432 candidate through the existing signer

Prepared only. No producer dispatch, registration, APK build, signing, acceptance or lock operation was performed by this workstream. The two Python files parsed successfully; their release operations have not been executed. The signed 2103431 recovery remains canonical until a new candidate is actually produced and verified.

`register_release.py` proposes generation 17 / versionCode 2103432 from the exact generation-16 authority in signed source `9ccc4c362a65118eeba38a8e7e4b0de5723c69af`. Default behavior writes a separate reviewable proposal; `--apply` is an explicit registration step after all checks. Neither operation accepts or promotes the candidate.

| Authority item | Required result |
| --- | --- |
| Updated owners | COBRA and CHOOSER_SHELL only |
| Cobra | revision 8; `2103432.cobra.1`; five reviewed existing classes and the four bounded helper families |
| Chooser | revision 10; `2103432.version-metadata.1`; exact431 executable DEX/UI; only `cobra.last_updated_in=2103432` changes |
| Infinity | Exact431 ZIP `16eeb91a24bf0cf99d558d9e3dd17aedfd127e9a1936dcce413341c48683cd6c`; implementation remains2103427 |
| Android contract | Exact431 ZIP `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`; icons/native/shared members frozen |
| Protected contract, icon exception, accepted pointer | Unchanged |
| Previous authority digest | `96470eac85e2c897c0b95bd9861cc1f6cc624e730db58fe7c37bc984948b8f9e` |

The frozen owners retain their existing approved sources, component revisions and immutable artifact locations. Recovery APK SHA256 remains `3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471`. Permanent certificate remains `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

## Producer artifact contract

Use the existing feature-only workflow on the existing Cobra branch. Root owns the new scoped producer job and the exact selected test list; this document authorizes no additional runtime scenario. Package only after the selected essential checks pass.

Upload components directly at the root of `Cobra-Cards-Prepared-Owners-RUNID`: `catalog.json` and all four owner ZIPs. Upload the following evidence directly at the root of `Cobra-Cards-Host-Evidence-RUNID`:

```json
{
  "schema": 1,
  "status": "PASS_CARDS_PREPARED_OWNERS",
  "source": "EXACT_PRODUCER_COMMIT",
  "run_id": 0,
  "branch": "work/cobra-only-from-2103427-20261028",
  "catalog_sha256": "SHA256_OF_COMPONENT_CATALOG_FILE",
  "compiler_source_files": {"ALL_20_CURRENT_COMPILER_INPUTS": "SHA256"},
  "tested_source_files": {"ALL_COMPILED_PACKAGING_PREPARATION_AND_SELECTED_TEST_SOURCES": "SHA256"},
  "files": {
    "BUILD.json": "SHA256",
    "CORRECTIVE-PRESERVATION.json": "SHA256",
    "PACKAGE-CANONICAL-RESULT.json": "SHA256",
    "SOURCE-BINDINGS.json": "SHA256",
    "checks/cache/SELECTION.json": "SHA256",
    "checks/cache/INPUTS.json": "SHA256",
    "checks/cache/JUNIT.xml": "SHA256"
  },
  "selected_checks": [{
    "name": "root-selected-cache-check",
    "status": "PASS",
    "selection_file": "checks/cache/SELECTION.json",
    "inputs_file": "checks/cache/INPUTS.json",
    "junit_files": ["checks/cache/JUNIT.xml"]
  }],
  "runtime_limits": "Host correctness/work counts; device acceptance pending; no shutdown tests"
}
```

The illustrative check is not a prescribed test. Each actual selection JSON is written before its invocation:

```json
{"class":"ActualSelectedTestClass","methods":["exactSelectedMethod"],"recorded_before_execution":true}
```

Its JUnit methods must match exactly, with nonzero tests and zero failures/errors/skips. Each inputs_file must bind the actual final host SOURCE-BINDINGS hash, production/support jar hashes and committed selected test source hash. Existing reuse and Layout preparer receipt shapes are supported; stale owner inputs are refused. Bind every consumed raw result/selection in `files`, and bind the uniquely named selected Java test source in `tested_source_files`. Preserve actual selected raw evidence; a preparation-only SOURCE-BINDINGS status is not itself a test PASS.

The source map must include the complete `build.compiler_sources()` manifest, `package_owners.bound_sources()`, both new release scripts, `integrated-qa/prepare_release.py`, the feature workflow, selected tests and their preparers. Registration checks that each byte matches both the producer commit and the current checkout. The independent package proof, actual owner DEX, BUILD, host overlay SOURCE-BINDINGS and matching component ZIPs must agree. A later source change requires a matching producer, rather than editing its receipt.

Preserve the official downloaded artifact ZIPs. Registration checks their SHA256 against GitHub's artifact digest and compares each consumed local file to those archives. Example after a successful real producer:

```sh
python3 repairs/cobra-next-from-2103427/cards-from-2103431/register_release.py \
  --bundles extracted-owners --owners-archive owners-artifact.zip \
  --evidence extracted-evidence --evidence-archive evidence-artifact.zip \
  --producer-run RUNID --out reviewed432-authority-proposal.json
```

Review the concrete proposal, then invoke with a fresh `--out` path plus `--apply` when registering the verified vector. Do not run either command before the final source-bound producer passes. The registration commit must keep tested production/QA/package sources unchanged.

## Exact minimal root-owned policy proposal

In `repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json`, add only these project-root entries, retaining all existing entries and policies:

```json
"CobraCardsTiles": "COBRA",
"CobraCardsLayout": "COBRA",
"CobraProfileDataReuse": "COBRA",
"CobraCardsReuse": "COBRA"
```

This assigns the new reviewed Cobra helper families; it grants no cross-owner dependency or native/shared edit. Current class/member ownership and dependency gates continue to inspect the actual APK. The new authority refreshes the existing source_files pin for this reviewed policy.

## Exact minimal sole-signer workflow proposal

Retain `.github/workflows/infinity-combined-release.yml` as the **only** signer (workflow ID397702717), with its existing branch, trigger, serial concurrency, original credentials, retired-route checks, remote-lock/lineage checks, actual-payload gates and repeated pre-key checks. No edit to `release_gate.py` or `release_authority.py` is needed. Proposed workflow edits only:

1. Change dispatch description to `Sign reviewed2103432 Cards and Cobra performance candidate`.
2. After selected-owner assembly and before the existing hard pre-sign gate, recover and verify the registered Cards evidence using the command below. The evidence archive must be fetched from the artifact ID stored in `owner_update_evidence.artifacts`, from the actual successful producer. Check its stored/API SHA256 before safe extraction. Preserve it in release evidence. Do not rerun runtime tests in the signer.
3. Replace the final `Recover exact signed2103427...` step with run-id40971769136, artifact `Infinity-Combined-Original-Signer-40971769136`, path `previous2103431`. Remove the obsolete unaccepted430 download/comparison step.
4. Replace only the final delivery-verifier command with the new one below. Keep upload names/paths and all signing machinery unchanged.

Pre-key source/evidence check:

```yaml
      - name: Verify registered Cards producer evidence before keys
        run: |
          set -euo pipefail
          python3 - <<'PY'
          import subprocess
          from pathlib import Path
          from zipfile import ZipFile
          from inventory import load,file_sha,validate_names
          from release_gate import require
          a=load(Path('repairs/dual-experience-isolation-2103420/release-authority.json'))
          e=a['owner_update_evidence']; name='Cobra-Cards-Host-Evidence-'+str(e['producer_run'])
          row=e['artifacts'][name]; archive=Path('cards-evidence.zip')
          with archive.open('wb') as stream:
              subprocess.run(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/'+str(row['id'])+'/zip'],stdout=stream,check=True)
          require(file_sha(archive)==row['digest'].removeprefix('sha256:'),'OFFICIAL_CARDS_EVIDENCE')
          with ZipFile(archive) as z:
              validate_names(z);z.extractall('reviewed-cards-evidence')
          PY
          python3 repairs/cobra-next-from-2103427/cards-from-2103431/register_release.py \
            --check-registered --bundles combined-build/components \
            --evidence reviewed-cards-evidence --evidence-archive cards-evidence.zip
          cp reviewed-cards-evidence/PRODUCER-RESULT.json release-evidence/CARDS-PRODUCER-RESULT.json
          cp cards-evidence.zip release-evidence/CARDS-PRODUCER-EVIDENCE.zip
```

The equivalent standalone guard is:

```sh
python3 repairs/cobra-next-from-2103427/cards-from-2103431/register_release.py \
  --check-registered --bundles combined-build/components \
  --evidence reviewed-cards-evidence --evidence-archive cards-evidence.zip
```

This additional check is essential: generic `release_authority.verify_evidence()` does not consume the informational tested_source_files map. The Cards-specific pre-key check binds selected CI, all compiler/packager/verifier/preparer sources and actual packaged owner DEX to the final signer checkout, while preserving generic release-gate behavior. It repeats producer success/artifact identity checks and refuses missing/expired/changed evidence.

Final verifier:

```sh
python3 repairs/cobra-next-from-2103427/cards-from-2103431/verify_delivery.py \
  --baseline previous2103431/Infinity-2103431-Combined-Original-Signer.apk \
  --signed signed-combined --bundles combined-build/components \
  --sdk "$ANDROID_HOME/build-tools/35.0.0"
```

It verifies the actual original certificate and v1/v2/v3 signatures, install-over identity and typed version-only manifest change, every APK member/component DEX, exact431 frozen ZIPs/icons/native/chooser code, original authenticated Infinity modules, checksums and the reviewed icon exception. ZIP16K alignment is reported accurately; it does not assert ELF segment compatibility or fix the unchanged native warning.

Only after successful producer, reviewed registration and sole signing may the new signed candidate be delivered. Physical Fold acceptance remains pending; there is no automatic lock, promotion, shutdown test, installation, data clearing or recovery replacement.
