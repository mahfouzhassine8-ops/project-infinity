# Controlled Infinity testing APK 2103458 and forward recovery 2103459

Both APKs are original-key signed, available to download, and independently
verified against their signed member inventories. These are testing/recovery
artifacts, not physically accepted releases. The Fold's installed version is
**UNVERIFIED**. Nothing was installed, uninstalled, reset, promoted or locked.

| Artifact | Signed APK download | Exact matching component ZIPs | Signing source / run |
|---|---|---|---|
| 2103458 testing | [APK artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42108276626/artifacts/13452054420) | [Components](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42108276626/artifacts/13452864327) | `b740fc6f2f987c83b9a67617bfae82a34bd307d2` / [42108276626](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42108276626) |
| 2103459 forward recovery | [APK artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42112995114/artifacts/13453414655) | [Components](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42112995114/artifacts/13454173762) | `c9e765fdc0bdc7d87c0b74392c0d40038570608f` / [42112995114](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42112995114) |

GitHub artifact links download ZIP archives; extract the single named APK for
installation. The component artifacts contain the matching INFINITY, COBRA,
CHOOSER_SHELL and MINIMAL_ANDROID_CONTRACT ZIPs and catalog. GitHub repository
access is required. All four linked artifacts were actually downloaded and
verified here; they are not inferred from a green workflow.

APK SHA-256:

```text
eb2c5121b6a0173dc3848eda93ea0d640d1db9245de5b5985933312d56e951fd  Infinity-2103458-Combined-Original-Signer.apk
7a7f1d0f36cc38665626f0759a129f1adb6522d6a7910a7241f96256742f9f93  Infinity-2103459-Combined-Original-Signer.apk
```

Both retain package `com.projectinfinity.kodi`, one original signer, and verified
v1/v2/v3 signing. Certificate SHA-256:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
The original workflow's apksigner results are bound to the actual independently
downloaded APK hashes; this is not a claim of local APK installation. ELF64 / AArch64,
SONAME, dependencies and strong ABI checks passed for the reused engine. Manifest
comparison permits only versionCode changes. Device install-over is NOT RUN.

## Findings and included correction

The actual signed 2103456 payload contains the intended drawer XML/helper. Missing
packaged files do not explain the reported phone behavior. Its raw skin helper
lacks the registered clean first-party native owner that the existing authenticated
Command Center entry has. 2103458 sends five drawer callbacks through that existing
entry and the same guarded navigation functions. Provider identity/source/entrypoint
checks remain intact; there is no substitute provider or intermediate Infinity menu.
This fixes a confirmed integration gap, not a proven attribution of the failed phone
tap. Installed Umbrella/SportHD compatibility and real destination execution remain
NOT RUN. Favorites still uses the original native Favorites route; the missing saved
collection cannot be attributed without the existing read-only device diagnostic.

The verified failing Light screenshot matches specific browser defects: overlapping
nested coordinate spaces, stretched poster, untinted white-pixel panel and the
legacy `GlobalCaseVar` fallback to `trailers.png` when resolution/case metadata is
absent. The typed-media normal/Slim List now uses bounded two-column geometry,
proportional genuine artwork, available selected-item details and existing native
Play/Trailer/Info actions. Short-window actions remain outside independently
scrolling details. Existing palette, fonts, textures, loading ownership and view
preference reconciliation remain in use. Passive genre tags use the existing
resident tick, with no new worker, provider calls, settings writes or action authority.

The canonical PNG was reconstructed from the 12 original transport parts,
SHA-verified as `6786b5cadb7153bb0036a651dcfba889a58f2a5acd79a759a798302e2d70c0ad`,
and opened with the original failed JPEG. Both originals are committed unchanged
in `630e4009`. [Reference findings](VERIFIED-REFERENCE-CONTINUATION.md).
Application-source checkpoint is `924fd6e593c4f0fcc7cf96bcd5f9b3347b3a295d`;
official preparation source is `735f269f6c2f0fc223b4fd98648f666d41a2496e`.

## Exact preservation

Against the actual signed 2103456 APK, testing 2103458 changes **14 existing payload
members and adds one helper**; **7,607 existing members are byte-identical**. All
**47 native libraries and five DEX files** are unchanged, including the already
approved touch engine SHA `9f77b092899b51850928007578e0fbf91bad38c05f147a308f3ac0cf5c036638`.
The accepted drawer height, row sizes/order and Power behavior remain unchanged;
only five callback strings differ in that drawer XML.

