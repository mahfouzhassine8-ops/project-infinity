# Original-tool preparation

`prepare_release.py` prepares unsigned inputs and unsigned APKs only. It uses the
unchanged `module_bundle.build`, the original public key, and
`component_bundles.combine`. The existing `SignInfinityModules.java` remains the
sole module signing tool; this script neither invokes it nor reads credentials.
It does not modify authority, registry, workflow, signer, installed files, or
the protected originals. No behavioral acceptance is asserted.

The read-only selected inventory passed; see
`contract-evidence/RELEASE-BASELINE-INVENTORY.json`. All 79 baseline module
records and the original signature match. `INSTALL-BASELINE.v1` is retained
byte-for-byte; its historical migration preimages are recorded in the report.
The unchanged installer derives normal signed-generation upgrade preimages
from the installed authenticated manifest. Root separately runs its selected
actual-installer admission/recovery checks; this tooling does not replace them.

## Inputs required before staging

- Root's freshly audited JSON admission: `status` =
  `CONFIRMED_UNUSED_FORWARD_PAIR`, `authority_source` =
  `2aa41804821264581fe69e0fb1d10703e6583baf`, `generation` = 54,
  `latest_signed_versionCode` = 2103467, `candidate_versionCode` = 2103468,
  `recovery_versionCode` = 2103469, `candidate_CC` = `0.3.5.66`,
  `recovery_CC` = `0.3.5.67`, `reserved` = false. These are provisional
  prospective inputs, not an issued reservation.
- Committed complete `RUNTIME-SOURCE-PINS.json`: exact six `native` source
  entries and three `python` basenames plus `saved_playback.py` when present.
- Matching ARM64 artifact directory containing `libkodi.so`,
  `ARM64-LINK-VERIFIED.json`, and the complete `NATIVE-SOURCE-MAP.json`.
- The retained signed 2103466 APK and official prepared 2103466 components.

```sh
python repairs/infinity-watchlist-playback-2103466-20261108/prepare_release.py inputs \
  --apk /workspace/scratch/three-signed/2103466/Infinity-2103466-Combined-Original-Signer.apk \
  --prepared /workspace/scratch/three-official-prepared/2103466 \
  --native-artifact /path/to/matching-arm64-artifact \
  --admission-file /path/to/root-reviewed-version-admission.json \
  --out /path/to/fresh-watchlist-preparation
```

Review/freeze `SOURCE-PINS.json`, both `INPUTS.json` files and both complete
unsigned `modules/script.infinity.commandcenter/INFINITY-MODULES.v1` files.
Only the three CC files and optional helper enter the candidate. Recovery
restores baseline66 functional Python and native66, authenticates the same
helper without calling it, and advances metadata. Both retain Trakt 1.2.8.1
unchanged. Recovery does not delete unknown/newer files. Existing separately
signed 2103467 recovery is not an input and remains unused.

After the existing authorized owner workflow supplies each original-key `.sig`
beside its frozen complete manifest, run the thirteen selected actual-installer
cases with `python verify_modules.py --prepared STAGED_PAIR --out FRESH_AUDIT_DIR`.
The selection is recorded in `MODULE-TEST-SELECTION.md`. This adapts the pinned
original fixture/helper and runs its unchanged generated Java installer against
the new80 inputs, including recovery of every baseline66 functional module
byte, retained inactive helper and no-overwrite refusal cases. Then run `finish`
with the same preparation arguments.
Outputs are per-version `combined-unsigned.apk`, `publish/components/`,
`publish/PREPARATION.json`, and `publish/APK-PRESERVATION.json`. Finish checks
all frozen inputs, exact signature, complete79/80 manifest, unchanged protected
bundles and DEX, and exact APK members against original66. Only native,
allowlisted CC source, module signature/manifest, CC addon version, Infinity
experience label, component versions and typed Android version may differ.

`compare --apk BASE66 --candidate APK --preparation PREPARATION.json --out REPORT`
also checks a later APK against those frozen member hashes, ignoring only APK
signature members. It does not verify the APK signing certificate; the existing
original signer/release gate remains responsible for signature and release
admission. Neither successful preparation nor comparison is install acceptance.
