# Infinity 2103490 Cast — YouTube APK reference and root-cause handoff

**Purpose:** Deliver findings from user-supplied `YouTube_21.45.82.apks` into the existing **signed-90-derived source-only investigation**. **No release authorization and no production-code change.**

## 1. Verified reference-bundle facts (static inspection, not runtime tests)

The supplied Android split-APK archive contains `base.apk`, `split_config.arm64_v8a.apk`, `split_config.en.apk`, and `split_config.xxhdpi.apk`. The archive SHA-256 is `9f5cef44c9af5c60e35a562bb1b81018782714fe068b920e48ff24435ef9ec15`.

- Package: `com.google.android.youtube`; version `21.45.82`; `targetSdkVersion=37`.
- Declares `android.permission.ACCESS_LOCAL_NETWORK`.
- Cast options provider: `com.google.android.libraries.youtube.mdx.castclient.CastOptionsProvider`.
- YouTube MDX MediaRoute2 provider service: `com.google.android.libraries.youtube.mdx.mediaroute.providerservice.MdxMediaRouteProviderService`.
- DEX contains Cast and DIAL session identifiers and `urn:x-cast:com.google.youtube.mdx`.

**Interpretation:** YouTube has app-specific Cast/MDX/DIAL integration. These observations **do not** establish Infinity's TV failure or justify using the YouTube receiver ID, copying proprietary YouTube code, adding DIAL, or altering receiver selection.

Do **not** upload the actual APK or unreviewed diagnostics into this public repository. If Codex needs to inspect the binary, attach the original APKS directly in its private task environment.

## 2. Existing Infinity source evidence

Existing investigation JSON: `repairs/infinity-cast-root-cause-2103490-20261113/INVESTIGATION.json`, branch `work/infinity-cast-root-cause-from-2103490-20261113`. It records:

1. **Confirmed signed-90 source defect:** a connection deadline may persist into subsequent relay/LOAD phases; a retained reproduction is fixed in the later 92 branch.
2. **Confirmed signed-90 source defect:** Matroska content can be reported as WebM; subsequent 92/96 work handles classification / compatible remuxing.
3. **Confirmed signed-90 source defect:** public `User-Agent`/`Accept` headers may be lost at redirected media origins, yielding HTTP 403; later 94 correction retains public headers with credential isolation.
4. **Separate later-94 cleanup improvement:** resource retirement/cleanup completion; do not confuse a subsequent sender cleanup with the first media-transfer failure.

These are source/test findings **not proof of which issue caused the November 13 receiver return to the home screen**. Infinity already uses Google's `DEFAULT_MEDIA_RECEIVER_APPLICATION_ID` in `InfinityCastOptions.java`, so adding YouTube MDX or DIAL is not justified.

## 3. Remaining essential input

`Infinity-Diagnostics-20261113-134555.zip` (the **existing** November 13 diagnostics) is unavailable to this ChatGPT session or the prior Codex branch. **Reattach that same ZIP privately to Codex.** No new phone capture is requested.

## 4. Codex task / acceptance gates

- Trace the first failure from discovery → session/receiver launch → source/proxy preparation → LOAD → media HTTP GET/HEAD/range → PAUSED/PLAYING confirmation → cleanup. Correlate timestamps, error categories, callback IDs and HTTP outcomes from the existing November 13 ZIP.
- Decide which of the **already verified** narrow corrections (92 phase timer; 92/96 container handling; 94 redirect headers) actually applies. Preserve secure redirect credential boundaries. If there is no attribution, **report blocked**, rather than combine unrelated experiments or sign another speculative build.
- Preserve the complete signed-90 functional baseline and signing identity. No edits to Cobra, search, providers, tracking, networking settings, UI, shutdown, native engine or unrelated Infinity code.
- Produce the smallest casting-only diff and focused regression tests. Build **one signed, in-place installable APK only after** the causal fix is supported and quality gates pass, then provide exact SHA, branch, workflow run, signing-match proof and unchanged-component evidence. Never call a passing host/unit test physical TV acceptance.

## Status

**YouTube reference reviewed; root-cause attribution remains blocked solely on the existing Nov 13 diagnostic evidence. No production changes or APK produced by this handoff.**
