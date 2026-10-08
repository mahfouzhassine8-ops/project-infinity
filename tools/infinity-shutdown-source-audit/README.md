# Infinity installed source audit

Read-only add-on source collector needed to resolve the installed-owner coverage
gap in `repairs/android-checkpoint-shutdown/runtime-tests/INSTALLED_OWNER_COVERAGE.md`.
It does not certify persistence or enable the new shutdown route.

Install the ZIP through Kodi's **Add-ons → Install from zip file**, then run
**Infinity Installed Source Audit** from Program add-ons. Select a writable
folder and upload the resulting **Infinity-Installed-Addon-Code-*.zip**.

The tool resolves installed paths through Kodi, parses manifests without running
other add-ons, and exports code plus SHA-256 hashes and dependency declarations.
It excludes profiles, add-on data, account settings, databases, logs and symlink
targets. Opaque binary/compiled code is recorded by hash instead of copied.
Errors, unresolved paths and source changes are recorded rather than certified.
It performs no network requests or changes to other add-on code/settings.

The archive contains installed source, so share it in the private audit workflow.
Source review and runtime contracts remain necessary after collection.
