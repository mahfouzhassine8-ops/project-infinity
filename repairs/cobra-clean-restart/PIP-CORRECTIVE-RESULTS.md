# Cobra PiP corrective repair — automated correction passed

Continued from `aca973f21642c30148367baaf7ed0e0f83f079f8`; the implementation was not restarted. This report supersedes the active stop status in the historical `STOP-RECORD.md`. Earlier source and failed-run evidence remain preserved.

**All 185 required candidate cases passed. No APK was assembled, permanently signed, installed, locked or promoted.** The full package-preservation and physical-device acceptance gates remain separate.

## Verified execution

| Run | Source commit | Executed | Passed | Failed | Errors | Skipped |
|---|---|---:|---:|---:|---:|---:|
| Saved failed implementation, 38213877859 | daa8c1b19d02c84b86696fc82cb8cb0a0ac30563 | 185 | 172 | 13 | 0 | 0 |
| First PiP correction, 38216862555 | b53d887ae31d07363ac505b110547459d91e823d | 185 | 184 | 1 | 0 | 0 |
| Corrective final, 38217628815 | e82f9a677532554c0d020f5c08d3f29ebe89296c | 185 | 185 | 0 | 0 | 0 |
| Untouched-source reference, 38217628897 | e82f9a677532554c0d020f5c08d3f29ebe89296c | 169 | 169 | 0 | 0 | 0 |

Candidate final includes all **167 inherited cases** and all **18 existing corrective cases**. The reference includes the same 167 inherited cases, the original view-geometry case and one new Groups traversal comparison.

The downloaded final candidate XML contains exactly the same 185 class/test names as the saved failed run. No required case was deleted, replaced or skipped. All inherited source-provenance entries match the saved run exactly, including only the already documented original 2103324 exclusion. Existing new-suite assertions remain; its fixture now allows ordinary Android framework traversal, and additional locked/stale-session negative assertions were added to the mini-PiP case.

## PiP comparison and selective reuse

The user's physical report establishes that PiP worked in the scenario they tested on rejected 2103370. It does not accept that complete build or establish unreported entry, mute, fold or lifecycle scenarios.

Compared reference: `47d9e563a6052e6ac5d90f784ad526346d93d9cf`, `repairs/cobra-six-2103370/changes.patch`. Both implementations enter through the preserved Android PiP implementation and promote/return the same preview session.

The clean implementation selectively reuses only the reference's mini-entry guards: refuse a locked/already-PiP request and require the preview channel key to match the actual preview session. These guards prevent promotion of a stale selection into a replacement player. The strengthened test verifies rejected stale/locked requests followed by the real visible PiP button and original same-player round trip.

No 2103370 Status/health rail, arrows, scrolling instructions, saved-preference Pro predicate, global audio carry across unrelated tuning, explicit paused/multi policy or unrelated Sports/header implementation was copied. See `PIP-SELECTIVE-REVIEW.md` for the comparison.

## Unsupported-PiP layout crash fixed

The newly added ninth Hero action remained in `player[]` when unsupported, without LayoutParams because it was not attached to the visible strip. The original layout loop dereferenced those missing parameters.

Only that new action now receives the correct LinearLayout parameters during initialization. The eight original controls, original layout loop, unsupported strip membership, order, visibility and callbacks remain unchanged. No exception is suppressed. All twelve cases previously failing at this shared cause now pass, including the protected TV/fallback case.

## Groups failure — independently reproduced test-helper defect

The failing Groups adapter held four Documentaries channels but no rendered rows. Read-only tracing showed pending layout requests in the list and its inner container while the manually laid-out ancestors no longer requested traversal.

A separate test on the **unchanged approved Cobra runtime within the retained transport** reproduced both outcomes:

| Same Groups workflow and list bounds | Channel data | Rendered rows | Pending layout |
|---|---:|---:|---|
| Historical manual measurement helper | 4 | 0 | Yes |
| Ordinary framework-driven traversal | 4 | 4 | No |

Both paths reached `GROUP:Documentaries` with a 392 x 358 list inside the asserted 412 x 915 window. The framework path verifies that the intended row is visible and clickable. This supports a test-helper cause for the reported automated failure; it is not a claim about every physical-device scenario.

