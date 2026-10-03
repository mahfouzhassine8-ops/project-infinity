# SPDX-License-Identifier: GPL-2.0-or-later
"""Publish existing Kodi weather for Android Choose Your Experience. Local files only."""
import json
import os
import time

SOURCE = 'Kodi.Weather'
MAX_AGE_MS = 24 * 60 * 60 * 1000


def reading(kodi, now_ms):
    # This service is started by Kodi's add-on manager after native initialization.
    # Never launch a weather provider, change its settings, or contact a network API.
    if not kodi.getCondVisibility('Weather.IsFetched'):
        return None
    labels = ('Weather.Location', 'Weather.Temperature', 'Weather.Conditions', 'Weather.FanartCode')
    values = {name: str(kodi.getInfoLabel(name) or '').strip() for name in labels}
    if any(not values[name] for name in labels[:3]):
        return None
    if values['Weather.Temperature'].upper() in ('N/A', 'NA', 'BUSY', '?'):
        return None
    if any(len(value) > 512 for value in values.values()):
        return None
    return {'schema': 1, 'source': SOURCE, 'captured_at_ms': now_ms, 'result': values}


def publish(kodi, target, monitor, now_ms=None):
    if monitor.abortRequested():
        return False
    try:
        snapshot = reading(kodi, int(time.time() * 1000) if now_ms is None else now_ms)
        if snapshot is None or monitor.abortRequested():
            return False
        parent = os.path.dirname(target)
        os.makedirs(parent, exist_ok=True)
        temporary = target + '.pending'
        with open(temporary, 'w', encoding='utf-8') as out:
            json.dump(snapshot, out, ensure_ascii=False, separators=(',', ':'))
            out.flush()
            os.fsync(out.fileno())
        if monitor.abortRequested():
            os.remove(temporary)
            return False
        os.replace(temporary, target)
        return True
    except (OSError, ValueError, TypeError, RuntimeError):
        # Weather failure never changes the provider, existing reading, or Kodi UI.
        return False


def main(kodi, target):
    monitor = kodi.Monitor()
    while not monitor.abortRequested():
        publish(kodi, target, monitor)
        if monitor.waitForAbort(30):
            break


if __name__ == '__main__':
    import xbmc
    from snapshot_config import SNAPSHOT_FILE
    main(xbmc, SNAPSHOT_FILE)
