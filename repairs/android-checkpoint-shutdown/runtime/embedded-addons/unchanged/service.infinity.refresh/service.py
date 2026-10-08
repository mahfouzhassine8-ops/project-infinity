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


def _bool(setting_id: str, default: bool) -> bool:
    value = ADDON.getSetting(setting_id)
    if value == '':
        return default
    return value.lower() == 'true'


def write_policy() -> None:
    os.makedirs(POLICY_DIR, exist_ok=True)
    selected = _value('mode', 'auto').strip().lower()
    max_hz = _value('max_hz', 'auto')
    ui_policy = _value('ui_policy', 'high_refresh')
    video_policy = _value('video_policy', 'match_video')
    respect_battery = _bool('respect_battery_saver', True)
    thermal = _bool('thermal_protection', True)
    override_battery = _bool('performance_override_battery', False)

    # Performance mode is intentionally implemented above the engine. The existing
    # native hook already understands a high-refresh request; this service translates
    # the user-facing Performance policy into that stable capability contract.
    if selected == 'performance':
        engine_mode = 'high_refresh'
        max_hz = 'highest'
        ui_policy = 'high_refresh'
        if override_battery:
            respect_battery = False
    else:
        engine_mode = selected

    lines = [
        'mode=' + engine_mode,
        'user_mode=' + selected,
        'max_hz=' + max_hz,
        'ui_policy=' + ui_policy,
        'video_policy=' + video_policy,
        'respect_battery_saver=' + str(respect_battery).lower(),
        'thermal_protection=' + str(thermal).lower(),
        'performance_override_battery=' + str(override_battery).lower(),
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
    xbmc.log('[InfinityRefresh] policy updated: mode=' + selected, xbmc.LOGINFO)


class Monitor(xbmc.Monitor):
    def onSettingsChanged(self) -> None:
        write_policy()


if __name__ == '__main__':
    monitor = Monitor()
    write_policy()
    # Android re-evaluates policy on Infinity lifecycle, window and playback events.
    # This service only persists/translates user choices and intentionally avoids busy polling.
    while not monitor.abortRequested():
        if monitor.waitForAbort(60):
            break
