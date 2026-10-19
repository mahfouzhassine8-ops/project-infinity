# Group #1 / Task 03 — exact default-Fold horizontal card geometry, source-only

**Date:** 2026-10-19. **Scope:** Continue Watching Movies panel 8830 and TV panel 8831 **only**, in `skin.infinity.diggz/unified/Home.xml`. **Status:** Staged and host-tested; real Fold swipe/tap/offset and vertical Resume/Play chooser still NOT VERIFIED/NOT FIXED. Group #1 still RED. No new APK, skin install, CI build or final lock.

## Signed original evidence and bug mechanism

- Signed provisional 2103390 parent: SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`; 7,430 APK members; skin `skin.infinity.diggz` version `1.0.5.228`.
- The ORIGINAL skin's `addon.xml` chooses **`unified` (1080x2400, 9:20, default=true)**. Original `unified/Home.xml` SHA-256 `61fe23defed0536ce24f7c6d2d9b6beed5c0f3b8d04a33809a929a6b1f2532be`.
- In exactly the two default Continue Watching horizontal panels **8830 and 8831**, original `itemlayout` and `focusedlayout` each have `width="auto" height="97.619048%" aspectratio="0.561219512"`. Native Kodi GUI list-item layout uses numeric `QueryFloatAttribute` for width/height and defaults missing/unparseable width to parent max width; horizontal scroll and tap rectangles depend on that width. Relevant upstream source: https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIListItemLayout.cpp ; https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIBaseContainer.cpp . Kodi's official panel-layout documentation also requires numeric width and height: https://kodi.wiki/view/Container_Item_Layout . This is source-mechanism evidence; shipped physical Fold click accuracy remains untested.
- The other **13 original signed Home.xml variants** already give panels 8830 and 8831 `width="230.1" height="410"`. Reusing those existing card dimensions is additive fidelity, not a new design.

## Surgical correction, exact source SHA

- Source script: `repairs/2103390-bugfixes/group1/continue_horizontal_touch_patch.py`.
- Source commit **`d6ba53d7317e379044a23062434ff128f5b39cf2`**; blob SHA `47c2b02ed6cd96a65453be6270cab01ab5243829` verified against tested local source.
- Replaces the width and height in EXACTLY **4 tag openers**, for `itemlayout` and `focusedlayout` in each existing panel 8830 and 8831, only inside `unified/Home.xml`. All `aspectratio` attributes, card include parameters, artwork, content URLs, visibility, focus navigation, Kodi player and entire remainder of the XML are byte-equivalent. No new buttons, actions or visual redesign.
- Refuses unknown preimage SHA, missing/duplicate panels, extra modifications, reapplication and any overwrite of the original signed input. Changes no native libraries, Cobra, shutdown, providers, third-party files, user data or signed APK.

## Executed host tests

- `group1/test_continue_horizontal_touch_patch.py`, test commit **`bd0ecbf5c608b649e5dcedbd8546174ab1e3f59b`**; exact Git blob `f6849eaeadc12993d3a177d1998933864b0edb26`. **6/6 PASS** on signed original asset. Tests exact default skin, both malformed hitboxes, reference numeric dimensions, exactly four tag changes, fail-closed tamper and safe separate staging.
- `group1/test_group1_scope_apk_15.py`, commit **`a07b7840ed835e98c54e5c389ce347f07dd9d946`**, blob `c580cef26c588bef39f95fd003162b24865501cb`. **1/1 PASS** against all **7,430 real signed members**, simulating the combined previously staged #01 TV resolver, #02 movie identity, #04 orb, two first-party dependency contract pins, and new #03 default Fold layouts. **Exactly 15 possible changed original APK members; 7,415 unchanged.** No Cobra/native/shutdown/watched service logic/deleted files in the 15-member simulation.
- Executed in ONE host process: `python -m unittest -v test_home_category_contract test_continue_horizontal_touch_patch test_group1_scope_apk_15 test_cc_preimage_contract_patch` => **17/17 PASS** (includes 5 owner-audit tests, 6 touch-source checks, 1 full APK-scope check and the existing 5 controller compatibility tests). Earlier **19/19** remains a historical separate run, NOT the same 17.

## Remaining RED gates for #03

Actual left/right swipe, exact intended poster tap after swiping, no gesture-initiated launch, selected card/offset restoration on back, both Movies and TV Shows in cover/inner Fold positions/rotation, compact VERTICAL Resume-from-time vs Play-from-beginning chooser with touch-friendly rows and preservation of Kodi resume timestamps. None verified on physical Fold; there is no new signed APK to install. The native/global DialogSelect and Android input must remain unchanged without separate proof of an exclusively scoped effect. No final Group #1 checkbox yet.
