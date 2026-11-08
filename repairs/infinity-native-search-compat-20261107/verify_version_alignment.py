"""Strict source-only preflight against exact already authenticated Infinity 2103464.

Produces evidence, NOT a ZIP or APK installer. The original permanent signer
must sign the newly generated complete manifest in an authorized release job.
"""
import ast
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[2]
PLAN=json.loads((Path(__file__).parent/'VERSION-ALIGNMENT.json').read_text())
SIGNED=PLAN["baseline"]
HERE=ROOT/'repairs/infinity-only-performance-2103425/overlay/script.infinity.commandcenter'
sys.path.insert(0,str(ROOT/'repairs/infinity-final-closure-2103407'))
import module_bundle

def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def check(value,message):
    if not value:raise RuntimeError("VERSION_ALIGNMENT_REFUSAL: "+message)

def verify(prepared_zip,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    check(SIGNED["apk_versionCode"]==PLAN["target"]["apk_versionCode"]==2103464,"Wrong APK version")
    check(SIGNED["command_center_version"]==PLAN["target"]["command_center_version"]=="0.3.5.62","Wrong CC base")
    check(SIGNED["skin_version"]==PLAN["target"]["skin_version"]=="1.0.5.270","Wrong skin")
    check(PLAN["recovery"]["apk_versionCode"]==2103465,"Wrong recovery APK")
    check(PLAN["recovery"]["command_center_version"]=="0.3.5.63","Wrong recovery CC")
    check(PLAN["recovery"]["skin_version"]=="1.0.5.271","Wrong recovery skin")
    check(PLAN["recovery"]["remains_original_key_signed_and_unmodified"],"Recovery changed")
    with tempfile.TemporaryDirectory(prefix="infinity-cc62-source-only-") as t:
        t=Path(t)
        inner_file=t/"exact464-infinity-owner.zip"
        if Path(prepared_zip).is_dir():
            metadata=json.loads((prepared_zip/"PREPARATION.json").read_text())
            shutil.copyfile(prepared_zip/"components/INFINITY.zip",inner_file)
        else:
            with ZipFile(prepared_zip) as outer:
                metadata=json.loads(outer.read("PREPARATION.json"))
                with outer.open("components/INFINITY.zip") as stream,inner_file.open("wb") as dst:
                    shutil.copyfileobj(stream,dst)
        check(metadata["status"]=="PASS_EXACT462_AND_AUTHENTICATED_CURRENT_COMPONENT_CONSOLIDATION","Invalid prepared source")
        for field,expected in [("versionCode",2103464),("CC","0.3.5.62"),("skin","1.0.5.270"),("run_id",SIGNED["prepared_run"])]:
            check(metadata[field]==expected,"Prepared "+field+" mismatch")
        roots=t/"source"
        roots.mkdir()
        prefix="payload/assets/addons/"
        with ZipFile(inner_file) as inside:
            for name in inside.namelist():
                if not name.startswith(prefix) or name.endswith("/"):continue
                rel=name[len(prefix):]
                if rel.split("/",1)[0] not in module_bundle.IDS:continue
                dest=roots/rel
                check(".." not in dest.relative_to(roots).parts,"Invalid owned member")
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(inside.read(name))
            check(hashlib.sha256(inside.read(prefix+'script.infinity.commandcenter/addon.xml')).hexdigest()==SIGNED["command_center_baseline_files"]["addon.xml"],"CC62 addon.xml mismatch")
            skin=ElementTree.fromstring(inside.read(prefix+'skin.infinity.diggz/addon.xml'))
            check(skin.get("version")=="1.0.5.270","Prepared actual skin mismatch")
        cc=roots/module_bundle.CC
        original=cc/module_bundle.MANIFEST
        signed_manifest=original.read_bytes()
        check(sha_bytes(signed_manifest)==SIGNED["command_center_baseline_files"]["INFINITY-MODULES.v1"],"Wrong original signed manifest")
        actual,old_files=module_bundle.build(roots)
        check(actual==signed_manifest,"Official builder fails to reproduce signed original CC62")
        check(len(old_files)==SIGNED["original_manifest_source_file_count"]==78,"Original manifest inventory mismatch")
        for file,want in SIGNED["command_center_baseline_files"].items():
            check(sha_bytes((cc/file).read_bytes())==want,"Prepared "+file+" mismatch")
        source_file=HERE/"provider_inventory.py"
        helper_file=HERE/"native_search_compatibility.py"
        source=source_file.read_bytes()
        old=(cc/"provider_inventory.py").read_bytes()
        start=source.find(b"    if not operations and addon_id in ('plugin.video.umbrella', 'plugin.video.pov'):\n")
        check(start>=0,"Missing scoped Umbrella/POV admission")
        end=source.find(b"    if not operations:\n        operations = _automatic_search",start)
        check(end>start,"Unclear end of sole scoped change")
        check(source[:start]+source[end:]==old,"Unexpected modification in existing signed provider_inventory.py")
        ast.parse(source)
        ast.parse(helper_file.read_bytes())
        (cc/"provider_inventory.py").write_bytes(source)
        (cc/"native_search_compatibility.py").write_bytes(helper_file.read_bytes())
        new,files=module_bundle.build(roots)
        check(len(files)==79 and new!=signed_manifest,"New signed source inventory is incorrect")
        check(new.splitlines()[:3]==signed_manifest.splitlines()[:3],"CC/protocol version changed")
        check(files[module_bundle.CC+"/native_search_compatibility.py"]==helper_file.read_bytes(),"Helper differs")
        # Distinguish source inputs from the signer-owned signature. A ZIP with
        # the old .sig would be unusable and must never be offered to install.
        check((cc/(module_bundle.MANIFEST+".sig")).is_file(),"Missing original signature reference")
        differences=[name for name in files if name not in old_files or files[name]!=old_files[name]]
        check(set(differences)=={
            "script.infinity.commandcenter/provider_inventory.py",
            "script.infinity.commandcenter/native_search_compatibility.py"
        },"Unapproved source changed:"+str(differences))
        result=dict(
            status="PASS_EXACT_464_CC62_SAME_VERSION_SOURCE_SIGNABILITY_ONLY",
            baseline_apk=2103464,baseline_cc="0.3.5.62",skin_unchanged="1.0.5.270",
            forward_recovery_apk=2103465,forward_recovery_cc="0.3.5.63",
            forward_recovery_skin="1.0.5.271",
            original_signed_manifest_sha256=sha_bytes(signed_manifest),
            new_unsigned_manifest_sha256=sha_bytes(new),
            baseline_signed_source_records=78,proposed_signed_source_records=79,
            allowed_changed_source_files=differences,
            unchanged_original_source_records=77,
            original_certificate=SIGNED["certificate_sha256"],
            unchanged_apk=True,unchanged_skin=True,
            unchanged_other_first_party_modules=True,unchanged_providers=True,
            changes_to_original_signing_system=False,
            original_key_new_signature="REQUIRED_NOT_PRODUCED",
            installable_zip=False,public_release=False,
            Android17="NOT_RUN",physical_Fold="NOT_RUN")
        (out/"EXACT-VERSION-ALIGNMENT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print("PASS exact prepared signed464; CC62 patch, skin270 unchanged; recovery465 CC63; no unverified ZIP")
        return result
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--prepared",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    verify(a.prepared,a.out)
