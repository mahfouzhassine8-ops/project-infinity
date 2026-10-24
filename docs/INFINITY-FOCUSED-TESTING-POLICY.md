# Infinity focused verification

User-approved permanent policy, October 23, 2026. This changes test orchestration
and reporting; the installed APK's shutdown and persistence protections remain
unchanged. Build 39994772688 and its eight passing runtime-mode records are retained.

## Select the correction, then its test

In GitHub Actions, choose **Infinity feature-only verification**. Supply the
corrective source/test branch or exact commit, existing signed build run, the
user-authorized scope, and exactly one feature. The default is an invalid
placeholder: omitting a real selection fails before any application test runs.
There is no push trigger or automatic full matrix.
Workflow definitions are registered on `main`; runtime code is checked out from
the supplied corrective `source_ref`. Run policy contracts from that corrective
checkout, which contains the current harness and packaging sources.

| Selection | Executed feature checks |
| --- | --- |
| saved-navigation | Existing saved TV route, affected TMDb 330430 failure/recovery, exact Umbrella favorite episode reference, original Movie/Continue Playing routes, saved-state preservation |
| provider-pov | Actual POV Movie/TV resolution and original saved-route preservation |
| provider-umbrella | Actual Umbrella Movie/TV resolution and original saved-route preservation |
| provider-seren | Actual Seren Movie/TV resolution and original saved-route preservation |
| provider-future | Compatible future-provider resolution, rejection of unrelated destinations, original saved-route preservation |
| multiimage | Actual tested GUI image-job BEGIN and corresponding verified retirement only |

These are explicit test groups. Select only groups authorized by the user's
correction. For a narrower/new correction, add a named narrow case first; do not
silently broaden to an existing group. Provider initialization is limited to the selected route and its retained
Movie/Continue Playing source fixture. It is not authorization to test all providers. No feature
group executes Normal Close, Essential-First admission, durability, process-death
acceptance or reopen. The feature report records shutdown as **NOT RUN** and
depends only on the selected feature. CI disposes of the fresh emulator afterward.
The feature harness refuses existing installations and physical devices.

## Independent shutdown workflow

**Infinity shutdown verification - independent and explicitly selected** has
only a manual trigger and requires an explicit scenario and authorization note.
Each scenario's retained test includes its existing setup/navigation preconditions
and Close checks; the selected `safe` scenario retains the three Close/reopen cycles.
Negative controls and provider-specific scenarios are individually selected;
there is no automatic matrix. The optional startup close profiler is off by default.

Failure stays FAIL in that workflow and its evidence. It is not a dependency of
feature checks or packaging, is not converted into a passing result, and must not
be configured as a branch/ruleset required check for those independent outcomes.
Do not select it for a feature-only task. Its scripts and all previous failure
artifacts remain available; APK persistence safeguards are untouched.

## Packaging and reporting

**Infinity corrective APK packaging - independent of runtime tests** supports
both manual dispatch (with an explicit authorization note) and automatic builds
when reviewed source or this build workflow changes on the previously authorized
`work/infinity-saved-route-correction-20261023` branch. The push path filter and
the unchanged tracked `tracking/SCOPE.json` authorization are required for the
automatic route; no other branch or unrelated edit can start this build.
Source reconstruction, ARM64 compilation, permanent signature, install-over
package identity, and member/source integrity still gate the package. Packaging launches no behavioral suite and neither downloads nor
requires shutdown results. `VERIFICATION-STATUS.json` records both feature and
shutdown verification as **NOT_RUN_IN_PACKAGING**; separately executed reports
retain their own APK/source/run identity. Missing or failed shutdown reports do
not block package creation. Compilation/signing/integrity failures still do.

QA APK availability, selected-feature PASS, full release acceptance, and final lock
are separate decisions. This policy does not erase old failures or claim that an
untested behavior works. No APK rebuild is needed to apply this CI policy.

## Verification of this policy change

Only `.github/scripts/test_infinity_focused_policy.py` is run for the policy
change. Its mocked transport tests check dispatch isolation, selected-feature
routing, truthful NOT RUN results, manual-only workflows, and rejection of
termination/reset commands. They are not Android execution or physical Fold
acceptance. Do not launch device feature or shutdown suites merely to validate
workflow separation.

Policy-change validation: **14 focused contract tests PASS**. Shell and embedded
Python syntax checks pass. Android feature, shutdown, and physical Fold tests were
**NOT RUN** for this orchestration change; no APK was rebuilt or modified.

For the authorized tracking/navigation continuation, the feature workflow also
provides `tracking-recovery`, `tracking-actions`, and `tracking-continue`.
Select one explicitly, supply its authorization, the newly signed build run, and
`work/infinity-saved-route-correction-20261023` as `source_ref`. These cases use
the real provider/GUI paths on a disposable emulator, leave the app running,
and report physical Fold acceptance separately. The existing provider-only
choices remain independently selectable. Do not select the historical
`saved-navigation` case for a CC32 recovery-memory write: that earlier case
asserts that all saved bytes remain unchanged, before recovery memory existed.

## Restored authorized build automation — October 24, 2026

The prior manual-only packaging change unintentionally blocked normal build
handoff. A scoped push trigger now starts **compilation, signing and packaging**
for the already-approved Infinity corrective branch and only its listed source
and build-workflow paths. The tracked authorization guard must pass before
artifact downloads or compilation. Manual build dispatch remains available.

**Feature and shutdown workflows remain manual-only.** No automatic runtime
verification, no Close/reopen test, no weakened persistence, and no new release
acceptance are implied. Previous failures and unused test cases remain recorded
as FAIL or NOT RUN. This workflow change itself is a build trigger, so its
signed-candidate result must be reported truthfully; a queued or failed build
is not a deliverable.
