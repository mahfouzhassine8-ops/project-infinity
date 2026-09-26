# Infinity shipping audit RC1 — evidence and first repair batch

## Status: NOT release-approved

User-authorized preservation-first Infinity audit. Native candidate/source: 2103254, exact commit `84f293d753b863a06c9366d9575b459a9e2992d9`. Protected 2103229 rollback and original native branch remain intact. Cobra, providers, player and approved Infinity navigation/layouts are not changed. This branch contains audit sources and tests; it does not install or publish a replacement APK.

## Exact component inputs

| Component | Input | SHA-256 |
|---|---|---|
| Native APK | 2103254 | c526f740f258c48e3a208ccac6659f22995d077ff6a5097fc3d4d6617a51625e |
| Packaged libkodi.so | Rebuilt 2103254 engine | c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d |
| Health Center | 2.5.15 candidate | cb5530efdb872907efcedf41ad78bd9da931e4de02f43aa7d4a513de3f2012e7 |
| Authorization & Accounts | 0.5.0 | 832d8eb729db3d79fac20492a27f9b2ba3c49a0253a5af510ff6fc7e5206f7b7 |
| Infinity skin | Locked 1.0.5.167 | 71df8f682467bfb46b40221664219f75b0a41b4ae82fc8fb93080c7e60ccf008 |

## Implemented source candidates

* Health Center 2.5.16: selected-session/native-history separation, bounded and privacy-minimal tombstone summaries, explicit uncertainty in engine/exit attribution, readable procfs memory/FD counters, honest local-versus-server authorization state, bounded/cancellable repository downloads and pre-request HTTPS downgrade refusal.
* Authorization & Accounts 0.5.1: source-repair transactions with preflight, backup receipts, hash checks, guarded rollback and failure recovery; exact AM Lite 1.1.6 compatibility; executable-source status rather than marker-only success. The repair still needs real provider/AM source and device verification.
* Skin 1.0.5.168: only addon version and six DialogConfirm XML files changed, improving confirmation-body space and the off-canvas fallback. No home, player, widget, menu, provider or Cobra changes. 1,354 of 1,361 skin files are byte-identical; no files removed. Rendering/touch/focus remain device-test pending.
* Identity-only native patch is STAGED, not compiled or packaged: diagnostic Java/C/build-script stamps now distinguish the actual rebuilt engine from the historical parent. It does not change libkodi or fix FD_SET.

## Verified findings / unresolved blockers

The FD_SET abort retained in the 06:42Z diagnostic is the same event already present in the 05:35Z export. Its Android timestamp is 2026-09-26T05:28:17.334Z, before the selected later session but after the 2103254 build completed. Historical relative to an export does NOT mean fixed or pre-2103254. The collector's current app version is not an exit-event version.

The tombstone reports FD 1335 against a 1024 FD_SET limit, 1,340 open FDs, including 1,073 ZipArchive-owned FDs. Android resource retention is a lead, not a proven responsible component or leak. The recorder's restore-and-reraise frame obscures the original failing caller. FD_SET root cause/fix and attribution remain native release blockers.

Local Trakt refresh mismatches decreased from five to three across supplied exports. Umbrella, POV and The Crew still report refresh-token mismatch. TMDb Helper and the Trakt add-on show local alignment, NOT proof of successful server refresh/history sync. The popup proves source execution only; Real-Debrid authentication is separate from Trakt. No credentials are reset or copied by this audit.

## Tests and scope

82 local regression checks passed, including source/preservation/skin checks. CI independently runs the 60-test pure core subset, verifies the exact APK/engine and stages the identity-only source patch. Do not report these as 142 independent tests or as physical-device acceptance. A green workflow is a SOURCE-AUDIT pass, not a new native build, APK release or complete shipping audit.

The full app startup/shutdown, Android lifecycle, native resource stress, actual provider requests, playback/resume/subtitles/audio, live widgets/weather performance, complete remote/touch/focus traversal, export/install/rollback on the phone and every visible control still require device/integration acceptance. No rendering or provider call was fabricated.

## Reviewable source payload

Concatenate payload/part00 through part02, base64-decode and XZ-decompress to a UTF-8 JSON map of seven source files. Compressed payload SHA-256: `fedca0939214d589f7d316afa82da1de5bfd0b75184b8bf94398dcdbe0b917ef`. run_tests.py verifies and extracts this allowlisted map into audit-output/review-source before execution. The payload includes complete new modules, tests, an identity staging tool and hash-guarded deltas for 18 changed component files. Compression transports source; it is not an opaque executable.

For the complete component source, run apply_deltas.py against the exact owned baseline ZIP and decoded component-deltas.json. Output must be a new directory; no baseline or installed file is changed. Compiled Python caches are excluded. Skin fonts/media remain in the user's existing owned baseline; no font files or raw device diagnostics are published here. A partial skin delta is NOT a Kodi-installable skin ZIP.

## Acceptance gate

Do not lock or promote 2103254 or these candidates from these tests alone. A future integrated candidate needs resolved native blockers, actual Android compilation/package/signature/preservation checks as applicable, verified installed versions, repeated launch/open-select-back/exit and foreground/background cycles, normal playback and provider/Trakt tests, six-profile UI verification and a fresh Health Center export with correct session/build attribution. Preserve retained history; do not press Start Fresh again after a crash or reset user data just to make the report look clean.
