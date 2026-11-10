"""Exact signed77 performance intake and selected disposable Android measurements."""
import argparse
import codecs
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time
import traceback
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'repairs/infinity-tracking-integration-2103469-20261108'
sys.path.insert(0, str(OLD))
import qualify_android_baseline as base
import verify_tracking_android as gui
sys.path.insert(0, str(ROOT / 'repairs/infinity-final-closure-2103407'))
import android_frame_samples as frames
import surface_layers

QA = 'script.infinity.performanceprobe'
QP = base.PROFILE + '/addon_data/' + QA
REMOTE = '/sdcard/Download/infinity-performance-probe/'
APK_SHA = '93eb081cd6a86ff9cf1cb9aa75bc6d9087cd9c982fb46e0a9baa12c12aa9af22'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'


def selected():
    scope = base.load(HERE / 'SCOPE.json')
    base.require(scope['operation'] in ('signed77-performance-baseline','signed77-performance-followup','signed77-ui-cost-comparison') and
                 not scope['shutdown_tests'] and not scope['production_edits'], 'BASELINE_ONLY_SCOPE')
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        base.require(os.environ.get('SELECTED_FEATURE') == scope['selected_feature'], 'EXACT_NAMED_MEASUREMENT_SELECTION')
    for name, digest in scope['source_bindings'].items():
        base.require(base.sha(ROOT / name) == digest, 'SELECTED_SOURCE_BINDING:' + name)
    return scope


