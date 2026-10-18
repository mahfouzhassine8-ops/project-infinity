"""Disposable emulator observer; never installed on a user's Fold."""
import json
from pathlib import Path
import sys
import traceback
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

PROFILE = Path(xbmcvfs.translatePath('special://profile/'))
home = xbmcgui.Window(10000)
result = {}
try:
    operation = sys.argv[1] if len(sys.argv) > 1 else 'state'
    if operation == 'browse':
        home.setProperty('Infinity.BrowsePath', 'addons://sources/video')
        home.setProperty('Infinity.BrowseTitle', 'All Add-ons')
        home.setProperty('Infinity.BrowseSubtitle', 'Video Sources')
        xbmc.executebuiltin('ActivateWindow(1193)')
    elif operation == 'theme':
        home.setProperty('Infinity.SystemTheme', sys.argv[2])
        home.setProperty('Infinity.NativeSystemTheme', sys.argv[2])
    elif operation == 'home':
        xbmc.executebuiltin('ActivateWindow(home)', True)
        xbmc.executebuiltin('Skin.SetString(Infinity.VisualMode,normal)', True)
        menu = home.getControl(9000)
        count = int(xbmc.getInfoLabel('Container(9000).NumItems') or 0)
        for index in range(count):
            if xbmc.getInfoLabel('Container(9000).ListItemAbsolute(%d).Property(section)' % index) == sys.argv[2]:
                menu.selectItem(index)
                break
        else: raise RuntimeError('Requested Home section is absent')
    elif operation == 'seed':
        sys.path.insert(0, xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))
        from controller_access import load
        controller = load(); hub = controller.hub
        with controller.persistence_scope():
            data = hub.load(controller.PROFILE)
            for media in ('movie', 'tv'):
                identity = hub.media_identity(media, {'tmdb': '99999887'}, 1, 2)
                key = hub.identity_key(identity)
                data.setdefault('items', {})[key] = dict(key=key, identity=identity, media=media,
                    tmdb='99999887', season=1, episode=2, title='Infinity public UI fixture',
                    label='Infinity UI ' + media, showtitle='Infinity UI fixture',
                    position=10, duration=120, percentage=8, dbid=-1,
                    stable_source='plugin://plugin.video.infinityuitest0/?play=' + media,
                    updated=hub._now())
            hub.save(controller.PROFILE, data, hub.publish_home)
    elif operation == 'osd':
        xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
        xbmc.sleep(300)
        xbmc.executebuiltin('Action(OSD)')
    elif operation == 'rotate':
        xbmc.executebuiltin('SetFocus(263)', True)
        xbmc.executebuiltin('Action(Select)', True)
    elif operation == 'drawer':
        xbmc.executebuiltin('Skin.SetBool(Infinity.PlayerDrawerOpen)', True)
        xbmc.executebuiltin('SetFocus(270)', True)
    elif operation == 'restore':
        xbmc.executebuiltin('RunScript(script.infinity.uirepair,restore)')
    elif operation == 'choices':
        xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.infinityuitest0/,return)')
    elif operation == 'focus-choice':
        if xbmcgui.getCurrentWindowId() != 10025:
            raise RuntimeError('Fixture choices are not active')
        if not xbmcvfs.exists('special://profile/infinity-ui-fixture.mp4'):
            raise RuntimeError('Generated fixture is not visible through the application profile VFS')
        count = int(xbmc.getInfoLabel('Container(50).NumAllItems') or 0)
        matches = [i for i in range(count) if
                   xbmc.getInfoLabel('Container(50).ListItemAbsolute(%d).Label' % i) == 'Infinity UI public movie']
        if len(matches) != 1:
            raise RuntimeError('Public fixture choice is missing or ambiguous')
        xbmc.executebuiltin('SetFocus(50,%d,absolute)' % matches[0], True)
    elif operation != 'state':
        raise ValueError(operation)
    xbmc.sleep(350)
    window_id = xbmcgui.getCurrentWindowId()
    dialog_id = xbmcgui.getCurrentWindowDialogId()
    owner_id = dialog_id if dialog_id not in (0, 9999) else window_id
    owner = xbmcgui.Window(owner_id)
    result = dict(operation=operation, window=window_id, dialog=dialog_id,
        owner=owner_id, focus=owner.getFocusId(), skin=xbmc.getSkinDir(),
        rotation=xbmc.getCondVisibility('Skin.HasSetting(Infinity.PlayerRotationUnlocked)'),
        controls={}, labels={}, popup=owner.getProperty('Infinity.UI.Popup'),
        title=owner.getProperty('Infinity.UI.Title'))
    for ident in (2, 13, 50, 100, 101, 263, 280, 8830, 8831, 39799, 40001):
        try:
            control = owner.getControl(ident)
            row = dict(position=control.getPosition(), width=control.getWidth(), height=control.getHeight(),
                       visible=xbmc.getCondVisibility('Control.IsVisible(' + str(ident) + ')'))
            if hasattr(control, 'size'):
                # Another Python interpreter's WindowXMLDialog list wrapper
                # has an empty local vector even when the native GUI shows
                # populated rows. Read native absolute list items, as the
                # existing Rails observer does; never infer an empty menu.
                # Absolute indexing includes the parent-folder row; NumItems
                # excludes it. NumAllItems matches the actual native vector.
                count = int(xbmc.getInfoLabel('Container(%d).NumAllItems' % ident) or 0)
                current = xbmc.getInfoLabel('Container(%d).CurrentItem' % ident)
                row.update(size=count, python_wrapper_size=control.size(),
                    selected=int(current)-1 if current.isdecimal() else -1,
                    item_source='native-container-infolabels',
                    items=[dict(label=xbmc.getInfoLabel('Container(%d).ListItemAbsolute(%d).Label' % (ident,i)),
                                kind=xbmc.getInfoLabel('Container(%d).ListItemAbsolute(%d).Property(Infinity.UI.Kind)' % (ident,i)),
                                token=xbmc.getInfoLabel('Container(%d).ListItemAbsolute(%d).Property(Infinity.UI.Token)' % (ident,i)))
                           for i in range(min(count, 30))])
            result['controls'][str(ident)] = row
        except Exception as exc:
            result['controls'][str(ident)] = dict(error=str(exc))
    # Inactive Home controls retain old geometry; System.ScreenWidth/Height
    # describe the display mode, which can differ from a resized app surface.
    # Window.getWidth/getHeight read this active window's GetCoordsRes(), the
    # same coordinate space used by its controls and full-screen backdrop.
    result['viewport'] = [owner.getWidth(), owner.getHeight()]
    result['viewport_source'] = 'active-window-GetCoordsRes'
    result['display_mode'] = [xbmc.getInfoLabel('System.ScreenWidth'),
                              xbmc.getInfoLabel('System.ScreenHeight')]
    result['sample'] = dict(path=xbmcvfs.translatePath('special://profile/infinity-ui-fixture.mp4'),
                           exists=xbmcvfs.exists('special://profile/infinity-ui-fixture.mp4'))
    for ident in (50, 8830, 8831):
        for suffix in ('ListItem.Property(Infinity.UI.Token)', 'ListItem.Label', 'NumItems', 'Position', 'CurrentPage'):
            key = 'Container(' + str(ident) + ').' + suffix
            result['labels'][key] = xbmc.getInfoLabel(key)
    result['labels']['Container.FolderPath'] = xbmc.getInfoLabel('Container.FolderPath')
except Exception:
    result['error'] = traceback.format_exc()
result['request'] = sys.argv[-1]
target = PROFILE / 'infinity-ui-observation.json'
temporary = target.with_suffix('.tmp')
temporary.write_text(json.dumps(result, indent=2))
temporary.replace(target)
