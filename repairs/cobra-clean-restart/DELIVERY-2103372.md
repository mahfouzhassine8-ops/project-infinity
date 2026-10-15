# Cobra 2103372 — Permanently Signed Test Delivery

Date: 2026-10-12. Continued from saved checkpoint `4583f403521dbcc7f4d9734d9f750b9dd64b3824` on the existing branch. The implementation was not restarted.

**Status: automated/source/package gates passed; signed APK delivered for user testing. Physical Fold acceptance remains pending. No installation, release lock, baseline replacement or production promotion was performed.**

## Exact test artifact

- File: `Cobra-2103372-Six-Verified-RC1.apk`
- Package: `com.projectinfinity.kodi`
- Version: `1.0.9-Cobra-Six-Verified-RC1 (2103372)`
- APK bytes: `159257399`
- APK SHA-256: `266085eab9bf881494c26dd34f6e97f3ce62f8d6b4cd8fc851e920f92bea4d92`
- Permanent signer certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- Tested/built source commit: `89de52c34d9077adf643f2e6430a2eff67a460a5`
- Branch: `work/cobra-clean-restart-20261012`
- Successful final workflow: `38225099698`, job `114730548134`
- Signed APK artifact: `11736396460`; ZIP SHA-256 `812743b12b9e3af900ff0020e2583725c9e2d79a127ca1be57e79538eff81869`
- Full verification artifact: `11736536292`; ZIP SHA-256 `82188dba3f3d2d7cb268055e4d08c998be8639fc5f2920526e3fe8c13546d39c`

The APK and evidence ZIPs were downloaded after completion. Both ZIP SHA-256 values matched GitHub and both CRC checks passed. The extracted APK SHA-256 and byte count matched the final CI receipt.

## Executed verification

All **193 tests passed**, with **zero failures, zero errors and zero skips**, across 12 suites. This includes all 167 inherited preservation cases, all 18 existing corrective cases, and eight supplemental delivery cases. Independent JUnit parsing confirmed that all 185 saved class/test names remain present. Inherited test source provenance is unchanged; no required case was removed or waived.

The existing 48-combination fullscreen Channels audio matrix, all-mode mini/fullscreen PiP return checks, unsupported-PiP fallback, Pro-only isolation, Groups rendering, original playback/rewind/Multi-View/ambient regressions, and saved-state recreation checks passed again.

Additional delivery verification covers actual horizontal touch scrolling and a held gesture, stale-to-fresh Stats transitions, spoiler changes while Stats is open, supported metadata and wrong-game/missing/pre-game guards, four complete broadcast rows with additional choices through row 12, exact Stats glyph pixels, six-mode theme/ambient transitions, Pro-header glyph contrast, and original Close behavior. Screenshots were inspected against the recovered approved Sports reference and the user's later corrections.

## Actual runtime failures corrected in this continuation

**Requirement 4 — Pro Sports Stats:** The prior new panel could retain detailed values after freshness or spoiler state changed, and it did not project available venue location and game situation. The corrected scoped panel uses the existing repository response, retains original detailed statistics/player-leader lines, adds optional home/away metadata and team comparisons, and respects existing freshness/spoiler predicates while the panel is open. Missing or mismatched metadata is not fabricated. Scheduled season averages are not presented as this game's live comparative boxscore. The new observer stops when its owning panel detaches; it does not introduce network polling or change the global sports refresh policy.

**Requirement 6 — Pro header:** Visual review found existing header icons remaining white on a light background. Only those existing Pro-header icon inks were updated to the active palette. Their glyphs, callbacks, placement and other modes remain unchanged.

PiP, Groups, unrelated tuning/audio-focus/call/background behavior, native engine, providers, skin, Command Center and shutdown implementation were not modified by these final runtime corrections. The prior permitted selective 2103370 PiP guards remain; the rejected complete build is not a parent and its prohibited menus were not imported.

Two apparent failures were confined to supplemental test fixtures: an integer ambient value was corrected to the established string preference, and a freshness receipt was moved from the uninstrumented test runner's wall clock into Robolectric's actual PAUSED-mode app clock. No production timing rule changed. A title-case Away/Home label correction retained the original test expectation rather than weakening it.

## Six-change delivery boundary

1. All phone modes: fullscreen video UI > Channels retains explicit user mute across All/Favorites/Recents/Groups and the supported Sports route. The new override is scoped to that initiating route; negative unrelated-tuning checks pass.
2. All phone modes: mini-player and fullscreen PiP controls use the existing platform/player handoff. Same-player, originating-mode and mute checks pass; unsupported-PiP initialization is corrected. Physical Samsung PiP remains a user test.
3. Pro only: fullscreen menus scroll horizontally without added direction arrows or instruction text. Non-Sports retains original items and relative order, with PiP as the only added control.
4. Pro Sports only: `Channels > Display > Multi-View > PiP > Stats > More`, exact approved mini-player Stats glyph, supported game information in mini/fullscreen Stats, original detailed leader/statistics content preserved.
5. Pro Sports fullscreen only: broadcast choices stay in the foreground; four complete rows are shown when available; all additional choices scroll and remain selectable; fewer-than-four uses only actual choices. Original matching and Back/Close ownership remain intact.
6. Pro only: existing header palette/glass/icon compatibility corrected without layout redesign or retheming another mode.

Mobile, Compact, Cards and TV Grid do not acquire the new Pro scrolling container or Stats control. Pro non-Sports does not acquire new Sports-only controls. Originally approved features in those modes are retained.

## Source and compiled-package preservation

