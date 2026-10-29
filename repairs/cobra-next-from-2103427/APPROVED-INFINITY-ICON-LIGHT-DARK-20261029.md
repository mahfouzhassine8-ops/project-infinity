# Approved light/dark Infinity launcher-icon treatment — exact visual reference

**User approval:** October 29, 2026. After reviewing the side-by-side dark/light launcher mockup, user confirmed: **“Perfect. I want it to be byte for byte.”**

**Implementation interpretation:** Match the *approved mockup visually as precisely as the Samsung/Android launcher allows*; preserve all unrelated shipping source, binaries, data and behavior **byte-for-byte**. The mockup is illustrative, not a source asset whose pixels can be used directly as an Android adaptive icon. Do not represent a new light asset as byte-identical to an asset that must necessarily differ.

**Repository:** `mahfouzhassine8-ops/project-infinity`
**Existing Cobra corrective branch:** `work/cobra-only-from-2103427-20261028`
**Still locked and approved combined baseline:** `lock/infinity-cobra-2103427-user-approved-20261028`, source `782242090483982c39a78f9c4da932a4751bdafc`.
**Current separately reported QA:** Cobra candidate 2103429 has an outstanding user-confirmed Fullscreen / PiP / More button-action mismatch, documented in `P0-2103429-PLAYER-BUTTON-ACTION-MISMATCH-20261029.md`. This icon work must **not** replace, distract from or falsely close that P0.

## The exact user-approved appearance

**DARK MODE (current icon — preserve):**
- Rounded-square existing dark navy/near-black tile with the current bright cyan/turquoise Infinity loop/emblem as shown in the user's launcher screenshot and the left side of the approved mockup.
- Preserve the logo silhouette, strokes, ornament, inner padding, placement, border/radius and colors. Do **not** recolor or redesign the approved dark variant.

**LIGHT MODE (approved mockup):**
- The SAME Infinity emblem/silhouette, size, stroke proportions, symmetry, ornament, center placement and spacing.
- Clean **white rounded-square icon background**.
- **Black/dark Infinity emblem** for clear contrast, precisely as approved on the right side of the mockup. This is NOT a cyan emblem on white, a generic Infinity symbol, a redesigned emblem, or a blank white square.
- Follow the launcher mask/adaptive icon rules so the app icon remains sharp and recognizable at all supported Samsung launcher sizes, without cropping or distortion.

**Theme behavior:**
- Intended: when Android/One UI is in DARK mode, show the unchanged original dark Infinity icon; when in LIGHT mode, show the approved white-background/black-emblem variant.
- Apply to the **Infinity combined app's visible launcher icon**, including launcher/app drawer, Samsung Finder/suggested-app icon presentation, and supported system surfaces, to the extent the OS/launcher permits. Do not alter a separately installed CobraTV app's icon.
- Inspect Android 17 / One UI themed/adaptive icon behavior. The launcher may cache icons or control monochrome rendering: test an actual system-mode switch and refresh/launcher re-entry before claiming automatic parity. Do NOT claim all system surfaces change if platform restrictions prevent it.
- Do not use high-risk dynamic component toggling that can duplicate icons, break app shortcuts, reset icon permissions, change launcher identity, or disrupt a running experience. If exact auto-switching is impossible through supported, safe platform resources, disclose the precise limitation rather than introducing an unsafe workaround.

## Absolute byte-preservation / narrowly authorized exception

This is **one deliberately narrow user-authorized shell/branding exception** alongside the separately approved Choose Your Experience “Version” wording request. It is **not** permission to edit Infinity 2103427 features or Cobra playback, Pro Sports, Multi-View, Search, tracked/saved data, PiP, shutdown, etc.

- Start from the actual signed current asset(s) and Android adaptive/themed icon declarations; inventory all applicable launcher icon densities and monochrome assets. No guessing resource identifiers or installing an unrelated icon pack.
- Only necessary icon artwork resources, their safe theme-selection resource plumbing and approved release metadata may change. Avoid touching the launcher Activity behavior, package identity, app label, certificate or anything unrelated.
- All Infinity executable code, original dark icon source, existing Cobra functionality, shared native libraries, protected persistence/shutdown, chooser visual design and user data remain exactly preserved. Android resource or manifest changes beyond the specific whitelist require separate owner-gate review and permission.
- Record source/asset hashes, exact changed paths, before/after Android appearance and source/owner preservation checks. Respect the original combined owner/anti-rollback and signed artifact gate; do not weaken those tests to ship an icon.
- Do not modify the locked 2103427 ref or installed 2103429 candidate. Integrate only into a subsequent authorized original-key combined candidate, ideally with the confirmed Cobra button-action correction. One next consolidated install-over APK, not repeated icon-only diagnostic APKs.

## Acceptance

1. Dark-mode current Infinity icon is visually **identical** to today's approved version.
2. Light-mode Infinity icon is the approved white rounded square + black original Infinity emblem, visually matching the side-by-side mockup.
3. Light/dark switching works wherever supported without duplicate icons, broken shortcuts or user-data changes; document OS-managed exceptions accurately.
4. No change to any other app icon (including CobraTV), Cobra playback/Pro, Infinity features, chooser appearance, original signing identity, protected lifecycle or frozen lock.
5. Fullscreen/PiP/More button P0 remains separately required and must be verified independently.

**Status at specification commit:** Approved visual requirement recorded. Implementation and physical Fold validation are NOT claimed by this document.
