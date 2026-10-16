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
- Native **38957212563** passed host proof; its full ARM64 build is in progress.
- Matched RC05 Android **38957547396** waits for that exact native success, then
  requires fresh production Close and separate retained-upgrade early/loaded
  shutdown cases. All 308 regressions, both Java seals, essential receipts,
  whole-package death, database integrity and saved-data reopening remain gates.
- The optimized-Python fixture ENOENT was corrected and has 12 passing controls.
  The SDK loader prerequisite now passes actual isolated setup **38957342018**
  and 18 controls. Earlier setup failures are not Android shutdown outcomes.

Internal load uses controlled services and verified retained test state; it is
not a clone of the Fold's full Diggz ecosystem. No RC05 APK is deliverable until
all internal gates pass. Physical Fold acceptance and final lock remain false.
