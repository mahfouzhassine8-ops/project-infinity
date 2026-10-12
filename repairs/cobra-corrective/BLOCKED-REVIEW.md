# Latest preservation stop — 2026-10-12, run 38206152159

Implementation checkpoint: `0c18474b13650f17740869c1156a2d885e7c713e`, branch `work/cobra-astra-corrective-20261012`.

The corrected-size preview PiP test passed at 412x915, 915x412, 720x840 and 840x720, then failed its non-overlap assertion at 280x280. Exact window dimensions were asserted before geometry. The original Unmute and status geometry has not been changed, and must not be moved to hide this failure. App/source changes are stopped under the user's hard preservation gate; only this stop record and blocked metadata are being saved. A narrowly scoped new-PiP placement remedy requires direction before proceeding.

Read-only geometry trace: after the test's horizontal system insets, original stage padding and original Pro inset, the Hero is 232dp wide. New PiP occupies x=12..60dp; the original centered 124dp Unmute occupies x=54..178dp on the same 48dp row. Their intersection is 6x48dp. The status control starts at x=156dp and is not this intersection. Moving PiP a few pixels left alone is not proven safe because the original left navigation target must also remain unobstructed. Any future correction must place only the new target in genuinely free space and verify every original touch region; the existing controls may not be moved without additional scope authorization.

The same run passed all 167 inherited cases, the untouched-source routing reference, its candidate comparison, the actual rewind-proxy audio test, strengthened mini/fullscreen PiP return hierarchy checks and the four-row broadcast chooser at all five real sizes. It still failed actual Activity recreation (Robolectric's recreated ViewRoot is absent) and the Groups workflow (no different visible channel found in the fixture's first group). Neither unresolved result is called a pass or assumed to be an app defect.

Candidate total: 196 passed / 199 executed / 3 failed / 0 skipped. Baseline/source gates passed; functional/isolation completion is blocked. APK assembly and permanent signing were skipped. No candidate was installed, locked or promoted. Protected 2103324 Cobra and 2103369 native transport references remain unchanged, and rejected 2103370 is not an implementation parent.

Evidence artifact: `11727880760`, ZIP SHA-256 `89e4658620ba35a81cd83495308885990154cc1e936153a3e7a3d2c90f4b7fb2`. Downloaded ZIP integrity passed. Run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/38206152159

The earlier stop, continuation and hashes below are retained as history, not current acceptance statements.

# Historical blocked checkpoint — continuation authorized

The user explicitly authorized continuation from commit `c3d5b03602e6e8edc275203491b572b8e1c26c77`. The narrow routing alias below is now implemented at exactly the two documented callers; source-token checks prove no other change within those navigation methods. The new left preview PiP position remains, with new actual hierarchy/geometry/touch tests. All 27 existing new tests and 167 inherited cases are retained; four targeted continuation tests bring the new suite to 31. This source checkpoint is ready for parent compile/runtime gates, not accepted or promoted. Android tests, evidence renders and packaging have not yet run. The historical findings and checkpoint hashes below are preserved unchanged for audit.

## Historical stop record

The earlier source-ready checkpoint is withdrawn. Stop requested by the parent after independent review identified a protected playback/navigation regression. No routing correction has been applied. The source and tests are preserved as an incomplete draft for review, not for compilation, APK assembly, signing, promotion or installation.

No Android compilation or runtime tests have run for this draft. No runtime control inventory has been produced. No corrective APK has been assembled or signed. No physical-device result is claimed. The earlier local Java-token scope check is structural evidence only, not proof of runtime isolation or acceptance.

## Finding 1: changing the shared predicate changes protected return navigation

Verified by reading the exact approved 2103324 source and the new draft's callsites and ownership transitions; this is a source-level failure, not a reproduced device result.

Approved predicate:

```java
private boolean cobraProPlayerSportsEnabled(){return cobraTouchFirstDevice()&&"focus".equals(cobraGuideViewMode());}
```

Draft predicate:

```java
private boolean cobraProPlayerSportsEnabled(){return cobraTouchFirstDevice()&&mCobraProActive&&"focus".equals(mCobraGuideStyle);}
```

Actual live mode/ownership is required for new player controls, because Mobile deliberately preserves a previous saved guide preference of `focus`. However, the existing predicate is not confined to player controls. Two unchanged navigation methods consume it:

