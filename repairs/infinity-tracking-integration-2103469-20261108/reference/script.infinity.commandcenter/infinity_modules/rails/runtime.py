"""Kodi script/context/plugin entry points. Entirely on-demand; no threads/services."""
import json
import re
from pathlib import Path
import sys
from urllib.parse import parse_qs
import time

from .store import Store, RailError, SECTIONS, valid_id, ordered_tokens
from .catalog import default_catalog, installed_card, resolve_selected, merge

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
    # Only changed rail URLs are invalidated. No home/widget refresh or timers.
    home = gui.Window(10000)
    for section in sections:
        home.setProperty('Infinity.Rails.'+section+'.Revision', str(value))


def alert(gui, text):
    gui.Dialog().ok('Infinity Add-on Rails', str(text))


def need_candidate(xa, gui):
    version = xa.Addon('skin.infinity.diggz').getAddonInfo('version')
    try:
        ready = tuple(int(v) for v in version.split('.')) >= (1, 0, 5, 218)
    except (ValueError, TypeError):
        ready = False
    if not ready:
        alert(gui, 'Install the complete Infinity Custom Rails RC3 skin ZIP using Install from ZIP. No patch runner is needed.')
    return ready


def select(heading, options, subtitle=''):
    # The current skin supplies the XML and fonts in its actual resolution.
    from .dialog import choose
    return choose(heading, options, subtitle)


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
    chosen = select('ADD TO INFINITY RAILS',
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
    chosen = select('Choose an installed video add-on', [r.get('name',r['addonid']) for r in rows])
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
    chosen = select('Move ' + labels.get(token, token),
        ['Before '+labels.get(t,t) for t in others] + ['At the end'])
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
    changed, rev = Store(profile, monitor.abortRequested).remove(section, token[2:])
    if changed:
        revision(gui, rev, [section])


def selected_card(section, token):
    if section not in SECTIONS:
        raise RailError('Invalid rail destination.')
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    state, warning = Store(profile, monitor.abortRequested).load()
    if warning:
        raise RailError(warning + ' Changes are paused to protect your saved choices.')
    rows = merge(defaults(root), state, section,
                 lambda aid: installed_card(aid, xbmc, xa, vfs))
    row = next((row for row in rows if row['key'] == token), None)
    if row is None or not xbmc.getCondVisibility('System.AddonIsEnabled('+row['addon_id']+')'):
        raise RailError('This add-on is unavailable. Its saved placement has been kept.')
    return row


def has_settings(addon_id, xa, vfs):
    if not valid_id(addon_id):
        return False
    try:
        path = Path(vfs.translatePath(xa.Addon(addon_id).getAddonInfo('path')))
        return (path / 'resources' / 'settings.xml').is_file()
    except RuntimeError:
        return False


def capture_focus(xbmc, gui, token, removing=False):
    if not xbmc.getCondVisibility('Window.IsActive(home)'):
        return None
    try:
        control = gui.Window(10000).getFocusId()
        if control not in (9200, 8820, 8720, 19600, 19601):
            return None
        count = min(512, int(xbmc.getInfoLabel('Container(%d).NumItems' % control)))
        keys = [xbmc.getInfoLabel('Container(%d).ListItemAbsolute(%d).Property(Infinity.Rails.Key)' % (control, index)) for index in range(count)]
        if token not in keys:
            return None
        index = keys.index(token)
        neighbors = keys[index+1:] + list(reversed(keys[:index]))
        target = next((key for key in neighbors if key), '') if removing else token
        return control, target
    except (ValueError, RuntimeError, AttributeError):
        return None


def restore_focus(snapshot, section, xbmc, gui, monitor):
    if not snapshot:
        return
    control, target = snapshot
    if not target:
        return
    home = gui.Window(10000)
    expected = home.getProperty('Infinity.Rails.'+section+'.Revision')
    started = time.monotonic()
    # At most one second, only after an explicit mutation. No thread/timer/service.
    while time.monotonic()-started < 1.0 and not monitor.abortRequested():
        if not xbmc.getCondVisibility('Window.IsActive(home)') or home.getFocusId() != control:
            return  # user navigation takes precedence; never steal focus
        if home.getProperty('Infinity.Rails.'+section+'.LoadedRevision') == expected:
            try:
                count = min(512, int(xbmc.getInfoLabel('Container(%d).NumItems' % control)))
                for index in range(count):
                    key = xbmc.getInfoLabel('Container(%d).ListItemAbsolute(%d).Property(Infinity.Rails.Key)' % (control, index))
                    if key == target:
                        xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (control,index))
                        xbmc.log('Infinity Rails: local refresh/focus %.1f ms' % ((time.monotonic()-started)*1000), xbmc.LOGDEBUG)
                        return
            except (ValueError, RuntimeError):
                return
        if monitor.waitForAbort(0.025):
            return
    xbmc.log('Infinity Rails: focus restore deadline; retained Kodi fallback focus', xbmc.LOGWARNING)


