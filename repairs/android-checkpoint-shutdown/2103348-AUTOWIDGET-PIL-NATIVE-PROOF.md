# 2103348 AutoWidget / Pillow native-writer proof

Parent source: green 2103347 commit `1cebcde69ee01a4bbf0ff92a0c7151ce07dea7ab`.

The 2103347 Fold diagnostic failed closed with
`python_writer:unclassified_addon_native_extension` attributed to
`plugin.program.autowidget:service.py`. AutoWidget's service imports its common
utilities, which import Pillow. The exact 2103347 APK ships Pillow 5.1.0 wrappers
that load `PIL._imaging*` from `KODI_ANDROID_LIBS`.

2103348 does **not** exempt AutoWidget and does not allow arbitrary native
extensions. The persistence audit accepts only the five exact `PIL.*`
module/library pairs under the APK-owned native-library directory. Packaging
pins the SHA-256 of those five signed images. Wrong module, wrong path, changed
image, user library, ctypes call, SQLite extension, or any other add-on `.so`
remains fail-closed.

Rejected native imports now record `module=<name>;path=<file>`. Health Center
prints the Python failure writer, writer id, failure detail and writer/path
counts directly in report.txt.

The earlier separate `file_open_bypassed_checked_buffer_observer` failure
remains intentionally strict. The supplied diagnostic preserved no previous
failure-detail/path for that session, so this candidate does not weaken raw-file
protection based on a guess. If it recurs, the enhanced report will expose the
exact path/stack for a surgical follow-up.

No skin, provider, Command Center, Resume Hub, Cobra, user data, permanent
signer, or Force Close behavior is changed by this pass. This is a test
candidate, not a lock.