1. `showCobraPrimaryView`, when the current drawer owner is Sports, calls `stopCobraPreview()` if the predicate is false, then opens `showCobraSportsHub()`.
2. `showCobraSportsHub` uses the predicate to choose its embedded-guide branch versus stopping preview and building the standalone Sports Hub.

The approved sequence can be Pro Sports → switch to Mobile → fullscreen → Back. `cobraSwitchMode` changes the live mode and exits Pro ownership but does not change the existing Sports drawer owner. Mobile keeps the saved `guide_view_mode=focus`. On fullscreen Back, the approved predicate remains true: the Sports-owner return does not stop the transferred preview, and the embedded-guide branch rebuilds the actual Mobile guide. Thus the existing player can remain the preview owner.

The draft predicate is false after the same Pro exit. The same unchanged return caller therefore invokes `stopCobraPreview`, which disposes the transferred preview player, then takes the standalone Sports Hub path. This violates the protected navigation/playback preservation requirement. It cannot be accepted merely because the new rail and Stats no longer leak into Mobile.

There is a related stopped/cold-route distinction: `stopCobraPreview` clears `mCobraProActive`; the old navigation decision still reads the saved guide preference. The exact original routing behavior must be preserved, not replaced with a newly invented cold-start or forced-Pro restoration policy.

### Minimal proposal, NOT APPLIED

Separate routing compatibility from actual player/UI ownership:

- Retain the exact old predicate expression for only the two routing consumers above, through an explicitly named compatibility helper.
- Continue using actual phone/live-mode/Pro ownership for player/UI-only decisions, and current Sports section/pane for the newly added Stats and scoped chooser.
- Do not add new navigation intent, force a saved mode, change drawer ownership, alter Smart Return, or broaden cold-start behavior.
- Add attached-view return tests for Sports → Mobile with dirty saved focus, and stopped/cold routing comparisons against the approved source, before any acceptance claim.

This proposal awaits direction. Neither the compatibility helper nor either routing callsite change exists in the preserved draft.

## Finding 2: initial muted-preview PiP placement overlapped an original status control

The initial draft placed the new `previewPip` at `x = w - p - 48dp`, `y = actionY`, with a 48dp target. The original non-WATCHING status occupies `x = w - p - 64dp`, `y = actionY`, with a 64dp width and the same height. Those rectangles overlap. Existing Unmute/status controls must not be moved or replaced to make space for PiP.

### Minimal proposed correction and exact preserved state

Place only the new PiP target at the left `actionY` position (`x = p`), in the area occupied by the original muted badge/icon views, which are already GONE. Keep original Unmute and status geometry unchanged. Test actual visible target rectangles, focus/accessibility exposure and callback routing at every allowed size before accepting this position.

Timing note: the implementation agent applied that one new-target move immediately before receiving the parent's STOP message. The current preserved `CobraProUi.java.in` therefore has `place(previewPip,p,actionY,bh,bh)`. The original muted/status/Unmute expressions remain unchanged. The move has NOT been validated by Android layout/runtime tests, and does not clear this gate. No further source or test edits were made after STOP; this report is documentation only.

## Preserved draft contents and identity

| File | SHA-256 |
|---|---|
| `runtime-src/InfinityLiveActivity.java.in` | `5d075311b7a3fd6edb70b563e16852727aa078e18e5b49a4a4cff8ede3465366` |
| `runtime-src/CobraProUi.java.in` | `17d8ddfaebd1d77b2275777275dd7b22e1a9a0fbd813dc71adcf931e10f026ca` |
| `CobraCorrectiveContractsTest.java` | `a5520f06ad2efa1d4c727672832b97aaf3e96579a09a833b6cccf12e5f107a37` |

The new test specification contains 27 unexecuted tests. The inherited suite retains all 167 cases, with only four explicit PiP-addition expectation changes in one copied Controls test file. The source guard enumerates 27 draft method/class contracts, rejects candidate-only file additions, and checks protected tokens and other source bytes. Neither that allowlist nor the authored tests authorize ignoring the navigation failure.

Gate A baseline identity is separate and already verified. Gates C/D/E for this draft are NOT passed. Physical acceptance remains pending. No rejected 2103370 code was copied or cherry-picked, and no native/Infinity/backend/package source changes were made by this implementation agent.
