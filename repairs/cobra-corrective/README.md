# Cobra corrective test candidate — 2103371

Not locked. Not production-promoted. Physical Galaxy Fold acceptance is required.

**STOPPED AT PRESERVATION GATE.** Continuation from saved checkpoint `c3d5b03602e6e8edc275203491b572b8e1c26c77` reached runtime validation on commit `0c18474b13650f17740869c1156a2d885e7c713e`. Run `38206152159` passed 196/199 cases, including all 167 inherited cases and the approved-source routing comparison. Correctly sized tests exposed overlap between the new preview PiP target and an original control at 280x280. Recreation and the Groups workflow also remain unresolved. No APK was assembled or signed. Candidate metadata now blocks `prepare`; no gate or test is waived. See `BLOCKED-REVIEW.md` and `CI-RESUME-RESULTS.md`. All source and failed-run evidence are preserved. The 2103371 identity remains reserved only; no installation, promotion, physical acceptance or release lock is authorized.

## Foundation and preservation

The source of requirements is the user's latest **Astra Pro corrective handoff**, not the rejected 2103370 implementation and not older notes in the visual reference.

| Identity | Verified reference |
|---|---|
| Approved Cobra source | `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3` — 2103324 |
| Approval lock | `25497c4dfd6be8d83f32580495b16afb6eaed736` |
| Approved Cobra APK SHA-256 | `5af58f2e700e636cdc798cbde0acc89e8091153cfcf1e17c792375fe285dd8c3` |
| Retained transport source | `9abf7c84fbd8224958bc8465c983429bc5976074` — 2103369 |
| Retained transport APK SHA-256 | `83128afbd2595dbf4053ded40ee1d22ae0d1c7b798f62dd9f077bd4d729261f4` |
| Retained native library SHA-256 | `5d42d0d8ef6a90a5678fd7a24cc4e3b01e2375c213c590a92c178d7a34cc1113` |
| Permanent signer SHA-256 | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Isolated branch | `work/cobra-astra-corrective-20261012` |

`BASELINE-GATE-A.json` records all 254 approved runtime files, all 264 retained-transport runtime files, the 24 byte-identical Cobra-owned files, and verification of 2,175 tracked transport Git blobs. The retained transport already carries the exact approved Cobra files: there is no need to transplant rejected UI or downgrade the native engine. The original APKs and source directories are not edited.

The implementation is applied with a zero-fuzz patch to the verified 2103369 compiled-source archive. Only `InfinityLiveActivity.java.in` and `CobraProUi.java.in` may differ. `source_scope.py` must map every changed method or field to an authorized requirement. Native compilation is not part of this workflow.

## Six authorized changes

| Change | Allowed scope | Protected boundaries |
|---|---|---|
| 1. Preserve user mute during Channels selection | Phone fullscreen video UI → Channels, including its channel categories | Previous/Next, Last Channel, direct tuning, mini tuning, audio focus/calls, volume settings and background policy unchanged |
| 2. PiP buttons | Phone mini-player and fullscreen in every experience | Existing session, originating experience, player and lifecycle policy; no TV/onn changes |
| 3. Horizontal bottom menus | Pro fullscreen only | No arrows/instructions; non-Sports original controls/order plus PiP only |
| 4. Stats and game information | Pro Sports mini and fullscreen only | Exact fullscreen order: Channels → Display → Multi-View → PiP → Stats → More; existing mini Stats icon; existing detailed statistics/leaders, spoilers and freshness preserved |
| 5. Sports broadcast choices | Pro Sports fullscreen Channels → Sports selection only | No stale overlapping drawer; at least four complete rows when available; remaining rows scroll; existing matching and other menus unchanged |
| 6. Header theme compatibility | Existing Pro header only | Existing structure/actions/location; no retheming of other experiences or ambient engine |

Previously approved features are not removed merely because they resemble a newly requested feature. For example, the optional existing Pro score-alert policy remains intact; new Sports-only controls are independently restricted to their proper context.

## Mandatory gates and evidence

