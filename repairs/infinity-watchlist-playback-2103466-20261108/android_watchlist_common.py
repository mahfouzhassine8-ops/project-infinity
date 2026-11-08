"""Host-only reuse of retained, selected helpers; never invokes either old main."""
import ast
import codecs
import socket
import hashlib
import json
import os
import signal
import time
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RETAINED = '2f18336ec766cf6e0234ecf7e9727ab4993247ff'
CC = 'script.infinity.commandcenter'
QA = 'script.infinity.finalreleaseqa'
PACKAGE = 'com.projectinfinity.kodi'
HOME = '/sdcard/Android/data/' + PACKAGE + '/files/.kodi'
PROFILE = HOME + '/userdata'
QAROOT = PROFILE + '/addon_data/' + QA


def retained(path):
    return subprocess.check_output(['git', 'show', RETAINED + ':' + path], cwd=ROOT)


def selected_function(path, name, namespace):
    source = retained(path)
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise RuntimeError('Exact retained function missing: ' + name)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), path, 'exec'), namespace)
    return namespace[name]


def checked_observer(source):
    return selected_function('repairs/infinity-three-corrections-20261108/stage_three_android.py',
                             'checked_observer', {'ast': ast})(source)


def device_class():
    # Supply the unchanged measured OS tutorial helper to the retained Device import.
    # Its historical image self-test/main is not executed.
    import io, os, re, time
    from PIL import Image
    module = types.ModuleType('immersive_prompt')
    module.__dict__.update(io=io, json=json, os=os, re=re, subprocess=subprocess, time=time, Image=Image)
    module.locate = selected_function('repairs/infinity-preview-2103450-fullscreen-display/android-qa/immersive_prompt.py',
                                     'locate', module.__dict__)
    sys.modules['immersive_prompt'] = module
    # Only the retained transport factory executes; neither broad run/main is loaded.
    namespace = dict(subprocess=subprocess, HERE=ROOT / 'repairs/infinity-three-corrections-20261108',
                     ROOT=ROOT, OLD=ROOT / 'repairs/infinity-final-release-462-20261107',
                     PROVIDERS={'plugin.video.pov', 'plugin.video.umbrella'}, QA=QA, QAROOT=QAROOT)
    RetainedDevice = selected_function('repairs/infinity-three-corrections-20261108/verify_three_android.py',
                                       'transport', namespace)()

    class DeadlineDevice(RetainedDevice):
        def rpc(self, method, params=None, timeout=25):
            started = time.monotonic()
            deadline = started + timeout
            received = 0
            status = 'RUNNING'
            error = None
            started_epoch = time.time()

            def mark():
                value = dict(method=str(method)[:256], status=status,
                             started_epoch=started_epoch, timeout_seconds=timeout,
                             elapsed_seconds=time.monotonic() - started,
                             received_bytes=received)
                if error is not None:
                    value['error'] = error[:1000]
                try:
                    path = Path(self.out) / 'RPC-LAST.json'
                    temporary = path.with_suffix('.pending')
                    temporary.write_text(json.dumps(value, indent=2) + '\n')
                    temporary.replace(path)
                except OSError:
                    pass  # Diagnostic I/O cannot replace the original RPC result/error.

            def remaining():
                value = deadline - time.monotonic()
                if value <= 0:
                    raise TimeoutError('Absolute JSONRPC deadline exceeded: ' + method)
                return min(timeout, value)

            try:
                mark()
                request = dict(jsonrpc='2.0', id=464, method=method)
                if params is not None:
                    request['params'] = params
                with socket.create_connection(('127.0.0.1', 19090), timeout=remaining()) as conn:
                    conn.settimeout(remaining())
                    conn.sendall(json.dumps(request).encode())
                    decoder = json.JSONDecoder()
                    utf8 = codecs.getincrementaldecoder('utf-8')()
                    pending = ''
                    limit = 8 * 1024 * 1024
                    while received < limit:
                        conn.settimeout(remaining())
                        chunk = conn.recv(min(65536, limit - received))
                        if not chunk:
                            break
                        received += len(chunk)
                        pending += utf8.decode(chunk)
                        while pending.strip():
                            remaining()
                            pending = pending.lstrip()
                            try:
                                reply, end = decoder.raw_decode(pending)
                            except ValueError:
                                break
                            pending = pending[end:]
                            if reply.get('id') != 464:
                                continue
                            if 'error' in reply:
                                raise RuntimeError(method + ': ' + json.dumps(reply['error']))
                            remaining()
                            status = 'DONE'
                            return reply.get('result')
                raise RuntimeError('Incomplete bounded JSONRPC reply: ' + method)
            except BaseException as caught:
                status = 'FAIL'
                if isinstance(caught, TimeoutError) and time.monotonic() >= deadline:
                    error = 'TimeoutError: Absolute JSONRPC deadline exceeded: ' + method
                    raise TimeoutError('Absolute JSONRPC deadline exceeded: ' + method) from caught
                error = type(caught).__name__ + ': ' + str(caught)
                raise
            finally:
                mark()

    return DeadlineDevice


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def producer_pins():
    tree = ast.parse((HERE / 'overlay' / CC / 'saved_playback.py').read_text())
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PRODUCERS' for t in node.targets))


