# Infinity Skin 1.0.5.213 — Add-on Tile Selection RC1 (TEST ONLY)

**Applies to locked Infinity Kodi Mobile APK 2103377 RC5.** No APK update, engine rebuild, Trakt change, or Resume Hub modification.

**Locked parent skin:** `skin.infinity.diggz` 1.0.5.211, exact downloaded ZIP SHA-256
`460762f78ad2a1cb2d54639e973d20a5958de0c22575a0d7f228b7f1cdc73815`.

**New candidate:** `skin.infinity.diggz-1.0.5.213-Addon-Tile-Selection-RC1-TEST.zip`,
SHA-256 `2f251ccca12bb88c439ad94c11d17a2b55c233ecfb4e4cdbe01f8d9ba4cc0880`,
59,125,177 bytes.

## User-reported bug

On Android Fold portrait, the **ALL ADD-ONS / VIDEO SOURCES (35 items)** grid in *Infinity Browse* displays add-on posters and highlights them, but tapping **Otaku**, **Cumination**, and other add-ons does not open them. Scope is the entire grid, not a specific provider add-on.

## Root cause and minimal repair

The custom dialog `Custom_1193_InfinityBrowse.xml` uses Kodi's dynamic XML panel `<control type="panel" id="50">`. `<content>$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>` loads source `addons://sources/video` but fails to supply the video folder target Kodi requires for opening folder items. Kodi's official *Dynamic List Content* documentation explicitly requires a `target` for folder navigation.

For each of the 13 profile-specific `Custom_1193_InfinityBrowse.xml` files, make **only** this exact substitution:

```xml
<content>$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>
```

becomes

```xml
<content target="videos">$INFO[Window(Home).Property(Infinity.BrowsePath)]</content>
```

No ad-hoc `RunPlugin`, hardcoded Otaku paths, D-pad hacks, touch overlays, or alternative dialogs. The selected dynamic item retains its native Kodi folder routing and context handling. Only `addon.xml` changes version **1.0.5.211 → 1.0.5.213**.

## Validation and preservation

- All **13** responsive Browse layouts included: `16x9`, `20x9`, `5x6`, `6x5`, `portrait`, `unified`, plus `responsive/base`, `landscape`, `portrait`, `square`, `tall`, `ultrawide`, `wide`.
- All **2,075** skin XMLs parsed cleanly; full ZIP CRC readback passed.
- **2,964 of 2,978** ZIP entries byte-identical to locked skin 1.0.5.211; **14** changes in total (**13** browse XMLs and **1** skin `addon.xml`).
- Item placement, typography, images, focus ring, hitboxes, navigation directions, Home's browsing paths, existing UI, playback, services, ambient, Continuity and native shutdown code remain unchanged.
- The locked **1.0.5.211** ZIP is not overwritten. The locked **2103377 RC5** APK remains unchanged.

## Physical test before lock

Install this ZIP as a Kodi skin update (not a fresh installation). Open **All Add-ons** and tap Otaku, Cumination, then other items: each should enter its native add-on view. Check Back returns normally to Browse. Check cover screen, unfolded portrait/landscape, and existing movies/TV browse panels. If a tile still only highlights, save a diagnostic capture and report whether **D-pad/Enter** opens it; this distinguishes routing from Android touch hit-testing.

**No physical test has been performed by the assistant. Do not lock or replace 1.0.5.211 until the user passes device testing.**
