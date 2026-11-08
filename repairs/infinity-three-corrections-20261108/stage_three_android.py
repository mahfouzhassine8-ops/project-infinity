"""Source-pinned disposable Android fixture only; no production modifications."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'repairs/infinity-final-release-462-20261107'
sys.path[:0] = [str(HERE), str(ROOT / 'repairs/save-later-multiimage-20261023')]
import android_inputs
from verify_device_sources import audit


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_observer(source):
    # Kodi XBPython.cpp sets Py_OptimizeFlag=1. Preserve every selected check
    # and its evaluated SDK call using explicit runtime if/raise statements.
    class RuntimeChecks(ast.NodeTransformer):
        def visit_Assert(self, node):
            return ast.copy_location(ast.If(test=ast.UnaryOp(op=ast.Not(), operand=node.test),
                body=[ast.Raise(exc=ast.Call(func=ast.Name(id='AssertionError', ctx=ast.Load()),
                    args=[node.msg] if node.msg else [], keywords=[]), cause=None)], orelse=[]), node)

    tree = ast.fix_missing_locations(RuntimeChecks().visit(ast.parse(source)))
    assert not any(isinstance(n, ast.Assert) for n in ast.walk(tree))
    return ast.unparse(tree) + '\n'


def stage(baseline, candidate, recovery, sdk, out):
    assert not out.exists()
    out.mkdir(parents=True)
    pair = json.loads((HERE / 'SIGNED-PAIR.json').read_text())
    for version, path in ((2103464, baseline), (2103466, candidate), (2103467, recovery)):
        assert hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() == pair[str(version)]['sha256']
        signature = subprocess.check_output([str(sdk / 'apksigner'), 'verify', '--verbose', '--print-certs', str(path)], text=True)
        assert re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', signature) == [pair['certificate_sha256']]
        (out / (str(version) + '-SIGNATURE.txt')).write_text(signature)
    audit(HERE / 'inputs/Infinity_Source_Exports_For_Work.zip', out / 'owner', False)
    installed = out / 'owner/installed'
    addons = out / 'home/addons'
    addons.mkdir(parents=True)
    with ZipFile(baseline) as z:
        for name in z.namelist():
            if any(name.startswith('assets/addons/' + aid + '/') for aid in ('script.infinity.commandcenter', 'script.infinity.rails', 'script.infinity.uirepair', 'script.infinity.watchedbridge')) and not name.endswith('/'):
                target = addons / name.removeprefix('assets/addons/')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))
        builtins = {ET.fromstring(z.read(n)).get('id') for n in z.namelist() if n.startswith('assets/addons/') and n.endswith('/addon.xml')}
        compat = json.loads(subprocess.check_output(['git', 'show', '2759febb:repairs/infinity-final-release-462-20261107/COMPAT82-INPUT.json']))
        content = {p.name: p.read_bytes() for p in (ROOT / compat['original_source_directory']).iterdir() if p.is_file()}
        assert {n: sha(b) for n, b in content.items()} == compat['before']
        patch_bytes = z.read(compat['original_signed462_embedded_patch'])
        assert sha(patch_bytes) == compat['original_signed_patch_sha256']
        with ZipFile(io.BytesIO(patch_bytes)) as patch:
            manifest = json.loads(patch.read('manifest.json'))
            for row in manifest['files']:
                name = row['path']
                assert Path(name).name == name
                if row['before'] is not None:
                    assert sha(content[name]) == row['before']
                raw = patch.read('payload/' + name)
                assert sha(raw) == row['after']
                content[name] = raw
        assert {n: sha(b) for n, b in content.items()} == compat['after']
        target = addons / compat['addon']
        target.mkdir()
        for name, raw in content.items():
            (target / name).write_bytes(raw)
    shutil.copyfile(installed / 'script.infinity.commandcenter/native_search_compatibility.py', addons / 'script.infinity.commandcenter/native_search_compatibility.py')
    for aid in ('plugin.video.pov', 'script.module.tmdbhelper.sync.trakt'):
        shutil.copytree(installed / aid, addons / aid)
    pins = json.loads((HERE / 'ANDROID-INPUT-PINS.json').read_text())
    rows = []
    for row in pins['archives']:
        assert row['addon'] not in builtins
        raw = android_inputs.fetch(row['url'])
        assert sha(raw) == row['sha256']
        with ZipFile(io.BytesIO(raw)) as z:
            for i in z.infolist():
                assert not i.filename.startswith('/') and '..' not in i.filename.split('/') and '\\' not in i.filename
                assert Path(i.filename).parts[0] == row['addon'] and (i.external_attr >> 16) & 0o170000 != 0o120000
            z.extractall(addons)
        rows.append(row)
    # The publisher bytes remain unmodified. Only CRLF/LF differs from Fold's
    # five captured Umbrella files, including both complete native Search menus.
    for source in (installed / 'plugin.video.umbrella').rglob('*'):
        if source.is_file():
            assert source.read_text() == (addons / 'plugin.video.umbrella' / source.relative_to(installed / 'plugin.video.umbrella')).read_text()
    qa = addons / 'script.infinity.finalreleaseqa'
    qa.mkdir()
    (qa / 'addon.xml').write_text('<addon id="script.infinity.finalreleaseqa" name="Disposable three-scope QA" version="1.0.0" provider-name="Infinity engineering"><requires><import addon="xbmc.python" version="3.0.1"/><import addon="script.module.tmdbhelper.sync.trakt" version="1.2.8"/></requires><extension point="xbmc.python.script" library="qa.py"/><extension point="xbmc.addon.metadata"><summary lang="en">Selected Search and Trakt QA only</summary><platform>all</platform></extension></addon>')
    base = subprocess.check_output(['git', 'show', '2759febb:repairs/infinity-final-release-462-20261107/android_qa.py']).decode()
    assert "xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')==expected" in base
    assert 'select-row-no-list-read' not in base
    base = base.replace("PROVIDERS=['plugin.video.watchnixtoons2','plugin.video.umbrella']", "PROVIDERS=['plugin.video.pov','plugin.video.umbrella']")
    anchor = "if len(sys.argv)>1 and sys.argv[1].lstrip('-').isdigit():plugin_directory()"
    assert base.count(anchor) == 1
    observer = base.replace(anchor, (HERE / 'android_qa_extension.py.txt').read_text() + '\n' + anchor)
    observer = checked_observer(observer)
    compile(observer, 'qa.py', 'exec', optimize=1)
    (qa / 'qa.py').write_text(observer)
    shutil.copyfile(ROOT / 'repairs/save-later-multiimage-20261023/android_runtime_checks.py', qa / 'android_runtime_checks.py')
    profile = out / 'home/userdata'
    profile.mkdir()
    (profile / 'guisettings.xml').write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting></settings>')
    (profile / 'release-data-sentinel.txt').write_bytes(b'preserve-three-corrections-preupdate-data-v1')
    report = dict(status='PASS_PINNED_SIGNED_PAIR_AND_DISPOSABLE_SOURCE_FIXTURE', signed_pair=pair, provider_inputs=rows,
                  owner_POV_files=210, owner_Trakt_files=145, Umbrella_source='Unmodified publisher6.8.00; all5 captured Fold files text-identical after newline normalization',
                  existing_compat82='Exact six files reused from passing diagnosis; original guards unchanged',
                  live_ListItem_observer_retained=True, diagnostic_workaround_applied=False, APK_modified=False,
                  observer_assertions='EXPLICIT_IF_RAISE_VALID_UNDER_KODI_OPTIMIZATION1', observer_sha256=sha(observer.encode()),
                  owner_data_or_settings_accessed=False, physical_Fold='NOT_RUN', shutdown='NOT_SELECTED')
    (out / 'ANDROID-INPUTS.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for n in ('baseline', 'candidate', 'recovery', 'sdk', 'out'):
        p.add_argument('--' + n, type=Path, required=True)
    stage(**vars(p.parse_args()))
