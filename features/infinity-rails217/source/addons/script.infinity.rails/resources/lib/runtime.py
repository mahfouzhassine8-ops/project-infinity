"""On-demand Kodi entry points; no startup hooks, background services or networking."""
import json
import re
from pathlib import Path
import sys
from urllib.parse import parse_qs
import uuid

from .store import Store, RailError, SECTIONS, valid_id, ordered_tokens
from .catalog import default_catalog, installed_card, resolve_selected, merge
from . import menu
from functools import lru_cache

ADDON_ID = 'script.infinity.rails'
NAMES = {'movies': 'Movie Add-ons', 'tvshows': 'TV Show Add-ons'}


def env():
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcvfs
    addon = xbmcaddon.Addon(ADDON_ID)
    return xbmc, xbmcaddon, xbmcgui, xbmcvfs, addon


def setup():
    xbmc, xa, gui, vfs, addon = env()
    root = Path(vfs.translatePath(addon.getAddonInfo('path')))
    profile = Path(vfs.translatePath(addon.getAddonInfo('profile')))
    monitor = xbmc.Monitor()
    return xbmc, xa, gui, vfs, root, profile, monitor


@lru_cache(maxsize=2)
def defaults(root):
    # Immutable exact .215 source, packaged as XML data; no provider code is imported.
    return default_catalog((root / 'resources' / 'defaults.xml').read_bytes())


def revision(gui, value, sections=SECTIONS):
    stamp = str(value) + '-' + uuid.uuid4().hex
    for section in sections:
        gui.Window(10000).setProperty('Infinity.Rails.' + section + '.Revision', stamp)


def alert(gui, text):
    gui.Dialog().ok('Infinity Add-on Rails', str(text))


def need_candidate(xa, gui):
    # No skin resource writer or installer remains in the runtime helper.
    version = xa.Addon('skin.infinity.diggz').getAddonInfo('version')
    match = re.fullmatch(r'1\.0\.5\.(\d+)', version)
    if not match or int(match[1]) < 217:
        alert(gui, 'Install the complete Infinity skin 1.0.5.217 RC3 ZIP first. Your saved rail choices are kept. This helper does not patch skin files.')
        return False
    return True


def choose(gui, xbmc, root, title, choices, subtitle='', icon='', initial=0):
    profile = setup()[5]
    with menu.menu_lock(profile, 'rails-modal.lock') as acquired:
        if acquired:
            return menu.select(gui, xbmc, root, title, subtitle, choices, icon, initial)
    return None


def do_add(item=None, explicit_id=None):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if monitor.abortRequested():
        return
    if not need_candidate(xa, gui):
        return
    addon_id = explicit_id or resolve_selected(item)
    info = installed_card(addon_id, xbmc, xa, vfs)
    if info is None:
        raise RailError('That item is not an enabled, installed video add-on. Nothing was installed, enabled or changed.')
    chosen = choose(gui, xbmc, root, 'ADD TO INFINITY RAILS',
                    [(0, NAMES['movies']), (1, NAMES['tvshows']), (2, 'Both Rails'), (None, 'Cancel')],
                    info['label'], info['icon'])
    if chosen not in (0, 1, 2):
        return
    sections = [SECTIONS[chosen]] if chosen < 2 else list(SECTIONS)
    catalog = defaults(root)
    added, rev = Store(profile, monitor.abortRequested).add(addon_id, sections,
        {sec: [row['addon_id'] for row in catalog[sec]] for sec in SECTIONS})
    if added:
        revision(gui, rev, added)
    if not added:
        gui.Dialog().notification('Infinity Rails', 'Already present in the selected rail(s).', time=2200)
    else:
        gui.Dialog().notification('Infinity Rails', 'Added to ' + ' and '.join(NAMES[s] for s in added), time=2200)


