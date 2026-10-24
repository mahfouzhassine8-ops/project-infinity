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
