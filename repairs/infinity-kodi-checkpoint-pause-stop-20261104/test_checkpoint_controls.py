#!/usr/bin/env python3
"""Run only the preselected source-extracted host checks. Never build Kodi/APKs."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
MESSENGER = 'xbmc/messaging/ApplicationMessenger.cpp'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def function(text, signature):
    start = text.index(signature)
    opening = text.index('{', start)
    depth, index = 1, opening + 1
    while depth:
        depth += (text[index] == '{') - (text[index] == '}')
        index += 1
    return text[start:index]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    selection = json.loads((HERE / 'SELECTED-TESTS.json').read_text())
    delta = json.loads((HERE / 'SOURCE-DELTA.json').read_text())
    source_map = json.loads(Path('/tmp/kodi451-restored-proof/CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    bindings = {}

    def read(relative):
        value = (args.native / relative).read_bytes()
        assert sha(value) == source_map[relative], relative
        bindings[relative] = sha(value)
        return value.decode()

    before = read(MESSENGER)
    candidate = (HERE / 'candidate' / MESSENGER).read_bytes()
    assert sha(before.encode()) == delta['before'][MESSENGER]
    assert sha(candidate) == delta['after'][MESSENGER]
    header = read('xbmc/messaging/ApplicationMessenger.h')
    action_ids = read('xbmc/input/actions/ActionIDs.h')
    windows = read('xbmc/guilib/WindowIDs.h')
    android = read('xbmc/platform/android/activity/XBMCApp.cpp')
    application = read('xbmc/application/Application.cpp')
    window_manager = read('xbmc/guilib/GUIWindowManager.cpp')
    checkpoint = read('xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp')
    # Bind the real message/target/action declarations too; host substitutes are explicit.
    for relative in ['xbmc/messaging/ThreadMessage.h', 'xbmc/messaging/IMessageTarget.h',
                     'xbmc/input/actions/Action.h',
                     'xbmc/platform/android/activity/InfinityAndroidCheckpoint.h']:
        read(relative)
    assert 'void Stop() { m_bStop = true; }' in header
    assert 's.active.store(false)' not in checkpoint
    assert checkpoint.count('s.active.store(true)') == 1

    constants = '\n'.join(re.findall(r'^#define TMSG_.*$', header, re.M))
    constants += '\n' + re.search(r'^#define WINDOW_INVALID\s+.*$', windows, re.M)[0]
    constants += '\n' + '\n'.join(re.findall(r'^#define PLAYBACK_STATE_.*$', android, re.M))
    for name in ('ACTION_PAUSE', 'ACTION_STOP', 'ACTION_PLAYER_PLAY', 'ACTION_MOVE_LEFT'):
        constants += '\n' + re.search(r'^constexpr const int ' + name + r' = \d+;$', action_ids, re.M)[0]

    selected_bodies = {}
    common = []

    def keep(name, value):
        selected_bodies[name] = {'sha256': sha(value.encode()), 'bytes': len(value.encode())}
        return value

    for signature in ('void CXBMCApp::onResume()', 'void CXBMCApp::onPause()',
                      'void CXBMCApp::onStop()', 'void CXBMCApp::onAudioFocusChange(int focusChange)'):
        common.append(keep(signature, function(android, signature)))
    for signature in ('bool AllowNativeWrite(const char*)',
                      'CheckpointWriteGuard::CheckpointWriteGuard(const char* name)',
                      'CheckpointWriteGuard::~CheckpointWriteGuard()'):
        common.append('namespace InfinityAndroidCheckpoint {\n' + keep(signature, function(checkpoint, signature)) + '\n}')

    onaction = function(application, 'bool CApplication::OnAction(const CAction &action)')
    onaction_guard = onaction[:onaction.index('#endif') + len('#endif')]
    common.append(keep('OnAction exact checkpoint prefix', onaction_guard) + '''
  // Normal playback stands in for real player work in this HOST peer only.
  (void)action;
  ++playerCommands;
  InfinityAndroidCheckpoint::CheckpointWriteGuard guard("playback-command");
  assert(guard);return true;
}''')
    process = function(application, 'void CApplication::Process()')
    process_guard = process[:process.index('#endif') + len('#endif')]
    common.append(keep('Process exact checkpoint prefix', process_guard) + '''
  // Normal render/script/frame work is outside this host test.
  ++normalFrames;
  CServiceBroker::GetAppMessenger()->ProcessWindowMessages();
  CServiceBroker::GetAppMessenger()->ProcessMessages();
}''')
    app_message = function(application, 'void CApplication::OnApplicationMessage(ThreadMessage* pMsg)')
    app_guard = app_message[:app_message.index('#endif') + len('#endif')]
    common.append(keep('OnApplicationMessage exact checkpoint prefix', app_guard) + '''
  if(pMsg->dwMessage==TMSG_DISPLAY_SETUP||pMsg->dwMessage==TMSG_DISPLAY_DESTROY){
    displayBarrier.pause();displayObserved.push_back(pMsg->dwMessage);
    if(enqueueDisplayDuringHandler){enqueueDisplayDuringHandler=false;CServiceBroker::GetAppMessenger()->PostMsg(TMSG_DISPLAY_DESTROY);}
    pMsg->SetResult(42);
  }else otherObserved.push_back(pMsg->dwMessage);
}''')
    start = window_manager.index('  case TMSG_GUI_ACTION:')
    end = window_manager.index('  case TMSG_GUI_MESSAGE:', start)
    action_case = window_manager[start:end]
    common.append('''void CGUIWindowManager::OnApplicationMessage(ThreadMessage* pMsg){
  if(pMsg->dwMessage==TMSG_GUI_ACTION){++guardReceivers;if(pMsg->lpVoid)controlObserved.push_back(static_cast<CAction*>(pMsg->lpVoid)->GetID());}
  switch(pMsg->dwMessage){
''' + keep('GUIWindowManager exact GUI_ACTION case', action_case) + '''
  default:otherObserved.push_back(pMsg->dwMessage);break;
  }
}''')

    signatures = ['void CApplicationMessenger::Cleanup()',
                  'int CApplicationMessenger::SendMsg(ThreadMessage&& message, bool wait)',
                  'void CApplicationMessenger::ProcessMessages()',
                  'void CApplicationMessenger::ProcessWindowMessages()',
                  'void CApplicationMessenger::ProcessMessage(ThreadMessage *pMsg)',
                  'bool CApplicationMessenger::IsProcessThread() const',
                  'void CApplicationMessenger::ProcessCheckpointDisplayMessages()']
    report = {
        'scope': 'source-extracted host checks only; no Android/native-engine build or acceptance',
        'source_bindings': bindings,
        'candidate_sha256': sha(candidate),
        'selected_bodies': selected_bodies,
        'boundaries': ['CEvent/critical-section/ThreadMessage storage are host peers',
                       'real native Android callback bodies execute with Android service peers',
                       'real GUI_ACTION receiver branch and application checkpoint prefixes',
                       'real native write-guard bodies, reduced coordinator state',
                       'checkpoint Pump, native EGL, codecs, graphics lock and player work are peers',
                       'baseline and negative-case synthetic payload cleanup is test-only rescue'],
        'tests': [], 'complete': False, 'android_verified': False,
    }
    output = args.out / 'HOST-RESULTS.json'

    def save():
        output.write_text(json.dumps(report, indent=2) + '\n')

    save()
    for mode, source in [('before', before), ('after', candidate.decode())]:
        bodies = []
        if mode == 'after':
            bodies.append(keep('IsCheckpointPlaybackControl candidate', function(source, 'bool IsCheckpointPlaybackControl(const ThreadMessage& message)')))
        for signature in signatures:
            body = function(source, signature)
            bodies.append(keep(mode + ': ' + signature, body))
            if mode == 'after' and 'ProcessCheckpointDisplayMessages' not in signature:
                assert body == function(before, signature), signature
        cpp = args.out / (mode + '.cpp')
        cpp.write_text(constants + '\n' + (HERE / 'host_peers.cpp.in').read_text() + '\n' +
                       '\n'.join(bodies + common) + '\n' + (HERE / 'host_cases.cpp.in').read_text())
        exe = args.out / mode
        command = ['g++', '-std=c++17', '-pthread', '-Wall', '-Wextra', '-Werror',
                   '-DTARGET_ANDROID', str(cpp), '-o', str(exe)]
        compile_result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        (args.out / (mode + '-compile.txt')).write_text(compile_result.stdout + compile_result.stderr)
        report[mode + '_compile'] = {'returncode': compile_result.returncode, 'command': command,
                                    'harness_cpp_sha256': sha(cpp.read_bytes())}
        save()
        if compile_result.returncode:
            raise RuntimeError(compile_result.stderr)
        for case in selection['cases_' + mode]:
            started = time.monotonic()
            result = subprocess.run([str(exe), mode, case], capture_output=True, text=True, timeout=15)
            row = {'mode': mode, 'case': case, 'passed': result.returncode == 0,
                   'elapsed_seconds': round(time.monotonic() - started, 6),
                   'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
            report['tests'].append(row)
            save()
            print(result.stdout, end='', flush=True)
            if result.returncode:
                raise RuntimeError(json.dumps(row))
    assert len(report['tests']) == 18
    report['complete'] = True
    save()


if __name__ == '__main__':
    main()
