# Infinity Command Center 0.3.5.20 — Actual Settings Resource Update v2 (TEST)

## Why the prior UI still had blank labels

User's Fold screenshot after skin 1.0.5.215 showed the bottom buttons clearly labeled but the category and every setting name blank. **That proves only the skin's dialog geometry was updated, not that Kodi loaded Command Center's localized labels.** Installing the prior one-shot `script.infinity.ccsettingsfix` ZIP did not itself modify Command Center; it needed an explicit Run. Its generated English PO additionally left all translated `msgstr` entries blank; v2 writes explicit English `msgstr` values.

Kodi schema 1's Command Center 0.3.5.20 `resources/settings.xml` originally has English strings in `label` attributes, whereas settings labels are supposed to use add-on-local numeric string IDs. Kodi renders its values and toggles, but no descriptions.

## New verified updater

**Installable ZIP**: `script.infinity.ccsettingsfix-0.2.0-VERIFIED-UPDATE-TEST.zip`

- **ZIP SHA-256:** `9464b33cd4b5971ed34e3c62b3fc93c387c524dd8afb6c9e08c5c2d6d043dbc8`; **8,081 bytes**.
- Actual program add-on ID: `script.infinity.ccsettingsfix`; helper version **0.2.0**. Upgrades the previous helper **0.1.0**, if present.
- Actual protected Command Center add-on ID: `script.infinity.commandcenter`; **preserves version 0.3.5.20**.
- Enforces exact **installed CC 0.3.5.20 addon.xml SHA-256** `5711db9be562db665e1db70aa8798c7d254843196cc6beb7520055918758628f` — the observed native RC5 pin.
- Enforces exact original **Command Center resources/settings.xml SHA-256** `cf548b5529960c0765d94f74d5d4ecf7247dbfcc6af7a94669e3f93f45e243da`; patched settings SHA-256 `ab9f95d5936fc2fe17acf88a8542e0469eaf09981bfe70902faaa32927667fcb`.
- Rewrites only the **14 existing setting label attributes**, category label, two group titles to numeric localization IDs `32000..32016` while leaving all setting IDs, order, type, default, constraints, enabling conditions, controls and stored values unchanged. Writes explicit `msgid` **and nonblank `msgstr`** for every English caption to `resources/language/resource.language.en_gb/strings.po`.
- Saves original XML to `special://profile/addon_data/script.infinity.ccsettingsfix/CommandCenter-original-settings.xml`, writes a hash-pinned repair manifest, makes atomic file changes, reads back both installed files, and saves `last-verification.json`. A failure or version mismatch shows **NOT UPDATED** and does not call it a success.
- If the old helper's settings.xml was already patched and old English PO hash `ec6c637eba64f8392ec1d1a69511711679244fe6b165bc94f0b746f45e4a408b` is present, it checks the original backup then safely upgrades **only** the PO. Unknown translations or partial changes refuse modification.
- After a Normal Close and reopen, running the helper again checks `xbmcaddon.Addon("script.infinity.commandcenter").getLocalizedString(id)` against all **17 exact expected captions**. Only **17/17** reports **COMMAND CENTER VERIFIED UPDATED**. Installed-resource SHA success does **not** falsely claim Kodi reloaded its labels.
- The helper is a **Program add-on**, not a startup service. Installing the ZIP by itself does not patch Command Center. Running is mandatory.

## Protected locked APK/skin contracts

User-accepted locked **APK 2103377 RC5** and the 17/17 full-load save receipts remain untouched. Do not update `script.infinity.commandcenter/addon.xml`, its version or its executable modules `default.py`, `service.py`, `checkpoint_runtime.py`, `resume_hub.py`, `plugin.py`, etc. This is an **actual in-place Command Center resource update**, but deliberately **not an executable version bump**: a version bump would invalidate native RC5 pinning and require a separately verified APK update. Skin **1.0.5.215** already repaired footer geometry and preserved working add-on navigation. No new skin ZIP is needed for this test.

## Exact use sequence on Fold

1. Keep APK **2103377 RC5** and installed skin **1.0.5.215**. No APK or skin reinstall.
2. Kodi **Settings → Add-ons → Install from zip file** → install `script.infinity.ccsettingsfix-0.2.0-VERIFIED-UPDATE-TEST.zip`.
3. Crucially, **run** the helper under **My add-ons → Program add-ons → Infinity Command Center Settings Update & Verify → Run**, then approve the prompt. Wait for **COMMAND CENTER RESOURCES UPDATED & VERIFIED**.
4. Use **Normal Close Infinity**, reopen, and **run the helper a second time**. Only a report of **17/17 labels loaded by Kodi** demonstrates the actual Command Center resources were loaded in the device.
5. Open **Infinity Command Center → MOTION / SETTINGS**; verify actual field descriptions, values and options, as well as OK/Cancel/Defaults. Check existing Otaku/POV navigation, Resume Hub and fast/full-load shutdown before lock.
6. If the helper refuses, says **NOT UPDATED**, or reports fewer than **17/17** after reopening, export diagnostics and do not force-write, uninstall Command Center or clear user data.

## Verification artifacts

**31/31 local tests passed**: 24 exact-source/actual-write/hash-backup/rollback/migration/idempotence/tamper tests, and 7 additional mocked-Kodi dialog tests verifying explicit user consent, truthful update confirmation, **0/17 not-yet-loaded**, 17/17 fully loaded, wrong version, unknown settings and old repair upgrade.

- Installer script SHA256: `1134f798610430df9f89c92508a2bcfd5115a538028895d6f155f76b27f46706`.
- Evidence source/tests bundle SHA256: `887f28ddd5624facf34ac7b3f6b5290352a866815d6f731ad12b45e141ffa16d`.
- The user's **device is not yet verified updated**; ZIP generation and host tests are not device installation proof.
- **Not locked.** Previous approved skin rollback 1.0.5.211 remains available.
