#!/usr/bin/env python3
"""RC3 provisional *independent* native snapshot before waiting on Python.

This does NOT seal the persistence barrier or mark owners durable. The full
native-owner save pass remains mandatory after Python retirement. A failed
provisional local save is a real error, not a pass or termination waiver.
"""
from pathlib import Path
import hashlib
import json

SOURCE="xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp"
PIN="723f680401a31b36c21ee7b2cfa673feb48f622cb96e31d9c6365e3b44c52bcf"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def once(text, old, new):
    if text.count(old)!=1:
        raise RuntimeError(f"Missing or ambiguous RC3 early-save source anchor: {old[:100]}")
    return text.replace(old,new,1)

def apply(root):
    path=Path(root)/SOURCE
    data=path.read_bytes()
    if sha(data)!=PIN:
        raise RuntimeError("RC3 refuses non-pinned RC2 native shutdown coordinator: "+sha(data))
    source=data.decode()
    source=once(source,
        '  unsigned int stage{0}; // Written only by the application-thread pump.',
        '''  unsigned int stage{0}; // Written only by the application-thread pump.
  // Provisional copies protect already-local state against remote stalls; these
  // are never enough to authorize exit. Final owner saves remain mandatory.
  bool earlyLocalSnapshotAttempted{false};''')
    source=once(source,
        '    s.stage = 0;\n    s.sealed=false;',
        '    s.stage = 0;\n    s.earlyLocalSnapshotAttempted=false;\n    s.sealed=false;')
    marker='''      Complete("compat", true);

      // Inventory every script writer before deciding the global checkpoint.'''
    insert='''      Complete("compat", true);

      // Capture independently saveable local state now, before the optional
      // Python/network retirement gate. This is intentionally PROVISIONAL.
      // Callbacks from admitted scripts may still modify these stores later;
      // their mandatory final save/receipt occurs in stage five, unchanged.
      // Never count a provisional write as proof for SAFE_TO_TERMINATE.
      if (!s.earlyLocalSnapshotAttempted)
      {
        {
          std::lock_guard<std::mutex> lock(s.mutex);
          if (s.activeWrites != 0 || s.phase == "CHECKPOINT_FAILED")
            return;
          s.earlyLocalSnapshotAttempted = true;
        }
        InfinityShutdownTrace::Scope early("rc3.early_local_snapshot");
        const auto before = ErrorGeneration();
        const bool settingsOk = CServiceBroker::GetSettingsComponent()->GetSettings()->Save();
        const bool skinOk = CheckpointSkinSettings();
        const bool favouriteOk = CServiceBroker::GetFavouritesService().CheckpointForAndroidExit();
        if (!settingsOk || !skinOk || !favouriteOk || HasFailureSince(before))
        {
          RecordFailure("xml_files", "rc3_early_local_snapshot_failed");
          return;
        }
        InfinityShutdownTrace::Event("milestone", "rc3.provisional_local_snapshot_complete");
      }

      // Inventory every script writer before deciding the global checkpoint.'''
    source=once(source,marker,insert)
    # These downstream original save and termination gates are deliberately
    # unchanged. The earlier copies NEVER cause Complete(owner,..).
    for required in [
        'Complete("python_services", true);',
        'if (!InfinityDatabaseBarrier::Seal(s.generation))',
        'Operation("kodi_settings");',
        'Operation("favourites");',
        'Operation("profiles");',
        's.phase = "SAFE_TO_TERMINATE";',
        'bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid)',
    ]:
        if required not in source:
            raise RuntimeError("Cannot validate mandatory existing safety gate "+required)
    result=source.encode()
    path.write_bytes(result)
    return dict(source=SOURCE,before=sha(data),after=sha(result),
                changed=[SOURCE],final_owner_save_pass_retained=True,
                early_snapshot_only=True,remaining_unverified_python_writers_abandoned=False,
                termination_authorization_modified=False,
                early_snapshot_confers_durability_receipt=False)

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args()
    d=apply(args.source)
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(d,sort_keys=True,indent=2)+"\n")
