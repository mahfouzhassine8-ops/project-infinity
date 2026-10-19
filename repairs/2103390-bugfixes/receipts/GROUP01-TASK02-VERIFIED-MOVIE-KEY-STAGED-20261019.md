# GROUP #1 / ORIGINAL TASK 02 — VERIFIED DUPLICATE MOVIE CONTINUE WATCHING GUARD

**STATUS:** REAL COMMAND CENTER SOURCE PROTOTYPE STAGED; TESTED **5/5 HOST GREEN**, **NOT PACKAGED/INSTALLED/FOLD-QUALIFIED**. Current installed Infinty data has NOT been read or changed. Group #1 is NOT complete.

## Confirmed defect from EXACT signed 2103390 source (fixture reproduced)

Source member `assets/addons/script.infinity.commandcenter/resume_hub.py`, preimage SHA-256 `7794e25ec63348d29f74c45948d81db3e2fa1ba780437c329277fcffb1888eff`:
- `hub.entries(data, media='movie', bucket='items')` indiscriminately renders all stored rows, even when two different existing 64-hex keys contain the exact same validated movie identity.
- `hub.compatible_key` when `len(canonical)>1` takes `identity_key(identity)` rather than an existing original movie's saved key. In fixture: initial duplicate keys `'a'*64` and `'b'*64` both represent precisely verified TMDb `123` and identical IMDb `tt0000012`; old display returns **two cards**, and replay returns a NEW calculated key `2a6503f72d3a3d21f765e28b39c08a94ce1119894e4bf03a4a5783e855a66d7b` instead of latest existing key `'b'*64`.
- This is a proven codepath deficiency in a synthetic fixture, **NOT yet proof that the user's Insidious rows have the same verified IDs**. No user-specific data was guessed or merged.

## Explicit minimal non-destructive fix

Saved source-only patch code `repairs/2103390-bugfixes/group1/movie_identity_patch.py`; GitHub blob SHA `916e1a225b7abbcb16013e599d92d6fbeef67af0`; source commit `6f3c22179f056f113f0ef282edc4747ab042c545`.
Saved real-source tests `repairs/2103390-bugfixes/group1/test_movie_identity_patch.py`; GitHub blob SHA `a032ec5035325db515d6664dba2b5e530aa15772`; test commit `570095ca27fd0cc5f246ba6a7c8d6cdca7e5101c`.

The exact-hash-guarded source patch modifies **ONLY**:
1. `compatible_key`: when multiple verified matching movie keys exist **in existing Continue Watching items**, all identities mutually agree and have no conflicting namespace IDs, reuse the **most recent** existing key instead of minting a new third key. TV and ambiguous identities preserve their original code paths.
2. `entries`: for the Continue Watching **movie** bucket only, project a single display card from an already-sorted group of records with a fully verified **pairwise consistent** identical movie identity token. Other records remain separate.

**Critical:** NO JSON/database changes by this patch itself, no existing duplicate data deleted, no watchlist or watched change, no history/position reset, no title-only or poster-only match. Actual later in-app progress writes still use original Command Center write/atomic/durability mechanisms and remain protected. Conflicting or partially verified IDs remain separate; user-specific outcome must be checked with their actual retained data before marking done.

## Real local tests against original APK-carried Command Center

- `python -m unittest -v test_movie_identity_patch`: **5/5 PASS**, 0.036 seconds.
- Fixture RED-before: 2 displayed cards; replay selected new computed key, not existing latest. Patched fixture GREEN: 1 display card; latest existing key reused; source data deep copy unchanged.
- Verified differing movie IDs but identical labels remain TWO rows.
- Verified conflicting TMDb/IMDb namespace pairs remain TWO rows.
- Unverified legacy same-title rows remain untouched and visible; TV episodes remain unaffected.
- Exact source-only byte replacement of two specific function tails verified; replay of patch on already-patched file fails closed.
- GitHub source/test blobs were fetched and compared to actual local tested code by `git hash-object`; exact match.
- Compiled patched Python source using `compile(...,'exec')`: **PASS**.
- Patched Python source SHA-256 `087860b6a551a23fdd8f7f11ab103b367f0ef44be32b5b42cadecf907e548784` (staged source, not a signed ZIP/APK).

## Still REQUIRED

- Validate actual Insidious records represent the same canonical verified movie, without copying/wiping user profile or assuming title art proves identity. If ambiguous, do NOT hide/merge or claim successful repair.
- Real installed Kodi Command Center update source, actual playback timestamp durability and watched/Watchlist/Collection independence tests, ordinary player provider path, full APK scope gate, physical Galaxy Fold proof.
- Other Group #1: episode source (01), horizontal scroll / vertical chooser (03), status orb (04) Fold verification, category switch repeated loading (19).
- Standalone TMDb/SlyGuy quarantine task17 and CU LRC Lyrics task16: **SKIPPED_BY_USER**; no code/add-ons modified. COBRA absolutely untouched, original shutdown/Essential-First unchanged.

**USER-REQUIRED SAVEPOINT**: user asked to save every tested task and completed group for future chat. This is the immutable separate receipt; master status and continuation handoff must reference this and clock checkpoint before next group begins. No overall Group #1 green claimed.
