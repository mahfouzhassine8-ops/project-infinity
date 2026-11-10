"""Selected stock Android network checks. Test tooling only; no production edits."""
import argparse
import codecs
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
ROOT = TASK.parents[1]
OLD = ROOT / 'repairs/infinity-tracking-integration-2103469-20261108'
sys.path.insert(0, str(OLD))
import qualify_android_baseline as base
import verify_tracking_android as native
import verify_tracking_install as install
sys.path.insert(0, str(TASK / 'release'))
import prepare_modules as prep

QA = 'script.infinity.networkqa'
QA_PROFILE = base.PROFILE + '/addon_data/' + QA
REMOTE = '/sdcard/Download/infinity-network-qa/'
VERSIONS = (2103477, 2103478, 2103479)


def require(value, label):
    if not value:
        raise RuntimeError(label)


class Device(base.Device):
    METHODS = frozenset(('JSONRPC.Ping', 'GUI.GetProperties', 'GUI.ActivateWindow',
        'XBMC.GetInfoLabels', 'Input.Home', 'Input.Right', 'Input.Left', 'Input.Up',
        'Input.Down', 'Input.Back', 'Input.Select', 'Input.ExecuteAction',
        'Addons.GetAddonDetails', 'Addons.ExecuteAddon', 'Player.GetActivePlayers',
        'Player.GetProperties', 'Player.Stop'))

    def rpc(self, method, params=None, timeout=5):
        require(method in self.METHODS, 'BOUNDED_NETWORK_QA_METHOD')
        if method == 'Addons.ExecuteAddon':
            require(params == dict(addonid=QA), 'ONLY_DISPOSABLE_NETWORK_OBSERVER')
        if method == 'Input.ExecuteAction':
            require(params == dict(action='firstpage'), 'ONLY_NATIVE_LIST_FIRSTPAGE')
        deadline = time.monotonic() + min(timeout, 15)
        def remaining():
            seconds = deadline - time.monotonic()
            if seconds <= 0:
                raise TimeoutError('Network QA RPC absolute deadline: ' + method)
            return seconds
        request = dict(jsonrpc='2.0', id=478, method=method)
        if params is not None:
            request['params'] = params
        with socket.create_connection(('127.0.0.1', 19090), timeout=remaining()) as conn:
            conn.settimeout(remaining())
            conn.sendall(json.dumps(request).encode())
            utf8, decoder, pending, count = codecs.getincrementaldecoder('utf-8')(), json.JSONDecoder(), '', 0
            while count < 2 * 1024 * 1024:
                conn.settimeout(remaining())
                chunk = conn.recv(min(65536, 2 * 1024 * 1024 - count))
                if not chunk:
                    break
                count += len(chunk)
                pending += utf8.decode(chunk)
                while pending.strip():
                    remaining()
                    pending = pending.lstrip()
                    try:
                        reply, end = decoder.raw_decode(pending)
                    except ValueError:
                        break
                    pending = pending[end:]
                    if reply.get('id') != 478:
                        continue
                    require('error' not in reply, 'ACTUAL_RPC_ERROR:' + str(reply))
                    return reply['result']
        raise ConnectionError('Incomplete network QA RPC: ' + method)


class Observer:
    def __init__(self, device, out):
        self.device, self.out, self.sequence = device, out, 0
        device.rpc('Addons.ExecuteAddon', dict(addonid=QA))
        def ready():
            try:
                result = json.loads(device.shell('cat', QA_PROFILE + '/ready.json', check=False))
                return result if result.get('pid') == device.pid and result.get('qa') == QA else None
            except ValueError:
                return None
        self.ready = native.until(device, ready, 'Actual network observer ready', 45)

    def call(self, action, **values):
        self.sequence += 1
        request = dict(pid=self.device.pid, sequence=self.sequence, action=action, **values)
        path = self.out / 'request.json'
        base.save(path, request)
        self.device.adb('push', path, QA_PROFILE + '/request.pending')
        self.device.shell('mv', QA_PROFILE + '/request.pending', QA_PROFILE + '/request.json')
        def reply():
            raw = self.device.shell('head', '-c', '4194305', QA_PROFILE + '/reply.json', check=False)
            require(len(raw.encode()) <= 4 * 1024 * 1024, 'BOUNDED_OBSERVER_REPLY')
            try:
                result = json.loads(raw)
                return result if result.get('pid') == self.device.pid and result.get('sequence') == self.sequence else None
            except ValueError:
                return None
        result = native.until(self.device, reply, 'Network observer ' + action, 45)
        base.save(self.out / ('observer-%03d-%s.json' % (self.sequence, action)), result)
        require(result.get('passed') is True, 'OBSERVER_ACTION_FAILED:' + str(result))
        return result['result']