def browse_add(section=None):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    # One explicit local metadata query, only when the user selects Add.
    response = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc':'2.0', 'id':1, 'method':'Addons.GetAddons',
        'params':{'content':'video','enabled':True,'properties':['name']}})))
    if 'error' in response:
        raise RailError('Kodi could not list installed video add-ons. Use All Add-ons and long-press the add-on instead.')
    rows = [r for r in response.get('result',{}).get('addons',[]) if valid_id(r.get('addonid')) and r.get('addonid') != ADDON_ID]
    rows.sort(key=lambda r: r.get('name',r['addonid']).casefold())
    if not rows:
        raise RailError('No enabled video add-ons were found.')
    chosen = choose(gui, xbmc, root, 'ADD TO INFINITY RAILS',
                    [(i, r.get('name', r['addonid'])) for i, r in enumerate(rows)] + [(None, 'Cancel')],
                    'Choose an installed video add-on')
    if chosen is not None and 0 <= chosen < len(rows):
        do_add(explicit_id=rows[chosen]['addonid'])


def move_card(section, token):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    catalog = defaults(root)
    store = Store(profile, monitor.abortRequested)
    state, warning = store.load()
    if warning:
        raise RailError(warning + ' Changes are paused to protect your saved choices.')
    tokens = ordered_tokens([r['key'] for r in catalog[section]], state['rails'][section])
    if token not in tokens:
        raise RailError('That card is no longer in the rail.')
    labels = {r['key']:r['label'] for r in catalog[section]}
    for addon_id in state['rails'][section]['custom']:
        card = installed_card(addon_id, xbmc, xa, vfs)
        labels['c:'+addon_id] = card['label'] if card else addon_id+' (unavailable)'
    others = [t for t in tokens if t != token]
    chosen = choose(gui, xbmc, root, 'MOVE / REORDER',
        [(i, 'Before ' + labels.get(t, t)) for i, t in enumerate(others)] + [(len(others), 'At the end'), (None, 'Cancel')],
        labels.get(token, token))
    if chosen is None or not 0 <= chosen <= len(others):
        return
    changed, rev = store.move(section, token, others[chosen] if chosen < len(others) else None,
                        [r['key'] for r in catalog[section]])
    if changed:
        revision(gui, rev, [section])


def remove_card(section, token):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if not token.startswith('c:'):
        raise RailError('Approved built-in cards are protected. Only custom shortcuts can be removed.')
    if choose(gui, xbmc, root, 'REMOVE SHORTCUT?',
              [(True, 'Remove from ' + NAMES[section]), (None, 'Cancel')],
              'The add-on stays installed.') is not True:
        return
    changed, rev = Store(profile, monitor.abortRequested).remove(section, token[2:])
    if changed:
        revision(gui, rev, [section])


def selected_row(section, token, root, profile, monitor, xbmc, xa, vfs):
    if section not in SECTIONS:
        raise RailError('Invalid rail destination.')
    state, warning = Store(profile, monitor.abortRequested).load()
    if warning:
        raise RailError(warning + ' Changes are paused to protect your saved choices.')
    standard = defaults(root)[section]
    builtin = next((r for r in standard if r['key'] == token), None)
    if builtin is not None:
        return builtin
    if token.startswith('c:') and token[2:] in state['rails'][section]['custom']:
        if token[2:] not in {r['addon_id'] for r in standard}:
            return installed_card(token[2:], xbmc, xa, vfs)
    return None


