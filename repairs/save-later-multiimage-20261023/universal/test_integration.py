"""Selected CC34 staging, original-release preservation and source admission checks.

No Kodi application, shutdown, checkpoint or device scenario is executed.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPAIR = HERE.parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def run(source, reference, native_reference, contracts, out):
    component = module('universal_component_contract', REPAIR / 'component_contract.py')
    owner = module('universal_owner_binding', REPAIR / 'owner_binding.py')
    baseline = json.loads((HERE / 'BASE33-CONTROLLER-PINS.json').read_text())
    cc = 'script.infinity.commandcenter'
    for name, pin in baseline.items():
        assert sha((reference / cc / name).read_bytes()) == pin, name
    assert len(baseline) == 19
    required = set(baseline) | component.NEW_CONTROLLER_FILES
    assert len(required) == 24
    with tempfile.TemporaryDirectory(prefix='infinity-universal-integration-') as temp:
        temp = Path(temp)
        overlay = temp / 'overlay'
        ledger = component.stage(source, overlay, contracts)
        final = temp / 'final'
        shutil.copytree(source, final)
        shutil.copytree(overlay, final, dirs_exist_ok=True)
        pins = json.loads((final / 'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
        assert set(pins) == required
        assert pins == json.loads((final / 'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json').read_text())
        assert pins == {name: sha((final / cc / name).read_bytes()) for name in required}
        for addon, (_, version) in component.VERSIONS.items():
            assert ET.parse(final / addon / 'addon.xml').getroot().get('version') == version
        overlay_names = set(json.loads((HERE / 'OVERLAY-PREIMAGES.json').read_text()))
        generated = {addon + '/addon.xml' for addon in component.VERSIONS} | {
            cc + '/checkpoint_runtime.py', cc + '/infinity_trakt.py',
            'script.infinity.watchedbridge/controller.py',
            'script.infinity.watchedbridge/CONTROLLER-PREIMAGES.json',
            'script.infinity.uirepair/CONTROLLER-PREIMAGES.json'}
        allowed = overlay_names | generated
        preserved = 0
        for path in reference.rglob('*'):
            if not path.is_file():
                continue
            name = path.relative_to(reference).as_posix()
            if name.split('/')[0] not in component.VERSIONS:
                continue
            if name not in allowed:
                assert path.read_bytes() == (final / name).read_bytes(), 'Protected reference changed: ' + name
                preserved += 1
        old_navigation = (reference / cc / 'saved_navigation.py').read_text()
        new_navigation = (final / cc / 'saved_navigation.py').read_text()
        def without_available(text):
            tree = ast.parse(text)
            target = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'available')
            lines = text.splitlines(keepends=True)
            return ''.join(lines[:target.lineno-1] + lines[target.end_lineno:])
        assert without_available(old_navigation) == without_available(new_navigation)
        # Execute the real production verifier without importing unrelated Kodi
        # application modules. Every admitted source gets a negative control.
        tree = ast.parse((final / 'script.infinity.watchedbridge/controller.py').read_text())
        nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and
                 node.name in ('UnsupportedController', 'verify')]
        ns = {'hashlib': hashlib, 'json': json, 'Path': Path, 'ET': ET,
              '__file__': str(final / 'script.infinity.watchedbridge/controller.py')}
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), 'controller.verify', 'exec'), ns)
        assert ns['verify'](final / cc) == (final / cc).resolve()
        for name in sorted(required):
            path = final / cc / name
            original = path.read_bytes()
            path.write_bytes(original + b'\n')
            try:
                ns['verify'](final / cc)
            except ns['UnsupportedController']:
                pass
            else:
                raise AssertionError('Tampered source admitted: ' + name)
            finally:
                path.write_bytes(original)
        trakt = ast.parse((final / cc / 'infinity_trakt.py').read_text())
        binding = next(node for node in trakt.body if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Name) and target.id == 'BRIDGE_PINS' for target in node.targets))
        bridge = ast.literal_eval(binding.value)
        assert all(sha((final / 'script.infinity.watchedbridge' / name).read_bytes()) == pin
                   for name, pin in bridge.items())
        # Recover the literal pre-CC31 input from its exact signed reference by
        # removing only the old appended admissions, then require original SHA.
        native = temp / 'native'
        for name in owner.BEFORE:
            raw = (native_reference / name).read_bytes()
            if name == owner.CONTRACT:
                start = raw.index(b'    // INFINITY_2103401_SAVED_NAVIGATION_CC31_CC32_CC33_EXACT_SOURCES\n')
                end = raw.index(b'  };\n  return *contracts;', start)
                raw = raw[:start] + raw[end:]
            else:
                for version in ('0.3.5.31', '0.3.5.32', '0.3.5.33'):
                    part = (' && active["addon_version"].asString() != "' + version + '"').encode()
                    assert raw.count(part) == 1
                    raw = raw.replace(part, b'', 1)
            assert sha(raw) == owner.BEFORE[name], 'Original native source recovery mismatch: ' + name
            path = native / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        native_output = temp / 'native-overlay'
        native_ledger = owner.bind(native, source, final, native_output)
        assert set(native_ledger) == set(owner.BEFORE)
        text = (native_output / owner.CONTRACT).read_text()
        start = text.index('    // INFINITY_2103401_SAVED_NAVIGATION_CC31_CC32_CC33_CC34_EXACT_SOURCES\n')
        end = text.index('  };\n  return *contracts;', start)
        assert (text[:start] + text[end:]).encode() == (native / owner.CONTRACT).read_bytes()
        for inventory in (json.loads((REPAIR / 'tracking/PARENT-CONTROLLER-PINS.json').read_text()),
                          json.loads((REPAIR / 'tracking/final-eight/BASE32-CONTROLLER-PINS.json').read_text()), baseline, pins):
            block = ''.join('      {"' + cc + '/' + name + '", "' + pin + '"},\n'
                            for name, pin in sorted(inventory.items()))
            assert text[start:end].count(block) == 4
    report = {'host': 'PASS', 'source': 'actual staged production modules; no Kodi runtime',
              'CC33_original_inventory_retained': True, 'CC34_named_source_count': 24,
              'individual_tamper_rejections': 24, 'reference_files_byte_preserved': preserved,
              'TrackIt_non_discovery_source_byte_identical': True, 'reciprocal_bridge_UI_pins': True,
              'prior_native_contracts_byte_identical': True,
              'versions': {addon: versions[1] for addon, versions in component.VERSIONS.items()},
              'android': 'NOT RUN', 'physical_fold': 'NOT RUN', 'shutdown': 'NOT RUN; independent'}
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--native-reference', type=Path, required=True)
    parser.add_argument('--contracts', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.reference, args.native_reference, args.contracts, args.out), indent=2))
