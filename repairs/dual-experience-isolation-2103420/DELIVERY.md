# Signed 2103421 — ready for the Fold check

[Download the signed APK package](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40447183241/artifacts/12709465093)
(327 MB ZIP). Extract `Infinity-2103421-Combined-Original-Signer.apk` and install
it over the existing app. It remains one package, one icon and the original
Choose Your Experience. No component ZIP is installed separately.

APK SHA256:
`a1ea9442cd8ff82be09c34cc7c84887178fb162b8397005bba656ff6e28f5637`

Original permanent certificate SHA256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`

The APK is 777,992,848 bytes. Its v1, v2 and v3 signatures, 16 KiB ZIP alignment,
package/version, single launcher, all 16,526 expected packaged class/member
identities, and owner dependency boundaries were verified after downloading it.
The clean production build reproduced the reviewed component bundles exactly.

| Component | Version | Runtime state |
| --- | --- | --- |
| Infinity | `2103420.isolation.1` | Original native/Kodi state, own persistence queue/barrier and background service |
| Cobra | `bundled-2103420.isolation.1` | Own persistence queue/barrier and background service; existing settings retained, narrow shared settings snapshotted once |
| Chooser shell | `2103420.container.1` | Original launch preferences and single chooser |
| Android contract | `isolation-contract.1` | Versioned owner ports and combined termination authorization |

The approved component source is `9efaeabee45389b7c919ae1a3d88c394b1804173`.
The signing workflow source is `b69d18637658be676605c61e5a8792ab5ca179cb`,
authority generation 4. Later guard/distribution evidence updates changed no
component or APK payload. Three successful signing runs produced the same APK
hash; the final package uses compression for a smaller download.

[Build and signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40447183241)
completed successfully. [Download exact owner bundles](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40447183241/artifacts/12708932965)
and [gate evidence](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40447183241/artifacts/12709062400)
are available separately for engineering/reproduction.

The source-preservation check covered all 64,143 original methods and 311 copied
methods. Fifteen owner-contract cases and thirteen focused production-boundary
cases passed. Real independently built component controls preserved the opposite
owner. Higher-version stale Infinity/Cobra APKs and an altered common manifest
were rejected. Fingerprint/proposal controls also rejected cross-owner code,
protected receipt/native-lease changes and payload changes disguised as an
evidence refresh. No repetitive shutdown stress test was run.

The sole original-key release workflow rechecks the latest remote authority and
actual APK contents before signing, then rechecks authority before publication.
All 349 historical workflows with original-key access are disabled; their source,
runs and artifacts remain. The guarantee applies to this official signing
pipeline, not arbitrary installers or an administrator deliberately replacing it.

The user-approved 2103420 lock is still
`883c64a4de6f87077893921454de71bba850235b`. Its APK, reference data and accepted
combined-release registry are unchanged. Existing native libraries, add-ons,
skin and other assets remain baseline-identical; the six original add-on/skin
ZIPs still match their APK contents.

**Physical Fold acceptance is pending.** This candidate has not replaced the
accepted baseline. The only remaining acceptance step is the user's Fold check.
See [the data/lifecycle contract](DATA-AND-LIFECYCLE-CONTRACT.md),
[local delivery verification](results/delivery-2103421/DELIVERY-VERIFICATION.json),
and [source-bound focused evidence](results/scoped-correction/final).
