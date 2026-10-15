# Clean restart — implementation saved, preservation gate failed

**STOPPED. No candidate APK assembled or signed. No lock or production promotion.**

## Exact saved implementation

- Branch: `work/cobra-clean-restart-20261012`.
- Last tested source: `daa8c1b19d02c84b86696fc82cb8cb0a0ac30563`.
- Latest candidate run: `38213877859`, completed with failure.
- Evidence artifact: `11730895129`.
- Downloaded evidence ZIP SHA-256: `65f558241cd95d8424b5481c9ae90016cc4109fa49733e37089f23d79718bf5c`; ZIP integrity checked.

The implementation consists of the guarded `apply.py`, independently authored `CobraSix.fragment.java` and `HeroPip.fragment.java`, the actual runtime tests, and their staging/workflow files. The CI artifact retains exact compiled runtime-source and test-source archives, original JUnit XML, screenshots, inventories, and logs. This stop commit changes documentation only.

## Executed results

The untouched approved-source reference run `38209729246` passed **168/168** cases: all 167 inherited cases plus actual attached view measurement at five real window sizes. Its artifact is `11729196765`, SHA-256 `401d74baabac1a8d187b204982b72e3bc6bf0efd95537aadd9eefc36e00cd02d`.

First candidate run `38212088761`, source `21a0e1b84a9e53dc25ab99f1d01dfdc8840bb868`: **180/185 passed, five failed, zero skipped**.

Latest candidate run `38213877859`, source `daa8c1b19d02c84b86696fc82cb8cb0a0ac30563`: **172/185 passed, 13 failed, zero skipped**. Production Java and test Java compilation both passed. The latest run passed **17/18 new tests** and **155/167 inherited cases**. It is not an accepted candidate.

## Confirmed preservation stop — new unsupported-PiP control

The new ninth Hero action is not inserted into the strip when PiP is unsupported. That preserves the original visible ordering, but the action remains in the `player` array without LayoutParams. The existing `CobraProUi.Hero.onLayout` sizing loop iterates this array and dereferences the null parameters.

This new-control defect causes all 11 `CobraProControlsRefinementTest` cases and `CobraProHandoffTest.mobileDrawerHidesOnlyViewDestinationAndRetainsModesOnTv` to fail at the same null-pointer. These are 12 failing cases, not 12 independently diagnosed product defects. The original TV/onn APKs were not replaced, but this candidate fails the protected TV/fallback regression test.

Runtime source changes stopped after this finding. Do not remove tests, suppress the exception, alter the original controls, waive the gate, or package this source. A separately authorized continuation should correct only the new unsupported control's initialization/layout membership and rerun every inherited case.

## Separate unresolved Groups workflow

The actual fullscreen Channels workflow reaches `GROUP:Documentaries`. Its adapter has a genuinely different channel, but the test ListView has no rendered children: `first=0`, `last=-1`, `children=0`, measured `392x358`. The failing matrix iteration is Mobile, unmuted, Groups.

The cause has not been independently established as an application defect versus a test/layout-fixture issue. The complete all-mode/category audio matrix remains unverified. Do not substitute a hidden callback invocation for actual selectable rows.

## Six-change progress and limits

