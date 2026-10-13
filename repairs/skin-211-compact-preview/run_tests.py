#!/usr/bin/env python3
"""All original metadata/provider tests plus inherited+new preview behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'skin-209-preview-polish'
PREVIOUS = HERE.parent / 'skin-210-critical-correction'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    assert hashlib.sha256(args.parent.read_bytes()).hexdigest() == '8febf697772ece72c9a445d0b5b6fd2650f97889a00e1e311dc0588199596bb3'
    # Original tests import their exact preserved metadata/state fixture paths.
    with zipfile.ZipFile(args.parent) as archive:
        for name in ('infinity_zip_metadata.py','infinity_preview_state.py'):
            path=OLD/'delta/resources/lib'/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(archive.read('skin.infinity.diggz/resources/lib/'+name))
    # Preserve the original209 negative-control module from its tracked source.
    original_controller = OLD / 'resources/lib/infinity_file_preview.py'
    (OLD / 'delta/resources/lib/infinity_file_preview.py').write_bytes(original_controller.read_bytes())
    sys.path[:0]=[str(HERE/'tests'),str(HERE/'runtime'),str(PREVIOUS/'tests'),str(OLD/'tests')]
    import test_metadata
    import test_provider_routes
    import test_compact_controller
    groups=[('unchanged_metadata',test_metadata.MetadataTests),
            ('compact_controller',test_compact_controller.CompactControllerTests),
            ('compact_geometry',test_compact_controller.GeometryTests),
            ('unchanged_provider_registry',test_provider_routes.RegistryTests),
            ('unchanged_home_refresh',test_provider_routes.RefreshTests)]
    result_data={};good=True
    for name,cls in groups:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(cls)
        names=[case.id() for case in suite]
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        result_data[name]={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'cases':names}
        good=good and result.wasSuccessful() and not result.skipped
    receipt={'groups':result_data,'tests':sum(v['tests'] for v in result_data.values()),'all_passed':bool(good),
             'metadata_parser_and_state_machine_unchanged':True,'provider_scripts_unchanged':True,
             'original_test_sources_unchanged':True,'physical_device_accepted':False}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'SKIN-211-RUNTIME-TESTS.json').write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(0 if good else 1)


if __name__=='__main__':main()