The candidate fixture now advances the normal paused-looper frames and lets ViewRoot perform layout, rather than manually measuring and laying out the decor. It does not manufacture rows, reset the adapter, clear framework flags or bypass the user-facing selection. **No Groups filtering, navigation or runtime rendering code changed.**

The original audio matrix then completed all **48** combinations: six contexts x muted/unmuted x All/Favorites/Recents/Groups. It uses actual production controls, selects a genuinely different channel, verifies player replacement and checks the preserved mute state before preparation and playback.

## Runtime isolation and other executed checks

Mobile, Compact, Cards and TV Grid expose `Channels > Display > Multi-View > PiP > More` without the new Pro scrolling container or Stats. Pro non-Sports has the same items in its horizontal container. Pro Sports alone has `Channels > Display > Multi-View > PiP > Stats > More`.

The 185-case rerun also passed the existing active-mode/stored-preference isolation, Pro-to-other-mode transitions, same-player mini/fullscreen PiP returns in all six contexts and both mute states, denied PiP recovery, preview PiP geometry at five actual window sizes, real rewind-proxy mute timing, negative direct-tuning checks, four-row broadcast choice/scroll/Back checks, Stats details/leaders/spoiler/stale-callback checks, header geometry/theme ownership and saved-state recreation checks.

These are controlled production-view tests with player/network/platform boundaries controlled. They are not Samsung physical decoder, audio-focus, PiP or Fold acceptance.

## Exact source preservation

The continuation adds only two runtime hunks relative to the saved implementation: new-PiP layout initialization and mini-entry session guards. Both map to authorized Change 2. Groups repair is test-only. No new runtime file or registered Android source was added.

Only the same two runtime files differ from the approved-source/transport archive; the other **262 of 264** files are byte-identical. Extracted final runtime hashes match the generated source receipt and are identical to the first corrective run, proving the Groups resolution did not change runtime code:

- `CobraProUi.java.in`: `a096e19cb594752274ded0ea18a40a48f9e5ee55ad5e7f6caf474236d56372cb`
- `InfinityLiveActivity.java.in`: `77482b135aff60a4c0c6953bb92b1949c32e447528434df659aa869892ab4c1c`

The generator emits the narrow `pip-corrective.patch`, `PIP-CORRECTIVE-DELTA.json`, full `changes.patch`, updated `CHANGED-METHODS.json`, `SOURCE-PRESERVATION.json` and test provenance. No unrelated native, skin, provider, Command Center, shutdown, settings or TV/onn source was modified by this continuation. No native rebuild ran.

Approved Cobra source: `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3`; approval lock: `25497c4dfd6be8d83f32580495b16afb6eaed736`. Retained 2103369 transport: `9abf7c84fbd8224958bc8465c983429bc5976074`.

## Evidence identity

All listed downloaded ZIPs passed SHA-256 matching and CRC checks.

- Final candidate artifact `11732706403`, run `38217628815`: `238eb08304d32a44d630b96d87862628716f422951b94be4b8141ba499f41e08`.
- Unchanged Groups reference artifact `11733405955`, run `38217628897`: `c1baafa3ac8a0d6781fa609a59aee31903f0f82666573611ef78953b2a5c095c`.
- Earlier 184/185 artifact `11731174454`, run `38216862555`: `de50086587f968833dfd875cb317e5f5f2a8719f04bf143dc60ff317867575de`.
- Independently generated `FINAL-EVIDENCE-VERIFICATION.json`: `950a4bbbb9aac612471c54439743a409491defa822c3d943b84ccc9ae225beca`.

## Remaining acceptance boundaries

This corrective pass clears the named PiP crash, establishes the automated Groups failure's cause and passes the requested 185 cases. It does not certify every remaining requirement of the larger six-change delivery.

The broader outstanding items recorded before this continuation remain: complete source/compiled-bytecode and package-preservation review, any remaining full visual/mockup/theme/ambient and Sports freshness/data-availability coverage, final artifact identity and permanent signing, and physical Fold acceptance. No tests were waived and no APK was packaged to skip those gates. No new candidate version is assigned. No automatic release lock or promotion is authorized.
