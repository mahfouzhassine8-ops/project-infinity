# Provider-owned fresh-result policy experiment — HOLD FOR REVIEW

**Not a release. Not an authorized replacement of the existing strict settings/ABA contract.**

Parent source: `c75e6de691cc6263236d778cd16b50573e7eb348`.
Branch: `work/infinity-search-provider-owned-fresh-results-20261107`.

The original source already sends an owned `Files.GetDirectory` request for each
verified enabled installed provider, and a native lease reports whether that
provider completed. This branch tests an alternative common acceptance rule:
for a **fresh completed native-provider result only**, if the **only** change
in the existing response signature is that provider's own `settings.xml`
metadata, retain its original returned rows. Re-verify current native source,
manifest, dependency, profile and route consistency, and do not cache the
response when the settings generation changed.

No provider-specific exceptions, provider code modifications, new search
engines, new navigation screens, fallback retries or duplicate requests.

**Known unresolved safety tradeoff:** This rule cannot distinguish a harmless
history write from a meaningful native provider configuration change or
A→B→A in that file. The candidate host suite deliberately demonstrates both
cases being accepted. It is therefore **NOT approved for release** under the
earlier mandatory meaningful/ABA rejection requirements. It must not be merged,
signed, or represented as a completed safe validator. The separate proof-model
branch `work/infinity-search-settings-proof-candidate-20261107` specifies the
native evidence requirements to distinguish these cases reliably.

All source is isolated to the Search experiment branch. Preserve parent,
installed APK462, original signer, Cobra, Preview, all third-party providers,
native engine/graphics/keyboard source, and every locked UI element.

## Gate

Do not promote unless the owner explicitly changes the meaningful/ABA policy,
or verified complete request-owned native mutation evidence closes the current
safety gap. Never silently weaken existing source/enable/dependency/profile/
cancellation checks, and never claim a host-only PASS is an Android/Fold PASS.
