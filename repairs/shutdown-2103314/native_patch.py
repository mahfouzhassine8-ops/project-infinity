#!/usr/bin/env python3
"""Observe the full 3312 native shutdown; preserve its shutdown behavior."""
import argparse, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
HEADER='xbmc/platform/android/activity/InfinityShutdownTrace.h'
FILES=['xbmc/application/Application.cpp','xbmc/platform/android/activity/XBMCApp.cpp',
       'xbmc/platform/android/activity/android_main.cpp','xbmc/addons/Service.cpp',
       'xbmc/interfaces/generic/ScriptInvocationManager.cpp',
       'xbmc/interfaces/generic/LanguageInvokerThread.cpp',
       'xbmc/interfaces/python/PythonInvoker.cpp','xbmc/interfaces/python/XBPython.cpp']
PARENT_MAP='5a3b93bc966f4918ed582f92d01b1659a79968f07c498c6ee4c1834beb394f15'
ALLOWED=set(FILES+[HEADER])
def digest(data): return hashlib.sha256(data).hexdigest()
def snapshot(root):
 return {p.relative_to(root).as_posix():digest(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
def once(s,a,b):
 if s.count(a)!=1: raise ValueError('Preimage not unique: '+a[:100])
 return s.replace(a,b,1)
def function(s,name):
 start=s.index(name);a=s.index('{',start);depth=1;i=a+1
 # Selected methods have no braces in string literals beyond paired log braces.
 while depth:
  if s[i]=='{': depth+=1
  if s[i]=='}': depth-=1
  i+=1
 return start,i,s[start:i]
def alter(s,name,fn):
 a,b,body=function(s,name);return s[:a]+fn(body)+s[b:]
def span(s,statement,label,invoker='-1'):
 n=s.count(statement)
 if n!=1: raise ValueError(f'{label}: statement occurs {n} times')
 line=s[:s.index(statement)].split('\n')[-1];indent=line if not line.strip() else ''
 # Braces make the helper's duration exactly the operation and preserve existing
 # if/else binding when an original single statement is conditionally executed.
 new='{\n'+indent+'  InfinityShutdownTrace::Scope evidence("'+label+'", '+invoker+');\n'+indent+'  '+statement+'\n'+indent+'}'
 return s.replace(statement,new,1)
def mark_method(body,label,invoker='-1'):
 at=body.index('{')+1
 return body[:at]+'\n  InfinityShutdownTrace::Scope methodEvidence("'+label+'", '+invoker+');'+body[at:]
def transform(name,s):
 anchor='#include "'+Path(name).stem+'.h"'
 s=once(s,anchor,anchor+'\n#include "platform/android/activity/InfinityShutdownTrace.h"') if name!=FILES[2] else once(s,'#include "EventLoop.h"','#include "EventLoop.h"\n#include "InfinityShutdownTrace.h"')
 if name==FILES[0]:
  def pre(b):
   b=mark_method(b,'application.pre_destroy')
   for stmt,label in [('AnnounceQuit(exitCode);','pre.announce_quit'),('CServiceBroker::GetSettingsComponent()->GetSettings()->Save();','pre.save_settings'),('g_SkinInfo->SaveSettings();','pre.save_skin'),('CServiceBroker::GetServiceAddons().Stop();','pre.stop_services'),('CScriptInvocationManager::GetInstance().StopRunningScripts();','pre.stop_scripts')]:b=span(b,stmt,label)
   return b
  s=alter(s,'void CApplication::PrepareAndroidShutdownScripts',pre)
  def stop(b):
   b=mark_method(b,'application.stop')
   operations=[('appPlayer->ClosePlayer();','stop.close_player'),('g_alarmClock.StopThread();','stop.alarm_thread'),('AnnounceQuit(exitCode);','stop.announce_quit'),('CServiceBroker::GetSettingsComponent()->GetSettings()->Save();','stop.save_settings'),('g_SkinInfo->SaveSettings();','stop.save_skin'),('CServiceBroker::GetJobManager()->CancelJobs();','stop.cancel_jobs'),('CServiceBroker::GetAppMessenger()->Cleanup();','stop.messenger_cleanup'),('m_ServiceManager->GetNetwork().NetworkMessage(CNetworkBase::SERVICES_DOWN, 0);','stop.network'),('vfsAddon->DisconnectAll();','stop.vfs_disconnect'),('CServiceBroker::GetServiceAddons().Stop();','stop.services'),('CScriptInvocationManager::GetInstance().StopRunningScripts();','stop.scripts'),('m_pActiveAE->Shutdown();','stop.audio_engine')]
   for stmt,label in operations:b=span(b,stmt,label)
   return b
  s=alter(s,'bool CApplication::Stop(int exitCode)',stop)
  def cleanup(b):
   b=mark_method(b,'application.cleanup')
   operations=[('StopPlaying();','cleanup.stop_playing'),('m_ServiceManager->DeinitStageThree();','cleanup.services_stage3'),('GetComponent<CApplicationSkinHandling>()->UnloadSkin();','cleanup.unload_skin'),('CScriptInvocationManager::GetInstance().Uninitialize();','cleanup.scripts_uninitialize'),('renderSystem->DestroyRenderSystem();','cleanup.render'),('winSystem->DestroyWindow();','cleanup.window'),('m_pGUI->GetWindowManager().DestroyWindows();','cleanup.gui_windows'),('m_ServiceManager->DeinitStageTwo();','cleanup.services_stage2'),('m_pGUI->Deinit();','cleanup.gui'),('winSystem->DestroyWindowSystem();','cleanup.window_system'),('m_ServiceManager->DeinitStageOne();','cleanup.services_stage1'),('m_ServiceManager.reset();','cleanup.service_manager_destructor')]
   for stmt,label in operations:b=span(b,stmt,label)
   return b
  return alter(s,'bool CApplication::Cleanup()',cleanup)
 if name==FILES[1]:
  s=alter(s,'bool CXBMCApp::Stop(int exitCode)',lambda b:mark_method(b.replace('{','{\n  InfinityShutdownTrace::Begin();',1),'android.stop'))
  s=alter(s,'void CXBMCApp::Quit()',lambda b:span(mark_method(b.replace('{','{\n  InfinityShutdownTrace::Begin();',1),'android.quit'),'m_thread.join();','android.kodi_thread_join'))
  s=span(s,'CAppEnvironment::TearDown();','android.environment_teardown')
  return s
 if name==FILES[2]:
  s=once(s,'  // Copy the pathname while ANativeActivity still owns its storage.', '  InfinityShutdownTrace::Configure(state && state->activity ? state->activity->internalDataPath : nullptr);\n  // Copy the pathname while ANativeActivity still owns its storage.')
  s=span(s,'theApp.Quit();','android.main_quit')
  s=span(s,'CXBMCApp::Destroy();','android.native_destroy')
  s=once(s,'  exit(0);','  InfinityShutdownTrace::Event("milestone", "process.exit_requested");\n  exit(0);')
  return s
 if name==FILES[3]:
  s=alter(s,'void CServiceAddonManager::Stop()',lambda b:span(mark_method(b,'services.stop_all'),'Stop(service);','services.stop_one','service.second'))
  return s
 if name==FILES[4]:
  def u(b):
   b=mark_method(b,'scripts.uninitialize')
   b=span(b,'Process();','scripts.final_process')
   b=span(b,'it.thread->Stop(true);','scripts.join_remaining','it.id') if 'it.id' in b else span(b,'it.thread->Stop(true);','scripts.join_remaining')
   b=span(b,'tempList.clear();','scripts.destroy_invokers')
   return span(b,'it.second->Uninitialize();','scripts.handler_uninitialize')
  s=alter(s,'void CScriptInvocationManager::Uninitialize()',u)
  return alter(s,'void CScriptInvocationManager::StopRunningScripts',lambda b:mark_method(b,'scripts.stop_pass'))
 if name==FILES[5]:
  s=alter(s,'bool CLanguageInvokerThread::stop(bool wait)',lambda b:span(span(mark_method(b,'invoker_thread.stop','GetId()'),'result = m_invoker->Stop(wait);','invoker_thread.python_stop','GetId()'),'CThread::StopThread(wait);','invoker_thread.join','GetId()'))
  return alter(s,'CLanguageInvokerThread::~CLanguageInvokerThread()',lambda b:mark_method(b,'invoker_thread.destructor','GetId()'))
 if name==FILES[6]:
  s=alter(s,'CPythonInvoker::~CPythonInvoker()',lambda b:mark_method(b,'python.invoker_destructor','GetId()'))
  def stop(b):
   b=mark_method(b,'python.stop','GetId()')
   b=once(b,'  std::unique_lock<CCriticalSection> lock(m_critical);','  InfinityShutdownTrace::Scope lockEvidence("python.stop.lock", GetId());\n  std::unique_lock<CCriticalSection> lock(m_critical);\n  lockEvidence.End();')
   # First GIL acquisition precedes the existing five-second timer.
   b=b.replace('      PyEval_RestoreThread(ts);','      {\n        InfinityShutdownTrace::Scope gilEvidence("python.abort.gil_acquire", GetId());\n        PyEval_RestoreThread(ts);\n      }',1)
   b=once(b,'    XbmcThreads::EndTime<> timeout(PYTHON_SCRIPT_TIMEOUT);','    InfinityShutdownTrace::Scope waitEvidence("python.stop.cooperative_wait", GetId());\n    XbmcThreads::EndTime<> timeout(PYTHON_SCRIPT_TIMEOUT);')
   b=once(b,'    lock.lock();','    waitEvidence.End();\n    InfinityShutdownTrace::Scope relockEvidence("python.stop.relock", GetId());\n    lock.lock();\n    relockEvidence.End();')
   # Explicitly target the second acquisition inside CSingleExit.
   b=once(b,'        CSingleExit ex2(m_critical);\n        PyEval_RestoreThread(ts);','        CSingleExit ex2(m_critical);\n        InfinityShutdownTrace::Scope escalationEvidence("python.escalation.gil_acquire", GetId());\n        PyEval_RestoreThread(ts);')
   return b
  s=alter(s,'bool CPythonInvoker::stop(bool abort)',stop)
  def done(b):
   b=mark_method(b,'python.execution_done','GetId()')
   restore='if (!m_invokerOwnsGil)\n    {\n      PyEval_RestoreThread(m_threadState);\n      m_invokerOwnsGil = true;\n    }'
   b=span(b,restore,'python.finalize.gil_guard','GetId()')
   modules='PyObject* modules = PyImport_GetModuleDict();\n    if (modules)\n      PyDict_Clear(modules);'
   b=span(b,modules,'python.finalize.modules_clear','GetId()')
   for stmt,label in [('onDeinitialization();','python.finalize.addon_callback'),('PyErr_Clear();\n    PyGC_Collect();','python.finalize.gc_before_modules'),('PyGC_Collect();\n    PyErr_Clear();','python.finalize.gc_after_modules'),('Py_EndInterpreter(m_threadState);','python.finalize.end_interpreter')]:b=span(b,stmt,label,'GetId()')
   return b
  return alter(s,'void CPythonInvoker::onExecutionDone()',done)
 if name==FILES[7]:
  s=alter(s,'XBPython::~XBPython()',lambda b:span(span(mark_method(b,'python.runtime_destructor'),'PyDict_Clear(modules);','python.runtime.modules_clear'),'Py_Finalize();','python.runtime.finalize'))
  return alter(s,'void XBPython::Uninitialize()',lambda b:span(mark_method(b,'python.runtime_uninitialize'),'tmpvec.clear();','python.runtime.release_threads'))
 raise ValueError(name)
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['apply','verify']);p.add_argument('--source',type=Path,required=True);p.add_argument('--parent-proof',type=Path);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 if a.mode=='verify':
  r=json.loads(a.receipt.read_text());actual=snapshot(a.source)
  assert actual==r['after'],'Source changed after receipt';return
 before=snapshot(a.source);parent=json.loads(a.parent_proof.read_text())['after']
 assert before==parent,'Not exact locked native parent'
 assert digest(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==PARENT_MAP,'Wrong complete native parent map'
 for name in FILES:(a.source/name).write_text(transform(name,(a.source/name).read_text()))
 (a.source/HEADER).write_bytes((HERE/'InfinityShutdownTrace.h').read_bytes())
 after=snapshot(a.source);changed={n for n in set(before)|set(after) if before.get(n)!=after.get(n)}
 assert changed==ALLOWED,changed
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps({'candidate':2103314,'parent':2103312,'before':before,'after':after,'changed':sorted(changed),'diagnostics_only':True},indent=2)+'\n')
 print('PASS: shutdown evidence only;',len(changed),'native source entries; full baseline behavior retained')
if __name__=='__main__':main()
