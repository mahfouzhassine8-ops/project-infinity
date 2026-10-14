"""Kodi script/context/plugin entry points. Entirely on-demand; no threads/services."""
import json
import re
from pathlib import Path
import sys
from urllib.parse import parse_qs

from .store import Store, RailError, SECTIONS, valid_id, ordered_tokens
from .catalog import default_catalog, installed_card, resolve_selected, merge
from .menu import choose

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


def defaults(root):
    # Immutable exact .215 source, packaged as XML data; no provider code is imported.
    return default_catalog((root / 'resources' / 'defaults.xml').read_bytes())


def revision(gui, value, sections=SECTIONS):
    # URI invalidation is limited to the rail(s) actually changed. No home refresh.
    for section in sections:
        gui.Window(10000).setProperty('Infinity.Rails.'+section+'.Revision', str(value))


def alert(gui, text):
    gui.Dialog().ok('Infinity Add-on Rails', str(text))


def need_candidate(gui, xa):
    version = xa.Addon('skin.infinity.diggz').getAddonInfo('version')
    parts = tuple(int(p) for p in version.split('.'))
    if parts < (1, 0, 5, 219):
        raise RailError('Install the complete Infinity .219 skin ZIP. The Rails helper does not patch skin resources.')
    return True


def do_add(item=None, explicit_id=None):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if monitor.abortRequested():
        return
    need_candidate(gui, xa)
    addon_id = explicit_id or resolve_selected(item)
    info = installed_card(addon_id, xbmc, xa, vfs)
    if info is None:
        raise RailError('That item is not an enabled, installed video add-on. Nothing was installed, enabled or changed.')
    chosen = choose(gui, 'ADD TO INFINITY RAILS',
                    [NAMES['movies'], NAMES['tvshows'], 'Both Rails', 'Cancel'], info['label'])
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
    chosen = choose(gui, 'ADD TO INFINITY RAILS', [r.get('name',r['addonid']) for r in rows] + ['Cancel'], 'Choose an installed video add-on')
    if 0 <= chosen < len(rows):
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
    chosen = choose(gui, 'MOVE / REORDER',
        ['Before '+labels.get(t,t) for t in others] + ['At the end', 'Cancel'], labels.get(token, token))
    if not 0 <= chosen <= len(others):
        return
    changed, rev = store.move(section, token, others[chosen] if chosen < len(others) else None,
                        [r['key'] for r in catalog[section]])
    if changed:
        revision(gui, rev, [section])


def remove_card(section, token):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if not token.startswith('c:'):
        raise RailError('Approved built-in cards are protected. Only custom shortcuts can be removed.')
    if choose(gui, 'REMOVE RAIL SHORTCUT?', ['Remove from '+NAMES[section], 'Cancel'], 'The add-on, its settings and data stay installed.') != 0:
        return
    changed, rev = Store(profile, monitor.abortRequested).remove(section, token[2:])
    if changed:
        revision(gui, rev, [section])


def selected_card(section, token, xbmc, xa, vfs, root, profile, monitor):
    if section not in SECTIONS:
        raise RailError('Invalid rail destination.')
    catalog = defaults(root)
    state, warning = Store(profile, monitor.abortRequested).load()
    if warning:
        raise RailError(warning + ' Changes are paused to protect your saved choices.')
    for row in merge(catalog, state, section, lambda aid: installed_card(aid, xbmc, xa, vfs)):
        if row['key'] == token:
            return row
    raise RailError('That shortcut is unavailable or is no longer in the rail. Your other choices were kept.')


def has_settings(aid, xa, vfs):
    if not valid_id(aid):
        return False
    try:
        return (Path(vfs.translatePath(xa.Addon(aid).getAddonInfo('path'))) / 'resources/settings.xml').is_file()
    except (OSError, RuntimeError):
        return False


def open_card(section, token, settings=False):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if monitor.abortRequested():
        return
    row = selected_card(section, token, xbmc, xa, vfs, root, profile, monitor)
    if not xbmc.getCondVisibility('System.AddonIsEnabled('+row['addon_id']+')'):
        raise RailError('This add-on is unavailable. Its saved rail position was retained.')
    if settings:
        if not has_settings(row['addon_id'], xa, vfs):
            raise RailError('This add-on has no supported settings dialog.')
        xbmc.executebuiltin('Addon.OpenSettings('+row['addon_id']+')')
    elif row['is_folder']:
        # Retain approved built-in deep links. Never resolve or play a video here.
        xbmc.executebuiltin('ActivateWindow(Videos,"'+row['uri'].replace('"', '%22')+'",return)')
    else:
        xbmc.executebuiltin('RunScript('+row['addon_id']+')')


