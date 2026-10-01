"""Deterministic edits against verified Command Center .17; never edits the input."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'controller/script.infinity.commandcenter'
out=ROOT/'candidate/script.infinity.commandcenter'
if out.exists(): shutil.rmtree(out)
shutil.copytree(source,out,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))

def edit(file,old,new,count=1):
    p=out/file;s=p.read_text()
    found=s.count(old)
    assert found==count,(file,found,old[:100])
    p.write_text(s.replace(old,new))

edit('experience.py','import time\n','import time\nimport threading\n')
edit('experience.py',"        self.recovery = None\n        self.retry_count = 0", "        self.recovery = None\n        self.retry_lock = threading.RLock()\n        self.retry_count = 0")
edit('experience.py',"            data.get(collection, {}).pop(key, None)\n            self.api['save_continue'](self.profile, data)","""            data.get(collection, {}).pop(key, None)
            if collection == 'sources':
                # The progress row and current item contain a compatibility copy.
                # Forgetting one copy must not resurrect it on the next save.
                entry = data.get('items', {}).get(key)
                if isinstance(entry, dict):
                    entry.pop('stable_source', None)
                if self.player.cw_item and self.player.cw_item.get('key') == key:
                    self.player.cw_item.pop('stable_source', None)
            self.api['save_continue'](self.profile, data)""")
edit('experience.py',"    def on_started(self):\n        item = self.player.cw_item\n        if not item:\n            return\n        if self.xbmc.getCondVisibility('Pvr.IsPlayingTV | Pvr.IsPlayingRadio'):\n            return", """    def cancel_recovery(self, status='unavailable'):
        with self.retry_lock:
            self.recovery = None
            self.seek_pending = None
            self.recovery_notice = False
            self.publish('Recovery.Available', 'false')
            self.publish('Recovery.Status', status)

    def on_started(self):
        item = self.player.cw_item
        if not item or self.xbmc.getCondVisibility('Pvr.IsPlayingTV | Pvr.IsPlayingRadio'):
            # Do not carry a movie retry or seek into an unidentified/live session.
            self.cancel_recovery('playing')
            return""")
edit('experience.py',"        if self.origin and time.monotonic() - self.origin['at'] < 20:","        if not route and self.origin and time.monotonic() - self.origin['at'] < 20:")
edit('experience.py',"        item = dict(self.player.cw_item or {})\n        if self.xbmc.getCondVisibility", "        self.cancel_recovery()\n        if self.api['str']('playback_recovery', 'prompt') == 'off':\n            return\n        item = dict(self.player.cw_item or {})\n        if self.xbmc.getCondVisibility")
edit('experience.py',"            saved = data.get('items', {}).get(item['key'], {})", "            saved = data.get('items', {}).get(item['key'], {})\n            if not isinstance(saved, dict):\n                saved = {}")
start=(out/'experience.py').read_text().index('    def retry(self):')
end=(out/'experience.py').read_text().index('    def capture_session(self):',start)
p=out/'experience.py';s=p.read_text();s=s[:start]+'''    def retry(self):
        # Reserve exactly one in-flight open. The RPC is outside the lock so a
        # playback callback cannot deadlock behind an Android/Kodi response.
        with self.retry_lock:
            if self.api['str']('playback_recovery', 'prompt') == 'off':
                self.cancel_recovery('disabled')
                return False
            if (not self.recovery or self.retry_count >= 2 or self.player.isPlaying()
                    or self.seek_pending is not None
                    or self.xbmc.getCondVisibility('Pvr.IsPlayingTV | Pvr.IsPlayingRadio')):
                return False
            if time.monotonic() - self.recovery['at'] > 300:
                self.cancel_recovery('expired')
                return False
            record = self.recovery
            self.retry_count += 1
            self.publish('Recovery.Status', 'retrying')
            self.publish('Recovery.Available', 'false')
            pending = dict(record, ready=False, started=time.monotonic())
            self.seek_pending = pending
        result = self.api['rpc']('Player.Open', {'item': {'file': record['route']}})
        with self.retry_lock:
            if 'error' in result:
                # A newer callback may already own recovery. A delayed response
                # from this open must not clear that newer session's state.
                if self.seek_pending is pending:
                    self.seek_pending = None
                    self.publish('Recovery.Status', 'failed')
                    self.publish('Recovery.Available', 'true' if self.retry_count < 2 else 'false')
                return False
        return True

'''+s[end:];p.write_text(s)
edit('experience.py',"        if win not in names or time.time() - number(saved.get('updated')) > 604800:","        if type(win) is not int or win not in names or time.time() - number(saved.get('updated')) > 604800:")
edit('experience.py',"        if manual:\n            view =", "        if manual and isinstance(saved.get('view'), str):\n            view =")
edit('experience.py',"        self.last_tick = now\n        if self.recovery_notice:","        self.last_tick = now\n        if self.api['str']('playback_recovery', 'prompt') == 'off':\n            self.cancel_recovery('disabled')\n        if self.recovery_notice:")
edit('experience.py',"                self.publish('Recovery.Status', 'failed')\n            elif pending.get('ready')", "                self.publish('Recovery.Status', 'failed')\n                self.publish('Recovery.Available', 'true' if self.recovery and self.retry_count < 2 else 'false')\n            elif pending.get('ready')")
edit('experience.py',"            if now > saved['expires'] or playing:","            if now > saved['expires'] or playing or self.gui.getCurrentWindowDialogId() != 9999:")

p=out/'plugin.py';s=p.read_text();start=s.index('def _target(');end=s.index('\n\ndef listing',start)
s=s[:start]+'''def _target(entry, sources=None):
    preference = sources.get(entry.get('key'), {}) if isinstance(sources, dict) else {}
    if not isinstance(preference, dict):
        preference = {}
    preferred = stable_route(preference.get('route') or entry.get('stable_source', ''))
    failed = number(preference.get('failures')) >= 2

    def available(route):
        if route.startswith('plugin://'):
            host = route.split('/')[2]
            return bool(xbmc.getCondVisibility('System.HasAddon(%s)' % host))
        return bool(route)

    if setting_bool('source_memory_enabled', True) and preferred and not failed and available(preferred):
        return preferred
    tmdb = str(entry.get('tmdb') or '').strip()
    media = entry.get('media')
    if tmdb.isdigit() and _has_tmdb_helper():
        if media == 'tv':
            season = str(int(number(entry.get('season'))))
            episode = str(int(number(entry.get('episode'))))
            return ('plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=tv&tmdb_id=' + tmdb +
                    '&season=' + season + '&episode=' + episode)
        return 'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=movie&tmdb_id=' + tmdb
    source = str(entry.get('source') or '').strip()
    stable = stable_route(source)
    if stable:
        # The original-source fallback must obey the same failure and provider
        # gates as preference selection. Otherwise it reopens the rejected route.
        if available(stable) and not (failed and stable == preferred):
            return stable
        return ''
    # Keep the existing short-lived direct-stream fallback only for a recent,
    # otherwise unfailed record. No arbitrary builtin or opaque path is playable.
    age = time.time() - number(entry.get('updated'))
    if (not failed and 0 <= age < 21600 and source.startswith(('https://', 'http://'))
            and not any(c in source for c in '\\r\\n\\x00')):
        return source
    return ''
'''+s[end:];p.write_text(s)
edit('service.py','import json\n','import json\nimport math\n')
edit('service.py','from experience import ExperienceController','from experience import ExperienceController, number')
edit('service.py','    def onAVStarted(self):\n        self.cw_item = None', '''    def onAVStarted(self):
        # Track observations belong to the preceding semantic key until a fresh
        # Kodi response exists. Never store them under the next title's key.
        self.persist()
        self.restore_pending = False
        self.cw_pending = False
        self.cw_item = None''')
edit('service.py',"        if self.isPlayingVideo() and setting_bool('continue_watching_enabled', True):\n            if self.cw_pending or not self.cw_item:\n                self._arm_continue()\n            self.persist_continue(completed=False, force=False)","""        if self.isPlayingVideo() and (setting_bool('continue_watching_enabled', True)
                or setting_bool('source_memory_enabled', True)
                or setting_str('playback_recovery', 'prompt') != 'off'):
            if self.cw_pending or not self.cw_item:
                if self._arm_continue() and self.experience:
                    self.experience.on_started()
            self.persist_continue(completed=False, force=False)""")
edit('service.py',"        log('Continue Watching armed for ' + item.get('label', 'video'))", "        log('Continue Watching armed for ' + item.get('label', 'video'))\n        return True")
edit('service.py',"            position = max(0.0, float(self.getTime()))\n            duration = max(0.0, float(self.getTotalTime()))", """            raw_position, raw_duration = float(self.getTime()), float(self.getTotalTime())
            if not math.isfinite(raw_position) or not math.isfinite(raw_duration):
                # An invalid clock is not evidence that a title was completed.
                return
            position, duration = max(0.0, raw_position), max(0.0, raw_duration)""")
edit('service.py',"abs(float(prior.get('position', 0.0) or 0.0) - position)","abs(number(prior.get('position'), -1.0) - position)")
print(out)
