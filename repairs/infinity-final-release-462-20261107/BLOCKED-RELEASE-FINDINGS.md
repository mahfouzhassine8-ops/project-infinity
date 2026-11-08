# Signed 2103464: exact release blockers

**Disposition: hold candidate and recovery.** The latest selected Android run failed with a genuine native heap abort. Corrected-baseline dark-mode visual review also failed. No public APK/recovery publication or accepted-baseline change occurred.

## Evidence identity

| Item | Exact identity |
| --- | --- |
| Android run | [42437719318](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42437719318), job128600072991, conclusion failure |
| Test source | `152ae1bed123894af9669640edd2f6508cd80996` |
| Result artifact |13601500225; SHA256 `026afc06cb8c306dbd4c7c6fb1d82d6b73b0866b0b4883df0c96484c56d12726` |
| Signed2103464 APK | SHA256 `eb4ea5594d18d83c5638d10c0c1b22b2124e6c61c303d41908108dcd02b6ae54` |
| Exact candidate engine | SHA256 `6fc35b8718621ef2e941540b8c858d7d7cd7f408c810ed2fd0d14f7031e8fbb7` |
| Target | Stock Android17/API37.0, x86_64 with advertised ARM64 libndk_translation, 4KiB pages; not physical Samsung/Fold acceptance |
| Existing component fixture | Authenticated CC61/skin268 and exact existing Compat0.8.2. All six compatibility files, theme publication, UID/data sentinel and all 78 live signed module files verified. |

## Native heap abort

Seven complete Search cycles were recorded: The Matrix, Just Friends, Inception, Toy Story, Spirited Away, Finding Nemo and Re:zero. Eighth query SpongeBob/TV returned seven native Umbrella rows and one WatchNixtoons2 row. Offline review confirms exact query/media in all eight saved result snapshots; these were not a previous query's page.

Last request: QA sequence192, select row1, unchanged Umbrella native `tvSearchterm&name=SpongeBob` route. No matching reply followed. At **2026-11-08 02:36:12.944 UTC**, Scudo reported an invalid chunk state on deallocation and raised **SIGABRT** in PID4925, thread5135 (Thread-3). Android recorded process death at 02:36:14.408; the final screenshot shows the launcher. The host later reported select-row timeout because it checked the PID only before/after replies. The native abort preceded that timeout.

The [33-frame native stack](evidence/android-42437719318/NATIVE-CRASH-464.txt) passes through Python-callable getInfoLabel, GetMultiInfoLabel, shared-pointer release, CGUIListItem destruction and string/map deallocation. [Exact-engine symbolication](evidence/android-42437719318/ADDR2LINE.txt) resolves:

| Address | Source failure site |
| --- | --- |
|0x1d86084 | xbmc/GUIInfoManager.cpp:11119; shared-pointer cleanup in GetMultiInfoLabel |
|0x1b15478 | xbmc/guilib/GUIListItem.cpp:51; list-item destruction |
|0x1695f9c | xbmc/interfaces/legacy/ModuleXbmc.cpp:308; Python-callable label read |

These files and reviewed item/container helpers match the exact462 authenticated source map. Concurrent ownership/lifetime or earlier corruption are hypotheses; the corruption writer and minimal safe fix are **unproven**. Observer and ARM translation involvement remain possible. This is neither a demonstrated Fold reproduction nor a proved emulator-only defect. There is no evidence proving Input.Select was delivered; the accurate description is a failure during the eighth heading-navigation check.

## Dark-mode visual failure

Manual [front dark](evidence/android-42437719318/front-yes-home.png) and [inner dark](evidence/android-42437719318/inner-yes-home.png) review fails: cards are white with white/pale text. Effective/native theme are both dark, readiness flags true, card-surface label F5000000 and primary text FFF7FBFF. Home, variable and palette source remain byte-identical to authenticated268.

Exact existing Compat0.8.2 restores missing effective-theme publication and correct light background. [Front light](evidence/android-42437719318/front-no-home.png) and [inner light](evidence/android-42437719318/inner-no-home.png) have readable navigation text. Dark cards remain unresolved. Original JSON layout_snapshot PASS means captured, not approved. Full approved-UI and white-line acceptance remain unpassed.

## Required continuation

1. Establish the corruption/lifetime cause and a narrowly scoped repair. Preserve the failure; do not delete the observation or retry the unchanged candidate to seek a lucky pass. No speculative shared GUI/lifecycle patch has been applied.
2. Establish why dark cards render light despite correct theme/palette labels. No verified protected UI/palette fix exists.
3. Before a future selected run, require decoded exact Search query/media in readiness and check the original PID while awaiting replies. Current snapshot identities were checked offline; no new application test is implied.
4. After a causal repair, complete eight Search cycles and heading navigation, watched/unwatched, actual native Info Play/Trailer, Downloads/white-line review and actual forward recovery. These later checks were **NOT RUN** after the abort.
5. Only after all engineering/visual gates pass, package one matching recovery and publish the consolidated APK, recovery, checksums and report. Keep one final Fold acceptance test afterward.

Internally signed recovery2103465 passed independent signature/full-member checks and original Java installer host cases; actual Android forward recovery is unexecuted. A recovery ZIP has not been delivered as complete. Cobra, Preview, third-party providers, protected UI source and unrelated code remain preserved. No user data reset, user-device installation or new phone diagnostic request occurred.

[Machine-readable findings](BLOCKED-RELEASE-FINDINGS.json) bind screenshot/native evidence, exact source hashes and all partial results. [VERIFICATION.md](VERIFICATION.md) summarizes completed engineering. Earlier eight-cycle evidence from run42435881141 remains separate and cannot override the corrected-baseline failure.