Approved Cobra 2103324 source: `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3`; approval lock: `25497c4dfd6be8d83f32580495b16afb6eaed736`.

Retained 2103369 transport source: `9abf7c84fbd8224958bc8465c983429bc5976074`; exact APK SHA-256: `83128afbd2595dbf4053ded40ee1d22ae0d1c7b798f62dd9f077bd4d729261f4`.

Only `InfinityLiveActivity.java.in` and `CobraProUi.java.in` differ within the runtime archive. The other **262 of 264 runtime files are byte-identical**. Host build/test/review files are separately tracked and are not application runtime changes.

Exact final runtime source SHA-256:

- `InfinityLiveActivity.java.in`: `484b73bc677090a70667daa6c62e895402d4fed5a2f8dcdbe9a1f4e510d9f861`
- `CobraProUi.java.in`: `a096e19cb594752274ded0ea18a40a48f9e5ee55ad5e7f6caf474236d56372cb`

The JDK parser checked 3,131 original named-member records and inventories **100 changed/added records: 24 modifications and 76 additions, no removed original members**. Every record maps to requirements 1–6. Full bodies, including anonymous classes inside methods, are hashed; exact whole-source hashes also gate assembly. `CHANGED-MEMBERS.json` SHA-256: `81ffb47d2971ddb781e3216c2d95b0169e7baf9c8c4fd5ae6a10d12604c27b6b`.

The final package preserves **4,172 protected ZIP entries byte-for-byte**, including all assets, resources and **47 native libraries**. Native compilation did not run. JNI/native declaration contracts and Android resource IDs match. The manifest matches except the new version code/name; the APK is not debuggable. `lib/arm64-v8a/libkodi.so` remains `5d42d0d8ef6a90a5678fd7a24cc4e3b01e2375c213c590a92c178d7a34cc1113`.

**7,978 protected decoded classes** passed comparison, with no unexpected differences. Comparison resolves exact stateless D8 helper bodies and only normalizes string-encoding width and proven unreachable payload-alignment padding. Registers, data, branches, exception regions and executable instructions remain checked. The two allowed runtime families are additionally covered by the exact source/member gate.

Run `38224181197` assembled successfully but stopped before signing on two library alignment nops after terminal returns. Inspection proved unchanged executable/data content; the host comparator was corrected to recognize baksmali's sequential `:array_0` labels. Negative tests still reject reachable nops and changed values/targets. No application/library source changed to clear that comparator finding. Final run `38225099698` passed the corrected comparison.

## Permanent signature and independent download checks

All four existing permanent-signing settings were required; there was no debug/ephemeral-key fallback. CI apksigner verified the original and final APKs and the exact expected certificate. The final artifact verifies under v1, v2 and v3 and passes zip alignment. The eight existing META-INF v1 warnings are identical to the original APK; unrelated metadata was not deleted.

Independent local verification checked the exact downloaded APK hash/size, CRC, entry membership, all 4,172 protected entries, all 47 native hashes, and the same embedded public signer certificate. This local step is not a second apksigner cryptographic run; CI performed that verification. `Cobra-2103372-Independent-Verification.json` SHA-256: `4e017d13d96eed5022b317afcadabbf542c760b9d3f24515276099b57668b9c0`.

Final `DELIVERY.json` receipt SHA-256: `a8ea4723e90dd73d73fcbea65706986da46dc78e48fab1298ec1b83973fd39b1`.

## Installation and rollback boundaries

This is an update-over-install test candidate with the same package and permanent signer, not a separate cloned application. Keep the previous APK and use the APK as an update. Do not uninstall, clear data, force a downgrade, or replace rollback records. Any installer error must be reported and investigated without deleting user data.

The original approved Cobra 2103324 APK remains the provenance/rollback reference with SHA-256 `5af58f2e700e636cdc798cbde0acc89e8091153cfcf1e17c792375fe285dd8c3`. The compatible 2103369 transport artifact remains intact. Installing a lower version may require a separately reviewed data-preserving rollback procedure; no such downgrade was performed or authorized here.

## Physical Fold checklist — still required

- In Mobile, Compact, Cards, TV Grid, Pro non-Sports and Pro Sports: fullscreen > Channels > different channel, both muted and unmuted, including available categories. Then check unchanged Previous/Next/Last Channel, normal volume and mini tuning.
- Enter and return from both mini/fullscreen PiP. Check same stream/session, original experience, mute state, Back behavior and no duplicate surface. Exercise cover/inner display, rotation, split screen and a narrow floating window.
- Switch Pro Sports to every other mode and back. Only Pro Sports has new Stats; only Pro has the new horizontal fullscreen container. Check exact six-item Sports order, original Stats icon and no new scroll arrows/instructions.
- Open mini/fullscreen Stats with actual supported game data. Check logos, home/away, venue/location/time, score/period/possession, detailed stats/leaders, unavailable data, spoiler changes and delayed/fresh feed behavior. Fixtures and a read-only schema sample do not certify every live provider field.
- From Pro fullscreen > Channels > Sports, select another game with multiple broadcasts. Check four visible choices when available, scrolling extras, successful tuning and Back/Close with no obscured panel.
- Check Light/Dark/OLED/System, Ambient and Night Cinema header readability, unchanged control placement, normal playback/scaling, subtitles, rewind/timeshift, Multi-View, Favorites/Recents, navigation and settings.

Automated production-view tests control decoder/network/platform boundaries. Actual Samsung decoder, audio-focus/call, fold/multi-window and live-provider behavior is not certified by CI. Report physical results before any lock or promotion. Historical stop records and failed-run evidence remain preserved; this document records a test delivery, not a release acceptance.
