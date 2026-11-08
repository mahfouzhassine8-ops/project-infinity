from xbmcgui import Dialog
from jurialmunkey.window import get_property
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.files.locker import mutexlock
from tmdbhelper.lib.files.futils import json_loads as data_loads
from tmdbhelper.lib.files.futils import json_dumps as data_dumps
from tmdbhelper.lib.addon.plugin import KeyGetter
from tmdbhelper_sync_trakt.api.recovery import TraktAuthorizationResult, TraktTokenRecovery
from tmdbhelper_sync_trakt.localization import get_localized
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.tmdate import get_timestamp, set_timestamp


class TraktStoredAccessToken:
    mutex_lockname = 'TraktCheckingAuthorization'
    expiry_margin = 30
    cooldown_seconds = 300

    def __init__(self, trakt_api):
        self.trakt_api = trakt_api

    @cached_property
    def stored_authorization(self):
        return self.winprop_traktusertoken or self.get_stored_authorization()

    def get_stored_authorization(self):
        try:
            return data_loads(self.trakt_api.user_token.value) or {}
        except ValueError as exc:
            kodi_log(f'Unable to read Trakt authorization: {exc}', 1)
            return {}

    def reload_authorization(self, from_settings=False):
        self.stored_authorization = (
            self.get_stored_authorization() if from_settings else
            self.winprop_traktusertoken or self.get_stored_authorization())
        if from_settings:
            self.winprop_traktusertoken = data_dumps(self.stored_authorization)

    def get_key(self, key):
        return KeyGetter(self.stored_authorization).get_key(key)

    @property
    def access_token(self):
        return self.get_key('access_token')

    @property
    def refresh_token(self):
        return self.get_key('refresh_token')

    @property
    def expires_in(self):
        return self.get_key('expires_in')

    @property
    def created_at(self):
        return self.get_key('created_at')

    @property
    def expires_in_timestamp(self):
        return (self.created_at or 0) + (self.expires_in or 0)

    @property
    def has_valid_token(self):
        return bool(self.access_token and get_timestamp(self.expires_in_timestamp - self.expiry_margin))

    @property
    def refresh_cooldown_active(self):
        return get_timestamp(get_property('TraktRefreshTimeStamp', is_type=float) or 0)

    @property
    def authorization(self):
        return self.get_authorization()

    def get_authorization(self):
        self.reload_authorization()
        if self.refresh_cooldown_active:
            return
        if self.has_valid_token:
            get_property('TraktIsAuth', set_property=f'{self.expires_in_timestamp}')
            return self.stored_authorization
        if self.access_token or self.refresh_token or self.trakt_api.authenticator.login_if_required:
            return self.recover()

    def recover(self, rejected_token=None, allow_login=False, force_login=False):
        self.reload_authorization()
        result = self.get_refreshed_token(
            rejected_token=rejected_token,
            allow_login=allow_login or self.trakt_api.authenticator.login_if_required,
            force_login=force_login,
            previous_token=self.access_token)
        if result is None:  # Mutex timeout or Kodi shutdown.
            return
        if result.logged_in:
            self.trakt_api.authenticator.configure_provider()
        if result.failed:
            self.trakt_api.authenticator.notify_failure()
        return result.authorization

    def on_failure(self, reason):
        kodi_log(f'Trakt authentication failed: {reason}. Suppressing retries for {self.cooldown_seconds}s.', 1)
        get_property('TraktRefreshTimeStamp', set_timestamp(self.cooldown_seconds))
        get_property('TraktIsAuth', clear_property=True)
        return TraktAuthorizationResult(failed=True)

    def on_success(self):
        # Refresh tokens are single-use: persist their replacement before any further request.
        self.update_stored_authorization()
        self.update_traktisauth_property()
        kodi_log('Trakt authentication token refreshed.', 1)
        return TraktAuthorizationResult(self.stored_authorization)

    def update_traktisauth_property(self):
        get_property('TraktIsAuth', set_property=f'{self.expires_in_timestamp}')
        get_property('TraktRefreshAttempts', clear_property=True)
        get_property('TraktRefreshTimeStamp', clear_property=True)

    def update_stored_authorization(self):
        self.trakt_api.user_token.value = self.winprop_traktusertoken = data_dumps(self.stored_authorization)

    def delete_stored_authorization(self):
        self.stored_authorization = {}
        self.trakt_api.user_token.value = self.winprop_traktusertoken = ''
        get_property('TraktIsAuth', clear_property=True)
        get_property('TraktUserToken', clear_property=True)
        get_property('TraktRefreshAttempts', clear_property=True)
        get_property('TraktRefreshTimeStamp', clear_property=True)

    @property
    def winprop_traktusertoken(self):
        return data_loads(get_property('TraktUserToken')) or {}

    @winprop_traktusertoken.setter
    def winprop_traktusertoken(self, value):
        get_property('TraktUserToken', f'{value}')

    def refresh_authorization_token(self):
        response = self.trakt_api.set_authorisation_token(self.refresh_token)
        if response is None:
            return self.on_failure('no response from token endpoint')
        try:
            if response.status_code == 200:
                self.stored_authorization = response.json()
                return self.on_success()
            if response.status_code == 400 and response.json().get('error') == 'invalid_grant':
                return  # Only a definitive credential rejection permits interactive reauthorization.
            return self.on_failure(f'token endpoint HTTP {response.status_code}')
        except ValueError:
            return self.on_failure('invalid JSON from token endpoint')
        finally:
            response.close()

    @mutexlock
    def get_refreshed_token(
            self, rejected_token=None, allow_login=False, force_login=False, previous_token=None):
        return TraktTokenRecovery(
            self,
            rejected_token=rejected_token,
            allow_login=allow_login,
            force_login=force_login,
            previous_token=previous_token
        ).get_result()

    def reject_authorization(self, rejected_token):
        result = self.reject_authorization_locked(rejected_token)
        if result is not None and result.failed:
            self.trakt_api.authenticator.notify_failure()

    @mutexlock
    def reject_authorization_locked(self, rejected_token):
        self.reload_authorization(from_settings=True)
        if self.access_token != rejected_token or self.refresh_cooldown_active:
            return TraktAuthorizationResult()
        return self.on_failure('request remained unauthorized after recovery')

    @mutexlock
    def revoke_authorization(self):
        self.reload_authorization(from_settings=True)
        response = self.trakt_api.del_authorisation_token(self.access_token) if self.access_token else None
        self.delete_stored_authorization()
        return (response,)

    def logout(self):
        result = self.revoke_authorization()
        if result is None:
            return False
        response, = result
        text = (
            get_localized(32108)
            if response is None else
            get_localized(32109)
            if response.status_code != 200 else
            get_localized(32110)
        )
        if response is not None:
            response.close()
        Dialog().ok(get_localized(32106), text)
        return True
