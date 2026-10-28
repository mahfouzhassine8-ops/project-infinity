This is a review proposal only. None of the changes below has been applied.
Runtime implementation and focused host source inputs are available at
`a0d1c0475e0168d28d93587e542a63e7cd44ee2a` on the existing working branch.

The user explicitly froze the chooser, and `CODEX-START-HERE-20261028.md` requires
its existing version-label bytes to remain identical. The current
`release_authority.py` requires an Infinity update to advance its displayed
last-updated number and requires the chooser bundle to carry that metadata.
Both constraints cannot hold simultaneously. Do not bypass either implicitly.

Requested narrow exception 1: change **only this chooser-owned metadata file**:

```diff
--- assets/experience-component-updates.properties
+++ assets/experience-component-updates.properties
@@
-infinity.last_updated_in=2103421
+infinity.last_updated_in=2103426
 cobra.last_updated_in=2103423
```

Preserve every chooser class, UI resource, setting, layout and behavior byte for
byte. Preserve the complete Cobra component ZIP byte for byte. Advance only the
chooser component's metadata revision, with an explicit metadata-only owner diff.

Requested narrow exception 2: adapt the **existing sole original-key combined
pipeline**, without enabling any other signer:

- Bind remote authority and its workflow guard to
  `work/infinity-only-stability-speed-from-2103425-20261028`. Keep protected
  2103425 and 2103420 refs exact; check the latest remote head before and after
  signing. Change no accepted pointer or physical acceptance status.
- Add a narrowly guarded module-preparation phase in that same workflow. Check
  actual baseline signature, exact immutable owner ZIPs, the five approved
  source preimages and every frozen member/function before using the original
  key to sign the reconstructed 75-file Infinity source manifest. Verify the
  original RSA signature natively/JCA before creating its new owner ZIP.
- Build the chooser metadata-only bundle and select the exact unchanged Cobra
  and Android-contract ZIPs. Register only those concrete component hashes in
  the next reviewed release-authority generation; do not waive any payload,
  protected-contract, source-evidence or dependency-ownership check.
- Run the final combined pre-sign gate and original signer for combined
  **2103426**, then verify signer, package identity, normalized manifest,
  matching component ZIPs and all protected bytes. Deliver one final APK.

This proposal does not authorize edits to Cobra or protected lifecycle,
shutdown execution, a redesign, a new signing key, destructive operations, or
release acceptance. Physical Fold testing remains the user's acceptance step.