def request():
    row = base.load(HERE / 'ANDROID-REQUEST.json')
    require(row['operation'] == 'verify-original77-network78-recovery79' and row['build_sign'] is False
            and row['publication'] is False and row['shutdown_tests'] is False, 'SELECTED_NETWORK_ONLY_REQUEST')
    for name, digest in row['source_bindings'].items():
        require(base.sha(ROOT / name) == digest, 'SELECTED_SOURCE:' + name)
    return row


def download(row, target):
    helper = OLD / 'tracking_module_fixture.py'
    require(base.sha(helper) == 'af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb', 'FROZEN_ARTIFACT_HELPER')
    spec = importlib.util.spec_from_file_location('network_original_artifact_download', helper)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.download(row, target)


def admit(out, sdk):
    selected = request()
    require(not out.exists(), 'FRESH_NETWORK_INPUT_INTAKE')
    out.mkdir(parents=True)
    inputs = {}
    for version in VERSIONS:
        row = selected['artifacts'][str(version)]
        files = download(row, out / str(version))
        apk = files / ('Infinity-%d-Combined-Original-Signer.apk' % version)
        require(base.sha(apk) == selected['APK_sha256'][str(version)], 'EXACT_ORIGINAL_SIGNED_APK')
        signature = base.command([sdk / 'build-tools/35.0.0/apksigner', 'verify', '--verbose', '--print-certs', apk], timeout=60)
        require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [base.CERT], 'ORIGINAL_CERT_ONLY')
        for scheme in ('v1', 'v2', 'v3'):
            require(any(line.startswith('Verified using ' + scheme + ' scheme') and line.endswith(': true') for line in signature.splitlines()), 'ALL_ORIGINAL_SIGNATURE_SCHEMES')
        (out / str(version) / 'HOST-SIGNATURE.txt').write_text(signature)
        inputs[str(version)] = str(apk.resolve())
    baseline = Path(inputs['2103477'])
    import prepare_apk
    for version in VERSIONS[1:]:
        files = out / str(version) / 'files'
        proof = base.load(files / 'PREPARATION.json')
        require(base.load(files / 'BUILD-RECEIPT.json')['source'] == selected['artifacts'][str(version)]['source'], 'ORIGINAL_SIGNING_RECEIPT_SOURCE')
        base.save(out / str(version) / 'EXACT77-PRESERVATION.json', prepare_apk.compare(baseline, Path(inputs[str(version)]), proof))
    zips = out / 'zips'; zips.mkdir()
    fixture = out / 'fixture'; fixture.mkdir()
    base.command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=24',
                  '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '90', '-c:v', 'mpeg4', '-b:v', '800k',
                  '-c:a', 'aac', '-movflags', '+faststart', fixture / 'fixture.mp4'], timeout=90)
    base.command(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', fixture / 'server.key',
                  '-out', fixture / 'server.crt', '-days', '1', '-subj', '/CN=localhost'], timeout=30)
    addon = ('<addon id="'+QA+'" name="Disposable network transport QA" version="1.0.0" provider-name="Infinity engineering">'
             '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
             '<extension point="xbmc.python.script" library="default.py"/></addon>')
    zip_path = zips / (QA + '-1.0.0.zip')
    with ZipFile(zip_path, 'x', compression=ZIP_DEFLATED) as archive:
        archive.writestr(QA + '/addon.xml', addon)
        archive.writestr(QA + '/default.py', (HERE / 'network_observer.py').read_bytes())
        for name in ('fixture.mp4', 'server.key', 'server.crt'):
            archive.write(fixture / name, QA + '/' + name)
    base.save(out / 'INPUTS.json', dict(apks=inputs, qa=dict(addon=QA, version='1.0.0', archive=zip_path.name,
              sha256=base.sha(zip_path)), request_sha256=base.sha(HERE / 'ANDROID-REQUEST.json')))


