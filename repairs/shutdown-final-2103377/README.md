# Infinity 2103377 — targeted cooperative-abort correction

Resume parent: `603ef906e33927103b806a19dcf355586a468b75` on the completed
overflow-diagnostic lineage. This is a staged implementation delta, not an
integrated or signed final repair. All earlier runtime, lifecycle, Android tests,
native builds, trace/overflow work and locked branches remain unchanged.

## Implemented and reproduced

The checkpoint closes script admission, then notifies selected existing
`xbmc.Monitor` instances via `XBPython::NotifyScriptAborting`. Unlike the later
global engine-shutdown broadcast, the per-invocation checkpoint request has no
latch. A monitor registered or recreated after that notification misses it.
The global shutdown flag is still false while canonical participants must save.

`cooperative_abort.py` applies a two-file, exact-preimage patch to the green
XBPython source. A per-invocation latch is serialized with registration under
the existing native monitor-list lock. Only the coordinator-selected invocation
inherits the signal. Command Center and compatibility participants retain their
original operation. It changes no save receipt, thread-retirement requirement,
writer obligation, kill authority, deadline, add-on or normal running path.

`test_cooperative_abort.py` compiles the actual original and corrected Register
and Notify method bodies with controlled native peers. It reproduces three
deterministic failures (late registration, recreation and targeted inheritance)
before the patch and passes all nine corrected scenarios, including 1,000
concurrent registration/notification interleavings. These are host tests of
the real method bodies, not a complete native-engine build or physical evidence.

Apply only after the existing full-source reconstruction and shutdown-wide
trace transform. Verify both XBPython preimages against the complete green
native map, apply this delta, and update the candidate manifest with its two
postimages. Do not edit the historical green manifest or reviewed original
test files to accept this new candidate. The saved Java/native lifecycle pairing
remains mandatory.

## Latest actual evidence

Capture: `Infinity-Diagnostics-20261013-094401.zip`, SHA-256
`9336786dbf65e6d20a9fbd3c92a78083387e8b7ab4dc4a88ba71384f2dcc1781`.
Checkpoint failed after 25,087 ms. Playback, Command Center and compatibility
were committed; PVR was already durable. Eight Python services remained pending:

- script.artistslideshow:default.py
- plugin.video.jetproxy:service.py
- plugin.video.pov:service.py
- plugin.video.redlight:service.py
- plugin.video.seren:service.py
- plugin.video.thecrew:service.py
- plugin.video.themoviedb.helper:service.py
- plugin.video.tmdb.bingie.helper:service.py

The other settings/database save owners were downstream of stage 4, not proven
individually defective. Never turn their deadline-generated failed rows into
claims that their actual save routines ran and failed. Playlist Browser was
not in this pending list; no Playlist Browser bytes or behavior were changed.

## Recovered existing installed-source evidence

The earlier user-provided `Infinity-Installed-Addon-Code-20261008-071505.zip`
contains the eight services and dependencies. It was retrieved and inspected;
no new diagnostic APK or collector was developed. It is historical evidence,
not proof of every currently executed dependency.

Today's Seren addon.xml/service.py hashes and POV addon.xml hash match that
export. That does not prove current versions of the remaining service files or
all imported dependencies. The archived POV, The Crew and TMDB Helper service
entries and Red Light startup child contain `wait_for_am_trakt(timeout=120)`
loops that read settings and call `xbmc.sleep(1000)` without checking abort.
This is a concrete candidate for targeted cooperative-wait correction; the
capture does not establish that each pending invocation was in this function.
Do not blanket-dispose of these add-ons, alter their approved on-state behavior,
or skip their cleanup and pending data because the wait is slow.

## Exact open release gate

The eight current invocations have neither complete retirement/durability
receipts nor verified disposable-operation contracts. The capture does not
identify a safely cancellable current network request for each one. The new
latch corrects a reproduced race but is not proof that all eight will retire.

Before integrating a final repair, bind the exact current service entry bytes
and relevant dependencies to the recovered source, or enforce exact loaded-byte
preimages for any runtime source correction. Correct verified abort-insensitive
waits and specific optional work without suppressing essential cleanup. Preserve
unknown writes and every real save/retirement barrier; then run the full 274
Android tests plus new shutdown regressions, persistence checks, complete native
compile, matched lifecycle integration and original-identity signing.

This continuation did not rerun all 274 Android cases or compile a new complete
engine. Their accepted source hashes were checked unchanged. No final APK was
built or signed, and nothing was promoted, installed or locked. The user alone
approves physical-device behavior and any later lock.
