"""Prepare the pinned actual owner-v3 host overlay. No behavioral execution.

Only five intentionally changed existing classes and the exact BUILD-declared
helpers may replace/extend accepted431. All other host bytes stay exact431.
Independent canonical actual-DEX equality is required before translation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SIGNED_SOURCE = '9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
SIGNED_APK = '3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
BASE_DEX = {
    'classes.dex': '07b94bfde6dbc3e3a6bfc8436ea65e6a67bdef5ca868379809e20f2fb7ce8efb',
    'classes2.dex': '2e8fa1ae27e670db0525d31a655e93d861893fa20316d5c54a4c6283a97ca304',
    'classes3.dex': '7e18d8092de33a4d44e299305965e9b9eb943372a9643452f6f78afe209fb215',
    'classes4.dex': '9f82b0420b32ad8bdda7ef042e44bb975c8c01663f66506eaf33d22123f49b82',
    'classes5.dex': 'af03db41f53209de52f5d8609e411da49fee106d0fe544d6ea6e5d8230d88363',
}
ACCEPTED_COBRA_ZIP = '98583b7a935103c8d13744fc624a6005f0566b1e3d26a47f240295cafd21cae7'
BUILD_PIN = 'c71a792cc166f0e5c9f5cd83b8af83f85d1c6886f12ce9c85451da5b169cc970'
CANONICAL_PIN = '236000df80d6534d210659354b022e830d5e916e3d584f38920c724ab20ac192'
OWNER_DEX = {
    'part-0.dex': '7d27a7a73b78599f2fa08a3451b24be27ea2a4b4404b8666cf9862cb6bad0c46',
    'part-1.dex': '2cccda92792bc5a3827b0e5f15bd5c214b1ac9c1697988f2d762629de4dd12fa',
}
CHANGED = {
    'com/projectinfinity/kodi/InfinityLiveActivity.class',
    'com/projectinfinity/kodi/InfinityLiveActivity$CobraPosterChannelCard.class',
    'com/projectinfinity/kodi/InfinityCobraFeatureRuntime.class',
    'com/projectinfinity/kodi/CobraLogoRequests.class',
    'com/projectinfinity/kodi/CobraComponent.class',
}
HELPER_ROOTS = {
    'com/projectinfinity/kodi/CobraCardsLayout',
    'com/projectinfinity/kodi/CobraCardsTiles',
    'com/projectinfinity/kodi/CobraCardsReuse',
    'com/projectinfinity/kodi/CobraProfileDataReuse',
}
EXCLUDED = ('com/google/common/', 'com/google/thirdparty/')
NATIVE_DEPS = {
    'nativeruntime': ('4.14.1', 'nativeruntime-4.14.1.jar'),
    'nativeruntime-dist-compat': ('1.0.16', 'nativeruntime-dist-compat-1.0.16.jar'),
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def class_name(descriptor):
    assert descriptor.startswith('Lcom/projectinfinity/kodi/') and descriptor.endswith(';')
    return descriptor[1:-1] + '.class'


def read_classes(paths):
    result = {}
    for path in paths:
        with ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith('.class'):
                    assert name not in result, 'Duplicate translated class: ' + name
                    result[name] = archive.read(name)
    return result


def prepare(baseline, build, dex2jar, accepted_component, out):
    baseline = baseline.resolve()
    build = build.resolve()
    dex2jar = dex2jar.resolve()
    accepted_component = accepted_component.resolve()
    out = out.resolve()
    assert not out.exists(), 'Fresh output required; preserve prior preparation evidence'
    assert sha(build / 'BUILD.json') == BUILD_PIN, 'Owner build receipt changed'
    baseline_receipt = json.loads((baseline / 'INPUTS.json').read_text())
    receipt = json.loads((build / 'BUILD.json').read_text())
    assert baseline_receipt['source'] == receipt['baseline_signed_source'] == SIGNED_SOURCE
    assert baseline_receipt['APK_sha256'] == SIGNED_APK
    assert baseline_receipt['DEX_sha256'] == BASE_DEX and baseline_receipt['versionCode'] == 2103431
    assert receipt['status'] == 'COMPILED_UNSIGNED_COBRA_OWNER_ONLY' and receipt['APK'] == 'NOT_BUILT'
    assert {class_name(n) for n in receipt['changed_classes']} == CHANGED
    new_expected = {class_name(n) for n in receipt['new_classes']}
    assert len(new_expected) == len(receipt['new_classes']), 'Duplicate helper declaration'
    assert {n[:-6].split('$', 1)[0] for n in new_expected} == HELPER_ROOTS
    for name, pin in BASE_DEX.items():
        assert sha(baseline / name) == pin, name
    for name, pin in baseline_receipt['translated_jar_SHA256'].items():
        assert sha(baseline / (Path(name).stem + '-translated.jar')) == pin, name
    for name, pin in OWNER_DEX.items():
        assert sha(build / 'owner-dex/COBRA' / name) == pin, name
    compiler_sources = receipt['compiler_source_files']
    assert len(compiler_sources) == 20, 'Pinned v3 complete compiler-source manifest required'
    for name, pin in compiler_sources.items():
        source = (REPO / name).resolve()
        assert source.is_relative_to(REPO), 'Source manifest escaped repository'
        assert sha(source) == pin, 'Compiler source changed after owner build: ' + name
    helpers = receipt['helper_sources']
    assert len(helpers) == len(HELPER_ROOTS) == 4
    for name, pin in helpers.items():
        assert compiler_sources[name] == pin, 'Helper omitted/mismatched in compiler-source manifest'
        assert sha(REPO / name) == pin, 'Helper source changed after owner build: ' + name
    assert {'com/projectinfinity/kodi/' + Path(n).stem for n in helpers} == HELPER_ROOTS
    tool_pins = json.loads((REPO / 'repairs/cobra-next-from-2103427/cards-from-2103431/DEX2JAR-LIB-PINS.json').read_text())
    assert {p.name for p in (dex2jar / 'lib').glob('*.jar')} == set(tool_pins)
    for name, pin in tool_pins.items():
        assert sha(dex2jar / 'lib' / name) == pin, 'Translation tool changed: ' + name
    full_original = read_classes([baseline / 'classes4-translated.jar', baseline / 'classes5-translated.jar'])
    original = {n: raw for n, raw in full_original.items() if not n.startswith(EXCLUDED)}
    assert read_classes([baseline / 'production.jar']) == original, 'Baseline host production changed'
    support = {}
    for part in ('classes-translated.jar', 'classes2-translated.jar', 'classes3-translated.jar'):
        with ZipFile(baseline / part) as archive:
            for n in archive.namelist():
                if n.endswith('.class') and n.startswith(('com/projectinfinity/kodi/', 'androidx/')) and not n.startswith(EXCLUDED):
                    support.setdefault(n, archive.read(n))
    assert read_classes([baseline / 'support.jar']) == support, 'Baseline shared/Infinity support changed'

    canonical_file = build / 'INDEPENDENT-CANONICAL-RESULT.json'
    assert sha(canonical_file) == CANONICAL_PIN, 'Independent canonical proof changed'
    canonical = json.loads(canonical_file.read_text())
    assert canonical['status'] == 'PASS_EXACT_FIVE_CLASS_DELTA'
    assert canonical['baseline_signed_source'] == SIGNED_SOURCE
    assert canonical['new_DEX_sha256'] == OWNER_DEX
    assert canonical['build_receipt_sha256'] == BUILD_PIN
    assert canonical['compiler_source_files'] == compiler_sources
    assert {class_name(n) for n in canonical['changed_existing_classes']} == CHANGED
    assert {class_name(n) for n in canonical['new_classes']} == new_expected
    assert not canonical['missing_classes']
    assert sha(accepted_component) == ACCEPTED_COBRA_ZIP
    with ZipFile(accepted_component) as archive:
        metadata_raw = archive.read('component.json')
        component = json.loads(metadata_raw)
        assert component['owner'] == 'COBRA' and component['version'] == '2103431.cobra.1'
        assert component['dex'] == {'dex/part-0.dex': BASE_DEX['classes4.dex'], 'dex/part-1.dex': BASE_DEX['classes5.dex']}
        for n, pin in component['dex'].items():
            assert digest(archive.read(n)) == pin
    accepted_hashes = {k[6:]: v['sha256'] for k, v in component['payload'].items() if k.startswith('class:')}
    actual_hashes = {}
    for part in ('part-0', 'part-1'):
        root = build / 'independent-canonical' / part
        assert root.is_dir()
        for path in sorted(root.rglob('*.smali')):
            descriptor = 'L' + path.relative_to(root).as_posix()[:-6] + ';'
            assert descriptor not in actual_hashes, 'Duplicate canonical class'
            actual_hashes[descriptor] = sha(path)
    canonical_changed = {n for n in accepted_hashes if actual_hashes.get(n) != accepted_hashes[n]}
    canonical_new = set(actual_hashes) - set(accepted_hashes)
    assert len(accepted_hashes) == len(full_original) == canonical['baseline_existing_classes'] == 7142
    assert len(actual_hashes) == len(accepted_hashes) + len(new_expected)
    assert {class_name(n) for n in canonical_changed} == CHANGED
    assert {class_name(n) for n in canonical_new} == new_expected
    assert set(accepted_hashes) <= set(actual_hashes)
    assert canonical['unchanged_existing_classes'] == len(accepted_hashes) - len(CHANGED) == 7137

    out.mkdir(parents=True)
    binding = {
        'status': 'PREPARING_ACTUAL_OWNER_DEX_CLASSPATH',
        'phase': 'UNSIGNED_COBRA_OWNER_PROTOTYPE_V3_NO_APK',
        'baseline_signed_source': SIGNED_SOURCE, 'baseline_APK_sha256': SIGNED_APK,
        'baseline_DEX_sha256': BASE_DEX, 'owner_DEX_sha256': OWNER_DEX,
        'owner_BUILD_sha256': BUILD_PIN, 'owner_BUILD': receipt,
        'compiler_source_files': compiler_sources, 'helper_source_sha256': helpers,
        'allowed_changed_existing_classes': sorted(CHANGED),
        'expected_new_helper_classes': sorted(new_expected),
        'canonical_chain': {
            'independent_proof_sha256': CANONICAL_PIN, 'accepted_COBRA_ZIP_sha256': ACCEPTED_COBRA_ZIP,
            'accepted_component_metadata_sha256': digest(metadata_raw),
            'canonical_existing_classes_checked': len(accepted_hashes),
            'canonical_unchanged_existing_classes': 7137, 'canonical_new_helpers': len(new_expected),
            'proof': 'Pinned actual DEX independently disassembled by root; every unselected canonical class rechecked against exact accepted431 component metadata',
        },
        'translation_tool_lib_sha256': tool_pins,
        'behavioral_execution': 'NOT_RUN', 'application_APK': 'NOT_BUILT_OR_MODIFIED',
        'CI': 'NOT_RUN', 'physical_Fold': 'NOT_RUN', 'shutdown': 'NOT_RUN',
    }

    def save():
        (out / 'SOURCE-BINDINGS.json').write_text(json.dumps(binding, indent=2) + '\n')

    save()
    shutil.copyfile(build / 'BUILD.json', out / 'OWNER-BUILD.json')
    shutil.copyfile(canonical_file, out / canonical_file.name)
    try:
        errors = out / 'translation-errors'
        errors.mkdir()
        translated = []
        for name in OWNER_DEX:
            target = out / (Path(name).stem + '-translated.jar')
            translated.append(target)
            command = ['java', '-cp', str(dex2jar / 'lib/*'), 'com.googlecode.dex2jar.tools.Dex2jarCmd',
                       str(build / 'owner-dex/COBRA' / name), '-o', str(target), '-e', str(errors / (name + '.zip'))]
            with (out / (Path(name).stem + '-D2J.txt')).open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            assert result.returncode == 0, 'Actual DEX translation failed: ' + name
        assert not list(errors.iterdir()), 'Actual owner translation error archive refused'
        actual = read_classes(translated)
        new_detected = set(actual) - set(full_original)
        missing = set(full_original) - set(actual)
        changed_translation = sorted(n for n in full_original if n in actual and full_original[n] != actual[n])
        drift = sorted(set(changed_translation) - CHANGED)
        assert not missing, 'Existing class disappeared from actual owner DEX translation'
        assert new_detected == new_expected, 'Unexpected translated helper classes'
        assert CHANGED <= set(changed_translation), 'Selected existing class missing production change'
        diff = {
            'baseline_class_count': len(full_original), 'actual_translated_class_count': len(actual),
            'changed_existing_translated_classes': changed_translation,
            'unselected_translation_differences_EXCLUDED': drift,
            'class_sha256': {n: {'accepted431': digest(full_original[n]), 'owner_v3': digest(actual[n])} for n in changed_translation},
            'policy': 'Canonical actual DEX proof passed; overlay only five selected existing classes and exact BUILD-declared helpers. Unselected translated bytes are excluded.',
        }
        (out / 'EXCLUDED-TRANSLATION-DRIFT.json').write_text(json.dumps(diff, indent=2) + '\n')
        merged = dict(original)
        for n in CHANGED | new_expected:
            merged[n] = actual[n]
        assert {n for n in original if merged[n] != original[n]} == CHANGED
        assert set(merged) == set(original) | new_expected
        assert all(merged[n] == original[n] for n in original if n not in CHANGED)
        with ZipFile(out / 'production.jar', 'w', ZIP_DEFLATED) as archive:
            for n in sorted(merged):
                info = ZipInfo(n, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, merged[n])
        assert read_classes([out / 'production.jar']) == merged
        shutil.copyfile(baseline / 'support.jar', out / 'support.jar')
        assert sha(out / 'support.jar') == sha(baseline / 'support.jar')
        shutil.copytree(baseline / 'android-test-libs', out / 'android-test-libs')
        native = {}
        for artifact, (version, name) in NATIVE_DEPS.items():
            jar = Path.home() / '.m2/repository/org/robolectric' / artifact / version / name
            assert jar.is_file(), 'Cached official native dependency missing: ' + artifact
            native[artifact] = {'version': version, 'jar_sha256': sha(jar), 'scope': 'host test dependency; no APK inclusion'}
        pom = (baseline / 'pom.xml').read_text().replace(str(baseline), str(out))
        deps = ''.join('<dependency><groupId>org.robolectric</groupId><artifactId>' + a + '</artifactId><version>' + v + '</version><scope>test</scope></dependency>' for a, (v, _) in NATIVE_DEPS.items())
        pom = pom.replace('</dependencies>', deps + '</dependencies>').replace('projection.output', 'integrated.output')
        (out / 'pom.xml').write_text(pom)
        (out / 'src/test/java/com/projectinfinity/kodi').mkdir(parents=True)
        fixtures = out / 'fixtures-not-selected'
        fixtures.mkdir()
        fixture = HERE.parent / 'settings-return/CobraSettingsReturnBaselineTest.java'
        shutil.copyfile(fixture, fixtures / fixture.name)
        hashes = {n: digest(merged[n]) for n in sorted(CHANGED | new_expected)}
        (out / 'HOST-OVERLAY-CLASS-HASHES.json').write_text(json.dumps(hashes, indent=2) + '\n')
        (out / 'ACTUAL-CANONICAL-CLASS-HASHES.json').write_text(json.dumps(actual_hashes, sort_keys=True, indent=2) + '\n')
        binding.update(
            status='PASS_CANONICAL_BOUND_EXACT_FIVE_CLASS_OVERLAY_PREPARED_NO_TESTS',
            changed_existing_classes=sorted(CHANGED), new_helper_classes=sorted(new_expected),
            unchanged_baseline_host_class_count=len(original) - len(CHANGED),
            unchanged_full_owner_canonical_class_count=len(full_original) - len(CHANGED),
            unselected_translated_differences_excluded=len(drift),
            production_jar_sha256=sha(out / 'production.jar'), support_jar_sha256=sha(out / 'support.jar'),
            translated_owner_jar_sha256={p.name: sha(p) for p in translated},
            host_overlay_class_hash_inventory_sha256=sha(out / 'HOST-OVERLAY-CLASS-HASHES.json'),
            canonical_class_hash_inventory_sha256=sha(out / 'ACTUAL-CANONICAL-CLASS-HASHES.json'),
            excluded_translation_drift_inventory_sha256=sha(out / 'EXCLUDED-TRANSLATION-DRIFT.json'),
            native_graphics_dependencies=native, pom_sha256=sha(out / 'pom.xml'),
            fixture_source={'path': str(fixture), 'sha256': sha(fixture), 'copied_to': 'fixtures-not-selected/' + fixture.name, 'execution': 'NOT_SELECTED_OR_RUN'},
            prepare_source_sha256=sha(Path(__file__)),
        )
        save()
        print(json.dumps({k: v for k, v in binding.items() if k != 'owner_BUILD'}, indent=2))
    except Exception as failure:
        binding.update(status='FAILED_CLOSED_ACTUAL_DEX_PREPARATION', error=str(failure))
        save()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'build', 'dex2jar', 'accepted-component', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    prepare(**vars(parser.parse_args()))
