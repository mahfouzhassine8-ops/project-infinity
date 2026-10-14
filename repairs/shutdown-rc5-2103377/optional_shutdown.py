#!/usr/bin/env python3
"""Apply narrowly scoped optional stop-only Trakt and Infinity Continuity contracts.

Trakt and skin diagnostic trace are NOT Infinity-required save owners. They
remain active and unchanged until native Close, at which time native
NotifyScriptAborting + Stop(false) is used. No third-party add-on is modified.

Only recognised script identity/path permits this exemption. Any other Python
writer still requires the complete checkpoint/retirement/durability barrier.
"""
import argparse
import hashlib
import json
from pathlib import Path

CLASSIFIER = "xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp"
MANAGER = "xbmc/interfaces/generic/ScriptInvocationManager.cpp"
CONTINUITY_211 = "a9a5477eec6ae1684d04d6b0a574be3f6b07172ca793240af82c8d26a421c9d1"
CONTINUITY_212 = "97469b505ffae522b31a5bf96ef4313b2b184d1abd5937ee52b65dd7fe96599a"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def replace_one(text, before, after, label):
    n = text.count(before)
    if n != 1:
        raise RuntimeError("RC5 unverified source anchor "+label+": "+str(n))
    return text.replace(before, after, 1)

OPTIONAL_BLOCK = r'''    // RC5: Trakt is a user-controlled external/cloud integration, not the
    // authoritative local-first Infinity Resume Hub. Its addon-owned default
    // entry stays available and upgradeable while Infinity is RUNNING.
    // On native Close this contract receives cooperative Stop(false) but
    // NEVER joins the local required-save/writer admission barrier.
    // Verify both the registered addon pointer's ID and its exact Kodi
    // add-on entry path. Other Trakt scripts and spoofed add-ons fail closed.
    if (addon == "script.trakt")
    {
      for (const char* root : {"special://home/addons/", "special://xbmc/addons/"})
      {
        const std::string entry = std::string(root) + "script.trakt/default.py";
        if (actual == CSpecialProtocol::TranslatePath(entry))
          return "stop-only:trakt-cloud-owned";
      }
    }

    // Continuity is an Infinity skin diagnostic trace, NOT saved viewing
    // state. Keep its runtime property bridge intact; stop its background
    // observer at Close without letting optional trace JSON-RPC/read or flush
    // hold up local user save owners. Unlike Trakt, it is pinned to the exact
    // reviewed skin source, because raw RunScript has no AddonPtr.
    if (addon.empty() || addon == "skin.infinity.diggz")
    {
      for (const char* root : {"special://home/addons/", "special://xbmc/addons/"})
      {
        const std::string entry = std::string(root) +
            "skin.infinity.diggz/resources/lib/infinity_continuity.py";
        if (actual != CSpecialProtocol::TranslatePath(entry))
          continue;
        const auto digest = CUtil::GetFileDigest(entry, KODI::UTILITY::CDigest::Type::SHA256);
        if (digest == "a9a5477eec6ae1684d04d6b0a574be3f6b07172ca793240af82c8d26a421c9d1" ||
            digest == "97469b505ffae522b31a5bf96ef4313b2b184d1abd5937ee52b65dd7fe96599a")
          return "stop-only:continuity-diagnostic";
      }
    }
'''

def apply(source: Path):
    source = Path(source)
    classifier = source / CLASSIFIER
    manager = source / MANAGER
    inputs = {CLASSIFIER: classifier.read_bytes(), MANAGER: manager.read_bytes()}
    c, m = (inputs[p].decode("utf-8") for p in (CLASSIFIER, MANAGER))
    assert "stop-only:trakt-cloud-owned" not in c, "Do not double-stage RC5"
    assert "stop-only:continuity-diagnostic" not in c, "Do not double-stage RC5"
    assert 'InfinityScriptPersistence::Admit(' in m
    assert 'if (checkpointContract.empty())' in m
    assert 'CServiceBroker::GetXBPython().NotifyScriptAborting(thread.get());' in m
    assert 'invoker->Stop(false);' in m
    c = replace_one(c, '''    // Home RunScript has no add-on object.''',
                    OPTIONAL_BLOCK + '''    // Home RunScript has no add-on object.''',
                    "classifier_approved_entry")
    m = replace_one(m,
        '''        if (contract.empty() || contract.rfind("nonpersistent:", 0) == 0 ||
            contract.rfind("reconstructible-cache:", 0) == 0)''',
        '''        if (contract.empty() || contract.rfind("nonpersistent:", 0) == 0 ||
            contract.rfind("reconstructible-cache:", 0) == 0 ||
            contract.rfind("stop-only:", 0) == 0)''',
        "cooperative_stop_only")
    # Contract admission is checked before the existing 'empty()' ledger/admit
    # checks; we neither change their logic nor silently return a fake receipt.
    assert m.count('if (checkpointContract.empty())') == inputs[MANAGER].decode().count('if (checkpointContract.empty())') == 2
    assert m.count('InfinityScriptPersistence::Admit(') == inputs[MANAGER].decode().count('InfinityScriptPersistence::Admit(')
    assert m.count('AndroidCheckpointForeignScripts()') == 1
    assert m.count('NotifyScriptAborting(thread.get());') == 1
    assert "stop-only:trakt-cloud-owned" in c and "stop-only:continuity-diagnostic" in c
    assert c.count('addon == "script.trakt"') == 1
    out = {CLASSIFIER: c.encode(), MANAGER: m.encode()}
    for name, data in out.items():
        (source / name).write_bytes(data)
    return {
        "scope": "registered Trakt default.py and SHA-pinned Infinity Continuity skin trace only",
        "before": {p: sha(data) for p, data in inputs.items()},
        "after": {p: sha(data) for p, data in out.items()},
        "changed": list(out),
        "trakt_enabled_and_files_unchanged": True,
        "trakt_updates_not_source_pinned": True,
        "trakt_not_required_save_owner": True,
        "trakt_receipt_fabricated": False,
        "normal_running_unchanged": True,
        "native_cooperative_stop_at_close": True,
        "continuity_exact_source_pinned": [CONTINUITY_211, CONTINUITY_212],
        "other_foreign_writers_still_require_durability": True,
        "actual_inflight_optional_external_writes_guaranteed": False,
        "all_17_required_owner_gates_unchanged": True,
        "native_full_build_passed": False,
        "full_loaded_fold_verified": False,
        "locked": False,
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    report = apply(args.source)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps(report, indent=2, sort_keys=True))
