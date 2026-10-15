#!/usr/bin/env python3
"""Reviewed cooperative stop + independent late evidence, on exact passed 2103325."""
from pathlib import Path
import argparse,importlib.util,hashlib,json,difflib
HERE=Path(__file__).resolve().parent
PARENT_MAP='463dfd2faaf5bd1af1f5ad90946f34a80ff34eb7cd8c878c2abddb02c94b9f1a'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(b):return hashlib.sha256(b).hexdigest()
def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);args=p.parse_args()
source=dest=args.source
coop=load('legacycoop',HERE.parent/'shutdown-2103313/native_patch.py')
diag=load('diag325',HERE.parent/'shutdown-diagnostics-2103325/native_patch.py')
before=snapshot(source);expected=json.loads(args.proof.read_text())['after']
assert before==expected,'Not exact passed native source'
assert sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==PARENT_MAP,'Wrong native map'
original={n:(source/n).read_text() for n in coop.ALLOWED|{diag.HEADER}}
for name in coop.ALLOWED:
 text=original[name]
 if name==coop.APP:
  # Close admission before OnQuit; broadcast abort only after the pre-script saves.
  # Both entry routes: normal pre-destroy pass and external task destruction.
  block='''  // Admission closes before OnQuit; settings still precede monitor abort.
  CScriptInvocationManager::GetInstance().BeginShutdown();
'''
  sig='void CApplication::PrepareAndroidShutdownScripts(int exitCode)'
  a,b,body=diag.function(text,sig)
  old='  CSingleExit releaseFrameGuard(m_frameMoveGuard);'
  assert body.count(old)==1
  body=body.replace(old,old+'\n'+block,1)
  anchor='  {\n    InfinityShutdownTrace::Scope evidence("pre.stop_services"'
  assert anchor in body
  body=body.replace(anchor,'#ifdef HAS_PYTHON\n  CServiceBroker::GetXBPython().BeginShutdown();\n#endif\n'+anchor,1)
  text=text[:a]+body+text[b:]
  # External Activity destruction bypasses stage one. Broadcast on that route too.
  a,b,body=diag.function(text,'bool CApplication::Stop(int exitCode)')
  old='    m_frameMoveGuard.unlock();'
  assert body.count(old)==1
  body=body.replace(old,old+'\n\n#if defined(TARGET_ANDROID)\n'+block+'#endif',1)
  body=body.replace('    m_bStop = true;', '#if defined(TARGET_ANDROID) && defined(HAS_PYTHON)\n    CServiceBroker::GetXBPython().BeginShutdown();\n#endif\n    m_bStop = true;',1)
  text=text[:a]+body+text[b:]
 else:
  text=coop.transform(name,text)
 (dest/name).write_text(text)
# Diagnose late native cleanup even when low-level Python/thread detail fills up.
h=dest/diag.HEADER
text=h.read_text().replace('MAX_EVENTS = 2048','MAX_EVENTS = 8192').replace('infinity-shutdown-2103325-v1','infinity-shutdown-2103326-v1')
text=text.replace('inline std::atomic<int> descriptor{-1};','''inline std::atomic<int> descriptor{-1};
inline std::atomic<int> criticalDescriptor{-1};
inline std::atomic<unsigned> criticalCount{0};
constexpr unsigned MAX_CRITICAL_EVENTS = 1024;
inline bool Critical(const char* phase) noexcept
{
  // A separate budget: per-invoker/thread traffic cannot hide the final phase.
  return phase && (std::strncmp(phase,"application.",12)==0 ||
      std::strncmp(phase,"android.",8)==0 || std::strncmp(phase,"stop.",5)==0 ||
      std::strncmp(phase,"pre.",4)==0 || std::strncmp(phase,"cleanup.",8)==0 ||
      std::strncmp(phase,"scripts.",8)==0 || std::strncmp(phase,"services.",9)==0 ||
      std::strncmp(phase,"python.runtime",14)==0 || std::strncmp(phase,"process.",8)==0 ||
      std::strncmp(phase,"capture.",8)==0);
}''')
text=text.replace('  if (serial>MAX_EVENTS) return;','''  const bool critical=Critical(phase);
  const unsigned criticalSerial=critical ? criticalCount.fetch_add(1,std::memory_order_relaxed) : MAX_CRITICAL_EVENTS+1;
  if (serial>MAX_EVENTS && criticalSerial>MAX_CRITICAL_EVENTS) return;''')
