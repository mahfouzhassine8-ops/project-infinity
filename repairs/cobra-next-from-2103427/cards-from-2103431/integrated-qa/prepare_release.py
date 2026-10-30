"""Fresh CI host-classpath preparation for the coordinated Cobra434 candidate.

This performs source/canonical/translation verification only. It cannot register,
sign, install, accept, lock or promote a release, and runs no behavioral tests.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
OWNER = HERE.parent
REPO = OWNER.parents[2]
BRANCH = 'work/cobra-only-from-2103427-20261028'
REPOSITORY = 'mahfouzhassine8-ops/project-infinity'
SIGNED_SOURCE = '9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
SIGNED_APK = '3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
VERSION = 2103435
GENERATION = 20  # Target only; registration follows successful producer evidence.
BASE_DEX = {
    'classes.dex': '07b94bfde6dbc3e3a6bfc8436ea65e6a67bdef5ca868379809e20f2fb7ce8efb',
    'classes2.dex': '2e8fa1ae27e670db0525d31a655e93d861893fa20316d5c54a4c6283a97ca304',
    'classes3.dex': '7e18d8092de33a4d44e299305965e9b9eb943372a9643452f6f78afe209fb215',
    'classes4.dex': '9f82b0420b32ad8bdda7ef042e44bb975c8c01663f66506eaf33d22123f49b82',
    'classes5.dex': 'af03db41f53209de52f5d8609e411da49fee106d0fe544d6ea6e5d8230d88363',
}
BASE_COMPONENTS = {
    'CHOOSER_SHELL.zip': '36ca822a886b5df4443c798c933a2c304a30be002c10b4284f6b2ed7934fe912',
    'MINIMAL_ANDROID_CONTRACT.zip': '432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8',
    'INFINITY.zip': '16eeb91a24bf0cf99d558d9e3dd17aedfd127e9a1936dcce413341c48683cd6c',
    'COBRA.zip': '98583b7a935103c8d13744fc624a6005f0566b1e3d26a47f240295cafd21cae7',
}
CHANGED = {
    'com/projectinfinity/kodi/InfinityLiveActivity.class',
    'com/projectinfinity/kodi/InfinityLiveActivity$CobraPosterChannelCard.class',
    'com/projectinfinity/kodi/InfinityCobraFeatureRuntime.class',
    'com/projectinfinity/kodi/CobraLogoRequests.class',
    'com/projectinfinity/kodi/CobraComponent.class',
}
HELPER_PATHS = {
    'runtime/CobraCardsLayout.java', 'runtime/CobraCardsTiles.java',
    'profile-reads/runtime/CobraProfileDataReuse.java', 'cards-reuse/runtime/CobraCardsReuse.java',
}
HELPER_ROOTS = {'com/projectinfinity/kodi/' + Path(n).stem for n in HELPER_PATHS}
EXPECTED_COMPILER_FILES = {
    'BASELINE.json', 'CARDS-SOURCE-BUDGET.json', 'DEX2JAR-LIB-PINS.json',
    'PROJECTION-SOURCE-BUDGET.json', 'SCOPE.json', 'build.py', 'cards_patch.py',
    'projection_patch.py', 'presentation_patch.py', 'logo-clear/patch.py',
    'logo-clear/SOURCE-BUDGET.json', 'profile-reads/patch_feature.py',
    'profile-reads/SOURCE-BUDGET.json', 'profile-reads/runtime/CobraProfileDataReuse.java',
    'cards-reuse/patch.py', 'cards-reuse/SOURCE-BUDGET.json',
    'cards-reuse/runtime/CobraCardsReuse.java', 'runtime/CobraCardsLayout.java',
    'runtime/CobraCardsTiles.java', 'fullscreen-more/patch.py',
    'fullscreen-more/SOURCE-BUDGET.json', 'fullscreen-more/rejected434/SCOPE.json',
}
EXPECTED_COMPILER_PATHS = {str((OWNER / n).relative_to(REPO)) for n in EXPECTED_COMPILER_FILES} | {
    'repairs/dual-experience-isolation-2103420/ModuleDexWriter.java'}
EXCLUDED = ('com/google/common/', 'com/google/thirdparty/')
NATIVE_DEPS = {
    'nativeruntime': ('4.14.1', 'c07b66d315aec3272a7c64aa5f154b4194be2cc6030a733d16f2ee87330232a8'),
    'nativeruntime-dist-compat': ('1.0.16', '2f4e879b00eed634d0e43353ecff80db4d5ce24b3b213d1e6053cb21b0ced10f'),
}
NAMESPACE = 'http://maven.apache.org/POM/4.0.0'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def descriptor_class(descriptor):
    require(descriptor.startswith('Lcom/projectinfinity/kodi/') and descriptor.endswith(';'), 'COBRA_CLASS_DESCRIPTOR')
    return descriptor[1:-1] + '.class'


def read_classes(paths):
    result = {}
    for path in paths:
        with ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith('.class'):
                    require(name not in result, 'DUPLICATE_TRANSLATED_CLASS:' + name)
                    result[name] = archive.read(name)
    return result


def canonical_classes(folder):
    result = {}
    for path in folder.rglob('*.smali'):
        raw = path.read_text()
        name = raw.splitlines()[0].split()[-1]
        require(name not in result, 'DUPLICATE_CANONICAL_CLASS:' + name)
        result[name] = raw
    return result


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def committed(path, source):
    relative = path.resolve().relative_to(REPO).as_posix()
    expected = subprocess.check_output(['git', '-C', str(REPO), 'show', source + ':' + relative])
    require(expected == path.read_bytes(), 'EXACT_COMMITTED_SOURCE:' + relative)
    return digest(expected)


def portable_pom(baseline, out):
    """Use Maven's repository resolution; no developer-home/offline SDK paths."""
    ET.register_namespace('', NAMESPACE)
    q = lambda name: '{' + NAMESPACE + '}' + name
    root = ET.fromstring((baseline / 'pom.xml').read_text())
    systems = root.findall('.//' + q('systemPath'))
    require(len(systems) == 2, 'TWO_HOST_SYSTEM_JARS_REQUIRED')
    expected = {str(baseline / 'production.jar'): '${project.basedir}/production.jar',
                str(baseline / 'support.jar'): '${project.basedir}/support.jar'}
    require({node.text for node in systems} == set(expected), 'BASELINE_POM_HOST_BINDING')
    for node in systems:
        node.text = expected[node.text]
    for properties in root.findall('.//' + q('systemPropertyVariables')):
        for node in list(properties):
            name = node.tag.rsplit('}', 1)[-1]
            if name in {'robolectric.offline', 'robolectric.dependency.dir', 'projection.output', 'integrated.output'}:
                properties.remove(node)
        ET.SubElement(properties, q('integrated.output')).text = '${project.basedir}/measurements'
    classpath = root.findall('.//' + q('additionalClasspathElement'))
    require(len(classpath) == 2, 'TWO_ANDROID_TEST_LIBRARIES_REQUIRED')
    require({Path(node.text).name for node in classpath} == {'monitor.jar', 'espresso.jar'}, 'ANDROID_TEST_LIBRARY_NAMES')
    for node in classpath:
        node.text = '${project.basedir}/android-test-libs/' + Path(node.text).name
    dependencies = root.find(q('dependencies'))
    require(dependencies is not None, 'MAVEN_DEPENDENCIES_REQUIRED')
    for artifact, (version, _) in NATIVE_DEPS.items():
        found = [node for node in dependencies if node.findtext(q('groupId')) == 'org.robolectric'
                 and node.findtext(q('artifactId')) == artifact]
        require(not found, 'UNEXPECTED_PREEXISTING_NATIVE_DEPENDENCY:' + artifact)
        item = ET.SubElement(dependencies, q('dependency'))
        for name, value in [('groupId', 'org.robolectric'), ('artifactId', artifact), ('version', version), ('scope', 'test')]:
            ET.SubElement(item, q(name)).text = value
    ET.indent(root, space='  ')
    text = ET.tostring(root, encoding='unicode') + '\n'
    require(str(baseline) not in text and str(Path.home()) not in text, 'NO_LOCAL_DEVELOPER_PATHS_IN_POM')
    require('robolectric.offline' not in text and 'robolectric.dependency.dir' not in text, 'PORTABLE_ROBOLECTRIC_RESOLUTION')
    (out / 'pom.xml').write_text(text)


