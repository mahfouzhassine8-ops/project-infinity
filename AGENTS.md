# Scoped exception — 2103420 one-APK Infinity/Cobra separation (Codex sole owner)

For branch `work/infinity-cobra-isolation-from-2103420-20261026` **only**, the user has explicitly authorized a **behavior-preserving internal ownership refactor** so Infinity and Cobra become separately versioned, separately owned modules within the SAME Android package, signed with the original key. **Codex is the ONE engineering owner** for architecture, coding, review, targeted test evidence, APK signing, and delivery. Read `repairs/dual-experience-isolation-2103420/ASTRA-PRO-MASTER-IMPLEMENTATION-BRIEF-20261026.md` (historical filename; header explicitly assigns Codex) and `repairs/dual-experience-isolation-2103420/EXECUTION-AUTHORIZATION.json` before editing. The original Cobra-off-limits policy below remains fully binding for all ordinary Infinity fixes and all Cobra *feature* changes; this scoped task permits ONLY necessary Cobra-owned structural partitioning with exactly unchanged Cobra functionality. Do not edit the locked 2103420 branch.

Keep ONE APK/one app icon/one Choose Your Experience; preserve every existing feature of both experiences, original signer and the user's settings/data. Infinity 2103420 Kodi, PiP, playback, Continue, Home and Essential-First shutdown are frozen. No shutdown mutation, new shutdown test, destructive data migration or independently distributed stale-side APK is authorized. A fully implemented latest-approved-combined release gate must reject stale Infinity/Cobra components and unauthorized cross-owner mutations **before signing**. If a protected shared-lifecycle edit is necessary, stop that particular change and report it, do not assume permission. The user alone accepts the finished candidate on the Fold.

---

# Permanent focused testing policy — user approved 2026-10-23

For every new corrective task, run only the tests explicitly authorized for that
correction. Record the correction and exact selected test before execution.
There is no implicit full matrix, regression sweep, shutdown check, or reopen
check. If no feature/test is selected, run no application tests. Do not infer
shutdown authorization from a navigation, UI, build, packaging, or APK request.

Use the manual **Infinity feature-only verification** workflow for the selected
feature. It must not invoke Normal Close, Essential-First, shutdown durability,
service-retirement verification, or unrelated runtime suites, including during
setup, teardown, or error handling. Do not reuse a shutdown-capable main runner
and merely suppress its result. The emulator may be disposed of by CI; that is
not an application shutdown acceptance test.

Use **Infinity shutdown verification - independent and explicitly selected**
only when the user explicitly requests that shutdown scenario. Keep its real
PASS/FAIL result independent. Never make it a `needs`, required status,
workflow-run trigger, artifact prerequisite, or aggregate gate for feature
verification or APK compilation/signing/packaging. Never turn failure into PASS
with `continue-on-error`. Unselected checks are NOT RUN, never PASS.

APK packaging retains compilation, permanent-signature, package identity, and
integrity checks. It does not run behavioral suites. Packaging may auto-run ONLY
for changes to specifically allowlisted build/source paths on the previously
user-authorized Infinity corrective branch, after the checked-in tracking/SCOPE.json
authorization and protected-source guard are verified. Manual packaging still
requires a scope note. This never auto-runs feature or shutdown tests.
Select behavioral tests independently when authorized. Changing test orchestration never authorizes weakening runtime
protections or altering the APK to make a test pass.

Preserve passing evidence and exact source/APK bindings; do not rerun completed
tests without an authorized correction-specific reason. Physical QA installation
does not mean release acceptance or final lock. Historical failure evidence is
retained; a passing selected feature does not claim untested shutdown behavior.

COBRA IS OFF LIMITS: no source, resources, settings, data, behavior, or indirect
shared-runtime changes affecting Cobra. No uninstall, data clear, database reset,
provider/cache purge, or unrelated functionality changes.

For a change to this policy or its workflows, run only the focused policy/routing
contract tests unless the user explicitly authorizes application execution.
See `docs/INFINITY-FOCUSED-TESTING-POLICY.md` for the supported workflow choices.
