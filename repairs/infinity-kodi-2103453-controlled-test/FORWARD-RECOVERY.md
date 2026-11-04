# Forward recovery from testing 2103453

Do not install 2103452 or 2103451 over 2103453: Android normally rejects the lower
versionCode. Do not use downgrade flags, uninstall, clear data or reset profiles.

Before 453 is signed, preparation builds an unsigned recovery rehearsal at
2103454 from the exact signed 452 payload, checks every member, original package
identity and unchanged data schemas, and exercises the existing authority's
forward version/owner/protected-contract checks. Only manifest versionCode and
truthful last-updated metadata differ from 452. This rehearsed APK is deleted
after its hashes and comparison are recorded. It is not signed or installable.

If 453 fails, stop testing and preserve diagnostics, the installed version,
native hash, session identity and timestamps. If Kodi reports pending saving,
CHECKPOINT_FAILED or unknown durability ownership, do not force-close or install
an update over that unresolved session. Capture evidence and seek targeted
recovery guidance; replacing an APK cannot rescue unsaved in-memory data.

After an ordinary, verified durable close is possible, request a **forward
recovery build restoring the exact 2103452 payload**. Use the next unused version
higher than the installed/highest issued version (2103454 was rehearsed, not
reserved). Reuse the original 452 engine, without compilation. Repackage the two
changed owner bundles with advanced component revisions and truthful metadata;
all DEX, resources, providers and settings schemas remain unchanged. Run the same
official preparation, source/owner/payload, exact-member, signing and alignment
gates, using the original permanent certificate and com.projectinfinity.kodi.
The original signer must recheck the current authority and version before signing.

Compare the recovery APK to signed 452: every nonsignature member except the two
version metadata members must match. Compare it to 453: only the approved engine
reversal and metadata may differ. Verify certificate and higher version before
the user installs it as a normal update. Android's same-package/same-signer
update retains the app sandbox; no migration or reset is part of this procedure.
After installation, verify retained profiles, watched history and resume state.

**Verification limit:** the package restoration and authority transition are
rehearsed; physical Android installation/recovery is not tested. No signed recovery
APK is delivered now. Future recovery signing requires explicit authorization and
available original-key infrastructure. The currently delivered signed 453 proves
that signing route works at delivery time, not that future service availability
or unsaved in-memory data recovery is guaranteed. If a future gate fails, stop.

The 451 locked recovery APK/source and signed 452 remain unchanged and available.
This restores the pre-453 testing payload; it does not promote 452 to an accepted
baseline or claim its unrelated memory/loading problems are solved.
