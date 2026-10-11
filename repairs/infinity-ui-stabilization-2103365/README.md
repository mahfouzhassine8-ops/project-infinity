# Approved Infinity UI source baseline

Use **1.0.5.204 Closing Status Polish RC1**, skin ID `skin.infinity.diggz`, active profile `unified`. The user confirmed this installed identity and description on 11 October 2026. The `.206` audit package is diagnostic guidance only.

| Source | Package SHA256 |
| --- | --- |
| Approved `.204` current source and rollback | `4238c9eaf341d921b319fd421bae5c47e3ed51925bed63033a558ae898787b47` |
| Protected locked `.201` parent | `c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5` |

The protected repository's existing `repairs/directory-close-2103330/build_skin204.py` reproduces the original `.204` ZIP byte for byte from the locked `.201` archive. Only `addon.xml` and `unified/DialogButtonMenu.xml` differ between these packages. All 2,938 other files are identical.

Keep `unified/DialogButtonMenu.xml` byte identical to `.204`: SHA256 `149b614b9dd96094e64c7b7a837fbc911bfceda40e4ecef84716f7a3a6220d78`. This preserves the existing closing acknowledgment, optional motion, property transitions and Close/Force Close routes. Do not introduce a new shutdown popup or change its native handling.

## Verification

The inventory generator checks original archive hashes, complete extracted-file equality, original-builder reproduction, skin identity/description, active profile, the complete `.201` → `.204` delta and active XML parsing. `source-inventory.json` records all 2,940 approved file hashes and eight screen owners. `source-gate.json` records the concise source proof and rollback references.

Run the existing `.204` builder into a temporary `reproduced-1.0.5.204.zip`, then:

```sh
python3 repairs/infinity-ui-stabilization-2103365/record_source_inventory.py \
  --approved /absolute/extracted-204/skin.infinity.diggz \
  --parent /absolute/extracted-201/skin.infinity.diggz \
  --packages /absolute/original-archives-and-reproduction \
  --evidence /absolute/audit-and-diagnostic-evidence \
  --out repairs/infinity-ui-stabilization-2103365
```

Expected original filenames are `skin.infinity.diggz-1.0.5.204-Closing-Status-Polish-RC1.zip` and `skin.infinity.diggz-1.0.5.201-Complete-Settings-Polish-RC1.zip`. Preserve both archives unchanged. Packaging must start from the full `.204` archive and retain every unmodified entry byte for byte; list every authorized UI delta. Assign a distinct repair-candidate version without changing the skin ID or existing contracts.

## Isolation and pending evidence

This preparation branch starts at protected 2103365 commit `faf41ee1d35fe55140bb1e193089643cc9ac06ee`. These records change no skin, native, Android, provider, Command Center, Resume Hub or diagnostic-classification source. The concurrent 2103366 branch is not updated or merged.

No UI repairs or candidate promotion are claimed yet. Independent Fold byte export, runtime bounds, interactions, theme/window coverage, backend status/watched contracts, comparative performance measurements and physical acceptance remain pending. Screenshot identity is not a hash of every installed byte.

For rollback, restore the original `.204` skin package without deleting settings or userdata. Retain `.201` as the protected parent; do not automatically downgrade to it. Do not install `.206` to implement these repairs.
