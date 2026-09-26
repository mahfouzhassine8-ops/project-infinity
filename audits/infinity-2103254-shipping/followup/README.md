# Resumed first repair batch — Health 2.5.17 / Accounts 0.5.2

Status: source candidates and offline tests; NOT stable, NOT a new APK, NOT complete shipping acceptance.

## Real AM Lite source findings and corrections

Review input is the author's actual script.module.acctmgr 1.1.6 ZIP, exactly 5,150,123 bytes, Git blob SHA-1 b9de2983bd5785c14c9bdf9aabbe12fe9783cbda and SHA-256 6cee6f35744608e080d66c8ba6af6d5bdb44c5a18dca6f6a3f0467b71958737f. CI fetches and verifies it, never floating silently to different bytes.

The original master refresh value was the literal '1'. The earlier repair corrected that value but missed an access-token-only skip condition: a target with matching access token and stale refresh token could be skipped. The earlier all-target selector also missed Fen Light and included unsupported/inactive targets.

Accounts 0.5.2 repairs nine active XML adapter branch conditions to consider both tokens, uses the real master refresh, stops before propagating incomplete credentials, and selects the exact 18 active AM Lite targets that are installed. Mocked full adapter execution proves the stale-refresh case for Umbrella, POV and The Crew. Database-backed and JSON-provider live refresh are NOT established by those tests.

Source changes use strict full-source signatures for exact upstream, recognized previous Infinity repair, or exact current repair. Unknown source is refused; marker-only/no-op source cannot claim success. Existing transactional backup, failure rollback and explicit user confirmation are retained. The new all-target actions do not force-kill Kodi, disable updates, or reauthorize an already authorized account during resync. They say sync was attempted, not that every server request succeeded. Installation alone neither patches AM Lite nor resets credentials. Trakt authorization and Real-Debrid authorization are separate.

## Health Center 2.5.17

Retains selected-session/native-history separation, bounded native parsing and privacy-minimal summaries from 2.5.16. Adds exact Trakt selection-file handling, failure-over-success precedence for contradictory same-line markers, correct first-event counts, expanded target visibility, SALTS underscore credential names, and database-backed status as unverified rather than falsely missing. Local token agreement is not server verification.

Dependency retrieval now respects destination cancellation, validates bounded archive paths/size/identity/version, verifies before publishing, never overwrites an existing ZIP, and cleans its own incomplete files on caught failure. Network deadline/cancellation and HTTPS-downgrade protections remain. No automatic installation or userdata/reset action is added. A hard process kill during final file copying could still leave an incomplete candidate ZIP; this is not claimed crash-atomic.

## Skin and native limits

Skin 1.0.5.168 changes only addon.xml plus DialogConfirm.xml in six resolution profiles. 1,354 of 1,361 files remain byte-identical, with all control IDs and action/navigation tags preserved. Full rendering/focus testing remains pending. Delivery is a font-free source delta, not an installable full skin.

Native identity stamping is staged only. FD_SET root cause is unresolved, no libkodi rebuild or new APK is made, and Cobra is unchanged. The retained crash is not counted as a new later-session crash and is not declared fixed.

## Reproducibility and current tests

Concatenate payload/part00..03, base64-decode and XZ-decompress to the exact 11-file JSON source map. Compressed source SHA-256: 2c00aeef3586666c1f4f497cff11d9b5feda7a92f4a538721771f430354a861d. run_tests.py verifies the allowlist and source-function provenance, reuses two exact unchanged first-batch modules, and runs 55 retained plus 58 new/current regressions (113 total) using the real upstream source with mocked Kodi/storage/network boundaries. The earlier 60 tests overlap and are not additive. No live provider credentials or device state are used.

Local delivery ZIP identities:
- Health 2.5.17: f659173c224bae64534cd27cd904416d45fdbd7bb5bc9861f2cc98113b647640
- Accounts 0.5.2: 2efbdfd842738b720220009db2e08a9644dd479113480f9987934937c48ab894

These archive hashes identify locally packaged companions; CI tests their hash-guarded source representation, not an installed APK. Device verification, native stress, full playback/provider/navigation coverage, live Trakt and complete HD polish remain acceptance gates.
