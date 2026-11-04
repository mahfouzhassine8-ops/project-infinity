# Controlled UI454 and forward-recovery 455 delivery

Both requested original-key-signed testing APKs were produced, downloaded and independently verified. Neither was installed, accepted, promoted or locked. Scudo remains unresolved. The separate Search audit is not included in either APK.

Base: exact signed 2103453, SHA256 `08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8`. UI source remains `1cc7684bd05581c21f31682cdb0f2d4e156a585e`; readiness remains `fd8a7dbace118a908508f324a5a8ba0a70d765aa`.

| Artifact | Signing source | Original signing run | Downloads |
|---|---|---|---|
| 2103454 UI test | `8986dfa23e387b4597f19feca54d9388f7512ba8` | [41900547905](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41900547905) | [APK ZIP](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41900547905/artifacts/13359155363) · [Matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41900547905/artifacts/13358915535) |
| 2103455 forward recovery | `03d788a78481911a9648fa1c4a30e6e4424d022e` | [41901526958](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41901526958) | [APK ZIP](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41901526958/artifacts/13358381510) · [Matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41901526958/artifacts/13358161664) |

The APK ZIP contains the actual `.apk`, signing receipt and complete preservation inventories. Components contain `INFINITY.zip`, `COBRA.zip`, `MINIMAL_ANDROID_CONTRACT.zip`, `CHOOSER_SHELL.zip`, catalog and checksums. These artifacts currently expire February 2, 2027; retain both APKs and evidence offline before any separately approved device test.

| APK | SHA-256 |
|---|---|
| 2103454 | `db8dd757343d2e321b4f0964e99dd479017d3f52428e85f982685acaf36945fa` |
| 2103455 | `1065bc5e26ed06f62cedd483597ba5cb41d4917222ffbc304d93be70e7648772` |

Full APK/component hashes: [SHA256SUMS.txt](SHA256SUMS.txt), with files grouped under `2103454/` and `2103455/`. Each artifact also includes its own checksum file.

Original certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. One original 4096-bit RSA signer; v1/v2/v3 signatures verified on the actual published APKs. Package remains `com.projectinfinity.kodi`, ARM64. All manifest fields except versionCode are unchanged. The unchanged signing workflow checks 16 KiB native/4-byte ZIP alignment after signing. These establish package compatibility, not successful Android installation.

## Exact preservation

Both published APKs passed byte comparisons against signed 2103453. All **7,602 protected existing members, five DEX files and 47 native libraries** are byte-identical, including Cobra, Infinity Preview, shared/chooser code, providers/add-ons, player and shutdown/checkpoint code. No user profile was opened or modified.

Native engine SHA-256 remains `d0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98`. No native Kodi rebuild occurred.

2103454 has exactly **19 authorized payload changes**: 12 changed existing members and seven additions. 2103455 has only **eight metadata changes** against 453 and no added payload members; functional code is restored exactly. [Every authorized member and exception](EXACT-MEMBER-ALLOWLIST.json) is enumerated. Every before/after payload hash is in each APK artifact under `preservation/ALL-APK-MEMBER-HASHES.json`. Independent reports: [454](evidence/published454/PUBLISHED-VERIFICATION.json), [455](evidence/published455/PUBLISHED-VERIFICATION.json).

Only the three original signing entries (`META-INF/MANIFEST.MF`, `META-INF/INFINITY.SF`, `META-INF/INFINITY.RSA`), APK v2/v3 signing blocks and ZIP alignment/packaging metadata are additional exceptions. Signing blocks are not ZIP members. No broad META-INF exception is allowed.

Production UI source remains exactly the approved checkpoint. Packaging source changes are confined to this directory, the existing trusted workflow, its exact authority-branch selector and release-authority records. The original signer, ownership engine, installer, security policy, accepted registry and recovery locks remain unchanged.

## Authentication and forward recovery

| Generation | UI454 | Recovery455 |
|---|---|---|
| APK versionCode | 2103454 | 2103455 |
| Command Center | 0.3.5.55, 77 signed files | 0.3.5.56, original 76-file functional inventory |
| Skin | 1.0.5.252, 948 protected records | 1.0.5.253, original 942-record functional inventory |

Both actual module signatures verify with the unchanged original key; every recorded file and skin hash matches. Original installer, native authentication, downgrade and unknown-local-edit checks remain unchanged. Issuance authority advances to generations 40/41; the accepted pointer does not move.

All **20 host recovery checks passed**: interruption after source replacement but before manifest commit, continuation with the same recovery, old-generation refusal, signature tampering rejection, refusal to overwrite unknown local edits, generation backups and retained disposable user data. These execute original installer logic with host platform adapters, not Android. [Evidence and limits](evidence/published455/RECOVERY-VERIFICATION.json).

Recovery excludes all seven candidate-only members. The unchanged installer may retain old installed files. The leftover `media_view.py` is rejected by the restored authenticated import contract; baseline source has no routes to the new skin helpers/dialogs; the three modal dialogs have no automatic visibility. No destructive cleanup is introduced. This proves normal-entry unreachability, not a sandbox against deliberate manual RunScript/ActivateWindow calls or arbitrary third-party execution. Actual Android skin generation/window selection remains pending.

Before a separately approved installation, retain verified recovery 455 offline and confirm the phone's installed package/certificate/version, free space and APK hashes. Finish ordinary saving and safe normal closure. An unresolved checkpoint or durability obligation blocks replacement; do not force-kill or bypass it.

If UI454 fails, recovery 455 installs forward over 454 after safe normal closure and restores 453 functional code with higher authenticated generations. Never downgrade to 453/454, uninstall, clear data or edit databases. After 455, a later UI test requires a newly authorized higher version. Verify installed module/skin selection and retained data on the phone. An APK cannot recover unsaved in-memory writes.

## Verification limits and physical checks

- Reused source evidence retains exact byte bindings: 55 cumulative host cases and 145 Linux fixture assertions; the final source continuation ran 39 cases. These are not Android workflows. [Source results](../infinity-kodi-2103453-ui-navigation/RESULTS.md).
- Nine packaging host tests and 20 host recovery checks passed. [Preparation 41898723487](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41898723487) authenticated both generations. Both signing runs and independent published APK/component checks passed.
- Earlier preparation failures stopped safely and remain recorded: ref-name parser ambiguity and relative-path verifier invocation. Wrapper corrections preserved the original checks. A local out-of-workflow check was refused as designed; official CI ran the gate. Local extraction exhausted disk capacity, then complete official bytes were verified in memory. No protected baseline was deleted.
- No compatible connected Android target is exposed. Install-over, recovery, actual service/skin startup and Fold UI acceptance remain **PENDING**, not PASS. No known-broken emulator was restarted.
- Sports requires the existing configured supported route. Downloads remains subject to existing Android permissions. No new storage permission or substitute provider was introduced.
- Search is unchanged. Scudo and independent native issues are not fixed. Unselected shutdown behavior was not newly tested.

Use the [physical Fold checklist](../infinity-kodi-2103453-ui-navigation/release-readiness/FOLD-ACCEPTANCE.md): cover/inner and portrait/landscape; global List/Posters/InfoWall/TriPanel across providers/pages/Back/refresh/reopen; registered fallbacks; artwork/details; one-tap X and Back/focus; Navigation/Library; authorized downloaded-video playback through Kodi and return to the folder. Installation and final acceptance remain separate user decisions.

No installation, promotion, acceptance, automatic lock, data clearing or recovery-baseline overwrite occurred.
