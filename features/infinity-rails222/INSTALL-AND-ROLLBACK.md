# Infinity Rails Hold RC02 + Mocha menu — testing only

**No lock. Physical Fold acceptance required.**

This APK is an isolated Android-native correction for the previously identified Home rail long-press routing defect. It **does not** include or install a skin or helper. Its counterpart test packages must be installed separately and retained for rollback:

- Full skin: `skin.infinity.diggz-1.0.5.222-Mocha-Rails-RC2-TEST.zip` (SHA256 `cfecda1c8f0442f368fea361760b15e7c9d7487e2f362093baedddf0e757fc17`)
- Helper: `script.infinity.rails-0.2.5-Mocha-Rails-RC2-TEST.zip` (SHA256 `5219ca62141c4b570765c405dbac5f5f026da7ccd56c2c9bd3ac96329f31403b`)
- Native APK: `Infinity-2103377-Rails-Hold-Native-RC2-TEST.apk`, signed only after native and Kodi gates, same Android versionCode 2103377.

## Protected ancestors

- Current skin before this change: **1.0.5.221**, installed Rails helper 0.2.4. The protected, user-accepted earlier skin **1.0.5.215** is unchanged. **Never base on 1.0.5.211.**
- Original signed Infinity APK RC5 2103377 unchanged and available separately; this experimental APK is update-over-install and uses the same permanent signing identity.
- No change to rail preference schema, Resume Hub, settings, Command Center label repair, add-on databases, native protected shutdown owners or playback except the touch routing hook.

## Install only after full package success

1. Keep the original approved full APK and skin ZIPs as separate safe backups. Do not clear Kodi/Infinity user data, uninstall the application or force-close during a save.
2. From Infinity, install the **0.2.5 helper** ZIP over the installed helper through normal Install from ZIP.
3. Install the complete **1.0.5.222 skin** ZIP from Kodi Install from ZIP (no manual patch runner); accept the skin reload.
4. Close Infinity normally if possible, then install the signed **Rails Hold RC02 APK** over Infinity. Do not uninstall.
5. Launch Infinity and test a **single hold** on a rail card (including one that wasn't focused), normal tap to open, horizontal swipe, Move/Reorder, Remove custom shortcut only, settings, Cancel/Back, themes/modes, Fold/cover rotation and restart state.
6. If the first hold still launches Super Favourites or opens black panel, capture diagnostics and stop. Don't lock. The ANR regression is an additional release gate, not guaranteed repaired by this patch.

## Action semantics

- One hold on a qualifying visible Home rail card → selected addon name and art in approved pearl/cyan Mocha Rail Options menu, blue highlighted Move/Reorder, red custom-only Remove, Settings when available, Cancel/X.
- Ordinary tap opens the add-on; swipe scrolls; hold outside a qualifying rail follows original Kodi input behavior.
- No provider gets uninstalled or disabled by removal.

## Validation boundaries

The native workflow and gated signer prove compilation, related host tests and APK lineage; the previous real-Kodi smoke tests the helper's stock chooser callback. The new custom `WindowXMLDialog` visual has **not** been accepted on the Fold. This package is an experimental **TEST**, not a production lock.

## Rollback

Do not delete data. Close Infinity normally and reinstall the original same-version-code permanently signed RC5 APK over the test; restore helper 0.2.4 and full skin 1.0.5.221 using ordinary Install from ZIP only if needed. The approved 1.0.5.215 remains a separate protected backup.