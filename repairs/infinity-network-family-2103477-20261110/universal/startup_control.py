"""One selected first-start control per exact frozen APK; no playback or repair."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import threading
import time
import traceback

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
ROOT = TASK.parents[1]
OLD = ROOT / 'repairs/infinity-tracking-integration-2103469-20261108'
sys.path.insert(0, str(OLD))
import qualify_android_baseline as base

CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'


def require(value, label):
    if not value:
        raise RuntimeError(label)


def selected(version):
    request = base.load(HERE / 'STARTUP-CONTROL-REQUEST.json')
    require(request['operation'] == 'matched-frozen77-78-first-start-only', 'EXACT_STARTUP_CONTROL_SELECTION')
    require(version in request['versions'] and request['starts_per_VM'] == 1 and
            request['playback_tests'] is False and request['shutdown_tests'] is False and
            request['production_changes'] is False and request['signing'] is False, 'ONE_START_NO_PLAYBACK_OR_MUTATION')
    for name, digest in request['source_bindings'].items():
        require(base.sha(ROOT / name) == digest, 'EXACT_SELECTED_TOOL:' + name)
    return request


def admit(version, sdk, out):
    request = selected(version)
    require(not out.exists(), 'FRESH_CONTROL_INPUTS')
    helper = OLD / 'tracking_module_fixture.py'
    require(base.sha(helper) == 'af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb', 'ORIGINAL_ARTIFACT_INTAKE')
    spec = importlib.util.spec_from_file_location('unchanged_original_artifact_intake', helper)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    row = request['artifacts'][str(version)]
    files = module.download(row, out)
    apk = files / ('Infinity-%d-Combined-Original-Signer.apk' % version)
    require(base.sha(apk) == request['APK_sha256'][str(version)], 'EXACT_FROZEN_APK')
    signature = base.command([sdk / 'build-tools/35.0.0/apksigner', 'verify', '--verbose', '--print-certs', apk], timeout=60)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [CERT], 'ORIGINAL_SIGNER')
    (out / 'SIGNATURE.txt').write_text(signature)
    base.save(out / 'INTAKE.json', dict(version=version, apk=str(apk.resolve()), sha256=base.sha(apk),
              artifact=row, request_sha256=base.sha(HERE / 'STARTUP-CONTROL-REQUEST.json'),
              status='PASS_FROZEN_INPUTS_ONLY_APPLICATION_NOT_STARTED'))


def log_limit():
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024, 32 * 1024 * 1024))


def capture_all_logcat(device, out):
    args = ['timeout', '--signal=TERM', '--kill-after=2', '600', str(device.adb_bin), '-s', device.serial,
            'logcat', '-b', 'all', '-v', 'threadtime']
    base.save(out / 'LOGCAT-COMMAND.json', dict(argv=args, byte_limit=32*1024*1024,
              filters='NONE', scope='Fresh disposable VM; no owner account or device', buffer_clear=False))
    with (out / 'all-logcat.txt').open('wb') as stdout, (out / 'all-logcat.stderr').open('wb') as stderr:
        return subprocess.Popen(args, stdout=stdout, stderr=stderr, preexec_fn=log_limit)


def diagnostic(device, args, timeout=4):
    """Keep failed reads distinguishable from empty successful output."""
    started = time.time()
    result = subprocess.run([str(device.adb_bin), '-s', device.serial, *args],
                            capture_output=True, timeout=timeout)
    return dict(argv=args, returncode=result.returncode,
                stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace'),
                started_epoch=started, finished_epoch=time.time())


def process_detail(device, out, pid, stage):
    for name, args in [('stat', ['cat', '/proc/'+pid+'/stat']),
                       ('maps', ['head', '-c', '2097153', '/proc/'+pid+'/maps']),
                       ('threads', ['ps', '-T', '-p', pid, '-o', 'PID,TID,NAME'])]:
        path = out / ('pid-'+pid+'-'+stage+'-'+name)
        try:
            result = diagnostic(device, ['shell', *args], timeout=2)
            text = result.pop('stdout')
            result.update(stdout_bytes=len(text.encode()), truncated=len(text.encode()) > 2097152)
            path.with_suffix('.txt').write_text(text)
            base.save(path.with_suffix('.json'), result)
        except Exception as error:
            base.save(path.with_suffix('.json'), dict(error=repr(error), argv=args))


def process_samples(device, out, stop):
    seen = {}
    with (out / 'PID-GENERATIONS.jsonl').open('w') as stream:
        while not stop.is_set():
            row = dict(epoch=time.time(), monotonic=time.monotonic())
            try:
                query = diagnostic(device, ['shell','pidof',base.PACKAGE+':kodi'], timeout=2)
                pids = query['stdout'].strip().split()
                row['pidof'] = query
                row['native_pids'] = pids
                for value in pids:
                    if not value.isdigit():
                        continue
                    if value not in seen:
                        seen[value] = dict(first=time.monotonic(), samples={0})
                        process_detail(device,out,value,'initial')
                    else:
                        for seconds in (3,6):
                            if seconds not in seen[value]['samples'] and time.monotonic()-seen[value]['first'] >= seconds:
                                seen[value]['samples'].add(seconds)
                                process_detail(device,out,value,'after-'+str(seconds)+'s')
            except Exception as error:
                row['error'] = repr(error)
            stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush()
            stop.wait(.25)


def tombstones(device, out):
    """Capture every matching process generation through existing CI permissions."""
    report = dict(read_only=True, files=[], errors=[], partial_crash_buffer_is_not_full_tombstone=True,
                  complete_file_does_not_guarantee_resolved_guest_unwind=True)
    try:
        producer = diagnostic(device,['shell','pidof','crash_dump64'],timeout=3)
        report['producer_query'] = producer
        producer_finished = producer['returncode'] == 1 and not producer['stdout'].strip() and not producer['stderr'].strip()
        names = device.shell('ls', '-t', '/data/tombstones', timeout=4).splitlines()
        for name in [n for n in names if re.fullmatch(r'tombstone_[0-9]+', n)][:12]:
            remote = '/data/tombstones/' + name
            try:
                size = device.shell('stat', '-c', '%s', remote, timeout=3).strip()
                require(size.isdigit() and int(size) <= 8*1024*1024, 'BOUNDED_FULL_TEXT_TOMBSTONE')
                raw = device.adb('exec-out', 'cat', remote, timeout=6, binary=True)
                require(len(raw) == int(size), 'COMPLETE_TOMBSTONE_BYTES')
                if base.PACKAGE.encode() not in raw:
                    continue
                again = device.shell('stat','-c','%s',remote,timeout=3).strip()
                producer_after = diagnostic(device,['shell','pidof','crash_dump64'],timeout=3)
                after_finished = (producer_after['returncode']==1 and not producer_after['stdout'].strip()
                                  and not producer_after['stderr'].strip())
                text = raw.decode(errors='replace')
                pid = re.search(r'(?m)^pid:\s*([0-9]+)',text)
                stamp = re.search(r'(?m)^Timestamp:\s*(.*)',text)
                (out / (name+'.txt')).write_bytes(raw)
                record = dict(name=name, text_bytes=len(raw), text_sha256=hashlib.sha256(raw).hexdigest(),
                              complete_text=producer_finished and after_finished and again==size,
                              producer_finished_before_and_after=producer_finished and after_finished,
                              producer_after_query=producer_after, size_stable=again==size,
                              pid=int(pid[1]) if pid else None, timestamp=stamp[1] if stamp else None,
                              matches_first_startup_runner_PID=bool(pid and int(pid[1])==device.pid))
                report['files'].append(record)
                proto = remote + '.pb'
                proto_stat = diagnostic(device,['shell','stat','-c','%s',proto],timeout=3)
                record['proto_stat'] = proto_stat
                length = proto_stat['stdout'].strip() if proto_stat['returncode']==0 else ''
                if length.isdigit() and 0 < int(length) <= 8*1024*1024:
                    try:
                        data = device.adb('exec-out', 'cat', proto, timeout=6, binary=True)
                        if len(data) == int(length):
                            (out / (name+'.pb')).write_bytes(data)
                            record.update(proto_bytes=len(data), proto_sha256=hashlib.sha256(data).hexdigest())
                        else:
                            record['proto_error'] = 'INCOMPLETE_PROTO_BYTES'
                    except Exception as error:
                        record['proto_error'] = repr(error)
                else:
                    record['proto_error'] = 'UNAVAILABLE_OR_EXCEEDS_SELECTED_CAPTURE_LIMIT'
            except Exception as error:
                report['errors'].append(dict(name=name, error=repr(error)))
    except Exception as error:
        report['errors'].append(dict(error=repr(error)))
    report['matching_complete_text_captured'] = any(row['complete_text'] for row in report['files'])
    base.save(out / 'TOMBSTONE-CAPTURE.json', report)


def run(version, inputs, sdk, out):
    request = selected(version)
    require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GITHUB_REF') ==
            'refs/heads/work/infinity-network-family-from-2103477-20261109', 'SELECTED_CI_BRANCH_ONLY')
    require(not out.exists(), 'FRESH_CONTROL_RESULTS'); out.mkdir(parents=True)
    report = dict(version=version, status='RUNNING', starts_requested=0, automatic_retries=0,
                  playback='NOT_SELECTED', shutdown='NOT_SELECTED', physical_Fold='NOT_TESTED')
    device, log, sampler = None, None, None
    stopped = threading.Event()
    try:
        intake = base.load(inputs / 'INTAKE.json')
        require(intake['request_sha256'] == base.sha(HERE / 'STARTUP-CONTROL-REQUEST.json') and
                intake['version'] == version and base.sha(Path(intake['apk'])) == request['APK_sha256'][str(version)], 'EXACT_ADMITTED_CONTROL')
        device = base.Device(out, sdk)
        report['environment'] = base.environment(device, out)
        require(not device.shell('pm', 'list', 'packages', base.PACKAGE).strip(), 'FRESH_VM_NO_PREEXISTING_APP')
        base.root_reconnect(device, out)
        log = capture_all_logcat(device, out)
        result = device.adb('install', '--no-streaming', intake['apk'], timeout=300)
        require(result.strip().endswith('Success'), 'NORMAL_SIGNED_PACKAGE_INSTALL')
        paths = device.shell('pm', 'path', base.PACKAGE).splitlines()
        require(len(paths) == 1 and paths[0].startswith('package:/data/app/'), 'ONE_INSTALLED_APK')
        actual = device.shell('sha256sum', paths[0][8:], timeout=30).split()[0]
        require(actual == intake['sha256'], 'ACTUAL_INSTALLED_FROZEN_BYTES')
        device.shell('mkdir', '-p', base.PROFILE)
        settings = out / 'HARNESS-BOOTSTRAP-guisettings.xml'
        settings.write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting>'
            '<setting id="general.addonupdates">2</setting><setting id="services.esenabled">true</setting>'
            '<setting id="services.esallinterfaces">true</setting></settings>')
        advanced = out / 'HARNESS-BOOTSTRAP-advancedsettings.xml'
        advanced.write_text('<advancedsettings><loglevel hide="false">1</loglevel></advancedsettings>')
        device.adb('push', settings, base.PROFILE+'/guisettings.xml')
        device.adb('push', advanced, base.PROFILE+'/advancedsettings.xml')
        uid = device.shell('stat', '-c', '%u', '/data/user/0/'+base.PACKAGE).strip()
        require(uid.isdigit(), 'ACTUAL_FRESH_PACKAGE_UID')
        device.shell('chown', '-R', uid+':'+uid, '/data/media/0/Android/data/'+base.PACKAGE)
        device.shell('restorecon', '-RF', '/data/media/0/Android/data/'+base.PACKAGE)
        device.adb('forward', 'tcp:19090', 'tcp:9090')
        sampler = threading.Thread(target=process_samples, args=(device,out,stopped), daemon=True)
        sampler.start()
        report.update(starts_requested=1, first_launch_epoch=time.time(), actual_installed_sha256=actual,
                      application_uid=int(uid), profile='FRESH_VM_HARNESS_BOOTSTRAP_NOT_OWNER_DATA')
        base.save(out/'STARTUP-CONTROL.json', report)
        report['startup'] = base.start_once(device, version, out)
        process_detail(device,out,str(device.pid),'observed-home')
        until = time.monotonic() + request['stable_after_home_seconds']
        while time.monotonic() < until:
            base.crash_free_alive(device)
            time.sleep(.5)
        device.screenshot('observed-home')
        report['status'] = 'PASS_ONE_SELECTED_FIRST_START_ONLY_NOT_INTERMITTENT_CRASH_RESOLUTION'
    except Exception:
        report.update(status='FAIL_OR_BLOCKED_SELECTED_FIRST_START', error=traceback.format_exc())
        if device:
            # The existing bounded collector retains the first PID, including death.
            try:
                base.capture_failure(device, out)
            except Exception as error:
                report['original_capture_error'] = repr(error)
        raise
    finally:
        if device:
            tombstones(device, out)
            for name, args in [('final-crash-buffer.txt', ['logcat','-b','crash','-d']),
                               ('final-processes.txt', ['ps','-A']),
                               ('final-activities.txt', ['dumpsys','activity','activities']),
                               ('dropbox-native-crashes.txt', ['dumpsys','dropbox','--print','SYSTEM_TOMBSTONE'])]:
                try:
                    result = diagnostic(device,['shell',*args],timeout=8)
                    text = result.pop('stdout')
                    result.update(stdout_bytes=len(text.encode()), truncated=len(text.encode()) > 8*1024*1024)
                    (out/name).write_text(text[:8*1024*1024])
                    base.save(out/(name+'.result.json'),result)
                except Exception as error:
                    (out/(name+'.error')).write_text(repr(error))
            for name in ('kodi.log','kodi.old.log'):
                try:
                    result = diagnostic(device,['pull',base.HOME+'/temp/'+name,str(out/name)],timeout=8)
                    base.save(out/(name+'.pull.json'),result)
                except Exception as error:
                    base.save(out/(name+'.pull.json'),dict(error=repr(error)))
        stopped.set()
        if sampler:
            sampler.join(timeout=12)
            report['sampler_finished'] = not sampler.is_alive()
        if log:
            log.terminate()
            try:
                log.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log.kill(); log.wait(timeout=3)
            report['logcat_exit_code'] = log.returncode
            report['all_logcat_limit_reached'] = (out/'all-logcat.txt').stat().st_size >= 32*1024*1024
        report['first_startup_runner_observed_native_pid'] = device.pid if device else None
        report['sampler_generations_recorded_separately'] = 'PID-GENERATIONS.jsonl'
        report['subsequent_OS_restart_does_not_clear_first_failure'] = True
        base.save(out/'STARTUP-CONTROL.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['admit','run'])
    parser.add_argument('--version', type=int, choices=[2103477,2103478], required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--inputs', type=Path)
    args = parser.parse_args()
    if args.operation == 'admit':
        admit(args.version,args.sdk,args.out)
    else:
        run(args.version,args.inputs,args.sdk,args.out)
