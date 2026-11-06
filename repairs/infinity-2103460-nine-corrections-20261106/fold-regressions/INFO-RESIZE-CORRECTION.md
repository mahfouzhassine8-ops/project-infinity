# Final targeted resize correction — supersedes the 264/265 testing artifacts

No264/265 package was installed, promoted, locked or recommended to the user.
The immutable current device reference remains APK462 / skin262 / CC61.

A necessary final source review found that the proposed grouplist minimum
width is retained across in-place reflow. The actual frozen GetWidth and
SetMinSize methods reproduce clipping over successive logical widths2400,
2000 and1900: the stale minimum can exceed the updated maximum after the
first resize. This is a host source counterexample, not a claim of a new
observed device failure.

The correction is confined to Info group9000. Use a normal percentage-sized
group, four explicit proportional positions and conditional left/right focus
links that skip the episode-hidden Trailer. Add links to the existing Back
and Cast controls. All playback/trailer/cast/more onclicks, metadata, textures,
fonts, visibility, IDs and the video preview geometry remain unchanged.
The preview stays behind the controls as previously corrected. No native fix
or new APK is required.

Only the affected test
`test_integrated_corrections.SkinAndProtectedPasses.test_applied_info_matches_previously_verified_candidate`
was revised and run. INFO-RESIZE-RECHECK.txt records PASS: compiled actual old
native methods expose the counterexample; the normal group fits all five
logical widths; exact existing onclicks are preserved; hidden-Trailer focus
and Back links are checked. Other14 source cases are reused unchanged.
This does not establish Android rendering or physical Fold acceptance.

Issue forward skin266 / recovery267, never a different payload under264.
Both complete CC module payloads are byte-identical to those authenticated
and tested in run42281237899. CC-AUDIT-REFERENCE.json binds their complete
member hashes, original production Java source, host Java sources and six
actual installer/recovery results. Reuse those cases only after exact hash
comparison; do not rerun unchanged Java tests. Recheck the new skin integrity,
component signatures and member preservation on the actual downloaded266/267
artifacts. Recovery267 restores exact262 functionality while retaining native462.

Search All's two validation failures, actual reported heading attribution and
real repeated native Search stability remain explicitly unresolved. No
native crash fix, complete repair or physical acceptance is claimed.
