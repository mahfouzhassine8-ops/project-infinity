# INFINITY — PHYSICAL FOLD VIDEO EVIDENCE: PLAYER ROTATE AND HOME CONTINUE WATCHING

**Scope:** Two previously known regressions only. This is the user's **2026-10-18 video assessment**, not a new build authorization, not a new locked skin, and not permission to modify locked APK 2103384. Keep the independently approved Video Sources tile-selection/context-menu repair in its [separate exact contract](APPROVED-ADDON-VIDEO-SOURCES-MENU-EXACT-CONTRACT.md).

**Evidence provided privately by user:** `18891.mp4`, SHA-256 `73c52dac35de6b6fe4f9297aef785b468ff0c5bf107bd27292f7c5d21da0a46e`, duration ~96.74 seconds, 1080×2520 vertical Fold screen recording. **Do not upload or commit the recording or captured content into this public GitHub repository.** Observations below are from sampled original video frames, not a synthetic reproduction.

**Source foundation:** User-locked Infinity **APK 2103384**, `com.projectinfinity.kodi`, signed APK SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`. Installed `skin.infinity.diggz` 1.0.5.225 was observed previously; physical screenshot says `INFINITY 1.0.5` but doesn't itself establish precise skin patch version. Preserve Diggz/custom skin, native playback, saved data, Rails and Essential-First normal Close unchanged.

## Regression 1 — video player's Rotate control performs Repeat

### Physical video evidence
- **~7–16 s**: Fullscreen playback OSD is open on a real video, displaying the horizontal control strip.
- The control near the right edge, between display/monitor and lock, presents **loop/repeat arrows** instead of the approved Rotate action.
- **~12–16 s**: After activating it, overlay text visibly reads **`Repeat: Off`** and the tile appears focused/highlighted.
- This is a **functional wrong-command mapping**, not merely a cosmetic or icon issue. Video continues playing.

### Required behavior (restore, do not redesign)
- Use the same intended OSD slot with the original **Rotate** action, icon, tooltip/accessibility name, and state indication.
- Original documented policy: **Follow Device (white) ↔ Infinity-controlled orientation (cyan)**; handoff to the app's existing Android rotation pathway, not Kodi's repeat/playlist action. Recheck that this behavior applies only to the valid Android video player contexts without affecting TV/Cobra or unrelated controls.
- The slot must **never call `PlayerControl(Repeat)`** or update repeat status when pressed; pressing Rotate must actually change/control orientation as approved, with no video recoloring, playback stop, session loss, or background/PiP regression.
- Preserve the adjacent fullscreen controls and existing native `libkodi.so`; don't add a redundant Rotate button or move the strip.

### Reuse prior work
- `repairs/full-system-20261017/player_rotate_226.py` and `test_player_rotate_source.py` already contain a forward-only candidate skin **1.0.5.226** intended to replace `PlayerControl(Repeat)` with native Android `PLAYER_ROTATION_UNLOCKED` / `PLAYER_ROTATION_FOLLOW_DEVICE` actions. Source tests existing ≠ proven installed APK/skin or Fold pass.
- **Verify source/input/skin baseline first**. Prefer reusing/correcting the reviewed .226 candidate over rewriting or reintroducing already fixed components. Never silently install it or claim physical success.

## Regression 2 — Home Continue Watching long-press context menu missing

### Physical video evidence
- **~34–38 s**: Infinity Home clearly displays the populated **`Continue Watching`** rail (the user refers to this feature as `Continue Playing`), with thumbnails, names and watched indicators. **The rail itself works.**
- **~36–38 s**: Selecting a progress item shows `Choose an action`, offering `Resume from 00:02:44` and `Play from beginning`. This is a real, useful playback-choice dialog and must remain.
- **~42–44 s**: Playback flow continues to a separate `Choose Action` provider/add-on picker listing IMDb Trailers, Umbrella, POV, Seren, The Crew, etc.
- **~44–47 s**: A provider/route choice leads to source preparation and eventually playback. **At no point in this recorded interaction is the former item-level press-and-hold options/context menu visible.**
- The recording does **not** expose raw Android touch/long-press events or the actual input handler. It proves the visible result, not the exact callback at fault. Don't assume this requires native APK modifications until the installed skin/rails/helper path is traced.

### Required behavior
- **Keep** the populated Continue Watching rail, its selected media identity, blue watched markers, resume positions, normal single-tap playback, `Resume from ...` / `Play from beginning` choice, provider chooser, and subsequent playback intact.
- **Restore** the **former item-specific long-press context menu** for a Home Continue Watching card. A deliberate press-and-hold should dispatch the correct focused item into options (not silently route through the normal click / Resume dialog / provider list). Close menu with Back/cancel, remain at the same highlighted card/scroll position, no unintended launch.
- Restore approved existing actions from the actual prior implementation, not random generic actions copied from the All Add-ons menu and not a new arbitrary eight-item list. Actions must relate to the selected movie/episode and respect watched/resume progress. If the precise historical menu content or component isn't available, **inspect the prior source and request confirmation** rather than inventing alternatives.
- Keep this separate from `All Add-ons → Video Sources` two-tap-to-launch grid semantics and existing Movie/TV Add-on Rail Options repairs. Never force double-tap for Continue Watching unless the user specifically approves it.
- Verify Fold touch holding: long-press recognition, Kodi RightClick/ContextMenu (where appropriate), selection identity, popup positioning, Back dismissal and preservation of content.

## Regression gates and protected scope

These are **two lost behaviors in an otherwise working system**, not a request to rebuild watched/resume/player functionality. Preserve every other implemented feature.

1. Source review: compare current installed skin/add-on helper with the earlier user-approved Rotate and Continue Watching context actions. Trace event wiring; no speculative duplicate handlers.
2. Targeted experimental skin/helper correction from correct installed source. Preserve `skin.infinity.diggz` ID, Diggz setup, existing installed data and new baseline. No need to recompile `libkodi.so` unless evidence shows an actual native dependency.
3. On Fold: activate OSD slot, confirm actual orientation control and **no Repeat toast**; check white/cyan policies, fold/unfold, rotate and player/PiP continuity.
4. On Fold Home: single-tap retains Resume/Play choice; long-press opens media-specific context menu without playing; selection and focus persist when dismissed. Validate movies and episodes.
5. Keep complete accepted Video Sources context menu design in the separate approved spec. Do not conflate the two context menus.
6. The signed **2103384** native shutdown baseline remains locked and its exact APK safely backed up. Every future signed APK must meet exact-APK real Android fresh/upgrade Close, preservation and physical Fold verification before user approves a new lock. An unverified skin candidate is NOT physically accepted by host source tests.

**STATUS:** Video reviewed; two regressions now evidence-grounded and scoped. **No implementation, package/build, emulator acceptance or physical retest of fixes has been performed in this evidence entry.**
