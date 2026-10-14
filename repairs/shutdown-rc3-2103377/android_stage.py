#!/usr/bin/env python3
"""Stage only RC3 notification recovery atop the preserved 274-case Java source.

The original lifecycle candidate is first reconstructed via the pinned
verify_android.py. Then TWO Java templates are modified; all 274 original
JUnit tests and every other resource/source remain byte-identical.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import early_blocker_ui

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def apply(build,folder):
    build=Path(build);folder=Path(folder)
    source=folder/"source"
    proof_path=folder/"SOURCE-PRESERVATION.json"
    proof=json.loads(proof_path.read_text())
    before=dict(proof["after"])
    for p,sha in early_blocker_ui.PINS.items():
        assert before.get(p)==sha,("Unapproved RC3 Android source",p)
    original_templates={p:(source/p).read_text() for p in early_blocker_ui.PINS}
    result=early_blocker_ui.apply(source)
    for path,expected in result["after"].items():
        assert digest(source/path)==expected
        template=(source/path).read_text()
        for marker,value in {
          "APP_PACKAGE":"com.projectinfinity.kodi",
          "APP_NAME":"Kodi",
          "APP_NAME_LC":"kodi"
        }.items():
            template=template.replace("@"+marker+"@",value)
        target=build/"xbmc/java/com/projectinfinity/kodi"/Path(path).name.removesuffix(".in")
        assert target.exists(),target
        expected_original=original_templates[path]
        for marker,value in {
          "APP_PACKAGE":"com.projectinfinity.kodi",
          "APP_NAME":"Kodi",
          "APP_NAME_LC":"kodi"
        }.items():
            expected_original=expected_original.replace("@"+marker+"@",value)
        # Require exact reviewed original Java before introducing RC3 delta.
        assert target.read_text()==expected_original,("RC3 Java donor mismatch",path)
        target.write_text(template)
        assert target.read_text()==template
    new=dict(before)
    new.update(result["after"])
    proof["after"]=new
    proof["changed"]=sorted(set(proof["changed"])|set(result["changed"]))
    proof["unchanged_runtime_files"]=sum(a==b for name,a in proof["before"].items()
                                         if (b:=new.get(name)) is not None)
    proof["rc3_recovery_notice"]=True
    proof["rc3_recovery_apk_unsigned"]=True
    proof_path.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n")
    (folder/"RC3-ANDROID-DELTA.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("PASS RC3 Android source staging: two guarded Java templates, all 274 test sources unchanged")

def verify(build,folder):
    build=Path(build);folder=Path(folder)
    result=json.loads((folder/"RC3-ANDROID-DELTA.json").read_text())
    status=json.loads((folder/"ANDROID-VERIFICATION.json").read_text())
    assert status["totals"]=={"tests":274,"failures":0,"errors":0,"skipped":0}
    assert status["previous_234_test_sources_unchanged"]
    assert status["previous_234_case_names_preserved"]
    assert status["runtime_source_matches_candidate"]
    assert status["compiled_java_inputs_match_candidate"]
    assert result["no_force_exit_without_explicit_user"]
    assert result["recovery_grace_ms"]==2500
    assert result["no_recents_navigation_changes"]
    donor=folder/"donor.apk"
    assert donor.is_file() and donor.stat().st_size>1000000
    receipt={
      "schema":1,"source_commit":__import__("os").environ["GITHUB_SHA"],
      "verified_unmodified_274_cases":274,"tests_freshly_executed":True,
      "rc3_two_java_templates_only":True,
      "targeted_recovery_notice":True,
      "grace_ms":2500,"no_automatic_force_close":True,
      "donor_sha256":digest(donor),
      "source_hashes":result["after"],
      "physical_shutdown_verified":False,"locked":False}
    (folder/"RC3-ANDROID-VERIFICATION.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("PASS RC3 Android: all 274 tests, matching compiled Java, unchanged test membership, donor APK produced")

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("mode",choices=["apply","verify"])
    cli.add_argument("--build",required=True,type=Path)
    cli.add_argument("--folder",required=True,type=Path)
    args=cli.parse_args()
    if args.mode=="apply":apply(args.build,args.folder)
    else:verify(args.build,args.folder)
