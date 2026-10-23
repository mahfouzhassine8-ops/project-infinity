"""On-demand actions. No worker service, provider edits or new progress database."""
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from menu_model import addon_rows, valid_id, hidden_setting
from popup import choose

ID = 'script.infinity.uirepair'

def rpc(method, params):
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params))))
    if 'error' in reply:
        raise RuntimeError('Kodi could not complete ' + method + '.')
    return reply.get('result')

def addons():
    values = rpc('Addons.GetAddons', dict(type='xbmc.addon.video', enabled=True, properties=['name', 'thumbnail', 'path']))
    # Video capability is authoritative; an ID prefix is not a media type.
    return [r for r in values.get('addons', []) if valid_id(r.get('addonid', '')) and r['addonid'] != ID]

def destination(aid):
    if not valid_id(aid) or aid == ID:
        return None
    addon = xbmcaddon.Addon(aid)
    root = Path(xbmcvfs.translatePath(addon.getAddonInfo('path')))
    with (root / 'addon.xml').open('rb') as stream:
        raw = stream.read(131073)
    if len(raw) > 131072 or b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:
        return None
    manifest = ET.fromstring(raw)
    if manifest.get('id') != aid:
        return None
    script = None
    for extension in manifest.findall('extension'):
        provides = (extension.findtext('provides') or '').split()
        if 'video' not in provides: continue
        if extension.get('point') == 'xbmc.python.pluginsource':
            return ('plugin', 'plugin://' + aid + ('/?content_type=video' if len(provides) > 1 else '/'))
        if extension.get('point') == 'xbmc.python.script':
            script = ('script', aid)
    return script

def manageable(aid):
    return not aid.startswith(('script.infinity.', 'service.infinity.', 'skin.infinity.'))

def addon_info(aid):
    if not valid_id(aid):
        raise ValueError('Not an installed video source')
    values = rpc('Addons.GetAddonDetails', dict(addonid=aid, properties=['name', 'thumbnail', 'path', 'enabled']))
    row = values.get('addon', {})
    if row.get('addonid') != aid or not row.get('enabled') or not destination(aid):
        raise RuntimeError('This video source is unavailable. Its data was kept.')
    return row

def hidden(aid):
    return xbmc.getCondVisibility('Skin.HasSetting(' + hidden_setting(aid) + ')')

def refresh_grid():
    # Revision refresh keeps DirectoryProvider's stable-path selection. Do not
    # navigate away, rebuild Home, or reset the panel for a dismissed popup.
    xbmcgui.Window(10000).setProperty('Infinity.UI.GridRevision', str(time.monotonic_ns()))

def set_hidden(aid, value):
    if value and not manageable(aid):
        raise ValueError('This Infinity navigation entry must remain available.')
    command = 'Skin.SetBool' if value else 'Skin.Reset'
    xbmc.executebuiltin(command + '(' + hidden_setting(aid) + ')', True)
    if hidden(aid) != value:
        raise RuntimeError('Kodi did not apply the view visibility setting.')
    refresh_grid()

def settings_available(aid):
    addon = xbmcaddon.Addon(aid)
    return xbmcvfs.exists(str(Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))) / 'resources/settings.xml'))

def rails_supported():
    if not xbmc.getCondVisibility('System.AddonIsEnabled(script.infinity.rails)'):
        return False
    return xbmcaddon.Addon('script.infinity.rails').getAddonInfo('version') in ('0.2.6', '0.2.7')

def open_addon(aid):
    addon_info(aid)
    kind, target = destination(aid)
    xbmc.executebuiltin('RunScript(' + aid + ')' if kind == 'script' else
                       'ActivateWindow(Videos,' + target + ',return)')

def ensure_selected_addon(aid):
    """Refuse actions for a tile that changed while its popup was open.

    This guard is only called by the Video Sources item menu, never Resume
    Hub, Rails, the original Kodi add-on manager or any Cobra control.
    """
    if (not valid_id(aid) or xbmcgui.getCurrentWindowId() != 11193 or
            xbmc.getInfoLabel('Container(50).ListItem.Property(Addon.ID)') != aid or
            xbmc.getInfoLabel('Container(50).ListItem.Property(Infinity.UI.Token)') != aid):
        raise RuntimeError('The selected Video Source changed. Open its menu again.')


