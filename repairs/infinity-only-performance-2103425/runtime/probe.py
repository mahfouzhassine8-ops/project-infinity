"""One focused journey on a disposable Android17 emulator; APK remains exact.

No shutdown/reset transport or application restart. Fixture metadata and video
are synthetic and cannot establish physical Fold or provider-network performance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'repairs/save-later-multiimage-20261023'))
import android_feature_device as device
sys.path.insert(0, str(REPO / 'repairs/infinity-final-closure-2103407'))
import cached_poster_observer

ADDON = 'service.infinity.performanceqa'
CC = 'script.infinity.commandcenter'
CORE = (CC, 'script.infinity.rails', 'script.infinity.uirepair', 'script.infinity.watchedbridge')
APK_SHA = '5a9e5702a99606cc51b094f9f786edf091b6852306d9a70eaab2787f256e7f39'
PROPERTIES = {'bionic.linker.16kb.app_compat.enabled': 'true', 'pm.16kb.app_compat.disabled': 'false'}
CLIP = 'special://profile/infinity-runtime-qa.mp4'


def require(value, message):
    if not value: raise RuntimeError(message)


def platform_guard(values, existing_package, existing_profile):
    require(values.get('qemu') == '1' and values.get('sdk') == '37' and values.get('release') == '17',
            'Only an actual disposable Android17/API37 emulator is authorized')
    require(values.get('serial', '').startswith('emulator-') and 'arm64-v8a' in values.get('abis', '').split(','),
            'Recognized emulator serial and actual ARM64 native bridge required')
    require(values.get('page_size') == '16384' and values.get('uid') == '0' and values.get('selinux') == 'Enforcing',
            'Selected ps16k root/enforcing emulator required')
    require(not existing_package and not existing_profile, 'Existing application/profile refused; no user data may be replaced')


def platform_before_root(values, existing_package):
    require(values.get('qemu') == '1' and values.get('sdk') == '37' and values.get('release') == '17' and
            values.get('serial', '').startswith('emulator-') and 'arm64-v8a' in values.get('abis', '').split(','),
            'Root transport is limited to the already selected Android17 ARM-compatible emulator')
    require(not existing_package, 'Existing installation refused before root transport')


def fixture():
    def entry(key, media):
        identity = dict(schema=1, kind='movie' if media == 'movie' else 'episode',
                        scope='movie' if media == 'movie' else 'show_episode',
                        ids={'tmdb': '603' if media == 'movie' else '1396'})
        if media == 'tv': identity.update(season=1, episode=2)
        return dict(key=key, media=media, identity=identity, title='QA saved ' + media,
                    label='QA saved ' + media, showtitle='QA saved series' if media == 'tv' else '',
                    season=1 if media == 'tv' else -1, episode=2 if media == 'tv' else -1,
                    tmdb=identity['ids']['tmdb'], source=CLIP, stable_source=CLIP,
                    position=60.0, duration=180.0, percentage=100 / 3, updated=1,
                    poster=cached_poster_observer.URI, playback_occurrence='1' * 32)
    return dict(schema=2, revision=1, items={'a' * 64: entry('a' * 64, 'movie'), 'b' * 64: entry('b' * 64, 'tv')},
                watched={}, watchlist={}, collection={}, later={}, sources={}, ratings={}, lists={})


def observed_card(labels, flags, expected, media):
    rail = 8830 if media == 'movie' else 8831
    prefix = 'Container(%d).ListItem.' % rail
    if not flags.get('Control.IsVisible(%d)' % rail) or labels.get('Container(%d).NumItems' % rail) != '1':
        return False
    try: selection = json.loads(labels.get(prefix + 'Property(Infinity.Selection.Snapshot)', ''))
    except (TypeError, ValueError): return False
    return (selection.get('key') == expected['key'] and selection.get('identity') == expected['identity'] and
            selection.get('source') == expected['source'] and selection.get('stable_source') == expected['stable_source'] and
            labels.get(prefix + 'Property(Infinity.ResumeHub.Watched)') == 'false' and
            abs(float(labels.get(prefix + 'PercentPlayed') or -1000) - float(expected.get('percentage', 0))) <= 1.1)


def run(apk, out):
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity',
            'Only the existing authorized disposable CI runner may execute this fixture')
    require(os.environ.get('SELECTED_FEATURE') == 'infinity-performance-android' and os.environ.get('AUTHORIZED_SCOPE', '').strip(),
            'Explicit selected feature and authorization required')
    with apk.open('rb') as stream:
        require(hashlib.file_digest(stream, 'sha256').hexdigest() == APK_SHA, 'Exact signed2103426 APK required')
    require(not out.exists(), 'Fresh host evidence destination required')
    out.mkdir(parents=True)
    report = dict(apk_sha256=APK_SHA, passed=False, cases=[], snapshots=[],
                  application_launches=0, application_restarts=0, app_termination_requested=False,
                  shutdown='NOT_RUN', physical_Fold='NOT_RUN', APK_changed=False,
                  fixture='Synthetic saved identities, generated local video and cached QA bitmap; no provider-network/content claim',
                  mode='EMULATOR_OS16K_BACKCOMPAT_ONLY_NOT_STRICT16K')
    save = lambda: (out / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n')
    owner = None
    try:
        props = {name: device.shell('getprop', prop).strip() for name, prop in (
            ('qemu', 'ro.kernel.qemu'), ('sdk', 'ro.build.version.sdk'), ('release', 'ro.build.version.release'),
            ('abis', 'ro.product.cpu.abilist'))}
        props['serial'] = device.adb('get-serialno').strip()
        existing = device.shell('pm', 'list', 'packages', device.PACKAGE).strip()
        platform_before_root(props, existing)
        device.adb('root', check=False)
        device.adb('wait-for-device')
        props.update(page_size=device.shell('getconf', 'PAGE_SIZE').strip(),
                     uid=device.shell('id', '-u').strip(), selinux=device.shell('getenforce').strip())
        profile_exists = device.shell('sh', '-c', 'if [ -e ' + device.PROFILE + ' ] || [ -L ' + device.PROFILE + ' ]; then echo present; fi').strip()
        platform_guard(props, existing, profile_exists)
        report['platform'] = props
        report['native_bridge'] = device.shell('sha256sum', '/system/lib64/libndk_translation.so').strip()
        before = {key: device.shell('getprop', key).strip() for key in PROPERTIES}
        for key, value in PROPERTIES.items(): device.shell('setprop', key, value)
        after = {key: device.shell('getprop', key).strip() for key in PROPERTIES}
        require(after == PROPERTIES, 'Documented emulator OS compatibility property readback failed')
        report['OS_compatibility'] = dict(before=before, after=after, APK_installed_at_configuration=False)
        require('Success' in device.adb('install', '--no-incremental', apk), 'Original APK installation failed')
        device.shell('input', 'keyevent', '82')
        device.shell('appops', 'set', device.PACKAGE, 'MANAGE_EXTERNAL_STORAGE', 'allow')
        uid = device.shell('stat', '-c', '%u', device.PRIVATE).strip()
        require(uid.isdigit(), 'Installed test application UID unavailable')
        staging = out / 'fixture'
        addons = staging / 'addons'
        addons.mkdir(parents=True)
        with ZipFile(apk) as archive:
            for name in archive.namelist():
                if not name.startswith('assets/addons/'): continue
                relative = name[len('assets/addons/'):]
                if relative.split('/')[0] not in CORE: continue
                target = addons / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
        qa = addons / ADDON
        qa.mkdir()
        shutil.copyfile(HERE / 'observer.py', qa / 'observer.py')
        (qa / 'addon.xml').write_text('<addon id="' + ADDON + '" name="Disposable performance observation" version="1.0.0" provider-name="Infinity CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.service" library="observer.py" start="startup"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Selected finite QA observer</summary><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        profile = staging / 'userdata'
        state_path = profile / 'addon_data' / CC / 'continue-watching.json'
        state_path.parent.mkdir(parents=True)
        state = fixture()
        state_path.write_text(json.dumps(state))
        (profile / cached_poster_observer.NAME).write_bytes(cached_poster_observer.png())
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=gray:s=64x64:r=1', '-t', '180',
                        '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(profile / 'infinity-runtime-qa.mp4')], check=True)
        (profile / 'guisettings.xml').write_text('<settings version="2"><resolutions/><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting></settings>')
        (profile / 'advancedsettings.xml').write_text('<advancedsettings><loglevel hide="true">1</loglevel></advancedsettings>')
        preference = staging / 'infinity_experience.xml'
        preference.write_text('<map><string name="default">infinity</string></map>')
        device.shell('mkdir', '-p', device.PROFILE, device.PROFILE + '/../addons', device.PRIVATE + '/shared_prefs')
        device.adb('push', str(profile) + '/.', device.PROFILE)
        for addon in addons.iterdir(): device.adb('push', addon, device.PROFILE + '/../addons/' + addon.name)
        device.adb('push', preference, device.PRIVATE + '/shared_prefs/infinity_experience.xml')
        device.shell('chown', '-R', uid + ':' + uid, '/data/media/0/Android/data/' + device.PACKAGE, device.PRIVATE + '/shared_prefs')
        device.shell('restorecon', '-RF', '/data/media/0/Android/data/' + device.PACKAGE, device.PRIVATE + '/shared_prefs')
        require(device.shell('getenforce').strip() == 'Enforcing', 'SELinux changed')
        device.adb('forward', 'tcp:19090', 'tcp:9090')
        launched = time.monotonic()
        report['launch'] = device.shell('am', 'start', '-W', '-n', device.PACKAGE + '/.Splash')
        report['application_launches'] = 1
        save()
        def ready():
            try: return device.rpc('JSONRPC.Ping') == 'pong'
            except (OSError, RuntimeError): return False
        device.until(ready, 180)
        owner = device.until(device.running_engine, 20)
        report['engine'] = owner
        report['launch_to_RPC_ready_ms'] = (time.monotonic() - launched) * 1000
        report['actual_CC'] = device.rpc('Addons.GetAddonDetails', {'addonid': CC, 'properties': ['version', 'enabled']})['addon']
        require(report['actual_CC']['version'] == '0.3.5.50', 'Actual authenticated installed component differs')
        # Dismiss only Android's identified first-use tutorial, never app errors.
        device.shell('uiautomator', 'dump', '/data/local/tmp/infinity-performance-ui.xml')
        raw = device.shell('cat', '/data/local/tmp/infinity-performance-ui.xml')
        for node in ET.fromstring(raw).iter('node'):
            if node.get('text') == 'Got it' and node.get('package') == 'com.android.systemui' and node.get('clickable') == 'true':
                bounds = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
                require(len(bounds) == 4, 'System tutorial bounds unavailable')
                device.shell('input', 'tap', (bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)
        observer_root = device.PROFILE + '/addon_data/' + ADDON
        expected_observer = hashlib.sha256((HERE / 'observer.py').read_bytes()).hexdigest()
        admission = device.until(lambda: device.read_json(observer_root + '/ready.json'), 20)
        require(admission.get('pid') == owner['pid'] and admission.get('source_sha256') == expected_observer, 'Observer PID/source binding failed')
        sequence = 0
        def alive():
            current = device.running_engine()
            require(current and current.get('pid') == owner['pid'] and current.get('owner') == owner['owner'], 'Engine died or restarted')
        def command(action):
            nonlocal sequence
            alive()
            sequence += 1
            path = out / 'request.json'
            path.write_text(json.dumps(dict(pid=owner['pid'], sequence=sequence, action=action)))
            device.adb('push', path, observer_root + '/request.json')
            response = device.until(lambda: (lambda value: value if value.get('pid') == owner['pid'] and value.get('sequence') == sequence else None)(device.read_json(observer_root + '/response.json')), 10)
            (out / ('observer-%02d.json' % sequence)).write_text(json.dumps(response, indent=2))
            require('failure' not in response, 'Observer: ' + str(response.get('failure')))
            return response['observed']
        def home():
            device.rpc('GUI.ActivateWindow', {'window': 'home'})
            device.until(lambda: device.rpc('GUI.GetProperties', {'properties': ['currentwindow']})['currentwindow']['id'] == 10000, 20)
        def resource(stage):
            alive()
            pid = str(owner['pid'])
            for name, arguments in (('memory', ('dumpsys', 'meminfo', pid)), ('stat', ('cat', '/proc/' + pid + '/stat')),
                                    ('frames', ('dumpsys', 'gfxinfo', device.PACKAGE, 'framestats'))):
                (out / (stage + '-' + name + '.txt')).write_text(device.shell(*arguments, check=False))
            report['snapshots'].append(dict(stage=stage, monotonic=time.monotonic(), pid=owner['pid']))
        def card(media, label, expected, deadline=None):
            home()
            start = time.monotonic()
            deadline = min(start + 20, deadline) if deadline is not None else start + 20
            command('movie-tab' if media == 'movie' else 'tv-tab')
            rail = 8830 if media == 'movie' else 8831
            prefix = 'Container(%d).ListItem.' % rail
            fields = ['Container(%d).NumItems' % rail] + [prefix + field for field in (
                'Property(Infinity.Selection.Snapshot)', 'Property(Infinity.ResumeHub.Watched)', 'PercentPlayed')]
            last = {}
            def visible():
                last['labels'] = device.rpc('XBMC.GetInfoLabels', {'labels': fields})
                last['flags'] = device.rpc('XBMC.GetInfoBooleans', {'booleans': ['Control.IsVisible(%d)' % rail]})
                return last if observed_card(last['labels'], last['flags'], expected, media) else None
            try: actual = device.until(visible, max(.01, deadline - time.monotonic()))
            finally: (out / (label + '-last-card.json')).write_text(json.dumps(last, indent=2))
            elapsed = (time.monotonic() - start) * 1000
            poster = cached_poster_observer.observe(device, out / (label + '-poster'), start, deadline)
            require(not device.rpc('Player.GetActivePlayers'), 'Unexpected autoplay')
            report['cases'].append(dict(case=label, passed=True, selected_card=actual, tab_to_observed_card_ms=elapsed,
                poster=poster, no_autoplay=True, timing='Emulator observed upper bound, not physical/GPU first paint'))
            save()
        home()
        resource('before')
        card('movie', 'initial-movie', state['items']['a' * 64])
        card('tv', 'initial-tv', state['items']['b' * 64])
        home()
        command('search')
        def keyboard():
            device.shell('uiautomator', 'dump', '/data/local/tmp/infinity-performance-ui.xml')
            raw = device.shell('cat', '/data/local/tmp/infinity-performance-ui.xml')
            (out / 'search-ui.xml').write_text(raw)
            return [n for n in ET.fromstring(raw).iter('node') if n.get('class') == 'android.widget.EditText' and n.get('package') == device.PACKAGE and n.get('enabled') == 'true']
        device.until(keyboard, 45)
        backs = 0
        for _ in range(2):
            device.shell('input', 'keyevent', '4')
            backs += 1
            if not keyboard(): break
        require(not keyboard(), 'Search keyboard did not cancel')
        alive()
        report['cases'].append(dict(case='actual-search-keyboard-cancel', passed=True, observed_native_EditText=True,
                                    Back_actions=backs, provider_request_cancellation='NOT_SELECTED'))
        save()
        home()
        command('movie-tab')
        command('movie-focus')
        require(device.rpc('XBMC.GetInfoBooleans', {'booleans': ['Control.HasFocus(8830)']})['Control.HasFocus(8830)'], 'Actual saved movie must have focus')
        require(not device.rpc('Player.GetActivePlayers'), 'Unexpected playback before deliberate Select')
        device.rpc('Input.Select')
        players = device.until(lambda: [p for p in device.rpc('Player.GetActivePlayers') if p.get('type') == 'video'], 20)
        player = players[0]['playerid']
        def resumed():
            properties = device.rpc('Player.GetProperties', {'playerid': player, 'properties': ['time', 'speed']})
            stamp = properties.get('time', {})
            seconds = stamp.get('hours', 0) * 3600 + stamp.get('minutes', 0) * 60 + stamp.get('seconds', 0)
            return dict(properties=properties, seconds=seconds) if properties.get('speed') == 1 and seconds >= 62 else None
        playback = device.until(resumed, 20)
        stopped = time.monotonic()
        stop_deadline = stopped + 20
        device.rpc('Player.Stop', {'playerid': player})
        device.until(lambda: not device.rpc('Player.GetActivePlayers'), max(.01, stop_deadline - time.monotonic()))
        def fresh_progress():
            updated = device.read_json(device.PROFILE + '/addon_data/' + CC + '/continue-watching.json')
            value = updated.get('items', {}).get('a' * 64)
            return value if isinstance(value, dict) and 61 <= float(value.get('position', 0)) < 180 else None
        current = device.until(fresh_progress, max(.01, stop_deadline - time.monotonic()))
        require(isinstance(current, dict) and current.get('identity') == state['items']['a' * 64]['identity'], 'Saved movie identity changed after playback')
        require(current.get('source') == CLIP and 61 <= float(current.get('position', 0)) < 180, 'Fresh post-playback progress/source unavailable')
        current = dict(current, key='a' * 64)
        current['percentage'] = float(current['position']) / float(current['duration']) * 100
        report['playback'] = dict(deliberate_input='Input.Select on actual focused saved card', observed=playback,
                                  stopped_monotonic=stopped, fresh_progress=current)
        card('movie', 'playback-return-movie', current, deadline=stop_deadline)
        report['playback']['Stop_to_proof_finished_ms'] = (time.monotonic() - stopped) * 1000
        resource('after')
        command('finish')
        alive()
        report['passed'] = True
    except Exception as error:
        report['failure'] = type(error).__name__ + ': ' + str(error)
        report['traceback'] = traceback.format_exc()
    finally:
        if report.get('platform', {}).get('qemu') == '1':
            for name, arguments in (('logcat.txt', ('logcat', '-d', '-v', 'threadtime')),
                                    ('processes.txt', ('shell', 'ps', '-A'))):
                try: (out / name).write_text(device.adb(*arguments, check=False))
                except Exception: pass
            try: device.adb('pull', device.PROFILE + '/../temp/kodi.log', out / 'kodi.log', check=False)
            except Exception: pass
            if owner:
                try: (out / 'last-GUI.json').write_text(json.dumps(device.rpc('XBMC.GetInfoLabels', {'labels': [
                    'Container(9000).ListItem.Property(section)', 'Container(8830).NumItems', 'Container(8831).NumItems',
                    'Container.FolderPath', 'Window(Home).Property(Infinity.ContinueWatchingRevision)']}), indent=2))
                except Exception: pass
                if not report['passed']:
                    try: (out / 'failure-native-backtrace.txt').write_text(device.shell('debuggerd', '-b', str(owner['pid']), check=False))
                    except Exception: pass
        with apk.open('rb') as stream:
            report['post_execution_APK_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        if report['post_execution_APK_sha256'] != APK_SHA:
            report['passed'] = False
            report['failure'] = 'Signed APK bytes changed; evidence quarantined'
        save()
    print(json.dumps({key: report.get(key) for key in ('passed', 'failure', 'application_launches', 'APK_changed', 'shutdown', 'physical_Fold')}, indent=2))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.apk, args.out) else 1)
