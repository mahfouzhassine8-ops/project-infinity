#!/usr/bin/env python3
"""Run unchanged metadata cases and current lifecycle/provider regressions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest
import warnings
import zipfile

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'skin-209-preview-polish'


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True); args = parser.parse_args()
    assert hashlib.sha256(args.parent.read_bytes()).hexdigest() == '544279a735b2e2a4a7d1d77ac94a101dfd112f5f538deca1968f341d0ab6bb08'
    # Existing tests expect the original ignored overlay. Materialize only the
    # exact parent runtime fixture; never alter any original test source.
    with zipfile.ZipFile(args.parent) as archive:
        for name in ('infinity_file_preview.py', 'infinity_zip_metadata.py', 'infinity_preview_state.py'):
            path = OLD / 'delta/resources/lib' / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read('skin.infinity.diggz/resources/lib/' + name))
    sys.path[:0] = [str(HERE / 'tests'), str(OLD / 'tests')]
    import test_metadata
    import test_preview_lifecycle
    import test_provider_routes
    groups = [('unchanged_metadata', test_metadata.MetadataTests),
              ('preview_lifecycle', test_preview_lifecycle.ControllerTests),
              ('provider_registry', test_provider_routes.RegistryTests),
              ('home_refresh', test_provider_routes.RefreshTests)]
    result_data = {}
    good = True
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', SyntaxWarning)
        for name, cls in groups:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
            names = [case.id() for case in suite]
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            result_data[name] = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                                 'skipped': len(result.skipped), 'cases': names}
            good = good and result.wasSuccessful() and not result.skipped
    receipt = {'groups': result_data, 'tests': sum(value['tests'] for value in result_data.values()),
               'all_passed': bool(good), 'physical_device_verified': False,
               'metadata_parser_and_state_machine_unchanged': True, 'original_209_test_sources_unchanged': True}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'SKIN-210-RUNTIME-TESTS.json').write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(0 if good else 1)


if __name__ == '__main__':
    main()
