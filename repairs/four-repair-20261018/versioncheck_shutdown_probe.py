"""Targeted Version Check evidence on disposable API37, with original Close gates.

The app-side helper reads path metadata as the actual Kodi UID. It never
executes lsb_release or any other child. Diagnostics are not durability proof.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time

ADDON = 'service.xbmc.versioncheck'
DIAGNOSTIC = 'script.infinity.versioncheckdiagnostic'
SERVICE = 'resources/lib/version_check/service.py'
FAVOURITE = 'Infinity Version Check shutdown probe'
DESTINATION = 'plugin://plugin.video.infinityuitest0/'

DIAGNOSTIC_SOURCE = r'''import errno, hashlib, json, os, stat, sys
import xbmc, xbmcaddon, xbmcvfs
addon = xbmcaddon.Addon('service.xbmc.versioncheck')
target = xbmcvfs.translatePath('special://profile/infinity-versioncheck-paths.json')
def observe(path):
    result = {'path': path}
    for label, operation in (
        ('lstat', lambda: os.lstat(path)), ('stat', lambda: os.stat(path))):
        try:
            value = operation()
            result[label] = {'dev': value.st_dev, 'ino': value.st_ino,
                             'mode': value.st_mode, 'uid': value.st_uid, 'gid': value.st_gid}
        except OSError as error:
            result[label] = {'errno': error.errno, 'error': str(error)}
    try:
        value = os.statvfs(path)
        result['statvfs'] = {'flags': value.f_flag,
                            'readonly': bool(value.f_flag & getattr(os, 'ST_RDONLY', 1))}
    except OSError as error:
        result['statvfs'] = {'errno': error.errno, 'error': str(error)}
    if stat.S_ISLNK(result.get('lstat', {}).get('mode', 0)):
        try: result['symlink'] = os.readlink(path)
        except OSError as error: result['symlink_error'] = {'errno': error.errno}
    return result
paths = os.environ.get('PATH', '')
try: cwd = os.getcwd()
except OSError as error: cwd = {'errno': error.errno, 'error': str(error)}
try: mount_namespace = {'target': os.readlink('/proc/self/ns/mnt')}
except OSError as error: mount_namespace = {'errno': error.errno, 'error': str(error)}
rows = []
for entry in paths.split(':'):
    if not os.path.isabs(entry) and not isinstance(cwd, str):
        rows.append({'path_entry': entry, 'candidate_unresolved': cwd})
        continue
    directory = os.path.normpath(entry if os.path.isabs(entry) else os.path.join(cwd, entry))
    candidate = os.path.join(directory, 'lsb_release')
    parents = []
    parent = directory
    while True:
        parents.append(observe(parent))
        if parent == '/': break
        parent = os.path.dirname(parent)
    rows.append({'path_entry': entry, 'candidate': observe(candidate), 'parents': parents})
source = os.path.join(addon.getAddonInfo('path'), 'resources/lib/version_check/service.py')
with open(source, 'rb') as stream: service_sha256 = hashlib.sha256(stream.read()).hexdigest()
result = {'schema': 1, 'owner': sys.argv[1], 'pid': os.getpid(), 'uid': os.getuid(),
          'scope': 'read-only metadata from actual Kodi interpreter; no child execution',
          'sys_platform': sys.platform, 'android': xbmc.getCondVisibility('System.Platform.Android'),
          'path': paths, 'cwd': cwd,
          'loader_environment_names': sorted(name for name in os.environ
                                             if name.startswith(('LD_', 'DYLD_'))),
          'mount_namespace': mount_namespace, 'path_candidates': rows,
          'addon_path': addon.getAddonInfo('path'), 'addon_version': addon.getAddonInfo('version'),
          'service_sha256': service_sha256,
          'settings': {key: addon.getSetting(key) for key in ('versioncheck_enable', 'upgrade_apt')}}
with open(target + '.tmp', 'w') as stream: json.dump(result, stream, indent=2)
os.replace(target + '.tmp', target)
'''


def require(condition, message):
    if not condition:
        raise RuntimeError('Version Check shutdown comparison: ' + message)


def stage_diagnostic(staging):
    folder = Path(staging) / DIAGNOSTIC
    folder.mkdir()
    (folder / 'addon.xml').write_text(
        '<addon id="' + DIAGNOSTIC + '" name="Version Check readonly CI evidence" '
        'version="1.0.0" provider-name="Infinity CI">'
        '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
        '<extension point="xbmc.python.script" library="default.py"/>'
        '<extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable evidence</summary>'
        '<description lang="en_GB">Actual app UID path observations without child execution</description>'
        '<platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (folder / 'default.py').write_text(DIAGNOSTIC_SOURCE)
    return folder


def _save(out, name, value):
    (Path(out) / name).write_text(json.dumps(value, indent=2) + '\n')


def _command(*args, timeout=15):
    """Keep diagnostics' exit codes/errors; no shell output masquerades as proof."""
    try:
        result = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=timeout)
        return {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as error:
        def decode(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
        return {'returncode': None, 'timed_out': True,
                'stdout': decode(error.stdout), 'stderr': decode(error.stderr)}


def _same_live_owner(probe, owner):
    if not owner or not isinstance(owner.get('pid'), int):
        return False
    current = probe.read_json(probe.PRIVATE + '/files/infinity-kodi-process.json')
    return (current.get('owner') == owner.get('owner') and current.get('pid') == owner['pid'] and
            any(row['pid'] == owner['pid'] and str(row['uid']) == str(probe.APP_UID) and
                row['name'] == probe.PACKAGE + ':kodi' for row in probe.processes()))


def _settings(probe):
    path = probe.PROFILE + '/addon_data/' + ADDON + '/settings.xml'
    # Hash original bytes, without universal-newline conversion of XML.
    result = subprocess.run(['adb', 'exec-out', 'cat', path],
                            capture_output=True, timeout=15)
    stderr = result.stderr.decode(errors='replace')
    exists = True if result.returncode == 0 else False if 'No such file or directory' in stderr else None
    return {'path': path, 'exists': exists,
            'sha256': hashlib.sha256(result.stdout).hexdigest() if result.returncode == 0 else None,
            'bytes': len(result.stdout) if result.returncode == 0 else None,
            'returncode': result.returncode, 'stderr': stderr}


def before_close(probe, out, report, args):
    owner = report['native_owner']
    require(probe.shell('getprop', 'ro.kernel.qemu').strip() == '1', 'disposable emulator required')
    require(report['android_platform']['sdk'] == '37', 'actual API37 required')
    require(_same_live_owner(probe, owner), 'original engine owner changed before comparison')
    require(args.versioncheck_expected_version and args.versioncheck_expected_service_sha,
            'exact Version Check identity is required')
    details = probe.rpc('Addons.GetAddonDetails',
                        {'addonid': ADDON, 'properties': ['version', 'enabled']})['addon']
    require(details['enabled'], 'Version Check must remain enabled')
    require(details['version'] == args.versioncheck_expected_version, 'unexpected Version Check version')
    info = probe.rpc('Addons.GetAddonDetails',
                     {'addonid': DIAGNOSTIC, 'properties': ['enabled']})['addon']
    if not info['enabled']:
        require(probe.rpc('Addons.SetAddonEnabled', {'addonid': DIAGNOSTIC, 'enabled': True}) == 'OK',
                'cannot enable disposable read-only evidence helper')
    require(probe.rpc('Addons.ExecuteAddon',
                     {'addonid': DIAGNOSTIC, 'params': [owner['owner']], 'wait': False}) == 'OK',
            'cannot request app UID path observations')
    deadline = time.monotonic() + 60
    observation = {}
    while time.monotonic() < deadline:
        observation = probe.read_json(probe.PROFILE + '/infinity-versioncheck-paths.json')
        if observation.get('owner') == owner['owner'] and observation.get('pid') == owner['pid']:
            break
        time.sleep(.25)
    _save(out, 'VERSIONCHECK-APP-PATHS.json', observation)
    require(observation.get('owner') == owner['owner'] and observation.get('pid') == owner['pid'],
            'app UID observation missing or belongs to a different engine')
    require(str(observation['uid']) == str(probe.APP_UID) and observation['android'],
            'path observation not produced by actual Android application UID')
    require(observation['addon_version'] == args.versioncheck_expected_version and
            observation['service_sha256'] == args.versioncheck_expected_service_sha,
            'running addon source differs from exact comparison input')
    # Natural startup execution, not a synthetic second Version Check invocation.
    deadline = time.monotonic() + 45
    seen = []
    while time.monotonic() < deadline:
        log = probe.shell('cat', probe.PROFILE + '/../temp/kodi.log', check=False)
        seen = [line for line in log.splitlines() if ADDON in line and 'runner.py' in line]
        if seen:
            break
        time.sleep(.5)
    (Path(out) / 'versioncheck-startup-log.txt').write_text('\n'.join(seen) + '\n')
    require(seen, 'Version Check natural startup execution not observed; no Close result can qualify it')
    require(_same_live_owner(probe, owner), 'engine changed during read-only evidence collection')
    require(probe.rpc('Favourites.AddFavourite',
                     {'title': FAVOURITE, 'type': 'window', 'window': 'videos',
                      'windowparameter': DESTINATION}) == 'OK', 'native favourite mutation failed')
    settings = _settings(probe)
    _save(out, 'VERSIONCHECK-SETTINGS-BEFORE.json', settings)
    require(settings['exists'] is not None, 'Version Check settings cannot be observed before Close')
    report['versioncheck_shutdown'] = {
        'targeted_only': True, 'full_ui_matrix_executed': False,
        'addon': details, 'app_paths': observation, 'natural_execution_log': seen,
        'owner_before': owner, 'settings_before': settings, 'favourite': DESTINATION,
        'native_shutdown_assertions_unchanged': True,
    }
    pid = str(owner['pid'])
    _save(out, 'VERSIONCHECK-ENGINE-MOUNTS.json', {
        'scope': 'root reads of the same engine mount table; app UID candidate metadata is separate',
        'mountinfo': _command('shell', 'cat', '/proc/' + pid + '/mountinfo'),
        'mount_namespace': _command('shell', 'readlink', '/proc/' + pid + '/ns/mnt'),
        'processes': probe.processes(),
    })


def after_close(probe, out, report, args):
    state = report['versioncheck_shutdown']
    current = probe.read_json(probe.PRIVATE + '/files/infinity-kodi-process.json')
    require(current.get('owner') != state['owner_before']['owner'] and
            current.get('pid') != state['owner_before']['pid'], 'reopen reused old owner')
    settings = _settings(probe)
    _save(out, 'VERSIONCHECK-SETTINGS-AFTER.json', settings)
    require(settings['exists'] == state['settings_before']['exists'] and
            settings['sha256'] == state['settings_before']['sha256'],
            'Version Check settings changed or disappeared across Close/reopen')
    favourites = probe.rpc('Favourites.GetFavourites', {'properties': ['windowparameter']})
    require(any(item.get('windowparameter') == DESTINATION and item.get('title') == FAVOURITE
                for item in favourites.get('favourites') or []), 'native favourite lost across restart')
    state.update(settings_preserved=True, native_favourite_preserved=True,
                 owner_after=current, passed=True)
    _save(out, 'VERSIONCHECK-SHUTDOWN.json', state)


def capture_failure(probe, out, report):
    """Only after failure, no close retry, no extended deadline, no process kill."""
    evidence = {'captured': False, 'scope': 'post-failure diagnostics; never acceptance'}
    owner = report.get('native_owner')
    try:
        if probe.shell('getprop', 'ro.kernel.qemu', check=False).strip() != '1':
            evidence['skipped'] = 'physical or unknown device'
        elif not _same_live_owner(probe, owner):
            evidence['skipped'] = 'original engine identity no longer live'
        else:
            pid = str(owner['pid'])
            evidence['owner_before'] = probe.read_json(probe.PRIVATE + '/files/infinity-kodi-process.json')
            evidence['maps'] = _command('shell', 'cat', '/proc/' + pid + '/maps')
            command = ('for t in /proc/' + pid + '/task/*; do echo "$t"; '
                       'cat "$t/comm" "$t/wchan" "$t/stat" 2>/dev/null; done')
            evidence['threads'] = _command('shell', command)
            if _same_live_owner(probe, owner):
                evidence['native_backtrace'] = _command('shell', 'debuggerd', '-b', pid)
                evidence['captured'] = True
            evidence['owner_after'] = probe.read_json(probe.PRIVATE + '/files/infinity-kodi-process.json')
            evidence['same_owner_after'] = _same_live_owner(probe, owner)
    except Exception as error:
        evidence['capture_error'] = str(error)
    report['failed_versioncheck_close_evidence'] = evidence
    _save(out, 'VERSIONCHECK-FAILED-ENGINE.json', evidence)
