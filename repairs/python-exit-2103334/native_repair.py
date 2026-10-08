#!/usr/bin/env python3
"""Close the late message admission race and capture bounded script-exit evidence on the exact 3330 engine installed in 3333."""
from pathlib import Path
import argparse,difflib,hashlib,json,shutil
HERE=Path(__file__).resolve().parent
INVOKER='xbmc/interfaces/python/PythonInvoker.cpp'
HELPER='xbmc/interfaces/python/InfinityPythonExitEvidence.h'
MESSENGER='xbmc/messaging/ApplicationMessenger.cpp'
MESSENGER_H='xbmc/messaging/ApplicationMessenger.h'
TRACE='xbmc/platform/android/activity/InfinityShutdownTrace.h'
THREAD='xbmc/threads/Thread.cpp'
ALLOWED={INVOKER,HELPER,TRACE,THREAD,MESSENGER,MESSENGER_H}
PARENT_MAP='d1e9fd8d209935463a960dd9c73bb32cf7936843f49a3b9407c02097e3970b52'

def sha(data):return hashlib.sha256(data).hexdigest()
def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
def require(ok,msg):
    if not ok:raise ValueError(msg)
def once(text,old,new):
    require(text.count(old)==1,'Source preimage changed: '+old[:120]);return text.replace(old,new,1)

def transform(name,text):
    if name==INVOKER:
        text=once(text,'#include "PythonInvoker.h"','#include "PythonInvoker.h"\n#if defined(TARGET_ANDROID)\n#include "InfinityPythonExitEvidence.h"\n#endif')
        old='      PyThreadState* state = PyInterpreterState_ThreadHead(m_threadState->interp);\n      while (state)'
        new='#if defined(TARGET_ANDROID)\n      InfinityPythonExitEvidence::Capture(ts, [this](unsigned long id, const char* file,\n                                                     const char* function, int line) {\n        char target[65]{};\n        std::snprintf(target, sizeof(target), "%lu:%.16s:%d:%.16s", id, file, line, function);\n        InfinityShutdownTrace::Event("milestone", "python.exit_frame", GetId(), 0, 0, 0,\n                                    m_addon ? m_addon->ID().c_str() : nullptr,\n                                    line > 0 ? "frame_observed" : "no_python_frame", target);\n      });\n#endif\n      PyThreadState* state = PyInterpreterState_ThreadHead(m_threadState->interp);\n      while (state)'
        text=once(text,old,new)
        text=once(text,'        executeScript(fp, realFilename, moduleDict);','''        executeScript(fp, realFilename, moduleDict);
        InfinityShutdownTrace::Event("milestone", "python.bytecode_returned", GetId(), 0, 0, 0,
                                    m_addon ? m_addon->ID().c_str() : nullptr);''')
        text=once(text,'        old = s;','''        old = s;
        char target[32]{};
        std::snprintf(target, sizeof(target), "%lu", s->thread_id);
        InfinityShutdownTrace::Event("milestone", "python.child_thread_wait", GetId(), 0, 0, 0,
                                    m_addon ? m_addon->ID().c_str() : nullptr,
                                    "waiting", target);''')
        return text
    if name==TRACE:
        text=once(text,'infinity-shutdown-2103330-v1','infinity-shutdown-2103334-v1')
        return once(text,'std::strncmp(phase,"python.runtime",14)==0 ||',
            'std::strncmp(phase,"python.runtime",14)==0 || std::strcmp(phase,"python.exit_frame")==0 ||\n      std::strcmp(phase,"python.bytecode_returned")==0 || std::strcmp(phase,"python.child_thread_wait")==0 ||')
    if name==MESSENGER_H:
        text=once(text,'#include <map>','#if defined(TARGET_ANDROID)\n#include <atomic>\n#endif\n#include <map>')
        return once(text,'  bool m_bStop{ false };','#if defined(TARGET_ANDROID)\n  std::atomic<bool> m_bStop{false};\n#else\n  bool m_bStop{ false };\n#endif')
    if name==MESSENGER:
        text=once(text,'#include "ApplicationMessenger.h"','#include "ApplicationMessenger.h"\n#if defined(TARGET_ANDROID)\n#include "platform/android/activity/InfinityShutdownTrace.h"\n#endif')
        return once(text,'  std::unique_lock<CCriticalSection> lock(m_critSection);\n\n  if (msg->dwMessage == TMSG_GUI_MESSAGE)','  std::unique_lock<CCriticalSection> lock(m_critSection);\n\n#if defined(TARGET_ANDROID)\n  // Stop can occur after the fast-path check, before this queue lock. Recheck\n  // while serialized with Cleanup: either the request is admitted before the\n  // drain and its waiter is signalled there, or it is rejected here. Never\n  // leave a late synchronous sender waiting on an already drained queue.\n  if (m_bStop)\n  {\n    InfinityShutdownTrace::Event("milestone", "scripts.late_message_rejected", -1,\n                                0, 0, 0, nullptr, "not_dispatched");\n    delete msg;\n    return -1;\n  }\n#endif\n\n  if (msg->dwMessage == TMSG_GUI_MESSAGE)')
    if name==THREAD:
        return once(text,'''    if (!Join(std::chrono::milliseconds::max())) // eh?
      lthread->join();''','''    if (!Join(std::chrono::milliseconds::max())) // eh?
    {
      // Evidence only: retain the exact unconditional native join fallback.
      InfinityShutdownTrace::Scope evidence("thread.std_join_fallback", -1, nullptr, m_ThreadName.c_str());
      lthread->join();
    }''')
    raise ValueError('Unexpected native target: '+name)

def apply(source,proof,receipt):
    expected=json.loads(proof.read_text())['after']
    require(sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())==PARENT_MAP,'Wrong full 3330 native parent map')
    before=snapshot(source);require(before==expected,'Not exact native source installed in 3333')
    require(HELPER not in before,'Exit evidence helper unexpectedly exists')
    delta=json.loads((HERE/'native-delta.json').read_text())
    originals={n:(source/n).read_text() for n in ALLOWED if n!=HELPER}
    for n,t in originals.items():(source/n).write_text(transform(n,t))
    shutil.copy2(HERE/'InfinityPythonExitEvidence.h',source/HELPER)
    after=snapshot(source)
    changed={n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}
    require(changed==ALLOWED and after.keys()-before.keys()=={HELPER} and not before.keys()-after.keys(),'Unexpected native file delta')
    require({n:after[n] for n in changed}==delta['after'],'Unreviewed native postimages')
    result=dict(candidate=2103334,parent=2103330,apk_parent=2103333,locked_rollback=2103327,
        before=before,after=after,changed=sorted(changed),late_message_admission_recheck=True,python_abort_behavior_changed=False,
        shutdown_timeout_changed=False,final_joins_preserved=True,physical_device_verified=False,locked=False)
    receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n')
    patches=[]
    for n in sorted(ALLOWED):
        patches.extend(difflib.unified_diff(originals.get(n,'').splitlines(True),(source/n).read_text().splitlines(True),fromfile='a/'+n if n in originals else '/dev/null',tofile='b/'+n))
    (receipt.parent/'native-reviewed.patch').write_text(''.join(patches))
    print('PASS: exact 3330 parent; late-message rejection plus bounded evidence; Python abort policy unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();apply(a.source,a.proof,a.receipt)
