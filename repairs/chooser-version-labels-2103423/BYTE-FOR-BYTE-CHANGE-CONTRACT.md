# CODEX — SINGLE-CHANGE CHOOSER VERSION LABELS (STRICT PRESERVATION)

**USER AUTHORIZATION AND ABSOLUTE REQUIREMENT:** Add only the approved component update labels to the user's **actual** Choose Your Experience launcher. **Everything else is preserved byte-for-byte wherever technically possible.** This is a narrow chooser presentation/release-metadata change, NOT an Infinity feature update or a Cobra feature update, NOT permission to redesign any UI, and NOT a new playback/shutdown task.

Repository: `mahfouzhassine8-ops/project-infinity`.  
Dedicated work branch: `work/chooser-version-labels-from-2103423-20261027`.  
Exact signed-source starting point: `4e2f6b19e52b9641bf9e48e6bc72137e3cf12c87`.  
Current signed *candidate*: APK 2103423, run `40486072720`, APK SHA256 `4cbbf963be72904de962f434d00ee5f9d5080de6b6b9fd4b3e31ab1d6ac01aff`; original cert SHA256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.  
Infinity original accepted lock: `lock/infinity-2103420-user-approved-baseline-20261026`, commit `883c64a4de6f87077893921454de71bba850235b`.  
**The signed 2103423 candidate has not been marked physically Fold-accepted in the existing release receipt. Do not silently advance the accepted pointer.**

## Exact approved visual change

The user uploaded their **actual** full-resolution portrait chooser screenshot as `20430.jpg` in this chat. It is the authority for visual appearance; it is not a public repository asset and must not be uploaded to public GitHub. Respect the original actual:
- dark starfield/galaxy/central swirl, Earth horizon sunrise and arc;
- live clock/date/weather on top left, HM badge top right;
- centered typographic `CHOOSE YOUR / EXPERIENCE` and `TWO UNIVERSES.`;
- **two tall side-by-side cards**, **gold Infinity on the LEFT**, **cyan Cobra on the RIGHT**;
- original gold infinity mark, original blue cobra emblem, existing card shapes/borders/background, card selection interactions, focus, animations, and two settings gear controls;
- bottom exact original taglines `MORE THAN ENTERTAINMENT` and `A HIGHER EXPERIENCE`.

**Only additions:**
1. Within the existing **Infinity** card, just below its original `INFINITY` title: small readable `Last updated in <N>`.
2. Within the existing **Cobra** card, just below `COBRA`: `Last updated in <N>` in the matching small, subtle style.
3. In quiet footer space near the existing bottom slogans, small centered `App version <N>` without changing slogans' text or layout.

Do NOT convert the two cards into list rows, add chevrons, add a new giant Infinity brand header, change logos/gear positions or functionalities, replace the galaxy artwork, change time/weather, or move the cards.

**Keep all current geometry and positions.** The new noninteractive labels should fit the available free space between title and gear and should not overlap any card content at cover/inner display sizes, landscape, or larger Android font scale. No extra onboarding, dialogs, menu rows, button, settings persistence, background work, or animations. Labels should be accessible as read-only text; card and gear controls remain identical.

## Release-controlled values, not misleading hardcoded numbers

Read from **trusted packaged release metadata**, validated against the actual component owner fingerprints at signing. No network access or time-based guessing. Version lines show the **last signed combined APK in which that specific experience's payload changed**, not the version of the currently installed whole APK and not the date of the current build.

The signed 2103423 history yields these grounded label values:
- Infinity last changed in the combined **2103421** isolation candidate (its owner payload stayed identical in 2103423).
- Cobra changed in signed combined **2103423** for fold reflow.
- Current whole 2103423 APK version is **2103423**.

**Important:** If the chooser update ships in a NEW signed APK, its app versionCode MUST increase (e.g. `2103424`, if that version is actually reserved and authorized). The screen must then display `App version 2103424` (actual signed version), **not** the example 2103423. Infinity still reads `Last updated in 2103421`, and Cobra reads `Last updated in 2103423` if their bytes truly remain unchanged. Never relabel those two as 2103424 solely because the chooser shell changed. Metadata must update correctly for future Infinity-only, Cobra-only, or simultaneous releases. No offline synchronization is needed.

Pin data schema and verified release evidence and require signed metadata equals the actual packaged owner revisions, their first/most-recent update release, and Android manifest version. A failed/missing/mismatched record **fails closed in production packaging**; do not invent defaults or report arbitrary last-updated values.

## BYTE-FOR-BYTE preservation: objective evidence, not marketing

