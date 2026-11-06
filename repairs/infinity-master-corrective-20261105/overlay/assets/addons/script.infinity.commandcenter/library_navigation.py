"""On-demand Kodi navigation only; no service, player or persistent state."""
import json
import os
import sys
import ast
from pathlib import Path
import xml.etree.ElementTree as ET


def rpc(xbmc, method, params):
    try:
        value = json.loads(xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))
        return value.get('result') if 'error' not in value else None
    except (TypeError, ValueError, RuntimeError):
        return None


def activate(xbmc, gui, path, direct_library=False, downloads_only=False):
    # JSON-RPC passes a vector of window parameters; folder names never become
    # executable builtin text. Kodi retains its own directory/player history.
    parameters = [path, 'return']
    if downloads_only:
        if path != 'files' or direct_library:
            return False
        parameters.append('infinity-downloads-only')
    if direct_library:
        if path not in ('videodb://movies/titles/', 'videodb://tvshows/titles/'):
            return False
        parameters.append('infinity-library-direct')
    result = rpc(xbmc, 'GUI.ActivateWindow',
                 {'window': 'videos', 'parameters': parameters})
    if result != 'OK':
        gui.Dialog().ok('Infinity', 'Kodi could not open this location. '
                        'Your files and media sources have not been changed.')
        return False
    return True  # Request accepted, not a claim of completed directory loading.


def browse(xbmc, gui):
    # VideoNav maps "files" to sources://video/. This is Kodi's existing
    # folder/video browser, not the shared dialog skinned for ZIP installation.
    # Playback, Back/history and source access remain owned by Kodi.
    return activate(xbmc, gui, 'files')


def _provider_tools():
    # Reuse authenticated first-party source/inventory checks. No provider
    # module is imported, executed, searched or modified by this helper.
    import xbmcaddon
    import xbmcvfs
    root = xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('path'))
    sys.path.insert(0, root)
    try:
        from provider_inventory import eligible
        from infinity_search import route
        from saved_navigation import _source
        return eligible, route, _source
    finally:
        sys.path.remove(root)


def _umbrella_menu(raw, action, method):
    """Verify the installed router's exact existing Navigator dispatch."""
    tree = ast.parse(raw)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'router']
    if len(functions) != 1:
        return False
    expected = ast.parse('navigator.Navigator().%s(folderName=folderName)' % method).body[0]
    for node in ast.walk(functions[0]):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name)
                and test.left.id == 'action' and len(test.ops) == len(test.comparators) == 1
                and isinstance(test.ops[0], ast.Eq) and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == action):
            continue
        if len(node.body) != 2 or not isinstance(node.body[0], ast.ImportFrom):
            return False
        imported = node.body[0]
        return (imported.module == 'resources.lib.menus' and imported.level == 0
                and len(imported.names) == 1 and imported.names[0].name == 'navigator'
                and imported.names[0].asname is None
                and ast.dump(node.body[1]) == ast.dump(expected))
    return False


def direct(action, xbmc, gui):
    try:
        eligible, route, source = _provider_tools()
        if action in ('movies', 'tv'):
            media = 'movie' if action == 'movies' else 'tv'
            ready, _ = eligible(media, operation='title_navigation', force=True,
                                provider_id='plugin.video.umbrella')
            if len(ready) != 1 or ready[0]['id'] != 'plugin.video.umbrella' or ready[0]['family'] != 'action-list-v1':
                raise ValueError('unverified provider')
            provider = ready[0]
            menu, method = ('movieNavigator', 'movies') if action == 'movies' else ('tvNavigator', 'tvshows')
            if not _umbrella_menu(source(Path(provider['root']), 'resources/lib/modules/router.py'), menu, method):
                raise ValueError('unverified menu')
            # Only params change; all installed source/dependency pins remain.
            operation = dict(provider, contract=dict(provider['contract'], params={'action': menu}))
            destination = route(operation)  # Recheck actual installed pins now.
        elif action == 'sports':
            identity = 'plugin.video.sporthdme'  # Reviewed SportHD publisher identity.
            details = rpc(xbmc, 'Addons.GetAddonDetails', {
                'addonid': identity, 'properties': ['name', 'version', 'path', 'enabled']})
            addon = details.get('addon') if isinstance(details, dict) else None
            if not (isinstance(addon, dict) and addon.get('addonid') == identity and addon.get('enabled') is True
                    and addon.get('name') == 'SportHD' and xbmc.getCondVisibility('System.AddonIsEnabled(' + identity + ')')):
                raise ValueError('unverified provider')
            import xbmcvfs
            root = Path(xbmcvfs.translatePath(addon['path'])).resolve()
            raw = source(root, 'addon.xml')
            text = raw.decode('utf-8-sig')
            if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
                raise ValueError('unsupported manifest')
            manifest = ET.fromstring(text)
            plugin = manifest.find('extension[@point="xbmc.python.pluginsource"]')
            if (manifest.get('id') != identity or manifest.get('name') != 'SportHD'
                    or manifest.get('version') != addon.get('version')
                    or manifest.get('provider-name') != 'Bugatsinho' or plugin is None
                    or plugin.get('library') != 'default.py'):
                raise ValueError('unverified entrypoint')
            source(root, 'default.py')  # Existing bounded/non-symlink source reader.
            destination = 'plugin://' + identity + '/'  # Provider-owned root only.
        else:
            return False
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, ImportError, SyntaxError, ET.ParseError):
        gui.Dialog().ok('Infinity navigation',
                        'The installed destination or its entrypoint could not be verified. '
                        'Check the existing Umbrella or SportHD add-on. No other provider was opened.')
        return False
    return activate(xbmc, gui, destination)


def run(action, xbmc, gui, environ=None):
    if action in ('library-movies', 'library-tv'):
        path = ('plugin://script.infinity.commandcenter/?action=movies'
                if action == 'library-movies'
                else 'plugin://script.infinity.commandcenter/?action=tv')
        return activate(xbmc, gui, path)
    if action in ('movies', 'tv', 'sports'):
        return direct(action, xbmc, gui)
    if action == 'browse':
        return browse(xbmc, gui)
    if action == 'downloads':
        # Native scoped source view; no Android storage probe or source deletion.
        return activate(xbmc, gui, 'files', downloads_only=True)

    return False


if __name__ == '__main__':
    import xbmc
    import xbmcgui
    run(sys.argv[1] if len(sys.argv) > 1 else '', xbmc, xbmcgui)
