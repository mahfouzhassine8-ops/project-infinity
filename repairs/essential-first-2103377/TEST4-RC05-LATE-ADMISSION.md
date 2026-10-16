# TEST4 RC05: stop new background admission at accepted Close

The exact RC04 early-upgrade retry in run **38945702659**, job
**117154485478**, failed after 25.719 seconds. Native evidence is preserved in
`evidence/test4-late-python-admission-38945702659.json`. Artifact **12070806322**
has SHA256 `c44a401d078384b114d66b057bc7a3a30444ef17183a1583d2464d5f174b573b`.

## What the new trace proves

At the captured native deadline, all **41** Python owners had been admitted
about **16 seconds after** the accepted native Close request. Their observer
initialization had only about nine seconds left within the original deadline.
The complete, untruncated inventory showed 31 at interpreter creation, five
at Kodi module initialization, four executing observer source and one
installing hooks. Zero were observed; zero Python blocking failures or
exceptions were recorded. This trace does not establish 37 identical hook
installation failures or implicate Diggz, the custom Infinity skin or retained
user data.

The coordinator deferred `BeginShutdown()` until core startup completed. That
kept required native startup operations alive, but also admitted the configured
optional services after the user had already requested Close. Those new
obligations then consumed the remaining deadline. The earlier Fold tracebacks
through `ctypes.PyDLL(None)` and the retained narrow read-only correction are
documented separately in `FOLD-OBSERVER-CLOSE-RACE.md`.

## Targeted correction

Native commit **92b5be7892a3a70f6a8daad2e235f77a9feaa7b8** closes new background
invoker admission at the accepted request, serialized with dispatch under the
existing manager lock. Native core initialization continues normally. Only
missing Command Center and compat save residents may bootstrap during the
pending startup window; the existing complete path/source-hash contracts,
unique resident checks and original deadline remain mandatory.

Rejected requests cannot reset/release existing invokers, reuse retained or
completed interpreter identities, consume quarantine retry requests, or create
new persistence obligations. Writers admitted before the cutoff keep every
observer, write and durability requirement. Normal startup after reopening
retains the configured enabled services. No add-on files, user databases,
custom skin, service settings or physical Fold data are modified by this fix.

The existing hard admission and protected-write gates still activate only
after core proof and every admitted observer are ready. The 25-second deadline,
16 required essential owners, Java seals, genuine-write failure behavior and
termination authorization are unchanged.

## Verification and current limits

- Fifteen new controls compile actual manager admission methods and the actual
  source classifier, including 37 concurrent in-flight requests, required
  bootstrap, forged/changed/duplicate/reused identities and retained failures.
- All 34 coordinator cases, six status serialization cases and the existing
  lifetime/escalation/quarantine control pass. Eleven observer initialization,
  five Close-race and eight progress cases also pass, including 37-interpreter
  initialization and fail-closed controls.
- Native **38957212563** passed host proof and the full ARM64 build.
- Matched RC05 Android **38957547396** passed all 308 regressions, signing and
  baseline preservation, fresh Close (13.319s) and 37-service loaded-upgrade Close
  (5.017s). Each passed all 16 essential owners, both Java seals, external
  whole-UID death, seven database integrity checks and saved-data reopening.
  Only pre-core cold-start Close failed, after 25.227s; promotion was skipped.
- The optimized-Python fixture ENOENT was corrected and has 12 passing controls.
  The SDK loader prerequisite now passes actual isolated setup **38957342018**
  and 18 controls. Earlier setup failures are not Android shutdown outcomes.

Internal load uses controlled services and verified retained test state; it is
not a clone of the Fold's full Diggz ecosystem. No RC05 APK is deliverable until
all internal gates pass. Physical Fold acceptance and final lock remain false.

## Latest failure and the physical startup boundary

The RC05 cold case now admits only two required residents and observes both
correctly. Native write admission starts, both ACTIVE checks pass and playback
commits at 24.127 seconds. Command Center's PREPARE confirmation is incomplete
at expiry. In-flight buffers and `flock:129` are recorded, but their exact file
identity was not captured; they are not proof of a durability error or deadlock.

Read-only comparison with the actual Fold files shows `initialize done` at
04:10:10.998 local and Close at 04:10:15.907: core initialization finished
4.909 seconds before the Fold request. The RC05 emulator case requested Close
13.392 seconds before core completion. These are different startup phases.
Evidence is preserved in
`../android-checkpoint-shutdown/runtime-tests/evidence/rc05-startup-phase-comparison.json`.

A separate optional comparison reuses the exact signed APK with SHA256
`5103a01db85129e9e2f3a9c8f08dc97c7e2433e6491ee0011bfe7e6713f96cfb`.
It waits for genuine current-process core initialization while requiring
unready services and actual pending native observers. The existing cold
stress remains recorded as failed. No engine changes, repeated green tests,
new signer, APK promotion or final lock are part of this comparison.

Isolated comparison **38963791371** is running from `ccf1a103`; its workflow
checks the 21 new host controls and saved input identities before starting the
AVD. It cannot build or promote an APK. Its outcome is pending.
