# Infinity skin delivery correction: 1.0.5.195

The APK 2103304 delivery does not contain a skin update. The first separately
delivered skin ZIP had the incorrect `addons/skin.infinity.diggz/` archive root.
The corrected ZIP contained the existing seven XML repairs, but retained skin
version 1.0.5.194 and the same filename as the malformed ZIP. Kodi's local ZIP
installer can reuse an existing package-cache file with that filename. Device
logs are required to determine whether that happened; equal version alone does
not prove Kodi rejected or ignored the installation.

This candidate gives those same seven repaired XML files a distinct filename and
version, 1.0.5.195. It preserves the internal add-on ID, dependencies, unified
profile registration, all assets and every other code file. Only addon.xml and
the two current release/integrity metadata documents change beyond the existing
repair. Protected-file membership is retained; hashes are refreshed against
verified package bytes, including 12 entries already stale in baseline 194.
Historical release records remain historical. Baseline 194 is not overwritten.

Reproduce from this repository and the original locked ZIP:

```sh
python3 repairs/skin-delivery-1.0.5.195/package_skin.py \
  --baseline /path/to/Infinity-1.0.5.194-Mobile-Repair-RC4.zip \
  --output-dir /path/to/output
```

The packager checks the exact baseline SHA, applies the existing repair patch,
verifies all seven before/after hashes, runs the eight existing skin source
contracts, enforces exactly ten changed files, and reads every output ZIP member
back for equality. See package-proof.json for the resulting digest and counts.

Install the uniquely named ZIP through Kodi's Install from zip file using the
already delivered APK 2103304. Confirm Infinity's add-on information reports
1.0.5.195. Expected source changes include no More options drawer row and UI Theme
immediately above Power. A version-confirmed screenshot and Kodi log are needed
if the old drawer remains. Do not delete user data or reinstall the APK as a
substitute for verifying the active skin.

This is a packaging correction, not additional UI repair or device acceptance.
Umbrella source-window sizing/Back freeze, idle takeover and the rest of the
unverified repair brief remain open. No APK/native/signing changes are made;
the deferred movie-video framing files are byte-identical to baseline 194.
