# Signed 2103423 — Cobra all-layout window reflow

[Download the signed APK package](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40486072720/artifacts/12724339360)
(327 MB ZIP). Extract `Infinity-2103423-Combined-Original-Signer.apk` and install
over the existing 2103421. One APK, one icon and the original chooser remain.

APK SHA256:
`4cbbf963be72904de962f434d00ee5f9d5080de6b6b9fd4b3e31ab1d6ac01aff`

Original certificate SHA256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`

The correction observes the current measured window before rendering and invokes
Cobra's existing panel/tile/guide layout operations. This corrects the shipped
path that could leave fixed cover-width canvas parameters after the parent grew.
It applies to single player and every supported Multi-View count, 2–4, including
existing Fit/Fill and enlarged layouts. The shipped store rejects counts over 4.
Window bounds, surface replacement, display, insets, padding and density changes
are observed without requiring a configuration callback. Exactly one observer
survives Android's transfer of pre-attachment listeners.

Infinity, chooser and shared-contract component bundles are byte-for-byte the
same as in 2103421. Cobra's existing playback, channel, audio, seek, persistence
and shutdown implementations are unchanged. Only Cobra Activity initialization,
two view-layout bridge methods, the geometry observer and Cobra's component
version differ from the installed foundation. There is no data/schema migration.

| Check | Result |
| --- | --- |
| Original fixed-width failure reproduced using shipped layout code | Reproduced |
| Counts 2,3,4; Fit/Fill; normal/enlarged; both directions and rotation-sized bounds | Passed: 48 measured geometry fixtures |
| Single player; cover/inner/rotation/PiP-sized return; replacement presentation | Passed |
| Actual rebuilt Activity bridge | Passed |
| Attachment listener transfer | Earlier candidate reproduced 2 observers; final candidate verified 1 |
| Non-target owners and protected contract | Exact unchanged fingerprints |
| Higher-version stale Cobra packages | Rejected before signing |
| Downloaded final APK | Original v1/v2/v3 signatures, package/version, alignment, single launcher and all 16,528 expected class/member identities verified |

Six focused tests passed using actual production DEX translated for Robolectric
API35. These are Android view-measurement fixtures. Real decoded stream/audio
continuity, physical folding and actual system PiP/fullscreen transitions remain
for the user's Fold check; PiP-sized fixtures are not device PiP acceptance.
No Infinity application or shutdown stress scenario was run.

Cobra component: `bundled-2103420.isolation.1.fold-reflow.2`, revision 3.
Infinity remains `2103420.isolation.1`. Authority generation 6 reserves app 2103423.
The intermediate 2103422 engineering candidate is superseded by this build.

[Feature source and tests](https://github.com/mahfouzhassine8-ops/project-infinity/tree/207949de66e09cc8cf4d493cafdb324dbc29475c/repairs/cobra-all-layout-fold-reflow-20261027)
are on the dedicated Cobra branch.
[Producer CI](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40485414619)
and [original-key combined signing](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40486072720)
passed. [Local delivery receipt](results/cobra-reflow-2103423/DELIVERY-VERIFICATION.json)
and [focused results](results/cobra-reflow-2103423) preserve the exact bindings.

**READY_FOR_FOLD_CHECK.** The user reported installing 2103421. No physical
acceptance is inferred from installation, and the accepted-release pointer stays
at the previously approved baseline. The immutable Infinity 2103420 lock remains
`883c64a4de6f87077893921454de71bba850235b`.

The [2103421 foundation delivery](DELIVERY-2103421.md) is retained for reference.
