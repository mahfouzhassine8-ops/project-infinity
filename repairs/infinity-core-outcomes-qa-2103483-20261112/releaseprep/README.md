# Key-free preparation from locked83

No signing code or credentials are included. Existing scripts, policy, workflow,
registry, original83 APK and protected recovery artifacts remain unchanged.

`BASELINE83.json` records the live November12 reconciliation: canonical source
`3d9709bb1226a2ffa3a474cf04b3d3842b084611`, generation68, candidate83,
last-issued82, and actual original83 signing run43119348510. No later original
workflow issuance appeared in the observed run list. A new version is neither
reserved nor selected by this helper; the request must name a reviewed provisional
version and the live canonical ref is checked again before staging.

The owner-selected83 starts/functions but has a retained owner shutdown failure.
This diagnostic preparation does not claim that failure is repaired.

## Input contract

Keep `REQUEST.template.json` disabled until root freezes actual inputs. Producer
rows have `run`, `source`, `workflow_id`, `id`, `name`, `digest` and `size_in_bytes`.
Both run and artifact identity are checked through read-only GitHub metadata.
Downloaded owner/native/Android ZIP digests and consumed members are checked.

`native_proofs` has exactly `build` and `source_preservation`. Each descriptor has
`file`, `sha256`, `status` (an actual frozen PASS status) and `required_fields`.
The build fields must include actual `native_sha256` and `source_commit`.
Source preservation fields must bind the original83 native hash and actual
native producer commit. Root supplies the exact proof filenames/status/fields
after its ARM64 workflow emits them; no successful proof is assumed here.

`android_proof` uses the same descriptor form. Actual selected native-injection
evidence must bind `native_sha256`, `baseline_APK_sha256`, `native_injection:true`,
`APK_modified:false`, `before_first_launch:true`, and `owner_device:false`.

The Android experiment installs exact original83 on a fresh qualified CI VM and
replaces only its extracted engine before first launch. It does not sign another
APK or bypass the original package/certificate/module guards. Record the original
installed APK/certificate separately from the injected runtime-native hash.
This proves only the selected modified-engine execution, never candidate APK
installation, install-over data retention, owner-device behavior or acceptance.

## Staging command after reviewed ARM64 and Android evidence

```sh
python repairs/infinity-core-outcomes-qa-2103483-20261112/releaseprep/stage.py \
  --request <frozen-request.json> --baseline <original83.apk> \
  --components <original83-owner-components> --owners-archive <official83-owners.zip> \
  --native <verified-native-files> --native-archive <official-native.zip> \
  --android <selected-android-evidence-files> --android-archive <official-android.zip> \
  --sdk <android-build-tools35> --out <fresh-output>
```

The implementation hashes original39 toolkit files before importing them and
reuses the immutable `copy_entry/rebuild_owner` implementation from the83
producer, then calls original `component_bundles.combine`. It compares every
non-signature APK member to exact83. Only `lib/arm64-v8a/libkodi.so`, typed Android
version metadata and `assets/experience-component-updates.properties` may differ.
The entire Cobra and minimal-contract owner ZIPs remain byte-identical. DEX,
modules, Python, Core paths/files, providers, skin and other resources cannot
change through this adapter.

## Original signing remains a separate later operation

The existing sole original-key workflow is `infinity-combined-release.yml`,
ID397702717, with original `release_gate.py` then `assemble.py sign` and its
existing identity/key cleanup. Existing `release_internal_qa.py` is hard-pinned
to82-to83, generation68 and its old evidence; do not pass new inputs to it.
Root must review a narrow83-based authority/signing admission after actual
evidence exists, reconcile the then-live next version, and retain every original
policy/source/owner/certificate gate. Do not weaken an original rejection.

Only after original signing can actual PackageManager install-over and retained
data checks be attributed to the new originally signed diagnostic APK. They are
not replaced by injected-native Android evidence. No canonical workflow changes,
authority proposal, original-key invocation or owner installer is produced here.
