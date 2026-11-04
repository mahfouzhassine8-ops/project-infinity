"""On-demand Kodi navigation only; no service, player or persistent state."""
import json
import os
import sys
from urllib.parse import urlsplit


def rpc(xbmc, method, params):
    try:
        value = json.loads(xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))
        return value.get('result') if 'error' not in value else None
    except (TypeError, ValueError, RuntimeError):
        return None


def activate(xbmc, gui, path):
    # JSON-RPC passes a vector of window parameters; folder names never become
    # executable builtin text. Kodi retains its own directory/player history.
    result = rpc(xbmc, 'GUI.ActivateWindow',
                 {'window': 'videos', 'parameters': [path, 'return']})
    if result != 'OK':
        gui.Dialog().ok('Infinity', 'Kodi could not open this location. '
                        'Your files and media sources have not been changed.')
        return False
    return True  # Request accepted, not a claim of completed directory loading.


def browse(xbmc, gui):
    # Native picker includes configured video sources plus Android-authorized
    # local drives. It does not add a source, scan a library or play a second engine.
    folder = gui.Dialog().browseSingle(0, 'Browse Files', 'video')
    return activate(xbmc, gui, folder) if folder else False


def run(action, xbmc, gui, environ=None):
    if action == 'browse':
        return browse(xbmc, gui)
    if action == 'sports':
        home = gui.Window(10000)
        path = home.getProperty('Infinity.Playlist.SportsPath')
        try:
            parsed = urlsplit(path)
        except ValueError:
            parsed = None
        if (xbmc.getCondVisibility('System.AddonIsEnabled(plugin.video.playlistbrowser)')
                and home.getProperty('Infinity.Playlist.Ready') == 'v1'
                and parsed is not None and parsed.scheme == 'plugin'
                and parsed.netloc == 'plugin.video.playlistbrowser'):
            return activate(xbmc, gui, path)
        gui.Dialog().ok('Infinity Sports',
                        'An existing Sports destination is not available. '
                        'Configure Sports through your existing Home integration, '
                        'then try again. No other provider has been substituted.')
        return False
    if action == 'downloads':
        if not xbmc.getCondVisibility('System.Platform.Android'):
            gui.Dialog().ok('Downloads', 'Choose the Downloads folder accessible to Kodi.')
            return browse(xbmc, gui)
        env = os.environ if environ is None else environ
        # /storage/self/primary follows the current Android user. Neither path
        # grants access or bypasses Android's storage permissions.
        storage = env.get('EXTERNAL_STORAGE') or '/storage/self/primary'
        if not storage.startswith('/') or '\x00' in storage:
            storage = '/storage/self/primary'
        path = storage.rstrip('/') + '/Download/'
        result = rpc(xbmc, 'Files.GetDirectory', {
            'directory': path, 'media': 'video', 'limits': {'start': 0, 'end': 1}})
        # Empty is a completed, accessible directory. Errors are not empty lists.
        if isinstance(result, dict) and ('files' in result or 'limits' in result):
            return activate(xbmc, gui, path)
        if gui.Dialog().yesno('Downloads access',
                'Kodi cannot read this Downloads folder. Check Infinity’s existing '
                'video/file permission in Android App settings, or choose an already '
                'accessible folder. No additional storage permission is requested.',
                nolabel='Cancel', yeslabel='Browse Files'):
            return browse(xbmc, gui)
        return False
    return False


if __name__ == '__main__':
    import xbmc
    import xbmcgui
    run(sys.argv[1] if len(sys.argv) > 1 else '', xbmc, xbmcgui)
