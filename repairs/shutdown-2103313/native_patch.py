#!/usr/bin/env python3
"""Cooperative Android script shutdown on the exact 3308/3312 native baseline.

Broadcast abort before waiting, keep late monitors aborted, close the script
launch gate, release registry locks during stop/join, and share the existing
five-second Python grace period. No process kill or native join bypass.
"""
import argparse
import hashlib
import json
from pathlib import Path

APP = 'xbmc/application/Application.cpp'
SERVICE = 'xbmc/addons/Service.cpp'
MANAGER = 'xbmc/interfaces/generic/ScriptInvocationManager.cpp'
MANAGER_H = 'xbmc/interfaces/generic/ScriptInvocationManager.h'
PYTHON = 'xbmc/interfaces/python/XBPython.cpp'
PYTHON_H = 'xbmc/interfaces/python/XBPython.h'
INVOKER = 'xbmc/interfaces/python/PythonInvoker.cpp'
PARENT_MAP = '5a3b93bc966f4918ed582f92d01b1659a79968f07c498c6ee4c1834beb394f15'
PREIMAGES = {
    APP: 'abd841bd83198951928803bf68eb5d4c9e10f603a5b7636a15fb628f8167e36b',
    SERVICE: '97950fa48b71afe1fe8ebe9d20a316c97ef25b35630d031953fa659ba5638442',
    MANAGER: 'caa8973c8ca85fa02ff682f5d3d33759980108ebc19ddf8c7fae8f4c1c8f6183',
    MANAGER_H: '46d60583eab0551e3af3e7017026dd0a3fe5ca7b8066429eb6029310609093cd',
    PYTHON: '3715fe3289fd9c9e998e7b6133b1beaab5cf6d7e0002f983204f39694019f1a9',
    PYTHON_H: 'cb1f4ed553cf624e7da464503c7a68a10027d5356b71d9e1691b2db202e86643',
    INVOKER: 'dc4e4b0cfada7a6a462fbe263606bbdb3cc8d9f7ec0190ae31797d63c53371af',
}
ALLOWED = set(PREIMAGES)


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
    if name == APP:
        return once(text, '''  CServiceBroker::GetServiceAddons().Stop();
  CScriptInvocationManager::GetInstance().StopRunningScripts();
}
#endif
''', '''  // INFINITY_SHUTDOWN_3313: stop admission before broadcasting. All current
  // monitors and monitors created by already-starting scripts see shutdown.
  // The Android event loop/messenger stays alive until the existing stage two.
  CScriptInvocationManager::GetInstance().BeginShutdown();
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().BeginShutdown();
#endif
  CLog::Log(LOGINFO, "Infinity shutdown: broadcast script abort; shared grace begins");
  CServiceBroker::GetServiceAddons().Stop();
  CLog::Log(LOGINFO, "Infinity shutdown: service stop pass complete");
  CScriptInvocationManager::GetInstance().StopRunningScripts();
  CLog::Log(LOGINFO, "Infinity shutdown: script stop pass complete; final cleanup pending");
}
#endif
''')
    if name == MANAGER_H:
        text = once(text, '  void Uninitialize();\n',
                    '  void Uninitialize();\n  void BeginShutdown();\n')
        return once(text, '  mutable CCriticalSection m_critSection;\n',
                    '  mutable CCriticalSection m_critSection;\n'
                    '  bool m_shutdownRequested{false}; // guarded by m_critSection\n')
    if name == MANAGER:
        text = once(text, 'void CScriptInvocationManager::Uninitialize()\n', '''void CScriptInvocationManager::BeginShutdown()
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  m_shutdownRequested = true;
}

void CScriptInvocationManager::Uninitialize()
''')
        text = once(text, '''LanguageInvokerPtr CScriptInvocationManager::GetLanguageInvoker(const std::string& script)
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
''', '''LanguageInvokerPtr CScriptInvocationManager::GetLanguageInvoker(const std::string& script)
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  if (m_shutdownRequested)
    return LanguageInvokerPtr();
''')
        text = once(text, '''  std::unique_lock<CCriticalSection> lock(m_critSection);

  if (m_lastInvokerThread && m_lastInvokerThread->GetInvoker() == languageInvoker)
''', '''  std::unique_lock<CCriticalSection> lock(m_critSection);
  if (m_shutdownRequested)
    return -1;

  if (m_lastInvokerThread && m_lastInvokerThread->GetInvoker() == languageInvoker)
''')
        # CLanguageInvokerThread::Execute only dispatches; CThread::Create signals
        # StartEvent before running Python. Serialize dispatch with BeginShutdown
        # so a registered but unstarted thread cannot start after the stop pass.
        text = once(text, '''    // After we leave the lock, m_lastInvokerThread can be released -> copy!
    CLanguageInvokerThreadPtr invokerThread = m_lastInvokerThread;
    lock.unlock();
    invokerThread->Execute(script, arguments);
''', '''    // Keep dispatch serialized with BeginShutdown; no script join occurs here.
    CLanguageInvokerThreadPtr invokerThread = m_lastInvokerThread;
    invokerThread->Execute(script, arguments);
''')
        text = once(text, '''  // After we leave the lock, m_lastInvokerThread can be released -> copy!
  CLanguageInvokerThreadPtr invokerThread = m_lastInvokerThread;
  lock.unlock();
  invokerThread->Execute(script, arguments);
''', '''  // Create signals its start event before running the script. Do not let
  // BeginShutdown pass this registration before the thread is actually started.
  CLanguageInvokerThreadPtr invokerThread = m_lastInvokerThread;
  invokerThread->Execute(script, arguments);
''')
        text = once(text, '''  if (invokerThread == NULL)
    return false;

  return invokerThread->Stop(wait);
''', '''  if (invokerThread == NULL)
    return false;

  // Stop pumps messages and may join a thread whose OnExit needs this registry.
  // The shared pointer retains ownership while callbacks remove map entries.
  lock.unlock();
  return invokerThread->Stop(wait);
''')
        text = once(text, '''  for (auto& it : m_scripts)
  {
    if (!it.second.done)
      Stop(it.second.script, wait);
  }
''', '''  std::vector<CLanguageInvokerThreadPtr> pending;
  {
    std::unique_lock<CCriticalSection> lock(m_critSection);
    for (const auto& it : m_scripts)
    {
      if (!it.second.done)
        pending.push_back(it.second.thread);
    }
  }
  // A stop can pump Process() and erase the registry. Iterate retained owners.
  for (const auto& thread : pending)
    thread->Stop(wait);
''')
        return once(text, '''  return Stop(script->second, wait);
''', '''  const int scriptId = script->second;
  lock.unlock();
  return Stop(scriptId, wait);
''')
    if name == SERVICE:
        text = once(text, '''  std::unique_lock<CCriticalSection> lock(m_criticalSection);
  for (const auto& service : m_services)
  {
    Stop(service);
  }
  m_services.clear();
''', '''  std::map<std::string, int> pending;
  {
    std::unique_lock<CCriticalSection> lock(m_criticalSection);
    pending.swap(m_services);
  }
  // Add-on cleanup can call back into the service registry.
  for (const auto& service : pending)
    Stop(service);
''')
        return once(text, '''    Stop(*it);
    m_services.erase(it);
''', '''    const auto service = *it;
    m_services.erase(it);
    lock.unlock();
    Stop(service);
''')
    if name == PYTHON_H:
        text = once(text, '#include <memory>\n', '#include <atomic>\n#include <cstdint>\n#include <memory>\n')
        text = once(text, '  void NotifyScriptAborting(ILanguageInvoker* invoker) override;\n',
                    '  void NotifyScriptAborting(ILanguageInvoker* invoker) override;\n'
                    '  void BeginShutdown();\n'
                    '  bool IsShutdownRequested() const { return m_shutdownDeadlineMs.load() != 0; }\n'
                    '  bool ShutdownGraceExpired() const;\n')
        return once(text, '  MonitorCallbackList m_vecMonitorCallbackList;\n',
                    '  MonitorCallbackList m_vecMonitorCallbackList;\n'
                    '  std::atomic<int64_t> m_shutdownDeadlineMs{0};\n')
    if name == PYTHON:
        text = once(text, '#include <algorithm>\n', '#include <algorithm>\n#include <chrono>\n')
        text = once(text, '  m_vecMonitorCallbackList.push_back(pCallback);\n', '''  m_vecMonitorCallbackList.push_back(pCallback);
  // A service still importing at close must not miss the broadcast.
  if (IsShutdownRequested())
    pCallback->AbortNotify();
''')
        return once(text, 'void XBPython::NotifyScriptAborting(ILanguageInvoker* invoker)\n', '''void XBPython::BeginShutdown()
{
  // AbortNotify only signals a native event; it does not execute Python or need
  // its GIL. Serialize the broadcast with registration/unregistration.
  std::unique_lock<CCriticalSection> lock(m_vecMonitorCallbackList);
  if (!IsShutdownRequested())
  {
    const auto now = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    m_shutdownDeadlineMs.store(now + 5000);
  }
  for (auto* monitor : m_vecMonitorCallbackList)
    monitor->AbortNotify();
}

bool XBPython::ShutdownGraceExpired() const
{
  const auto deadline = m_shutdownDeadlineMs.load();
  if (deadline == 0)
    return false;
  const auto now = std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
  return now >= deadline;
}

void XBPython::NotifyScriptAborting(ILanguageInvoker* invoker)
''')
    if name == INVOKER:
        # During global shutdown monitor notification already happened without
        # the GIL. Leave the accepted individual-stop/runtime path unchanged.
        start = text.index('      PyThreadState* ts = PyThreadState_New(m_threadState->interp);',
                           text.index('bool CPythonInvoker::stop(bool abort)'))
        end = text.index('      PyThreadState_DeleteCurrent();', start) + len('      PyThreadState_DeleteCurrent();')
        body = text[start:end]
        text = once(text, body, '''      if (!CServiceBroker::GetXBPython().IsShutdownRequested())
      {
'''+ '\n'.join('  '+line if line else '' for line in body.split('\n')) + '''
      }''')
        text = once(text, '''      if (timeout.IsTimePast())
      {
        CLog::Log(LOGERROR,
''', '''      if (CServiceBroker::GetXBPython().ShutdownGraceExpired())
      {
        CLog::Log(LOGWARNING,
                  "CPythonInvoker({}, {}): shared shutdown grace exhausted; requesting abort",
                  GetId(), m_sourceFile);
        break;
      }
      if (timeout.IsTimePast())
      {
        CLog::Log(LOGERROR,
''')
        return once(text, '    if (!timeout.IsTimePast())\n',
                    '    if (!timeout.IsTimePast() && !CServiceBroker::GetXBPython().ShutdownGraceExpired())\n')
    raise ValueError('Unexpected target: ' + name)