| Gate | Required evidence | Stop condition |
|---|---|---|
| A — foundation | Original source/artifact hashes and clean transport identity | Any mismatch or native compatibility conflict |
| B — exact scope | Full source snapshot and changed-method inventory | Any unmapped or protected source change |
| C — runtime isolation | Attached production Android view inventories for Mobile, Compact, Cards, TV Grid, Pro non-Sports and Pro Sports; transitions/recreation | New Pro content outside Pro or new Stats outside Pro Sports |
| D — functional contracts | Actual production click handlers with controlled player, sports repository and Android PiP boundaries; inherited regressions | Required test failure, omission or new skip |
| E — package | Unchanged protected resources/assets/native payload, protected decoded bytecode, manifest identity and permanent signature | Any unexpected package, signer or protected-code change |
| F — physical acceptance | User's installed Galaxy Fold results | Remains pending until explicitly accepted |

`package.py gates` requires all named suites, minimum test counts, no failures/errors/skips, and the six-context runtime inventory before assembly is allowed. The 167 inherited Cobra tests retain the exact pre-existing 2103324 exclusion documented in the packaging script; corrective work may not invent new exclusions. Updated inherited expectations, if necessary solely for the authorized PiP button, are separately hashed and disclosed.

Robolectric executes actual Android view construction and production listeners, but player/network/system-PiP boundaries are controlled. This does not certify physical decoder behavior, real Android audio focus or Samsung PiP/fold transitions. Screenshots, where available, are supplemental; source tokens or a green GitHub status are not substitutes for the required assertions.

`bytecode_guard.py` compares protected decoded classes after exact synthetic-helper resolution. It only normalizes instruction encoding width and provably unreachable payload-alignment padding. It must not suppress changed operands, branches, exception regions or executable instructions. Payload checks separately protect resources, assets and native libraries.

## Update and rollback policy

Only offer the signed candidate if gates A–E actually pass. Confirm its SHA-256 against the generated receipt. Install over the existing application without clearing data or uninstalling; package identity and permanent signer must match. Report installation errors explicitly and retain the prior APK.

2103369 remains the protected transport rollback. 2103324 remains the original Cobra provenance reference, not an instruction to downgrade the native transport. Android may reject a lower version code as a downgrade; do not uninstall, clear data or force a rollback without a separately reviewed data-preserving procedure.

Neither an APK artifact nor automated success authorizes replacing a locked baseline or creating a release lock.

## Remaining physical Fold checklist

- In Mobile, Compact, Cards, TV Grid, Pro non-Sports and Pro Sports: fullscreen → video UI → Channels → select another channel, both muted and unmuted, including available categories. Verify original volume behavior and unchanged Previous/Next, Last Channel and mini-player tuning.
- Enter/exit PiP from each mode's mini-player and fullscreen, both mute states; confirm original experience, same playback session, no duplicated surface, and normal Back behavior. Exercise cover/inner display, rotation and multi-window.
- Switch Pro Sports → each other mode and back, including Back, PiP return and activity recreation. No newly introduced Stats, Status, Pro rail, scores or Pro header may leak into another experience.
- Pro non-Sports: original menu items plus PiP, smooth horizontal scrolling, no arrows or instructional text. Pro Sports: exact six-button order, label Stats and the existing mini Stats icon.
- Compare live, upcoming, delayed and unavailable Stats data, spoiler settings, venues, team/player details and existing leaders. No fabricated fields.
- Pro Sports fullscreen → Channels → Sports → another game: four complete channel rows where at least four exist, vertical scrolling for extras, all rows selectable, no overlapping/stale layers; verify Close/Back and correct tuning.
- Pro header: Light, Dark, OLED/System and existing Ambient variants, including transitions; unchanged controls and layout.
- Confirm protected playback, scaling/Fill, Multi-View, timeshift/rewind, subtitles/audio menus, Favorites/Recents/Pins/My Teams, providers, settings and navigation remain intact.

Record actual failures and screenshots before acceptance. Do not lock or promote on partial results.
