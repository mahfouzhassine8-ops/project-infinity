#!/usr/bin/env python3
"""Derive QA-only overlays from exact retained sources, never mutate the baseline."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INCLUDE = '#include "interfaces/generic/InfinityStartupTrace.h"\n'


def once(s, old, new):
    assert s.count(old) == 1, (old[:100], s.count(old))
    return s.replace(old, new, 1)


def event(stage, arguments=''):
    return 'InfinityStartupTrace::Record(InfinityStartupTrace::Stage::'+stage+arguments+');'


def manager(s):
    s=once(s,'#include "ScriptInvocationManager.h"\n','#include "ScriptInvocationManager.h"\n'+INCLUDE)
    s=once(s,'void CScriptInvocationManager::Process()\n{','''void CScriptInvocationManager::Process()
{
  InfinityStartupTrace::Drain([](const InfinityStartupTrace::Event& event) {
    CLog::Log(LOGINFO, "InfinityStartupTrace stage={} request={} invoker={} tid={} us={} value={} flags={} tracked={}",
      InfinityStartupTrace::Name(event.stage), event.request, event.invoker, event.tid,
      event.monotonicUs, event.value, event.flags, event.tracked);
  });''')
    for name, assignment, stage in [('BeginCheckpointStartupAdmission','m_checkpointStartupAdmissionClosed = true;','StartupGateClosed'),('BeginShutdown','m_shutdownRequested = true;','ShutdownGateClosed')]:
        marker='void CScriptInvocationManager::'+name+'()\n{\n  std::unique_lock<CCriticalSection> lock(m_critSection);\n  '+assignment
        s=once(s,marker,marker.replace('{\n','{\n  (void)InfinityStartupTrace::Enabled(); // Resolve QA identity before taking the manager lock.\n',1)+'\n  '+event(stage,', -1, 0, (m_shutdownRequested ? 1U : 0U) | (m_checkpointStartupAdmissionClosed ? 2U : 0U), m_scripts.size()'))
    s=once(s,'void CScriptInvocationManager::BeginAndroidCheckpoint()\n{','void CScriptInvocationManager::BeginAndroidCheckpoint()\n{\n  (void)InfinityStartupTrace::Enabled();')
    s=once(s,'    m_shutdownRequested = true;\n    // Only one stop notification wave','    m_shutdownRequested = true;\n    '+event('CheckpointGateClosed',', -1, 0, (m_shutdownRequested ? 1U : 0U) | (m_checkpointStartupAdmissionClosed ? 2U : 0U), m_scripts.size()')+'\n    // Only one stop notification wave')
    marker='''  std::unique_lock<CCriticalSection> lock(m_critSection);
  if (m_shutdownRequested || (m_checkpointStartupAdmissionClosed &&
      !CanAdmitCheckpointStartupLocked(script, addon, reuseable)))
    return LanguageInvokerPtr();'''
    s=once(s,marker,'''  InfinityStartupTrace::Request infinityRequest;
  '''+event('LookupWait')+'''
  std::unique_lock<CCriticalSection> lock(m_critSection);
  '''+event('LookupLocked',', -1, 0, (m_shutdownRequested ? 1U : 0U) | (m_checkpointStartupAdmissionClosed ? 2U : 0U), m_scripts.size()')+'''
  if (m_shutdownRequested || (m_checkpointStartupAdmissionClosed &&
      !CanAdmitCheckpointStartupLocked(script, addon, reuseable)))
  {
    InfinityStartupTrace::Record(m_shutdownRequested ? InfinityStartupTrace::Stage::ShutdownClosed : InfinityStartupTrace::Stage::StartupClosed);
    return LanguageInvokerPtr();
  }''')
    s=once(s,'  return LanguageInvokerPtr();\n}\n\nint CScriptInvocationManager::ExecuteAsync(', '  '+event('MissingHandler')+'\n  return LanguageInvokerPtr();\n}\n\nint CScriptInvocationManager::ExecuteAsync(')
    # Only the two asynchronous entry points; synchronous behavior is untouched.
    start=s.index('int CScriptInvocationManager::ExecuteAsync(')
    end=s.index('int CScriptInvocationManager::ExecuteSync(',start)
    body=s[start:end]
    body=once(body,'{\n  if (script.empty())\n    return -1;','{\n  InfinityStartupTrace::Request infinityRequest;\n  if (script.empty())\n  { '+event('EmptyScript')+' return -1; }')
    body=body.replace('if (!CFileUtils::Exists(script, false))\n  {','if (!CFileUtils::Exists(script, false))\n  {\n    '+event('MissingScript'))
    body=once(body,'{\n  if (script.empty() || languageInvoker == NULL)\n    return -1;','''{
  InfinityStartupTrace::Request infinityRequest;
  if (script.empty() || languageInvoker == NULL)
  {
    InfinityStartupTrace::Record(script.empty() ? InfinityStartupTrace::Stage::EmptyScript : InfinityStartupTrace::Stage::NullInvoker);
    return -1;
  }''')
    body=body.replace('std::unique_lock<CCriticalSection> admissionCheck(m_critSection);', event('DispatchWait')+'\n    std::unique_lock<CCriticalSection> admissionCheck(m_critSection);\n    '+event('DispatchLocked',', languageInvoker->GetId(), 0, (m_shutdownRequested ? 1U : 0U) | (m_checkpointStartupAdmissionClosed ? 2U : 0U), m_scripts.size()'))
    body=body.replace('std::unique_lock<CCriticalSection> lock(m_critSection);',event('DispatchWait')+'\n  std::unique_lock<CCriticalSection> lock(m_critSection);\n  '+event('DispatchLocked',', languageInvoker->GetId(), 0, (m_shutdownRequested ? 1U : 0U) | (m_checkpointStartupAdmissionClosed ? 2U : 0U), m_scripts.size()'))
    old='!CanAdmitCheckpointStartupLocked(script, addon, reuseable, languageInvoker)))\n    return -1;'
    assert body.count(old)==2
    body=body.replace(old,'''!CanAdmitCheckpointStartupLocked(script, addon, reuseable, languageInvoker)))
  {
    InfinityStartupTrace::Record(m_shutdownRequested ? InfinityStartupTrace::Stage::ShutdownClosed : InfinityStartupTrace::Stage::StartupClosed);
    return -1;
  }''')
    body=once(body,'CLog::Log(LOGINFO, "Infinity quarantine: suppressing failing background service {}", addon->ID());',event('Quarantined')+'\n    CLog::Log(LOGINFO, "Infinity quarantine: suppressing failing background service {}", addon->ID());')
    body=once(body,'    invokerThread->Execute(script, arguments);','    '+event('ReusedDispatch',', invokerThread->GetId(), 0, 0, m_scripts.size()')+'\n    invokerThread->Execute(script, arguments);')
    body=once(body,'  invokerThread->Execute(script, arguments);\n\n  return invokerThread->GetId();','  '+event('FreshDispatch',', invokerThread->GetId(), 0, 0, m_scripts.size()')+'\n  invokerThread->Execute(script, arguments);\n\n  return invokerThread->GetId();')
    return s[:start]+body+s[end:]


def builtin(s):
    s=once(s,'#include "AddonBuiltins.h"\n','#include "AddonBuiltins.h"\n'+INCLUDE)
    s=once(s,'static int RunScript(const std::vector<std::string>& params)\n{','static int RunScript(const std::vector<std::string>& params)\n{\n  InfinityStartupTrace::Request infinityRequest;\n  '+event('BuiltinResolve'))
    s=once(s,'    CScriptInvocationManager::GetInstance().ExecuteAsync(scriptpath, addon, argv);','''    // Diagnostic only: retain the public built-in return contract below.
    '''+event('BuiltinResolved')+'''
    const int infinityInvocationResult = CScriptInvocationManager::GetInstance().ExecuteAsync(scriptpath, addon, argv);
    '''+event('BuiltinResult',', infinityInvocationResult, infinityInvocationResult') )
    return s


def python(s):
    s=once(s,'#include "PythonInvoker.h"\n','#include "PythonInvoker.h"\n'+INCLUDE)
    mapping={'native.execute.enter':'ExecuteEnter','native.execute.file_exists':'ExecuteMissing',
             'native.handler.initialize':'HandlerBegin','native.handler.initialized':'HandlerReady',
             'native.interpreter.acquire_gil':'GilWait','native.interpreter.create':'InterpreterCreate',
             'native.interpreter.created':'InterpreterCreated','native.interpreter.restore_gil':'RestoreGilWait',
             'native.kodi_module.initialize':'KodiInitialize','native.kodi_module.initialized':'KodiInitialized',
             'native.observer.before_start':'ObserverBegin'}
    # Existing stages remain exactly intact; add native observation beside them.
    lines=[]
    for line in s.splitlines(keepends=True):
        lines.append(line)
        for original, stage in mapping.items():
            if 'InitializationProgress(GetId(), "'+original+'"' in line and stage!='ExecuteMissing':
                lines.append('      '+event(stage,', GetId()')+'\n')
    s=''.join(lines)
    s=once(s,'  if (!onExecutionInitialized())\n    return false;','  if (!onExecutionInitialized())\n  { '+event('HandlerRejected',', GetId()')+' return false; }')
    s=once(s,'  if (!CFileUtils::Exists(script))\n  {','  if (!CFileUtils::Exists(script))\n  {\n    '+event('ExecuteMissing',', GetId()'))
    for needle, stage in [('Python main thread state unavailable','MainStateMissing'),('PyThreadState_New failed','ThreadStateFailed')]:
        line=next(l for l in s.splitlines() if needle in l)
        if stage=='ThreadStateFailed':
            assert s.count(line)==3
            s=s.replace(line,'        '+event(stage,', GetId()')+'\n'+line,1)
        else:
            s=once(s,line,'        '+event(stage,', GetId()')+'\n'+line)
    s=once(s,'      PyEval_RestoreThread(m_mainThreadState);\n      m_invokerOwnsGil = true;','      PyEval_RestoreThread(m_mainThreadState);\n      '+event('GilAcquired',', GetId()')+'\n      m_invokerOwnsGil = true;')
    s=once(s,'      if (l_threadState == nullptr)\n      {','      if (l_threadState == nullptr)\n      {\n        '+event('InterpreterFailed',', GetId()'))
    # Pinned CPython3.11.7 recoverable NULL returns retain this caller's
    # temporary state and GIL. The old second acquisition self-deadlocks.
    failed=s.index('      if (l_threadState == nullptr)\n      {')
    cleanup=s.index('        PyThreadState_Clear(m_mainThreadState);',failed)
    redundant='        PyEval_RestoreThread(m_mainThreadState);\n        m_invokerOwnsGil = true;\n'
    assert s[failed:cleanup].endswith(redundant)
    s=s[:failed]+s[failed:cleanup].removesuffix(redundant)+s[cleanup:]
    s=once(s,'  PyEval_RestoreThread(l_threadState);\n  m_invokerOwnsGil = true;','  PyEval_RestoreThread(l_threadState);\n  '+event('RestoreGilAcquired',', GetId()')+'\n  m_invokerOwnsGil = true;')
    line='  m_infinityPersistenceObserver = InfinityPythonPersistence::Start(GetId(), m_threadState->interp);'
    s=once(s,line,line+'\n  if (InfinityStartupTrace::Enabled()) '+event('ObserverReturned',', GetId(), PyErr_Occurred() ? 1 : 0'))
    s=once(s,'          executeScript(fp, realFilename, moduleDict);','          '+event('BytecodeEnter',', GetId()')+'\n          executeScript(fp, realFilename, moduleDict);\n          if (InfinityStartupTrace::Enabled()) '+event('BytecodeReturned',', GetId(), PyErr_Occurred() ? 1 : 0'))
    s=once(s,'        }catch(...){if(waitProbe)InfinityPythonWaitProbe::BodyReturned();throw;}','        }catch(...){'+event('BytecodeException',', GetId()')+'if(waitProbe)InfinityPythonWaitProbe::BodyReturned();throw;}')
    s=once(s,'  if (!stopping)\n  {','  if (stopping) { '+event('StoppingBeforeBytecode',', GetId()')+' }\n  if (!stopping)\n  {')
    s=once(s,'  m_systemExitThrown = false;\n  InvokerState stateToSet;','  if (InfinityStartupTrace::Enabled()) '+event('ExecutionFinished',', GetId(), (failed ? 1 : 0) | (PyErr_Occurred() ? 2 : 0)')+'\n  m_systemExitThrown = false;\n  InvokerState stateToSet;')
    return s


def runtime(s):
    s=once(s,'#include "XBPython.h"\n','#include "XBPython.h"\n'+INCLUDE)
    marker='  CLog::Log(LOGDEBUG, "initializing python engine.");\n  std::unique_lock<CCriticalSection> lock(m_critSection);'
    s=once(s,marker,'  '+event('RuntimeWait',', invoker->GetId()')+'\n'+marker+'\n  '+event('RuntimeLocked',', invoker->GetId(), m_bInitialized ? 1 : 0, 0, m_iDllScriptCounter'))
    s=once(s,'    Py_Initialize();\n','    '+event('RuntimeInitialize',', invoker->GetId()')+'\n    Py_Initialize();\n')
    s=once(s,'    m_bInitialized = true;\n  }\n\n  return m_bInitialized;','    m_bInitialized = true;\n    '+event('RuntimeInitialized',', invoker->GetId()')+'\n  }\n  else { '+event('RuntimeReused',', invoker->GetId()')+' }\n\n  return m_bInitialized;')
    return s


def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);a=p.parse_args()
    pins=json.loads((HERE/'RETAINED-SOURCE-CHECK.json').read_text())
    transforms={'xbmc/interfaces/generic/ScriptInvocationManager.cpp':manager,
                'xbmc/interfaces/builtins/AddonBuiltins.cpp':builtin,
                'xbmc/interfaces/python/PythonInvoker.cpp':python,
                'xbmc/interfaces/python/XBPython.cpp':runtime}
    report={};diff=[]
    for path, transform in transforms.items():
        original=(a.runtime/path).read_text()
        before=hashlib.sha256(original.encode()).hexdigest();assert before==pins[path]['sha256'],path
        candidate=transform(original)
        target=HERE/'native/overlay'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(candidate)
        report[path]={'before':before,'after':hashlib.sha256(candidate.encode()).hexdigest()}
        diff.extend(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),'a/'+path,'b/'+path))
    (HERE/'native/SOURCE-DIFF.patch').write_text(''.join(diff))
    (HERE/'native/SOURCE-BINDINGS.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Prepared four source-bound diagnostic overlays; original native tree unchanged.')


if __name__=='__main__':main()
