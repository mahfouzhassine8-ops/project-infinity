"""Verify a proposed source overlay, without constructing an APK or component."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as E
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
PREFIX = 'assets/addons/skin.infinity.diggz/'
APK_SHA = '08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8'
ENGINE_SHA = 'd0b6f115e839fbe39e764e2fecad47418c501ab1ece853294578652cd0b80b98'
ALLOWED = {PREFIX + n for n in (
    'unified/Includes.xml', 'unified/MyVideoNav.xml', 'unified/Custom_1198_InfinityNav.xml',
    'unified/custom_1136_InfinityVideoViews.xml', 'unified/custom_1137_InfinityVideoViewSettings.xml',
    'unified/custom_1138_InfinityVideoDisableViews.xml', 'unified/Includes_InfinityVideoOptions.xml',
    'resources/lib/infinity_library_navigation.py')}
ALLOWED |= {'assets/addons/script.infinity.commandcenter/' + n
            for n in ('service.py', 'media_view.py')}


def sha(data):return hashlib.sha256(data).hexdigest()


def main(apk, out):
    with apk.open('rb') as f:apk_hash = hashlib.file_digest(f, 'sha256').hexdigest()
    assert apk_hash == APK_SHA, 'Signed source APK changed'
    plan = json.loads((HERE / 'SOURCE-PLAN.json').read_text())
    root = HERE / 'overlay'
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    assert set(files) == ALLOWED == set(plan['changes']), 'Unexpected source member'
    with ZipFile(apk) as z:
        for name, digest in plan['preimages'].items():
            assert sha(z.read(name)) == digest, 'Preimage mismatch: ' + name
        changes = []
        names = set(z.namelist())
        for name, p in sorted(files.items()):
            data = p.read_bytes()
            before = sha(z.read(name)) if name in names else None
            after = sha(data)
            assert before == plan['changes'][name]['before']
            assert after == plan['changes'][name]['after']
            assert before != after
            if name.endswith('.xml'):E.fromstring(data)
            else:compile(data, name, 'exec')
            changes.append({'member': name, 'baseline_sha256': before, 'source_sha256': after})
        with z.open('lib/arm64-v8a/libkodi.so') as f:
            engine = hashlib.file_digest(f, 'sha256').hexdigest()
        assert engine == ENGINE_SHA
        other = sorted(n for n in names if n not in files and not n.endswith('/'))
        native = [n for n in other if n.startswith('lib/')]
        dex = [n for n in other if n.endswith('.dex')]
        # No new installable artifact exists. These are protected baseline
        # inventory counts excluded from the proposed source-member overlay.
        result = {
            'status': 'PASS_SOURCE_SCOPE_ONLY', 'signed_apk_sha256': apk_hash,
            'native_engine_sha256': engine, 'source_members': changes,
            'existing_members_modified': sum(c['baseline_sha256'] is not None for c in changes),
            'new_source_members': sum(c['baseline_sha256'] is None for c in changes),
            'protected_original_member_count': len(other),
            'protected_dex_count': len(dex), 'protected_native_count': len(native),
            'new_apk_built': False, 'actual_candidate_apk_comparison': 'NOT APPLICABLE: source-only',
            'android_runtime': 'NOT RUN', 'physical_fold': 'PENDING',
            'original_visual_evidence': 'INACCESSIBLE',
        }
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'source_members'}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apk', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args();main(a.apk, a.out)
