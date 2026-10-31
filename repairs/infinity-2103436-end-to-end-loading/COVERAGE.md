# Signed436 loading coverage — incomplete implementation, no release claim

The exact signed Infinity ZIP is bound in SCOPE.json. The generated
results/SIGNED436-ACTION-INVENTORY.json contains all201 active unified skin XML
files,4529 action/content declarations,155 existing loading-frame instances,
and relevant calls from25 Command Center Python members. Every entry remains
explicitly runtime-unverified. Includes, dynamic expressions and implicit Kodi
list actions mean these counts are not a count of independently tested routes.

| Category | Actual signed source / ownership | Reliable signal and current limitation | Status |
| --- | --- | --- | --- |
| Home, Movies/TV/anime rails, Cinema, View All | Home.xml, Includes_InfinityHomeUnified.xml, Includes_InfinityRails.xml, Includes_CinemaBrowse.xml; explicit builtins and implicit directory lists | XML action/dispatched identifies dispatch only. It cannot prove native directory readiness. Registered item frames exist; real Kodi busy state drives drawer fallback. | Existing partial coverage; expansion/visual verification unfinished |
| First-party library, Resume/Continue, custom lists, navigator, commands | Command Center plugin.py main wrapper, routes movies/movie-navigator/tv/tv-navigator/custom-lists/library/continue/resume/commands | Existing preparation context terminates on Python return/exception; endOfDirectory publishes results, including empty results. Publication is not proof of viewport painting. | Independent task ownership corrected and host-tested; navigation/render integration pending |
| Search entry, provider selection, Search All/history | infinity_search.py _open_search and plugin search-provider/search-all routes | Search inventory preparation has an explicit context before modal entry. Selecting a provider is not executing a search. External execution and source resolution retain their original contracts. | Existing semantics preserved; representative runtime and broader readiness work pending |
| Native directories, details, seasons/episodes, external providers | MyVideoNav.xml and native View_* includes; original add-on paths | Native busy lifetime is observable; arbitrary provider completion cannot be inferred from list length or builtin return. No second provider invocation or prefetch is introduced. | Safe original routing retained; fallback coverage incomplete |
| Favorites, drawer, system settings, profile/add-on browser | DialogFavourites.xml, Custom_1198_InfinityNav.xml, Settings.xml and Kodi windows | Dialog identity and real loading ownership must be matched before hiding native feedback. These windows do not all use SideBladeLeft. | Additional frame/readiness integration unfinished |
| Command Palette, Health/Command Center, information and settings dialogs | Custom_1190_InfinityPalette.xml; default.py, information.py, infinity_settings.py; external health add-ons | Opening a modal is not its completion. Health launch belongs to its installed add-on. Current preparation coverage cannot be generalized to these controls without mapping the actual dialog. | Safe original actions retained; new integration unfinished |
| Playback startup, fullscreen/PiP return, recovery, subtitles/audio | Existing Kodi/player and provider contracts | Player callbacks and provider resolution are not equivalent to directory readiness. Playback/persistence code remains frozen. | No new playback behavior; current-device verification pending |
| Background refresh, overlapping directories and resize | action_loading.LoadingState and existing service tick | Terminal events belong to individual tokens. Same-profile window/geometry changes do not finish background tasks. Profile mismatch rejects delayed work. | Four new host regressions and12 existing state regressions PASS; runtime pending |
| Other background artwork/metadata work | Native Kodi/third-party loaders and existing first-party publishers | No authoritative universal artwork-completion callback has been established. Do not invent a counter or timer for unobservable work. | Native/external fallback; no universal coverage claim |

## Proven defects versus unresolved delay

The signed action_loading.py globally advanced a retirement watermark on any
task completion, discarded background jobs on window/geometry changes, and
accepted delayed background tasks from another profile. Focused regressions
reproduce these defects against the exact signed source; the candidate corrects
the three affected methods. No new worker, poll interval, native action,
provider execution, persistence operation or navigation delay is added.

Signed DialogBusy.xml sets its entire content group invisible unconditionally.
The replacement frame is not installed on every native/dialog surface. This
requires a separately verified availability/fallback correction; the current
checkpoint does not falsely mark it repaired or expose the old large panel.

Two actual plain `ActivateWindow(Videos)` routes occur in
Custom_1198_InfinityNav.xml: Library1198104 and Discover1198109. This does not
identify the recorded tap. A focused POV item is not proof of the executed
route. The75second delay is not reproduced, measured or repaired at this
checkpoint. No performance gain is claimed from these host state tests.

## Runtime and media access limits

No20741 media bytes are exposed in the workspace or current attachment tools;
no original video/static-frame inspection is claimed. The supplied scope's
description is secondhand evidence only.

The workspace has no adb, Kodi executable, /dev/kvm or attached native-ARM
Android target. The prior authorized API37.1 x86_64 native-bridge route failed
inside unchanged libkodi.so constructors before Kodi/Python/readiness tests
(run40726662543; see the existing Infinity performance runtime/OUTCOME.md).
That historical failure is not a newly executed436 result. Repeating it or
modifying protected native libraries is not a valid substitute for a working
runtime target. Current436 Kodi/skin execution must still be established before
the required end-to-end visual/readiness gate can pass.

No successor version is reserved, no component is reauthenticated, no APK is
built/signed, and no recovery baseline is changed by this checkpoint. The work
is incomplete: remaining frame coverage, truthful native fallback, complete
route classification, timing/runtime verification and final package gates must
be completed before a consolidated candidate can be delivered.
