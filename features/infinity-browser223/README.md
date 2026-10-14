# Infinity Skin 1.0.5.223 — Add-on Browser / Select ZIP Polish RC1

**TEST CANDIDATE — NOT LOCKED.** This branch is based on the exact user-approved Mocha Rails lock commit `35b210fe191c1fb3361e91b7e405f5532f73236c`.

## Protected input and immutable lineage

- **Exact locked parent skin:** `skin.infinity.diggz-1.0.5.222-Mocha-Rails-RECOVERED-RC2-TEST.zip`
- **Parent SHA-256:** `db494e0b479859190c041494ff68e0c0e38d6b0f482dc65840a0a7fc0227da03`
- Never rebuild from `1.0.5.211`. The accepted `1.0.5.215` corrections, `1.0.5.221` rails and full `1.0.5.222` Mocha visual lock remain in place.
- No changes to APK `2103377`, Rails helper `0.2.5`, user databases or Add-on Manager internals.

## Package verification

- **Candidate full skin ZIP:** `skin.infinity.diggz-1.0.5.223-Addon-Browser-Polish-RC1-TEST.zip`
- **Candidate SHA-256:** `557003afc83a2661fec6ccef921979e264ff28e93595fb633340c618ab69bd56`
- **Reproducible source + tests archive SHA-256:** `04cfe776ded94625c20bd788f05711c2bb4e5c52deec56604d5cad800cb08a0d`
- **30 host tests passing, zero failures.** Kodi live renderer, Fold interactions and exact screenshot fidelity remain unverified.
- 14 source profiles updated in parallel: each `AddonBrowser.xml`, `FileBrowser.xml` and `Includes.xml`; add scoped theme include `Includes_InfinityBrowser223.xml` in each; add nine small graphical assets. `addon.xml` increments version only and updates the description.
- **2,989 original files byte-identical. 43 original files changed, 23 new files, 0 removed.**
- Protected `InfinityRailsOptions.xml`, `DialogContextMenu.xml`, `DialogAddonInfo.xml`, `DialogAddonSettings.xml`, Home, Command Center, and existing files outside owned scope unchanged.

## Owned features

- Add-on Browser category/folder views (Programs, Recently Updated, Repositories, Updates, Dependencies): dark/navy glass row surfaces, subtle cyan stroke/focus, dynamic icon handling, two-line-safe labels, chevron affordances, contextual folder heading, segmented informational footer.
- Native Select ZIP `FileBrowser.xml`: refreshed header, breadcrumb, file/folder row cards, same focus token, polished existing native action sidebar.
- Native Kodi controls and IDs unchanged. `FileBrowser` ids `450/451/61/413/414/415/419/9410` unchanged, including the native file preview visibility gate and click actions. `AddonBrowser` id `50` preserved and no new handler.
- Footer remains **read-only**, as in the approved prior skin. Real installation, repo, update and dependency navigation continues through native Kodi list items. No dummy controls or invented installer logic.
- Reuses original approved theme/palette conditions for Light, Dark and OLED. No new background services or startup polling.

## Testing and rollout

Run source builders from the downloadable source-and-verification archive after extracting the exact locked .222 package, and inspect `HOST-TESTS.txt` and `DIFF-PRESERVATION.json`.

Install test ZIP through Kodi **Install from ZIP** over 1.0.5.222; no helper or APK update required. Test every Add-on Browser category, Select ZIP native actions and safe ZIP preview, back/focus and long-press, all themes and Fold/rotation/window modes. Maintain the exact full .222 ZIP as rollback and do not uninstall or clear user data.

**Do not promote to locked release until the user physically approves it.**
