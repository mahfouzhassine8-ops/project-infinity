"""Retained authenticated artifact intake; original75 is ownership metadata only."""
import argparse
import importlib.util
from pathlib import Path
import prepare_modules as prep

def intake(out):
    assert not out.exists();prep.tools()
    helper=prep.ROOT/'repairs/infinity-tracking-integration-2103469-20261108/tracking_module_fixture.py'
    assert prep.sha(helper.read_bytes())=='af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb'
    spec=importlib.util.spec_from_file_location('retained_artifact_intake',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    import json
    pins=json.loads((prep.HERE/'INPUT-ARTIFACTS.json').read_text())
    roots={label:m.download(row,out/label) for label,row in pins.items()}
    def one(root,pattern):
        found=list(root.rglob(pattern));assert len(found)==1,(pattern,len(found));return found[0]
    apk=one(roots['signed77'],'Infinity-2103477-Combined-Original-Signer.apk');assert prep.sha(apk.read_bytes())==prep.BASE_APK
    components=one(roots['ownership75'],'catalog.json').parent
    modules=one(roots['modules'],'performance-module-prepared/PREPARATION.json').parent.parent
    prep.save(out/'INTAKE.json',dict(status='PASS_PINNED_ORIGINAL_WORKFLOW_ARTIFACTS',apk=str(apk.resolve()),components=str(components.resolve()),module_fixture=str(modules.resolve()),artifacts=pins,APK_signing=False,registry_mutation=False,ownership75_payload_source=False,networking_inputs=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);intake(p.parse_args().out)
