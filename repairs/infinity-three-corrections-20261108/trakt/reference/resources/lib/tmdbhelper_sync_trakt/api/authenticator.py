from xbmcgui import Dialog, DialogProgress, DLG_YESNO_YES_BTN
from jurialmunkey.parser import boolean
from jurialmunkey.window import get_property
from jurialmunkey.ftools import cached_property
from tmdbhelper_sync_trakt.api.token import TraktStoredAccessToken
from tmdbhelper.lib.addon.plugin import get_localized as get_kodi_localized, KeyGetter
from tmdbhelper_sync_trakt.localization import get_localized
from tmdbhelper.lib.addon.logger import kodi_log


class TraktAuthenticator:

    state = None
    progress = 0
    interval_default = 5

    def __init__(self, trakt_api):
        self.trakt_api = trakt_api
        self.login_if_required = trakt_api.login_if_required

    def get_key(self, dictionary, key):
        return KeyGetter(dictionary).get_key(key)

    @property
    def attempted_login(self):
        return boolean(get_property('TraktAttemptedLogin'))

    @attempted_login.setter
    def attempted_login(self, value):
        get_property('TraktAttemptedLogin', f'{value}')

    @property
    def authorization(self):
        return self.trakt_stored_access_token.authorization

    @property
    def trakt_stored_access_token(self):
        # A token snapshot belongs to one operation, including across threads sharing this client.
        return TraktStoredAccessToken(self.trakt_api)

    @property
    def access_token(self):
        return self.get_key(self.authorization, 'access_token')

    @property
    def is_authorized(self):
        return bool(self.access_token)

    def authorize(self, forced=False):
        self.login_if_required = self.login_if_required or forced
        return self.is_authorized

    @cached_property
    def dialog_noapikey_header(self):
        return f'{get_localized(32100)} {self.trakt_api.req_api_name} {get_localized(32101)}'

    @cached_property
    def dialog_noapikey_text(self):
        return get_localized(32102)

    @cached_property
    def code(self):
        return self.trakt_api.get_device_code()

    @cached_property
    def user_code(self):
        return self.get_key(self.code, 'user_code')

    @cached_property
    def device_code(self):
        return self.get_key(self.code, 'device_code')

    @cached_property
    def verification_url(self):
        return self.get_key(self.code, 'verification_url')

    @cached_property
    def expires_in(self):
        return self.get_key(self.code, 'expires_in') or 0

    @cached_property
    def interval(self):
        return self.get_key(self.code, 'interval') or self.interval_default

    @cached_property
    def auth_dialog_head(self):
        return get_localized(32103)

    @cached_property
    def auth_dialog_text(self):
        return f'{get_localized(32104).format(self.verification_url)}\n{get_localized(32105)}: [B]{self.user_code}[/B]'

    @cached_property
    def auth_dialog(self):
        auth_dialog = DialogProgress()
        auth_dialog.create(self.auth_dialog_head, self.auth_dialog_text)
        return auth_dialog

    @property
    def auth_dialog_route(self):
        auth_dialog_route = {
            'aborted': self.on_aborted,
            'expired': self.on_expired,
        }
        return auth_dialog_route[self.state]

    @property
    def auth_dialog_progress(self):
        return int((self.progress * 100) / self.expires_in)

    def auth_dialog_update(self):
        self.progress += self.interval
        self.auth_dialog.update(self.auth_dialog_progress)

    @cached_property
    def xbmc_monitor(self):
        from xbmc import Monitor
        return Monitor()

    def on_expired(self):
        """Triggered when the device authentication code has expired"""
        kodi_log(u'Trakt authentication expired!', 1)

    def on_aborted(self):
        """Triggered when device authentication was aborted"""
        kodi_log(u'Trakt authentication aborted!', 1)

    def on_success(self, authorization):
        """Triggered when device authentication has been completed"""
        kodi_log(u'Trakt authenticated successfully!', 1)
        token = self.trakt_stored_access_token
        token.stored_authorization = authorization
        token.update_stored_authorization()
        token.update_traktisauth_property()
        self.attempted_login = False

    def configure_provider(self):
        from tmdbhelper.lib.script.sync.provider_setup import SyncProviderOnboarding
        SyncProviderOnboarding('script.module.tmdbhelper.sync.trakt').configure()

    def notify_failure(self):
        Dialog().ok(get_localized(32103), get_localized(32111))

    def poller(self):
        authorization = None
        while True:

            if self.xbmc_monitor.abortRequested():
                self.state = 'aborted'
                break

            if self.auth_dialog.iscanceled():
                self.state = 'aborted'
                break

            self.auth_dialog_update()

            if self.expires_in <= self.progress:
                self.state = 'expired'
                break

            authorization = self.trakt_api.get_authorisation_token(self.device_code)

            if authorization:
                self.state = 'success'
                break

            self.xbmc_monitor.waitForAbort(self.interval)

        self.auth_dialog.close()
        if self.state == 'success':
            self.on_success(authorization)
            return authorization
        self.auth_dialog_route()

    def ask_to_login(self):
        # Called only by the owner of the shared authorization recovery lock.
        if self.attempted_login:
            return

        x = Dialog().yesnocustom(
            self.dialog_noapikey_header,
            self.dialog_noapikey_text,
            nolabel=get_kodi_localized(222),
            yeslabel=get_kodi_localized(186),
            customlabel=get_kodi_localized(13170),
            defaultbutton=DLG_YESNO_YES_BTN
        )
        if x == 1:
            return self.login_device()
        if x == 2:
            self.attempted_login = True

    def login(self):
        return self.trakt_stored_access_token.recover(allow_login=True, force_login=True)

    def get_login_authorization(self, prompt=True):
        # A fresh session must obtain new device codes after failure or cancellation.
        session = TraktAuthenticator(self.trakt_api)
        return session.ask_to_login() if prompt else session.login_device()

    def login_device(self):
        if not self.user_code or not self.device_code:
            return
        return self.poller()

    def logout(self, confirmation=True):
        if confirmation and not Dialog().yesno(get_localized(32106), get_localized(32107)):
            return
        if not self.trakt_stored_access_token.logout():
            return
        from tmdbhelper.lib.sync.providers.selection import SyncProviderSetting
        SyncProviderSetting.clear_provider('trakt')
        return True