1. **Fullscreen Channels user mute:** scoped channel-bound override saved for regular and Sports tuning. Actual local-rewind proxy mute before prepare/play, temporary-silence negative control and direct-tuning preservation tests passed. Full category/mode proof is blocked by Groups.
2. **Mini/fullscreen PiP:** visible controls and same-player mini/fullscreen return tests passed for all six contexts and both mute states. Denied-entry return and five-size Pro preview geometry passed. The unsupported-PiP/TV fallback crash is the current preservation stop. Physical Samsung PiP is untested.
3. **Pro horizontal controls:** actual six-mode menus, active-mode versus stored-preference isolation, mode switching, scroll range and prohibited arrow/instruction absence passed. The scroll test is not a full physical gesture certification.
4. **Pro Sports Stats:** exact menu/order/label, existing mini Stats renderer, home/away names and logo slots, venue/kickoff/score/meta, retained detailed statistics/leaders, spoiler confirmation and stale callback isolation are saved and tested. Live logos, city/possession coverage, all freshness states and approved-mockup comparison are not certified.
5. **Pro Sports broadcast choices:** foreground ownership, three/four/seven actual choices at five real sizes, four complete 48dp rows, scrolling to and selecting the last row, and original Back/Close passed. Synthetic system-bar/cutout combinations and physical Fold testing remain pending.
6. **Pro header:** palette/glass correction, unchanged child geometry, Light/Dark/OLED/System transitions and release of new theme ownership into the original reused Compact toolbar passed. Full ambient/theme visual coverage remains pending.

Actual saved-state recreation now passes through explicit pause/stop/save/destroy and fresh create/start/restore/postCreate/resume/visible callbacks: the original Activity is destroyed, the replacement is a different attached instance in Compact, and no new Pro elements appear. The earlier Robolectric convenience `recreate()` missing-ViewRoot failure remains historical evidence, not a retroactive pass. This does not certify Samsung fold/process-death behavior.

## Source identity and scope

- Approved Cobra 2103324: `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3`.
- Approval lock: `25497c4dfd6be8d83f32580495b16afb6eaed736`.
- Retained 2103369 transport: `9abf7c84fbd8224958bc8465c983429bc5976074`.
- Rejected 2103370 and the earlier corrective branch were not implementation parents and no rejected UI/player patch was imported.

Only `tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in` and `tools/android/packaging/xbmc/src/CobraProUi.java.in` differ from the exact retained runtime archive. The remaining 262 of 264 runtime files are byte-identical. No native rebuild ran. No skin, provider, Command Center, shutdown source or installed APK was replaced.

A read-only JDK named-member inventory identifies 69 changed/added members: 50 methods/constructors and 19 fields; 46 members are additions. Every listed member is mapped to the six authorized requirements. The generated `CHANGED-MEMBERS.json` has SHA-256 `a3178819428e9516800f71dcad9084bebc07cccdb03c171075832d1c21259932`. This is not a final compiled-bytecode or APK preservation certificate.

## Read-only diagnosis of 2103370 leakage

The rejected patch at `47d9e563a6052e6ac5d90f784ad526346d93d9cf` chose its shared fullscreen Pro rail using `cobraProPlayerSportsEnabled()`. The original predicate checks the saved `guide_view_mode=focus` preference rather than the active experience. This is a concrete source path consistent with the user's reported leakage; the exact historical physical-device sequence was not reproduced.

That rejected rail explicitly specified the `health` icon, `Status`, left/right arrows and swipe instruction text for every admitted context, including non-Sports. The fresh implementation independently guards its presentation with actual active Pro state and a current fullscreen/channel/profile Sports context.

## Signing and rollback

No candidate version is assigned and no candidate has been assembled or permanently signed. CI's debug key is compile-only, not an update artifact.

Original APK SHA-256:

- 2103324: `5af58f2e700e636cdc798cbde0acc89e8091153cfcf1e17c792375fe285dd8c3`.
- 2103369: `83128afbd2595dbf4053ded40ee1d22ae0d1c7b798f62dd9f077bd4d729261f4`.
- Permanent signer certificate: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

The generated saved-implementation archive is 76,586 bytes, SHA-256 `cdb92445abc30b6ea4eed9be3203381397a89846c52c7c967bcb0bca5070594e`. It contains source inputs, the changed-member inventory and checkpoint evidence, **not an APK**.

Preserve all work and failure evidence. Do not restart baseline recovery, clear data, uninstall, downgrade, rename an old APK into a candidate, lock, or promote. Complete the outstanding source, runtime, payload, signature and physical-device gates before acceptance.
