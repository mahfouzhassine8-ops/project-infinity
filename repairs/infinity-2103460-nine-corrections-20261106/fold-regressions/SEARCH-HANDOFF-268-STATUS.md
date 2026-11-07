# Infinity Search All — source correction ready for original-key signing (268/269)

**User request:** Correct Crew and Nixtoons Search through the existing authenticated Command Center quick-update system; do not rebuild the APK unless native cause is proven.

**Status:** Implemented in source, **13 exact-source local host checks PASS**; the original-key signer workflow has **NOT run for this commit**, so **no new installable 268/269 ZIP exists yet**. This is NOT a full `state_changed` fix, nor proof of heading navigation on Android.

## Confirmed cause and limitation

2026-11-07 user diagnostic: the existing Search All aggregate rejected two completed Nixtoons requests with 31 original results each and two completed Crew requests with 2 original results each. All four changed the provider's settings-file metadata. Exact writer and intermediate meaningful/ABA changes are not proven. **Do not accept those existing rows just because the endpoint settings XML looks unchanged**. Existing `_query_signature` and `_provider_result` remain byte/AST unchanged.

## Functional script-only correction

1. The **266 explicit provider form path** still opens the original source-verified provider URI directly, rather than aggregate Search All. It stays unchanged.
2. When **Search All** rejects a completed response with `state_changed`, the provider heading now opens a **new first-party `search-open-verified` action** on the user's tap (and has a matching context-menu action), instead of reusing the original invalidated aggregate response.
3. The first-party action discovers the current verified provider by exact ID/media, runs the existing source/dependency/enable/pin checks using `route()` twice, binds the current Kodi profile, rejects changed/unsafe routes and app-abort, finishes its temporary directory and then requests normal Kodi Videos navigation to the fresh original provider URI.
4. Failed verification **does not dispatch**. Previous aggregate rows are **not republished**, stale cached results are not transplanted, no query or route is logged, and no additional request starts until the user explicitly clicks. New `INFINITY_SEARCH_NAV` events record only provider ID and outcome so an unobserved native click is distinguishable from a verified handoff requested.
5. The user-facing rejected heading says **Open fresh provider search**. This does **not** claim that the `state_changed` validator is now capable of safely accepting benign settings writes. That separate full acceptance repair remains open pending complete writer/ABA evidence.

## Exact files/verification

Only the two Search runtime Python files changed against original signed266 source:
- `repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py` SHA256 **ae7c456c5a3ba5c66080df9fd619bce722bf0cdb9736d22e9127923410cc7c06**
- `repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/plugin.py` SHA256 **65960f264c6564749c8f1c88da93cd3e39cda922a2a073ee1469030d7db1bf35**.

Local Python AST compilation PASS, **13** host checks PASS on the exact 266 signed artifact source, and original signed266 manifest verifies using the original permanent public key (openssl Verified OK). Tests include invalidated non-publication, correct fresh URL shape, verified double route/profile checks, disabled/malformed/source-changed/aborted refusal, attempted endOfDirectory before Kodi builtin, privacy-safe logging, and AST identity of the strict original route/native lease/settings/ABA guard functions. **Not Android execution or actual provider navigation**.

The source inventory pins both new SHA256 values. The original full Kodi add-on packager and only original signing workflow are retained, with skin generation advanced to **1.0.5.268** and forward recovery **1.0.5.269**; Command Center stays **0.3.5.61**. **Critical gate repaired**: because the Command Center payload changed from signed266, the real original Java installer/recovery audit must run fresh; reuse of 266's host evidence is refused. The test script is run before signing when the workflow is dispatched.

## Signing and physical acceptance

Use the existing sole original-key workflow, not a new signer:
- Workflow: `.github/workflows/infinity-combined-release.yml`
- Branch: `work/infinity-2103460-nine-corrections-20261106`
- Dispatch operation: **`package-nine-quick-updates`**
- Expected artifact: `Infinity2103460-Authenticated-Quick-Updates-<run id>` containing complete native Kodi **Command Center corrective and recovery ZIPs**, skin268 corrective and skin269 recovery ZIPs, original-key module and outer envelope signatures, SHA256SUMS and fresh real-Java test evidence.

**Do not install from an unsigned local or source ZIP.** No key is available in this workspace; only the sole original-key workflow can authenticate revised Command Center scripts.

**When an installer exists and its signature/recovery gates PASS:** Controlled Fold test uses the user's installed APK2103462 and active skin262/CC61 without APK replacement. Explicit Crew/Nixtoons form selection, then Search All provider heading, original query results and native navigation. Capture the first `INFINITY_SEARCH_NAV` event and corresponding native Kodi navigation if the heading still fails. Preserve four physical passes (Power, Movies, TV, Downloads) and Cobra/Preview. Search-crash stress remains **UNTESTED**; genuine history/identical-settings writes remain rejected by aggregate and require separate proven correction.

**Verdict:** Real script-level fresh verified handoff prepared and locally tested; no full Search All settings-validation repair and no signed installer or physical PASS yet.