def admit(sdk, out):
    scope = selected()
    base.require(not out.exists(), 'FRESH_INTAKE_DIRECTORY')
    helper = OLD / 'tracking_module_fixture.py'
    base.require(base.sha(helper) == 'af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb', 'UNCHANGED_ARTIFACT_INTAKE')
    spec = importlib.util.spec_from_file_location('original_artifact_intake', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    files = module.download(scope['artifact'], out)
    apk = files / 'Infinity-2103477-Combined-Original-Signer.apk'
    base.require(base.sha(apk) == APK_SHA, 'EXACT_SIGNED77_BYTES')
    signature = base.command([sdk / 'build-tools/35.0.0/apksigner', 'verify', '--verbose', '--print-certs', apk], timeout=60)
    base.require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT], 'ORIGINAL_SIGNER')
    (out / 'SIGNATURE.txt').write_text(signature)
    archive = out / 'performance-observer.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
        z.writestr(QA + '/addon.xml', '<addon id="'+QA+'" version="1.0.0" name="Disposable performance observer" provider-name="Infinity QA">'
            '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
            '<extension point="xbmc.python.script" library="default.py"/>'
            '<extension point="xbmc.addon.metadata"><summary lang="en_GB">CI-only measurement</summary>'
            '<description lang="en_GB">Not shipped</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
        z.write(HERE / 'observer.py', QA + '/default.py')
        z.write(HERE / 'context_batch_prototype.py', QA + '/context_batch_prototype.py')
    base.save(out / 'INTAKE.json', dict(apk=str(apk.resolve()), sha256=APK_SHA,
        artifact=scope['artifact'], observer=dict(addon=QA, version='1.0.0', archive=archive.name,
        sha256=base.sha(archive)), observer_path=str(archive.resolve()), scope_sha256=base.sha(HERE / 'SCOPE.json')))


class Device(base.Device):
    METHODS = frozenset(('JSONRPC.Ping', 'GUI.GetProperties', 'GUI.ActivateWindow', 'XBMC.GetInfoLabels',
        'Input.Home', 'Input.Left', 'Input.Right', 'Input.Up', 'Input.Down', 'Input.Back', 'Input.Select',
        'Input.ExecuteAction', 'Addons.GetAddonDetails', 'Addons.ExecuteAddon'))

    def rpc(self, method, params=None, timeout=5):
        base.require(method in self.METHODS, 'SELECTED_PERFORMANCE_RPC')
        if method == 'Addons.ExecuteAddon':
            base.require(params == dict(addonid=QA), 'ONLY_DISPOSABLE_OBSERVER_EXECUTION')
        if method == 'Input.ExecuteAction':
            base.require(params == dict(action='firstpage'), 'ONLY_NATIVE_LIST_FIRSTPAGE')
        deadline = time.monotonic() + timeout
        request = dict(jsonrpc='2.0', id=477, method=method)
        if params is not None:
            request['params'] = params
        def remaining():
            value = deadline - time.monotonic()
            if value <= 0:
                raise TimeoutError('Bounded performance RPC: ' + method)
            return value
        with socket.create_connection(('127.0.0.1', 19090), timeout=remaining()) as conn:
            conn.sendall(json.dumps(request).encode())
            pending, count = '', 0
            utf8, decoder = codecs.getincrementaldecoder('utf8')(), json.JSONDecoder()
            while count < 2*1024*1024:
                conn.settimeout(remaining())
                chunk = conn.recv(min(65536, 2*1024*1024-count))
                if not chunk:
                    break
                count += len(chunk)
                pending += utf8.decode(chunk)
                while pending.strip():
                    pending = pending.lstrip()
                    try:
                        reply, end = decoder.raw_decode(pending)
                    except ValueError:
                        break
                    pending = pending[end:]
                    if reply.get('id') == 477:
                        base.require('error' not in reply, 'REAL_RPC_ERROR:' + str(reply))
                        return reply['result']
        raise ConnectionError('Incomplete performance RPC: ' + method)


def query(device, *args, timeout=8):
    start = time.monotonic()
    result = subprocess.run([str(device.adb_bin), '-s', device.serial, 'shell', shlex.join(args)],
                            capture_output=True, timeout=timeout)
    return dict(start_monotonic=start, finish_monotonic=time.monotonic(), returncode=result.returncode,
                stdout=result.stdout[:8*1024*1024].decode(errors='replace'),
                stderr=result.stderr[:256*1024].decode(errors='replace'),
                stdout_truncated=len(result.stdout)>8*1024*1024, stderr_truncated=len(result.stderr)>256*1024)


def snapshot(device, out, label, layer=None):
    device.alive()
    row = dict(monotonic=time.monotonic(), pid=device.pid, process_start=device.start_time)
    for name, args in [('proc_stat', ['cat', '/proc/%d/stat' % device.pid]),
                       ('status', ['cat', '/proc/%d/status' % device.pid]),
                       ('fd', ['ls', '/proc/%d/fd' % device.pid]),
                       ('threads', ['ps', '-T', '-p', str(device.pid)]),
                       ('layers', ['dumpsys', 'SurfaceFlinger', '--list'])]:
        row[name] = query(device, *args)
    candidates = surface_layers.candidates(row['layers']['stdout']) if row['layers']['returncode']==0 and not row['layers']['stdout_truncated'] else []
    row['matching_layer_candidates'] = candidates
    selected = next((v for v in candidates if v['name']==layer),None) if layer else candidates[0] if len(candidates)==1 else None
    if len(candidates) != 1:
        selected = None
    row['layer'] = selected['name'] if selected else None
    row['layer_identity'] = selected
    row['same_requested_layer_present'] = layer is None or row['layer'] == layer
    if row['layer']:
        row['surface_inventory'] = query(device, 'dumpsys', 'SurfaceFlinger',timeout=12)
        row['layer_corroboration'] = surface_layers.corroborate(row['surface_inventory']['stdout'],selected,device.pid)
        row['presentations'] = query(device, 'dumpsys', 'SurfaceFlinger', '--latency', row['layer'])
    row['finished_monotonic'] = time.monotonic()
    base.save(out / (label + '.json'), row)
    return row


def scene(device, out, label, actions):
    before = snapshot(device, out, label+'-before')
    events = []
    for action in actions:
        at = time.monotonic()
        if action == 'idle':
            time.sleep(.4)
        else:
            device.rpc(action)
            time.sleep(.08)
        events.append(dict(action=action, start=at, finished=time.monotonic()))
    after = snapshot(device, out, label+'-after', before['layer'])
    stable = before['pid'] == after['pid'] and before['process_start'] == after['process_start']
    same_layer = bool(before['layer'] and before['layer'] == after['layer'])
    available = (same_layer and stable and before.get('presentations', {}).get('returncode') == 0
                 and after.get('presentations', {}).get('returncode') == 0
                 and before.get('layer_corroboration',{}).get('confirmed')
                 and after.get('layer_corroboration',{}).get('confirmed')
                 and before['surface_inventory']['returncode']==0 and after['surface_inventory']['returncode']==0
                 and not before['surface_inventory']['stdout_truncated'] and not after['surface_inventory']['stdout_truncated']
                 and not before['presentations']['stdout_truncated'] and not after['presentations']['stdout_truncated'])
    observed = frames.summarize(before.get('presentations', {}).get('stdout', ''),
                                after.get('presentations', {}).get('stdout', '')) if available else dict(status='UNAVAILABLE_LAYER_PROCESS_OR_QUERY')
    ticks_raw = query(device, 'getconf', 'CLK_TCK')['stdout'].strip()
    ticks = int(ticks_raw) if ticks_raw.isdigit() else 0
    cpu = frames.cpu_interval(dict(monotonic=before['proc_stat']['finish_monotonic'], proc_stat=before['proc_stat']['stdout']),
                              dict(monotonic=after['proc_stat']['finish_monotonic'], proc_stat=after['proc_stat']['stdout']), ticks)
    result = dict(events=events, native_presentations=observed, cpu=cpu,
                  host_measurement_windows=dict(
                    before_presentation_query=before.get('presentations', {}),
                    first_action_start=events[0]['start'] if events else None,
                    last_action_finished=events[-1]['finished'] if events else None,
                    after_presentation_query=after.get('presentations', {}),
                    cpu_start=before['proc_stat']['finish_monotonic'], cpu_end=after['proc_stat']['finish_monotonic'],
                    before_proc_stat_query_seconds=before['proc_stat']['finish_monotonic']-before['proc_stat']['start_monotonic'],
                    after_proc_stat_query_seconds=after['proc_stat']['finish_monotonic']-after['proc_stat']['start_monotonic']),
                  host_and_device_clocks_not_synchronized=True,
                  query_overhead_in_interval=True, no_full_action_FPS_or_jank_or_touch_latency_claim=True,
                  before_fd=len(before['fd']['stdout'].splitlines()) if before['fd']['returncode']==0 else None,
                  after_fd=len(after['fd']['stdout'].splitlines()) if after['fd']['returncode']==0 else None)
    base.save(out / (label + '-measurement.json'), result)
    return result


class Observer:
    def __init__(self, device, out):
        self.device, self.out, self.sequence = device, out, 0
        device.rpc('Addons.ExecuteAddon', dict(addonid=QA))
        self.ready = self.wait('ready.json', lambda r: r.get('pid') == device.pid and r.get('qa') == QA, 30)

    def wait(self, name, valid, seconds):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            self.device.alive()
            raw = self.device.shell('head', '-c', '1048577', QP+'/'+name, check=False)
            base.require(len(raw.encode()) <= 1024*1024, 'BOUNDED_OBSERVER_REPLY')
            try:
                value = json.loads(raw)
                if valid(value):
                    return value
            except ValueError:
                pass
            time.sleep(.15)
        raise TimeoutError('Observer reply: ' + name)

    def call(self, action, *, timeout=25, **kwargs):
        self.sequence += 1
        request = dict(sequence=self.sequence, pid=self.device.pid, action=action, **kwargs)
        path = self.out / 'request.json'
        base.save(path, request)
        self.device.adb('push', path, QP+'/request.pending')
        self.device.shell('mv', QP+'/request.pending', QP+'/request.json')
        reply = self.wait('reply.json', lambda r: r.get('pid') == self.device.pid and r.get('sequence') == self.sequence, timeout)
        base.save(self.out / ('observer-%02d.json' % self.sequence), reply)
        base.require('error' not in reply, 'REAL_OBSERVER_FAILURE:' + str(reply.get('error')))
        return reply['result']


def run(sdk, inputs, out):
    scope = selected()
    base.require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REF') ==
        'refs/heads/work/infinity-2103477-full-performance-ui-stability-20261110', 'EXACT_DISPOSABLE_CI_BRANCH')
    base.require(not out.exists(), 'FRESH_RESULTS'); out.mkdir(parents=True)
    report = dict(status='RUNNING', APK=2103477, starts_requested=0, application_retries=0,
        production_edits=False, shutdown='NOT_SELECTED', physical_Fold='NOT_RUN', thermal_battery='NOT_RUN',
        first_drawn_frame_artwork_and_true_input_latency='NOT_MEASURED_BY_THIS_FIRST_PROBE',
        live_provider_Search_playback_tracking_smoke='NOT_SELECTED_FOR_FIRST_BASELINE_PROBE')
    device, reader = None, None
    try:
        intake = base.load(inputs / 'INTAKE.json')
        base.require(intake['scope_sha256'] == base.sha(HERE/'SCOPE.json') and intake['sha256'] == APK_SHA, 'EXACT_ADMITTED77')
        device = Device(out, sdk)
        report['environment'] = base.environment(device, out)
        base.require(not device.shell('pm', 'list', 'packages', base.PACKAGE).strip(), 'FRESH_VM_ONLY')
        base.root_reconnect(device, out)
        reader = base.start_lifecycle_log(device, out)
        installed = device.adb('install', '--no-streaming', intake['apk'], timeout=300)
        base.require(installed.strip().endswith('Success'), 'NORMAL_ORIGINAL_SIGNED_INSTALL')
        paths = device.shell('pm','path',base.PACKAGE).splitlines()
        base.require(len(paths)==1 and paths[0].startswith('package:/data/app/'), 'ONE_INSTALLED_BASELINE_APK')
        report['installed_APK_sha256'] = device.shell('sha256sum',paths[0][8:],timeout=30).split()[0]
        base.require(report['installed_APK_sha256']==APK_SHA,'EXACT_ACTUAL_INSTALLED77')
        device.shell('mkdir', '-p', base.PROFILE, REMOTE)
        settings = out/'FRESH-FIXTURE-guisettings.xml'
        settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting>'
            '<setting id="general.addonupdates">2</setting><setting id="addons.unknownsources">true</setting>'
            '<setting id="services.esenabled">true</setting><setting id="services.esallinterfaces">true</setting></settings>')
        sources = out/'FRESH-FIXTURE-sources.xml'
        sources.write_text('<sources><files><source><name>Disposable performance observer</name><path pathversion="1">'+REMOTE+'</path><allowsharing>false</allowsharing></source></files></sources>')
        device.adb('push', settings, base.PROFILE+'/guisettings.xml')
        device.adb('push', sources, base.PROFILE+'/sources.xml')
        device.adb('push', intake['observer_path'], REMOTE+intake['observer']['archive'])
        uid = device.shell('stat', '-c', '%u', '/data/user/0/'+base.PACKAGE).strip()
        base.require(uid.isdigit(), 'FRESH_PACKAGE_UID')
        device.shell('chown', '-R', uid+':'+uid, '/data/media/0/Android/data/'+base.PACKAGE)
        device.shell('restorecon', '-RF', '/data/media/0/Android/data/'+base.PACKAGE)
        device.adb('forward', 'tcp:19090', 'tcp:9090')
        report['starts_requested'] = 1
        begun = time.monotonic()
        report['startup'] = base.start_once(device, 2103477, out)
        report['startup_observed_usable_ms'] = 1000*(time.monotonic()-begun)
        report['startup_measurement_limit'] = 'Fresh-profile bootstrap and permission/chooser handling plus polling; not exact first-frame latency or representative owner-cache cold launch'
        comparison = scope['operation']=='signed77-ui-cost-comparison'
        if not comparison:
            for name, args in [('display', ('dumpsys','display')), ('surface-inventory', ('dumpsys','SurfaceFlinger')),
                               ('memory-initial', ('dumpsys','meminfo',str(device.pid)))]:
                base.save(out/(name+'.json'), query(device,*args,timeout=12))
        followup = scope['operation']=='signed77-performance-followup'
        report['reused_first_run'] = scope.get('reuse',{})
        if not followup and not comparison:
            report['idle_home_before_observer'] = scene(device,out,'idle-home', ['idle']*20)
        else:
            report['startup_is_fresh_VM_setup_not_repeated_acceptance_metric'] = True
        if not comparison:
            report['home_horizontal_focus'] = scene(device,out,'home-horizontal', ['Input.Right']*8+['Input.Left']*8)
        gui.install_zip(device, intake['observer'], dict(remote_zip_directory=REMOTE), out, 'performance-observer')
        observer = Observer(device, out)
        report['native_authenticated_CC75'] = observer.ready
        device.rpc('Input.Home')
        ready_started = time.monotonic()
        resident_samples = []
        deadline = ready_started + 60
        while time.monotonic() < deadline:
            current = observer.call('state')
            resident_samples.append(current)
            if (current['resident_context'] and current['resident_current_window']=='10000'
                    and current['properties']['State'] in ('idle','preparing')):
                break
            time.sleep(.25)
        else:
            base.save(out/'RESIDENT-READINESS.json',resident_samples)
            raise TimeoutError('Resident loading observer not ready; no loading preparation sent')
        report['resident_readiness'] = dict(wait_seconds=time.monotonic()-ready_started,samples=resident_samples)
        base.save(out/'RESIDENT-READINESS.json',report['resident_readiness'])
        report['home_frame_focus'] = observer.call('home-focus')
        if comparison:
            report['context_comparison'] = observer.call('context-compare',timeout=90)
            report['read_only_integrity_cost'] = observer.call('skin-integrity-cost',timeout=90)
            report['observer_finished'] = observer.call('finish')
            base.crash_free_alive(device)
            report['status'] = 'COMPLETED_SELECTED_ACTUAL_SOURCE_COST_COMPARISON_NOT_PRODUCTION_PATCH_OR_RELEASE'
            return
        report['loading'] = []
        for outcome in ('ready','ready','failed'):
            report['loading'].append(observer.call('loading',outcome=outcome))
            time.sleep(.137)
        report['hub'] = observer.call('hub')
        report['hub_vertical_focus'] = scene(device,out,'hub-vertical', ['Input.Down']*5+['Input.Up']*5)
        report['loading'].append(observer.call('loading',outcome='context-cancel'))
        device.rpc('Input.Home')
        before = device.pid
        device.shell('input','keyevent','3')  # Android Home: background only, not app shutdown.
        time.sleep(2)
        begun = time.monotonic()
        device.shell('am','start','-W','-n',base.PACKAGE+'/.Main',timeout=30)
        device.alive()
        report['warm_foreground_return'] = dict(same_pid=device.pid==before,
            request_return_ms=1000*(time.monotonic()-begun), scope='Same-process foreground return, not cold launch/first rendered frame')
        report['observer_finished'] = observer.call('finish')
        report['idle_home_after_observer'] = scene(device,out,'idle-home-after-probe', ['idle']*20)
        base.save(out/'memory-final.json',query(device,'dumpsys','meminfo',str(device.pid),timeout=12))
        device.screenshot('final-home')
        base.crash_free_alive(device)
        report['status'] = 'COMPLETED_SELECTED_BASELINE_MEASUREMENTS_NOT_RELEASE_OR_PERFORMANCE_PASS'
    except Exception:
        report.update(status='FAILED_OR_BLOCKED_SELECTED_BASELINE', error=traceback.format_exc())
        if device:
            try:
                base.capture_failure(device, out)
            except Exception as error:
                report['failure_capture_error'] = repr(error)
        raise
    finally:
        if device:
            for source, target in [(base.HOME+'/temp/kodi.log',out/'kodi.log'),
                                   (QP,out/'observer-profile')]:
                try:
                    device.adb('pull',source,target,timeout=15,check=False)
                except Exception as error:
                    report.setdefault('collection_errors',[]).append(dict(source=source,error=repr(error)))
        if reader:
            try:
                report['lifecycle_reader'] = base.stop_lifecycle_log(reader,out)
            except Exception as error:
                report['reader_collection_error'] = repr(error)
        base.save(out/'BASELINE-PERFORMANCE.json',report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation',choices=('admit','run'))
    parser.add_argument('--sdk',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--inputs',type=Path)
    args = parser.parse_args()
    admit(args.sdk,args.out) if args.operation=='admit' else run(args.sdk,args.inputs,args.out)
