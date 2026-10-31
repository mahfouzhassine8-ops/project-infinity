# Cards drawer-only435 continuation checkpoint

**The sections below this notice retain the historical b7e17d4e read-only
checkpoint. Current implementation/evidence status is in
[CORRECTION-CHECKPOINT.md](CORRECTION-CHECKPOINT.md).**

The two required repository contracts were read in full. Existing development branch `work/cobra-only-from-2103435-20261031` is operational; its protected lock resolves to exact signed source `e0c6153588992001d84076d33fdf8f0d676c0d00`. No existing production/build/release file was modified. Infinity, all other Cobra functionality, chooser, native components and shutdown remain unchanged. No APK/version reservation/signing occurred.

The actual official435 signed archive and complete APK stream were rehashed, together with the matching Cobra ZIP/DEX identities. The reused435 host translation is the source/canonical-bound actual owner from the preceding delivery, not an older architecture or the historical drawer snippet.

One preselected baseline test (`signed435DrawerTranslationAndInsetGeometry`) passed as a trace and reproduces the defect. It uses the original Cards header button pointer, actual native drawer code and bounded native frame input. The fixture compiles other layout cases but executes only this selected method. No provider/decoder/device/shutdown acceptance is claimed.

| Host observation | Decor/shell width | Stage translation X | Toolbar/grid width | Preview width | Columns | New I/O jobs |
|---|---:|---:|---:|---:|---:|---:|
| Closed435 |1600|0|1600|774|4|0|
| Drawer opened |1600|448|1600|774|4|0|
| Original native restyle with drawer open |1600|448|1152|550|4|0|
| Drawer closed after animation |1600|0|1152|550|4|0|

The window/root insets are `[0,0,0,0]` and stage scale stays1. `animateCobraDrawerShift` moves `mStage`; its original open target is `min(drawerWidth, decorWidth * .28)`. The existing `CobraCardsLayout.State.physicalLayout` uses the translated `shell.getLocationInWindow()` to compute `max(0, shellX + shellWidth - decorWidth + systemInsetRight)`. A448px parent translation becomes a false448px right inset, so the page gets only1152px while the real window and shell remain1600px. Closing restores the parent translation but leaves the reduced child geometry until another native refresh. This establishes an actual signed-source/host defect consistent with the supplied physical-device notes. It is not personal review or reproduction of the full physical recordings.

The correction should isolate expanded Cards content from experience-drawer translation while retaining the original drawer overlay/navigation/animation and front/non-Cards policy. Genuine drawer-open fold/rotation transitions must be reconciled using the actual new window, with no new timers/observers, re-created grid/player, or data reload. A final method-level allowlist must follow complete recording review and targeted negative controls, not speculation. Simply freezing one width or correcting only the right-inset formula would leave the unwanted content shift and/or genuine fold behavior unresolved.

**Exact blocker:** neither20728.mp4 nor20729.mp4 is materialized in this workspace or exposed as a readable uploaded-file reference. The known private reference Page has no references for them; available Page file tools support images/text/documents and explicitly exclude arbitrary binary/video. No authorized direct download URL or Sediment identifier is supplied. The repository inspection notes describe the videos but do not supply their bytes. An existing local path or authorized private download link was requested asynchronously; no new upload or permission brief was requested. Do not claim complete video inspection or sign a candidate before the mandatory review is possible.

Resume from these measurements once recording bytes are accessible. Do not repeat this completed baseline trace or reopen the Infinity/earlier Cobra projects. Scope remains exactly one Cards drawer-layout correction.

## Original ZIP handoff and further read-only trace

The user confirmed the original recordings and comparison files are in `Cobra_2103435_Drawer_Resize_Original_Videos.zip` and explicitly directed read-only investigation if media access remains blocked. The archive still is not materialized or exposed via a supported file/download reference; the refreshed private Page contains only earlier20689 evidence. This is a runtime attachment-access gap, not a claim that the user failed to supply files. No video or included-frame verification is claimed.

Further actual435 native tracing finds the same translated-location inset subtraction in `cobraLayoutGuide`, before logical `model.width`/columns are calculated, in addition to the existing Cards helper's physical sizing. The persistent attached-guide branch of `onConfigurationChanged` calls layout, browser rendering and restyling and returns without taking the later generic drawer-close branch. The drawer root's existing size listener updates only its panel width. Thus there are two sizing consumers affected by the translated parent during genuine configuration changes. A later implementation must address ownership before both sizing calculations and preserve front/non-Cards drawer behavior; a helper-only width patch is insufficient. `FOLD-SOURCE-TRACE.json` retains actual canonical method preimages. No extra runtime test, production edit, signing, data operation or shutdown test was performed for this source trace.
