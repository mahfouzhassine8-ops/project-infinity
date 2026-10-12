# BLOCKED — corrective draft, not a candidate

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
