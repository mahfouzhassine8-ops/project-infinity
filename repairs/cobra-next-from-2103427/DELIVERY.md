# Consolidated 2103431 install-over candidate

Contains the Cobra player-button repair, density-safe automatic light/dark Infinity launcher resources, and all retained 2103429 improvements. **2103430 is superseded before delivery.** Physical Fold acceptance belongs only to the user. No phone installation or accepted-lock promotion occurred.

## Downloads and source

- [One original-key signed APK](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971769136/artifacts/12940184150): `Infinity-2103431-Combined-Original-Signer.apk`.
- [Exactly matching four component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971769136/artifacts/12940139275).
- [Successful sole signing build 40971769136](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971769136).
- Signed source: `9ccc4c362a65118eeba38a8e7e4b0de5723c69af`. Tested owner producer: `b41d51daa8b32dfee265dc9ea0abf844bff8f44e`, [successful CI 40971144336](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40971144336). Production files match exactly between these commits.
- Package `com.projectinfinity.kodi`, versionCode **2103431**, 778,358,062 bytes. Original certificate and package identity retained. The normalized manifest changes only its typed versionCode. Install-over identity/signature/version compatibility is verified; installation over the user's populated device remains untested.
- Chooser labels: Infinity **Version 2103427**, Cobra **Version 2103431**, App version **2103431**. Existing Version wording, chooser code, selection preferences and behavior remain unchanged.

## Corrections

Pro previously dispatched Fullscreen/More through indices into a hidden preview row whose More button had moved. It now resolves the original native action views by identity. Existing listeners, player/PiP/menu bodies, Pro appearance, ordering, hitboxes and retained non-Pro ordering remain intact.

| Visible button | Signed 2103429 host reproduction | Corrected production host result |
|---|---|---|
| Fullscreen | PiP | Fullscreen |
| PiP | PiP | PiP |
| More | Fullscreen | Original More menu |

Launcher resources use normal Android day/night selection for the existing icon IDs. Light is white with the original emblem in black; dark selects the original navy/cyan assets byte-for-byte. Modern foreground alpha/placement are preserved; legacy densities resample the original mask to the established viewport. No aliases, component toggles, polling, startup hook, app-label change or separate CobraTV icon change.

During verification, unaccepted 2103430 exposed a real density-override defect: its inline white drawable color produced resource ID zero in `getDrawableForDensity`. Ordinary Settings App Info rendered it, while the launcher fell back to Android's default icon. The final nested white shape fixes that loading path. Only the two light adaptive XML payloads and genuine version data change from 430; the table, IDs, five light PNGs, dark assets and entire button implementation remain exact. [Correction and evidence](FOLLOWUP-2103431.md).

## Verification and preservation

- CI: six actual production-view touch/key tests plus three adjacent regressions pass. Signed 429 retains one expected route assertion failure with zero fixture errors. Coverage includes initial/retained Pro, scrolling, clipped targets, resizing, remote activation and synthetic Sports ordering. Terminal fullscreen/menu/OS-PiP boundaries are explicit host spies.
- Nine offline icon checks, Android aapt2 parsing and one native-framework test pass. The native test renders both IDs in day/night at default/420 density: sixteen baseline/candidate renders, exact original dark pixel comparison, black-on-white checks, and required signed-430 ResourceID0 negative control. This is API35 host rendering, not Samsung acceptance.
- All 23 release controls pass in the successful signing job, followed by fresh actual-APK owner/resource gates before key access.
- Independent downloaded-byte verification passes: original v1/v2/v3 certificate signatures; four matching ZIPs and five ordered DEX files; original Infinity module authentication; exact protected contract; all 47 native libraries unchanged, including the three stored native libraries aligned to 16KB. All stored ZIP members meet four-byte alignment.
- Infinity ZIP is exact locked 2103427. Shared executable DEX/classes, manifest identity, persistence, original artwork and non-icon payloads remain frozen. The resource exception stays under its existing owner. Chooser DEX and second Cobra DEX are unchanged from 429/430. Relative to 430, only the component version class, version metadata and two light XMLs change.
- Previous 429 layout, gesture, logo, reflow and performance evidence remains retained with its original scope; those implementations are unchanged. No shutdown modifications or tests occurred.
- Exact signed-431 [Android run 40973858059](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40973858059) confirmed native Fullscreen, then failed after a measured More coordinate produced actual system PiP. QA had revealed controls after measuring, causing a native layout request without a fresh target observation. The actual final recipient is undetermined. The failed result remains preserved; [evidence and review](results/runtime/candidate31-first-actions/REVIEW.md). The earlier 40972601469 install-client timeout occurred before Activity launch and is retained separately.
- Visually inspected Android 17 App Info frames show the approved black-on-white light variant and original navy/cyan dark variant. Actual Pixel Launcher All Apps shows the light variant, then retains its light bitmap after switching to dark despite correct framework/App Info selection. This establishes an observed launcher refresh limitation, not automatic parity across all surfaces.
- In [run 40975572601](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40975572601), the fresh-target guard stopped before pressing More: the extra reveal changed its visible bounds from `[858,743][1016,911]` to a five-pixel edge fragment, while PiP moved beneath the old coordinate. Fullscreen again passed. [Measured evidence](results/runtime/candidate31-fresh-target/REVIEW.md). The unchanged APK is now undergoing [focused check 40976739449](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40976739449), QA source `8146d518eedecb22cd417785f88aa10ce2a9d608`. It reveals once, observes, scrolls if needed, then immediately presses the freshly observed target with no extra reveal or screenshot. **IN PROGRESS**; no result is presumed.

Samsung launcher/app drawer/Finder/suggestions, monochrome palettes, physical fold/window behavior and populated install-over acceptance remain user-device checks. Pixel Launcher demonstrably cached its light bitmap across the observed dark switch; framework resource selection does not guarantee universal surface refresh. No unsafe cache-reset or component workaround is included.

No new device-speed, FPS, CPU, thermal or long-running memory claim is made. Prior host work counts remain preserved: 7,000 identical layout requests become zero, and 100 cold duplicate-logo submissions become one. These are host fixture results, not measured Fold gains. See [performance](PERFORMANCE.md), [completion ledger](COMPLETION-LEDGER.md), and [independent verification](results/signed2103431/INDEPENDENT-VERIFICATION.json).

## SHA256

```text
3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471  Infinity-2103431-Combined-Original-Signer.apk
36ca822a886b5df4443c798c933a2c304a30be002c10b4284f6b2ed7934fe912  CHOOSER_SHELL.zip
98583b7a935103c8d13744fc624a6005f0566b1e3d26a47f240295cafd21cae7  COBRA.zip
16eeb91a24bf0cf99d558d9e3dd17aedfd127e9a1936dcce413341c48683cd6c  INFINITY.zip
432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8  MINIMAL_ANDROID_CONTRACT.zip
```

Original certificate SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. [Machine-readable checksums](results/signed2103431/SHA256SUMS).

Artifact downloads require repository access and expire on 2027-01-27. The original signing identity is permanent; artifact retention is separate. Approved 2103427 remains `782242090483982c39a78f9c4da932a4751bdafc`; protected 2103425 remains `db730100a3bfea7e06d2e6c3434e89aeb6fa8a15`. Neither lock was changed.
