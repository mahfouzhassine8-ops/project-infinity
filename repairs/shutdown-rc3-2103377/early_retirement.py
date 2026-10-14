#!/usr/bin/env python3
"""Move *cooperative* unknown Python service stop to native Request(), not stage 1.

Protect canonical Command Center and compat writers; no GIL/async exception,
thread detach, required-save bypass, deadline change, or process hard kill.

The script manager already owns the stop contract. The changes below only
advance its first notification and make accidental duplicate starts idempotent.
"""
from pathlib import Path
import hashlib
import json

CHECKPOINT="xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
SCRIPT_MANAGER="xbmc/interfaces/generic/ScriptInvocationManager.cpp"
SCRIPT_MANAGER_PIN="847d9b0fdb26fde4973744689204bbd7531e2fa249e423c63dd9539cda430239"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def once(text,original,replacement,name):
    if text.count(original)!=1:
        raise ValueError("Unexpected exact RC3 early-retirement anchor: "+name+" count="+str(text.count(original)))
    return text.replace(original,replacement,1)

def apply(source,expected_checkpoint_sha):
    source=Path(source)
    checkpoint=source/CHECKPOINT
    manager=source/SCRIPT_MANAGER
    original_checkpoint=checkpoint.read_bytes()
    original_manager=manager.read_bytes()
    if sha(original_checkpoint)!=expected_checkpoint_sha or sha(original_manager)!=SCRIPT_MANAGER_PIN:
        raise ValueError("RC3 native source lineage mismatch: no early retirement edit permitted")
    c=original_checkpoint.decode()
    m=original_manager.decode()
    # We inventory existing and historical unknown writers BEFORE signalling
    # their monitors, so a very fast retirement cannot erase the obligation.
    c=once(c,'''  CScriptInvocationManager::GetInstance().BeginShutdown();
  const auto unresolved = CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters();
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    s.unresolvedForeignOwners = unresolved;
    s.requestReady = true;
  }
  return true;''',
'''  CScriptInvocationManager::GetInstance().BeginShutdown();
  const auto unresolved = CScriptInvocationManager::GetInstance().AndroidCheckpointUnresolvedWriters();
  // Do not defer Monitor.abortRequested() until the application has frozen
  // playback and finalized Command Center. That delay allowed Playlist Browser
  // to start a fresh Curl read several seconds AFTER Close in the Fold trace.
  // The script manager selects ONLY unknown/nonpersistent generic services;
  // recognized resident Command Center and compat save owners are excluded.
  // NotifyScriptAborting is the existing native event/latch mechanism; the
  // subsequent Stop(false) sets CPythonInvoker's legacy m_stop flag with NO
  // join, injected SystemExit, GIL entry, or unsafe persistence receipt.
  CScriptInvocationManager::GetInstance().BeginAndroidCheckpoint();
  InfinityShutdownTrace::Event("milestone", "rc3.python_abort_requested_at_close");
  {
    std::lock_guard<std::mutex> lock(s.mutex);
    s.unresolvedForeignOwners = unresolved;
    s.requestReady = true;
  }
  return true;''',
    "native request starts service retirement early")
    c=once(c,'''      CScriptInvocationManager::GetInstance().BeginAndroidCheckpoint();
      Operation("command_center");''',
'''      // Request() already notified unknown Python services at Close time.
      // Repeating BeginAndroidCheckpoint() here would reset the 3s grace
      // timer and possibly duplicate/reorder stop callbacks.
      Operation("command_center");''',
    "remove deferred stage-one Python stop")
    m=once(m,'''    m_shutdownRequested = true;
    m_androidCheckpointRetirementStarted = std::chrono::steady_clock::now();''',
'''    m_shutdownRequested = true;
    // Only one stop notification wave per engine checkpoint. Retaining the
    // original grace start also prevents a late stage restart from hiding a
    // stubborn service behind another full timeout.
    if (m_androidCheckpointRetirementArmed)
      return;
    m_androidCheckpointRetirementStarted = std::chrono::steady_clock::now();''',
    "idempotent Python stop at first native checkpoint")
    # Future reviewers: do not let this change move native save authority.
    for preserved in (
      'bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)',
      'if (!InfinityDatabaseBarrier::Seal(s.generation))',
      's.phase = "SAFE_TO_TERMINATE";',
      'Complete("python_services", true);',
      'if (scriptManager.AndroidCheckpointEscalationsActive() != 0)',
    ):
        if c.count(preserved)!=original_checkpoint.decode().count(preserved):
            raise ValueError("RC3 early stop unexpectedly altered final save authority: "+preserved)
    checkpoint.write_text(c)
    manager.write_text(m)
    return {
      "before":{CHECKPOINT:sha(original_checkpoint),SCRIPT_MANAGER:sha(original_manager)},
      "after":{CHECKPOINT:sha(c.encode()),SCRIPT_MANAGER:sha(m.encode())},
      "changed":[CHECKPOINT,SCRIPT_MANAGER],
      "first_stop_before_playback_checkpoint":True,
      "source_ledger_snapshotted_before_abort":True,
      "same_legacy_and_monitor_signals":True,
      "commandcenter_and_compat_excluded_by_existing_contract":True,
      "idempotent_reentry":True,
      "required_writer_retirement_waived":False,
      "system_exit_injected":False,
      "deadline_changed":False,
      "native_termination_authority_changed":False,
      "full_native_build_passed":False,
      "physical_fold_verified":False
    }

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--expected-checkpoint-sha256",required=True)
    p.add_argument("--receipt",required=True,type=Path)
    args=p.parse_args()
    report=apply(args.source,args.expected_checkpoint_sha256)
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
