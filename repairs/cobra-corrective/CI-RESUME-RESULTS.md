# Corrective continuation — execution record

## Run 38204812804 — failed, no APK

Source commit: `6d55b72bf5786772c470352dc504e3fbc2741873`.

- Gates A/B and all four host guard tests passed.
- 198 Android tests executed: 184 passed, 14 failed, no skipped cases.
- All 167 inherited cases passed. Seventeen of 31 new corrective cases passed.
- The attached six-context inventory passed, including dirty saved-focus Mobile isolation. This is not acceptance of the failed workflows or all lifecycle transitions.
- Android donor assembly, packaging and permanent signing were skipped by the workflow.
- Evidence artifact: `11726443648`, SHA-256 `47310e63bc49b16186780744766991265e0a934ff575ddd6be443afb479f4a62`.
- Run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/38204812804

## Failure triage and next gate

Nine failures were traced to test selectors: existing Channels category buttons expose stable tags rather than the descriptions the test requested; Last Channel has a dynamic description. A separate test incorrectly assumed every Sports-owner Back route creates a guide, although the approved Compact/Cards/Grid route opens the standalone Sports Hub.

Touch callback dispatch, chooser scrolling, Activity recreation attachment and stopped-Pro routing remain blocking until properly exercised and verified. Stats screenshots must also wait for the original sheet animation and assert visible panel geometry; finding text in the hierarchy alone is insufficient. No assertions may be bypassed, no cases skipped, and no runtime source correction is justified merely by these test-setup failures.

The next workflow includes one focused reference suite compiled from the untouched 264-file approved transport source. It captures five exact return-path states. The identical test then runs on the candidate, and the gate independently compares every recorded field, source hashes and test identity. This phase does not assemble an APK or rebuild native code. The candidate retains the existing 31 tests, adds that one comparison test, and retains all 167 inherited cases.

Only an actual passing rerun can clear the gates. This record does not claim that the next run passed or that a signed candidate exists.

## Run 38205359098 — fixture compilation failed, no APK

Source commit: `17329e48f0a63a6050b8c8bad5433236b1040e47`.

Gates A/B passed. The new approved-source reference phase failed to compile because its reused Handoff fixture references `CobraProSeason317Test`, which the isolated reference project had not staged. No reference or candidate runtime test executed in this run, and assembly/signing were skipped. The staging list now includes that unchanged dependency; no production code or assertion changes are involved.

Evidence artifact `11726967151`, SHA-256 `345bbf8b2520b3129c9d3d916ce0b3fc301aaa1e50e077301b4ed6ff7e987af8`.

Run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/38205359098

## Run 38205532514 — three runtime checks remain blocked, no APK

Source commit: `08547352ebc1ed3f24b4902a2a360e15eeb8e454`.

Gates A/B and the untouched-source routing reference passed. The candidate executed 199 tests: 196 passed, three failed, none skipped. All 167 inherited cases and the candidate-versus-approved routing comparison passed. Assembly and signing were skipped.

Unresolved failures (not waived):

- Initial local-rewind construction test expected its controlled player but observed null at line 128.
- Actual Activity recreation encountered a Robolectric `ActivityController.windowFocusChanged` null precondition during `recreate` at line 94.
- The Channels filter matrix did not locate another selectable channel in the Groups fixture at line 97.

The attached six-context fullscreen inventory passed, as did the real broadcast chooser callbacks, four-row sizing/vertical scrolling, mini/fullscreen PiP session checks, preview PiP five-size geometry and touch checks, Stats data/visibility, and theme tests. Additional explicit post-PiP/recreation hierarchy and different-channel identity assertions remain pending execution; these must not be inferred from inventory or session assertions alone.

The rendered portrait Stats panel, broadcast chooser and 412x915 preview PiP were inspected. Stats is visibly presented (not just found in the hierarchy); the chooser has more than four complete visible choices; the new PiP label fits without moving the original Unmute or status controls. Screenshot evidence is automated rendering, not device acceptance or live provider verification.

Further visual review invalidated this run's claimed five-size geometry coverage: window qualifiers were changed after each Activity was created, so four preview PNG dimensions lagged their requested size by one iteration. The next test-only follow-up creates each Activity after setting qualifiers and asserts both measured and laid-out decor dimensions before accepting geometry or screenshots. The passing geometry test names above are raw run results, not accepted size evidence. No size case is removed.

Evidence artifact `11727530866`, SHA-256 `9236113afaa59a80c2641c102a1ac6f8bfae233aafc6217d81e746d7af364d2b`. Its downloaded ZIP passed CRC checks.

Run: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/38205532514
