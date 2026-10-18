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
        for index in range(menu.size()):
            if menu.getListItem(index).getProperty('section') == sys.argv[2]:
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
    elif operation == 'restore':
        xbmc.executebuiltin('RunScript(script.infinity.uirepair,restore)')
    elif operation == 'choices':
        xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.infinityuitest0/,return)')
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
    for ident in (2, 50, 100, 263, 8830, 8831, 39799, 40001):
        try:
            control = owner.getControl(ident)
            row = dict(position=control.getPosition(), width=control.getWidth(), height=control.getHeight(),
                       visible=xbmc.getCondVisibility('Control.IsVisible(' + str(ident) + ')'))
            if hasattr(control, 'size'):
                row.update(size=control.size(), selected=control.getSelectedPosition(),
                    items=[dict(label=control.getListItem(i).getLabel(),
                                kind=control.getListItem(i).getProperty('Infinity.UI.Kind'),
                                token=control.getListItem(i).getProperty('Infinity.UI.Token'))
                           for i in range(min(control.size(), 20))])
            result['controls'][str(ident)] = row
        except Exception as exc:
            result['controls'][str(ident)] = dict(error=str(exc))
    try:
        viewport = home.getControl(39799)
        result['viewport'] = [viewport.getWidth(), viewport.getHeight()]
    except Exception:
        result['viewport'] = [int(xbmc.getInfoLabel('System.ScreenWidth')), int(xbmc.getInfoLabel('System.ScreenHeight'))]
    for ident in (50, 8830, 8831):
        for suffix in ('ListItem.Property(Infinity.UI.Token)', 'ListItem.Label', 'NumItems', 'Position', 'CurrentPage'):
            key = 'Container(' + str(ident) + ').' + suffix
            result['labels'][key] = xbmc.getInfoLabel(key)
except Exception:
    result['error'] = traceback.format_exc()
result['request'] = sys.argv[-1]
target = PROFILE / 'infinity-ui-observation.json'
temporary = target.with_suffix('.tmp')
temporary.write_text(json.dumps(result, indent=2))
temporary.replace(target)