def manage(aid, row):
    if not manageable(aid):
        return
    ensure_selected_addon(aid)
    result = choose('More / Manage Add-on — ' + row.get('name', aid), [('Disable Add-on', 'disable')])
    if result != 'disable':
        return
    if not xbmcgui.Dialog().yesno('Disable Add-on',
            'Disable ' + row.get('name', aid) + '? This disables it everywhere and may affect other Infinity features. '
            'Its settings and data will be kept. Use Hide from This View to hide only this tile.',
            nolabel='Cancel', yeslabel='Disable Add-on'):
        return
    # Explicit confirmation cannot disable a different tile when provider
    # focus updates during a nested dialog.
    ensure_selected_addon(aid)
    addon_info(aid) # Revalidate after user input. Kodi retains dependency enforcement.
    rpc('Addons.SetAddonEnabled', dict(addonid=aid, enabled=False))
    refresh_grid()

def addon_menu(aid):
    ensure_selected_addon(aid)
    row = addon_info(aid)
    action = choose('Add-on Options — ' + row.get('name', aid),
                    addon_rows(settings_available(aid), rails_supported(), manageable=manageable(aid)))
    if action is None:
        return
    # The popup can outlive asynchronous grid/item updates. Never launch,
    # hide, favourite, manage or act on an old tile after focus changes.
    ensure_selected_addon(aid)
    addon_info(aid)
    current = addon_rows(settings_available(aid), rails_supported(),
                         manageable=manageable(aid))
    if action not in {op for _, op in current}:
        raise RuntimeError('This Video Source action is no longer available. Open the menu again.')
    if action == 'open':
        open_addon(aid)
    elif action == 'info':
        xbmc.executebuiltin('Action(Info,11193)')
    elif action == 'settings':
        xbmcaddon.Addon(aid).openSettings()
    elif action == 'favourite':
        kind, path = destination(aid)
        existing = rpc('Favourites.GetFavourites', dict(properties=['window', 'windowparameter', 'path']))
        # Kodi serializes an empty favourites vector as null. Treat it as an
        # empty collection so the first favourite can actually be added.
        if any(f.get('windowparameter') == path or f.get('path') == path for f in (existing.get('favourites') or [])):
            xbmcgui.Dialog().notification('Infinity', 'This add-on is already in Favourites.')
            return
        target = dict(type='script', path=path) if kind == 'script' else dict(type='window', window='videos', windowparameter=path)
        rpc('Favourites.AddFavourite', dict(title=row.get('name', aid), thumbnail=row.get('thumbnail', ''), **target))
    elif action == 'rails':
        xbmc.executebuiltin('RunScript(script.infinity.rails,add,' + aid + ')')
    elif action == 'hide':
        set_hidden(aid, True)
    elif action == 'manage':
        manage(aid, row)

def restore_hidden():
    rows = [(r.get('name', r['addonid']), r['addonid']) for r in addons() if hidden(r['addonid'])]
    if not rows:
        xbmcgui.Dialog().notification('Infinity', 'No hidden video sources.')
        return
    aid = choose('Restore Hidden Video Sources', rows)
    if aid:
        set_hidden(aid, False)

def resume_menu(key):
    from controller_access import load, context_rows, mutate
    plugin = load()
    entry, rows = context_rows(plugin, key)
    if not rows:
        raise RuntimeError('This saved item is no longer available. No progress was changed.')
    op = choose('Continue Playing — ' + str(entry.get('label') or entry.get('title') or 'Item'), rows)
    if op is None:
        return
    choice, name = None, ''
    if op == 'rate':
        selected = choose('Rate', [('Remove rating', '0')] + [(str(i) + ' / 10', str(i)) for i in range(1, 11)])
        if selected is None:
            return
        choice = int(selected)
    elif op == 'add-list':
        name = xbmcgui.Dialog().input('Add to custom list').strip()[:80]
        if not name:
            return
    expected_label = next((label for label, action in rows if action == op), None)
    if expected_label is None:
        raise RuntimeError('The selected Continue Playing action changed. No data was modified.')
    if mutate(plugin, key, entry, op, choice, name, expected_label=expected_label):
        # Original publish_home updates the existing rail revision. No forced
        # Home navigation or Container.Refresh on an unrelated provider window.
        xbmcgui.Dialog().notification('Infinity Resume Hub', 'Saved', time=1800)
    else:
        xbmcgui.Dialog().notification('Infinity Resume Hub',
                                     'Item changed. Open its menu again.', time=3500)