text=text.replace('  if (serial==MAX_EVENTS) {kind="limit"; std::strcpy(safePhase,"capture.event_limit");outcome="truncated";}','')
old='  if(n>0 && static_cast<size_t>(n)<sizeof(row)) { const auto ignored=::write(fd,row,static_cast<size_t>(n)); (void)ignored; }'
new='''  if(n>0 && static_cast<size_t>(n)<sizeof(row))
  {
    const int criticalFd=criticalDescriptor.load(std::memory_order_acquire);
    if (critical && criticalSerial<MAX_CRITICAL_EVENTS && criticalFd>=0)
    { const auto ignored=::write(criticalFd,row,static_cast<size_t>(n)); (void)ignored; }
    if (serial<MAX_EVENTS)
    { const auto ignored=::write(fd,row,static_cast<size_t>(n)); (void)ignored; }
  }
  if (serial==MAX_EVENTS || (critical && criticalSerial==MAX_CRITICAL_EVENTS))
  {
    char limit[256]{};
    const int size=std::snprintf(limit,sizeof(limit),
      "{\\\"schema\\\":1,\\\"kind\\\":\\\"limit\\\",\\\"phase\\\":\\\"capture.event_limit\\\",\\\"pid\\\":%ld,\\\"session_start_ns\\\":%lld,\\\"boot_ns\\\":%lld,\\\"seq\\\":%u,\\\"outcome\\\":\\\"truncated\\\"}\\n",
      static_cast<long>(::getpid()),originNs,boot,serial);
    const int output=serial==MAX_EVENTS ? fd : criticalDescriptor.load();
    if(size>0 && static_cast<size_t>(size)<sizeof(limit) && output>=0)
    { const auto ignored=::write(output,limit,static_cast<size_t>(size)); (void)ignored; }
  }'''
assert old in text;text=text.replace(old,new)
old='  descriptor.store(fd,std::memory_order_release);'
new='''  // Preserve an independently bounded high-level timeline and its prior run.
  char criticalPath[1056]{},criticalPrevious[1080]{};
  const int cn=std::snprintf(criticalPath,sizeof(criticalPath),"%s.critical",path);
  const int pn=std::snprintf(criticalPrevious,sizeof(criticalPrevious),"%s.previous",criticalPath);
  if(cn>0 && pn>0 && static_cast<size_t>(cn)<sizeof(criticalPath) && static_cast<size_t>(pn)<sizeof(criticalPrevious))
  {
    const auto ignored=::rename(criticalPath,criticalPrevious); (void)ignored;
    criticalDescriptor.store(::open(criticalPath,O_WRONLY|O_CREAT|O_TRUNC|O_APPEND|O_CLOEXEC,0600),std::memory_order_release);
  }
  descriptor.store(fd,std::memory_order_release);'''
assert old in text;text=text.replace(old,new)
h.write_text(text)
# Add final cleanup sites that used to be visible only inside broad cleanup span.
name='xbmc/application/Application.cpp';p=dest/name;text=p.read_text()
for stmt,label in [('m_pAnnouncementManager->Deinitialize();','cleanup.announcement_deinitialize'),('m_pAnnouncementManager.reset();','cleanup.announcement_destructor'),('UnregisterSettings();','cleanup.unregister_settings')]:
 a,b,body=diag.function(text,'bool CApplication::Cleanup()');body=diag.span(body,stmt,label);text=text[:a]+body+text[b:]
p.write_text(text)

# Fail closed against the exact locally exercised outputs, not just an allow-list.
expected_delta={'xbmc/addons/Service.cpp': '9c7a3fe4dc4457214be50731d9ccee939cf72b33ecba8e72cd692537edfb1749', 'xbmc/application/Application.cpp': '747d8701b76006bbfecc80f9aa239e1c5eecfebb63c0fe15cd092962b8868d41', 'xbmc/interfaces/generic/ScriptInvocationManager.cpp': '999c6cd8d4081c3422bed9e155d8e69f06a4efdfc0590dfcfd62b9ee0860af29', 'xbmc/interfaces/generic/ScriptInvocationManager.h': '3a3eac4bd729cea9c743cd5225dea3051875fd16690091f6545fbcf1a1398b1f', 'xbmc/interfaces/python/PythonInvoker.cpp': '6aaf2ff0512938e14cbd876e023f96b2782d1a8d0e3744697d901f110a8c7a2d', 'xbmc/interfaces/python/XBPython.cpp': 'b8c041ef300537694d7ad6156ab8f507ab97c05f7f3a503dd6cf484de279ab27', 'xbmc/interfaces/python/XBPython.h': '306b2a9629b191e49fa66e7e7b6caca598364606a38b1dfc23d7d1e2ca509c7f', 'xbmc/platform/android/activity/InfinityShutdownTrace.h': '44774b6d08fe8656cf7fffcb0c98471eb1d85c323d34dfc49b5d8be8841947d8'}
actual=snapshot(source);changed={n for n in before.keys()|actual.keys() if before.get(n)!=actual.get(n)}
assert changed==set(expected_delta) and before.keys()==actual.keys(),'Undeclared native source delta'
assert {n:actual[n] for n in changed}==expected_delta,'Native output differs from reviewed/tested code'
args.receipt.parent.mkdir(parents=True,exist_ok=True)
args.receipt.write_text(json.dumps({'candidate':2103326,'parent':2103325,'locked_rollback':2103324,'kind':'native','before':before,'after':actual,'changed':sorted(changed),'physical_device_verified':False,'locked':False},indent=2)+'\n')
(args.receipt.parent/'native-reviewed.patch').write_text(''.join(''.join(difflib.unified_diff(original[n].splitlines(True),(source/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in sorted(changed)))
print('PASS: exact 2103325 source and reviewed eight-file cooperative repair; no native final-cleanup bypass')
