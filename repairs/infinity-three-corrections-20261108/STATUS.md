# Infinity three-correction handoff — not releasable

Target reported by the owner: combined APK2103464, Infinity2103464,
Cobra2103445 and Command Center0.3.5.62. These values supersede the earlier
462/CC61 report. No device was connected or changed during this investigation.
The owner directly confirmed these versions and Trakt sync1.2.8 on the Fold.
Trakt auto-update is ON and remains unchanged. Version labels are confirmed;
The four installed-source exports are now supplied in
Infinity_Source_Exports_For_Work.zip (SHA256
e14b1e9c8441e78ce5c930dea8c7a5885053011d531df9ec51377fcb18298b65).
The remaining device identity gap is the installed APK hash and the16 source
records belonging to the other three signed first-party module roots.

## Umbrella/POV

The reported Movies message, “Search interface not verified for this category”,
maps to an installed provider with no admitted operation. It is distinct from
the Kodi disabled-add-on state.

The authenticated original APK CC62 package contains the old provider inventory
and does not contain native_search_compatibility.py. The actual installed CC62
export additionally contains the exact approved helper as an unlisted loose
file, while its inventory and78-file signed manifest are still original.
The original RSA signature and all62 exported declared CC source hashes PASS.
This directly establishes an inactive partial compatibility update. A focused integration test
ran the actual shipped CC62 inventory against the exact public provider sources
used by the existing compatibility work. Both were unsupported. Repeating only
that inventory integration with the two unchanged approved source files admitted
Movie Search and TV Search for both providers. No provider code was imported,
executed or modified. No navigation or identity operation was granted.

The passing provider matrix42435806833 is reused. CC62-SOURCE-REUSE.json pins the
existing approved source files; no additional compatibility development was
needed. The same actual inventory scan now also passes against the supplied
Umbrella6.8.00 and POV6.11.02 installed sources: old CC62 rejects both, and the
approved two-file overlay admits only native Movie/TV Search. This is source
integration evidence, not actual Android result/heading execution.
See evidence/DEVICE-SOURCE-VERIFICATION.json. No provider code was executed.

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

The complete installed145-file source export is now verified. Its two patch
preimages exactly match514a82e5. Two other installed files differ from the public
reference: keys.py contains an installed CLIENT_ID application identifier and
recovery.py contains the Account Manager Lite sentinel-refresh-token guard.
Both are preserved byte-for-byte. The actual-source candidate changes only the
two approved notification files, preserving143 others. The original13 host
cases were run once against this changed installed recovery dependency, plus
one sentinel-preservation case:14 PASS. The old reference evidence remains
unchanged. Auto-update is enabled and remains unchanged.
See trakt/REPAIR-NOTE.md for exact call paths, source pins and remaining gates.

An equal-version APK copy alone cannot establish deployment: the unchanged
Kodi AddonManager::FindAddons scans the external add-on directory after bundled
directories and selects the external copy when versions are equal. Packaging
must prove the selected Trakt path/version/hash on Android with an existing
external1.2.8 installation. The staged standard bundled-source route uses
forward1.2.8.1 metadata and1.2.8.2 recovery, retaining the complete installed
functional source except the two approved notification edits. There is no
generic updater, forced external source overwrite or settings change.

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

The owner subsequently reports Health Center2.5.26 Add-on Exporter fails for
Umbrella6.8.00 with “Database has no readable SQLite header; raw fallback
refused”. The matching preserved helper receives every file in the add-on
folder, including database-extension files even in source-only mode. The exact
refusal was reproduced locally without a SQLite connection. The installed
failing filename and Health Center source hashes are unknown. Do not retry a
full-folder export, change the snapshot helper, or alter any database to obtain
Search source. See HEALTH-EXPORT-INVESTIGATION.md for the reference-version
distinction and five passing local checks.

Prefer the existing read-only collector with optional computer-only source
copies:

    python3 read_device_inventory.py --out INFINITY-INSTALLED-INVENTORY.json --sources-out INFINITY-SOURCE-INSPECTION

Use an already authorized ADB host. This writes a new local folder containing
only specifically named code/manifests, not a recursive add-on copy or database
backup. It includes the provider routes, Trakt failure-path sources, CC metadata
and inventory, and the three Health Center implementation files needed to
identify the installed exporter. Attach the JSON and a ZIP of this local folder.
The ZIP is diagnostic source, not an installable fix. Access denial remains a
blocker; no root or permission bypass is authorized.

## Release gate

The one necessary native compile/link is complete; do not repeat it for
reporting or metadata changes. Actual installed-source authentication and
scoped source integration now PASS. Preparation is selected in
PACKAGING-SCOPE.json and reuses the existing original module signer and owner
bundle assembler. Original-key APK signing PASS for466 and matching forward recovery467. Android/Fold acceptance remains pending.
If the native correction
is confirmed and adopted, it requires a source-matched combined APK rather than
an add-on-only ZIP; reusing the old engine would not carry the C++ correction.
Do not assign or reuse release/recovery versions before checking the existing
owner registry and monotonic component requirements.

The sole-signer history audit checked47 signed APK releases and confirms465 is
latest issued. The selected unused pair is466/467, CC64/65; skin270 is byte
identical. The separately signed465/CC63 recovery is preserved unchanged.
The new recovery restores the exact464 engine and pre-correction functional
sources with higher version metadata. Both CC packages authenticate79 files,
including the already-present helper (inactive with the old inventory in
recovery), so no stale-source deletion is required.

The next gates are original module signatures, selected real-Java installer
upgrade/refusal/recovery cases, exact APK/component preservation, original-key
QA APK signing, then the selected Android Search/Trakt/install-over/recovery
checks in ANDROID-REQUEST.json. Runtime verification needs that signed QA
installer; object/link success cannot substitute for it. Verify the remaining
Fold identities before installation and perform one final owner acceptance.
No final installer, completed production repair, or Fold acceptance is claimed.

Cobra, layouts/themes, native provider search implementations, unrelated
providers, Continue Playing, Resume Hub, playback, user settings/databases,
account data, signing implementation and existing recovery are unchanged.
Watchlist-to-Progress tracking remains deferred. No shutdown test was selected.

## Signed pair and selected Android gate

Original-key signatures and full source/component preservation PASS for candidate466
(run42462319257) and forward recovery467 (run42463180613). SIGNED-PAIR.json
pins their exact APK hashes. The unchanged original module signer produced both
complete79-file manifests;10 unchanged Java installer transition/refusal/recovery
cases PASS in preparation run42460784588. No native rebuild is required.

First selected Android run42464385488 FAIL before any correction cases: the
retained start_qa transport requested a playback fixture absent from the selected
Search/Trakt-only profile. The observer is registered in Kodi; its missing clip
is unrelated. The narrowly scoped transport override admits only the existing
script observer, preserving original live GUI-list reads, APKs and every assertion.
The failed report is retained in evidence/ANDROID-FIRST-ATTEMPT-FAIL.json.
Retry only the still-missing selected Android journey with the exact signed pair.
No Android functionality PASS or Fold acceptance is claimed.