def select_mode(device, observer, mode):
    hub = observer.call('focus_hub')
    require(hub == dict(window=1191, focus=1191105, label='NETWORK CONNECTIONS'), 'ACTUAL_HUB_NETWORK_CONTROL')
    device.rpc('Input.Select')
    wanted = {'auto': 'Automatic (Default)', 'ipv4': 'IPv4 Only', 'ipv6': 'IPv6 Only'}[mode]
    popup = native.until(device, lambda: (p if (p := observer.call('popup')).get('title') == 'Network Connections' else None),
                         'Real Network Connections selector', 15)
    for _ in range(5):
        if popup['label'] == wanted:
            break
        device.rpc('Input.Down')
        popup = observer.call('popup')
    require(popup['label'] == wanted, 'ACTUAL_SELECTED_FAMILY_LABEL')
    device.rpc('Input.Select')
    current = native.until(device, lambda: (v if (v := observer.call('identity'))['mode'] == mode else None), 'Persisted network setting', 10)
    remote = base.PROFILE + '/addon_data/' + base.CC + '/settings.xml'
    raw = device.shell('cat', remote)
    values = [node.text for node in ET.fromstring(raw).iter('setting') if node.get('id') == 'network_family']
    require(values == [mode], 'ACTUAL_DISK_SETTING_MODE')
    return dict(selector=popup, identity=current)


def identity(observer, version):
    result = observer.call('identity')
    cc, skin, count = {2103477: ('0.3.5.75', '1.0.5.270', 80),
                       2103478: ('0.3.5.76', '1.0.5.271', 81),
                       2103479: ('0.3.5.77', '1.0.5.272', 80)}[version]
    require(result['CC'] == cc and result['skin'] == skin, 'ACTIVE_CC_AND_SKIN_GENERATION')
    require(result['declared_sources'] == count, 'COMPLETE_AUTHENTICATED_SOURCE_COUNT')
    require(result['native_authenticated'] == 1 and result['native_version'] == cc and result['protocol'] == 1
            and result['native_manifest'] == result['manifest_sha256'], 'ACTUAL_NATIVE_MODULE_AUTHENTICATION')
    result['expected_count'] = count
    return result


