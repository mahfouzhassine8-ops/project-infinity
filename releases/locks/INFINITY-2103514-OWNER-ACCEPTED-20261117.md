# 🔒 INFINITY / COBRA — OWNER-ACCEPTED LOCKED BASELINE 2103514

**Owner decision:** 2026-11-17 (America/Detroit)  
**Status:** OWNER ACCEPTED — CURRENT STARTING/PRESERVATION BASELINE  
**Exact versionCode:** `2103514`  
**Package:** `com.projectinfinity.kodi`  
**Owner's confirmation:** “At last baby at fucken last it works” followed by “Lock it and preserve 514. This is our new base.”

## Exact signed artifact: the baseline to preserve

- **Filename:** `Infinity-2103514-Combined-Original-Signer.apk`
- **APK SHA-256:** `4bfe67cf9d3edefdc1d3e04accc826089b314e043a8dd98dba206cd1924a1d8c`
- **Release:** https://github.com/mahfouzhassine8-ops/project-infinity/releases/tag/infinity-2103514-fast-qa
- **Direct APK:** https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103514-fast-qa/Infinity-2103514-Combined-Original-Signer.apk
- **Immutable release/source tag ref:** `refs/tags/infinity-2103514-fast-qa` → source/authority commit `a70aaaec062eac447556d22325affef9d8d496ec` at the time of this lock
- **Original signing certificate SHA-256:** `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`; reported v1/v2/v3 verification PASS
- **Verification bundle:** https://github.com/mahfouzhassine8-ops/project-infinity/releases/download/infinity-2103514-fast-qa/INFINITY-2103514-QA-VERIFICATION.zip
- **ARM64 / selected Android media workflow:** https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44230184774 — PASS
- **Original signing workflow:** https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44234028066 — PASS
- **Original-signed forward-recovery workflow:** https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44234725861 — PASS
- **Install-over verification:** https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44235339813 — PASS
- **Publication verification:** https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/44236030698 — PASS
- **Preservation receipt:** four changed APK payload members relative to prior signed 2103512; 7,773 unchanged. Kodi engine, Cobra, shutdown code, and unrelated payload remain preserved.

## Owner acceptance boundaries

The owner personally reported that casting **works** in the physical Fold/receiver test immediately before instructing this new baseline lock. This is **positive owner acceptance of the current Cast implementation as working**, not an inference from CI or the Cast SDK's PLAYING status.

The owner did **not** separately specify in the acceptance message which of Onn 4K / Nest Hub / Nest Hub Max passed, or expressly verify every pause, seek, Return-to-Phone, shutdown/relaunch, and long-run thermal scenario. Preserve the result without inventing additional PASS claims. The owner's baseline decision is effective despite this reporting boundary.

The entire **exact signed 2103514 combined APK** is the protected starting snapshot for all future authorized corrections, not just an isolated Cast subcomponent. Previous protected baseline artifacts and records remain as historical recovery points; none should overwrite the active 2103514 base.

## Mandatory successor rules — preservation-first

1. **Start from exact signed 2103514** and the source/authority evidence above. No substitute or silent rollback to 2103512, 2103510, 2103508, 2103506, 2103504, 2103486 or an older unrelated source branch. Source-only branches are not substitutes for the signed owner-accepted APK.
2. **Freeze the known-working Cast end-to-end behavior.** Do not rework the receiver policy, authenticated relay, HEVC/H.264 conversion path, AAC timing, MKV source planning, fragment buffering, initialization, seeking, cancellation, or handoff unless the owner specifically authorizes a narrowly evidenced change.
3. **Freeze all unrelated Infinity and Cobra functionality**: Kodi engine, Cobra 2103445 features, Search and providers, Watchlist/tracking, Continue Playing, menus, settings, UI, Video Lock, shutdown safety, networking, user data and schemas. A future correction does not implicitly authorize any of these.
4. Do not uninstall, factory reset, clear app data/cache wholesale, migrate or rewrite user stores, rotate the original signing identity, or produce an APK that cannot install over the existing package.
5. Require owner-selected scope; compare every source/APK payload change to **signed 2103514's exact bytes**; run focused verification only for the approved scope; verify the same permanent signing identity, package/UID install-over continuity, and a valid **forward recovery restoring 2103514 functionality** when creating a successor.
6. A CI-green build, higher versionCode, release publication, or experimental QA does **not** replace 2103514 as active owner-approved baseline. Only a later explicit owner acceptance/promotion can supersede this record.
7. Preserve the exact signed release asset, its checksum and its source reference. Do not delete, overwrite, retag, or force-move this lock/release history. This lock is an archive/acceptance record, **not a new APK build** or authorization to change application code.
8. Keep untested scenarios truthfully labelled unverified; do not turn positive Cast owner acceptance into a claim that unrelated app defects (including deferred Continue Playing) are fixed.
9. Do not repeat owner testing of unchanged accepted behavior merely to justify an administrative lock.

## Forward-recovery clarification

Existing `Infinity-2103515-Combined-Original-Signer.apk` (SHA-256 `c54175ca62b160649f21c50b6787e621ee784bec7dd47021aa2178e5ac5515e0`) is an **older QA recovery** that restores **2103512**, **not** the newly accepted 2103514. Do **not** treat 2103515 as the correct recovery target for future 2103514-based changes. Generate a new, original-signed *forward* recovery preserving 2103514 only when a specific successor is authorized.

## Administrative scope / limitations

This lock branch begins from the exact GitHub tag's source/authority commit `a70aaaec062eac447556d22325affef9d8d496ec` and changes **only this owner-acceptance text record**. It does not modify any signed binary, production source, installed app, user profile, release tag, package registry, certificate or workflow. It does not itself enable GitHub branch-protection or immutable-release enforcement.

The legacy `repairs/dual-experience-isolation-2103420/accepted-combined-release.json` ledger remains a historical bootstrap acceptance registry for 2103420 and must not be carelessly overwritten with a hand-written 2103514 payload map. Any formal signing-ledger reconciliation needs exact 2103514 APK member/class fingerprints, validated owner schema, and explicit source/authority lineage. **This owner decision and signed-APK lock are definitive even while that separate legacy registry is unreconciled.**
