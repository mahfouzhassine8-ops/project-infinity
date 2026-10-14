# Infinity 2103377 RC5 + skin 1.0.5.211 — All Add-ons and legacy Infinity Live
**Read-only audit. No locked APK/skin/add-on files modified.**

## User issues

The **All Add-ons / Video Sources** screen currently shows **35 items** and highlights tiles (including Otaku and Cumination), but taps do not open them. User requests all normal third-party add-ons to be selectable, no internal Infinity entries in this gallery, and asks where the old **Infinity Live** script can be deleted.

## Verified facts

- Exact locked skin: `skin.infinity.diggz-1.0.5.211-Compact-ZIP-Preview-RC1.zip` (2,978 archive entries; used for the user-approved 2103377 RC5 baseline).
- Skin has **14** profile directories, including `fallback`. **13** copies of `Custom_1193_InfinityBrowse.xml`, one per profile except fallback. Every profile also has an `AddonBrowser.xml`. Prior references to "13 profiles" confused bespoke *Infinity Browse* XML count with total skin profile count.
- Those 13 bespoke Browse panels have dynamic list `<content>$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>` with no explicit `target=` window, while other native source widgets include `target="videos"`. **Likely** reason folder navigation/tapping fails across the grid. Actual input dispatch is still **unverified on device**; fix is separate from legacy add-on removal, and must be tested before any skin promotion.
- The prior device-installed add-on inventory `Infinity-Installed-Addon-Code-20261008-071505.zip` includes `addons/script.infinity.live/addon.xml`, version **0.1.13**. It declares BOTH `xbmc.python.script` (library `launch_tv.py`) and `xbmc.python.pluginsource` (library `default.py`, provides `video`). This **explains why it appears as a Video Source**, even though its ID begins with `script.`.
- Exact locked skin **1.0.5.211** `addon.xml` no longer imports `script.infinity.live`; a full inspection of its readable text found exactly one legacy mention in `INFINITY_LIVE_MERGE_1_0_5_108.txt`. This is a historical note, not a runtime invocation.
- Scanning the prior installed-add-on ZIP for `script.infinity.live` outside `addons/script.infinity.live/**` found only an **optional dependency** in the older skin **1.0.5.204** `addon.xml` and a generic Infinity Live UI-reflow comment in Command Center. **No executable cross-add-on call was found** in that snapshot.
- The repository has an older **0.1.0** `addons/script.infinity.live/` implementation; this is distinct from the **0.1.13** installed snapshot. Do not overwrite newer user add-on files with older repository code.
- `script.infinity.commandcenter` is **not obsolete**: its installed manifest declares `xbmc.python.script`, `xbmc.python.pluginsource` (provides video), and a startup `xbmc.service`. It owns core Resume Hub services and Infinity Movies/TV routes. It must remain installed and enabled. Hide its tile only in **user-facing gallery**.
- The currently displayed 35 add-on identities are not all available from the older October 8 inventory. Do not invent an exhaustive count or claim the first-party entries are the only unwanted ones without fresh on-device inventory.

## Practical removal of obsolete standalone Infinity Live (user choice)

On phone: **Settings → Add-ons → My add-ons → Video add-ons** (or **Program add-ons**) → **Infinity Live** → **Information → Uninstall**. This uninstalls **only** `script.infinity.live`; don't manually delete neighboring `script.infinity.commandcenter`, `service.infinity.compat`, or approved Live TV integrations.

Physical Kodi virtual directories:
- Code: `special://home/addons/script.infinity.live/`
- User data: `special://profile/addon_data/script.infinity.live/`

Keep the add-on data backup (M3U/EPG/provider configuration) until the user explicitly agrees to discard it. This audit **does not** delete the add-on or its data, uninstall from the actual device, or alter any installed APK.

## Production packaging recommendation (not implemented)

For a future approved APK or installed-add-on cleanup candidate, remove the old packaged standalone `script.infinity.live` **only after** verifying no native launch, skin shortcut, custom favourite or user-selected Live TV source depends on it. Kodi registration metadata and any first-party gallery visibility should be corrected separately: `script.infinity.commandcenter` must stay registered/usable but should not clutter the All Add-ons presentation. Generic Kodi add-on listings may continue showing registered video add-ons unless the UI layer filters them by exact IDs. Do not filter by name prefix `Infinity` alone, since that may hide unrelated third-party titles.

### Preservation

APK 2103377 RC5 is locked with both fast and full-load shutdown accepted. Skin 1.0.5.211 remains locked. Existing untested skin 1.0.5.213 proposal is separate and must not be promoted as a remedy for this removal request. No native shutdown engine, Resume Hub, Trakt, provider, or skin file was changed by this read-only audit.