def checks(device, observer, out):
    ready = observer.ready
    urls = dict(v4='http://127.0.0.1:%d' % ready['ipv4'], v6='http://[::1]:%d' % ready['ipv6'])
    report = {}
    for mode, allowed, denied, family in (('ipv4', 'v4', 'v6', 2), ('ipv6', 'v6', 'v4', 10)):
        selected = select_mode(device, observer, mode)
        positive = observer.call('fetch', url=urls[allowed] + '/echo')
        require(positive['opened'] and positive['response']['family'] == family, 'MATCHING_FAMILY_POSITIVE:' + mode)
        hits = positive['hits']
        negative = observer.call('fetch', url=urls[denied] + '/echo')
        require(not negative['opened'] and negative['hits'] == hits, 'FORBIDDEN_LITERAL_NO_REQUEST:' + mode)
        redirected = observer.call('fetch', url=urls[allowed] + '/redirect')
        require(redirected['opened'] and redirected['response']['family'] == family, 'SAME_FAMILY_REDIRECT:' + mode)
        report[mode] = dict(status='PASS_REAL_ANDROID_VFS', selected=selected, positive=positive, negative=negative, redirect=redirected)
    cross = observer.call('fetch', url=urls['v6'] + '/cross-v4')
    require(not cross['opened'] and cross['hits'][-1]['path'] == '/cross-v4', 'IPV6_REDIRECT_CANNOT_ESCAPE_TO_IPV4')
    mapped = observer.call('fetch', url='http://[::ffff:127.0.0.1]:%d/echo' % ready['ipv4'])
    require(not mapped['opened'] and mapped['hits'] == cross['hits'], 'IPV6_V4_MAPPED_LITERAL_REJECTED')
    report['ipv6_security'] = dict(cross_redirect=cross, mapped_literal=mapped)
    select_mode(device, observer, 'auto')
    automatic = {name: observer.call('fetch', url=url + '/echo') for name, url in urls.items()}
    require(all(v['opened'] for v in automatic.values()), 'AUTOMATIC_BOTH_LITERAL_FAMILIES')
    tls = observer.call('fetch', url='https://example.com/')
    require(tls['opened'], 'PUBLIC_VALID_TLS_UNAVAILABLE_OR_FAILED')
    bad_tls = observer.call('fetch', url='https://127.0.0.1:%d/echo' % ready['tls'])
    require(not bad_tls['opened'], 'SELF_SIGNED_TLS_REJECTED')
    dns = observer.call('fetch', url='http://infinity-networkqa.invalid/|connection-timeout=3')
    require(not dns['opened'], 'INVALID_DNS_NO_SUCCESS')
    http_error = observer.call('fetch', url=urls['v4'] + '/deny')
    require(not http_error['opened'], 'HTTP_REJECTION_NOT_HIDDEN')
    report['automatic'] = dict(status='PASS_AVAILABLE_ANDROID_ROUTES', requests=automatic, valid_tls=tls,
        self_signed_tls=bad_tls, invalid_dns=dns, http_rejection=http_error,
        timed_ipv6_connect_failure_then_ipv4='HOST_EVIDENCE_REUSED_NOT_REPRODUCED_BY_LOOPBACK')
    # Sequential reused real handles; no concurrent close/read or fake native cancel.
    samples = []
    for _ in range(3):
        for _ in range(10):
            require(observer.call('fetch', url=urls['v4'] + '/echo')['opened'], 'REPEATED_REAL_VFS')
        samples.append(observer.call('identity'))
    report['connection_stability'] = dict(samples=samples, requests=30, status='MEASURED_REQUIRES_RESOURCE_REVIEW',
                                         global_leak_proof=False)
    select_mode(device, observer, 'ipv4')
    before_play = observer.call('playing')
    event_floor = len(before_play['events'])
    fixture_url = urls['v4'] + '/fixture.mp4'
    observer.call('play', url=fixture_url)
    playing = native.until(device, lambda: (p if (p := observer.call('playing'))['video'] and
                            p['source'] == fixture_url and any(e['event'] == 'AVStarted' for e in p['events'][event_floor:])
                            and p['time'] > 2 else None),
                            'Genuine progressive HTTP playback AV/time', 45)
    first = playing['time']
    select_mode(device, observer, 'ipv6')
    advanced = native.until(device, lambda: (p if (p := observer.call('playing'))['video'] and p['time'] > first + 2 else None),
                            'Active playback survives setting switch', 20)
    require(observer.call('fetch', url=urls['v6'] + '/echo')['opened'], 'NEW_CONNECTION_USES_NEW_MODE')
    observer.call('stop')
    stopped = native.until(device, lambda: (p if not (p := observer.call('playing'))['playing'] else None), 'Ordinary player stop', 15)
    before_bytes = max(h['bytes_sent'] for h in playing['hits'] if h['path'] == '/fixture.mp4')
    after_bytes = max(h['bytes_sent'] for h in advanced['hits'] if h['path'] == '/fixture.mp4')
    require(after_bytes > before_bytes, 'EXISTING_HTTP_PLAYBACK_CONNECTION_CONTINUES_AFTER_MODE_SWITCH')
    report['playback'] = dict(status='PASS_ACTUAL_HTTP_PLAY_AV_STOP', before=playing, after_switch=advanced, stopped=stopped)
    select_mode(device, observer, 'ipv4')
    observer.call('play', url=urls['v4'] + '/stalled.mp4')
    def actual_delay():
        current = observer.call('playing')
        return current if any(h['path'] == '/stalled.mp4' and h.get('delay_enter') for h in current['hits']) else None
    delayed = native.until(device, actual_delay, 'Actual server observed delayed playback request', 15)
    started = time.monotonic()
    observer.call('stop')
    stopped = native.until(device, lambda: (p if not (p := observer.call('playing'))['playing'] else None), 'Stop while transport fixture delayed', 15)
    report['cancellation'] = dict(status='PASS_OBSERVED_PLAYER_STOP_ONLY', seconds=time.monotonic()-started, delayed=delayed, stopped=stopped,
                                 specific_CurlFile_Cancel_callback='NOT_CLAIMED_WITHOUT_NATIVE_TRACE')
    select_mode(device, observer, 'ipv6')
    layouts = []
    try:
        for name, size in (('fold-front-surrogate', '904x2316'), ('fold-inner-surrogate', '1812x2176')):
            device.shell('wm', 'size', size)
            time.sleep(1)
            observer.call('focus_hub')
            device.rpc('Input.Select')
            popup = native.until(device, lambda: (p if (p := observer.call('popup'))['title'] == 'Network Connections' else None),
                                 'Network selector after Android viewport change', 15)
            device.screenshot(name + '-network-selector')
            device.rpc('Input.Back')
            require(observer.call('identity')['mode'] == 'ipv6', 'CANCEL_SELECTOR_PRESERVES_MODE')
            layouts.append(dict(viewport=size, selector=popup, hardware='ANDROID_EMULATOR_SURROGATE_NOT_PHYSICAL_FOLD',
                                screenshot=name + '-network-selector.png'))
    finally:
        device.shell('wm', 'size', 'reset')
    report['responsive_selector'] = layouts
    device.rpc('Input.Home')
    device.screenshot('network-after-checks')
    base.save(out / 'NETWORK-CHECKS.json', report)
    return report