def prepare(apk, baseline, build, dex2jar, bundles, jars, out, source):
    apk, baseline, build, dex2jar, bundles, jars, out = (
        p.resolve() for p in (apk, baseline, build, dex2jar, bundles, jars, out))
    require(re.fullmatch('[0-9a-f]{40}', source) is not None, 'EXACT_COMMITTED_SOURCE_SHA')
    require(subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip() == source, 'SOURCE_IS_CURRENT_HEAD')
    branch = (os.environ.get('GITHUB_REF_NAME') if os.environ.get('GITHUB_ACTIONS') == 'true' else
              subprocess.check_output(['git', '-C', str(REPO), 'branch', '--show-current'], text=True).strip())
    require(branch == BRANCH and load(OWNER / 'SCOPE.json')['branch'] == BRANCH, 'AUTHORIZED_WORKING_BRANCH')
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'AUTHORIZED_REPOSITORY')
        require(os.environ.get('GITHUB_SHA') == source, 'EXACT_CI_SOURCE')
    require(not out.exists(), 'FRESH_OUTPUT_REQUIRED')
    committed(Path(__file__), source)
    for code in ('build.py', 'verify_owner_source.py'):
        committed(OWNER / code, source)
    sys.path.insert(0, str(OWNER))
    builder = module('cards_release_builder', OWNER / 'build.py')
    verifier = module('cards_release_canonical_verifier', OWNER / 'verify_owner_source.py')
    require(builder.VERSION == str(VERSION) + '.cobra.1' and builder.BASE_SOURCE == SIGNED_SOURCE, 'CANDIDATE_COMPONENT_VERSION')
    receipt = load(build / 'BUILD.json')
    require(receipt['status'] == 'COMPILED_UNSIGNED_COBRA_OWNER_ONLY' and receipt['APK'] == 'NOT_BUILT', 'ACTUAL_UNSIGNED_OWNER_BUILD')
    require(receipt['baseline_signed_source'] == SIGNED_SOURCE, 'ACCEPTED431_SOURCE')
    require(receipt['candidate_component_version'] == builder.VERSION, 'EXACT_TARGET_VERSION')
    require({descriptor_class(n) for n in receipt['changed_classes']} == CHANGED, 'EXACT_FIVE_CHANGED_CLASSES')
    expected_sources = {p.relative_to(REPO).as_posix(): sha(p) for p in builder.compiler_sources()}
    require(set(expected_sources) == EXPECTED_COMPILER_PATHS and len(expected_sources) == 23, 'EXACT_REVIEWED_TWENTY_THREE_COMPILER_PATHS')
    require(receipt['compiler_source_files'] == expected_sources, 'COMPLETE_CURRENT_COMPILER_SOURCE_MANIFEST')
    for name, pin in expected_sources.items():
        require(committed(REPO / name, source) == pin, 'COMMITTED_COMPILER_SOURCE:' + name)
        require(sha(build / 'compiler-source-snapshot' / name) == pin, 'IMMUTABLE_COMPILER_SNAPSHOT:' + name)
    helpers = {str((OWNER / name).relative_to(REPO)): sha(OWNER / name) for name in HELPER_PATHS}
    require(receipt['helper_sources'] == helpers, 'EXACT_FOUR_HELPER_SOURCE_FILES')
    require(all(expected_sources.get(name) == pin for name, pin in helpers.items()), 'HELPERS_IN_COMPILER_MANIFEST')
    new_expected = {descriptor_class(n) for n in receipt['new_classes']}
    require(len(new_expected) == len(receipt['new_classes']), 'NO_DUPLICATE_HELPER_DECLARATIONS')
    require({name[:-6].split('$', 1)[0] for name in new_expected} == HELPER_ROOTS, 'EXACT_FOUR_HELPER_ROOTS')
    helper_smali = canonical_classes(build / 'helper-smali')
    require({descriptor_class(n) for n in helper_smali} == new_expected, 'EXACT_COMPILED_HELPER_CLASS_SET')
    tools = load(OWNER / 'DEX2JAR-LIB-PINS.json')
    require({p.name: sha(p) for p in (dex2jar / 'lib').glob('*.jar')} == tools, 'PINNED_DEX2JAR_TOOLS')
    baksmali_pins_path = REPO / 'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json'
    committed(baksmali_pins_path, source)
    require({p.name: sha(p) for p in jars.glob('*.jar')} == load(baksmali_pins_path), 'PINNED_CANONICAL_TOOLS')
    require(sha(apk) == SIGNED_APK, 'EXACT_ACCEPTED431_APK')
    with ZipFile(apk) as archive:
        require({n: digest(archive.read(n)) for n in BASE_DEX} == BASE_DEX, 'EXACT_FIVE_BASELINE_APK_DEX')
    baseline_receipt = load(baseline / 'INPUTS.json')
    require(baseline_receipt['source'] == SIGNED_SOURCE and baseline_receipt['versionCode'] == 2103431, 'BASELINE_HOST_IDENTITY')
    require(baseline_receipt['APK_sha256'] == SIGNED_APK and baseline_receipt['DEX_sha256'] == BASE_DEX, 'BASELINE_HOST_SOURCE_BINDING')
    for name, pin in BASE_DEX.items():
        require(sha(baseline / name) == pin, 'BASELINE_HOST_DEX:' + name)
    for name, pin in baseline_receipt['translated_jar_SHA256'].items():
        require(sha(baseline / (Path(name).stem + '-translated.jar')) == pin, 'BASELINE_TRANSLATION:' + name)
    require(set(baseline_receipt['translated_jar_SHA256']) == set(BASE_DEX), 'ALL_BASELINE_TRANSLATIONS_REQUIRED')
    for name, pin in BASE_COMPONENTS.items():
        require(sha(bundles / name) == pin, 'EXACT_ACCEPTED431_COMPONENT:' + name)
    require(load(OWNER / 'BASELINE.json')['component_sha256'] == BASE_COMPONENTS, 'PROTECTED_BASELINE_COMPONENT_VECTOR')
    baseline_authority = json.loads(subprocess.check_output(['git', '-C', str(REPO), 'show', SIGNED_SOURCE + ':repairs/dual-experience-isolation-2103420/release-authority.json']))
    require(baseline_authority['generation'] == 16 and baseline_authority['candidate_versionCode'] == 2103431, 'ACCEPTED431_AUTHORITY')
    require(receipt['baseline_components'] == load(bundles / 'catalog.json') == baseline_authority['bundle_catalog'], 'EXACT_COMPILED_ACCEPTED431_CATALOG')
    with ZipFile(bundles / 'COBRA.zip') as archive:
        metadata_raw = archive.read('component.json')
        component = json.loads(metadata_raw)
        require(component['owner'] == 'COBRA' and component['version'] == '2103431.cobra.1', 'ACCEPTED_COBRA_IDENTITY')
        require(component['dex'] == {'dex/part-0.dex': BASE_DEX['classes4.dex'], 'dex/part-1.dex': BASE_DEX['classes5.dex']}, 'ACCEPTED_COBRA_DEX_VECTOR')
    owner_dex = {p.name: sha(p) for p in (build / 'owner-dex/COBRA').glob('*.dex')}
    require(set(owner_dex) == {'part-0.dex', 'part-1.dex'}, 'EXACT_TWO_OWNER_DEX_PARTS')
    full_original = read_classes([baseline / 'classes4-translated.jar', baseline / 'classes5-translated.jar'])
    original = {n: raw for n, raw in full_original.items() if not n.startswith(EXCLUDED)}
    require(read_classes([baseline / 'production.jar']) == original, 'EXACT_ACCEPTED431_HOST_CLASSES')
    support = {}
    for part in ('classes-translated.jar', 'classes2-translated.jar', 'classes3-translated.jar'):
        with ZipFile(baseline / part) as archive:
            for name in archive.namelist():
                if name.endswith('.class') and name.startswith(('com/projectinfinity/kodi/', 'androidx/')) and not name.startswith(EXCLUDED):
                    support.setdefault(name, archive.read(name))
    require(read_classes([baseline / 'support.jar']) == support, 'EXACT_FROZEN_SUPPORT_CLASSES')

    out.mkdir(parents=True)
    binding = dict(status='PREPARING_FRESH_COMMITTED_CI_OWNER_CLASSPATH', phase='FRESH_CI_OWNER_COMPILE_QA_NO_BEHAVIOR', source=source, branch=branch,
                   versionCode=VERSION, candidate_generation=GENERATION, baseline_signed_source=SIGNED_SOURCE,
                   baseline_APK_sha256=SIGNED_APK, baseline_DEX_sha256=BASE_DEX,
                   baseline_component_sha256=BASE_COMPONENTS, owner_DEX_sha256=owner_dex,
                   owner_BUILD_sha256=sha(build / 'BUILD.json'), compiler_source_files=expected_sources,
                   allowed_changed_existing_classes=sorted(CHANGED), expected_new_helper_classes=sorted(new_expected),
                   translation_tool_lib_sha256=tools,
                   frozen_compiler_snapshot='ALL_CURRENT_MANIFEST_FILES_BYTE_VERIFIED', helper_source_sha256=helpers,
                   owner_BUILD=receipt, prepare_source_sha256=sha(Path(__file__)),
                   verifier_source_sha256=sha(OWNER / 'verify_owner_source.py'),
                   behavior='NOT_RUN', application_APK='NOT_BUILT_OR_MODIFIED', CI_signer='NOT_INVOKED',
                   acceptance='NOT_GRANTED_OR_MODIFIED', physical_Fold='NOT_RUN', shutdown='NOT_RUN')
    save(out / 'SOURCE-BINDINGS.json', binding)
    shutil.copyfile(build / 'BUILD.json', out / 'OWNER-BUILD.json')
    try:
        # Fresh verifier output in a separate workspace avoids reusing any old
        # proof and leaves producer/package canonical output directories intact.
        scratch = out / 'fresh-canonical-work'
        scratch.mkdir()
        shutil.copyfile(build / 'BUILD.json', scratch / 'BUILD.json')
        for name in ('baseline', 'owner-dex'):
            (scratch / name).symlink_to(build / name, target_is_directory=True)
        proof = verifier.verify(scratch, bundles, jars)
        require(proof['build_receipt_sha256'] == binding['owner_BUILD_sha256'], 'FRESH_CANONICAL_BUILD_BINDING')
        require(proof['compiler_source_files'] == expected_sources, 'FRESH_CANONICAL_COMPILER_BINDING')
        require(proof['verifier_source_sha256'] == binding['verifier_source_sha256'], 'FRESH_CURRENT_VERIFIER')
        require(proof['new_DEX_sha256'] == owner_dex, 'FRESH_ACTUAL_OWNER_DEX_BINDING')
        require(proof['unchanged_existing_classes'] == 7137 and proof['baseline_existing_classes'] == len(full_original) == 7142, 'FROZEN_CANONICAL_CLASS_COUNT')
        require({descriptor_class(n) for n in proof['changed_existing_classes']} == CHANGED, 'FRESH_EXACT_FIVE_CLASS_DELTA')
        require({descriptor_class(n) for n in proof['new_classes']} == new_expected and not proof['missing_classes'], 'FRESH_EXACT_HELPER_DELTA')
        require(len(proof['changed_methods']['Lcom/projectinfinity/kodi/InfinityLiveActivity;']) == 22, 'REVIEWED_TWENTY_TWO_ACTIVITY_METHODS')
        canonical = canonical_classes(scratch / 'independent-canonical')
        for name, raw in helper_smali.items():
            require(canonical[name] == raw, 'ACTUAL_HELPER_MATCHES_COMPILED_SOURCE:' + name)
        shutil.copyfile(scratch / 'INDEPENDENT-CANONICAL-RESULT.json', out / 'INDEPENDENT-CANONICAL-RESULT.json')
        save(out / 'ACTUAL-CANONICAL-CLASS-HASHES.json', {name: digest(raw.encode()) for name, raw in sorted(canonical.items())})
        errors = out / 'translation-errors'
        errors.mkdir()
        translated = []
        for name in sorted(owner_dex):
            target = out / (Path(name).stem + '-translated.jar')
            translated.append(target)
            command = ['java', '-cp', str(dex2jar / 'lib/*'), 'com.googlecode.dex2jar.tools.Dex2jarCmd',
                       str(build / 'owner-dex/COBRA' / name), '-o', str(target), '-e', str(errors / (name + '.zip'))]
            with (out / (Path(name).stem + '-D2J.txt')).open('w') as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        require(not list(errors.iterdir()), 'OWNER_TRANSLATION_ERROR_ARCHIVES_REFUSED')
        actual = read_classes(translated)
        new_detected = set(actual) - set(full_original)
        require(not set(full_original) - set(actual) and new_detected == new_expected, 'EXACT_TRANSLATED_CLASS_SET')
        changed_translation = sorted(n for n in full_original if full_original[n] != actual[n])
        require(CHANGED <= set(changed_translation), 'SELECTED_TRANSLATED_CLASSES_CHANGED')
        drift = sorted(set(changed_translation) - CHANGED)
        save(out / 'EXCLUDED-TRANSLATION-DRIFT.json', dict(
            changed_existing_translated_classes=changed_translation, unselected_translated_differences_EXCLUDED=drift,
            class_sha256={n: {'accepted431': digest(full_original[n]), 'current_owner': digest(actual[n])} for n in changed_translation},
            policy='Fresh canonical proof passed; only five selected existing classes and exact compiled helpers are admitted'))
        merged = dict(original)
        for name in CHANGED | new_expected:
            merged[name] = actual[name]
        require({n for n in original if merged[n] != original[n]} == CHANGED, 'EXACT_FIVE_HOST_CLASS_OVERLAY')
        require(set(merged) == set(original) | new_expected, 'NO_UNDECLARED_HOST_CLASSES')
        require(all(merged[n] == original[n] for n in original if n not in CHANGED), 'ALL_UNSELECTED_HOST_CLASS_BYTES_FROZEN')
        with ZipFile(out / 'production.jar', 'w', ZIP_DEFLATED) as archive:
            for name in sorted(merged):
                info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, merged[name])
        require(read_classes([out / 'production.jar']) == merged, 'WRITTEN_HOST_CLASSES_EXACT')
        shutil.copyfile(baseline / 'support.jar', out / 'support.jar')
        require(sha(out / 'support.jar') == sha(baseline / 'support.jar'), 'FROZEN_SUPPORT_JAR_BYTES')
        shutil.copytree(baseline / 'android-test-libs', out / 'android-test-libs')
        require({p.name for p in (out / 'android-test-libs').iterdir()} == {'monitor.jar', 'espresso.jar'}, 'EXACT_ANDROID_TEST_LIBRARIES')
        portable_pom(baseline, out)
        (out / 'src/test/java/com/projectinfinity/kodi').mkdir(parents=True)
        fixture = OWNER / 'settings-return/CobraSettingsReturnBaselineTest.java'
        committed(fixture, source)
        fixtures = out / 'fixtures-not-selected'
        fixtures.mkdir()
        shutil.copyfile(fixture, fixtures / fixture.name)
        save(out / 'HOST-OVERLAY-CLASS-HASHES.json', {n: digest(merged[n]) for n in sorted(CHANGED | new_expected)})
        # Recheck source/artifact identity after all compilation-QA operations.
        require(sha(build / 'BUILD.json') == binding['owner_BUILD_sha256'], 'OWNER_BUILD_MUTATED_DURING_PREP')
        require({p.name: sha(p) for p in (build / 'owner-dex/COBRA').glob('*.dex')} == owner_dex, 'OWNER_DEX_MUTATED_DURING_PREP')
        require({p.relative_to(REPO).as_posix(): sha(p) for p in builder.compiler_sources()} == expected_sources, 'SOURCE_MUTATED_DURING_PREP')
        require(sha(OWNER / 'verify_owner_source.py') == binding['verifier_source_sha256'], 'VERIFIER_MUTATED_DURING_PREP')
        binding.update(status='PASS_FRESH_SOURCE_BOUND_EXACT_FIVE_CLASS_HOST_OVERLAY_NO_BEHAVIOR',
                       fresh_canonical_proof_sha256=sha(out / 'INDEPENDENT-CANONICAL-RESULT.json'),
                       changed_existing_classes=sorted(CHANGED), new_helper_classes=sorted(new_expected),
                       unchanged_baseline_host_class_count=len(original) - len(CHANGED),
                       unchanged_actual_owner_canonical_classes=7137, unchanged_full_owner_canonical_class_count=7137,
                       host_overlay_class_hash_inventory_sha256=sha(out / 'HOST-OVERLAY-CLASS-HASHES.json'),
                       excluded_translation_drift_inventory_sha256=sha(out / 'EXCLUDED-TRANSLATION-DRIFT.json'),
                       unselected_translation_differences_excluded=len(drift), behavioral_execution='NOT_RUN',
                       canonical_class_hash_inventory_sha256=sha(out / 'ACTUAL-CANONICAL-CLASS-HASHES.json'),
                       canonical_chain=dict(independent_proof_sha256=sha(out / 'INDEPENDENT-CANONICAL-RESULT.json'),
                                            accepted_COBRA_ZIP_sha256=BASE_COMPONENTS['COBRA.zip'],
                                            accepted_component_metadata_sha256=digest(metadata_raw),
                                            canonical_existing_classes_checked=7142, canonical_unchanged_existing_classes=7137,
                                            canonical_new_helpers=len(new_expected),
                                            proof='Fresh current verifier on actual owner DEX; exact accepted431 metadata and reviewed methods'),
                       fixture_source=dict(path=str(fixture), sha256=sha(fixture),
                                           copied_to='fixtures-not-selected/' + fixture.name, execution='NOT_SELECTED_OR_RUN'),
                       production_jar_sha256=sha(out / 'production.jar'), support_jar_sha256=sha(out / 'support.jar'),
                       translated_owner_jar_sha256={p.name: sha(p) for p in translated}, pom_sha256=sha(out / 'pom.xml'),
                       android_test_library_sha256={p.name: sha(p) for p in (out / 'android-test-libs').iterdir()},
                       native_graphics_dependencies={name: {'version': version, 'expected_jar_sha256': pin, 'scope': 'host-test-only; official Maven resolution'}
                                                    for name, (version, pin) in NATIVE_DEPS.items()})
        save(out / 'SOURCE-BINDINGS.json', binding)
        print(json.dumps({k: v for k, v in binding.items() if k != 'owner_BUILD'}, indent=2))
    except Exception as failure:
        binding.update(status='FAILED_CLOSED_SOURCE_CANONICAL_OR_CLASSPATH_PREPARATION', error=str(failure))
        save(out / 'SOURCE-BINDINGS.json', binding)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('apk', 'baseline', 'build', 'dex2jar', 'bundles', 'jars', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source', required=True)
    prepare(**vars(parser.parse_args()))
