# Targeted drawer correction from signed2103435

Continued the existing authorized branch from `b7e17d4e`. The completed
1600−448=1152 baseline reproduction was reused; no original defect replay,
Infinity execution or shutdown test was performed. The original signed APK,
component ZIPs and protected lock remain unchanged.

## Implemented production delta

Both original sizing consumers now use `CobraCardsDrawerViewport.location`:
native `InfinityLiveActivity.cobraLayoutGuide` and Cards
`CobraCardsLayout.State.physicalLayout`. Only their coordinate-read call sites
change. Every original inset/working-height/rectangle/column calculation stays
intact. The native drawer animators, callback, panel sizing, duration,
interpolator and stage translation are unchanged.

The new Cobra-only helper removes the drawer's presentation translation from
the position used for inset calculation. It never writes a view dimension,
translation, inset, window flag, preference, channel or player. It requires the
attached visible Cards shell directly owned by the original stage, excludes
Pro/Pro Sports and visible fullscreen/Multi-View overlays, and corrects only
an inner-display drawer journey. Weak Activity/stage/drawer identities retain
that ownership across a genuine inner→cover transition and closing-animation
tail. A new cover-only drawer starts its original policy; no timer, worker,
polling, remembered viewport dimension or extra view tree is introduced.

This retained journey is necessary: an inner-only instantaneous guard fixed
inner sizing but left the original false narrow width after returning to the
cover with the same drawer. The final test requires the normal approved
two-column cover geometry after that genuine transition, while independently
requiring unchanged435 cover-only drawer geometry.

## Verification completed

The exact actual435 Cobra bundle and all7166 canonical classes were validated
before compilation. Actual emitted owner DEX was independently disassembled:

- Two existing methods change, plus two new helper classes.
- All7164 other original classes are canonical-identical. Existing class
  fields, interfaces and annotations are unchanged.
- `part-1.dex` remains byte-identical:
  `cf1f796e1e1c5ddb208ad9a6fe79328f40161ce07a2f69923f8aff69b136252e`.
- The changed `part-0.dex` is
  `56c030dd52d55dae7b5b2e77d86d860b49a8866b52ba2103bd0d2f4bcb429f09`.
- Existing Cards Java source has exactly one coordinate-call replacement;
  inverse replacement equals signed435 source byte-for-byte.
- Frozen Infinity, Minimal Android and chooser ZIP SHA256 values match the
  protected435 contract. No native/resource/icon member was rebuilt.

All five preselected host cases pass. They execute original translated owner
code with native Android views/graphics, actual pointer dispatch, animation
frames and real `WindowInsets` inputs in Robolectric4.14.1/SDK35. Synthetic
channels/EPG and a state-only player fixture are used. This is host evidence,
not an Android17 emulator result or physical Fold acceptance.

| Measurement / check | Signed435 | Corrected owner, host only |
|---|---|---|
|1600px inner toolbar/grid after drawer-open restyle|1152px|1600px throughout tested frames|
|Inner preview width|550px after false inset|774px throughout tested frames|
|Inner grid columns / scale|4 /1|4 /1|
|Close animation and rapid interruptions|Baseline trace retained|Stable measured geometry; original motion retained|
|Actual800dp/840dp/600dp viewport transitions with retained drawer|649/689/449dp false model widths in new baseline configuration check|800/840/600dp;4/4/3 columns|
|Return to360dp cover with same inner journey|259dp false width;1 column|360dp; approved normal2-column geometry|
|Independent cover-only and other-mode fixed-viewports|Exact435 measurements|Equal to435 at both selected sizes|
|Nonzero root insets [24,32,40,48]px|Original arithmetic preserved|1536px usable toolbar,24px origin; both sizing paths agree|
|Drawer-only channel/adapter/scroll/player/texture/EPG references and new I/O|Baseline trace and current checks|Preserved; no added I/O jobs|

The original full configuration callback creates new Theme/UiContract
identities, so its existing reuse policy reconstructs the grid. That unchanged
behavior was recorded on actual435 as well as the corrected owner. It is not
reported as retained grid identity, a new crash, or a repaired lifecycle issue.
Player/texture/channel/inventory/EPG references survive the simulated callback.
One initial host negative-control assumption treated ListView as GridView;
that harness error was corrected. An initial configuration assertion required
grid identity which the unchanged original callback does not retain; source
and baseline evidence explain it. The final fold case keeps the viewport,
channel/player/data and normal-cover restoration assertions strict. Failed
evidence is retained; it is not relabeled PASS.

Actual results, original JUnit XML, selected scope, compiler hashes, baseline
measurements and the failed configuration assertion are in `correction-host/`.
`verify_checkpoint.py` checks the source budget, frozen bundle hashes, exact
owner budget and exactly five successful selected JUnit methods.

## Evidence/release gate — blocked, no signed candidate

The user supplied a timestamped-frame PDF, but its bytes and an authorized
readable file reference are not exposed by this workspace or the connected
reference Page. No PDF exists in the searched workspace locations. The known
Page still contains only the older approved design/20689 evidence; those files
were not substituted for20728/20729. An existing accessible PDF reference or
private link was requested asynchronously.

**Static PDF-frame inspection: NOT PERFORMED. Full original video playback:
NOT PERFORMED.** Extracted prose or repository notes are not pixel review.
Once the supplied PDF becomes accessible, inspect its actual rendered frames
and timestamps; label that as static-frame review, not full playback.

Final release integration, selected actual Android interaction checks and the
mandatory complete successor APK-member comparison remain pending this
evidence gate. Full decoder/surface/focus and physical Fold acceptance are not
claimed. No successor version was reserved; no APK was created or signed, no
signing workflow was dispatched, and no lock/accepted pointer was changed.

Resume with the saved implementation and passing evidence, not another
baseline investigation. Do not invoke the historical435-from431 full rebuild
against this source: use the new exact435 delta compiler to preserve all
unrelated owner definitions. The eventual release must reuse435 Infinity and
Minimal Android bundles exactly, enumerate every permitted APK member/version
metadata change and pass original-key checks before delivering one candidate.
