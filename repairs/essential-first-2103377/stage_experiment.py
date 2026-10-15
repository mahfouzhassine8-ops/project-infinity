#!/usr/bin/env python3
"""Stage an essential-first shutdown experiment on the exact locked source.

This patch is NOT a delivery gate. Production write-hook coverage, Android
validation and the full native build must independently pass before packaging.
"""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ACTIVITY = "xbmc/platform/android/activity/"
CHECKPOINT = ACTIVITY + "InfinityAndroidCheckpoint.cpp"
PIN = "13b492e2fd4b1885fa2127ebf1ea8bd2ed31fd3cbf35ebe82d3a3044383fa04b"

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Unverified source anchor: " + old[:120])
    return text.replace(old, new, 1)

def checkpoint(text):
    text = once(text, '#include "InfinityScriptPersistence.h"',
                '#include "InfinityScriptPersistence.h"\n#include "InfinityEssentialScriptFence.h"')
    at = text.index("struct Owner\n")
    text = text[:at] + '''// Keep all 17 diagnostic owners. Python retirement is optional; its shared
// file/transaction capabilities are independently required by the fence.
bool EssentialOwner(const std::string& name) { return name != "python_services"; }

''' + text[at:]
    text = once(text, '  ++s.errors;\n  const auto safeOwner=', '''  if (ownerName == "python_services" && !fatal)
  {
    // A diagnostic failure is not an essential save receipt or a global veto.
    auto& optional = s.owners[ownerName];
    optional.error = detail.substr(0, 384);
    optional.complete = false;
    optional.dirty = true;
    return;
  }
  ++s.errors;
  const auto safeOwner=''')
    text = once(text, '  result["schema"] = 1;\n  result["blocker_inventory_contract"]', '''  result["schema"] = 1;
  result["exit_policy"] = "essential_first_process_exit_v1";
  result["exit_kind"] = (s.phase == "SAFE_TO_TERMINATE" || s.phase == "ENGINE_TERMINATING") ?
      "essential_verified_process_exit" : "essential_first_process_exit_requested";
  result["process_death_confirmed"] = false;
  const auto essential = InfinityEssentialScriptFence::Snapshot();
  result["essential_write_generation"] = essential.generation;
  result["essential_writes_sealed"] = essential.sealed;
  result["essential_writes_durable"] = essential.durable;
  result["optional_unfinished_writers"] = static_cast<uint64_t>(essential.optionalUnfinished);
  result["optional_data_recovery_guaranteed"] = false;
  result["essential_write_blockers"] = CVariant(CVariant::VariantTypeArray);
  for (const auto& blocker : essential.blockers)
    result["essential_write_blockers"].push_back(blocker);
  result["blocker_inventory_contract"]''')
    text = once(text, '  result["owners"] = CVariant(CVariant::VariantTypeArray);',
                '  result["owners"] = CVariant(CVariant::VariantTypeArray);\n  result["essential_owners"] = CVariant(CVariant::VariantTypeArray);')
    text = once(text, '    result["required_owners"].push_back(name);', '''    result["required_owners"].push_back(name); // Legacy full diagnostic inventory.
    if (EssentialOwner(name)) result["essential_owners"].push_back(name);''')
    text = once(text, '    item["owner"] = name;',
                '    item["owner"] = name;\n    item["essential"] = EssentialOwner(name);')
    # Replace both authorization dependencies, not merely the final loop.
    start = text.index('  const auto scripts = InfinityScriptPersistence::Snapshot();',
                       text.index('bool AuthorizeTermination('))
    end = text.index('  const auto database = InfinityDatabaseBarrier::GetSnapshot();', start)
    text = text[:start] + '''  if (!InfinityEssentialScriptFence::Authorized(s.generation))
  {
    RecordFatalFailure("native_admission", "essential_write_fence_not_authorized");
    return false;
  }
''' + text[end:]
    text = once(text, '    const auto found = s.owners.find(name);\n    if (found == s.owners.end()',
                '    if (!EssentialOwner(name)) continue;\n    const auto found = s.owners.find(name);\n    if (found == s.owners.end()')
    start = text.index('      // Capture independently saveable local state now,')
    end = text.index('      Operation("background_jobs");', start)
    text = text[:start] + '''      // First-party callbacks have finished. Close new observed Python
      // mutation admission before examining existing protected capabilities.
      // No optional retirement pump, grace interval, Stop(true), or join.
      if (!InfinityEssentialScriptFence::CloseAdmission(s.generation,
            {CSpecialProtocol::TranslatePath("special://profile"),
             CSpecialProtocol::TranslatePath("special://masterprofile")},
            {CSpecialProtocol::TranslatePath("special://temp")}))
      {
        const auto denied = InfinityEssentialScriptFence::Snapshot();
        RecordFatalFailure("native_admission", denied.blockers.empty() ?
            "protected_write_admission_close_failed" : denied.blockers.front().c_str());
        return;
      }
      const auto essential = InfinityEssentialScriptFence::Snapshot();
      if (!essential.blockers.empty())
      {
        // Do not invent durability or wait out an optional service timeout.
        RecordFatalFailure("native_admission", essential.blockers.front().c_str());
        return;
      }
      // Leave python_services pending unless its original independent proof
      // is actually available. Never manufacture a 17/17 save result.
      const auto scripts = InfinityScriptPersistence::Snapshot();
      if (scripts.durable && scripts.active == 0 && scripts.blockingCount == 0)
        Complete("python_services", true);

''' + text[end:]
    text = once(text, '''          CScriptInvocationManager::GetInstance().AndroidCheckpointCompatCount() != 1 ||
          CScriptInvocationManager::GetInstance().AndroidCheckpointForeignScripts() != 0)''',
                '          CScriptInvocationManager::GetInstance().AndroidCheckpointCompatCount() != 1)')
    text = once(text, '{ RecordFatalFailure("python_services", "source_contract_changed_or_unproven_writer_admitted"); return; }',
                '{ RecordFatalFailure("native_admission", "essential_participant_source_contract_changed"); return; }')
    text = once(text, '      Complete("native_admission", false);\n      s.stage = 5;', '''      if (!InfinityEssentialScriptFence::Seal(s.generation))
      { RecordFatalFailure("native_admission", "essential_script_file_seal_failed"); return; }
      Complete("native_admission", false);
      s.stage = 5;''')
    text = once(text, '        const auto& owner = s.owners.at(name);',
                '        if (!EssentialOwner(name)) continue;\n        const auto& owner = s.owners.at(name);')
    return text

def apply(root):
    root = Path(root)
    source = root / CHECKPOINT
    old = source.read_bytes()
    if hashlib.sha256(old).hexdigest() != PIN:
        raise ValueError("Not the exact Rails Handoff RC1 coordinator")
    result = checkpoint(old.decode())
    target = root / (ACTIVITY + "InfinityEssentialScriptFence.h")
    if target.exists():
        raise ValueError("Refusing duplicate fence staging")
    source.write_text(result)
    target.write_bytes((HERE / target.name).read_bytes())
    return {
        "before": {CHECKPOINT: PIN},
        "after": {CHECKPOINT: hashlib.sha256(source.read_bytes()).hexdigest(),
                  ACTIVITY + target.name: hashlib.sha256(target.read_bytes()).hexdigest()},
        "production_hook_coverage_verified": False,
        "candidate_deliverable": False,
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(apply(args.source), indent=2) + "\n")
