# Isolate actual-source cost before a production patch

Selected feature: **infinity77-ui-cost-comparison** on unchanged signed77.
This is a distinct, bounded comparison, not a repeat of completed Home/Hub/frame/loading/warm-return cases.
Existing run42811609761 completed those selected observations. Physical Fold and full release acceptance remain pending.

Observed preparation context/setup cost fell1253.8→51.8→15.6ms as the emulator warmed; loading publication
also varied. Do not attribute the full cold delay to one API or announce a batching improvement without measurement.

Exact selected experiment after normal fresh-VM setup and real resident readiness:

1. Seven alternating AB/BA pairs call the **same original signed** `action_loading._context(xbmc,gui)`.
   A per-call diagnostic SDK adapter delegates all original reads; the B variant routes only the six named
   current-control ListItem expressions through the existing `XBMC.GetInfoLabels` message. No global/module
   state or production function is monkeypatched. Repeated Home9000 reads remain original calls. Each adapter
   is discarded after one invocation; no cross-context cache exists. Record raw times, bridge calls, fallback,
   complete context equality and unstable pairs. No gain may be claimed from unequal/fallback results.
2. Invoke original signed `common.skin_baseline_integrity()` once, read-only, after normal resident startup.
   The protected manifest covers948 files/43,793,653 bytes. Record import cost separately from function cost.
   A warm filesystem cache may apply. This is not a measurement or attribution of the original cold21-second span.

The prototype uses explicit dependency parameters already present in `_context`; it does not replace the
resident observer, its service, source-loader contract, settings, database or native GUI code. All six exact
expressions use standard native TranslateString/GetLabel DEFAULT_CONTEXT; generic Python untranslated-label
fallbacks differ, so invalid/missing/nonstring/error batch results fall back to the original per-label calls.

No native frame, initial idleCPU, provider, playback, Cobra, shutdown or physical-device test is rerun here.
Fresh start/authentication is required disposable-VM setup only. Operation-specific diagnostic reply budgets
are90s; these are not relaxed UI/loading acceptance deadlines. The existing resident-readiness limit remains60s.
Failure remains visible, and no production version, APK build, signing or owner installation is selected.

Selected offline adapter checks: valid exact strings including empty; malformed/missing/nonstring/error/wrong-id
fallback; control0/wrong-control/unknown expression passthrough; repeated Home reads not cached. These protect
the experiment's attribution and do not establish a production performance PASS.
