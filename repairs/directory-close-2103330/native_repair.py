#!/usr/bin/env python3
"""Cancel abandoned Android background listing waits, not their script owners."""
from pathlib import Path
import argparse, difflib, hashlib, json

HERE = Path(__file__).resolve().parent
MANAGER_H = 'xbmc/interfaces/generic/ScriptInvocationManager.h'
MANAGER_C = 'xbmc/interfaces/generic/ScriptInvocationManager.cpp'
RUNNER = 'xbmc/interfaces/generic/ScriptRunner.cpp'
DIRECTORY = 'xbmc/guilib/listproviders/DirectoryProvider.cpp'
TRACE = 'xbmc/platform/android/activity/InfinityShutdownTrace.h'
ALLOWED = {MANAGER_H, MANAGER_C, RUNNER, DIRECTORY, TRACE}

def sha(data): return hashlib.sha256(data).hexdigest()
def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob('*')
            if p.is_file() and '.git' not in p.relative_to(root).parts}
def require(ok, msg):
    if not ok: raise ValueError(msg)
def once(text, before, after):
    require(text.count(before) == 1, 'Unexpected source preimage: '+before[:160])
    return text.replace(before, after, 1)

def transform(name, text):
    if name == MANAGER_H:
        return once(text, '  void BeginShutdown();', '''  void BeginShutdown();
  // Read the existing admission gate; does not stop or release an invoker.
  bool IsShutdownRequested() const;''')
    if name == MANAGER_C:
        return once(text, 'void CScriptInvocationManager::BeginShutdown()', '''bool CScriptInvocationManager::IsShutdownRequested() const
{
  std::unique_lock<CCriticalSection> lock(m_critSection);
  return m_shutdownRequested;
}

void CScriptInvocationManager::BeginShutdown()''')
    if name == RUNNER:
        text = once(text, '#include "ScriptRunner.h"', '''#include "ScriptRunner.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityShutdownTrace.h"
#endif''')
        old = '''    // wait for the script to finish or be cancelled
    while (!IsCancelled() && CScriptInvocationManager::GetInstance().IsRunning(scriptId) &&
           !m_scriptDone.Wait(20ms))
      ;

    // give the script 30 seconds to exit before we attempt to stop it
    XbmcThreads::EndTime<> timer(30s);
    while (!timer.IsTimePast() && CScriptInvocationManager::GetInstance().IsRunning(scriptId) &&
           !m_scriptDone.Wait(20ms))
      ;'''
        new = '''#if defined(TARGET_ANDROID)
    // A background directory RESULT is not the language invoker's lifetime.
    // During global shutdown its display consumer must not wait for Python
    // finalization that is owned by later ScriptInvocationManager cleanup.
    // Returning false unregisters the result handle through its existing lock.
    // No SetDone, Stop, registry erase, thread detach or early final join here.
    auto shutdownResultCancelled = [this, scriptId]() {
      if (!CScriptInvocationManager::GetInstance().IsShutdownRequested())
        return false;
      const auto addon = GetAddon();
      const std::string addonId = addon ? addon->ID() : std::string{};
      InfinityShutdownTrace::Event("milestone", "directory.result_wait_cancelled",
                                  scriptId, 0, 0, 0, addonId.c_str(), "result_cancelled");
      return true;
    };
#endif
    // wait for the script to finish or be cancelled
    while (!IsCancelled() && CScriptInvocationManager::GetInstance().IsRunning(scriptId) &&
           !m_scriptDone.Wait(20ms))
    {
#if defined(TARGET_ANDROID)
      if (shutdownResultCancelled())
        return false;
#endif
    }

#if defined(TARGET_ANDROID)
    if (shutdownResultCancelled())
      return false;
#endif
    // give the script 30 seconds to exit before we attempt to stop it
    XbmcThreads::EndTime<> timer(30s);
    while (!timer.IsTimePast() && CScriptInvocationManager::GetInstance().IsRunning(scriptId) &&
           !m_scriptDone.Wait(20ms))
    {
#if defined(TARGET_ANDROID)
      if (shutdownResultCancelled())
        return false;
#endif
    }
#if defined(TARGET_ANDROID)
    if (shutdownResultCancelled())
      return false;
#endif'''
        return once(text, old, new)
    if name == DIRECTORY:
        text = once(text, '#include "DirectoryProvider.h"', '''#include "DirectoryProvider.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityShutdownTrace.h"
#endif''')
        text = once(text, '''    CFileItemList items;
    if (CDirectory::GetDirectory(m_url, items, "", DIR_FLAG_DEFAULTS))
    {''', '''#if defined(TARGET_ANDROID)
    // Display-only work checks the existing JobManager cancellation contract.
    if (ShouldCancel(0, 0))
      return false;
    InfinityShutdownTrace::Scope fetchEvidence("directory.fetch");
#endif
    CFileItemList items;
    const bool fetched = CDirectory::GetDirectory(m_url, items, "", DIR_FLAG_DEFAULTS);
#if defined(TARGET_ANDROID)
    fetchEvidence.End();
    if (ShouldCancel(0, 0))
      return false;
#endif
    if (fetched)
    {''')
        return once(text, '''      for (int i = 0; i < limit; i++)
      {
        CGUIStaticItemPtr item(new CGUIStaticItem(*items[i]));''', '''      for (int i = 0; i < limit; i++)
      {
#if defined(TARGET_ANDROID)
        if (ShouldCancel(static_cast<unsigned int>(i), static_cast<unsigned int>(limit)))
          return false;
        InfinityShutdownTrace::Scope itemEvidence("directory.metadata_item");
#endif
        CGUIStaticItemPtr item(new CGUIStaticItem(*items[i]));''')
    if name == TRACE:
        text = once(text, 'infinity-shutdown-2103327-v1', 'infinity-shutdown-2103330-v1')
        return once(text, 'std::strncmp(phase,"jobs.",5)==0);',
                    'std::strncmp(phase,"jobs.",5)==0 || std::strncmp(phase,"directory.",10)==0);')
    raise ValueError('Unexpected target: '+name)

def apply(source, proof, receipt):
    expected = json.loads(proof.read_text())['after']
    delta = json.loads((HERE/'native-delta.json').read_text())
    require(sha(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()) == delta['parent_map'],
            'Not exact 2103327 native map')
    before = snapshot(source)
    require(before == expected, 'Complete native source differs from 2103327')
    originals = {n:(source/n).read_text() for n in ALLOWED}
    for name in sorted(ALLOWED):
        require(before.get(name) == delta['before'][name], 'Unexpected native preimage: '+name)
        p = source/name; p.write_text(transform(name, p.read_text()))
    after = snapshot(source)
    changed = {n for n in before.keys() | after.keys() if before.get(n) != after.get(n)}
    require(before.keys() == after.keys() and changed == ALLOWED, 'Undeclared native delta')
    require({n:after[n] for n in changed} == delta['after'], 'Native output differs from tested delta')
    result = dict(candidate=2103330, parent=2103327, locked_rollback=2103327,
                  before=before, after=after, changed=sorted(changed),
                  result_wait_cancellation=True, final_worker_join_preserved=True,
                  script_owner_cleanup_preserved=True, physical_device_verified=False, locked=False)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2)+'\n')
    (receipt.parent/'native-reviewed.patch').write_text(''.join(''.join(difflib.unified_diff(originals[n].splitlines(True),(source/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in sorted(changed)))
    print('PASS: exact 2103327 source; five-file Android background result-wait repair')

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--proof',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();apply(a.source,a.proof,a.receipt)
