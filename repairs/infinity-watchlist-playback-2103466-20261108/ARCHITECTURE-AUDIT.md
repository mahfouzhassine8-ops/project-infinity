# Independent Astra review of the integrated Phase A design

Verdict: **suitable as a conditional Phase A design; not implementation-ready or
complete-feature approval.** Astra performed read-only source review and a second
independent audit after GPT-6.1's design was integrated. No edits or tests by either
supporting agent.

The existing player/store owner, schema2, thresholds and persistence remain the
correct architecture. The saved-card resume join is source-supported. Seven
existing production files plus at most one authenticated helper is a plausible
scope ceiling; it must not silently expand.

Required qualifications incorporated in the plan:

- Lineage must prove the selected item and its navigation generation through the
resolver/active item; matching URLs, cached/copied properties or saved membership
are insufficient. Specify invalidation and bounds before implementation.
- Keep lineage independent of recovery ticket success/failure/cancellation and
return values. No new native locking or RPC/network work in critical sections.
- Canonical legacy proof views are opt-in for saved playback. Globally changing
identity equality, progress grouping or checkpoint helpers risks unrelated behavior.
- Saved-row progress matching must be exact, fresh, conflict-aware and respect
hidden/completed state. Do not substitute a show's newest episode or revive an
older hidden alias. Preserve routes and folder navigation.
- Actual Umbrella episode-emitter evidence is incomplete; public same-version
source is not proof of installed bytes. Do not globally expand playback contracts.
- No verified nonlibrary successor catalogue/interface has been established.
Filtered provider directories are insufficient; no installed TMDb Helper version
is assumed. Missing proof safely withholds next-up but does not complete the feature.
- No generic movie-recording failure was proven. The demonstrated movie issue is
saved-card progress projection. No player logic, lifecycle, shutdown, provider,
Search, authentication or Cobra change is justified by this investigation.

Phase B needs explicit owner authorization for the exact scope. Origin and
catalogue contracts must close before implementation. Additional source files or
dependencies require a revised review. Baseline owner approval is separate from
feature acceptance and automated Search clearance.

Astra then reviewed the actual written artifacts. The review confirmed the
conditional verdict and Watchlist-only scope, and identified two ambiguities
corrected before handoff: preserve existing player/local-library JSON-RPC while
forbidding new blocking metadata work in callbacks; and apply the120s threshold
only to new partial entries, preserving baseline ended/95% completion even for
short content. No further material scope misrepresentation was found.

GPT-6.1 also reviewed the written plan. Its completion-threshold correction was
incorporated, including unknown-duration natural end. It identified direct-click
freshness as an unresolved subcondition of the launch protocol: current raw
provider URL dispatch does not already perform a fresh Python progress read.
The plan now explicitly requires a reviewed solution and a stale-render/direct-
click test before implementation can be considered ready.
