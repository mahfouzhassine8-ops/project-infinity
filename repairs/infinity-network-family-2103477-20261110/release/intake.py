"""Pinned original-workflow artifact admission; no build, signing or app execution."""
from pathlib import Path
import argparse
import importlib.util
import json
import subprocess
import prepare_modules as prep


def one(root, pattern):
    paths = list(root.rglob(pattern))
    assert len(paths) == 1, (pattern, paths)
    return paths[0]


def intake(out):
    assert not out.exists()
    t = prep.tools()
    helper = prep.ROOT/'repairs/infinity-tracking-integration-2103469-20261108/tracking_module_fixture.py'
    assert prep.sha(helper.read_bytes()) == 'af14da368c555a5d9d0862aa1c1f490bfcf64d389026cb82092261d39ce3ecdb'
    spec = importlib.util.spec_from_file_location('retained_verified_artifact_download',helper)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    pins = json.loads((prep.HERE/'INPUT-ARTIFACTS.json').read_text())
    roots = {label:module.download(row,out/label) for label,row in pins.items()}
    apk = one(roots['signed77'],'Infinity-2103477-Combined-Original-Signer.apk')
    engine = one(roots['native'],'libkodi.so')
    components = one(roots['components75'],'components/catalog.json').parent
    fixture = one(roots['modules'],'network-module-prepared/PREPARATION.json').parent.parent
    native_map = one(roots['native'],'NATIVE-SOURCE-MAP.json')
    assert prep.sha(native_map.read_bytes()) == '292d4d2057d00447a5a8ce3a7da8fb3f5dddc9a228f7ddacee6f227044c28f71'
    compiled = json.loads(native_map.read_text())
    current = json.loads((prep.TASK/'SOURCE-PINS.json').read_text())
    assert all(compiled[name] == digest for name,digest in current['native'].items())
    record = dict(status='PASS_PINNED_OFFICIAL_ARTIFACTS_ONLY', artifacts=pins,
                  apk=str(apk.resolve()), native=str(engine.resolve()),
                  components=str(components.resolve()), module_fixture=str(fixture.resolve()),
                  source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=prep.ROOT,text=True).strip(),
                  original_download_helper_sha256=prep.sha(helper.read_bytes()),
                  original_tools=t.pins, native_map_sha256=prep.sha(native_map.read_bytes()),
                  APK_signing=False, registry_mutation=False, Android='NOT_RUN')
    prep.save(out/'INTAKE.json',record)
    print('PASS official signed77, retained ARM64 engine, original-signed modules and ownership-only75 component input admission')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    intake(p.parse_args().out)
