"""Manually launched read-only diagnostic; writes one new report only."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import uuid

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from collector import Cancelled, collect

TITLE = 'Infinity Read-only Identity Report'


def addon_info(aid):
    addon = xbmcaddon.Addon(aid)
    return dict(id=addon.getAddonInfo('id'), version=addon.getAddonInfo('version'),
                path=xbmcvfs.translatePath(addon.getAddonInfo('path')))


def write_new(folder, name, raw):
    """Unique report name only; no existing file is opened for writing."""
    destination = folder.rstrip('/\\') + '/' + name
    if xbmcvfs.exists(destination):
        raise OSError('Report filename already exists; existing file preserved')
    if os.path.isabs(destination):
        try:
            with open(destination, 'xb') as stream:
                stream.write(raw)
            with open(destination, 'rb') as stream:
                if stream.read(len(raw)+1) != raw:
                    raise OSError('New report readback did not match')
            return destination
        except FileExistsError:
            raise
        except OSError:
            if xbmcvfs.exists(destination):
                raise OSError('Report write did not complete; existing/new partial report preserved')
    # Kodi VFS can use an existing document-provider grant where direct open
    # cannot. It does not request a grant or change Android permissions.
    stream = xbmcvfs.File(destination, 'w')
    try:
        written = stream.write(raw)
        if written is not True and not (type(written) is int and written == len(raw)):
            raise OSError('Kodi could not write the complete report')
    finally:
        stream.close()
    if not xbmcvfs.exists(destination):
        raise OSError('Kodi did not confirm the new report exists')
    reader = xbmcvfs.File(destination)
    try:
        if bytes(reader.readBytes(len(raw)+1)) != raw:
            raise OSError('New report readback did not match')
    finally:
        reader.close()
    return destination


def main():
    own = xbmcaddon.Addon()
    root = Path(xbmcvfs.translatePath(own.getAddonInfo('path')))
    raw_pins = (root / 'resources/identity-pins.json').read_bytes()
    pins = json.loads(raw_pins)
    progress = xbmcgui.DialogProgress()
    progress.create(TITLE, 'Reading installed APK and active source identities. No account settings or databases are opened.')

    def update(done, total):
        if progress.iscanceled():
            raise Cancelled()
        progress.update(min(70, int(70*done/max(1, total))), 'Reading installed APK SHA-256 using Kodi’s existing access…')

    try:
        report = collect(addon_info, pins, os.environ.get('KODI_ANDROID_APK'), update)
        report.update(collected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      diagnostic_addon=own.getAddonInfo('id'), pins_sha256=hashlib.sha256(raw_pins).hexdigest(),
                      Kodi_version=xbmc.getInfoLabel('System.BuildVersion'),
                      collection_scope='Only installed APK, known code/manifests and source hashes. No account settings, credentials, tokens or databases.')
        progress.update(100, 'Identity collection finished. Saving a new JSON report…')
    except Cancelled:
        return
    except Exception as error:
        xbmcgui.Dialog().ok(TITLE, 'Collection could not finish: ' + type(error).__name__ + ': ' + str(error) + '\nNo permissions were changed.')
        return
    finally:
        progress.close()
    name = 'Infinity-Installed-Identity-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex + '.json'
    raw = (json.dumps(report, indent=2, sort_keys=True) + '\n').encode('utf-8')
    folders = []
    external = os.environ.get('EXTERNAL_STORAGE')
    if external and os.path.isabs(external):
        folders.append(external.rstrip('/') + '/Download')
    folders += ['/storage/emulated/0/Download', '/sdcard/Download']
    saved, failures = None, []
    for folder in dict.fromkeys(folders):
        try:
            if not xbmcvfs.exists(folder):
                continue
            saved = write_new(folder, name, raw)
            break
        except Exception as error:
            failures.append(type(error).__name__)
    if saved is None:
        xbmcgui.Dialog().ok(TITLE, 'Android did not allow saving to Downloads. Select a folder already accessible to Kodi, or cancel. This diagnostic does not request or bypass storage permissions.')
        folder = xbmcgui.Dialog().browse(3, 'Choose an already accessible report folder', 'files')
        if not folder:
            return
        try:
            saved = write_new(folder, name, raw)
        except Exception as error:
            xbmcgui.Dialog().ok(TITLE, 'Report was not saved: ' + type(error).__name__ + ': ' + str(error) + '\nNo permission bypass was attempted.')
            return
    apk = report['apk']
    summary = ('APK SHA-256 collected.' if apk.get('sha256') else 'APK could not be read. The report records the limitation; no APK hash was invented.')
    xbmcgui.Dialog().ok(TITLE, 'Saved:\n' + saved + '\n\n' + summary + '\nSend this JSON report for verification. This report does not clear an Infinity installation or complete the three repairs.')


if __name__ == '__main__':
    main()
