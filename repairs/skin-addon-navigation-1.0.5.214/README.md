# Infinity Skin 1.0.5.214 — Normal Browse Window / Add-on Launch RC2

**Authorization:** User resumed the stalled All Add-ons/Otaku/Cumination selection fix. **Skin-only test candidate, not locked.** Parent Android APK **2103377 RC5** remains locked; parent skin **1.0.5.211** remains locked.

## Evidence and root cause

The user's 36-second Fold screen recording `18645.mp4` shows normal touch focus changes in the 35/34-item Video Sources card panel without navigating into the selected add-on. Back exits properly. The rejected **skin 1.0.5.213 RC1** added Kodi's `target="videos"` to dynamic panel content but **did not remove the dialog**; user tested and all add-on launches still failed.

The actual parent `skin.infinity.diggz` 1.0.5.211 is a hash-locked ZIP with **14 layout directories** (including fallback) and **13 custom `Custom_1193_InfinityBrowse.xml`** instances. Every instance uses `<window id="1193" type="dialog">` and an `id="50"` dynamic add-on container. Home sets `Infinity.BrowsePath=addons://sources/video` and calls `ActivateWindow(1193)`.

Kodi 21.2's actual window-manager source rejects activation of new windows while modal dialogs are open; selected plugin video folder items are launched by native `ActivateWindow(videos,plugin://...,return)`. Further, Kodi's `ApplicationSkinHandling.cpp` specifically constructs `CGUIWindow` when the custom skin window has **no `type` attribute**, and a `CGUIDialog` when `type="dialog"`. See [Kodi 21.2 custom window loader](https://sources.debian.org/src/kodi/2%3A21.2%2Bdfsg-4/xbmc/application/ApplicationSkinHandling.cpp) and [official Kodi custom-window guide](https://kodi.wiki/view/HOW-TO:Add_a_new_window_or_dialog_via_skinning).

**Distinct from the failed 213 repair:** The RC2 fix converts Browse to a **normal Kodi window**; this allows selection to replace Browse with the proper plugin video window. Existing on-unload hooks would otherwise clear the current browse path when a child add-on is entered, so the RC2 repair removes only those 3 cleanup hooks. Every Home entry explicitly sets the BrowsePath, Title and Subtitle when opening a new Browse session. The manual Back button changes from dialog-specific `Close` to native normal-window `PreviousMenu` so Back can return through Kodi's history.

## Exactly approved XML changes (13 files)

For **each** `skin.infinity.diggz/{profile}/Custom_1193_InfinityBrowse.xml`:

1. `<window id="1193" type="dialog">` → `<window id="1193">`
2. `<content>$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>` → `<content target="videos">$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>`
3. `<onclick>Close</onclick>` → `<onclick>PreviousMenu</onclick>` on existing Back button `id="10"`
4. Remove **only** `<onunload>ClearProperty(Infinity.BrowsePath,Home)</onunload>`, `...BrowseTitle...` and `...BrowseSubtitle...`, retaining state for plugin return.

The **only other change** is `skin.infinity.diggz/addon.xml` `1.0.5.211 → 1.0.5.214`. Exact home launcher, poster card geometry, touch sizes, focus, styling, theme, motion, provider URLs, Resume Hub and every other add-on remain unchanged. No native APK rebuild and no new script or service. User's disabled legacy `script.infinity.live` remains unchanged; removal is not attempted.

## Exact ZIP identity and validation

| Item | Verified |
| --- | --- |
| Locked parent ZIP SHA256 | `460762f78ad2a1cb2d54639e973d20a5958de0c22575a0d7f228b7f1cdc73815` |
| RC2 ZIP SHA256 | `3b1d5b2bb2edf8ca79ed285804e6ef71de03dfa7bfaa3853a926334c6b8b45e1` |
| Candidate | `skin.infinity.diggz-1.0.5.214-Addon-Window-Navigation-RC2-TEST.zip` |
| Candidate size | **59,124,756 bytes** |
| Tested layouts | **14 total**, 13 custom Browse targets |
| XML parse | **2,075 of 2,075 valid** |
| ZIP CRC / entries | **2,978 of 2,978 valid**, original ordering retained |
| Byte-identical files | **2,964/2,978** |
| Actual changed paths | 13 custom Browse XML files + 1 `addon.xml` |

Independent host regression suite **20/20 green**: source SHA, exact new ZIP hash, all 14 Home windows unchanged, all 13 new Browse window classes, native video target, Back action, preserved Browse properties, no visual/layout/control XML changes beyond whitelist, manifest version, source comparison against rejected 213, all ZipInfo identity, XML parse and CRC.

**Not physical-device verified, not locked.** Host XML tests cannot prove actual Android click events.

## Reproducible build

`python3 repairs/skin-addon-navigation-1.0.5.214/build.py --parent <exact-locked-211.zip> --out skin.infinity.diggz-1.0.5.214-Addon-Window-Navigation-RC2-TEST.zip --receipt RC2-verification.json`

Builder refuses a different parent hash, unexpected window/UI shape, unexpected profiles, unapproved file mutations, a mismatched output hash, or changed other ZIP content.

## Physical acceptance

Keep existing locked APK **2103377 RC5** installed. Install candidate as a skin update via Kodi Settings → Add-ons → Install from zip file (no uninstall/data clearing). In **ALL ADD-ONS**, touch Otaku, POV and Cumination; check they open their add-on pages. Press Back once to return to All Add-ons with the tiles still present and press Back again to return to Home; verify other genres, Movies, Shows, favourites, fold/unfold/rotation and one full-load Normal Close/reopen. If the page still doesn't open, capture a Kodi debug log around selection (search for `Activate of window ... refused because there are active modal dialogs`) and do not promote RC2.

This candidate is separate from the legacy Infinity Live/Command Center visibility audit, which is not authorized to delete underlying first-party components. **Lock/promote only after the user physically tests and explicitly approves.**
