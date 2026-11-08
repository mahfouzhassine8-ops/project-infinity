import sys
from os.path import join
from xbmc import executebuiltin
from xbmcaddon import Addon


def run(action=None, payload=None, **parameters):
    if action is None:
        executebuiltin(
            'RunScript(plugin.video.themoviedb.helper,configure_sync_provider,'
            'addon_id=script.module.tmdbhelper.sync.trakt)')
        return
    sys.path.insert(0, join(Addon('plugin.video.themoviedb.helper').getAddonInfo('path'), 'resources'))
    from tmdbhelper.lib.sync.providers.registry import SyncProviderRegistry
    provider = SyncProviderRegistry().find_provider('trakt')
    if provider is None:
        return
    if action in ('authenticate', 'revoke'):
        from tmdbhelper_sync_trakt.account import TraktAccountActions
        actions = TraktAccountActions(provider)
        return {'authenticate': actions.authenticate, 'revoke': actions.revoke}[action]()
    if payload is not None:
        from json import loads
        from urllib.parse import unquote
        parameters.update(loads(unquote(payload)))
    from tmdbhelper_sync_trakt.diagnostics import run_diagnostic
    return run_diagnostic(provider, action, **parameters)


if __name__ == '__main__':
    run(**dict(arg.split('=', 1) for arg in sys.argv[1:]))
