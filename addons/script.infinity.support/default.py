"""Manual support export. Never runs in the background or edits an add-on."""
from datetime import datetime
from pathlib import Path
import json
import tempfile
import uuid

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from android_logcat import collect as collect_logcat
from support import make_report

TITLE = 'Infinity Support Exporter'


def selected_appearance():
    result = {}
    for key in ('lookandfeel.skin', 'lookandfeel.font', 'lookandfeel.skincolors', 'lookandfeel.skintheme'):
        reply = json.loads(xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSettingValue',
            'params': {'setting': key}})))
        if 'result' in reply:
            result[key] = reply['result'].get('value')
    return result


def export(dialog):
    destination = dialog.browseSingle(0, 'Choose a folder to save the report', 'files')
    if not destination:
        return
    # getSkinDir is the add-on ID. System.SkinTheme is NOT the active skin ID.
    skin_id = xbmc.getSkinDir()
    skin = xbmcaddon.Addon(skin_id)
    skin_root = Path(xbmcvfs.translatePath(skin.getAddonInfo('path')))
    health_root = None
    try:
        health_root = Path(xbmcvfs.translatePath(
            xbmcaddon.Addon('script.kodihealthcenter').getAddonInfo('path')))
    except RuntimeError:
        pass
    native_roots = [Path(xbmcvfs.translatePath('special://temp/infinity-native-diagnostics'))]
    apk_assets = Path(xbmcvfs.translatePath('special://xbmc/'))
    if apk_assets.name == 'assets' and apk_assets.parent.name == 'apk' and apk_assets.parent.parent.name == 'cache':
        native_roots.append(apk_assets.parents[2] / 'files/infinity-native-diagnostics')
    has_traces = any(root.is_dir() and any(root.glob('exit-*.trace')) for root in native_roots)
    android_logcat = Path('/system/bin/logcat').is_file()
    include_traces = (has_traces or android_logcat) and dialog.yesno(TITLE,
        'Also try to collect Android crash evidence visible to this app? '
        'It may be unavailable and may contain private data. Nothing is uploaded automatically.')
    profile = Path(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
    reports = profile / 'reports'
    reports.mkdir(parents=True, exist_ok=True)
    name = 'Infinity-Support-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6] + '.zip'
    local = reports / name
    with tempfile.TemporaryDirectory(prefix='capture-', dir=str(reports)) as capture:
        logcat_status = collect_logcat(capture) if include_traces else {'status': 'not_requested'}
        receipt = make_report(local, skin_root, skin_id, selected_appearance(), health_root,
                              native_roots, include_traces, capture, logcat_status)
    target = destination.rstrip('/\\') + '/' + name
    if not xbmcvfs.copy(str(local), target) or not xbmcvfs.exists(target):
        dialog.ok(TITLE, 'Report created, but the chosen folder was not writable. Local copy:\n' + str(local))
        return
    if xbmcvfs.Stat(target).st_size() != local.stat().st_size:
        raise RuntimeError('Destination report is incomplete; original kept in exporter profile')
    # A successfully exported copy means a second local copy is unnecessary.
    if str(local) != target:
        local.unlink()
    message = 'Saved ' + skin_id + ' report:\n' + target
    if receipt['omitted']:
        message += '\nSome files were omitted; report.json lists them.'
    if not receipt['native_evidence_present']:
        message += '\nNo Android crash evidence was available. Skin report is still useful.'
    dialog.ok(TITLE, message)


def main():
    dialog = xbmcgui.Dialog()
    if not dialog.yesno(TITLE,
            'Create a small report of the active skin XML, appearance choices, and Health Center code? '
            'Account settings folders, media, and full Kodi logs are excluded. '
            'Skin/source files may contain embedded URLs. Review before sharing. Nothing is uploaded.'):
        return
    try:
        export(dialog)
    except Exception as error:
        xbmc.log('[InfinitySupport] Export failed: ' + type(error).__name__, xbmc.LOGERROR)
        dialog.ok(TITLE, 'Export did not finish: ' + type(error).__name__ + '. Your setup was not changed.')


if __name__ == '__main__':
    main()
