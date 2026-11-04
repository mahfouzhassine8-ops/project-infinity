"""Standalone Kodi read-only Search state probe. No installation or auto-run.

Run only through an already authorized Kodi RunScript/console route. It samples
state while the user searches, never dispatches providers or changes Search.
Writes one NEW sanitized JSON report in special://temp; never overwrites data.
"""
import hashlib
import hmac
import json
import os
import re
import stat
import time
import uuid
import xml.etree.ElementTree as ET

SECONDS = 60
INTERVAL = 0.5
MAX_SAMPLES = 121
MAX_EVENTS = 256
MAX_SETTINGS_BYTES = 256 * 1024
MAX_SOURCE_BYTES = 512 * 1024
MAX_REVISION_CHARS = 64 * 1024
CC = 'script.infinity.commandcenter'
PROVIDERS = ('plugin.video.thecrew', 'script.module.thecrew', 'plugin.video.watchnixtoons2')
IDENTITY_ONLY = ('plugin.video.umbrella', 'plugin.video.seren', 'plugin.video.otaku')
REVISIONS = ('Infinity.ContinueWatchingRevision', 'Infinity.ProviderInventory.Revision',
             'Infinity.ResumeHub.PresentationSnapshot', 'widgetreload', 'widgetreload2',
             'widgetreload-movies', 'widgetreload-tvshows')
SOURCE_FILES = {
    CC: ('addon.xml', 'infinity_search.py', 'provider_inventory.py', 'NAVIGATION-CONTRACTS.json', 'SEARCH-STRUCTURES.json'),
    'plugin.video.thecrew': ('addon.xml', 'thecrew.py'),
    'script.module.thecrew': ('addon.xml', 'lib/resources/lib/modules/crew.py', 'lib/resources/lib/indexers/tvshows.py',
                            'lib/resources/lib/modules/crewruntime.py', 'lib/resources/lib/modules/settings_repair.py'),
    'plugin.video.watchnixtoons2': ('addon.xml', 'default.py', 'lib/plugin.py', 'lib/network.py', 'lib/common.py',
                                 'lib/constants.py', 'lib/sites/wcoflix.py', 'lib/sites/wcoforever.py', 'lib/sites/wcostream.py'),
}


def stamp(path):
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode): return ('unreadable',)
        return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    except FileNotFoundError:
        return ('absent',)
    except OSError:
        return ('unreadable',)


def bounded_read(path, maximum):
    before = stamp(path)
    if len(before) != 5: return before[0], None, before
    if before[2] > maximum: return 'size_limit', None, before
    try:
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != before[:2]: return 'raced', None, before
            raw = stream.read(maximum + 1)
        if len(raw) > maximum: return 'size_limit', None, before
        if stamp(path) != before: return 'raced', None, before
        return 'readable', raw, before
    except OSError:
        return 'unreadable', None, before


def category(key):
    if key == 'searchHistory': return 'search_history'
    if key == 'requestTimes': return 'request_timing'
    if key in ('orion.installed', 'orion.boolinstalled', 'orion.username', 'orion.package', 'orion.expiration'):
        return 'integration_status'
    if any(part in key.lower() for part in ('token', 'password', 'credential', 'secret', 'refresh', 'auth', 'api_key', 'api.key')):
        return 'credential_related'
    return 'configuration_or_other'


def snapshot_settings(path, salt):
    state, raw, captured_stamp = bounded_read(path, MAX_SETTINGS_BYTES)
    if raw is None: return {'state': state, 'stamp': captured_stamp}
    result = {'state': 'readable', 'stamp': captured_stamp, 'raw': hmac.digest(salt, raw, 'sha256')}
    try:
        # Kodi writes UTF-8 settings. Reject alternate encodings and all entity
        # declarations rather than letting a diagnostic expand XML entities.
        text = raw.decode('utf-8-sig')
        if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): raise ValueError('unsupported')
        root = ET.fromstring(text)
        if root.tag != 'settings' or len(root) > 4096: raise ValueError('unsupported')
        entries = {}
        for child in root:
            key = child.get('id')
            if child.tag != 'setting' or not key or key in entries or len(child): raise ValueError('unsupported')
            # Value material exists only in memory. Neither values, key names,
            # raw digests nor salted digests are copied into the report.
            encoded = json.dumps([sorted(child.attrib.items()), child.text], ensure_ascii=True).encode()
            entries[key] = hmac.digest(salt, encoded, 'sha256')
        result['entries'] = entries
        result['root_attributes'] = hmac.digest(salt, json.dumps(sorted(root.attrib.items())).encode(), 'sha256')
    except (ET.ParseError, ValueError, TypeError, UnicodeError):
        result['state'] = 'unparsed'
    return result


