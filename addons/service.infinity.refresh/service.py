# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations
import os
import tempfile
import xbmc
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
POLICY_DIR = xbmcvfs.translatePath('special://profile/addon_data/service.infinity.refresh')
POLICY_FILE = os.path.join(POLICY_DIR, 'policy.properties')


def _value(setting_id: str, default: str) -> str:
    value = ADDON.getSetting(setting_id)
    return value if value != '' else default


def write_policy() -> None:
    os.makedirs(POLICY_DIR, exist_ok=True)
    lines = [
        'mode=' + _value('mode', 'adaptive'),
        'max_hz=' + _value('max_hz', 'auto'),
        'ui_policy=' + _value('ui_policy', 'high_refresh'),
        'video_policy=' + _value('video_policy', 'match_video'),
        'respect_battery_saver=' + str(ADDON.getSettingBool('respect_battery_saver')).lower(),
        'thermal_protection=' + str(ADDON.getSettingBool('thermal_protection')).lower(),
        '',
    ]
    fd, tmp = tempfile.mkstemp(prefix='.refresh-', dir=POLICY_DIR)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write('\n'.join(lines))
        os.replace(tmp, POLICY_FILE)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    xbmc.log('[InfinityRefresh] policy updated: ' + POLICY_FILE, xbmc.LOGINFO)


class Monitor(xbmc.Monitor):
    def onSettingsChanged(self) -> None:
        write_policy()


if __name__ == '__main__':
    monitor = Monitor()
    write_policy()
    # No high-frequency polling. Android re-evaluates policy on Infinity lifecycle,
    # window and playback events; this service only persists user choices.
    while not monitor.abortRequested():
        if monitor.waitForAbort(60):
            break
