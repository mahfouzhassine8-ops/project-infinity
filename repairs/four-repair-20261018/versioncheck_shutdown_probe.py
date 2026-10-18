"""Targeted Version Check evidence on disposable API37, with original Close gates.

The app-side helper reads path metadata as the actual Kodi UID. It never
executes lsb_release or any other child. Diagnostics are not durability proof.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid

ADDON = 'service.xbmc.versioncheck'
DIAGNOSTIC = 'script.infinity.versioncheckdiagnostic'
SERVICE = 'resources/lib/version_check/service.py'
FAVOURITE = 'Infinity Version Check shutdown probe'
DESTINATION = 'plugin://plugin.video.infinityuitest0/'
DESCRIPTOR_DIAGNOSTIC = 'script.infinity.readonlydescriptor'
DESCRIPTOR_PREFIX = 'infinity-readonly-descriptor-'

# Reuse the ordinary read/flush/close exercised by readonly_maps_fixture.py.
# Keep the descriptor open for a bounded host-side kernel metadata observation;
# no fcntl, ioctl, buffer/raw access, syscall emulation or write exemption.
DESCRIPTOR_SOURCE = r'''import json, os, stat, sys, time
import xbmc, xbmcvfs
prefix = xbmcvfs.translatePath('special://profile/infinity-readonly-descriptor-')
result = {'schema': 1, 'scope': 'disposable API37 descriptor diagnostics; never durability authority',
          'owner': sys.argv[1], 'nonce': sys.argv[2], 'pid': os.getpid(), 'uid': os.getuid(),
          'android': xbmc.getCondVisibility('System.Platform.Android'), 'errors': [], 'stream_opened': False}
def publish(suffix, data):
    path = prefix + suffix + '.json'
    with open(path + '.tmp', 'w', encoding='utf-8') as output:
        json.dump(data, output, sort_keys=True)
    os.replace(path + '.tmp', path)
def sample(descriptor):
    identity = os.fstat(descriptor)
    with open('/proc/self/fdinfo/' + str(descriptor), encoding='utf-8') as info:
        fdinfo = info.read(16384)
    return {'dev': identity.st_dev, 'ino': identity.st_ino, 'mode': identity.st_mode,
            'nlink': identity.st_nlink, 'regular_file': stat.S_ISREG(identity.st_mode),
            'readlink': os.readlink('/proc/self/fd/' + str(descriptor)), 'fdinfo': fdinfo}
maps = None
try:
    maps = open('/proc/self/maps', encoding='utf-8')
    result['stream_opened'] = True
    descriptor = maps.fileno()
    result.update(descriptor=descriptor, mode=maps.mode, writable=maps.writable(),
                  stream_type={'module': type(maps).__module__, 'name': type(maps).__name__},
                  read_succeeded=bool(maps.readline()), before=sample(descriptor),
                  hold_limit_seconds=30, release_received=False)
    publish('pre', result)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with open(prefix + 'release.json', encoding='utf-8') as control:
                release = json.load(control)
            if all(release.get(key) == result[key] for key in ('owner', 'nonce', 'pid', 'descriptor')):
                result['release_received'] = True
                break
        except (OSError, ValueError):
            pass
        time.sleep(.05)
    result['hold_timed_out'] = not result['release_received']
    result['after_hold'] = sample(descriptor)
    result['identity_stable_while_held'] = all(
        result['before'][key] == result['after_hold'][key]
        for key in ('dev', 'ino', 'mode', 'nlink', 'readlink'))
    maps.flush()
    result['flush_completed'] = True
except Exception as error:
    result['errors'].append({'stage': 'read_hold_flush', 'type': type(error).__name__, 'error': str(error)})
finally:
    if maps is not None:
        try:
            maps.close()
            result['close_completed'] = True
        except Exception as error:
            result['errors'].append({'stage': 'close', 'type': type(error).__name__, 'error': str(error)})
    result['closed'] = maps is None or maps.closed
    result['held'] = not result['closed']
    result['read_flush_close_completed'] = bool(result.get('read_succeeded') and
                                               result.get('flush_completed') and result.get('close_completed'))
    publish('post', result)
'''

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


def startup_evidence(log, observation):
    """Use existing native/service debug messages, never demand a cleanup error."""
    runner = observation['addon_path'].rstrip('/') + '/resources/lib/runner.py'
    lines = log.splitlines()
    invoked = [line for line in lines if 'CPythonInvoker(' in line and runner in line
               and any(marker in line for marker in ('start processing', 'the source file to load is',
                                                     'script successfully run', 'failure in script'))]
    message = ('Version Check: Disabled' if observation['settings']['versioncheck_enable'] == 'false'
               else 'Version Check: Version ' + observation['addon_version'] + ' started')
    service = [line for line in lines if message in line]
    # A failed original import is a valid negative control, not a healthy-service
    # pass. The corrected arm must reach the original run()/enabled-setting path.
    corrected = observation['addon_version'] == '0.5.28+infinity.1'
    return {'native_invocation': invoked, 'service_run': service,
            'ready': bool(invoked) and (bool(service) if corrected else True)}


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


def stage_descriptor_diagnostic(staging):
    folder = Path(staging) / DESCRIPTOR_DIAGNOSTIC
    folder.mkdir()
    (folder / 'addon.xml').write_text(
        '<addon id="' + DESCRIPTOR_DIAGNOSTIC + '" name="Readonly descriptor CI evidence" '
        'version="1.0.0" provider-name="Infinity CI">'
        '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
        '<extension point="xbmc.python.script" library="default.py"/>'
        '<extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable descriptor evidence</summary>'
        '<description lang="en_GB">Bounded metadata observation; no durability authority</description>'
        '<platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (folder / 'default.py').write_text(DESCRIPTOR_SOURCE)
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


def descriptor_identity_matches(observation, owner, nonce, uid, descriptor=None):
    """Correlate the held descriptor without assuming translated/kernel flags match."""
    fd = observation.get('descriptor')
    return (observation.get('owner') == owner.get('owner') and
            observation.get('pid') == owner.get('pid') and
            str(observation.get('uid')) == str(uid) and observation.get('nonce') == nonce and
            observation.get('android') is True and type(fd) is int and fd >= 0 and
            (descriptor is None or fd == descriptor))


def descriptor_terminal_matches(observation, owner, nonce, uid, descriptor=None):
    identity = (observation.get('owner') == owner.get('owner') and
                observation.get('pid') == owner.get('pid') and observation.get('nonce') == nonce and
                str(observation.get('uid')) == str(uid) and observation.get('android') is True)
    return (identity and observation.get('closed') is True and observation.get('held') is False and
            (observation.get('stream_opened') is False or
             descriptor_identity_matches(observation, owner, nonce, uid, descriptor)))


def capture_readonly_descriptor(probe, out, report):
    """One pre-Close diagnostic only; preserve all failures and never grant Close."""
    owner = report['native_owner']
    require(probe.shell('getprop', 'ro.kernel.qemu').strip() == '1' and
            report['android_platform']['sdk'] == '37', 'descriptor diagnostic requires disposable API37')
    require(_same_live_owner(probe, owner), 'descriptor diagnostic owner changed before start')
    nonce = uuid.uuid4().hex
    evidence = {'scope': 'diagnostic only; no durability or termination authority',
                'owner': owner, 'nonce': nonce, 'captured': False, 'kernel': {}}
    report['readonly_descriptor_diagnostic'] = evidence
    prefix = probe.PROFILE + '/' + DESCRIPTOR_PREFIX

    def read(suffix):
        command = _command('exec-out', 'cat', prefix + suffix + '.json', timeout=3)
        if command.get('returncode') == 0:
            try:
                return json.loads(command['stdout']), command
            except (ValueError, KeyError):
                pass
        return {}, command

    def release(descriptor):
        if not _same_live_owner(probe, owner):
            evidence['release_skipped'] = 'original engine identity changed'
            return
        signal = {'owner': owner['owner'], 'nonce': nonce, 'pid': owner['pid'],
                  'descriptor': descriptor}
        path = Path(out) / 'readonly-descriptor-release.json'
        path.write_text(json.dumps(signal))
        evidence['release_command'] = _command('push', str(path), prefix + 'release.json', timeout=3)

    descriptor = None
    try:
        details = probe.rpc('Addons.GetAddonDetails',
                            {'addonid': DESCRIPTOR_DIAGNOSTIC, 'properties': ['enabled']})['addon']
        if not details['enabled']:
            require(probe.rpc('Addons.SetAddonEnabled',
                             {'addonid': DESCRIPTOR_DIAGNOSTIC, 'enabled': True}) == 'OK',
                    'cannot enable disposable descriptor helper')
        require(probe.rpc('Addons.ExecuteAddon',
                         {'addonid': DESCRIPTOR_DIAGNOSTIC, 'params': [owner['owner'], nonce],
                          'wait': False}) == 'OK', 'cannot execute descriptor metadata helper')
        deadline = time.monotonic() + 60
        pre = {}
        while time.monotonic() < deadline:
            pre, evidence['last_pre_read'] = read('pre')
            if descriptor_identity_matches(pre, owner, nonce, probe.APP_UID):
                break
            post, evidence['early_post_read'] = read('post')
            if post.get('nonce') == nonce:
                evidence['post'] = post
                break
            time.sleep(.25)
        evidence['pre'] = pre
        require(descriptor_identity_matches(pre, owner, nonce, probe.APP_UID),
                'held descriptor identity unavailable or mismatched')
        descriptor = pre['descriptor']
        require(_same_live_owner(probe, owner), 'engine changed before kernel descriptor reads')
        fd_path = '/proc/' + str(owner['pid']) + '/fd/' + str(descriptor)
        commands = (
            ('readlink_before', ('shell', 'readlink', fd_path)),
            ('stat', ('shell', 'stat', '-L', '-c', '%d:%i:%f:%h', fd_path)),
            ('fdinfo', ('shell', 'cat', '/proc/' + str(owner['pid']) + '/fdinfo/' + str(descriptor))),
            ('readlink_after', ('shell', 'readlink', fd_path)),
        )
        try:
            for label, command in commands:
                require(_same_live_owner(probe, owner), 'engine changed during descriptor observation')
                evidence['kernel'][label] = _command(*command, timeout=3)
        finally:
            release(descriptor)
        deadline = time.monotonic() + 40
        post = {}
        while time.monotonic() < deadline:
            post, evidence['last_post_read'] = read('post')
            if descriptor_identity_matches(post, owner, nonce, probe.APP_UID, descriptor):
                break
            time.sleep(.25)
        evidence['post'] = post
        evidence['same_live_owner_after'] = _same_live_owner(probe, owner)
        evidence['captured'] = bool(
            descriptor_identity_matches(post, owner, nonce, probe.APP_UID, descriptor) and
            evidence['same_live_owner_after'] and post.get('release_received') and
            all(evidence['kernel'].get(key, {}).get('returncode') == 0 for key, _ in commands))
        # A captured ordinary flush failure remains valid diagnostic evidence;
        # the original Close gate below decides durability, never this helper.
    except Exception as error:
        evidence['error'] = str(error)
    finally:
        # Metadata errors must not race the still-held fixture into Close.
        # The helper releases itself after30s even without an acknowledgement.
        post = evidence.get('post', {})
        try:
            deadline = time.monotonic() + 40
            while (_same_live_owner(probe, owner) and
                   not descriptor_terminal_matches(post, owner, nonce, probe.APP_UID, descriptor) and
                   time.monotonic() < deadline):
                post, evidence['terminal_post_read'] = read('post')
                if descriptor_terminal_matches(post, owner, nonce, probe.APP_UID, descriptor):
                    break
                time.sleep(.25)
            evidence['post'] = post
            evidence['terminal_confirmed'] = bool(
                _same_live_owner(probe, owner) and
                descriptor_terminal_matches(post, owner, nonce, probe.APP_UID, descriptor))
            if not evidence['terminal_confirmed']:
                evidence['collector_incomplete'] = 'same-engine terminal post with closed descriptor unavailable'
        except Exception as error:
            evidence['terminal_confirmed'] = False
            evidence['collector_incomplete'] = str(error)
        _save(out, 'READONLY-DESCRIPTOR-DIAGNOSTIC.json', evidence)
    return evidence


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
    seen = {}
    while time.monotonic() < deadline:
        log = probe.shell('cat', probe.PROFILE + '/../temp/kodi.log', check=False)
        seen = startup_evidence(log, observation)
        if seen['ready']:
            break
        time.sleep(.5)
    _save(out, 'VERSIONCHECK-NATURAL-STARTUP.json', seen)
    (Path(out) / 'versioncheck-startup-log.txt').write_text(
        '\n'.join(seen.get('native_invocation', []) + seen.get('service_run', [])) + '\n')
    require(seen.get('ready'), 'Version Check natural startup execution not observed; no Close result can qualify it')
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
    # Evidence-only correlation with the *actual* failed Close receipt. It may
    # explain the x86_64 host's ARM64 translation mismatch, but MUST NOT turn
    # CHECKPOINT_FAILED into COMPLETE or grant any durability/exit authority.
    descriptor = report.get('readonly_descriptor_diagnostic')
    if descriptor is not None:
        from translated_descriptor_evidence import assess
        try:
            receipt = json.loads((Path(out) / 'CLOSE-RECEIPT.json').read_text())
            assessment = assess(descriptor, receipt)
        except (OSError, ValueError, TypeError):
            assessment = {'classification': 'insufficient_evidence',
                          'durable_close_verified': False,
                          'can_override_native_protection': False,
                          'fold_accepted': False}
        report['translated_descriptor_assessment'] = assessment
        _save(out, 'TRANSLATED-DESCRIPTOR-ASSESSMENT.json', assessment)