def delta(before, after):
    if before == after: return None
    out = {'before_state': before['state'], 'after_state': after['state'],
           'file_stamp_changed': before.get('stamp') != after.get('stamp')}
    if 'raw' in before and 'raw' in after:
        out['content_changed'] = before['raw'] != after['raw']
    if 'entries' in before and 'entries' in after:
        old, new = before['entries'], after['entries']
        counts = {}
        for key in set(old) | set(new):
            if old.get(key) != new.get(key):
                kind = category(key); counts[kind] = counts.get(kind, 0) + 1
        out['changed_key_categories'] = counts
        out['root_attributes_changed'] = before['root_attributes'] != after['root_attributes']
    return out


class KodiReader:
    """Read-only Kodi boundary; no provider imports or JSON-RPC execution."""
    def __init__(self, xbmc, xbmcaddon, xbmcgui, xbmcvfs):
        self.xbmc, self.addons, self.vfs = xbmc, xbmcaddon, xbmcvfs
        self.home = xbmcgui.Window(10000)
        self.monitor = xbmc.Monitor()

    def profile(self):
        return os.path.realpath(self.vfs.translatePath('special://profile'))

    def revision(self, name):
        return self.home.getProperty(name)

    def progress_profile(self):
        # Match Search's actual Command Center profile, not an assumed path.
        try:
            return os.path.realpath(self.vfs.translatePath(self.addons.Addon(CC).getAddonInfo('profile')))
        except Exception:
            return None

    def wait(self, seconds):
        return self.monitor.waitForAbort(seconds)

    def identity(self, aid):
        try:
            addon = self.addons.Addon(aid)
            version = addon.getAddonInfo('version')
            if not re.fullmatch(r'[0-9][A-Za-z0-9._+\-]{0,63}', version): version = 'unreported'
            root = os.path.realpath(self.vfs.translatePath(addon.getAddonInfo('path')))
            row = {'id': aid, 'version': version,
                   'enabled': self.xbmc.getCondVisibility('System.AddonIsEnabled(' + aid + ')'), 'sources': {}}
            for name in SOURCE_FILES.get(aid, ('addon.xml',)):
                path = os.path.join(root, *name.split('/'))
                if os.path.commonpath((root, os.path.realpath(path))) != root:
                    row['sources'][name] = {'state': 'outside_root'}; continue
                state, raw, _ = bounded_read(path, MAX_SOURCE_BYTES)
                row['sources'][name] = {'state': state}
                if raw is not None: row['sources'][name]['sha256'] = hashlib.sha256(raw).hexdigest()
            return row
        except Exception:
            return {'id': aid, 'state': 'unavailable'}


