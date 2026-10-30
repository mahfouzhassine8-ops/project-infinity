# Actual non-Pro inline preview host results

Signed429 and baseline27 each pass all three selected native view-dispatch checks: 60 actual presses per version (48 coordinate,12 remote), with Mobile/Compact/Cards/TVGrid active and Profalse asserted throughout. This does not reproduce the physical user's Fullscreen/PiP/More mismatch. No production patch or Fold acceptance is established.

Native429 More remains index6 across mode reuse; baseline27 retains its original index4. Every Fullscreen resolves to fullscreen, PiP follows its original fullscreen+PiP handoff, and More reaches More. Original callbacks/player routes are exercised; terminal fullscreen/menu/platformPiP actions are explicit host spies.

`COMPARISON.json` binds production DEX, translated JARs, test-source phases and all evidence hashes. Initial and retained methods were not rerun after passing. Their test bodies are unchanged in the final source. The retained method passed in an overall failed two-method run; that complete original FAIL remains archived. The failed geometry method alone was rerun after a QA viewport correction. All fixture failures remain separate, including attachment and actualWindowManager clipping failures. Narrow/wide results use separately attached windows and do not establish dynamic fold/window reflow acceptance.

No Pro entry, native playback, OS PiP, provider, shutdown or physical Fold acceptance is claimed.
