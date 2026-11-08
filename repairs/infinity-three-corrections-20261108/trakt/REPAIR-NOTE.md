# Exact Trakt failure dialog and presentation-only correction

The owner's exact title and message match the following pinned upstream source:

- Component: `script.module.tmdbhelper.sync.trakt`, reference version **1.2.8**.
- Repository: `jurialmunkey/script.module.tmdbhelper.sync.trakt`.
- Source commit: `fff6d9b38820d2e64e0b00cb2b469c72ff3fbe2b`.
- `resources/language/resource.language.en_gb/strings.po`: title32103 and message32111.
- `resources/lib/tmdbhelper_sync_trakt/api/authenticator.py`:
  `TraktAuthenticator.notify_failure()` calls `Dialog().ok()` with those IDs.

[Pinned dialog call](https://github.com/jurialmunkey/script.module.tmdbhelper.sync.trakt/blob/fff6d9b38820d2e64e0b00cb2b469c72ff3fbe2b/resources/lib/tmdbhelper_sync_trakt/api/authenticator.py#L141)
and [exact text](https://github.com/jurialmunkey/script.module.tmdbhelper.sync.trakt/blob/fff6d9b38820d2e64e0b00cb2b469c72ff3fbe2b/resources/language/resource.language.en_gb/strings.po#L122).

This identifies the matching producer implementation. The installed Fold's copy,
version and source hashes have not yet been captured. Do not replace or upgrade
the installed module blindly with this public reference version.

## Automatic failure path

`TraktAPI.access_token` -> `TraktAuthenticator.access_token` ->
`TraktStoredAccessToken.get_authorization()` -> `recover()` ->
`get_refreshed_token()` / `TraktTokenRecovery` -> failure result ->
`TraktAuthenticator.notify_failure()`.

`TraktStoredAccessToken.on_failure(reason)` first logs the failure, sets
`TraktRefreshTimeStamp` with `set_timestamp(300)`, clears `TraktIsAuth`, and returns
`TraktAuthorizationResult(failed=True)`. The notification runs after the locked
recovery method has returned. A second API401 after recovery has a separate
`reject_authorization()` path with the same log/cooldown operation and notification.

Neither original notification call checks Infinity Silent Mode. That explains
why the existing KaiToast-only silent gate cannot suppress this modal dialog.
The exact Home widget or background request that triggered the owner's instance
still needs runtime evidence; no specific widget is assumed by this correction.

## Manual path and minimal patch

The account settings action runs `action=authenticate` ->
`TraktAccountActions.authenticate()` -> `TraktAPI.login()` ->
`TraktAuthenticator.login()` -> `recover(allow_login=True, force_login=True)`.
Existing recovery deliberately bypasses the automatic cooldown for this forced
manual sign-in. Its device-code dialogs and polling remain unchanged.

Only two source files are modified:

1. `authenticator.py`: `notify_failure(manual=False)` checks
   `getSkinDir() == 'skin.infinity.diggz'` and
   `Skin.HasSetting(Infinity.SilentMode)` only for automatic failures. It returns
   before the original `Dialog().ok()` when both are true. Manual calls bypass
   the setting query entirely. Query errors retain the original dialog.
2. `token.py`: the failure notification in `recover()` forwards the existing
   `force_login` flag as `manual=force_login`. The second401 rejection remains
   an automatic notification and uses the default argument.

No global dialog hook, title/text filter, new mutex, authentication retry change,
setting write, token-store change, or Watchlist/playback operation is introduced.
The original logging, timestamp setter, 300-second value, failure result and
recovery policy are byte-identical. Every manual prompt method is unchanged.
Other skins retain the existing dialog, including Cobra.

## Verification

**13 focused local host tests PASS.** They use the pinned real authenticator,
token and recovery methods with synthetic SDK/HTTP/clock boundaries. They cover:

- Exact title/message lookup and reproduction of the original Silent Mode bug.
- Automatic Silent Mode ON suppression with unchanged logging and timestamp.
- Cooldown refusal before300 seconds and retry at expiry.
- Silent Mode OFF, non-Infinity skins and failed setting-query behavior.
- Manual sign-in during active cooldown with the original failure dialog.
- Second401 rejection, stale401 refusal and no-result recovery.
- Successful refresh/token rotation compared with the original implementation.
- Exact source-function preservation outside the two intended edits.

A separate complete-source patch audit PASS checked all146 files in the pinned
upstream tree: exactly2 modified,144 byte-identical, no additions or deletions.
The reference archive's Git blob identities were checked against its pinned tree.
`SOURCE-PINS.json` records the source and changed-file hashes. Reference source
and derived changes retain the upstream GPL-3.0-or-later license in
`reference/LICENSE.txt`.

No real Trakt account, token store, network, Kodi app, device, build or signer was
used by these tests. The synthetic token values are test fixtures only. These
results do not claim an installed Fold repair or production release acceptance.

## Outstanding gates

The read-only `read_device_inventory.py` now collects this module's addon.xml
and hashes of the relevant source, settings-definition and localization files.
It never reads the user's authentication settings or databases. Compare that
report with the pinned baseline before deciding whether this patch applies; a
different version/source requires a review against that actual input, not a
forced overwrite.

After installed-source identity is established, actual Android/Fold verification
must check automatic failure with Silent Mode ON/OFF, retained cooldown/error
recording, and manual sign-in. The existing provider compatibility and native
Search gates remain separate. No build or signing is authorized by this note;
the user's explicit hold remains in force.
