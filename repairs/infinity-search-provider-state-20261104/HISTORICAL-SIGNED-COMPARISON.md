# Signed Infinity Search historical comparison — completed 2026-11-04

**Status:** Historical code comparison complete. Confirmed overbroad `state_changed` regression mechanism. **Production Search is not repaired.** No APK was built, signed, installed, accepted or locked. Cobra, native, providers, data, recovery, and accepted releases remain untouched.

## Verified signed inputs

| Signed release | Exact evidence | Embedded `assets/addons/script.infinity.commandcenter/infinity_search.py` |
| --- | --- | --- |
| 2103401 | GitHub Actions run `39779917183`; signed APK/components artifact `12428701834`; embedded APK SHA-256 `17041a44f121693ab0852c6a826b7f728a4d834a64225efec363861616b698e6` | 22,333 bytes, SHA-256 `f712063e1a451b4dec2f11bdd7b92d7f83fa4f4f6fe3f4c517b801f6f4ec5003` (also matches separately released matching Command Center) |
| 2103453 | GitHub Actions run `41783963413`; original-key combined APK artifact `13301200085`; embedded APK SHA-256 `08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8` | 27,038 bytes, SHA-256 `cbbf36ee20974ada8be7a8630e0f0b621b0fb646004842508901b727ddad47b5` |

Both source files were extracted **directly from their archived signed APK payloads**, rather than inferred from a mutable source branch.

## Code comparison

**2103401:** `route()` validates the enabled provider and source pins, preserves its original query encoding, and returns an authenticated route (lines ~163–182). `search_all()` uses a 300-second cache bound to profile, route, and source pins (lines ~205–258). After the native call it keeps the original status and answer. **No** `_query_signature`, `_query_file_stamp`, `_provider_result`, or `state_changed` outcome appears in this signed source.

**2103453:** `_query_file_stamp()` (lines ~235–246) uses device/inode/size/mtime/ctime, treating a byte-identical rewrite with new metadata as a change. `_query_signature()` (lines ~249–274) binds route/profile/provider and dependency source to their settings.xml file stamps, Continue Playing metadata, Command Center identity and seven global widget/revision properties. `_provider_result()` (lines ~277–298) calculates this fingerprint before and after the native call; **any** mismatch returns `state_changed` and discards both answer and native status (line ~293), even on an otherwise successful provider response or a timeout. `_publish_result()` (lines ~327–335) produces the Infinity-owned message **“State changed; search again”**.

This conclusively demonstrates a **source-level change in the validation design** between the two signed versions. The unrelated-revision / metadata-stamp rejection is a real code-level defect. It does **not** determine which state component changed in the user's actual installed session, nor precisely which intermediate release introduced the new guard. The 2103401 provider inventory predates the later The Crew and WatchNixtoons2 TV adapters: it is not a direct head-to-head test for those integrations.

## Eight additional focused checks — offline, exact-source

Executed Python AST-extracted functions from the **unmodified signed 2103453 module**, with synthetic settings/filesystem, cached queries, UI properties and native responses. No real provider, network, Kodi, Android, user file or installed source was used.

All **8/8** passed:
1. Signed 2103401 has verified source-route logic but lacks the broad signature and `state_changed`.
2. Embedded signed 2103453 module SHA-256 matches expected bytes.
3. Stable result and second cache hit require only one native RPC.
4. An otherwise successful result is rejected after byte-identical settings file rewrite changing only its timestamp.
5. An unrelated widget revision rejects a successful result.
6. An actual source manifest change is still rejected as `unavailable`.
7. An unrelated Continue Watching revision masks an original native `timeout` as `state_changed`.
8. Without a revision change, native `timeout` remains visible.

These **pass because defect-reproduction assertions succeeded**. They are not repair acceptance. Earlier branch evidence retains **15** shipped-state and **7** provider-side-effect diagnostic cases. Separately, the read-only state probe passed 10 host safety checks but has **not** run on the Fold.

## Scope of provider attribution

- **WatchNixtoons2 0.14.24 reviewed reference:** `actionSearchMenu` writes `searchHistory` each nonempty query; request helper writes `requestTimes`; Kodi saves settings.xml. Current whole-file stamp checks can invalidate a completed result because of that normal bookkeeping. The installed phone's current version was **not** collected.
- **The Crew 3.2.2 / dependency 3.2.26 reviewed reference:** `TVShows.search_term` stores search history in SQLite, which the signature does not cover. Conditional settings repair / integration-status changes **can** alter settings, including meaningful credentials or account state. This is **not yet attributed** to the user's installed Crew case; globally ignoring settings writes would be unsafe.
- **Otaku:** Zero results are distinct from `state_changed`; do not label an adapter defect solely from an empty response. Successful Umbrella or Seren requests do not eliminate the shared failure path.

## Safe correction gate

1. Obtain one bounded **on-device** failing request for Crew and WatchNixtoons2 and record installed adapter/source identity, original native result before masking, cache/cancel/overlap status, and a privacy-safe changed-component **reason mask**. Do not log queries, media paths, URLs, titles, tokens, settings values or credentials.
2. Apply a separately authorized small correction in the existing **universal Search path**, separating strict cache freshness from acceptance of the **current owned fresh result**. Preserve source/dependency/profile changes, true credential/configuration changes, cancellation and native lease ownership. Do not rewrite provider add-ons, disable normal histories, bypass all settings, invent retries or mask native errors.
3. Run only explicitly scoped Search tests and then exact original-signer install-over preservation checks before user physical Fold acceptance. Cobra, native/shutdown, Preview, and any unrelated functionality remain frozen.

The existing standalone diagnostic sampler is read-only and observes sampled settings/revision changes, **not** original native RPC status or writer ownership. No request-local hook is installed and no authorized live Kodi control channel is available here. **Status remains: investigation complete; production repair pending.**