def _continue_choice_clock(seconds):
    seconds = max(0, int(seconds))
    minutes, remain = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return ('%d:%02d:%02d' % (hours, minutes, remain)) if hours else ('%d:%02d' % (minutes, remain))


def home_continue_choice(key, media):
    """Home Continue Watching ONLY. Never write progress or choose a new source.

    The existing popup uses a modal vertical two-row Kodi control with large
    touch targets. The original Command Center creates the ListItem, so
    identity, watched checkmark, video info and saved offset are reused.
    Changing media selection never mutates persisted state or Cobra.
    """
    from controller_access import load
    if media not in ('movie', 'tv'):
        return
    controller = load()
    if not controller.hub.KEY_RE.fullmatch(str(key)):
        return
    def current():
        data = controller.hub.load_view(controller.PROFILE)
        entry = data.get('items', {}).get(key)
        if not isinstance(entry, dict) or entry.get('media') != media or entry.get('synthetic_next'):
            return None, None, '', None
        identity = controller.hub.entry_identity(entry)
        if not identity:
            return None, None, '', None
        target = controller.navigation_target(entry, data, 'continue')
        return data, entry, target, identity
    data, entry, target, identity = current()
    if entry is None or not target:
        xbmcgui.Dialog().ok('Infinity Resume Hub',
            'This source is unavailable or has expired. Open the title in your provider to resolve a fresh source. Resume Hub kept your local state.')
        return
    pos = max(0.0, controller.number(entry.get('position')))
    duration = max(0.0, controller.number(entry.get('duration')))
    resume_allowed = pos > 0 and (duration <= 0 or pos < duration)
    label = str(entry.get('label') or entry.get('title') or 'Title')
    options = ([('Resume from ' + _continue_choice_clock(pos), 'resume')]
               if resume_allowed else [])
    options.append(('Play from beginning', 'begin'))
    selected = choose('Continue Watching — ' + label, options)
    if selected not in ('resume', 'begin'):
        return
    # A modal can outlive asynchronous playback progress/source updates.
    # The original identity & path must still match before launching.
    live_data, live, live_target, live_identity = current()
    if (live is None or not live_target or live_identity != identity or live_target != target or
            live.get('updated') != entry.get('updated') or
            live.get('position') != entry.get('position') or
            live.get('duration') != entry.get('duration')):
        xbmcgui.Dialog().notification('Infinity Resume Hub', 'Item changed. Open it again.', time=2500)
        return
    if selected == 'resume' and not resume_allowed:
        return
    offset = pos if selected == 'resume' else 0
    if target.startswith('plugin://script.infinity.commandcenter/?action=saved-recovery&'):
        controller.recover_entry(key, 'continue', resume_offset=offset)
        return
    _, item = controller._list_item(live, live_data, 'continue')
    item.setProperty('ResumeTime', str(offset))
    item.setProperty('StartOffset', str(offset))
    # Preserve Kodi's original URL/listitem playback path and selected
    # saved offset; no provider search, data reset, synthetic source or
    # global PlayMedia/DialogSelect rewrite.
    xbmc.Player().play(target, item)

def main(args):
    home = xbmcgui.Window(10000)
    if args and args[0] == 'option-b':
        from home_option_b import _trace
        _trace(xbmc, 'python.entry', 'received')
    if home.getProperty('Infinity.UI.MenuActive'):
        if args and args[0] == 'option-b':
            _trace(xbmc, 'python.entry', 'another_menu_active')
        return
    home.setProperty('Infinity.UI.MenuActive', '1')
    try:
        action = args[0] if args else 'restore'
        token = args[1] if len(args) > 1 else ''
        if action == 'addon': addon_menu(token)
        elif action == 'open': open_addon(token)
        elif action == 'resume': resume_menu(token)
        elif action == 'home-choice': home_continue_choice(token, args[2] if len(args) > 2 else '')
        elif action == 'option-b':
            # Only a signed C++ Home-8101/8102 touch dispatch has the
            # matching pending native item proof. Invalid/stale holds do nothing.
            from home_option_b import show_for_focused_top_poster
            if len(args) == 4:
                show_for_focused_top_poster(args[1:])
        elif action == 'restore': restore_hidden()
        else: raise ValueError('Unknown item action')
    except Exception as exc:
        xbmcgui.Dialog().ok('Infinity Item Options', str(exc))
    finally:
        home.clearProperty('Infinity.UI.MenuActive')
