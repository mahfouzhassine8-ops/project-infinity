# Selected Continue Playing checks

Run the signed 2103514 and candidate Python against the same read-only
fixtures. First reproduce a malformed remembered URI causing a second,
valid Continue item with the same provider pins to require recovery in a
shared render. Then verify that only the malformed URI requires recovery.
Check both list orders and preserve the signed Watchlist behavior.

Verify that exactly matching failed-route fingerprints still require recovery,
unrelated failure history does not, invalid remembered fingerprints fail,
changed provider source pins are rejected, and the unapproved Umbrella
6.8.02 and POV 6.11.03 manifests remain rejected. Check that matched typed
identity, Resume and Play from Beginning keep their original direct and
recovery offsets and that cancelling the chooser does not persist anything.
Diagnostics must use fixed labels and exclude the route, provider arguments,
title, saved key, typed identity and resume position.

Native verification remains the separately selected full ARM64 compile/link,
startup markers, exact 2103514 ABI and dependencies check in CI-NATIVE.json.
Selected Android verification checks activation of the scoped candidate
modules, the startup boundaries in a normal launch, and install-over and
forward recovery with profile data retained. No shutdown scenario is selected.

The recovery handoff fixture also supplies an existing exact native receipt
and first mismatches the playback path. Verify that this cannot write a
preference or report confirmed playback. Then provide matching playback
provenance and verify that the existing confirmation path is used. No profile
write or native playback is part of this host fixture.

For release preparation, check the original public-key signature on the full
signed 2103514 module inventory, compare all member hashes, apply the four-file
overlay and regenerate the unsigned manifests. Forward recovery restores
2103514 code. The Command Center manifest and addon.xml must use monotonic
versions on both sides so the unchanged installer activates them. Before APK
assembly both manifests require the original module signature and the updated
module set must pass real installer verification.

For APK assembly, select a ZIP member-copy fixture to check that stored and
deflated members preserve exact payload bytes and compression type, including
an explicit replacement. The actual candidate/recovery comparison is
separate and needs the full ARM64 receipt and original module signatures.