def apply(source, parent_proof, receipt):
    parent = json.loads(parent_proof.read_text())['after']
    if len(parent) != 9372 or digest(json.dumps(parent, sort_keys=True, separators=(',', ':')).encode()) != PARENT_MAP:
        raise ValueError('Not the exact 3308/3312 native source map')
    before = snapshot(source)
    if before != parent:
        raise ValueError('Complete source differs from the locked native parent')
    for name, expected in PREIMAGES.items():
        if before[name] != expected:
            raise ValueError('Wrong shutdown preimage: ' + name)
        target = source / name
        target.write_text(transform(name, target.read_text()))
    after = snapshot(source)
    changed = {n for n in before if before[n] != after[n]}
    if changed != ALLOWED or before.keys() != after.keys():
        raise ValueError('Undeclared native changes')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({
        'candidate': 2103313, 'apk_parent': 2103312, 'skin_parent': '1.0.5.201',
        'before': before, 'after': after, 'changed': sorted(changed),
        'native_rebuild_required': True, 'process_kill_added': False,
        'native_join_bypassed': False, 'physical_device_verified': False,
    }, indent=2, sort_keys=True)+'\n')


def verify(source, receipt):
    proof = json.loads(receipt.read_text())
    actual = snapshot(source)
    if any(actual.get(n) != value for n, value in proof['after'].items()):
        raise ValueError('Native source changed after validation')
    if set(proof['changed']) != ALLOWED:
        raise ValueError('Unexpected native delta')
    for name, expected in PREIMAGES.items():
        if proof['before'][name] != expected:
            raise ValueError('Wrong shutdown parent')


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
    print('PASS: exact native parent and declared shutdown delta')


if __name__ == '__main__':
    main()