Six existing runtime source members change: Command Center `default.py` and
`media_view.py`, plus skin `Custom_1198_InfinityNav.xml`,
`Includes_InfinityMediaLists.xml`, `MyVideoNav.xml` and `Variables.xml`.
Command Center `library_navigation.py` is the one new helper. The other eight
changes are version/authentication metadata: AndroidManifest, Command Center
addon/manifest/signature, skin addon/protected manifest/identity, and component
update properties. [Full member list and counts](packaging/signed458-evidence/INDEPENDENT-SIGNED456-COMPARISON.json).
[Every member's before/after hash](packaging/signed458-evidence/preservation/ALL-APK-MEMBER-HASHES.json).

These counts and member maps cover APK payloads. Original-key signing separately
regenerates `META-INF/MANIFEST.MF`, `META-INF/INFINITY.SF` and
`META-INF/INFINITY.RSA`; the v2/v3 APK Signing Block is outside the ZIP member list.
Those signing artifacts are excluded from payload-equality counts, not from the
full downloaded APK SHA-256 or original-certificate/signature verification.

Against frozen signed 2103451, the complete previously authorized master/touch
overlay is 16 changed existing members plus eight new members; 7,598 existing
members are unchanged. The sole native difference from 451 is the previously built
two-file touch correction, not a new 458 native repair. Cobra, Preview, all DEX,
providers and unrelated resources are preserved. No real profile/database was
opened or modified. Cobra and minimal/shared component ZIP hashes are identical
to their frozen originals. [451 comparison](packaging/signed458-evidence/preservation/APK-PRESERVATION.json).

Recovery 2103459 has **eight authenticated/version metadata changes** against
signed 2103451, no new payload members, and **7,606 existing members identical**.
It restores the exact frozen 451 functional code and native engine
`151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e`.
[Independent recovery comparison](packaging/signed459-evidence/INDEPENDENT-FROZEN451-COMPARISON.json).
All 19 recovery lock refs and the accepted-combined pointer remain unchanged.

## Verification and limitations

| Check | Result and limit |
|---|---|
| Browser source contracts | 17 PASS |
| Genre publication/race/fallback isolation | 6 PASS; initial observer-order failure retained and corrected |
| Existing global-view preference cases | 17 PASS |
| Guarded drawer dispatch and geometry preservation | 15 PASS; fixtures/isolated real functions, not Android bootstrap/provider execution |
| Packaging/routing contracts | 11 PASS |
| Original installer/JCA recovery cases | 21 PASS on host, including failed/interrupted recovery, retained-helper denial, anti-downgrade and disposable userdata sentinel |
| Original module authentication | PASS: original RSA and native verifier, 78 candidate / 76 recovery signed files; no key/verifier replacement |
| Actual downloads | PASS: CRC, outer/APK/component SHA-256, all 7,622 candidate / 7,614 recovery payload hashes, exact signed authorities/catalogs |
| Full-skin Linux renders/actions | PASS selected normal/Slim synthetic-media checks at representative cover/inner sizes; native Info and real generated-clip Play/Trailer decoding/return exercised |
| Search required acceptance | **2 FAIL, retained**; Crew attribution remains separate, no stale-results/security bypass |
| Favorites missing-entry attribution | **UNCONFIRMED**; phone collection/API/container observation missing |
| Android/Fold install, recovery, touch, routes and visual acceptance | **NOT RUN / PENDING**; no compatible connected target |

Linux uses upstream Kodi 21.2 with an explicit source-bound responsive projection,
not the signed Infinity ARM64 engine. Screenshot/manual review is genuine host
evidence, not physical acceptance. Original palette changes were exercised live.
The gesture guide uses text/dividers rather than the reference finger illustrations;
poster/metadata differences and native parent row remain. Alternative views retain
their unique layouts. **Pixel equivalence, universal all-view design matching and
physical Fold acceptance are not complete.** Initial clipped-action failure and
earlier fixture failures remain recorded. Scudo memory, unrelated ANR/Home and
settings-retirement work are not repaired by this candidate.

No shutdown/application suite ran during packaging. The download verifier's first
459 attempt ran out of local disk while saving evidence; only disposable Linux
fixture copies were removed, then the same downloaded archive was reverified
successfully. No integrity/signing/recovery failure was waived.

## Forward recovery and physical procedure

1. Keep both verified APK downloads available. Check actual installed package,
   certificate and version first. Install-over requires the matching certificate
   and a lower current version; do not force a downgrade or uninstall/reset.
2. Test 2103458 only as a controlled candidate, using the [Fold checklist](FOLD-CHECKLIST.md)
   for drawer destinations, Favorites, native file playback, global views, actual
   provider metadata, Light/Dark, taps/hold/Back and fold/orientation changes.
3. If recovery is needed, use normal protected saving/close handling, then apply
   **2103459**, which is higher than 458. Do not bypass unresolved checkpoints,
   force-kill, clear data or promise recovery of unsaved in-memory writes. If
   protected close cannot complete, retain diagnostics and stop that procedure.
4. Recovery advances authenticated module/skin generations (59/256 to 60/257;
   combined generation 44 to 45). Original installer/signature/downgrade gates
   remain. Retained candidate helper files cannot enter restored routes or pass
   the restored authenticated first-party import contract; they are not deleted.
   Host evidence is not a sandbox guarantee against deliberate arbitrary scripts.
5. Confirm restored functionality and existing data on the Fold. This physical
   recovery step remains PENDING. After 459, 458 is lower; future testing needs
   another higher-version verified candidate. Do not attempt a lower-version
   reinstall. User acceptance alone may authorize promotion/lock.

Machine-readable delivery details and component checksums:
[DELIVERY.json](packaging/DELIVERY.json), [SHA256SUMS.txt](packaging/SHA256SUMS.txt).
