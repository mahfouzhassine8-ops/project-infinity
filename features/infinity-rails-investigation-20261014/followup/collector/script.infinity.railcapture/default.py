"""Explicit, one-shot collector. No service extension or persistent polling."""
from pathlib import Path
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from capture_core import collect_files, observe, write_capture

ADDON = xbmcaddon.Addon('script.infinity.railcapture')
PROFILE = Path(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')))


def main():
    previous = sorted(PROFILE.glob('Infinity-Rail-Hold-*.zip')) if PROFILE.exists() else []
    options = ['Capture one rail hold (30 seconds maximum)']
    if previous:
        options.append('Export latest capture')
    options.append('Cancel')
    choice = xbmcgui.Dialog().select('Infinity Rail Hold Capture — diagnostic only', options)
    if previous and choice == 1:
        folder = xbmcgui.Dialog().browse(3,'Choose a folder to save the capture ZIP','files')
        if folder:
            destination = folder.rstrip('/\\') + '/' + previous[-1].name
            if xbmcvfs.copy(str(previous[-1]),destination):
                xbmcgui.Dialog().ok('Capture exported',destination)
            else:
                xbmcgui.Dialog().ok('Export failed','Choose another writable folder. The capture is retained.')
        return
    if choice != 0:
        return
    xbmcgui.Dialog().ok('Capture the failed hold',
        'After OK, Home opens. Press and hold the affected rail card ONCE. '
        'Leave the popup visible for two seconds, then dismiss it normally. '
        'This tool stops automatically. Run it again and select Export latest capture. '
        'If possible, enable Kodi debug logging first; this tool does not change that setting.')
    monitor = xbmc.Monitor()
    capture_id = time.strftime('%Y%m%d-%H%M%S')
    xbmc.log('Infinity Rail Hold Capture BEGIN '+capture_id,xbmc.LOGINFO)
    xbmc.executebuiltin('ActivateWindow(Home)')
    report = observe(xbmc,xbmcgui,monitor)
    report.update(schema=1,capture_id=capture_id,diagnostic_only=True,device_acceptance=False)
    # Never perform source inventory or zip work during a shutdown request.
    if monitor.abortRequested():
        return
    files, identities, unavailable = collect_files(xbmcaddon,xbmcvfs)
    report.update(installed=identities,unavailable=unavailable)
    target = PROFILE / ('Infinity-Rail-Hold-' + capture_id + '.zip')
    write_capture(target,report,files)
    xbmc.log('Infinity Rail Hold Capture SAVED '+capture_id,xbmc.LOGINFO)
    xbmcgui.Dialog().notification('Rail capture saved','Dismiss the popup, then run this tool again to export.',time=6000)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        xbmc.log('Infinity Rail Hold Capture ERROR: '+str(exc),xbmc.LOGERROR)
        xbmcgui.Dialog().ok('Capture could not finish',str(exc))