def options(section, token):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if monitor.abortRequested() or not need_candidate(xa, gui):
        return
    row = selected_row(section, token, root, profile, monitor, xbmc, xa, vfs)
    if row is None:
        raise RailError('This shortcut is unavailable or the rail has changed. Your saved choices are kept.')
    actions = [('open', 'Open Add-on'), ('move', 'Move / Reorder')]
    if row['custom']:
        actions.append(('remove', 'Remove from ' + NAMES[section]))
    addon_path = Path(vfs.translatePath(xa.Addon(row['addon_id']).getAddonInfo('path')))
    if (addon_path / 'resources' / 'settings.xml').is_file():
        actions.append(('settings', 'Add-on Settings'))
    actions.append((None, 'Cancel'))
    picked = choose(gui, xbmc, root, 'INFINITY — RAIL OPTIONS', actions,
                    row['label'] + ' · ' + NAMES[section], row['icon'])
    if picked is None or monitor.abortRequested():
        return
    # Re-resolve at commit time: a different interpreter may have changed the rail.
    row = selected_row(section, token, root, profile, monitor, xbmc, xa, vfs)
    if row is None:
        raise RailError('The selected shortcut changed. Please reopen its menu.')
    if picked == 'move':
        move_card(section, token)
    elif picked == 'remove' and row['custom']:
        remove_card(section, token)
    elif picked == 'settings' and (addon_path / 'resources' / 'settings.xml').is_file():
        xa.Addon(row['addon_id']).openSettings()
    elif picked == 'open':
        if not xbmc.getCondVisibility('System.AddonIsEnabled(' + row['addon_id'] + ')'):
            raise RailError('This add-on is currently unavailable. The shortcut is kept.')
        if row.get('action'):
            xbmc.executebuiltin(row['action'])
        elif row['is_folder']:
            xbmc.executebuiltin('ActivateWindow(Videos,"' + row['uri'] + '",return)')
        else:
            xbmc.executebuiltin('RunAddon(' + row['addon_id'] + ')')


def context_options():
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    home = gui.Window(10000)
    cid = home.getFocusId()
    if cid not in (9200, 8820, 8720, 19600) or not xbmc.getCondVisibility('Window.IsActive(home)'):
        return
    prefix = 'Container(' + str(cid) + ').ListItem.Property('
    section = xbmc.getInfoLabel(prefix + 'Infinity.Rails.Section)')
    token = xbmc.getInfoLabel(prefix + 'Infinity.Rails.Key)')
    if section not in SECTIONS or not token:
        return
    # The only automatic entry point is the native ContextMenu onload triggered
    # by an intentional long press/right click. No focus/scroll/startup action
    # opens a Python menu. Cancel the native popup before showing our modal.
    xbmc.executebuiltin('Dialog.Close(contextmenu,true)', True)
    with menu.menu_lock(profile) as acquired:
        if acquired and not monitor.abortRequested():
            options(section, token)


def manage(section):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if not need_candidate(xa, gui):
        return
    state, warning = Store(profile, monitor.abortRequested).load()
    if warning:
        raise RailError(warning)
    rows = merge(defaults(root), state, section,
                 lambda aid: installed_card(aid, xbmc, xa, vfs))
    chosen = choose(gui, xbmc, root, 'MANAGE ' + NAMES[section].upper(),
                    [('add', 'Add installed add-on…')] + [(r['key'], r['label']) for r in rows] + [(None, 'Cancel')])
    if chosen == 'add':
        browse_add(section)
    elif chosen is not None:
        options(section, chosen)


