# LOCKED DESIGN — Infinity shared media browser (user visual approval, 2026-11-04)

**Design acceptance: APPROVED / FROZEN. Implementation: NOT BUILT OR TESTED.**
The user examined the rendered mockup of their Umbrella VIDEOS browser and explicitly said: **"Lock that. That's exactly how it's supposed to look like."**

## Canonical visual reference

- Canonical image in the approving conversation: `a_polished_ui_mockup_of_the_same_screen_redesigne.png`, 820 × 1918 PNG, 1,547,339 bytes.
- Image SHA-256: `6786b5cadb7153bb0036a651dcfba889a58f2a5acd79a759a798302e2d70c0ad`.
- This record binds to **that specific image**. Do not substitute a different rendering or treat generated/example movie titles, posters, rating values, artwork, synopses or example metadata as real provider results.
- Reference scope: a portrait folded-phone screen headed `VIDEOS` and `Umbrella`, Infinity's black/cyan design, with a clean scrollable media list on the left and selected item's image/details on the right.
- The source image exists in the approving ChatGPT conversation. This Markdown record is the persistent design specification; no repo image binary was added by this commit.

## Locked composition

1. Preserve the Infinity infinity-symbol header, `VIDEOS` title, actual provider subtitle and thin cyan divider, along with the existing hamburger/menu affordance.
2. Left: a balanced, **fully legible list** of selectable media with small, properly proportioned item art, title and useful secondary metadata; one clean cyan outline/selection state. No excessive truncation, collisions, unexplained blank white rectangle, or focus overlapping rows.
3. Right: **only the currently selected movie/TV item**, with its real appropriately cropped/contained poster, title, available metadata, synopsis, and existing valid contextual actions below. Keep poster proportions stable without stretching. The content changes with the selected item.
4. **Remove the huge Apple-logo/`Trailers` column, unrelated provider icon enlargement, and enormous default-thumbnail/preview overlays entirely.** Never substitute a directory icon for a title's actual poster. An ordinary *small* Trailer action in the selected item's details area is allowed **only when the already-supported provider action exists**; it must never recreate the unwanted visual.
5. Black Infinity background, restrained cyan focus/dividers, proper spacing and readable hierarchy. Support existing light/dark mode parity; dark mock is the precise approved reference, not permission to break light mode.
6. Bottom gesture guidance in the reference conveys semantics; preserve the clean visual and show cues in a way compatible with existing controls. Do not introduce nonfunctional decorative Play/Trailer/Info buttons; only show actual supported actions.
7. Fit front/folded and unfolded displays and orientation responsively, **without shrinking the content to an unreadable sliver** or fattening a poster. Preserve approved front/inner viewport/layout ownership and existing View Modes; adapt layout where needed, not by indiscriminate independent X/Y scaling.

## Locked universal touch behavior

Across Infinity's selectable movie/TV/provider/list/card/poster/favorites/add-on/navigation item surfaces where these gestures apply:
- **First tap** selects/highlights the item without activating it.
- **Second tap on the already selected item** opens/activates it.
- **Press and hold** opens that item's existing context menu.
- Back/return preserves the established focus, selection, and navigation semantics.
- No duplicate activation, unintended player start, context-menu bypass or reinterpreted long press. Touch and keyboard/remote paths must coexist. Respect native modal controls and one-tap buttons such as Close/Back/Power where a two-tap requirement would be unsafe or inappropriate; do not turn this into a change to the shutdown mechanism.

The user explicitly clarified the screenshots were **examples**, not provider-limited scope: consistency is required throughout applicable **Infinity** experiences, not merely Umbrella or this one view. Implement shared UI/gesture ownership, *not* separate provider-specific hacks.

## Mandatory existing-system integration — explicitly reaffirmed by user

**Nothing in this design is a standalone or parallel implementation. Every new or changed capability must be connected to the existing Infinity ecosystem and behave as a native extension of what is already approved.** The theme is one example, not the only integration obligation. This is a release-blocking acceptance contract, not an optional styling preference.

