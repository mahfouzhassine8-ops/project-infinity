"""Optional, manually started, finite Videos observation; NOT in the overlay.

No URL, title, setting value other than numeric view, credential or media identity
is logged. Path fingerprints use an unexported per-run random key. SQLite is
read-only/query-only with zero lock wait. No settings/provider/player changes.
"""
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from urllib.parse import quote, urlsplit, urlunsplit, parse_qs

VIEWS = (50, 51, 52, 53, 55, 56, 57, 58, 59, 500, 501, 502, 503, 504, 505, 506, 507, 509, 591, 592, 602, 609)
CONTENTS = ('movies', 'tvshows', 'sets', 'seasons', 'episodes', 'musicvideos', 'videos', 'files', 'addons')


def numeric(value):
    return int(value) if re.fullmatch(r'\d{1,7}', str(value)) else None


def route(path, key):
    parts = urlsplit(path)
    provider = parts.netloc if parts.scheme == 'plugin' and re.fullmatch(r'plugin\.video\.[a-zA-Z0-9_.-]+', parts.netloc) else None
    pages = parse_qs(parts.query).get('page', [])
    return {'provider': provider,
            'path_token': hmac.new(key, path.encode(), hashlib.sha256).hexdigest()[:24],
            'page': numeric(pages[0]) if len(pages) == 1 else None}


def saved_view(database, path, skin):
    # Match exact current URL plus native normal trailing-path-slash variant.
    # Complex provider URL options may not match; absence is explicitly unknown.
    parts = urlsplit(path)
    slash = urlunsplit(parts._replace(path=parts.path.rstrip('/') + '/'))
    try:
        conn = sqlite3.connect('file:' + quote(str(database), safe='/') + '?mode=ro', uri=True, timeout=0)
        try:
            conn.execute('PRAGMA query_only=ON')
            rows = conn.execute('SELECT viewMode, skin FROM view WHERE window=? AND path IN (?,?) LIMIT 8',
                                (10025, path, slash)).fetchall()
            return {'status': 'read-only-match' if rows else 'no-exact-match',
                    'rows': [{'view_id': int(v) & 65535, 'skin_matches': s == skin} for v, s in rows]}
        finally:conn.close()
    except (sqlite3.Error, ValueError, OSError):
        return {'status': 'unavailable', 'rows': []}


def main():
    import xbmc
    import xbmcgui
    import xbmcvfs
    monitor = xbmc.Monitor()
    key = secrets.token_bytes(32)
    directory = Path(xbmcvfs.translatePath('special://temp/'))
    output = directory / ('infinity-view-probe-' + secrets.token_hex(6) + '.jsonl')
    database = Path(xbmcvfs.translatePath('special://database/ViewModes6.db'))
    started = time.monotonic()
    previous = None
    with output.open('x') as stream:
        for _ in range(180):
            if monitor.abortRequested():break
            if xbmc.getSkinDir() == 'skin.infinity.diggz' and xbmcgui.getCurrentWindowId() == 10025:
                path = xbmc.getInfoLabel('Container.FolderPath')
                row = route(path, key)
                row.update(window=10025, dialog=xbmcgui.getCurrentWindowDialogId(),
                           current_view=next((v for v in VIEWS if xbmc.getCondVisibility('Control.IsVisible(%s)' % v)), None),
                           global_view=numeric(xbmc.getInfoLabel('Skin.String(Infinity.MediaView.Default)')),
                           content=next((c for c in CONTENTS if xbmc.getCondVisibility('Container.Content(%s)' % c)), 'unknown'),
                           updating=bool(xbmc.getCondVisibility('Container.IsUpdating')))
                state = json.dumps(row, sort_keys=True)
                if state != previous:
                    previous = state
                    row['elapsed_ms'] = int((time.monotonic() - started) * 1000)
                    row['native_preference'] = saved_view(database, path, xbmc.getSkinDir())
                    stream.write(json.dumps(row, sort_keys=True) + '\n');stream.flush()
            if monitor.waitForAbort(1):break


if __name__ == '__main__':main()
