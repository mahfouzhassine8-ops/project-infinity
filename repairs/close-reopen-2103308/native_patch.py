#!/usr/bin/env python3
"""Move captured Python shutdown waits before NativeActivity destruction.

No timeout, process-kill, Python runtime, data reset, or Cobra change. Android
callbacks and Kodi's original second-stage shutdown retain their ownership.
"""
import argparse
import hashlib
import json
from pathlib import Path

CPP = 'xbmc/platform/android/activity/XBMCApp.cpp'
HEADER = 'xbmc/platform/android/activity/XBMCApp.h'
APP = 'xbmc/application/Application.cpp'
APP_HEADER = 'xbmc/application/Application.h'
ALLOWED = {CPP, HEADER, APP, APP_HEADER}
PARENT_MAP = '14e09e8714406e2f0e85c932cfa03cc3ff79f14749c3c92e8e49ca91f88d9097'
PREIMAGES = {
    CPP: '9feadf50fd1864815e819b598221cb2b20f78fea069aba7fb0a771b84ad95f49',
    HEADER: '6346c205fb12abaf47d0a532a70375107cc19ce86c368e6b4441521d18b5a1bc',
    APP: '8b0f5a5eb37d82f5ccacb555154a0af76d45f4c46982e9821ba6292258607475',
    APP_HEADER: 'dd511c41ac8bf8a76a52f5ff5ac83725a12e4a9e8fbece478061abb0e22f9994',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unreviewed preimage: ' + old[:100])
    return text.replace(old, new, 1)


def transform(name, text):
    if name == APP_HEADER:
        text = once(text, '  bool Stop(int exitCode);\n',
                    '  bool Stop(int exitCode);\n#if defined(TARGET_ANDROID)\n'
                    '  void PrepareAndroidShutdownScripts(int exitCode);\n#endif\n')
        return once(text, '  void PrintStartupLog();\n',
                    '  void PrintStartupLog();\n'
                    '  void AnnounceQuit(int exitCode);\n'
                    '#if defined(TARGET_ANDROID)\n'
                    '  bool m_infinityQuitAnnounced{false};\n#endif\n')
    if name == APP:
        announcement = '''    CVariant vExitCode(CVariant::VariantTypeObject);
    vExitCode["exitcode"] = exitCode;
    CServiceBroker::GetAnnouncementManager()->Announce(ANNOUNCEMENT::System, "OnQuit", vExitCode);
'''
        text = once(text, announcement, '    AnnounceQuit(exitCode);\n')
        helper = '''void CApplication::AnnounceQuit(int exitCode)
{
#if defined(TARGET_ANDROID)
  if (m_infinityQuitAnnounced)
    return;
  m_infinityQuitAnnounced = true;
#endif
  CVariant vExitCode(CVariant::VariantTypeObject);
  vExitCode["exitcode"] = exitCode;
  CServiceBroker::GetAnnouncementManager()->Announce(ANNOUNCEMENT::System, "OnQuit", vExitCode);
}

#if defined(TARGET_ANDROID)
void CApplication::PrepareAndroidShutdownScripts(int exitCode)
{
  // Process() owns this lock. Script teardown can make external GUI calls:
  // release it during preparation and reacquire it before Process() resumes.
  CSingleExit releaseFrameGuard(m_frameMoveGuard);
  AnnounceQuit(exitCode);

  // Keep a pre-script snapshot, as the original Stop() does. Its final uptime,
  // settings and skin saves remain in stage two; neither save is bypassed.
  if (CFile::Exists(CServiceBroker::GetSettingsComponent()->GetProfileManager()->GetSettingsFile()))
    CServiceBroker::GetSettingsComponent()->GetSettings()->Save();
  if (g_SkinInfo != nullptr)
    g_SkinInfo->SaveSettings();

  CServiceBroker::GetServiceAddons().Stop();
  CScriptInvocationManager::GetInstance().StopRunningScripts();
}
#endif

'''
        return once(text, 'bool CApplication::Stop(int exitCode)\n', helper + 'bool CApplication::Stop(int exitCode)\n')
    if name == HEADER:
        return once(text, '  std::atomic<bool> m_exiting{false};\n',
                    '  std::atomic<bool> m_exiting{false};\n'
                    '  // Claim stage one before script stop pumps reentrant quit messages.\n'
                    '  std::atomic<bool> m_finishRequested{false};\n'
                    '  bool m_shutdownPreparing{false}; // application thread only\n')
    if name != CPP:
        raise ValueError('Unexpected target')
    text = once(text, '''bool CXBMCApp::Stop(int exitCode)
{
  if (m_exiting)
''', '''bool CXBMCApp::Stop(int exitCode)
{
  // A native destroy can queue stage two while Python stop pumps messages.
  // Never recursively enter CApplication::Stop with its frame guard released.
  if (m_shutdownPreparing)
    return false;

  if (m_exiting)
''')
    return once(text, '''  // enter stage one: tell android to finish the activity
  CLog::Log(LOGINFO, "XBMCApp: Finishing the activity");

  m_exitCode = exitCode;
''', '''  // INFINITY_CLOSE_REOPEN_3308: the captured ANR waited in service Python
  // shutdown AFTER Android entered NativeActivity.onDestroy. native_app_glue
  // then blocks Android's UI thread until Quit() joins this application thread.
  // Perform the same cooperative script stop while the activity is still
  // alive. The application messenger/GUI and native event loop remain available
  // for script cleanup and Android lifecycle callbacks. No early runtime unload.
  if (m_finishRequested.exchange(true))
    return false;

  m_exitCode = exitCode;
  CLog::Log(LOGINFO, "Infinity shutdown: pre-destroy script cleanup begin");
  {
    m_shutdownPreparing = true;
    struct PreparationGuard
    {
      bool& preparing;
      ~PreparationGuard() { preparing = false; }
    } guard{m_shutdownPreparing};
    g_application.PrepareAndroidShutdownScripts(exitCode);
  }
  CLog::Log(LOGINFO, "Infinity shutdown: pre-destroy script cleanup complete");

  // An external Android destruction may have arrived during script cleanup.
  // In that case continue the original stage two instead of requesting finish.
  if (m_exiting)
    return true;

  // enter stage one: tell android to finish the activity
  CLog::Log(LOGINFO, "XBMCApp: Finishing the activity");
''')


def apply(source, parent_proof, receipt):
    proof = json.loads(parent_proof.read_text())
    parent = proof['after']
    if len(parent) != 9372 or digest(json.dumps(parent, sort_keys=True, separators=(',', ':')).encode()) != PARENT_MAP:
        raise ValueError('Not the exact 3306/3307 native source map')
    before = snapshot(source)
    if before != parent:
        raise ValueError('Complete native source differs from 3307 parent')
    for name, expected in PREIMAGES.items():
        if before[name] != expected:
            raise ValueError('Shutdown owner differs: ' + name)
        target = source / name
        target.write_text(transform(name, target.read_text()))
    after = snapshot(source)
    changed = {n for n in before if before[n] != after[n]}
    if changed != ALLOWED or before.keys() != after.keys():
        raise ValueError('Undeclared native delta')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({
        'apk_parent': 2103307, 'skin_parent': '1.0.5.201', 'candidate': 2103308,
        'before': before, 'after': after, 'changed': sorted(changed),
        'native_rebuild_required': True, 'python_runtime_changed': False,
        'automatic_process_kill_added': False, 'physical_device_verified': False,
        'shutdown_hang_resolved': False,
    }, indent=2, sort_keys=True) + '\n')


def verify(source, receipt):
    proof = json.loads(receipt.read_text())
    actual = snapshot(source)
    if any(actual.get(name) != expected for name, expected in proof['after'].items()):
        raise ValueError('Native source changed after validation')
    if set(proof['changed']) != ALLOWED:
        raise ValueError('Unexpected native delta')
    for name in ALLOWED:
        if proof['before'][name] != PREIMAGES[name]:
            raise ValueError('Unreviewed parent')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['apply', 'verify'])
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--parent-proof', type=Path)
    a = p.parse_args()
    if a.mode == 'apply':
        if not a.parent_proof:
            p.error('apply requires parent proof')
        apply(a.source, a.parent_proof, a.receipt)
    verify(a.source, a.receipt)
    print('PASS: exact native parent; only shutdown stage-one owners changed')


if __name__ == '__main__':
    main()
