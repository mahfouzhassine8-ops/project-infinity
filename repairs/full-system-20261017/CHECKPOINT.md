# Infinity — consolidated repair checkpoint (2026-10-17)

**User authorization:** Proceed with the previously approved full five-workstream repair. This checkpoint is an experimental working branch, **not** a new APK, accepted skin lock, or physical-device acceptance.

## Protected source and installed-state foundation

- Locked physically accepted APK: **2103377 TEST4**, SHA-256 `bcdcbed5aeaed0bf30e6e590d9ceda7c0177d780b12e98773fa9503beb793286`.
- Locked skin: **1.0.5.223**; installed experimental skin: **1.0.5.225** (the full user ZIP SHA-256 `8ca8fc72ce24ae88d558d06485345ec37a2cd491ebea5805e169d84acf8ed235`).
- Installed experimental APK: **2103382 TEST3**, `com.projectinfinity.kodi`, permanently signed; **no APK was rebuilt or signed during this checkpoint**.
- Preserve Rails helper 0.2.6, Command Center 0.3.5.20 and all databases, provider settings, Diggz contents, watched history, Cobra, playback/PiP/ambient/bkgd behavior.
- Full user-approved master brief remains the scope. **Do not drop any workstream or overwrite locked branches.**

## Workstream 1 — Native shutdown and Android stability

Latest **physical Fold** evidence: `Infinity-Diagnostics-20261017-055309.zip`. Exact coordinated Close receipt: `CHECKPOINT_FAILED` after **2513 ms**, `native_admission: protected_durability_failed:.../.kodi/addons/temp/1c160b3d-5630-4c50-a1cc-d6d1c995312f/16x9`. The earlier attempt failed on the **25-second** owner/deadline gate. Command Center and several other essentials had committed in the 2.5 s run, but overall final checkpoint and process-death authorization were not confirmed. Job history shows failed/verified add-on install transactions for Infinity skin and an EPG add-on.

Source audit found `InfinityProtectedWrites.h` treated an already-removed installer UUID parent as a durability failure, because `SyncProtectedPath` tried to fsync the immediate missing parent. This is a **hypothesis for the exact failing syscall**, since the diagnostics record path but not errno/stage. A narrow source candidate now syncs the first existing ancestor **only inside a trusted, profile-bound UUID installer-staging root**, after verifying that intermediate directories are absent. Missing profile/database directories, symlinks, malformed stage names, and absent staging roots remain fatal. The native host regression compiles the real header and tests those positive/negative cases.

**Not yet done:** verify native source integration against the exact 2103382 binary manifest; diagnose the independent 25-second failure; compile/verify a full ARM64 native candidate if the targeted correction remains supported; sign a higher-versionCode APK only if required; physically test Close/reopen and preserved data on the Fold. This is not proof that shutdown is fixed.

Preserve the proven OnJobComplete lock-inversion correction and all existing lifecycle/PiP/session behavior.

## Workstream 2 — Resume Hub, watched, Watchlist and Collection

The user confirms .225 restored visibility of Continue Playing and Resume Hub. Retain that.

Outstanding: Continue from **2:00** must actually begin at the saved position; prove the selected identity, source readiness, seek and actual player position after source resolution, close/reopen persistence, and feedback for unseekable sources. Existing Command Center `plugin.py` advertises `ResumeTime`/`StartOffset` and `setResolvedUrl`, but that alone does **not** prove the provider preserves or applies the offset. Do not invent success or overwrite the installed CC controller: the Fold installed-code hashes must be checked before changing any CC file.

Keep blue watched, mark watched/unwatched, Watchlist, Collection and identities consistent. Do not reset data.

## Workstream 3 — Player / long-press / add-on recovery

Confirmed source-level regression in exact installed .225 full ZIP: `unified/VideoOSD.xml` places a `PlayerControl(Repeat)` button with ID 265 where the approved responsive/16x9 Fold player still has Rotate button ID 263. The previous UI actions are:
- Android `PLAYER_ROTATION_UNLOCKED` when Follow Device/white.
- Android `PLAYER_ROTATION_FOLLOW_DEVICE` when Infinity-controlled/cyan.
- Existing `Infinity.PlayerRotationUnlocked` visual toggle.
- Repeat retained separately in `PlayerControls.xml`.

An isolated **full .226 experimental Rotate correction** has been assembled locally from the exact .225 ZIP; code is stored in `repairs/full-system-20261017/player_rotate_226.py`. The builder validates the old parent by SHA, requires exact control anchors, changes only unified VideoOSD, addon version and protected manifest, and retains every other ZIP member's uncompressed bytes. No skin has been installed or accepted on the physical Fold yet.

Outstanding: Continue Playing/Resident Evil press-and-hold menu routing through actual Home/Resume Hub controls, add-on rail parity, Otaku disabled-add-on recovery, and physical Rotate state/rotation/Repeat tests.

## Workstream 4 — Skin polish

Keep the Phase D .225 work and six successful signed-APK cover/inner/wide render jobs (`39020658216`). Those tests do **not** certify the player rotation action, Close or provider-resume seek. The .226 Rotate candidate remains experimental; full end-to-end skin physical approval pending. Do not revert .225 or redesign working screens.

## Workstream 5 — Integration / acceptance

Use signed Infinity rather than stock Kodi/Estuary for release authority. Reuse green source/runtime tests. Test upgraded Diggz+skin+user-data scenarios, not only disposable fresh installs. All prior red tests stay reported. Requires backup/rollback, correct permanent signing, actual Fold Close with full owner proof/engine death and data persistence, touch, resume seek, background 5/20/45/90 minutes, screensaver, PiP and Fold state changes. **Final Lock requires explicit user approval.**

### Current work status

- **Native installer staging durability candidate:** source committed; targeted real-header host tests green; **no signed APK or Fold proof**.
- **Rotate/Repeat mapping candidate:** isolated full skin .226 builder and source-level checks; **not installed or Fold-approved**.
- **Long-press, Resume Hub seek, remaining missing features, 25-second shutdown failure:** open and retained.
- **No data wipe, uninstall, release lock, production APK modification or silent baseline reset.**
