# Remaining workstreams — concrete interface findings

This audit retains the consolidated scope while the native correction passes
its first gate. It does not claim the watched or touch features are implemented.

## Watched / Resume Hub / Watchlist

The installed .20 overlay already implements canonical typed identities,
automatic >=95% completion, watched history, manual actions, Watchlist,
Collection, atomic persistence and the existing essential writer participant.
Its context ingress supports trustworthy never-played movie/episode metadata.
These are the starting implementation, not features to replace from .19.

The missing universal presentation boundary is substantive: context.py's
publish_selected_state explicitly decorates a selected ListItem copy. This does
not decorate every item in a foreign provider listing. Kodi 21.3 Window::getControl
can wrap native lists, but ControlList::getListItem reads Python-owned vecItems,
not an arbitrary provider container's CFileItems. Window.Property's key is also
translated as a literal in GUIInfoManager, so nested dynamic property-name
strings are not an established cross-row watched lookup API.

Do not call a recolored native overlay universal Resume Hub synchronization.
The next stage needs a supported, tested provider adapter or a narrowly scoped
read-only metadata presentation bridge with an immutable in-memory identity
index. It must avoid GUI callbacks into Python, per-poster disk reads, provider
database writes and weak title matches. Preserve existing manual actions,
progress, Watchlist/Collection and IDs; explicitly report unsupported native
provider two-way actions and unverified anime numbering.

The exact approved reference remains the small blue circular badge with a white
check at a poster's upper-right, with modest watched-title softening. No broad
row reflow or redesign is required.

## Custom All Add-ons grid and Home rails

The immutable TEST4 APK's system/keymaps/touchscreen.xml maps global longpress
to RightClick. InputManager preserves coordinates for that mouse action. A
coordinate-loss assumption would therefore be incorrect for this exact keymap.

A distinct native behavior is verified in the actual TEST4 binary:

- GUIBaseContainer::OnMouseEvent saves the old selected index, selects the item
  under the event point, and calls OnClick for a right-click only when the
  selected index did not change.
- ELF instructions 0x1a906d0 through 0x1a906f8 check RightClick (101), compare old
  and new selection, and branch around OnClick when they differ.
- Thus the first longpress on a different tile can select it and consume the
  event without opening its context menu. This is a specific mechanism to test
  against the reported cross-column behavior, not proof that every physical
  touch failure has this one cause.
- TEST4's OnInfinityRailLongPress coordinates and single-dispatch guard apply
  to the Home rails only; custom window 1193/panel 50 is outside that opt-in.

The next touch correction should preserve ordinary mouse/right-click behavior
and provider-owned context menus. Scope any Android longpress preselection to
the real processed custom grid, respect transforms, gesture state and modal
dialogs, and avoid duplicate context events. Reproduce both the first hold on a
different tile and the already-selected tile. Repeat left/right/edge positions,
scrolling and all Fold profiles. Source/counterexample tests do not replace the
required physical repetitions.

Disabled recovery remains a separate requirement: offer native add-on management,
show installed-but-disabled add-ons, confirm destructive Disable actions and
verify Otaku enable/reappearance with settings intact. Do not replace this with
an uninstall/reinstall or confuse custom-hidden, disabled and missing providers.

## Skin and integrated gates

The locked .223 ZIP has 3,055 files. Every extracted file matches it, and all
2,135 XML files parse. The inventory covers 16x9, 20x9, 5x6, 6x5, fallback,
portrait, responsive/base, responsive/landscape, responsive/portrait,
responsive/square, responsive/tall, responsive/ultrawide, responsive/wide and
unified. Manifest-declared runtime resolution and source variants are recorded
separately; their existence is not visual or touch acceptance.

All four original Android shutdown probes are retained for the new native APK.
The accepted TEST4 baseline had fresh/loaded passes and cold/core-initialized
failures. Record new outcomes as observed, without changing the tests or hiding
red results. The 5/20/45/90-minute physical Fold matrix, themes/screenshots,
playback/PiP, background continuity, persistence and final approval remain open.
