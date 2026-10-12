# Cobra 2103373 — user-approved locked baseline

Lock recorded: 2026-10-12. User instruction: “Lock 73 and that is out new base”.

## Authoritative Cobra base (no APK rebuild performed for this lock)

- Product: Cobra within Infinity Kodi for Android.
- Package: `com.projectinfinity.kodi`.
- APK: `Cobra-2103373-Targeted-Isolation-RC1.apk`.
- Android version code: `2103373`.
- Android version name: `1.0.9-Cobra-Targeted-Isolation-RC1`.
- APK size: `159249207` bytes.
- APK SHA-256: `76d333b0bfaf55d205e2dd25660c29ee15baf79157a2f941594c2db5bffaa388`.
- Signing certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Exact build/source commit: `c632fcf95f7c5bf3c96706e59023866c383323de`.
- Lock reference, pinned to that commit: `locked-cobra-2103373-targeted-isolation-user-approved-20261012`.
- Branch used for approved candidate: `work/cobra-targeted-isolation-2103373`.
- Successful GitHub Actions run: `38232872153`.
- Signed APK artifact: `11739871070` (`Cobra-2103373-Targeted-Isolation-Signed-Test-APK`).
- Verification evidence artifact: `11739930951` (`Cobra-2103373-Targeted-Isolation-Evidence`).

## Verified checks

- The downloaded signed APK ZIP contained a single APK matching the byte count and SHA-256 above.
- All 206 automated unit/integration contracts passed: zero failures, errors or skipped cases (193 existing + 13 targeted).
- Final signing output verified v1/v2/v3 with the matching Project Infinity release certificate.
- Evidence `RETIRED-DASHBOARD-APK.json` reports no surviving forbidden retired Sports dashboard methods/strings in the compiled DEX.
- `DEX-PRESERVATION.json` reports zero unexpected protected-class differences; native/payload preservation evidence exists.
- Existing targeted fixes concern Pro-only Sports menu isolation, retired standalone Sports dashboard removal, score ticker isolation and Sports Multi-View score isolation. This lock does not authorize further feature changes.

## Important acceptance limits

This lock records the user's express approval of 2103373 as the **new Cobra development baseline**. The GitHub evidence itself records `physical_device_verified=false` and `physical_acceptance=false`; do not invent an independent physical verification receipt. The user may have tested on their device before approval, but no new device report is asserted here.

The prior approved Cobra 2103324 remains a historical rollback; 2103372 was the preceding test candidate and is not the new approved baseline. Preserve source/build evidence for all three.

The new baseline supersedes earlier Cobra development parents only. It does **not** automatically change independent Infinity Kodi / skin / command-center lineage.

Next planned work: an **Astra Pro read-only whole-Infinity-system dead-weight/dependency audit**. No deletion, APK rewrite, cleanup or promotion is authorized by this lock. Future Cobra implementation branches must start from the exact locked commit and preserve accepted behavior. The lock reference should remain pinned to that source commit.
