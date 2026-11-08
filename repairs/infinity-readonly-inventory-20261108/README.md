# Infinity Read-only Identity Report 1.0.0

Standalone Kodi script add-on: `script.infinity.readonlyinventory`.
This is a diagnostic, not an Infinity repair installer. It has no service,
third-party Python dependency, update mechanism or APK build/signing step.

Install its ZIP using Kodi's existing **Add-ons → Install from zip file**,
then open **Program add-ons → Infinity Read-only Identity Report**. A new,
uniquely named `Infinity-Installed-Identity-….json` is saved in Downloads.
If Android denies Downloads, choose an already accessible folder or cancel.
No ADB, root, wireless debugging, permission change or bypass is used.

It attempts to stream-hash the original APK path exposed by Infinity's existing
native Android engine as `KODI_ANDROID_APK`. It reads actual package/version
fields from that APK's binary manifest. Unavailable APK access is recorded as a
limitation, with no fabricated or substituted APK hash. A complete APK hash
matching a previously original-key-verified reference is identified by byte
identity; this collector does not run a new APK signature verifier.

It collects the **active** CC signed manifest/signature and hashes all declared
known first-party source paths across the four owned roots. Unknown paths are
refused. Raw manifest/signature bytes are included for original-public-key
verification on the host. An exact known reference pair is identified by byte
comparison, without claiming new on-device cryptographic verification.

It obtains the **active** Trakt version/path from Kodi and hashes the145 known
source-only files. Unknown extra filenames are reported without reading their
contents. Source, account settings, credentials, tokens, databases and other
installed add-ons are never opened for writing. Databases and saved account
settings are not read. Source code is hashed, not executed or exported.

Only the new JSON report is written by the diagnostic. Installing this separate
add-on uses Kodi's normal add-on registration. It does not modify Command Center,
Trakt, providers, Health Center, skin, user settings or any Infinity/Cobra feature.
Health Center integration remains deferred for separate review.

The report is a per-file read snapshot, not an atomic device attestation or
installation clearance. Auto-update is unchanged. The three-correction release,
Search timeout investigation and final Galaxy Fold acceptance remain separate.

The complete installable diagnostic ZIP and its checksum are in dist/. The
ZIP contains only this separate diagnostic script and identity-reference data.