def plugin(argv=None):
    import xbmcplugin
    argv = sys.argv if argv is None else argv
    handle = int(argv[1])
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    query = parse_qs(argv[2].lstrip('?') if len(argv)>2 else '', keep_blank_values=True)
    section = query.get('section',[''])[0]
    action = query.get('action',[''])[0]
    # Root navigation is usable, but requesting a listing never opens a modal.
    # Management runs only after an explicit click of a helper navigation entry.
    if not section or action:
        if action == 'manage' and section in SECTIONS:
            main(args=['manage', section])
        elif action and action != 'setup':
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
            return
        entries = []
        for sec in SECTIONS:
            url = 'plugin://' + ADDON_ID + '/?action=manage&section=' + sec
            li = gui.ListItem(label='Manage ' + NAMES[sec], path=url, offscreen=True)
            li.setProperty('IsPlayable', 'false')
            entries.append((url, li, True))
        xbmcplugin.setContent(handle, 'files')
        accepted = xbmcplugin.addDirectoryItems(handle, entries, totalItems=len(entries))
        xbmcplugin.endOfDirectory(handle, succeeded=(accepted is not False), cacheToDisc=False)
        return
    if section not in SECTIONS:
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    home = gui.Window(10000)
    ready = 'Infinity.Rails.'+section+'.Ready'
    if monitor.abortRequested():
        home.clearProperty(ready)
        xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
        return
    try:
        catalog = defaults(root)
        state, warning = Store(profile, monitor.abortRequested).load()
        if warning:
            xbmc.log('Infinity Rails: '+warning, xbmc.LOGWARNING)
        rows = merge(catalog, state, section,
            lambda aid: installed_card(aid, xbmc, xa, vfs))
        rendered = []
        for row in rows:
            li = gui.ListItem(label=row['label'], label2=row['label2'], path=row['uri'], offscreen=True)
            li.setArt({'icon':row['icon'], 'thumb':row['thumb']})
            for key, value in row['properties'].items():
                numeric = re.fullmatch(r'\$NUMBER\[(\d+)\]', value)
                li.setProperty(key, numeric[1] if numeric else value)
            li.setProperty('Addon.ID', row['addon_id'])
            li.setProperty('Addon.Name', row['label'])
            li.setProperty('Infinity.Rails.Item','true')
            li.setProperty('Infinity.Rails.Section',section)
            li.setProperty('Infinity.Rails.Key',row['key'])
            li.setProperty('IsPlayable','false')
            li.setProperty('node.target','videos')
            li.setProperty('node.visible','['+row['visible']+'] + System.AddonIsEnabled('+ADDON_ID+') + String.IsEqual(Container(9000).ListItem.Property(section),'+section+')')
            li.addContextMenuItems([('Infinity — Rail Options', 'RunScript(' + ADDON_ID + ',options,' + section + ',' + row['key'] + ')')], replaceItems=True)
            rendered.append((row['uri'],li,row['is_folder']))
        xbmcplugin.setContent(handle,'addons')
        if not xbmcplugin.addDirectoryItems(handle, rendered, totalItems=len(rendered)):
            raise RailError('Kodi did not accept the new rail listing.')
        # Kodi Omega exposes a void return here (Python None), not a boolean.
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        # Publish only after a successful handoff. The original static items remain
        # available on first load, interpreter failure, or helper disable/uninstall.
        home.setProperty(ready,'true')
    except Exception as exc:
        home.clearProperty(ready)
        xbmc.log('Infinity Rails: listing failed; preserved static rail fallback. '+str(exc), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)


def main(args=None):
    args = sys.argv[1:] if args is None else args
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    try:
        if monitor.abortRequested():
            return
        if not args:
            sec = choose(gui, xbmc, root, 'INFINITY ADD-ON RAILS',
                         [('movies', 'Manage Movie Add-ons'), ('tvshows', 'Manage TV Show Add-ons'), (None, 'Cancel')])
            if sec in SECTIONS:
                manage(sec)
            return
        action = args[0]
        if action == 'context':
            context_options()
            return
        if action == 'add':
            do_add(explicit_id=args[1] if len(args) > 1 else None)
            return
        section = args[1] if len(args) > 1 else ''
        if section not in SECTIONS:
            raise RailError('Invalid rail destination.')
        if action == 'manage':
            manage(section)
        elif action == 'options' and len(args) == 3:
            with menu.menu_lock(profile) as acquired:
                if acquired:
                    options(section, args[2])
        elif action == 'move' and len(args) == 3:
            move_card(section, args[2])
        elif action == 'remove' and len(args) == 3:
            remove_card(section, args[2])
        else:
            raise RailError('Unknown rail action.')
    except Exception as exc:
        xbmc.log('Infinity Rails: ' + str(exc), xbmc.LOGERROR)
        alert(gui, str(exc))


def context_add(item):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    try:
        if item is None:
            raise RailError('Kodi did not supply the selected add-on. Nothing was changed.')
        do_add(item=item)
    except Exception as exc:
        xbmc.log('Infinity Rails: '+str(exc), xbmc.LOGERROR)
        alert(gui, str(exc))