def card_action(action, section, token):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if monitor.abortRequested() or not need_candidate(xa, gui):
        return
    row = selected_card(section, token)
    if action == 'open':
        # Retain the original approved built-in deep link and video target.
        if row['is_folder']:
            xbmc.executebuiltin('ActivateWindow(Videos,"'+row['uri']+'",return)')
        else:
            xbmc.executebuiltin('RunScript('+row['addon_id']+')')
    elif action == 'settings':
        if not has_settings(row['addon_id'], xa, vfs):
            raise RailError('This add-on does not provide settings.')
        xa.Addon(row['addon_id']).openSettings()
    elif action in ('move','remove'):
        snapshot = capture_focus(xbmc, gui, token, removing=action=='remove')
        old_revision = gui.Window(10000).getProperty('Infinity.Rails.'+section+'.Revision')
        if action == 'move':
            move_card(section, token)
        else:
            remove_card(section, token)
        if gui.Window(10000).getProperty('Infinity.Rails.'+section+'.Revision') != old_revision:
            restore_focus(snapshot, section, xbmc, gui, monitor)
    else:
        raise RailError('Unknown rail action.')


def manage(section):
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if section not in SECTIONS or not need_candidate(xa, gui):
        return
    catalog = defaults(root)
    state, warning = Store(profile, monitor.abortRequested).load()
    if warning:
        raise RailError(warning)
    rows = merge(catalog, state, section, lambda aid: installed_card(aid, xbmc, xa, vfs))
    picked = select('Manage '+NAMES[section],
                    ['Add installed add-on…']+[r['label'] for r in rows]+['Cancel'])
    if picked == 0:
        browse_add(section)
    elif 1 <= picked <= len(rows):
        row = rows[picked-1]
        actions = [('Open Add-on','open'), ('Move / Reorder','move')]
        if row['custom']:
            actions.append(('Remove from '+NAMES[section], 'remove'))
        if has_settings(row['addon_id'], xa, vfs):
            actions.append(('Add-on Settings','settings'))
        choice = select('INFINITY — RAIL OPTIONS', [a[0] for a in actions]+['Cancel'], row['label'])
        if 0 <= choice < len(actions):
            card_action(actions[choice][1], section, row['key'])


def options(section, token, expected_addon):
    """Native hit-test receipt: resolve the immutable key, never current selection."""
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    if monitor.abortRequested() or not need_candidate(xa, gui):
        return
    if (gui.getCurrentWindowId() != 10000 or
            gui.getCurrentWindowDialogId() != 9999 or
            xbmc.getInfoLabel('Container(9000).ListItem.Property(section)') != section):
        return
    row = selected_card(section, token)
    if row['addon_id'] != expected_addon:
        raise RailError('The held shortcut changed. Hold the card again.')
    home = gui.Window(10000)
    active = 'Infinity.Rails.OptionsActive'
    if home.getProperty(active) == 'true':
        return
    home.setProperty(active, 'true')
    try:
        xbmc.log('Infinity Rails options: section='+section+' key='+token+
                 ' addon='+expected_addon, xbmc.LOGINFO)
        from .mocha import rail_options
        command = rail_options(row, section, has_settings(row['addon_id'], xa, vfs), root)
        if command in ('open','move','remove','settings'):
            card_action(command, section, token)
    finally:
        home.clearProperty(active)


def inspect_rails():
    """Read-only snapshot with explicit current-window eligibility."""
    from .input_status import collect
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    snapshot = collect(xbmc, xa, gui, vfs)
    report = json.dumps(snapshot, indent=2, sort_keys=True)
    xbmc.log('Infinity Rails input status: ' + report, xbmc.LOGINFO)
    gui.Dialog().textviewer('Infinity Rails Input Status', report)