def commands(row, section, xa, vfs):
    prefix = 'RunScript('+ADDON_ID+','
    suffix = ','+section+','+row['key']+')'
    result = [('Open Add-on', prefix+'open'+suffix), ('Move / Reorder', prefix+'move'+suffix)]
    if row['custom']:
        result.append(('Remove from '+NAMES[section], prefix+'remove'+suffix))
    if has_settings(row['addon_id'], xa, vfs):
        result.append(('Add-on Settings', prefix+'settings'+suffix))
    result.append(('Cancel', 'noop'))
    return result


def options(section, token):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    # Invoked only by the native context window's Rails-specific onload bridge.
    # This window was opened by Kodi's context action/intentional long-press.
    xbmc.executebuiltin('Dialog.Close(contextmenu,true)')
    if monitor.abortRequested():
        return
    row = selected_card(section, token, xbmc, xa, vfs, root, profile, monitor)
    opts = commands(row, section, xa, vfs)
    action = choose(gui, 'INFINITY — RAIL OPTIONS', [o[0] for o in opts], row['label'], root)
    if not 0 <= action < len(opts)-1:
        return
    name = opts[action][1].split(',')[1]
    if name == 'move':
        move_card(section, token)
    elif name == 'remove':
        remove_card(section, token)
    else:
        open_card(section, token, settings=(name == 'settings'))


def manage(section):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    need_candidate(gui, xa)
    while not monitor.abortRequested():
        catalog = defaults(root)
        state, warning = Store(profile, monitor.abortRequested).load()
        if warning:
            raise RailError(warning)
        rows = merge(catalog, state, section, lambda aid: installed_card(aid, xbmc, xa, vfs))
        picked = choose(gui, 'MANAGE '+NAMES[section].upper(), ['Add installed add-on...']+[r['label'] for r in rows]+['Cancel'])
        if picked < 0 or picked > len(rows):
            return
        if picked == 0:
            browse_add(section)
            continue
        row = rows[picked-1]
        opts = commands(row, section, xa, vfs)
        action = choose(gui, 'INFINITY — RAIL OPTIONS', [o[0] for o in opts], row['label'])
        if 0 <= action < len(opts)-1:
            name = opts[action][1].split(',')[1]
            if name == 'move':
                move_card(section, row['key'])
            elif name == 'remove':
                remove_card(section, row['key'])
            else:
                open_card(section, row['key'], settings=(name == 'settings'))
                return


def plugin(argv=None):
    import xbmcplugin
    argv = sys.argv if argv is None else argv
    handle = int(argv[1])
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    query = parse_qs(argv[2].lstrip('?') if len(argv)>2 else '', keep_blank_values=True)
    section = query.get('section',[''])[0]
    action = query.get('action',[''])[0]
    # Opening the helper tile presents navigation only; no automatic modal menu.
    if not section or action:
        if action == 'manage' and section in SECTIONS:
            main(args=['manage', section])
        elif action not in ('', 'setup'):
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
            return
        entries = []
        for sec in SECTIONS:
            url = 'plugin://'+ADDON_ID+'/?action=manage&section='+sec
            li = gui.ListItem(label='Manage '+NAMES[sec], path=url, offscreen=True)
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
        cache = {}
        def discover(aid):
            if aid not in cache:
                cache[aid] = installed_card(aid, xbmc, xa, vfs)
            return cache[aid]
        rows = merge(catalog, state, section, discover)
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
            li.addContextMenuItems(commands(row, section, xa, vfs), replaceItems=True)
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
        if args:
            action = args[0]
            if action == 'add':
                do_add(explicit_id=args[1] if len(args)>1 else None)
                return
            section = args[1] if len(args)>1 else ''
            if section not in SECTIONS:
                raise RailError('Invalid rail destination.')
            if action == 'manage':
                manage(section)
            elif action == 'options' and len(args)==3:
                options(section,args[2])
            elif action == 'move' and len(args)==3:
                move_card(section,args[2])
            elif action == 'remove' and len(args)==3:
                remove_card(section,args[2])
            elif action in ('open', 'settings') and len(args)==3:
                open_card(section,args[2], settings=(action == 'settings'))
            else:
                raise RailError('Unknown rail action.')
            return
        need_candidate(gui, xa)
        picked = choose(gui, 'INFINITY ADD-ON RAILS', ['Manage Movie Add-ons', 'Manage TV Show Add-ons', 'Cancel'])
        if picked in (0, 1):
            manage(SECTIONS[picked])
    except Exception as exc:
        xbmc.log('Infinity Rails: '+str(exc), xbmc.LOGERROR)
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
