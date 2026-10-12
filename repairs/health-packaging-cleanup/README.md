# Health Center 2.5.20 — isolated packaging-only cleanup

Exact input SHA-256: `24cef2a75ac8e2bb853540bb75db30dbdc714f1c1a84e10fa3fe7919d201317f`.
Input: `Infinity-Health-Center-2.5.20-Complete-Repair-RC1.zip`.

Remove only the installable package's `tests/test_native_incident_correlation.py`.
Retain and execute the identical host test from the original source/evidence bundle.
Update only `KHC_RELEASE.json` to reflect the package inventory and parent checksum.
All 67 other entries, including addon.xml, runtime Python, services, settings,
assets and their compressed bytes, remain identical. The version stays 2.5.20;
this is a manually selected ZIP packaging revision, not an automatic runtime update.

The current 82 host tests pass with zero failures/errors/skips, including the
retained native incident test. The builder requires that complete result and
checks the retained host test against the original package bytes. It separately
proves candidate membership, manifest hashes, XML/Python syntax and preservation.

The original package and source bundle are retained. No health data, user profiles,
diagnostics, recorder, shutdown owner or dependency is deleted or changed.
The exact original 2.5.20 ZIP is the rollback. No physical installation, production
promotion or user acceptance is claimed.
