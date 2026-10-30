"""Strict host-only native Cards overlay on exact accepted431 translated inputs.

No application packaging/signing, provider execution or Android installation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
APK = '3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'
SOURCE = '9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
CARD = 'com/projectinfinity/kodi/InfinityLiveActivity$CobraPosterChannelCard.class'
LOGO = 'com/projectinfinity/kodi/CobraLogoRequests.class'
CLEAR_JAR = '7d0c726ce92d74bd2a1fddea9c7f2014f299e56e3faa5b1db4fe8c3a1bd2d39f'
CARD_DEX = 'c1d0c50f1a13427a58fe925c49ab7019d4b16e99937de1ba20b8d94dea290ebf'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def classes(path):
    with ZipFile(path) as jar:
        return {name: jar.read(name) for name in jar.namelist() if name.endswith('.class')}


def prepare(baseline, out, phase, clear_production=None, card_dex=None,
            helper_classes=None, helper_receipt=None, dex2jar=None):
    baseline, out = baseline.resolve(), out.resolve()
    assert phase in ('ACCEPTED431_BASELINE', 'CARDS_TILE_PROTOTYPE')
    receipt = json.loads((baseline / 'INPUTS.json').read_text())
    assert receipt['source'] == SOURCE and receipt['APK_sha256'] == APK and receipt['versionCode'] == 2103431
    for name, pin in receipt['DEX_sha256'].items():
        assert sha(baseline / name) == pin, name
    for name, pin in receipt['translated_jar_SHA256'].items():
        assert sha(baseline / (Path(name).stem + '-translated.jar')) == pin, name
    original = classes(baseline / 'production.jar')
    signed_original = {}
    for name in ('classes4-translated.jar', 'classes5-translated.jar'):
        for member, content in classes(baseline / name).items():
            if not member.startswith(('com/google/common/', 'com/google/thirdparty/')):
                signed_original.setdefault(member, content)
    assert original == signed_original, 'Baseline production jar must remain exact accepted431 translation'
    assert not out.exists(), 'Fresh host output required'
    out.mkdir(parents=True)
    merged = dict(original)
    prototype = None
    if phase == 'CARDS_TILE_PROTOTYPE':
        assert all(value is not None for value in (clear_production, card_dex, helper_classes, helper_receipt, dex2jar))
        assert sha(clear_production) == CLEAR_JAR
        clear = classes(clear_production)
        assert set(clear) == set(original)
        assert [name for name in original if clear[name] != original[name]] == [LOGO]
        assert sha(card_dex) == CARD_DEX
        translated = out / 'native-card-hook-translated.jar'
        errors = out / 'translation-errors'
        errors.mkdir()
        subprocess.run(['java', '-cp', str(dex2jar / 'lib/*'),
                        'com.googlecode.dex2jar.tools.Dex2jarCmd', str(card_dex),
                        '-o', str(translated), '-e', str(errors / 'card.zip')], check=True)
        assert not list(errors.iterdir()), 'Native card translation error refused'
        card = classes(translated)
        assert set(card) == {CARD}, 'Only actual native Cards class overlay admitted'
        compilation = json.loads(helper_receipt.read_text())
        source = HERE.parent / 'runtime/CobraCardsTiles.java'
        assert sha(source) == compilation['source_sha256'], 'Helper source changed after compilation'
        helper = {str(path.relative_to(helper_classes)): path.read_bytes()
                  for path in sorted(helper_classes.rglob('*.class'))}
        assert {name: hashlib.sha256(raw).hexdigest() for name, raw in helper.items()} == compilation['class_files']
        assert len(helper) == 7 and all(name.startswith('com/projectinfinity/kodi/CobraCardsTiles') for name in helper)
        assert not set(helper) & set(original), 'No accepted class can be replaced by Java helper compilation'
        merged.update(clear)
        merged.update(card)
        merged.update(helper)
        assert sorted(name for name in original if merged[name] != original[name]) == sorted((CARD, LOGO))
        prototype = {'clear_API_jar_sha256': sha(clear_production), 'card_DEX_sha256': sha(card_dex),
                     'helper_source_sha256': compilation['source_sha256'],
                     'new_helper_class_sha256': compilation['class_files'],
                     'changed_existing_translated_classes': sorted((CARD, LOGO)),
                     'all_other_accepted_translated_classes_exact': True}
    with ZipFile(out / 'production.jar', 'w', ZIP_DEFLATED) as jar:
        for name, raw in merged.items():
            jar.writestr(name, raw)
    shutil.copyfile(baseline / 'support.jar', out / 'support.jar')
    assert sha(baseline / 'support.jar') == sha(out / 'support.jar')
    shutil.copytree(baseline / 'android-test-libs', out / 'android-test-libs')
    test = HERE / 'CobraCardsNativeRenderTest.java'
    target = out / 'src/test/java/com/projectinfinity/kodi'
    target.mkdir(parents=True)
    shutil.copyfile(test, target / test.name)
    pom = (baseline / 'pom.xml').read_text().replace(str(baseline), str(out))
    properties = '<cards.render.phase>' + phase + '</cards.render.phase><cards.render.output>' + str(out / 'private-render') + '</cards.render.output>'
    pom = pom.replace('<systemPropertyVariables>', '<systemPropertyVariables>' + properties)
    (out / 'pom.xml').write_text(pom)
    selected = ['renderNativeCards941'] if phase == 'ACCEPTED431_BASELINE' else [
        'renderNativeCards941', 'nativeCardRecycleAndCurrentProgramme',
        'nativeCardDimensionsAndCornerTouch', 'nativeCardLogoRecycle']
    result = {'phase': phase, 'baseline_source': SOURCE, 'baseline_APK_sha256': APK,
              'baseline_INPUTS_sha256': sha(baseline / 'INPUTS.json'),
              'baseline_DEX_sha256': receipt['DEX_sha256'], 'prototype': prototype,
              'support_jar_exact_sha256': sha(out / 'support.jar'),
              'production_host_jar_sha256': sha(out / 'production.jar'),
              'test_source_sha256': sha(test), 'prepare_source_sha256': sha(Path(__file__)),
              'selected_class': 'CobraCardsNativeRenderTest', 'selected_methods': selected,
              'runtime': 'Robolectric API35 NativeGraphics HOST',
              'actual_native_UI': 'Original buildShell/showGuideShell plus actual native Card constructors/bind/refresh; no replacement header/list builders',
              'terminal_spies': 'Only selectGuidePreview/cobraShowQuickPeek for row dispatch; original More menu executes',
              'provider_IO': 'Existing executor admissions recorded, worker bodies not executed',
              'application_APK': 'NOT_BUILT_OR_MODIFIED', 'physical_Fold': 'NOT_RUN',
              'reference_images': 'PRIVATE; NOT_PACKAGED_OR_COPIED', 'shutdown': 'NOT_RUN'}
    (out / 'INPUTS.json').write_text(json.dumps(result, indent=2) + '\n')
    (out / 'SELECTION.json').write_text(json.dumps({'selected_class': result['selected_class'], 'selected_methods': selected,
                                                  'scope': str(HERE / 'SCOPE.json'), 'shutdown': 'NOT_SELECTED'}, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--phase', choices=('ACCEPTED431_BASELINE', 'CARDS_TILE_PROTOTYPE'), required=True)
    for name in ('clear-production', 'card-dex', 'helper-classes', 'helper-receipt', 'dex2jar'):
        parser.add_argument('--' + name, type=Path)
    prepare(**vars(parser.parse_args()))
