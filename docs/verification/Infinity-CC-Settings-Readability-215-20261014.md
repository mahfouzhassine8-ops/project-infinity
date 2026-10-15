# Infinity Command Center Motion / Settings readability — 215 RC1

## User device report

The user confirmed **skin 1.0.5.214 fixes all video add-on tile launches** on the Galaxy Fold, but **MOTION / SETTINGS** inside Infinity Command Center opens `Addon.OpenSettings(script.infinity.commandcenter)` with **blank setting descriptions, an unlabeled category, and truncated Cancel/Defaults buttons**. The screenshot `18652.jpg` shows toggle switches and values `Full`, `Immersive`, `Manual retry from Command Palette` without the field names.

## Verified technical cause — not a core Python regression

The original, hash-pinned Command Center **0.3.5.20** file `resources/settings.xml` is SHA-256 `cf548b5529960c0765d94f74d5d4ecf7247dbfcc6af7a94669e3f93f45e243da`. It has **14 setting labels and a category label written as bare English strings**, e.g. `label="Motion Mode"`, rather than numeric add-on-local string IDs. Kodi's `<settings version="1">` schema expects numeric IDs resolved through `resources/language/resource.language.en_gb/strings.po`, so those labels resolve blank while controls remain functional. See Kodi's official Add-on settings conversion and Language support guides:
- https://kodi.wiki/view/Add-on_settings_conversion
- https://kodi.wiki/view/Language_support

The green 1.0.5.214 skin's default `unified/DialogAddonSettings.xml` also sizes the category button at **24%** and three bottom buttons at **30% each** in an auto-sized `grouplist`. Android portrait rendered tiny category text space and shortened **Cancel / Defaults**. Those dimensions are a separate skin issue.

## Preservation and one-shot strategy

**NEVER** bump `script.infinity.commandcenter` version, touch its `addon.xml`, `default.py`, `service.py`, `checkpoint_runtime.py`, `resume_hub.py`, plugins, or **ANY executable source**. The locked APK **2103377 RC5** cryptographically pins Command Center's source files as save owner; repackaging them under a new version would invalidate the **17 required shutdown receipts**.

A **manual, one-shot** Kodi Program add-on `script.infinity.ccsettingsfix-0.1.0-ONE-SHOT-TEST.zip` contains NO service extension and makes no changes merely by being installed. When explicitly run:

1. Locates the actual installed Command Center via `xbmcaddon.Addon("script.infinity.commandcenter").getAddonInfo("path")`, not an invented path.
2. Requires the **exact original 0.3.5.20 settings.xml SHA-256** before permitting changes. Refuses unknown versions, existing translations or conflicting backups.
3. Asks confirmation. Saves an exact binary backup to `special://profile/addon_data/script.infinity.ccsettingsfix/CommandCenter-original-settings.xml`.
4. Changes **only** the human-facing `label` attributes (14 settings, 1 category and 2 group titles) in Command Center's `resources/settings.xml`. Adds `resources/language/resource.language.en_gb/strings.po` containing matching `#32000`–`#32016` English captions.
5. Verifies the XML tree's setting IDs, defaults, control types, level, options, enable conditions and order remain identical, and atomically writes both resource files. The user then performs **Normal Close** and reopens Infinity to reload Kodi's add-on settings localization.
6. When run again after application, the helper offers **rollback** to the exact original settings XML and removes only the unchanged hotfix translation file. Refuses to overwrite unrelated updates.
7. No background worker is installed. No viewing data, Resume Hub data, local databases, IPTV providers, Trakt, APK, native code or approved shutdown behavior changes.

**One-shot helper SHA-256:** `29aea76ff81a7ffa2e9339a42747d9809d46d109d16c65c5190fb5757c9adbf5`
**18 local source/mock-Kodi tests passed**, zero failures.

## Skin 1.0.5.215 RC1

**Parent:** exact user-tested **1.0.5.214** ZIP, SHA-256 `3b1d5b2bb2edf8ca79ed285804e6ef71de03dfa7bfaa3853a926334c6b8b45e1`.

**Candidate:** `skin.infinity.diggz-1.0.5.215-CommandCenter-Settings-Readability-RC1-TEST.zip`
**SHA-256:** `486aa86c8f8dcda31d80c6d058f4b96154dcb2b3f1a18cfa464c65e280ec7e70`
**Size:** 59,125,043 bytes.

Changes **only 15 of 2,978 entries**: 14 copies of `DialogAddonSettings.xml` plus skin `addon.xml` version from **1.0.5.214 → 1.0.5.215**. All other 2,963 entries are byte-identical, including **every `Custom_1193_InfinityBrowse.xml`** and **every `Custom_1194_InfinityCommandCenter.xml`**. The fixes:

- Category button width becomes **420 skin units**, not the narrow percent layout.
- On `unified`, three bottom actions **OK**, **Cancel**, **Defaults** use **248 skin units each** instead of nested `30%`, fitting the existing footer without ellipses.
- On all 14 profiles, long setting labels scroll when focused.
- All existing color variables, fonts, widget IDs, actions, textures, navigation, artwork, video sources, motion settings values, settings dialog state and saved data remain unchanged.

All **2,075 skin XML files** parsed; ZIP CRC and per-file readback passed; every changed dialog passed a semantic XML comparison confirming only these fields changed. No changes to Kodi's 2103377 RC5 engine.

## Test procedure — two separate Kodi installable ZIPs

**Both are unapproved test candidates; no lock.**

1. In Infinity **Settings → Add-ons → Install from ZIP**, install **skin 1.0.5.215** over the currently working **1.0.5.214**. Do NOT uninstall skin, delete data, or alter the locked APK.
2. From the same installer, install `script.infinity.ccsettingsfix-0.1.0-ONE-SHOT-TEST.zip`, then navigate to **My add-ons → Program add-ons → Infinity Command Center Labels Repair → Run** and explicitly approve the label-only repair. **Installing this helper alone changes nothing.**
3. Use **Normal Close** and reopen Infinity once (required to reload localization).
4. Open Command Center → **MOTION / SETTINGS**: category and **all fourteen settings labels** should be legible; `Full`, `Immersive`, other values remain associated with correct labels; **OK / Cancel / Defaults** display fully. Test scrolling and a toggle by **canceling rather than saving** initially.
5. Verify **Otaku and other video add-on tiles still launch**, normal Back navigation, Resume Hub, skin light/dark appearance, and Fast/Full-load Close.
6. If source pin check refuses patch, **do not force or lower the guard**. Send the exact error and a diagnostics ZIP. If an installed **system add-on** cannot be edited, report it; do not elevate permissions or overwrite the APK.
7. To roll back label changes, run the helper again; it verifies receipts before restoring. To roll back the skin, install saved **1.0.5.214** (user-tested) or approved locked **1.0.5.211**.

## Source security constraints and versioning

Never distribute a new version of the Command Center add-on as a replacement in this task. The one-shot helper's patched settings XML and `strings.po` are **resource-only**, with same installed 0.3.5.20 version and original executable/source hashes. If it refuses because files are read-only, this candidate remains unverified and the correction must be redesigned safely.

**RC5 locked APK, its signer, 17 save receipts, and skin 1.0.5.211 locked rollback remain protected.**
