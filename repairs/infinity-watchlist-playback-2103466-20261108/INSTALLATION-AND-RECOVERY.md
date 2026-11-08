# Engineering installer instructions — release gates pending

Do not install or distribute unfinished preparation inputs. The final signed
APK pair and SHA-256 values must be filled from the verified signing artifacts
only after focused Android installation, actual playback and recovery pass.
Galaxy Fold acceptance remains separate from those engineering results.

The planned installer is combined Infinity2103468 / Cobra2103445 with Command
Center0.3.5.66. Its matching **forward** recovery is combined Infinity2103469 /
Cobra2103445 with Command Center0.3.5.67. Recovery restores the protected2103466
functional native/Python code while keeping a higher Android/add-on generation.
The authenticated helper remains inactive; no unknown files or user data are
deleted. The pre-existing2103467 recovery is preserved and is not this pair's
recovery. Neither original2103466 nor2103468 is a downgrade path after2103469.

Install the original-key candidate as an Android update over the confirmed2103466
installation. Verify the downloaded APK's SHA-256 against the final release
manifest. Do not uninstall Infinity, clear storage, overwrite add-ons manually,
change signing verification or force a downgrade. If the installed APK or
Command Center is newer than this release, stop and retain it. Android must
accept the original package identity/signature and the authenticated module
installer must admit the complete installed generation. An authentication or
unknown-source refusal is a real blocker, not permission to replace files.

One final Fold acceptance sequence uses the existing Watchlist interface:

1. Save a movie and a TV show through the existing Infinity Trakt menu. Confirm
   saving/browsing alone creates no progress.
2. Actually play the movie from Infinity Movies Watchlist, then stop after the
   existing normal progress threshold. Reopen it from Watchlist and check its
   real saved position and existing Infinity-only resume display.
3. Actually play an identified episode through Infinity TV Watchlist. Confirm
   partial progress appears under its correct show/season/episode and resumes
   accurately. Complete it normally and check existing watched semantics.
4. Next Episodes may advance only when the existing local catalogue verifies a
   successor. Provider-only completion retains accurate watched/progress data
   and safely withholds an unproved next episode; no episode-number guess occurs.
5. Confirm Watchlist saving/removal/navigation, regular Movies/TV playback,
   existing Search and Cobra retain their approved behavior. Report any actual
   launch, resume, duplicate/history, crash or navigation failure.

If recovery is needed, install only the matching original-key2103469 update over
2103468, retaining application storage and account/settings data. Do not use a
lower APK or CC ZIP. The final release report must supply tested recovery hashes
and preserve the Android upgrade/recovery and source-integrity receipts.

Coverage is deliberately exact-source scoped. Current reviewed Umbrella6.8.00
and POV6.11.02 producer pins must match at runtime; a changed provider generation
withholds only Watchlist enrichment while retaining its ordinary playback.
Folder popup navigation retains its approved baseline path; the new provenance
connection is exercised by direct Watchlist selection and playable-title Play.
No Search repair or authentication change is part of this feature release.
