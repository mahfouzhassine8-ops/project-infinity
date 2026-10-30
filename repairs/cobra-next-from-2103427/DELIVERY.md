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
- Independent downloaded-byte verification passes: original v1/v2/v3 certificate signatures; four matching ZIPs and five ordered DEX files; original Infinity module authentication; exact protected contract; all 47 native libraries unchanged, including 16KB ZIP-offset alignment for the three stored native libraries. All stored ZIP members meet four-byte alignment. These are ZIP checks, not ELF LOAD/RELRO segment-alignment acceptance.
- Infinity ZIP is exact locked 2103427. Shared executable DEX/classes, manifest identity, persistence, original artwork and non-icon payloads remain frozen. The resource exception stays under its existing owner. Chooser DEX and second Cobra DEX are unchanged from 429/430. Relative to 430, only the component version class, version metadata and two light XMLs change.
- Previous 429 layout, gesture, logo, reflow and performance evidence remains retained with its original scope; those implementations are unchanged. No shutdown modifications or tests occurred.
- Exact signed-431 [Android run 40973858059](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40973858059) confirmed native Fullscreen, then failed after a measured More coordinate produced actual system PiP. QA had revealed controls after measuring, causing a native layout request without a fresh target observation. The actual final recipient is undetermined. The failed result remains preserved; [evidence and review](results/runtime/candidate31-first-actions/REVIEW.md). The earlier 40972601469 install-client timeout occurred before Activity launch and is retained separately.
- Visually inspected Android 17 App Info frames show the approved black-on-white light variant and original navy/cyan dark variant. Actual Pixel Launcher All Apps shows the light variant, then retains its light bitmap after switching to dark despite correct framework/App Info selection. This establishes an observed launcher refresh limitation, not automatic parity across all surfaces.
- In [run 40975572601](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40975572601), the fresh-target guard stopped before pressing More: the extra reveal changed its visible bounds from `[858,743][1016,911]` to a five-pixel edge fragment, while PiP moved beneath the old coordinate. Fullscreen again passed. [Measured evidence](results/runtime/candidate31-fresh-target/REVIEW.md). [Focused check 40976739449](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40976739449), QA source `8146d518eedecb22cd417785f88aa10ce2a9d608`, stopped before its first Fullscreen press: host accessibility-query overhead exceeded the strict 3.5-second freshness guard. No button action ran; [timing evidence](results/runtime/candidate31-host-timing/REVIEW.md).
- [Run 40979186412](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40979186412), QA source `0ed6848b3031ae512705e81804fe58538232de19`, **FAILED before Activity launch, icon probes or the native helper**. `install.txt` records `PerformingIncrementalInstall` and `Success` at 22,401ms; hashing the installed 778MB APK then exceeded the then-existing 30-second ADB timeout. This is not an application failure or a native-helper runtime result. [Incremental-install/hash evidence](results/runtime/candidate31-incremental-hash/). The narrow QA correction used `--no-incremental -r` for the same APK, requiring its full transfer before install success; official AOSP behavior and peer review were checked. That correction added no install retry, timeout increase or hash-guard weakening.
- [Run 40980338717](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40980338717), QA source `f0cc061cedd9fedb6e04bbf03dbd6c1d9ea97649`, **FAILED before launch**: the 30-second full-stream install was truncated after 541,530,240 of 778,358,062 bytes. The native helper, icon probes and button actions did not run. [Stream-truncation evidence](results/runtime/candidate31-stream-truncation/).
- Explicit management clarification subsequently authorized an appropriate QA infrastructure budget only for nonincremental APK installation and complete installed-file SHA256: APK size at 10MiB/s plus 45 seconds, capped at 120 seconds (120 seconds for this APK). Generic ADB stays at 30 seconds; the application control timer stays at four seconds, native coordinate freshness at 3,500ms and attempts at seven. No hash guard was weakened, and CI uses no compressed or staged APK transport.
- Run [40981874553](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40981874553) **FAILED at the first-screen observer**, after full regular installation and exact installed-APK SHA256 passed in 94.241 seconds. Cobra launch returned `Status: ok` (`TotalTime` 4,090ms). An Android-owned **Android App Compatibility** notice covered the app: its ELF LOAD/RELRO segment alignment checks failed, and Android selected page-size compatibility mode. All 47 native libraries are unchanged. ZIP-member alignment checks do not establish ELF segment alignment or general native 16KB compatibility. [Preserved notice and launch evidence](results/runtime/candidate31-compatibility-modal/). The native helper, icon probes and selected button actions did not run there.
- Run [40983247126](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40983247126), QA-only source `560d54b1c3d99f7e7256b4b326706144fa341585`, is **IN PROGRESS** against the identical original-key signed 431 APK. The QA harness preserves the exact known Android notice and acknowledges **OK** once; it does not select **Don’t Show Again**, change compatibility settings or modify native code. The two-class native helper queries fresh public bounds and injects actual coordinates in one device process under the unchanged 3,500ms freshness guard. Its actual runtime and complete button journey remain pending; compilation and review are not runtime acceptance.

| Requirement | Host | API37 emulator | Physical Fold |
|---|---|---|---|
| Fullscreen → Fullscreen | PASS — production-view routing, terminal spy | PASS — native fullscreen observed in 40973858059 and 40975572601 | NOT RUN |
| More → original More menu | PASS — production-view routing, terminal spy | PENDING — complete journey not yet verified | NOT RUN |
| PiP → system PiP and return | PASS — production-view routing, terminal spy | PENDING — PiP was observed after an uncertain earlier target; dedicated PiP/return journey incomplete | NOT RUN |
| Light App Info icon | PASS — API35 native resource rendering | PASS — reviewed white background / black original emblem | NOT RUN |
| Dark App Info icon | PASS — API35 native rendering matches original dark pixels | PASS — reviewed navy background / cyan original emblem | NOT RUN |
| Automatic launcher refresh | PASS — day/night resource selection; no launcher-refresh claim | LIMITATION — Pixel Launcher All Apps retains the light bitmap after the observed dark switch | NOT RUN — Samsung launcher/Finder/suggestions unverified |

The button host results come from six interaction tests and three adjacent regressions, with explicit terminal spies. The new on-device QA helper compiled to a DEX JAR containing two QA classes and passed inspection plus peer review; the intervening installation/hash failures never executed it. Its runtime result remains pending in [40983247126](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40983247126), QA source `560d54b1c3d99f7e7256b4b326706144fa341585`. The preceding run reached the Android compatibility notice but did not execute the helper. Compilation and review do not certify application behavior.

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
