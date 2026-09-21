"""Freeze exact 207→208 source, icon payloads, tests and isolated workflow.

Reads the candidate; never overwrites it. The candidate's Gradle version must
already be 208. All generated files remain in this successor recipe directory.
"""
from pathlib import Path
import base64
import difflib
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from contract import *
from branding_package import png_size, resource_slots, validate_rows

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
PARENT = WORK / 'cobra-2103207-locked-source'
CANDIDATE = WORK / 'cobra-2103208-work'
PARENT_EVIDENCE = WORK / 'cobra-207-delivery/evidence-1/audit207/repairs/cobra-feature-refinement-2103207'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def workflow():
    text = (PARENT_EVIDENCE / 'infinity-2103207-feature-refinement.yml').read_text()
    text = text.replace('name: Infinity | 2103207 Feature Refinement', 'name: Infinity | 2103208 Integration Polish', 1)
    text = text.replace('branches: [infinity-cobra-2103207-feature-refinement-rc1]', 'branches: [infinity-cobra-2103208-integration-polish-rc1]', 1)
    text = text.replace("'.github/workflows/infinity-2103207-feature-refinement.yml'", "'.github/workflows/infinity-2103208-integration-polish.yml'", 1)
    text = text.replace("'repairs/cobra-feature-refinement-2103207/**'", "'" + RECIPE_PATH + "/**'", 1)
    text = text.replace('group: infinity-2103207-', 'group: infinity-2103208-', 1)
    anchor = "with: {ref: '${{ github.sha }}', path: audit207, persist-credentials: false}"
    require(text.count(anchor) == 1, 'Parent checkout drift')
    text = text.replace(anchor, "with: {ref: " + PARENT_COMMIT + ", path: audit207, persist-credentials: false}\n" + '''      - name: Isolated reviewed 208 successor
        uses: actions/checkout@v7
        with: {ref: '${{ github.sha }}', path: audit208, persist-credentials: false}
      - name: Exact locked 207 rollback and source
        uses: actions/download-artifact@v8
        with: {name: Infinity-2103207-Feature-Refinement-TEST-CANDIDATE-Replica-1-Attempt-1, run-id: 35623403102, github-token: '${{ github.token }}', path: baseline207}''', 1)
    start = text.index('      - name: Publish verified 207 TEST CANDIDATE only after all gates')
    end = text.index('      - name: Preserve complete 207 and parent audit evidence', start)
    text = text[:start] + '''      - name: Guard successor recipe and apply only after all 691 original 207 cases pass
        run: |
          python3 audit208/repairs/cobra-integration-polish-2103208/test_guards.py
          python3 audit208/repairs/cobra-integration-polish-2103208/test_parent_png.py
          python3 audit208/repairs/cobra-integration-polish-2103208/ci.py upgrade
          python3 audit205/repairs/cobra-final-features-2103205/host_timeshift_adapter.py --fixture audit199/repairs/cobra-power-audit-2103199/tests/host_timeshift.py --source kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in --out audit208/host_timeshift
          python3 audit199/repairs/cobra-power-audit-2103199/tests/host_timeshift_stop.py --source kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in --out audit208/host_timeshift_stop
          python3 audit199/repairs/cobra-power-audit-2103199/tests/display_geometry_host.py --activity kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in --out audit208/display_geometry_host

      - name: Build 208 Android layer and exact approved branding delta without native rebuild
        env:
          INFINITY_KEYSTORE_B64: ${{ secrets.INFINITY_KEYSTORE_B64 }}
          INFINITY_STORE_PASSWORD: ${{ secrets.INFINITY_STORE_PASSWORD }}
          INFINITY_KEY_PASSWORD: ${{ secrets.INFINITY_KEY_PASSWORD }}
          INFINITY_KEY_ALIAS: ${{ secrets.INFINITY_KEY_ALIAS }}
        run: |
          python3 audit208/repairs/cobra-integration-polish-2103208/branding_package.py --source kodi --base-apk baseline168native/Infinity-1.0.9-Cobra-Status-Bar-PythonInvoker-Stability-RC1.apk --build-dir refinement208-build --out signed208
          python3 audit208/repairs/cobra-integration-polish-2103208/ci.py verify

      - name: Rerun all 691 inherited identities and reviewed successor cases
        run: python3 audit208/repairs/cobra-integration-polish-2103208/ci.py tests

      - name: Publish 208 TEST CANDIDATE only after every gate
        uses: actions/upload-artifact@v7
        with:
          name: Infinity-2103208-Integration-Polish-TEST-CANDIDATE-Replica-${{ matrix.replica }}-Attempt-${{ github.run_attempt }}
          path: signed208/
          if-no-files-found: error
          compression-level: 0
          retention-days: 90

''' + text[end:]
    text = text.replace('Preserve complete 207 and parent audit evidence', 'Preserve complete 208 and exact parent audit evidence', 1)
    text = text.replace('name: Infinity-2103207-Feature-Refinement-Evidence-', 'name: Infinity-2103208-Integration-Polish-Evidence-', 1)
    text = text.replace('            audit207/\n', '            audit207/\n            audit208/\n            signed208/*.json\n            signed208/*.txt\n', 1)
    text = text.replace('Preserve exact locked 2103206 rollback', 'Preserve exact locked 2103207 rollback', 1)
    text = text.replace('Infinity-2103206-Exact-Rollback-Before-2103207-', 'Infinity-2103207-Exact-Rollback-Before-2103208-', 1)
    text = text.replace('          path: baseline206/\n', '          path: baseline207/\n', 1)
    require("ref: '" + '${{ github.sha }}' + "', path: audit207" not in text, 'Parent recipe not pinned')
    require(text.count('ci.py tests') >= 2, 'Missing parent/successor test stages')
    return text

