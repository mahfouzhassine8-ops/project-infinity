#!/usr/bin/env python3
"""RC4 source-only contract for delayed, accurate, refreshable close notice.

This does NOT validate physical shutdown, Trakt Python socket cancellation,
Infinity Continuity retirement, safe-to-terminate, or watched-state durability.
"""
import argparse
import json
from pathlib import Path

def verify(build: Path, folder: Path) -> dict:
    root = build / "xbmc/java/com/projectinfinity/kodi"
    guard = (root / "InfinityCloseGuardService.java").read_text()
    splash = (root / "Splash.java").read_text()
    checks = {
        "deferred_to_6500ms": "RC3_RECOVERY_GRACE_MS=6500L" in guard,
        "dialog_eligibility_agrees": "System.currentTimeMillis()-owner.closeAt>=6500L" in splash,
        "initial_offer_scheduled": "ui.postDelayed(this::offerRC3Recovery,RC3_RECOVERY_GRACE_MS)" in guard,
        "recheck_every_second": "ui.postDelayed(this::offerRC3Recovery,1000L)" in guard,
        "iterates_entire_live_pending_list": "for(int i=0;i<pending.length();i++)" in guard,
        "does_not_use_first_pending_only": "pending.optString(0" not in guard,
        "live_trakt_and_continuity_names": 'names.add("Trakt")' in guard and 'names.add("Infinity Continuity")' in guard,
        "other_three_names_present": all(('names.add("'+n+'")') in guard for n in ("Playlist Browser","Umbrella","Zeus768")),
        "generic_when_no_pending": "Still closing: verifying saved data" in guard,
        "no_unverified_save_claim": "Still saving:" not in guard,
        "full_service_count_not_first_name": '" pending). Tap for options"' in guard,
        "no_stale_label_event": "rc3.grace_elapsed_wait_or_force_choice" not in guard,
        "no_new_force_close_termination": "System.exit(" not in guard and "killProcess(" not in guard,
        "all_exit_phases_respected": all(('"'+x+'".equals(phase)') in guard for x in ("COMPLETE","SAFE_TO_TERMINATE","ENGINE_TERMINATING","CHECKPOINT_FAILED")),
        "checkpoint_and_274_receipts_preserved": (folder / "SOURCE-PRESERVATION.json").is_file(),
    }
    if not all(checks.values()):
        raise AssertionError("RC4 recovery source contract failed: "+repr([k for k,v in checks.items() if not v]))
    return {"scope":"RC4 notification source and original Java input parity only; not device shutdown proof",
            "checks": checks,"passed":len(checks),"total":len(checks),"physical_fold_verified":False,
            "third_party_service_retirement_verified":False,"save_receipts_fabricated":False,
            "locked":False}

if __name__ == "__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--build",required=True,type=Path)
    cli.add_argument("--folder",required=True,type=Path)
    args=cli.parse_args()
    result=verify(args.build,args.folder)
    output=args.folder/"RC4-NOTICE-SOURCE-VERIFICATION.json"
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(f"RC4 notification source: {result['passed']}/{result['total']} checked; physical shutdown NOT verified")
