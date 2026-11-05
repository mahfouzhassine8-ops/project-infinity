# Infinity drawer height correction — source-only

## User's corrected requirement
The Power button **remains in its original place in the scrollable menu**, directly below System Hub and directly above the EXPLORE section. **Increase the drawer height** so Power is the last immediately visible option on opening; the entries below Power are accessed by ordinary scrolling. **Do not pin, float, relocate, duplicate, or change Power.**

The earlier source-only work branch `work/infinity-drawer-power-fixed-source-20261104` is **superseded** by this requirement and must not be packaged or merged. The corrective branch is `work/infinity-drawer-extended-scroll-20261104`, based on the unmodified scrolling-menu source in `work/infinity-drawer-shortcuts-scope-20261104`, not on the erroneous pinned version.

## Exact source change
Only one XML line changed in:
`repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml`

Old: `<height max="1050">88%</height>`

New: `<height max="1572">96%</height>`

All original menu structures, Power button ID `1198304`, power action `ActivateWindow(shutdownmenu)`, original scrolling grouplist ID `1198899`, menu order/children, actions and styling remain byte-identical. No separate footer or new control was added.

## Focused static checks (10 PASS)
GitHub re-fetch and diff confirmation: one changed XML file, one-line edit (1 addition/1 deletion), Power still part of original scroll list, no pinned footer, Scroll includes original items, Explore follows Power, and button bodies remain byte-identical. The scroll list begins at 132 and has a bottom inset of 18. At the **maximum drawer height** 1572 the visible list extent is `1572 - 132 - 18 = 1422` logical units. Power spans 1336–1416, and Explore starts at 1422. Thus Power is the last full visible row at that max height, with all subsequent content retained for scrolling.

**Important constraint:** actual final panel height uses the unchanged skin's available screen and maximum percent sizing rules; 96% of a sufficiently short viewport may be below 1572, so this static calculation is not a guarantee of Power visibility in every Android orientation or panel size. Physical Galaxy Fold front/inner and landscape verification remains pending. No runtime test or signed APK build was executed.

## Preservation
This is source-only. No approved APK, Cobra, search, provider, player, shutdown/checkpoint, Favorites data, native component, recovery, signed release, or installed package has been changed. No provider shortcut remaps are included; their separate previously documented scope remains pending.