def main():
    require(sha(WORK / 'Cobra-2103207-Feature-Refinement-RC1.apk') == PARENT_APK, 'Locked APK drift')
    exported = WORK / 'cobra-207-delivery/replica-1/Cobra-2103207-Generated-Android-Source.zip'
    require(sha(exported) == PARENT_SOURCE, 'Locked source archive drift')
    with zipfile.ZipFile(exported) as archive:
        inventory = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if not name.endswith('/')}
    require(len(inventory) == 226, 'Locked inventory drift')
    for directory in (PARENT, CANDIDATE):
        actual = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()}
        require(actual == set(inventory), 'Source files added/removed outside approved existing identities: ' + repr(actual ^ set(inventory)))
    files, binary, patch = {}, {}, ''
    for name, digest in sorted(inventory.items()):
        before, after = PARENT / name, CANDIDATE / name
        require(sha(before) == digest, 'Local immutable baseline drift: ' + name)
        if sha(after) == digest:
            continue
        require(name in ALLOWED_JAVA | set(ICON_SLOTS) | {GRADLE}, 'Source outside approved scope: ' + name)
        files[name] = dict(before=digest, after=sha(after))
        if name in ICON_SLOTS:
            binary[name] = base64.b64encode(after.read_bytes()).decode()
        else:
            patch += ''.join(difflib.unified_diff(before.read_text().splitlines(True), after.read_text().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
    require(GRADLE in files, 'Candidate must receive a new version identity before freeze')
    expected_gradle = (PARENT / GRADLE).read_text().replace('versionCode 2103207', 'versionCode 2103208').replace(OLD, NEW)
    require((CANDIDATE / GRADLE).read_text() == expected_gradle, 'Gradle changed outside release identity')
    (ROOT / 'features.patch').write_text(patch)
    (ROOT / 'asset-payloads.json').write_text(json.dumps(binary, indent=2) + '\n')
    with tempfile.TemporaryDirectory(prefix='cobra208-patch-') as temporary:
        tree = Path(temporary)
        for name in files:
            if name in ICON_SLOTS:
                continue
            (tree / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PARENT / name, tree / name)
        subprocess.run(['git', 'apply', '--check', str(ROOT / 'features.patch')], cwd=tree, check=True)
        subprocess.run(['git', 'apply', str(ROOT / 'features.patch')], cwd=tree, check=True)
        require(all(sha(tree / name) == row['after'] for name, row in files.items() if name not in ICON_SLOTS), 'Patch result differs from candidate')
    parser = module('parent_member_parser', WORK / 'cobra-ci-inputs/audit206/repairs/cobra-original-player-menu-2103197/apply.py')
    old_protected = json.loads((PARENT_EVIDENCE / 'protected-members.json').read_text())
    require(len(old_protected) == 49, 'Immutable protected inventory drift')
    before, after = (PARENT / ACTIVITY).read_text(), (CANDIDATE / ACTIVITY).read_text()
    protected = {}
    for name, digest in old_protected.items():
        kind = 'class' if name.startswith('Cobra') else 'method'
        original = parser.member(before, name, kind) if kind == 'class' else parser.member(before, name)
        candidate = parser.member(after, name, kind) if kind == 'class' else parser.member(after, name)
        require(hashlib.sha256(original.encode()).hexdigest() == digest, 'Immutable protected hash differs: ' + name)
        require(original == candidate, 'Protected source member changed: ' + name)
        protected[name] = dict(kind=kind, sha256=digest)
    (ROOT / 'protected-members.json').write_text(json.dumps(protected, indent=2) + '\n')
    slots = resource_slots((WORK / 'cobra-207-delivery/replica-1/base-resources.txt').read_text())
    resources = []
    with zipfile.ZipFile(WORK / 'Cobra-2103207-Feature-Refinement-RC1.apk') as apk:
        for name in sorted(binary):
            slot = ICON_SLOTS[name]
            require(slot in slots, 'Missing named existing resource: ' + repr(slot))
            entry = slots[slot]
            old, new = apk.read(entry), (CANDIDATE / name).read_bytes()
            require(png_size(old) == png_size(new), 'Branding dimension change: ' + name)
            resources.append(dict(source=name, slot=list(slot), entry=entry,
                                  before=hashlib.sha256(old).hexdigest(), after=hashlib.sha256(new).hexdigest(), dimensions=png_size(new)))
    validate_rows(resources)
    (ROOT / 'approved-resources.json').write_text(json.dumps(resources, indent=2) + '\n')
    cases = {}
    for path in sorted((ROOT / 'tests').glob('*.java')):
        owner = 'com.projectinfinity.kodi.' + path.stem
        names = re.findall(r'@Test\b(?:(?!@Test).)*?public void (\w+)\s*\(', path.read_text(), re.S)
        require(names and len(names) == len(set(names)), 'Invalid new test inventory: ' + path.name)
        cases[owner] = sorted([[owner, name] for name in names])
    require(bool(cases), 'No new behavior tests')
    (ROOT / 'new-cases.json').write_text(json.dumps(cases, indent=2) + '\n')
    (ROOT / 'infinity-2103208-integration-polish.yml').write_text(workflow())
    recipe = {str(path.relative_to(ROOT)): sha(path) for path in ROOT.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.name not in ('reviewed.json', 'publish-tree.json') and path.suffix != '.pyc'}
    (ROOT / 'reviewed.json').write_text(json.dumps(dict(parent_commit=PARENT_COMMIT, parent_apk_sha256=PARENT_APK,
        parent_source_sha256=PARENT_SOURCE, parent_inventory=inventory, files=files, recipe_hashes=recipe), indent=2) + '\n')
    tree = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.name == 'publish-tree.json' or path.suffix == '.pyc':
            continue
        relative = str(path.relative_to(ROOT))
        tree.append(dict(path=RECIPE_PATH + '/' + relative, mode='100644', type='blob', content=path.read_text()))
        if path.suffix == '.yml':
            tree.append(dict(path='.github/workflows/' + path.name, mode='100644', type='blob', content=path.read_text()))
    (ROOT / 'publish-tree.json').write_text(json.dumps(tree))
    print(json.dumps(dict(parent_files=len(inventory), changed_files=len(files), png_resources=len(resources), protected_members=len(protected), new_tests=sum(map(len, cases.values())), published_files=len(tree))))

if __name__ == '__main__':
    main()
