# Skin 207 verified cleanup → isolated 208 candidate

Exact parent: `skin.infinity.diggz` 1.0.5.207, SHA-256
`fdf7ea2b6e4409735f19718b0e16bf2c965a596f2578cd5f513d564985559ad0`.
Authenticated source-lock commit: `46ff3dbb76216b5e12f8a884e8cf0e6457efaea9`;
all 15 source-delta files match the package. The lock is scoped to an isolated
UI source candidate and does not claim physical Fold or combined acceptance.

The original .207 delivery specifies .204 as its rollback, independently verified
as SHA-256 `4238c9eaf341d921b319fd421bae5c47e3ed51925bed63033a558ae898787b47`.
The immediate rollback **from this new .208 candidate is the preserved .207 ZIP**.

Only `desktop.ini` is excluded. `addon.xml` changes only the version to 1.0.5.208.
Every other payload and its compressed bytes must remain identical. All XML is
parsed and the dependency manifest remains unchanged. The previous 11 UI checks,
16 profiles and 960 bounds checks are retained in a separately adapted validator;
the old no-removals assertion becomes an exact desktop.ini-only assertion.
The original .207 validator remains untouched; see validator-adaptation.patch.

The retired Kodi Live TV investigation found current conditional skin launch
routes to `script.infinity.live`, whose APK version 0.1.0 owns source settings,
favorites, last-channel state, EPG and Kodi playback. Historical 0.1.12/0.1.13
packages are reference material, not proven currently installed replacements.
The bundled `resources/lib/__init__.py` imports `install_multiview_hooks` and
`install_focus_contracts` under the Kodi guard, then patches the Live window's
construction and callbacks. Those modules are indirectly reachable. The old
`infinity-multiview` URI has no literal handler in the exact Android templates;
endpoint compatibility remains unresolved, not a reason to delete the callback.
No wholesale add-on, Live TV route or native PVR removal is authorized by this
evidence. The native PVR paths remain required by explicitly protected features.

Run package_candidate.py with the exact parent and rollback ZIPs, then run
validate_candidate.py against the .204 comparison base and generated .208 ZIP.
These are source/package/geometry checks, not physical-device acceptance.
No production promotion or baseline replacement is performed.
