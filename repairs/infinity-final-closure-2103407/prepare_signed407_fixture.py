"""Adapt artifact metadata for the existing probe; never alter APK/component bytes."""
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from inspect_signed407 import BASELINE_SHA, EXPECTED_COMPONENTS


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare(root):
    outputs = ('CANDIDATE.json', 'SHA256SUMS', 'FIXTURE-METADATA-EVIDENCE.json')
    if any((root / name).exists() for name in outputs):
        raise ValueError('Refuse to replace existing fixture metadata')
    apks = list(root.rglob('*.apk'))
    if len(apks) != 1 or digest(apks[0]) != BASELINE_SHA:
        raise ValueError('Exact permanently signed407 baseline required')
    apk = apks[0]
    sources = {apk.name: apk}
    for name, wanted in EXPECTED_COMPONENTS.items():
        matches = list(root.rglob(name))
        if len(matches) != 1 or digest(matches[0]) != wanted:
            raise ValueError('Matching component differs: ' + name)
        sources[name] = matches[0]
    with ZipFile(apk) as archive:
        versions = {name: ET.fromstring(archive.read('assets/addons/'+name+'/addon.xml')).get('version')
                    for name in ('script.infinity.commandcenter', 'script.infinity.uirepair',
                                 'script.infinity.watchedbridge')}
    expected = {'script.infinity.commandcenter':'0.3.5.39', 'script.infinity.uirepair':'0.1.22',
                'script.infinity.watchedbridge':'1.0.20'}
    if versions != expected:
        raise ValueError('Signed407 component version mismatch')
    for name, source in sources.items():
        if source.parent == root:
            raise ValueError('Unexpected flat407 artifact input')
        os.link(source, root / name)
    receipt = dict(source_commit='0e8739d2d0e1be0ab8f127519b526556426fb160',
                   apk_sha256=BASELINE_SHA, matching_component_versions=versions,
                   fixture_metadata_from_locked_artifact=True, apk_bytes_changed=False,
                   purpose='Existing probe metadata compatibility only; no test result',
                   physical_fold_verified=False, release_accepted=False)
    (root / 'CANDIDATE.json').write_text(json.dumps(receipt, indent=2)+'\n')
    hashes = dict(EXPECTED_COMPONENTS, **{apk.name:BASELINE_SHA})
    (root / 'SHA256SUMS').write_text(''.join(hashes[name]+'  '+name+'\n' for name in sorted(hashes)))
    (root / 'FIXTURE-METADATA-EVIDENCE.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    import sys
    print(json.dumps(prepare(Path(sys.argv[1])), indent=2))
