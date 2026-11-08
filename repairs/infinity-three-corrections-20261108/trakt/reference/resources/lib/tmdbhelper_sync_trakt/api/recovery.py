class TraktAuthorizationResult:
    def __init__(self, authorization=None, logged_in=False, failed=False):
        self.authorization = authorization
        self.logged_in = logged_in
        self.failed = failed


class TraktTokenRecovery:
    def __init__(
            self, token, rejected_token=None, allow_login=False, force_login=False, previous_token=None):
        self.token = token
        self.rejected_token = rejected_token
        self.allow_login = allow_login
        self.force_login = force_login
        self.previous_token = previous_token

    @property
    def authenticator(self):
        return self.token.trakt_api.authenticator

    @property
    def comparison_token(self):
        return self.previous_token if self.force_login else self.rejected_token

    @property
    def token_changed(self):
        return self.token.access_token != self.comparison_token

    @property
    def cooldown_active(self):
        return bool(self.token.refresh_cooldown_active and not self.force_login)

    @property
    def can_reuse_token(self):
        return self.token.has_valid_token and self.token_changed

    @property
    def can_refresh_token(self):
        return bool(self.token.refresh_token and not self.force_login)

    def get_result(self):
        # Called under the token's mutex: re-read credentials replaced by another process.
        self.token.reload_authorization(from_settings=True)
        if self.cooldown_active:
            return TraktAuthorizationResult()
        if self.can_reuse_token:
            return TraktAuthorizationResult(self.token.stored_authorization)
        return self.refresh_or_login()

    def refresh_or_login(self):
        if self.can_refresh_token:
            result = self.token.refresh_authorization_token()
            if result is not None:
                return result
        return self.login()

    def login(self):
        if not self.allow_login:
            return self.token.on_failure('user reauthorization required')
        authorization = self.authenticator.get_login_authorization(prompt=not self.force_login)
        if not authorization:
            return self.token.on_failure('user authorization was not completed')
        self.token.reload_authorization()
        return TraktAuthorizationResult(self.token.stored_authorization, logged_in=True)
