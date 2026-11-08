# Infinity three-correction handoff — not releasable

Target reported by the owner: combined APK2103464, Infinity2103464,
Cobra2103445 and Command Center0.3.5.62. These values supersede the earlier
462/CC61 report. No device was connected or changed during this investigation.

## Umbrella/POV

The reported Movies message, “Search interface not verified for this category”,
maps to an installed provider with no admitted operation. It is distinct from
the Kodi disabled-add-on state.

The authenticated original CC62 package contains the old provider inventory and
does not contain native_search_compatibility.py. A new focused integration test
ran the actual shipped CC62 inventory against the exact public provider sources
used by the existing compatibility work. Both were unsupported. Repeating only
that inventory integration with the two unchanged approved source files admitted
Movie Search and TV Search for both providers. No provider code was imported,
executed or modified. No navigation or identity operation was granted.

The passing provider matrix42435806833 is reused. CC62-SOURCE-REUSE.json pins the
existing approved source files; no additional compatibility development was
needed for these fixture versions. The observed Fold rejection is consistent
with this shipped package, but installed source identities are still needed to
confirm the exact Fold cause and current provider versions.

The CC61 ZIP from42448904041 is excluded from this device's update path.
Do not downgrade CC62, overwrite an unknown same-version generation, or assume
the host fixture versions are the owner's installed provider versions.

## Native Search crash

The retained failing run42437719318 records Scudo invalid-chunk-state during
deallocation. The guest ARM64 stack includes destruction of a CGUIListItem
property map, release of a shared CFileItem, CGUIInfoManager::GetMultiInfoLabel,
and XBMCAddon::xbmc::getInfoLabel. The corresponding original source functions
were recovered from authenticated source artifact13274901825 and checked against
the signed native source map. GUIInfoManager.cpp, GUIInfoHelper.cpp,
ModuleXbmc.cpp and AddonUtils.cpp match the preserved native source identities;
the four existing464 keyboard/graphics differences do not change these files.

The live-container helper copies a shared pointer out of the container. The
Python getInfoLabel API reaches that helper without the GUI guard already used
by getCondVisibility. Container reset can clear the item vector during navigation.
This is an evidence-supported unsafe access path consistent with the retained
stack, not proof that it is the only cause of every Search crash on the Fold.

An isolated native candidate changes only getInfoLabel and adds one standard
header in ModuleXbmc.cpp. For Infinity's skin and labels containing ListItem,
it uses the existing XBMCAddonUtils::GuiLock for the full label evaluation and
item-reference release. That guard already manages the Python call boundary
and the original frame/graphics lock order. There is no new mutex, altered
container ownership, observer workaround, or modification to GuiLock itself.
Other skins, non-item labels and every other function retain their original
implementation. The source is a candidate, not a released native correction.

The focused host test extracts the real original/candidate getInfoLabel bodies
and the real unchanged GuiLock constructor/destructor. It checks access during
a simulated GUI mutation, four item-label forms, existing lock order, and the
unrelated-skin/non-item/null controls. The original read completes while the
mutation guard is held; the candidate waits and performs guarded reads. PASS.
These are host adapters, not the complete Kodi container or Android process.

Real ARM64 compilation, a full native link, and before/after Android repeated
Search/provider-selection/navigation checks have NOT RUN. No production crash
repair is claimed. Existing isolated-heading PASS42441430136 and eight-cycle
diagnostic PASS42443988873 attempt2 remain valid diagnostic evidence only. The
eight-cycle observer modification is not incorporated into production.

## Silent Mode / Trakt

The existing Silent Mode implementation explicitly gates passive KaiToast
presentation and leaves interactive dialogs intact. The bundled Infinity Trakt
module manages local lists and has no OAuth authentication retry loop. Therefore
altering it would not address an unidentified external authentication dialog.

The actual failure producer and its automatic/manual distinction have not been
identified. The five-minute retry loop and exact dialog call site have not been
located in the authenticated bundled component source. A read-only comparison
with the pinned public Umbrella/POV auth sources did not establish that they own
the reported dialog. No third-party or authentication code was changed.

The text reports of the screenshots are available, but the image files themselves
were not attached to this execution context. The exact title/message, caller
add-on/version, and corresponding failure-handler source are still required.
No title-wide dialog filter or blanket interactive-dialog suppression is safe:
that could hide manual authentication or other required prompts.

The eventual correction must gate only automatic Trakt failure presentation
when Infinity Silent Mode is ON. Error recording and the five-minute cooldown
must execute exactly as before; manual sign-in, other authentication operations,
non-Infinity behavior, account data and tracking remain unchanged. No speculative
patch was made without identifying that boundary.

## Device verification

From an already authorized ADB host, this reads the APK metadata only:

    adb shell dumpsys package com.projectinfinity.kodi

The versionCode field is the APK code. For installed module identity, run:

    python3 read_device_inventory.py --out INFINITY-INSTALLED-INVENTORY.json

The collector reads the bounded signed module metadata, hashes of the named
owned module source files, and the two public provider addon.xml files at their
standard installed locations. It does not access user settings/databases, launch
or stop apps, install anything, change permissions, or write to the phone. It
does not clear installation or authenticate an unknown generation by itself.
If Android denies access, stop; do not root or bypass access controls.
The collector was syntax/CLI checked, not executed against the Fold.

## Release gate

No APK build, signing, installation or recovery change was initiated for these
three scopes. A combined release cannot be signed safely while the Trakt repair
is undefined and the native candidate is unverified. If the native correction
is confirmed and adopted, it requires a source-matched combined APK rather than
an add-on-only ZIP; reusing the old engine would not carry the C++ correction.
Do not assign or reuse release/recovery versions before checking the existing
owner registry and monotonic component requirements.

The next gates are: identify the actual Trakt producer; confirm the installed
module/provider identities; complete only the selected native/Trakt checks;
then perform one consolidated build/signing through the existing owner gate,
complete integrity/install-over/recovery checks, and one Galaxy Fold end-to-end
acceptance. No final installer, completed production repair, or Fold acceptance
is claimed by this handoff.

Cobra, layouts/themes, native provider search implementations, unrelated
providers, Continue Playing, Resume Hub, playback, user settings/databases,
account data, signing implementation and existing recovery are unchanged.
Watchlist-to-Progress tracking remains deferred. No shutdown test was selected.