def observe(reader, seconds=SECONDS, clock=time.monotonic):
    if not isinstance(seconds, (int, float)) or not 1 <= seconds <= SECONDS: raise ValueError('duration')
    salt = os.urandom(32)
    started = clock(); deadline = started + seconds
    report = {'schema': 1, 'read_only': True, 'requested_seconds': seconds,
              'provider_invocations': 0, 'settings_writes': 0, 'token_reads_or_writes': 0,
              'native_request_outcome': 'NOT_OBSERVABLE_WITHOUT_REQUEST_HOOK',
              'cache_hit_and_cancellation': 'NOT_OBSERVABLE_WITHOUT_REQUEST_HOOK',
              'identities_before': [reader.identity(aid) for aid in (CC,) + PROVIDERS + IDENTITY_ONLY],
              'events': [], 'samples': 0, 'event_limit_reached': False, 'unobservable_revisions': [],
              'settings_initial_states': {}, 'continue_watching_initial_state': None}
    previous_settings = {}; previous_revisions = {}; prior_profile = None; prior_continue = None
    work_seconds = 0.0
    def event(value):
        if len(report['events']) < MAX_EVENTS: report['events'].append(value)
        else: report['event_limit_reached'] = True
    while report['samples'] < MAX_SAMPLES:
        work_start = clock(); elapsed = round(work_start - started, 3)
        profile = reader.profile()
        if prior_profile is not None and profile != prior_profile:
            event({'at_seconds': elapsed, 'kind': 'profile_changed'})
            previous_settings.clear(); prior_continue = None
        for aid in PROVIDERS:
            path = os.path.join(profile, 'addon_data', aid, 'settings.xml')
            if os.path.commonpath((profile, os.path.realpath(path))) != profile:
                if aid not in previous_settings:
                    event({'at_seconds': elapsed, 'kind': 'settings_unobservable', 'provider': aid, 'state': 'outside_profile'})
                previous_settings[aid] = {'state': 'outside_profile', 'stamp': ('outside_profile',)}
                report['settings_initial_states'].setdefault(aid, 'outside_profile')
                continue
            current_stamp = stamp(path); previous = previous_settings.get(aid)
            if previous is None or previous.get('stamp') != current_stamp or previous.get('state') == 'raced':
                current = snapshot_settings(path, salt)
                report['settings_initial_states'].setdefault(aid, current['state'])
                if previous is not None:
                    changed = delta(previous, current)
                    if changed: event(dict(at_seconds=elapsed, kind='settings_changed', provider=aid, **changed))
                previous_settings[aid] = current
        progress_profile = reader.progress_profile()
        progress_stamp = stamp(os.path.join(progress_profile, 'continue-watching.json')) if progress_profile else ('unavailable',)
        current_continue = (progress_profile, progress_stamp)
        if report['continue_watching_initial_state'] is None:
            report['continue_watching_initial_state'] = 'regular_file' if len(progress_stamp) == 5 else progress_stamp[0]
        if prior_continue is not None and current_continue != prior_continue:
            event({'at_seconds': elapsed, 'kind': 'continue_watching_file_changed'})
        for name in REVISIONS:
            value = reader.revision(name)
            if not isinstance(value, str) or len(value) > MAX_REVISION_CHARS:
                if name not in report['unobservable_revisions']: report['unobservable_revisions'].append(name)
                previous_revisions.pop(name, None)
                continue
            hashed = hmac.digest(salt, value.encode('utf-8'), 'sha256')
            if name in previous_revisions and previous_revisions[name] != hashed:
                event({'at_seconds': elapsed, 'kind': 'global_revision_changed', 'property': name})
            previous_revisions[name] = hashed
        prior_profile = profile; prior_continue = current_continue
        report['samples'] += 1
        work_seconds += max(0.0, clock() - work_start)
        remaining = deadline - clock()
        if remaining <= 0: break
        if reader.wait(min(INTERVAL, remaining)):
            report['aborted'] = True; break
    report['identities_after'] = [reader.identity(aid) for aid in (CC,) + PROVIDERS + IDENTITY_ONLY]
    report['elapsed_seconds'] = round(clock() - started, 3)
    report['sample_work_seconds'] = round(work_seconds, 6)
    report['limits'] = [
        'Sampled deltas are not a complete write history and cannot identify the writer or request.',
        'No native request status, cache hit, cancellation token or query is observed.',
        'Multiple writes between samples can coalesce; unchanged values at both endpoints do not rule out intervening changes.',
        'Known-key categories describe fields, not a decision to ignore those changes.',
        'Only the listed provider settings files are sampled; other dependencies and source changes are not continuously traced.',
        'Platform API calls may block; the loop bound cannot interrupt a blocked Kodi API.',
        'No provider, Android playback or physical acceptance test is performed.']
    return report


def write_report(directory, report):
    name = 'Infinity-Search-State-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-' + uuid.uuid4().hex[:8] + '.json'
    path = os.path.join(directory, name)
    # Exclusively create one new diagnostic file. No existing file is replaced.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=True); stream.write('\n')
    return path


def main():
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcvfs
    reader = KodiReader(xbmc, xbmcaddon, xbmcgui, xbmcvfs)
    dialog = xbmcgui.Dialog()
    dialog.notification('Infinity Search diagnostic', 'Observe only: perform your TV search during the next 60 seconds.', time=7000)
    try:
        report = observe(reader)
        directory = xbmcvfs.translatePath('special://temp')
        path = write_report(directory, report)
        dialog.notification('Infinity Search diagnostic', 'Saved ' + os.path.basename(path) + ' in special://temp.', time=10000)
        xbmc.log('Infinity Search diagnostic completed: ' + os.path.basename(path), xbmc.LOGINFO)
    except Exception:
        # Exception text can contain a private path/value. Do not log it.
        dialog.notification('Infinity Search diagnostic', 'Observation failed; no settings were changed.', time=7000)
        xbmc.log('Infinity Search diagnostic failed (details withheld for privacy).', xbmc.LOGERROR)


if __name__ == '__main__':
    main()