- **Existing theme ownership:** Resolve colors, backgrounds, panel surfaces, focus treatments, typography, spacing, and imagery through Infinity's established theme/skin variables and resources. Honor the already-implemented light/dark choice immediately, including on every provider page, dialog, poster and details surface. Do not hardcode a new black/cyan palette because the design mockup is dark, or ship a separate theme toggle.
- **Existing view/mode ownership:** Retain and integrate the approved global media-view preference, List/Posters/InfoWall/TriPanel and other supported modes, the front/inner Fold reflow, landscape/portrait rules, window/view IDs and focus state. Apply the approved visual language through their existing entry points; do not create a competing browse engine or silently force a different saved view.
- **Existing touch and controls:** Use the existing native Kodi/Infinity touch dispatch and contextual-action paths to implement first-tap select, second-tap activate, and hold-for-context across applicable surfaces. Reuse existing real actions, including playback, info, long-press, Back, selection restoration and modal dismissal; do not add decorative controls or another gesture tracker that conflicts with earlier work.
- **Existing media/provider ownership:** Display the selected item via Kodi's existing provider list item, art and metadata fields. Reuse the verified provider routes and installed source adapters. Missing posters/metadata should degrade gracefully, never substitute a huge unrelated directory icon, forge results or change provider behavior.
- **Existing loading, lifecycle and persistence:** Respect the existing loading-indicator ownership, cancellation, native admission/worker lifetime, app foreground/background behavior, health diagnostics, data durability, settings, Favorites and Continue Playing. No duplicated timers, workers, network requests, storage models, or new persistence owners.
- **Existing cross-experience isolation and packaging:** Cobra, chooser, protected shared/native runtime and shutdown remain unchanged without separate authorization. Any implementation must pass the current module-authentication, original-signer, install-over version, exact-member preservation and forward-recovery gates. Do not treat a source-only test or visual mock as signed/device-accepted.
- **Integration verification:** Before claiming PASS, test that changing the existing Light/Dark setting updates the actual new surfaces; the chosen global view persists through page/provider changes; front/inner reflow, orientation, touch, focus, selected-item art, scroll, long-press, Back/return, loading and playback handoff all use the existing system. Report any integration blocker instead of introducing a second implementation.

**In short: connect to what we already built; preserve it; improve it in place.** The mockup defines the approved look and interaction target, not permission to replace existing architecture.

## Preservation and safety

- Do **not** change Cobra, original approved chooser, native playback/codec behavior, provider search routes/logic, Source/Library destinations, saved media or Favorites data, view-preference persistence, provider settings, security, checkpoint/shutdown admission, app identity, original signer or locks.
- The previous confirmed Search `state_changed` defect is a separate, unresolved workstream.
- The direct drawer-shortcut and drawer-height changes are separate scopes. Do not combine them implicitly merely because the screenshot also shows the hamburger.
- Do not assume all items have posters, trailers, ratings, information or playability; handle absent metadata gracefully without invented artwork or dead controls.
- This design lock **is not** an APK build approval, an application change, a device PASS or an accepted physical release. No source overlay, APK, module, provider data or signed baseline is modified by recording approval.

## Before claiming implementation

Audit existing Kodi Video list and shared media art/layout/gesture ownership against the exact approved signed baseline, then make narrowly necessary, reviewable changes. Verify at least:
- Umbrella, Red Light, The Crew, Nixtoons, Otaku and any other installed compatible video provider **as available**; native indexed Movies/TV, files, Favorites and relevant view modes, with content-specific fallbacks.
- Selected item poster versus directory icon, missing art, blank metadata, clipping, list scroll/selection, long press context, first/second tap activation, Back, and no unintended double launch.
- Fold front and unfolded portrait/landscape, theme light/dark, actual phone visual fit and touch acceptance.
- Exact authorized change allowlist; preserve original cert/update-over signing, no uninstall or data clear. Do not run unrelated feature or shutdown tests automatically.

The user remains the sole physical Galaxy Fold acceptance authority. **Until implemented and physically accepted, status is DESIGN LOCK ONLY.**