PINNED_EMULATOR_ACTION='a421e43855164a8197daf9d8d40fe71c6996bb0d'
DISPOSABLE_AVD='infinity-four-repair-api37'


def _host_process(pid):
    try:
        root=Path('/proc')/str(int(pid))
        if root.stat().st_uid!=os.getuid():return None
        fields=(root/'stat').read_text().rsplit(') ',1)[1].split()
        if fields[0]=='Z':return None
        return dict(pid=int(pid),parent=int(fields[1]),start=fields[19],
                    exe=str((root/'exe').resolve()),
                    args=[x.decode(errors='replace') for x in (root/'cmdline').read_bytes().split(b'\0') if x])
    except (OSError,ValueError,IndexError):return None


def _emulator_target(process,sdk,port):
    if not process:return False
    try:
        args=process['args']
        return (Path(process['exe']).is_relative_to(Path(sdk)/'emulator') and
                Path(process['exe']).name in ('emulator','qemu-system-x86_64','qemu-system-x86_64-headless') and
                args[args.index('-avd')+1]==DISPOSABLE_AVD and args[args.index('-port')+1]==str(port))
    except (ValueError,IndexError):return False


def _action_target(process):
    suffix='/_actions/reactivecircus/android-emulator-runner/'+PINNED_EMULATOR_ACTION+'/lib/main.js'
    return bool(process and Path(process['exe']).name in ('node','node24') and
                any(arg.lower().endswith(suffix) for arg in process['args']))


def _host_disposal_worker(spec):
    """CI host processes only, after the verifier exits; never sends Kodi commands."""
    out=Path(spec['out']);events=[]
    def record(status):
        value=dict(status=status,scope='disposable CI emulator/action host cleanup only',events=events,
                   application_shutdown_test=False,final_report_sha256=spec['report_sha256'])
        path=out/'HOST-DISPOSAL.json';temp=path.with_suffix('.pending')
        temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)
    if os.environ.get('GITHUB_ACTIONS')!='true':return
    parent=spec['parent'];deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        current=_host_process(parent['pid'])
        if not current or current['start']!=parent['start']:break
        time.sleep(.2)
    else:record('NOT_DISPOSED_VERIFIER_STILL_RUNNING');return
    if sha(out/'ANDROID-VERIFICATION.json')!=spec['report_sha256']:record('NOT_DISPOSED_REPORT_CHANGED');return
    time.sleep(20)  # Allow the pinned action's normal adb emu kill first.
    def same(target,kind):
        current=_host_process(target['pid'])
        return (current if current and current['start']==target['start'] and current['exe']==target['exe'] and
                (_emulator_target(current,spec['sdk'],spec['port']) if kind=='emulator' else _action_target(current)) else None)
    def send(target,kind,sig):
        if not same(target,kind):return
        if not hasattr(os,'pidfd_open') or not hasattr(signal,'pidfd_send_signal'):
            events.append(dict(kind=kind,pid=target['pid'],outcome='NO_PIDFD_NO_SIGNAL'));return
        try:
            fd=os.pidfd_open(target['pid'])
            try:
                if same(target,kind):
                    signal.pidfd_send_signal(fd,sig);events.append(dict(kind=kind,pid=target['pid'],signal=sig))
            finally:os.close(fd)
        except ProcessLookupError:pass
    for sig in (signal.SIGTERM,signal.SIGKILL):
        for target in spec['emulators']:send(target,'emulator',sig)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline and any(same(t,'emulator') for t in spec['emulators']):time.sleep(.2)
    node=spec.get('node');deadline=time.monotonic()+10
    while node and same(node,'node') and time.monotonic()<deadline:time.sleep(.2)
    if node and same(node,'node') and spec['report_status'].startswith('FAIL'):
        record('INFRASTRUCTURE_FAIL_PINNED_ACTION_CLEANUP_BOUND')
        for sig in (signal.SIGTERM,signal.SIGKILL):
            send(node,'node',sig)
            deadline=time.monotonic()+5
            while same(node,'node') and time.monotonic()<deadline:time.sleep(.2)
        record('INFRASTRUCTURE_FAIL_PINNED_ACTION_CLEANUP_BOUND');return
    if node and same(node,'node'):record('INFRASTRUCTURE_PENDING_NODE_LEFT_TO_STEP_TIMEOUT');return
    if any(same(t,'emulator') for t in spec['emulators']):
        record('INFRASTRUCTURE_FAIL_EMULATOR_PROCESS_REMAINS');return
    record('HOST_DISPOSAL_FINISHED_NO_APPLICATION_SHUTDOWN_CLAIM')


