# CODEX INVESTIGATION: Old vs new Continue Playing movie action-menu fallback

**Project:** `mahfouzhassine8-ops/project-infinity`  
**Owner-approved protected release:** Infinity **2103514**, source/release commit `a70aaaec062eac447556d22325affef9d8d496ec`.  
**Preservation record:** `lock/infinity-2103514-user-approved-baseline-20261117`.  
**Status:** Diagnosis requested. **Not** an approved fix, APK build, or baseline change.  
**Scope:** Universal Continue Playing movie action chooser/fail-safe, old saved records vs newly watched records. Do not change unrelated functionality.

## 1. Exactly how the owner discovered the working behavior — central evidence

On **Thursday, November 19, 2026, around 3:10–3:12 AM Detroit local time**, the owner tested two real movie entries in Infinity's **Continue Playing** on the **same Samsung Galaxy Fold 8 Ultra and the same currently installed 2103514 APK**, only minutes apart. The screenshots were provided in the ChatGPT conversation; no image URLs are represented here.

**Case A: newly watched movie, current record — working menu path**

- The owner had recently watched a movie and selected its Continue Playing entry.
- Infinity displayed the first-party menu headed exactly **`Choose Action`**.
- The menu was populated with **8 entries**:
  1. IMDb Trailers — `plugin.video.imdb.trailers`
  2. Umbrella — `plugin.video.umbrella`
  3. POV — `plugin.video.pov`
  4. Seren — `plugin.video.seren`
  5. THE CREW — `plugin.video.thecrew`
  6. TMDb Movies — `plugin.video.tmdbmovies`
  7. Red Light — `plugin.video.redlight`
  8. WatchNixtoons2 — `plugin.video.watchnixtoons2`
- The screenshot shows correct population and visible rendering of that full action list. It does **not** prove all eight can play that title, nor does it prove the resume position was honored.
- The owner commented: **“I want to say its working.”**

**Case B: movie watched previously / older persisted playback record — bad fallback**

- Approximately two minutes later, the owner selected a movie already present from an earlier playback period.
- Infinity displayed exactly **`Saved destination unavailable — open with`**.
- The *entire* displayed list contained only **`Seren`**.
- This is the failure: despite the same installation being able to enumerate eight actions for Case A, an older entry is stuck in a one-provider recovery path.

**Owner's explanation, verbatim:** “Its weird though why does one movie that i watched newly work but the old movie that I had previously during the time watched it still have this. I feel like regardless it sh9uld give me thie menu when it worked.”

**Follow-up requirement approved by the owner:** The fail-safe should function the same way across new and legacy entries. A stale or unavailable remembered destination must never cause an unexplained Seren-only fallback when the normal action chooser has eligible choices.

The high-value insight is the **same-build A/B comparison**. It indicates the provider inventory/menu can render on this APK, while saved-history route selection is record-dependent. **This is a hypothesis, not a proven root cause.** Do not blame a provider, Trakt, or the Infinity skin without tracing actual paths.

## 2. Expected behavior / acceptance contract

1. When a Continue Playing movie requires provider/action selection, old and newly watched entries receive the **same verified full chooser** with all *currently eligible* actions. Do not hard-code Umbrella, POV, Seren, or any provider; retain first-party inventory rules.
2. A **verified working** saved resume route may keep its existing successful direct-resume behavior, as already supported. When it cannot be used, invoke the shared chooser rather than an isolated single-provider fallback.
3. The chooser must not imply that every provider can play the title; each provider retains its own supported interface and compatible action checks.
4. Successful provider selection resumes the **correct movie** and preserves **valid recorded resume position** where the selected provider/player supports it; no invented stream, title-only ID, mismatched movie ID, or guessed episode route.
5. Merely opening/canceling a chooser must **not** change progress, watched state, stored keys, source-memory preference, Watchlist, or Trakt. No clearing, resetting, or forced migration of legacy records.
6. Existing working routes, repeated selection/back actions, and newly watched entries must not regress.

## 3. Codex investigation plan — evidence first

1. Determine **exact source files and versions actually packaged into the signed 2103514 APK**. An old reference tree may not match the installed artifact. Do not start by changing the source on the protected branch.
2. Locate all code that renders or dispatches the exact strings **`Choose Action`**, **`Saved destination unavailable — open with`**, and fallback labels such as **`Seren`**; identify their caller stacks from Continue Playing card selection.
3. Follow both pathways to shared provider discovery, user source memory/preferences, saved destination/route validation, and provider eligibility. Explain *why* one menu includes eight while the other gets one.
4. Compare **synthetic** newly saved and legacy records: `source`, `stable_source`, remembered `destination`, stored provider preference, failures, record `key`, typed media ID, title-only legacy ID, resume revision, progress, and status. Locate precisely the first diverging conditional. Preserve strict identity verification.
5. Distinguish intentional security refusal of an unverified source from **chooser discovery**. Rejecting an unsafe old replay URL should not automatically hide safe alternate provider actions.
6. Verify whether a provider inventory filter, stale cached snapshot, missing old media identity, a stale last-provider preference, or special legacy logic causes this. **Do not claim any of these is the cause without evidence.**
7. Add isolated host fixtures for (a) new entry, (b) old entry with missing saved route, (c) old entry with stale/disabled source, (d) valid saved route, (e) incompatible or ID-mismatched route, (f) no eligible providers, (g) no persistence writes from opening/canceling chooser.
8. Provide a report with **actual file paths and line references**, exact root cause, minimum proposed correction, preservation proof, and tests. **Diagnosis/recommendation only in this pass**; do not build, sign, release, or promote an APK without separate owner approval.

## 4. Earlier repo material useful for orientation (NOT proof of 514 packaged code)

- `repairs/infinity-movies-continue-cast-2103486-20261112/baseline/script.infinity.commandcenter/resume_hub.py` — stored records, legacy identity, progress keys, replay route handling.
- `repairs/infinity-movies-continue-cast-2103486-20261112/baseline/script.infinity.commandcenter/saved_playback.py` — selected-row provenance, destination launch, validation of actual playback.
- `repairs/infinity-movies-continue-cast-2103486-20261112/baseline/script.infinity.commandcenter/provider_inventory.py` — versioned read-only provider capability inventory and `eligible(...)` operation.
- `repairs/infinity-movies-continue-cast-2103486-20261112/test_movie_routes.py` — existing regression scenarios for **older saved movie without `stable_source`**, previously failed preference, native route proof, no writes during rendering.

Find exact 514 packaged counterparts or integration manifest before acting; those archived paths are **leads**, not proof of the running code.

## 5. Nonnegotiable preservation and deliverable

**Preserve locked Infinity 2103514 in full**, especially its user-verified **working Cast** (finally accepted), existing skin, Cobra, native engine, providers, network paths, Trakt, Search, Watchlist, and playback tracking. No broad refactor, no reset or upgrade/downgrade, no rewriting provider add-ons, no silent history migration.

**Deliverable for this pass:** A root-cause investigation with evidence and a narrowly scoped proposal; not a patched APK. The owner wants to avoid a sequence of unverified builds and repeated testing. Target a single meaningful acceptance test after a safe proposal is approved.

This is a diagnostic handoff document on a **separate investigation branch**, not an authorization to alter the protected release.