def run(inputs, sdk, out):
    selected = request()
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REF') ==
            'refs/heads/work/infinity-network-family-from-2103477-20261109', 'SELECTED_DISPOSABLE_CI_ONLY')
    require(not out.exists(), 'FRESH_ANDROID_EVIDENCE'); out.mkdir(parents=True)
    report = dict(status='RUNNING', production_changes=False, physical_Fold='PENDING_OWNER',
                  inherited_DNS_hard_deadline='FAIL_RETAINED_OWNER_APPROVED_LIMITATION', versions={})
    device, reader = None, None
    try:
        staged = base.load(inputs / 'INPUTS.json')
        require(staged['request_sha256'] == base.sha(HERE / 'ANDROID-REQUEST.json'), 'EXACT_ADMITTED_INPUTS')
        device = Device(out, sdk)
        report['environment'] = base.environment(device, out)
        require(not device.shell('pm', 'list', 'packages', base.PACKAGE).strip(), 'FRESH_DISPOSABLE_VM')
        base.root_reconnect(device, out)
        reader = base.start_lifecycle_log(device, out)
        device.adb('forward', 'tcp:19090', 'tcp:9090')
        uid, sentinel = None, None
        for version in VERSIONS:
            phase = out / str(version); phase.mkdir()
            if version != VERSIONS[0]:
                # Package update naturally restarts process; not shutdown qualification.
                device.shell('am', 'force-stop', base.PACKAGE)
                require(not device.pids(), 'STOP_ONLY_FOR_SELECTED_PACKAGE_UPDATE')
            result = device.adb('install', '--no-streaming', *(['-r'] if uid else []), staged['apks'][str(version)], timeout=300)
            require(result.strip().endswith('Success'), 'IN_PLACE_PACKAGE_INSTALL')
            observation = install.installed_package(device, dict(versionCode=version, sha256=selected['APK_sha256'][str(version)]), uid)
            uid = observation['uid']
            if sentinel:
                require(device.shell('sha256sum', sentinel['remote']).split()[0] == sentinel['sha256'], 'USERDATA_SENTINEL_RETAINED')
            if version == VERSIONS[0]:
                device.shell('mkdir', '-p', base.PROFILE, REMOTE)
                settings = out / 'guisettings.xml'
                settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting>'
                    '<setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting>'
                    '<setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting>'
                    '<setting id="debug.showloginfo">true</setting></settings>')
                sources = out / 'sources.xml'
                sources.write_text('<sources><files><source><name>Disposable networking QA</name><path pathversion="1">'+REMOTE+'</path>'
                    '<allowsharing>false</allowsharing></source></files></sources>')
                device.adb('push', settings, base.PROFILE + '/guisettings.xml')
                device.adb('push', sources, base.PROFILE + '/sources.xml')
                advanced = out / 'advancedsettings.xml'
                advanced.write_text('<advancedsettings><loglevel hide="false">1</loglevel></advancedsettings>')
                device.adb('push', advanced, base.PROFILE + '/advancedsettings.xml')
                device.adb('push', inputs / 'zips' / staged['qa']['archive'], REMOTE + staged['qa']['archive'])
                sample = out / 'engineering-retention-sentinel.json'
                sample.write_text('{"domain":"disposable_network_QA","not_real_owner_data":true}\n')
                remote = base.PROFILE + '/network-engineering-retention-sentinel.json'
                device.adb('push', sample, remote)
                sentinel = dict(remote=remote, sha256=base.sha(sample))
                device.shell('chown', '-R', str(uid)+':'+str(uid), '/data/media/0/Android/data/'+base.PACKAGE)
                device.shell('restorecon', '-RF', '/data/media/0/Android/data/'+base.PACKAGE)
            start = base.start_once(device, version, phase)
            if version == VERSIONS[0]:
                native.install_zip(device, staged['qa'], dict(remote_zip_directory=REMOTE), phase, 'network-observer')
            observer = Observer(device, phase)
            active = identity(observer, version)
            record = dict(install=observation, startup=start, active_identity=active)
            if version == 2103478:
                record['network'] = checks(device, observer, phase)
                observer.call('close')
                # One selected setting-persistence restart, not a shutdown test.
                device.shell('am', 'force-stop', base.PACKAGE)
                start = base.start_once(device, '78-persistence', phase)
                observer = Observer(device, phase)
                current = identity(observer, version)
                require(current['mode'] == 'ipv6', 'NETWORK_MODE_SURVIVES_PROCESS_RESTART')
                require(observer.call('fetch', url='http://[::1]:%d/echo' % observer.ready['ipv6'])['opened'], 'RESTART_RETAINED_MODE_REAL_CONNECTION')
                record['persistence'] = dict(status='PASS_REAL_RESTART', startup=start, identity=current)
            elif version == 2103479:
                require('network-connections' not in device.shell('cat', active['CC_path'] + '/default.py'),
                        'RECOVERY_ORIGINAL_DISPATCH_RESTORED')
                require(observer.call('fetch', url='http://127.0.0.1:%d/echo' % observer.ready['ipv4'])['opened'], 'RECOVERY_ORIGINAL_TRANSPORT')
                record['recovery'] = dict(status='PASS_ORIGINAL_FUNCTIONALITY_HIGHER_METADATA', inactive_extra_helper_may_remain=True)
            observer.call('close')
            device.screenshot('version-' + str(version))
            base.crash_free_alive(device)
            report['versions'][str(version)] = record
            base.save(out / 'ANDROID-NETWORK-VERIFICATION.json', report)
        report['status'] = 'PASS_SELECTED_REAL_ANDROID_NETWORK_AND_FORWARD_INSTALL_CASES'
        report['limitations'] = ['Physical Fold front/inner and carrier IPv6 pending owner',
            'Timed dual-stack handshake fallback reused host evidence; not reproduced on loopback',
            'Independent Python/direct FFmpeg/inputstream transports not controlled',
            'Provider-account operations are preserved bytes, not reauthenticated by this fixture',
            'No global resource-leak proof or inherited DNS deadline PASS claimed']
    except Exception:
        report.update(status='BLOCKED_OR_FAILED_SEE_EXACT_ERROR', error=traceback.format_exc())
        raise
    finally:
        if device:
            for name, remote in [('kodi.log', base.HOME + '/temp/kodi.log'), ('kodi.old.log', base.HOME + '/temp/kodi.old.log')]:
                try:
                    device.adb('pull', remote, out / name, check=False)
                except Exception:
                    pass
            try:
                (out / 'crash-log.txt').write_text(device.shell('logcat', '-b', 'crash', '-d', timeout=5))
            except Exception:
                pass
        if reader:
            reader.terminate()
            try:
                reader.wait(timeout=5)
            except subprocess.TimeoutExpired:
                reader.kill(); reader.wait(timeout=3)
        base.save(out / 'ANDROID-NETWORK-VERIFICATION.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['admit', 'run'])
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--inputs', type=Path)
    args = parser.parse_args()
    if args.operation == 'admit':
        admit(args.out, args.sdk)
    else:
        run(args.inputs, args.sdk, args.out)