def arm_host_disposal(device,out):
    """Detach with closed stdio so this watchdog cannot retain action pipes."""
    if os.environ.get('GITHUB_ACTIONS')!='true':return
    out=Path(out).resolve();path=out/'HOST-DISPOSAL-ARM.json'
    try:
        serial=device.serial
        if not serial.startswith('emulator-') or not serial.removeprefix('emulator-').isdigit():raise RuntimeError('Disposable emulator serial required')
        sdk=str(Path(os.environ['ANDROID_HOME']).resolve());port=int(serial.removeprefix('emulator-'))
        qemu=subprocess.check_output([str(device.adb_bin),'-s',serial,'shell','getprop','ro.kernel.qemu'],timeout=5,text=True).strip()
        avd=subprocess.check_output([str(device.adb_bin),'-s',serial,'emu','avd','name'],timeout=5,text=True).splitlines()
        if qemu!='1' or not avd or avd[0].strip()!=DISPOSABLE_AVD:raise RuntimeError('Exact disposable CI AVD required')
        targets=[p for name in Path('/proc').iterdir() if name.name.isdigit() and _emulator_target(p:=_host_process(int(name.name)),sdk,port)]
        if not targets:raise RuntimeError('No exact SDK emulator process; no broad process signal allowed')
        parent=_host_process(os.getpid());node=None;ancestor=parent
        for _ in range(16):
            if not ancestor:break
            if _action_target(ancestor):node=ancestor;break
            ancestor=_host_process(ancestor['parent'])
        report=json.loads((out/'ANDROID-VERIFICATION.json').read_text())
        spec=dict(out=str(out),sdk=sdk,port=port,parent=parent,node=node,emulators=targets,
                  report_status=report['status'],report_sha256=sha(out/'ANDROID-VERIFICATION.json'))
        # argv contains only this bounded host-process spec, no credentials or APK payload.
        code="import runpy,sys,json; m=runpy.run_path(sys.argv[1]); m['_host_disposal_worker'](json.loads(sys.argv[2]))"
        env={key:os.environ[key] for key in ('PATH','GITHUB_ACTIONS','PYTHONDONTWRITEBYTECODE') if key in os.environ}
        child=subprocess.Popen([sys.executable,'-c',code,str(Path(__file__).resolve()),json.dumps(spec)],
                               stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                               start_new_session=True,close_fds=True,env=env)
        path.write_text(json.dumps(dict(status='ARMED_AFTER_FINAL_REPORT',watchdog_pid=child.pid,
                                      emulator_pids=[p['pid'] for p in targets],node_pid=node['pid'] if node else None,
                                      report_status=report['status'],final_report_sha256=spec['report_sha256']),indent=2)+'\n')
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.SubprocessError) as error:
        try:path.write_text(json.dumps(dict(status='NOT_ARMED_SCOPE_OR_CAPTURE_UNAVAILABLE',error=str(error)[:1000]),indent=2)+'\n')
        except OSError:pass
