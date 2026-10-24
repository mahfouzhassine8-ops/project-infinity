"""Verify the exact signed CC34 QA reference before extending its source layer."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
APK = '5c331c1a7d365fe5cc80f206d78a9eef57035cfda3e24f44d4093e330df054af'
COMMIT = 'c0dba465e6b74af7bd82ea0c16755d5bf7508f1e'
BUILD = '40086558043'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
VERSIONS = {'script.infinity.commandcenter': '0.3.5.34',
            'script.infinity.watchedbridge': '1.0.15',
            'script.infinity.uirepair': '0.1.17', 'skin.infinity.diggz': '1.0.5.241'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(folder, tools):
    folder, tools = Path(folder), Path(tools)
    apks = list(folder.glob('*.apk'))
    if len(apks) != 1:
        raise RuntimeError('Exactly one signed CC34 reference APK required')
    apk = apks[0]
    with apk.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != APK:
            raise RuntimeError('Signed CC34 reference APK differs')
    candidate = json.loads((folder / 'CANDIDATE.json').read_text())
    expected = {'apk_sha256': APK, 'source_commit': COMMIT, 'build_run': BUILD,
                'permanent_certificate_sha256': CERT, 'version_code': 2103401,
                'matching_component_versions': VERSIONS}
    if any(candidate.get(k) != v for k, v in expected.items()):
        raise RuntimeError('Signed CC34 lineage receipt differs')
    signature = subprocess.check_output([str(tools / 'apksigner'), 'verify', '--verbose',
                                        '--print-certs', str(apk)], text=True)
    certs = re.findall(r'Signer #\d+ certificate SHA-256 digest:\s*([0-9a-f:]+)', signature, re.I)
    if len(certs) != 1 or certs[0].lower().replace(':', '') != CERT:
        raise RuntimeError('Signed CC34 permanent certificate differs')
    for version in (1, 2, 3):
        if not re.search(r'Verified using v' + str(version) + r' scheme[^\n]*:\s*true', signature, re.I):
            raise RuntimeError('Signed CC34 signature scheme failed')
    subprocess.run([str(tools / 'zipalign'), '-c', '-p', '4', str(apk)], check=True)
    baseline = json.loads((HERE / 'BASE34-CONTROLLER-PINS.json').read_text())
    if len(baseline) != 24:
        raise RuntimeError('Exact CC34 named source inventory required')
    component_hashes = {}
    with ZipFile(apk) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise RuntimeError('Duplicate signed CC34 APK members')
        for addon, version in VERSIONS.items():
            path = folder / (addon + '-' + version + '.zip')
            component_hashes[path.name] = sha(path.read_bytes())
            with ZipFile(path) as component:
                names = {n for n in component.namelist() if not n.endswith('/')}
                if len(component.namelist()) != len(set(component.namelist())):
                    raise RuntimeError('Duplicate reference component members')
                expected_names = {n[len('assets/addons/'):] for n in archive.namelist()
                                  if n.startswith('assets/addons/' + addon + '/') and not n.endswith('/')}
                if names != expected_names:
                    raise RuntimeError('Reference ZIP member inventory differs: ' + addon)
                if any(component.read(n) != archive.read('assets/addons/' + n) for n in names):
                    raise RuntimeError('Reference ZIP differs from signed APK: ' + addon)
            xml = archive.read('assets/addons/' + addon + '/addon.xml')
            if ET.fromstring(xml).get('version') != version:
                raise RuntimeError('Reference component version differs: ' + addon)
        for consumer in ('script.infinity.uirepair', 'script.infinity.watchedbridge'):
            if json.loads(archive.read('assets/addons/' + consumer + '/CONTROLLER-PREIMAGES.json')) != baseline:
                raise RuntimeError('Signed CC34 controller admission differs')
        if any(sha(archive.read('assets/addons/script.infinity.commandcenter/' + n)) != h
               for n, h in baseline.items()):
            raise RuntimeError('Signed CC34 source pin differs')
    return dict(expected, signature_schemes_verified=[1, 2, 3],
                component_zip_sha256=component_hashes, exact_CC34_sources_verified=24,
                actual_android_verified=False, physical_fold_verified=False)
