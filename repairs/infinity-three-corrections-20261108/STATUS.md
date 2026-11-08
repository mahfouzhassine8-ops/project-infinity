# Infinity three-correction handoff — not releasable

Target reported by the owner: combined APK2103464, Infinity2103464,
Cobra2103445 and Command Center0.3.5.62. These values supersede the earlier
462/CC61 report. No device was connected or changed during this investigation.
The owner directly confirmed these versions and Trakt sync1.2.8 on the Fold.
Trakt auto-update is ON and remains unchanged. Version labels are confirmed;
installed APK/module/provider source hashes have not been supplied.

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

Real Android ARM64 compilation and the full native engine link PASS in
[run42453405536](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42453405536),
sourcea2e803e7927c06ed4b7a8e526b688a730a1f31da, artifact13606537849.
The downloaded artifact's source maps confirm9,410 unchanged native files and
only the reviewed ModuleXbmc.cpp change. All71,213 strong native exports and all
11 runtime dependencies match the authenticated464 engine. The changed
getInfoLabel implementation is present in the linked ARM64 library. See
evidence/ARM64-ARTIFACT-IDENTITY.json and evidence/ARM64-LINK-VERIFIED.json.
Read-only ELF inspection also resolves actual AArch64 direct branch paths from
getInfoLabel through optional construction/destruction to the unchanged GuiLock
constructor/destructor (evidence/ARM64-GUARD-LINKAGE.json). The reproducible
inspector accepts only this exact linked-library hash.
The internal library is not an APK or installable update.

Android repeated Search/provider-selection/navigation and deadlock checks have
NOT RUN. No production crash repair is claimed. Existing isolated-heading
PASS42441430136 and eight-cycle
diagnostic PASS42443988873 attempt2 remain valid diagnostic evidence only. The
eight-cycle observer modification is not incorporated into production.

## Silent Mode / Trakt

The existing Silent Mode implementation explicitly gates passive KaiToast
presentation and leaves interactive dialogs intact. The bundled Infinity Trakt
module manages local lists and has no OAuth authentication retry loop. It is
therefore not the notification owner for the located sync-module dialog.

The exact screenshot wording has now been located in the pinned upstream
script.module.tmdbhelper.sync.trakt1.2.8 source, commit
fff6d9b38820d2e64e0b00cb2b469c72ff3fbe2b. TraktAuthenticator.notify_failure()
uses title32103 and message32111. TraktStoredAccessToken.on_failure() logs the
error and sets the300-second TraktRefreshTimeStamp before notification.

A presentation-only two-file correction is staged under trakt/candidate.
notify_failure checks Infinity Silent Mode for automatic failures only; recover
forwards its existing force_login flag so manual sign-in keeps the original
failure dialog and cooldown bypass. The second401 failure uses the automatic
path. No global dialog suppression or credential/Watchlist/tracking change was made.

Thirteen focused host checks PASS, including original failure reproduction,
automatic ON/OFF, other skins, cooldown expiry, manual sign-in, second401 and
successful refresh preservation. A complete pinned upstream tree audit PASS
confirms exactly2 modified files and144 unchanged files. These are local host
results with synthetic SDK/HTTP/clock boundaries, not Android/Fold acceptance.

The owner directly verified installed version1.2.8; source hashes remain
unverified. Auto-update is enabled. Do not upgrade, downgrade or replace an
installed version with this public reference blindly.
See trakt/REPAIR-NOTE.md for exact call paths, source pins and remaining gates.

An equal-version APK copy alone cannot establish deployment: the unchanged
Kodi AddonManager::FindAddons scans the external add-on directory after bundled
directories and selects the external copy when versions are equal. Packaging
must prove the selected Trakt path/version/hash on Android with an existing
external1.2.8 installation. No generic updater, source overwrite, version
reservation or settings change was implemented to bypass this gate.

## Device verification

From an already authorized ADB host, this reads the APK metadata only:

    adb shell dumpsys package com.projectinfinity.kodi

The versionCode field is the APK code. For installed module identity, run:

    python3 read_device_inventory.py --out INFINITY-INSTALLED-INVENTORY.json

The collector reads the bounded signed module metadata, hashes of the named
owned module source files, public provider/Trakt-module metadata, eight native
provider-route source hashes, eight relevant Trakt source hashes, and the
installed base APK hash when readable. It does not access user settings/databases, launch
or stop apps, install anything, change permissions, or write to the phone. It
does not clear installation or authenticate an unknown generation by itself.
If Android denies access, stop; do not root or bypass access controls.
The collector was syntax/CLI checked, not executed against the Fold.

An alternative already present on the Fold is Kodi Health Center's **Add-on
Exporter**. Export these four add-ons separately: Infinity Command Center,
Umbrella, POV, and TMDbHelper Sync - Trakt. Select **Add-on files only
(recommended for sharing/inspection)** and **Copy to a folder I choose**.
Attach the four ZIPs for local source inspection. Do not include saved
settings/data. This creates source export copies; it does not install a repair.
Its KHC_ADDON_EXPORT_MANIFEST.json supplies per-file size/SHA256 records, which
must be checked against the actual ZIP contents and then the trusted source
pins; the exporter manifest is not an Infinity module signature.

## Release gate

No APK build, signing, installation or recovery change was initiated for these
three scopes. The one necessary native compile/link is complete; do not repeat
it for reporting or metadata changes. A combined release cannot be prepared
safely while installed source identities are unknown. If the native correction
is confirmed and adopted, it requires a source-matched combined APK rather than
an add-on-only ZIP; reusing the old engine would not carry the C++ correction.
Do not assign or reuse release/recovery versions before checking the existing
owner registry and monotonic component requirements.

The immediate blocker is the missing installed source inventory/exports, not a
missing original-key signer. After that gate: prepare one source-matched
candidate and forward recovery through the existing owner-gated original-key
workflow; execute only the selected Android Search/Trakt/install-over/recovery
checks in ANDROID-REQUEST.json; then provide the verified installer for one
Galaxy Fold end-to-end acceptance. Runtime verification needs that signed QA
installer; object/link success cannot substitute for it. No final installer,
completed production repair, or Fold acceptance is claimed by this handoff.

Cobra, layouts/themes, native provider search implementations, unrelated
providers, Continue Playing, Resume Hub, playback, user settings/databases,
account data, signing implementation and existing recovery are unchanged.
Watchlist-to-Progress tracking remains deferred. No shutdown test was selected.
