"""Finite, native Kodi UI fixture; Linux only, no shutdown or playback test."""
import importlib.util
import json
from pathlib import Path
import time
import traceback
import xbmc
import xbmcgui

BASE = Path('/tmp/kodi-ui-runtime-qa')
config = json.loads((BASE / 'config.json').read_text())
OUT = BASE / 'evidence' / config['phase'];OUT.mkdir(parents=True, exist_ok=True)
import faulthandler
signal_log = (OUT / 'native-signal-python.log').open('w')
faulthandler.enable(file=signal_log, all_threads=True)
result = {'platform': 'upstream Linux Kodi 21.2; synthetic providers; actual signed skin plus source overlay',
          'phase': config['phase'], 'checks': [], 'observations': []}
controller = None
last_tick = 0.0
ids = (50, 51, 52, 53, 55, 56, 57, 58, 59, 500, 501, 502, 503, 504, 505, 506, 507, 509, 591, 592, 602, 609)


def tick():
    global last_tick
    now = time.monotonic()
    if controller and now - last_tick >= .5:
        last_tick = now
        return controller.tick()


def wait(predicate, seconds=12):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        tick()
        if predicate():return True
        xbmc.sleep(100)
    return False


def check(name, ok):
    result['checks'].append({'name': name, 'passed': bool(ok)})
    (OUT / 'PARTIAL.json').write_text(json.dumps(result, indent=2) + '\n')
    if not ok:raise RuntimeError(name)


def view():
    return next((i for i in ids if xbmc.getCondVisibility('Control.IsVisible(%s)' % i)), None)


def observation(label):
    result['observations'].append(dict(label=label, window=xbmcgui.getCurrentWindowId(),
        dialog=xbmcgui.getCurrentWindowDialogId(), view=view(),
        default=xbmc.getInfoLabel('Skin.String(Infinity.MediaView.Default)'),
        path=xbmc.getInfoLabel('Container.FolderPath'),
        items=xbmc.getInfoLabel('Container.NumItems'),
        title=xbmc.getInfoLabel('ListItem.Title')))


def shot(label):
    xbmc.sleep(350)
    xbmc.executebuiltin('TakeScreenshot(%s)' % (OUT / (label + '.png')))
    xbmc.sleep(250)


def mouse_click(x, y):
    import ctypes as C
    xlib = C.CDLL('libX11.so.6');xtest = C.CDLL('libXtst.so.6')
    xlib.XOpenDisplay.argtypes = [C.c_char_p];xlib.XOpenDisplay.restype = C.c_void_p
    xlib.XFlush.argtypes = [C.c_void_p];xlib.XCloseDisplay.argtypes = [C.c_void_p]
    xtest.XTestFakeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_ulong]
    xtest.XTestFakeButtonEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
    display = xlib.XOpenDisplay(None)
    if not display:raise RuntimeError('X11 test display unavailable')
    try:
        xtest.XTestFakeMotionEvent(display, -1, int(x), int(y), 0)
        xtest.XTestFakeButtonEvent(display, 1, 1, 0)
        xtest.XTestFakeButtonEvent(display, 1, 0, 0);xlib.XFlush(display)
    finally:xlib.XCloseDisplay(display)


def open_page(provider='a', page=1, content='movies'):
    url = 'plugin://plugin.video.infinityuiqa.%s/?page=%s&content=%s' % (provider, page, content)
    xbmc.executebuiltin('ActivateWindow(Videos,%s)' % url)
    check('directory-ready:%s:%s:%s' % (provider, page, content), wait(lambda:
        xbmcgui.getCurrentWindowId() == 10025 and
        xbmc.getInfoLabel('Container.FolderPath').rstrip('/') == url.rstrip('/') and
        not xbmc.getCondVisibility('Container.IsUpdating') and
        xbmc.getInfoLabel('Container.NumItems') == '9'))
    xbmc.sleep(250)


