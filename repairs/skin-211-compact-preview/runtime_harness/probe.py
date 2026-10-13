"""Runs ONLY inside real Kodi Python; no fake xbmcgui, no screenshot composition."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
import traceback

import xbmc
import xbmcgui
import xbmcvfs

CONFIG = json.loads(Path(xbmcvfs.translatePath('special://profile/render-config.json')).read_text())
OUT = Path(CONFIG['output'])
EVENTS = []
LOCK = threading.Lock()
PREFIX = 'Infinity.FilePreview.'


def record(event, **data):
    with LOCK:
        EVENTS.append({'event': event, 'time': time.monotonic(), **data})
        (OUT / 'events.json').write_text(json.dumps(EVENTS, indent=2) + '\n')
    xbmc.log('INFINITY_RENDER_HARNESS ' + event + ' ' + json.dumps(data), xbmc.LOGINFO)


def screenshot(name):
    dest = OUT / (name + '.png')
    xbmc.executebuiltin('TakeScreenshot(' + str(dest) + ',sync)')
    for _ in range(60):
        if dest.exists():
            record('screenshot', file=dest.name, sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
            return
        xbmc.sleep(100)
    record('screenshot-missing', file=dest.name)


def observer():
    initialized = threading.Event()
    try:
        deadline = time.monotonic() + 20
        while xbmcgui.getCurrentWindowDialogId() != 10126 and time.monotonic() < deadline:
            xbmc.sleep(50)
        record('browser-observed', dialog=xbmcgui.getCurrentWindowDialogId(), active_window=xbmcgui.getCurrentWindowId())
        if xbmcgui.getCurrentWindowDialogId() != 10126:
            raise RuntimeError('Real FileBrowser did not open')
        parent = xbmcgui.Window(10126)
        path = CONFIG['selected_zip']
        for key, value in {'NativeVersion': 'v1', 'OptIn': 'v1', 'Nonce': '1234', 'Path': path,
                           'Label': Path(path).name, 'Folder': 'false', 'Size': str(Path(path).stat().st_size),
                           'Active': 'true', 'RouteRevision': '2103376'}.items():
            parent.setProperty(PREFIX + key, value)
        # These are declared fixture inputs, not measured Android density.
        for key, value in {'Infinity.LogicalWidth': CONFIG['width'], 'Infinity.LogicalHeight': CONFIG['height'],
                           'Infinity.NativeDpWidth': CONFIG['dp_width'], 'Infinity.NativeDpHeight': CONFIG['dp_height'],
                           'Infinity.NativeWindowDpWidth': CONFIG['dp_width'], 'Infinity.NativeWindowDpHeight': CONFIG['dp_height']}.items():
            parent.setProperty(key, str(value))
        controller = Path(CONFIG['skin']) / 'resources/lib/infinity_file_preview.py'
        spec = importlib.util.spec_from_file_location('infinity_runtime_preview_subject', controller)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.PreviewDialog
        observed = []

        class ObservedDialog(original):
            def onInit(self):
                # Supply the same logical metrics real376 publishes; rendering
                # still happens in Kodi with the exact shipped XML.
                self.setProperty('Infinity.LogicalWidth', str(CONFIG['width']))
                self.setProperty('Infinity.LogicalHeight', str(CONFIG['height']))
                original.onInit(self)
                observed.append(self)
                controls = {}
                for control_id in (1, 10, 11, 12, 20, 30, 70, 80, 81, 82):
                    try:
                        control = self.getControl(control_id)
                        controls[str(control_id)] = {'x': control.getX(), 'y': control.getY(),
                                                     'w': control.getWidth(), 'h': control.getHeight()}
                    except Exception as error:
                        controls[str(control_id)] = {'error': type(error).__name__ + ': ' + str(error)}
                record('dialog-initialized', window=xbmcgui.getCurrentWindowDialogId(), controls=controls)
                initialized.set()

        module.PreviewDialog = ObservedDialog

        def capture_and_close():
            initialized.wait(12)
            xbmc.sleep(1600)
            properties = {}
            if observed:
                properties = {name: observed[-1].getProperty(name) for name in
                              ('Preview.Title', 'Preview.Subtitle', 'Preview.Summary', 'Preview.Status', 'Preview.LayoutReady')}
            record('capture-state', current_dialog=xbmcgui.getCurrentWindowDialogId(), initialized=initialized.is_set(),
                   properties=properties)
            screenshot('preview-' + CONFIG['label'] + '-' + CONFIG['theme'])
            xbmc.executebuiltin('Action(Back)')
            xbmc.sleep(500)
            screenshot('returned-' + CONFIG['label'] + '-' + CONFIG['theme'])
            xbmc.executebuiltin('Dialog.Close(all,true)')

        capture = threading.Thread(target=capture_and_close, name='RenderCapture', daemon=True)
        capture.start()
        previous = list(sys.argv)
        sys.argv = [str(controller), '10126']
        try:
            module.main()
        finally:
            sys.argv = previous
        capture.join(timeout=20)
        record('preview-returned', active=parent.getProperty(PREFIX + 'Active'), nonce=parent.getProperty(PREFIX + 'Nonce'),
               workers=[t.name for t in threading.enumerate() if t.name.startswith('InfinityZip')])
    except BaseException as error:
        record('exception', type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        screenshot('failure-' + CONFIG['label'] + '-' + CONFIG['theme'])
    finally:
        xbmc.executebuiltin('Dialog.Close(all,true)')
        xbmc.sleep(300)
        (OUT / 'done.json').write_text(json.dumps({'finished': True, 'events': len(EVENTS)}))
        xbmc.executebuiltin('Quit')


home = xbmcgui.Window(10000)
if not home.getProperty('RenderHarnessStarted'):
    home.setProperty('RenderHarnessStarted', 'true')
    theme = CONFIG['theme']
    home.setProperty('Infinity.SystemTheme', 'dark' if theme == 'cinema' else theme)
    home.setProperty('Infinity.NativeSystemTheme', 'dark' if theme == 'cinema' else theme)
    home.setProperty('Infinity.OptionalMotionAllowed', 'false')
    home.setProperty('Infinity.NativeWidthDp', str(CONFIG['dp_width']))
    home.setProperty('Infinity.NativeHeightDp', str(CONFIG['dp_height']))
    xbmc.executebuiltin('Skin.SetString(Infinity.HomeView,' + ('cinema' if theme == 'cinema' else 'normal') + ')')
    record('started', kodi=xbmc.getInfoLabel('System.BuildVersion'), skin=xbmc.getSkinDir(), config=CONFIG)
    thread = threading.Thread(target=observer, name='ActualKodiObserver', daemon=True)
    thread.start()
    try:
        xbmcgui.Dialog().browseSingle(1, 'Install from ZIP — desktop renderer fixture', 'files', '.zip',
                                     False, False, str(Path(CONFIG['selected_zip']).parent) + '/')
    except BaseException as error:
        record('browser-exception', type=type(error).__name__, message=str(error))
    thread.join(timeout=40)
    record('probe-finished')
