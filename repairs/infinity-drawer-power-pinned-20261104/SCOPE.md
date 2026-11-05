# Infinity drawer always-visible Power — source-only authorized correction

## Corrected user intent (2026-11-04)

Power is **the last visible option in the initial drawer viewport**, accessible as soon as the user opens the drawer without scrolling. The extra Browse Files, Downloads, Media Sources, Explore, and other options must remain usable through a scrollable list, **not push Power below the fold**. Do not move Power to the end of the entire scrollable content or simply enlarge the drawer blindly.

The existing shutdown-menu action, label, icon, visible styling, original control ID `1198304`, checkpoint/shutdown implementation, and Close action must remain unchanged. The Power row is a **fixed bottom footer**, with the main options in a reserved scroll area above. The footer must remain independently reachable by touch; from the scrolling list, Right must also be able to focus Power. The scrollable body continues to own all the original menu rows in their original order except for moving Power into its visual footer.

## Strict allowed source edit

Only `repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml` on this **isolated work branch**, based on `work/infinity-drawer-shortcuts-scope-20261104`. No accepted or signed APK, original code, module, skin package, source checkpoint or user device is modified. This source-only candidate has not been signed, installed, accepted, or released.

Geometry: original panel top/header fixed; scrolling grouplist `1198899` reserves **104 units** at its bottom (18 margin + 80 footer + 6 spacing). Power group is a sibling of the grouplist at left/right 18, bottom 18, height 80. All new content scrolls in the list without covering Power. Preserve original dialog height maximum, drawer width, background, animations, theme, and all menu destinations. Add only a Right-focus link from the scroll list to the original Power button, keeping the original Power button body byte-identical except indentation.

## Selected checks before execution

1. Exact starting source blob SHA `3821a892ff54e74b29c91cccd14b147d0cbdb214`; enforce one unique Power group, one grouplist, one closing anchor, no duplicate IDs or controls.
2. Confirm Power is outside grouplist and anchored, the grouplist is reduced by exactly one row+gap, Explore/Library and all other buttons remain in the scroll list, Power label/icon/actions unchanged.
3. Preserve all other action strings and child control definitions, original package and entrypoint absent any new code. No run of application, native, shutdown or unrelated tests.
4. Run source-only structural and focused check after staging. Actual front/inner Fold display, touch+remote focus, rotation, compact scaling and scrolling require **physical** verification; host structure is not device PASS.

No APK packaging, original-key signing, shutdown work or changes to Cobra, provider/Search, player, media view, Favorites data, native Kodi, or accepted branches are authorized by this source-only UI change. The separate four-shortcut route investigation remains on its prior branch.