def select(view_id):
    dialog = 1130 if config['phase'] == 'baseline' else 1136
    label = xbmc.getLocalizedString({50:535, 56:31243, 55:31078, 51:31247}[view_id])
    xbmc.executebuiltin('ActivateWindow(%s)' % dialog)
    check('selector-open:%s' % view_id, wait(lambda: xbmcgui.getCurrentWindowDialogId() == 10000 + dialog))
    xbmc.executebuiltin('SetFocus(9000,0,absolute)');xbmc.sleep(250)
    for _ in range(35):
        if xbmc.getInfoLabel('Container(9000).ListItem.Label') == label:break
        xbmc.executebuiltin('Action(Down)');xbmc.sleep(65)
    check('selector-row:%s' % view_id, xbmc.getInfoLabel('Container(9000).ListItem.Label') == label)
    xbmc.executebuiltin('Action(Select)')
    if config['phase'] == 'baseline':
        xbmc.sleep(200);xbmc.executebuiltin('Dialog.Close(%s)' % dialog)
    check('selected-view:%s' % view_id, wait(lambda: view() == view_id and xbmcgui.getCurrentWindowDialogId() == 9999))


try:
    xbmc.sleep(2200)
    home = xbmcgui.Window(10000)
    home.setProperty('Infinity.Continuity.Observer', 'active')
    home.setProperty('Infinity.NativeAmbient.WriterLifecycle', 'running-optional')
    check('actual-infinity-skin', xbmc.getSkinDir() == 'skin.infinity.diggz')
    if config['phase'] != 'baseline':
        p = Path(config['helper'])
        spec = importlib.util.spec_from_file_location('ui_media_view', p)
        mod = importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        controller = mod.MediaViewPreference(xbmc, xbmcgui)
    open_page()
    if config['phase'] == 'baseline':
        select(56);shot('posters');observation('explicit-posters')
        open_page('a', 2);observation('page-2-provider-default');shot('page-2')
        check('baseline-loses-requested-global-view', view() != 56)
    elif config['phase'] == 'restart':
        check('native-skin-setting-survived-process-restart', xbmc.getInfoLabel('Skin.String(Infinity.MediaView.Default)') == '55')
        check('global-view-restored-after-process-restart', wait(lambda: view() == 55))
        xbmc.executebuiltin('SetFocus(55,1,absolute)')
        check('native-movie-title-available', wait(lambda: xbmc.getInfoLabel('ListItem.Title').startswith('Fixture movies')))
        check('native-synopsis-available', 'Synthetic browsing metadata' in xbmc.getInfoLabel('ListItem.Plot'))
        item_before = xbmc.getInfoLabel('ListItem.Title')
        select(51)
        check('selected-movie-retained-across-view-switch', xbmc.getInfoLabel('ListItem.Title') == item_before)
        check('focus-returned-to-current-container', xbmcgui.Window(10025).getFocusId() == 51)
        xbmc.executebuiltin('Action(Down)')
        check('native-arrow-navigation-after-selector-close', wait(lambda: xbmc.getInfoLabel('ListItem.Title') != item_before and xbmc.getInfoLabel('ListItem.Title').startswith('Fixture movies')))
        observation('metadata-and-focus')
        shot('restart-tri-panel')
    elif config['phase'] == 'media-write-guard':
        select(55)
        check('movie-choice-saved', xbmc.getInfoLabel('Skin.String(Infinity.MediaView.Default)') == '55')
        open_page('b', 1, 'files');select(50)
        check('file-view-selection-preserves-media-default', xbmc.getInfoLabel('Skin.String(Infinity.MediaView.Default)') == '55')
        open_page('b', 2, 'movies')
        check('movie-default-restored-after-file-browser', wait(lambda: view() == 55))
    elif config['phase'].startswith('pointer'):
        xbmc.executebuiltin('SetProperty(MediaMenu,true,Home)');xbmc.sleep(400)
        xbmc.executebuiltin('SetFocus(2000)');xbmc.sleep(200)
        check('main-view-options-focus', xbmcgui.Window(10025).getFocusId() == 2000)
        xbmc.executebuiltin('Action(Select)')
        check('main-opens-scoped-selector', wait(lambda: xbmcgui.getCurrentWindowDialogId() == 11136))
        xbmc.sleep(400)
        dialog_window = xbmcgui.Window(11136)
        check('before-button-inspection', True)
        control = dialog_window.getControl(8999)
        check('button-inspection-returned', True)
        x, y = control.getPosition()
        px = (18 + x + control.getWidth() / 2) * xbmcgui.getScreenWidth() / 1080
        py = (18 + y + control.getHeight() / 2) * xbmcgui.getScreenHeight() / 2400
        result['pointer'] = {'x':px,'y':py,'width':control.getWidth(),'height':control.getHeight()}
        shot('before-pointer-close');mouse_click(px, py)
        check('mouse-x-closes-only-nested-selector', wait(lambda: xbmcgui.getCurrentWindowDialogId() == 9999 and xbmcgui.getCurrentWindowId() == 10025))
        check('legitimate-main-options-still-open', bool(home.getProperty('MediaMenu')))
        xbmc.executebuiltin('SetFocus(8999)');xbmc.sleep(200);xbmc.executebuiltin('Action(Select)')
        check('main-x-closes-options-without-exiting-videos', wait(lambda: not home.getProperty('MediaMenu') and xbmcgui.getCurrentWindowId() == 10025))
        shot('after-main-close')
    else:
        for desired in (50, 56, 51, 55):
            select(desired);shot('selected-%s' % desired)
            check('explicit-global-setting:%s' % desired, xbmc.getInfoLabel('Skin.String(Infinity.MediaView.Default)') == str(desired))
            # Follow the real folder item so native Back history has page one;
            # ActivateWindow directly addresses a category, not a page click.
            xbmc.executebuiltin('SetFocus(%s,9,absolute)' % desired);xbmc.sleep(200)
            check('next-page-item:%s' % desired, xbmc.getInfoLabel('ListItem.Label') == 'Next page')
            xbmc.executebuiltin('Action(Select)')
            check('next-directory:%s' % desired, wait(lambda: 'page=2' in xbmc.getInfoLabel('Container.FolderPath') and not xbmc.getCondVisibility('Container.IsUpdating')))
            check('next-page:%s' % desired, wait(lambda: view() == desired))
            xbmc.executebuiltin('Action(Back)')
            check('back:%s' % desired, wait(lambda: view() == desired and 'page=1' in xbmc.getInfoLabel('Container.FolderPath')))
            open_page('b', 1)
            check('other-provider:%s' % desired, wait(lambda: view() == desired))
            xbmc.executebuiltin('Container.Refresh')
            xbmc.sleep(300)
            check('refresh:%s' % desired, wait(lambda: view() == desired and not xbmc.getCondVisibility('Container.IsUpdating')))
            open_page('b', 2, 'tvshows')
            check('tv-provider:%s' % desired, wait(lambda: view() == desired))
            open_page('a', 1)
        select(51);open_page('b', 1, 'episodes')
        check('unsupported-fallback', wait(lambda: view() == 50))
        check('fallback-preserves-global-setting', xbmc.getInfoLabel('Skin.String(Infinity.MediaView.Default)') == '51')
        open_page('a', 1);check('restore-supported-view', wait(lambda: view() == 51))
        select(55)
        xbmc.executebuiltin('ActivateWindow(1136)')
        check('close-test-panel-open', wait(lambda: xbmcgui.getCurrentWindowDialogId() == 11136))
        shot('view-selector')
        xbmc.executebuiltin('SetFocus(8999)');xbmc.sleep(200);xbmc.executebuiltin('Action(Select)')
        check('x-native-select-closes-only-panel', wait(lambda: xbmcgui.getCurrentWindowDialogId() == 9999 and xbmcgui.getCurrentWindowId() == 10025))
        xbmc.executebuiltin('ActivateWindow(1136)')
        check('back-test-panel-open', wait(lambda: xbmcgui.getCurrentWindowDialogId() == 11136))
        xbmc.executebuiltin('Action(Back)')
        check('back-closes-only-panel', wait(lambda: xbmcgui.getCurrentWindowDialogId() == 9999 and xbmcgui.getCurrentWindowId() == 10025))
        settings = BASE / 'root/usr/share/kodi/portable_data/userdata/addon_data/skin.infinity.diggz/settings.xml'
        check('native-skin-setting-written-without-shutdown', wait(lambda: settings.exists() and 'Infinity.MediaView.Default' in settings.read_text(), 10))
    observation('final')
    result['status'] = 'PASS_LINUX_FIXTURE_ONLY'
except BaseException:
    result['status'] = 'FAIL'
    result['error'] = traceback.format_exc()
    observation('failure');shot('failure')
finally:
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
