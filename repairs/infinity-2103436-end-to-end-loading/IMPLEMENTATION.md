# Continuation from 925a87e3 — implementation saved, release blocked

The authoritative input remains original-key signed 2103436, source
`7bbe08363b493146ca7ed67cb872e9a98b1d888b`. Its lock and artifacts are unchanged.
This continuation does not reserve a version, authenticate a replacement module,
create an APK, invoke a signer, or promote a baseline.

## Production changes implemented

- Preserve the previous independent-completion, profile ownership and background
  resize corrections. Separate foreground retirement from the all-work cutoff:
  leaving an item must not discard an independently queued background start.
  A focused test first reproduced that remaining defect, then passed the fix.
- Bind selected loading to a window-local token, rather than a fixed list of
  four window IDs. Read local frame capabilities and the actual modal owner.
  Real Linux Kodi exposed `9999` as the no-modal sentinel; the implementation
  now explicitly preserves the base window for that value. That error was
  caught in unshipped code, not introduced into signed436.
- Keep an observed navigation cue through actual Kodi busy state. Dispatch
  without observable busy work still clears; a returning builtin is never
  treated as destination readiness or a reason for a fabricated wait.
- Extend the existing shared border include to existing eligible bordered
  buttons/focused layouts. Register 65 window XMLs through static include
  reachability. Add 219 border instances and 913 notification pairs around
  existing explicit actions. These are source counts, not tested workflows.
  Duplicate routes are checked per control, not suppressed file-wide.
- Restore native `DialogBusy.xml` fallback by removing its unconditional
  `visible=false`. Its original controls and progress identity remain intact.
  **This is a safety correction, not a completed drawer-only visual solution.**
  The original panel can still appear, including alongside a frame. There is
  no proven all-window visibility contract that safely permits hiding it.

There is no provider prefetch, duplicate original action, new worker, new poll
interval, navigation timer, forced destination-ready event, or stored-data change.
Implicit Kodi list navigation is not intercepted. Progress/error dialogs retain
native behavior. Player/OSD/audio/subtitle/seek/volume/visualisation and shutdown
XML paths are excluded from the expansion. Native libraries and services are
not edited. Search selection, providers, plugin routes, service.py, playback and
persistence remain original signed members.

## Focused evidence

- Original 16 host cases preserved and rerun once after the new cancellation
  boundary changed the state machine: all pass. The rerun reason is in SCOPE.
- Eleven new generated-source/monitor checks pass, plus the new cancellation
  regression: **28 distinct focused host cases** in total. This is not a broad
  application regression matrix.
- A real, isolated **Debian Kodi21.2 Linux renderer fixture** passes 25 assertions:
  Home/custom-window ownership, selected/background state, actual Kodi Select
  dispatch, one original handler per press, Back and terminal cleanup. Nine
  pixel-presence/absence checks confirm captured cues and cleanup. Actual native
  action/dispatched notifications were received, not directly invoked callbacks.
- The fixture uses exact staged border definitions/textures and current observer
  source. It does not load the full production skin, signed Android host, user
  profiles, providers, protected services or shutdown. Its illustrative controls
  are not approved UI screenshots; no exact full-skin visual parity is claimed.
- Reduced-motion capture uses the existing still texture. No production animation
  asset, geometry, font, color or optional-motion rule was changed.
- Final unsigned Infinity round-trip: **7,518 members; 90 changed, 7,428 identical;
  zero added/removed**. Every changed member is enumerated in
  `results/STAGING-PRESERVATION.json`. Original XML actions/control geometry are
  preserved after removing only the new marker-bound observers/frame calls.
  Python AST outside seven explicitly allowed functions is identical.

The unsigned component is deliberately **not installable**: original module
manifests/signatures are retained until the legitimate authentication pipeline
runs. These checks do not substitute for final signed-APK member comparison,
Cobra component equality, original-key signing or install-over gates.

## Runtime evidence provenance

Official Debian packages were downloaded through the inherited proxy with APT's
signed repository verification into `/tmp/infinity-kodi-renderer`; packages were
extracted locally, not installed into the system. No APK/native library was
replaced. A disposable Xvfb/Kodi profile ran the finite fixture. Disposal is not
an application shutdown test. The original recordings were not accessible and
were not inspected.

The native fixture attempts are retained rather than overwritten:
1. New dialog-owner implementation failed on actual no-modal ID9999; corrected.
2. State checks passed; screenshots taken immediately after property changes
   captured the preceding rendered frame. No production timing was changed.
3. A fixture-only rendering turn before capture resolved that observation issue.
4. Added actual Kodi Select/Back dispatch and invocation counting.
5. Enabled a non-service QA add-on registration to exercise the original XML
   enabled-addon guard and prove native NotifyAll delivery.
6. Current source rerun after foreground retirement was separated; all25 pass.

No repeated Android emulator attempt, diagnostic APK or signing run was used.
`LINUX-RENDERER-BINDING.json` binds the current Python and exact rendered include.
The original failed attempt and intermediate successes remain separately labeled.

## Remaining release-critical work

1. **Native fallback design is incomplete.** Restoring truthful native feedback
   prevents invisible busy UI, but does not establish the approved drawer-only
   appearance on all native/dialog surfaces. Control.IsVisible alone does not
   prove ancestor visibility or clipping; a stale service property is not a safe
   basis for hiding required Kodi feedback. Do not ship this as visually complete.
2. **Full Android workflow readiness/visual tests are unavailable.** This workspace
   has no attached compatible ARM Android target or local adb/KVM. The existing
   API37.1 x86 native-bridge evidence failed inside unchanged libkodi.so constructors
   before Python (run40726662543). That is historical evidence, not a new436 test.
   Linux fixture success does not clear this Android gate. No blind retry was made.
3. **The reported approximately75-second delay remains unmeasured and unresolved.**
   Video20741 bytes are unavailable. Static source does not identify its tap or
   provider execution. Two plain Videos routes exist in Library/Discover, but
   neither is proven to be the recorded action. No delay reduction is claimed.
4. **Release integration/authentication and signed binary gates remain NOT RUN.**
   Do not invoke the signer while the implementation/readiness gates above remain
   open. A candidate APK therefore cannot yet have matching signed components,
   a build URL or new checksums. Signed436 remains the protected recovery release.

The next meaningful runtime step requires a reachable compatible native-ARM
Android target running the signed baseline and the owner-authenticated candidate
through the established release mechanism. No shared/native repair or relaxation
of integrity checks is authorized or proposed. Physical Fold acceptance remains
exclusively the user's; this checkpoint is not acceptance and must not be locked.
