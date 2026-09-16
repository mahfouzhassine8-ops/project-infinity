# Cobra Mobile + TV Guide locked contract

Status: LOCKED implementation target
Baseline: RC3 Runtime v3 / player presentation 2103141
Scope: Cobra Android presentation runtime + ZIP UI contract only. Kodi native, renderer, provider/playback ownership, rotation, Fold ownership, background/resume and Infinity handoff remain protected.

## Mobile View
- Touch-first portrait layout.
- Live preview first, followed by current channel/program and EPG summary.
- Category picker, search/filter controls, favorites/recents and channel list.
- Persistent mobile navigation appropriate to Cobra.
- Normal channel tap selects/plays.
- Long press opens a Cobra bottom action sheet.
- Action sheet is context aware: Favorite/Unfavorite, Record/Schedule where supported, Add to Group where supported, View Channel Guide, Channel/Source information, Hide Channel; sharing only when supported.
- Bottom sheet dims background, consumes inside taps, dismisses by outside tap, Back, and downward dismissal gesture when practical. Destructive actions remain separated.

## TV Guide View
- TV/remote-friendly navigation with Favorites and channel groups/categories.
- Selecting a group exposes that group's channel/EPG grid.
- Proper EPG timeline with channel number/logo/name column, program cells, current-time marker, focus/selection state and current program detail.
- Preview/player area above the guide when navigation is expanded.
- First activation of a channel/program selects it and starts/updates the preview player.
- Second activation of the already-selected channel/program promotes the same stream to fullscreen playback.
- Back from fullscreen returns to the TV Guide with selection/preview state preserved.
- Expanded guide state may collapse navigation to maximize the EPG grid while preserving a route back to groups/menu.
- Touch and D-pad/remote behavior must both remain usable.

## Shared
- Mobile and TV Guide are two views of the same Cobra data/runtime, not separate apps.
- Preserve Runtime v3 ZIP UI installer and theme contract.
- Preserve player-settings dismissal and deterministic Fit/Crop repair.
- Preserve RC3 async/lifecycle guards.
- No native Kodi rebuild solely for presentation changes.
