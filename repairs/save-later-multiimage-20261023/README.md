# Save for Later / multi-image corrective investigation — NOT RELEASE READY

This work continues the passed RC8 foundation. It does not replace or restart
the universal persistence/RC8 repairs. Protected baseline: 2103400. Current
experimental package remains 2103401. No APK version or release identity has
been invented. Required component versions are derived from the actual input:
Command Center 0.3.5.29 → 0.3.5.30, Watched Bridge 1.0.10 → 1.0.11 and UI Repair
0.1.12 → 0.1.13. Native compilation/signing is handled by the isolated corrective
workflow; its result must pass the remaining runtime gates before delivery.

## Evidence and limits

- The supplied saved entry contains a typed show identity: TMDb 330430,
  TVDb 482439, IMDb tt48447471. Its POV destination is
  `mode=build_episode_list&season=all&tmdb_id=330430`. Saved/profile data was
  inspected read-only. No entry, membership, progress, database or account was
  rewritten.
- The published POV 6.10.21 manifest hash matches the physical export:
  `b73187d59e01a91f279cba5666aad1488850ec27b30430174288d2efd1961af5`.
  Its actual route table supports that endpoint, and its episode implementation
  explicitly handles `season=all`. A matching manifest does NOT establish that
  every installed source file matches the published distribution.
- A live read-only request through the published metadata functions initially
  failed. A follow-up returned HTTP 200, the exact Relationship Rehab title,
  and both saved external IDs. This does not justify an identity correction or
  substitution. The HTTP transport peer is not the installed Kodi runtime.
- The new 212-entry physical archive `Infinity-Universal-Trace-20261023-020632.zip`
  (SHA-256 `8eeaffeb5620b56e09266e96b89ea6e3610c957a466eafc05f87241060eea3ab`)
  contains the actual POV cache reader. It matches the published source exactly:
  `0cbb93769c9867a61d0faf31140510c19f3f8bbe6c1c0f312bd7cfd9e862de46`.
  The recorded invocation reaches POV's episode handler, metadata parser and
  cache reader, then fails at `meta_cache.py:78`: string `expiry` is compared
  with integer `current_time`. Infinity did invoke the requested provider.
- Executing that collected reader reproduces the exact exception before a DB
  read. The current published timestamp generator returns an integer and its
  JSON round trip preserves it. Both a string-expiry array and a two-key object
  reproduce the exception. SQLite TEXT in an INTEGER-affinity column can also
  propagate through this reader into memory. These are verified mechanisms,
  not proof of which malformed payload/producer existed on the Fold: that value
  and its database were not exported. No cache was cleared or coerced.
- Original `plugin.py` and `experience.verified_source` replay saved show URLs
  without verifying their current installed navigation contract. This generic
  gap is established in source. The new traceback establishes a separate cache
  failure after provider dispatch. The resolver detects failed requests and
  offers an explicitly selected compatible alternative with the same typed IDs.
- Successful native Close has no unknown jobs. The failed Close retains job
  313/token 314, operation `multiimage`, type
  `N14CGUIMultiImage14CMultiImageJobE`, phase
  `completed_without_owner_receipt`. The failed session's other 15 essential
  owners passed. This is distinct from the earlier TMDb Movies observer failure.
- Existing diagnostics do not identify job 313's directory/control or establish
  that the failed saved-item selection caused it. The recording starts after
  the job's approximate admission time; earlier clicks are not excluded.

Private diagnostics, recording, profile, opaque routes and playback/account
URLs are NOT checked into this repository.

## Experimental source work

`saved_navigation.py` is an Infinity-owned, later-only resolver. It reads typed
identity independently of a saved URL, obtains a fresh provider result, checks
IDs and installed API behavior, validates its destination and reports failures.
The URL preserves provider preference only. Another provider requires an explicit
selection. Titles retrieve candidates but never authorize matching. Episode IDs
are never reinterpreted as parent-show IDs. Continue Playing/Search code stays
unchanged. No saved-state mutation or automatic removal is introduced.

`provider_contracts.py` derives reviewed API shapes from pinned distributions.
Matching is based on source behavior, not provider names. Per-invocation raw
source/manifest hashes and enabled state are rechecked. A future provider with
the same reviewed API shape is supported without a core-name exception.
Comments, docstrings and manifest-version updates do not invalidate an otherwise
identical API; real API changes require a reviewed adapter. No claim is made
that every future add-on implements these APIs.

`native_contract.py`, `multiimage_methods.inc` and
`InfinityMultiImagePersistence.h` describe a narrow experimental native contract:

- Exact job and callback implementations are required, not class-name strings.
- Work stays mandatory until the existing completion/callback receipt passes.
- Actual audited POSIX/special-directory dispatch can establish an unchanged
  outcome, without changing original job results, exceptions or callbacks.
- Extension-driven binary handlers, network MIME paths, unreviewed backends,
  derived controls/jobs, opaque work and exceptions remain blockers.
- APK directory dispatch is intentionally NOT certified here. Its original
  `zip_open(..., 0)`/close behavior requires a separate complete dependency audit
  before any such path could receive an unchanged receipt.
- No JobManager, Python observer, transaction, native writer, protected-file,
  admission, termination or GUI waiting policy is relaxed.

## Verification checkpoint

Host results are in `qualification/`. The native harness compiles the actual
GUIMultiImage/JobManager implementations and audited directory/texture-path
functions, with documented GUI/service peers. Candidate: 32 production-source
cases. Original-source negative control: 32 cases, retaining the blocker.
The navigation suite has 16 test methods covering three real reviewed source
distributions, a simulated future compatible provider, identity/route errors,
disabled/updated providers, original profile read-only checks and later-only
hook isolation. Directory responses are mocked: these are NOT actual provider,
Android 17, playback, Close/reopen or physical Fold navigation acceptance.

The source/component staging tools are experimental. Do NOT install an isolated
staging output. Exact native owner pins and dependent controller pins are updated
together. The startup verifier adds an exact nineteen-file CC30 contract while
retaining all earlier branches. Only the verifier class may change in DEX; all
other definitions, including Cobra, Search and RC8 Close/receipt code, are taken
from the original signed DEX and checked. Native source changes comprise five
original files plus one new header; the other 9,399 inputs remain identical.

## Outstanding gates

1. DONE: use the collected cache reader and physical traceback to establish the
   first failing comparison. Preserve the unknown original cache-producer detail.
2. Execute actual provider navigation, not only mocked directory responses, and
   demonstrate the original affected entry opens its correct content.
3. Verify minimal deployment/source pin binding and Cobra isolation in the build.
4. Run retained universal/RC8 protection tests, integration tests and full exact
   ARM64 compile with source inventory before/after. Reuse RC8 binaries where
   unchanged; do not rebuild/rewrite unrelated functionality.
5. Verify signed APK/member delta, permanent certificate, exact changed-only
   component ZIPs and real API37 Close/reopen/negative-control tests.
6. Complete physical Fold checklist and user acceptance before claiming resolution.

Only this new repair directory contains local repository changes at this
checkpoint. Cobra sources/assets/DEX have not been changed. No installed
application, provider code, profile, database or user data has been modified.
