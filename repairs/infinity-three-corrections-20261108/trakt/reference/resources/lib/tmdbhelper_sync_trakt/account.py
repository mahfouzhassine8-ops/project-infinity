from tmdbhelper.lib.script.method.sync import invalidate_sync


class TraktAccountActions:
    def __init__(self, provider):
        self.provider = provider

    def authenticate(self):
        self.provider.api.login()
        if self.provider.api.authenticator.is_authorized:
            self.invalidate()

    def revoke(self):
        if self.provider.api.logout():
            self.invalidate()

    @staticmethod
    def invalidate():
        invalidate_sync('all', notification=False, sync=False)