def plugin(argv=None):
    import xbmcplugin
    argv = sys.argv if argv is None else argv
    handle = int(argv[1])
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    query = parse_qs(argv[2].lstrip('?') if len(argv)>2 else '', keep_blank_values=True)
    section = query.get('section',[''])[0]
    from .stability_probe import RailTrace
    stability_trace = RailTrace(query, section, xbmc)
    action = query.get('action',[''])[0]
    # This add-on intentionally supplies both a Program script and a directory
    # source for the skin. Kodi opens the directory when users tap its tile.
    # v0.1.0 returned an empty directory here. Give the root a usable setup
    # dialog AND real navigation choices without changing the rail endpoints.
    if not section or action:
        if (not action and not section) or action == 'setup':
            main(args=[])  # critical: do not forward plugin handle as script args
        elif action == 'manage' and section in SECTIONS:
            main(args=['manage', section])
        else:
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
            return
        choices = [
            ('Manage Infinity Rails',
             'plugin://'+ADDON_ID+'/?action=setup'),
            ('Manage Movie Add-ons',
             'plugin://'+ADDON_ID+'/?action=manage&section=movies'),
            ('Manage TV Show Add-ons',
             'plugin://'+ADDON_ID+'/?action=manage&section=tvshows'),
        ]
        entries = []
        for title, url in choices:
            listitem = gui.ListItem(label=title, path=url, offscreen=True)
            listitem.setProperty('IsPlayable', 'false')
            entries.append((url, listitem, True))
        xbmcplugin.setContent(handle, 'files')
        accepted = xbmcplugin.addDirectoryItems(handle, entries, totalItems=len(entries))
        xbmcplugin.endOfDirectory(handle, succeeded=(accepted is not False),
                                  cacheToDisc=False)
        return
    if section not in SECTIONS:
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        return
    home = gui.Window(10000)
    ready = 'Infinity.Rails.'+section+'.Ready'
    failed = 'Infinity.Rails.'+section+'.Failed'
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
        stability_trace.mark('data_ready', len(rows))
        for row in rows:
            li = gui.ListItem(label=row['label'], label2=row['label2'], path=row['uri'], offscreen=True)
            li.setArt({'icon':row['icon'], 'thumb':row['thumb']})
            for key, value in row['properties'].items():
                numeric = re.fullmatch(r'\$NUMBER\[(\d+)\]', value)
                li.setProperty(key, numeric[1] if numeric else value)
            li.setProperty('Addon.ID', row['addon_id'])
            li.setProperty('Addon.Name', row['label'])
            li.setProperty('Infinity.Rails.Item','true')
            if stability_trace.request:
                li.setProperty('Infinity.ResumeHub.Request', stability_trace.request)
            li.setProperty('Infinity.Rails.HoldVersion','1')
            li.setProperty('Infinity.Rails.Section',section)
            li.setProperty('Infinity.Rails.Key',row['key'])
            li.setProperty('IsPlayable','false')
            li.setProperty('node.target','videos')
            li.setProperty('node.visible','['+row['visible']+'] + System.AddonIsEnabled('+ADDON_ID+') + String.IsEqual(Container(9000).ListItem.Property(section),'+section+')')
            command = lambda action: 'RunScript('+ADDON_ID+','+action+','+section+','+row['key']+')'
            commands = [('Open Add-on · '+row['label'], command('open')), ('Move / Reorder', command('move'))]
            if row['custom']:
                commands.append(('Remove from '+NAMES[section], command('remove')))
            if has_settings(row['addon_id'], xa, vfs):
                commands.append(('Add-on Settings', command('settings')))
            commands.append(('Cancel', 'noop'))
            li.addContextMenuItems(commands)
            rendered.append((row['uri'],li,row['is_folder']))
        xbmcplugin.setContent(handle,'addons')
        if not xbmcplugin.addDirectoryItems(handle, rendered, totalItems=len(rendered)):
            raise RailError('Kodi did not accept the new rail listing.')
        # Kodi Omega exposes a void return here (Python None), not a boolean.
        xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
        # Publish only after a successful handoff. The original static items remain
        # available on first load, interpreter failure, or helper disable/uninstall.
        home.clearProperty(failed)
        home.setProperty(ready,'true')
        home.setProperty('Infinity.Rails.'+section+'.LoadedRevision', str(state['revision']))
        stability_trace.mark('directory_handoff', len(rendered))
    except Exception as exc:
        home.clearProperty(ready)
        home.setProperty(failed,'true')
        xbmc.log('Infinity Rails: listing failed; preserved static rail fallback. '+str(exc), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)


def main(args=None):
    args = sys.argv[1:] if args is None else args
    xbmc, xa, gui, vfs, root, profile, monitor = setup()
    try:
        if monitor.abortRequested():
            return
        if args:
            action = args[0]
            if action == 'inspect':
                inspect_rails()
                return
            if action == 'stability':
                from .stability_probe import menu
                menu(xbmc, xa, gui, vfs, profile, monitor)
                return
            if action == 'add':
                do_add(explicit_id=args[1] if len(args)>1 else None)
                return
            section = args[1] if len(args)>1 else ''
            if action == 'manage' and section in SECTIONS:
                manage(section)
            elif action == 'options' and section in SECTIONS and len(args)==4:
                options(section, args[2], args[3])
            elif action in ('open','settings','move','remove') and len(args)==3:
                card_action(action,section,args[2])
            else:
                raise RailError('Unknown rail action.')
            return
        if not need_candidate(xa, gui):
            return
        picked = select('INFINITY ADD-ON RAILS', [NAMES['movies'],NAMES['tvshows'],'Inspect Rail Input','Stability Evidence','Cancel'])
        if picked in (0,1):
            manage(SECTIONS[picked])
        elif picked == 2:
            inspect_rails()
        elif picked == 3:
            from .stability_probe import menu
            menu(xbmc, xa, gui, vfs, profile, monitor)
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
