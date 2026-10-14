"""Bounded local evidence collection; no input or UI mutation."""
import hashlib
import json
from pathlib import Path
import time
import zipfile

ADDONS = ('skin.infinity.diggz', 'script.infinity.rails', 'plugin.program.super.favourites', 'plugin.video.redlight')
CONTROLS = (9200, 8820, 8720, 19600, 19601)
MAX_FILE = 1024 * 1024
NO_DIALOG = (0, -1, 9999)  # Omega WINDOW_INVALID is 9999.


def snapshot(xbmc, gui):
    window, dialog = gui.getCurrentWindowId(), gui.getCurrentWindowDialogId()
    result = {'epoch_ms': int(time.time()*1000), 'window': window, 'dialog': dialog,
              'window_label': xbmc.getInfoLabel('System.CurrentWindow'),
              'control_label': xbmc.getInfoLabel('System.CurrentControl')}
    try:
        result['xml_property'] = gui.Window(dialog if dialog not in NO_DIALOG else window).getProperty('xmlfile')
    except RuntimeError:
        result['xml_property'] = ''
    # The native window-load log remains authoritative when xmlfile is absent.
    if window == 10000 and dialog in NO_DIALOG:
        try:
            result['focus'] = gui.Window(10000).getFocusId()
        except RuntimeError:
            result['focus'] = None
        result['section'] = xbmc.getInfoLabel('Container(9000).ListItem.Property(section)')
        result['controls'] = []
        for cid in CONTROLS:
            if not xbmc.getCondVisibility('Control.IsVisible(%d)' % cid):
                continue
            prefix = 'Container(%d).' % cid
            row = {'id': cid}
            for field, suffix in (('count','NumItems'),('directory','FolderPath'),('label','ListItem.Label'),
                                  ('key','ListItem.Property(Infinity.Rails.Key)'),
                                  ('section','ListItem.Property(Infinity.Rails.Section)'),
                                  ('addon','ListItem.Property(Addon.ID)'),
                                  ('dynamic','ListItem.Property(Infinity.Rails.Item)')):
                row[field] = xbmc.getInfoLabel(prefix + suffix)
            result['controls'].append(row)
    else:
        result['home_sampling'] = 'INACTIVE_NOT_SAMPLED'
    return result


def collect_files(xa, vfs):
    files, identities, unavailable = {}, {}, []
    def capture(name, path, tail=False):
        try:
            path = Path(vfs.translatePath(str(path)))
            if not path.is_file():
                unavailable.append(name)
                return
            size = path.stat().st_size
            if size > MAX_FILE and not tail:
                unavailable.append(name + ': exceeds 1 MiB bound')
                return
            with path.open('rb') as handle:
                if tail:
                    handle.seek(max(0, size - MAX_FILE))
                files[name] = handle.read(MAX_FILE)
        except (OSError, RuntimeError) as exc:
            unavailable.append(name + ': ' + type(exc).__name__)
    for aid in ADDONS:
        try:
            addon = xa.Addon(aid)
            info = {k:addon.getAddonInfo(k) for k in ('id','version','path')}
            identities[aid] = info
            root = Path(vfs.translatePath(info['path']))
            capture('installed/' + aid + '/addon.xml', root / 'addon.xml')
            relative = []
            if aid == 'script.infinity.rails':
                relative = ['resources/lib/runtime.py','resources/lib/dialog.py']
            elif aid == 'plugin.program.super.favourites':
                relative = ['menus.py','capture.py','captureLauncher.py',
                            'resources/keymaps/super_favourites_menu.xml',
                            'resources/skins/Default/720p/script-super-favourites-contextmenu.xml']
                profile = addon.getAddonInfo('profile')
                capture('profile/super-favourites/captureLauncher.py', profile.rstrip('/') + '/captureLauncher.py')
            elif aid == 'skin.infinity.diggz':
                relative = ['unified/Home.xml','unified/Includes_InfinityRails.xml',
                            'unified/DialogContextMenu.xml','unified/DialogSelect.xml','unified/Font.xml']
            for name in relative:
                capture('installed/' + aid + '/' + name, root / name)
        except (RuntimeError, OSError) as exc:
            identities[aid] = {'state':type(exc).__name__}
    for tag, base in (('system','special://xbmc/system/keymaps'),
                      ('masterprofile','special://masterprofile/keymaps'),
                      ('profile','special://profile/keymaps')):
        try:
            root = Path(vfs.translatePath(base))
            # Kodi also supports device-specific subdirectories. Include XML
            # files only, with a finite count and per-file size bound.
            paths = sorted(root.rglob('*.xml')) if root.is_dir() else []
            if not paths:
                unavailable.append('keymaps/' + tag + ': no files observed')
            for path in paths[:100]:
                capture('keymaps/' + tag + '/' + str(path.relative_to(root)), path)
            if len(paths) > 100:
                unavailable.append('keymaps/' + tag + ': truncated at 100 files')
        except (OSError, RuntimeError) as exc:
            unavailable.append('keymaps/' + tag + ': ' + type(exc).__name__)
    capture('logs/kodi.tail.log','special://logpath/kodi.log',tail=True)
    return files, identities, unavailable


def write_capture(path, report, files):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report['files'] = {name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
                       for name,data in files.items()}
    temporary = path.with_suffix('.tmp')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('capture.json', json.dumps(report,indent=2,sort_keys=True))
        for name, data in files.items():
            archive.writestr(name,data)
    temporary.replace(path)


def observe(xbmc, gui, monitor, seconds=30, clock=time.monotonic):
    """Observe transitions only during one explicit capture; never close a popup."""
    started = clock()
    events, last_signature = [], None
    seen_home, opened, closed = False, None, None
    while clock() - started < min(max(seconds,0),30):
        if monitor.abortRequested():
            break
        state = snapshot(xbmc,gui)
        signature = json.dumps({k:v for k,v in state.items() if k!='epoch_ms'},sort_keys=True)
        if signature != last_signature:
            events.append(state)
            last_signature = signature
        is_home = state['window'] == 10000 and state['dialog'] in NO_DIALOG
        if is_home:
            seen_home = True
            if opened is not None and closed is None:
                closed = clock()
        elif seen_home and opened is None:
            opened = clock()
        # Retain up to two seconds of the popup/error logs, but leave the
        # dialog open for the user to inspect and dismiss themselves.
        if opened is not None and clock() - opened >= 2:
            break
        if monitor.waitForAbort(0.1):
            break
    return {'events':events,'duration_seconds':round(clock()-started,3),
            'saw_home':seen_home,'saw_window_transition':opened is not None,
            'limits':['Window transition is not proof of a long-press action.',
                      'No native coordinates or translated action ID are available through this Python observer.',
                      'A Kodi debug log plus keymap/source inventory is needed to correlate dispatch.']}
