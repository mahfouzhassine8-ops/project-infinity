# Source export failure — read-only investigation

The owner reports Kodi Health Center2.5.26, Umbrella6.8.00, and:
`RuntimeError: Database has no readable SQLite header; raw fallback refused`.
No device file has been accessed or changed by this investigation.

## Located mechanism and limits

In the preserved authenticated APK source, `default.py::export_installed_addon`
walks every file in the selected add-on directory, excluding only bytecode and
`__pycache__`. The source-only selection excludes the separate profile/addon_data
directory; it does not restrict the add-on folder to Python/XML source files.
`khc_exports.export_entries` sends every collected file to
`khc_safety.snapshot_file`. That helper classifies `.db`, `.sqlite`, `.sqlite3`
extensions, or an actual SQLite header, as a database. An extension-classified
file without `SQLite format 3\0` raises the exact reported error before any
SQLite connection is opened. The exporter then discards its incomplete export
copies; its cleanup does not target the source file.

The error does not prove database corruption, encryption, or a Kodi library
failure. The source filename is omitted from this exception. It may be a
non-SQLite file with a database extension, an empty/incomplete file, or another
installed-file difference; no particular explanation is established on the Fold.

The independently pinned public Umbrella6.8.00 source at
`umbrellaplug/umbrellaplug.github.io`, commit
`e4f24004462d22757d375ebbea0bad26e9d983cc`, has no `.db`, `.sqlite`, or `.sqlite3`
file in its add-on root or complete resources subtree
`82375e40bdb61b51ec46286fc7f8d6bc45cf2eb0` (recursive Git tree, not truncated).
This cannot establish the contents of the installed Fold directory.

Important source distinction: the authenticated462 APK retained locally contains
Health Center2.5.27, whereas the owner reports installed2.5.26. Its exact matching
implementation is an identified reference, not an assertion that the installed
Health Center source has already been authenticated. The fallback collects only
addon.xml and the three relevant Health Center Python files to check that point.
No Health Center source change or database workaround is proposed.

## Selected checks — record before execution

Only these new local checks are selected:

1. Use the authenticated bundled `export_entries` and `snapshot_file` functions
   with a disposable fake add-on containing source and a non-SQLite `.db` file.
   Reproduce the exact exception with `includes_saved_data=False`; assert no
   SQLite connection, unchanged original fixture bytes, no completed export.
2. Exercise the existing inventory collector plus its optional source-copy
   output against a fake ADB transport. Assert only metadata commands and reads
   of explicitly named code/manifests; no database/profile file reads, recursive
   folder copy, install, launch, stop, permission change or device write. Test
   refusal of a database path in untrusted module metadata, source-copy output
   checksums, bounded reads and refusal to overwrite an existing local folder.

No Android application tests, native builds, signing, database validation,
repair, backup, shutdown checks, or prior passing suites are selected.

All five focused local cases PASS: exporter refusal/source preservation,
fixed-source collection, database-record refusal, oversized-source refusal,
and existing computer folder preservation. The SQLite connect mock was never
called. The fake ADB transport accepted no command that could write to the
phone, and the database fixture was never requested by the collector. These
are local results; neither the actual Fold nor its installed2.5.26 source was
tested. See evidence/HEALTH-EXPORT-INVESTIGATION.json.

## Safe fallback

From a computer with Python3.11+ and an already authorized ADB connection:

```sh
adb devices
python3 read_device_inventory.py --out INFINITY-INSTALLED-INVENTORY.json --sources-out INFINITY-SOURCE-INSPECTION
```

The optional `--sources-out` writes only the explicitly read code/manifests into
a new directory **on the computer**. It does not walk the add-on tree or read
the failing database. Included settings.xml is a shipped resource definition,
not the user's profile settings. Attach the JSON report and a ZIP of that local
folder for inspection; this is diagnostic source, not an installable add-on ZIP.
Unreadable standard paths are reported without rooting or changing permissions.
If ADB is unavailable or access is denied, installed-source verification remains
pending; do not bypass the database refusal or alter the Fold installation.

The original signed module manifest/signature and declared module source hashes
remain subject to original-key authentication after collection. These exports
alone do not clear installation or production behavior.