**Protected untouched owner bundles and entire data:**
- Exact **Infinity owner ZIP** bytes and its classes/method fingerprints equal the signed 2103423 composition, currently `sha256:656285de625c859f1d1d3cccc023a20b6dc9d88fff4b5d508d39e000c3b68abc`.
- Exact **Cobra owner ZIP** bytes and its classes/method fingerprints equal signed 2103423 composition, currently `sha256:eb30afa0e1ab9f50da897db27a604cb79a47059ff355c763dc7d7c955ddbcb6b`.
- Exact **MINIMAL_ANDROID_CONTRACT ZIP** bytes unchanged, currently `sha256:6e93a1eb9e47f7fc9bc6f1dbc9208b555e2e62445ca2a3065d4e17a3b473ba33`. Recheck this digest from current `release-authority.json` at build time. The same rule applies to every other non-target owner. Do not change native libraries, Kodi/skin/add-ons, provider assets, images, fonts, audio, profiles, content files, user data, theme or color palettes, preference schemas, or Android process declarations.
- The single launcher, package ID `com.projectinfinity.kodi`, existing launcher behavior/Ask Every Time and settings actions, original signing certificate and install-over data retention must remain.
- Allowed *application logic* deltas are solely exact enumerated **chooser-shell UI display code**, the minimal immutable packaged release metadata/read path, and required app version declaration. No recompiled/refactored unrelated method even in the shell. If existing DEX packaging is rewritten, prove unchanged original classes/methods through pinned canonical DEX member hashes and semantic code-reference hashes, not a false statement that the entire DEX container stays byte-identical.
- Check **every APK ZIP entry** against the signed 2103423 APK before release. Every unrelated uncompressed entry's bytes must match exactly. Allow only exact demonstrated AndroidManifest version metadata, DEX containers housing enumerated changed shell definitions, the small packaged release metadata member (if newly added), and signing artifacts. Do not turn this small allowlist into a generic `assets/**`, `classes*.dex`, or `META-INF/**` exemption from member-level/fingerprint auditing.
- A **new signed APK file** CANNOT have the identical whole-file hash as old 2103423: adding labels and changing `versionCode` necessarily changes classes/manifest and signature envelopes. “Byte-for-byte preserved” here means all other **logical app payloads/owner bundles, unchanged class definitions/methods and user state**, with manifest/signature/dex repacking differences audited separately.
- Compare before/after chooser screenshots and Android view geometries for both Fold displays and all actual chooser display modes. Only the three text labels may differ visually. The existing cards, backgrounds, logos and gears are fixed. If a version line clashes with title/gears at any tested density/font scale, fix only the new text position/size; do not move or resize existing elements.

## Required technical execution

1. Establish the exact current signed APK and owner artifacts from run `40486072720` and authoritative existing `release-authority.json`, not historical preview templates or generated redesigns. Confirm 2103423 SHA, signing identity, owner ZIP hashes and original chooser program.
2. Make the smallest scoped chooser shell presentation patch and read-only packaged release metadata. Preserve source-bound original method fingerprints in other classes. Avoid copy-pasting old all-in-one `InfinityGlassChooser.java.in` code to overwrite the current compiled chooser; work from actual shipped owner DEX.
3. Extend the existing release-authority metadata build/verification so the labels track each owner's **last actual owner update** through signed combined releases. Add a **pre-sign exact preservation diff** and source-bound negative controls (mutate Infinity, Cobra, shared-contract bytes or any non-target ZIP member: must fail; stale label value must fail; fake manifest version must fail). Verify metadata in produced *actual APK*, not only JSON source.
4. Verify no source/content drift in protected locked branch or accepted pointer. Run minimal chooser-focused host/device geometry and APK entry checks only. No unrelated shutdown stress tests or Cobra geometry repairs.
5. Create a new signed integrated APK with the original signer and only if the existing original-key combined release gate passes and 2103423/new sequence is properly authorized. No second app/icon, data wipe or downgrade. Keep 2103423 as a rollback reference and do not call the new candidate user-approved before physical Fold acceptance.
6. Deliver exact signed file link, build run, full SHA256, per-owner SHA, explicit allowlisted changed class/methods/member list, negative-test evidence and the three **actual** displayed version values. A failing or incomplete preservation audit MUST BLOCK SIGNING, NOT BE OVERRIDDEN.

**Failure rule:** If any unrelated source, asset, packaged member, owner digest, method fingerprint or user-data contract changes, do not sign or deliver; report the exact violation. Do not substitute a rough “looks the same” visual mockup as byte-preservation proof.
