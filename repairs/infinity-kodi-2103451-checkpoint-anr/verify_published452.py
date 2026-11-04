"""Bind actual downloaded signed452 and published owner ZIPs to official CI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile
import release452 as r
from component_bundles import read_bundle

RUN = 41742368066
SOURCE = 'f5b6dbb22bfa0f0ee3d540f7566baa06128e07ac'


def one(root, name):
    found = list(root.rglob(name)); r.require(len(found) == 1, 'ONE_PUBLISHED_FILE:' + name)
    return found[0]


def verify(signed, components, baseline, out):
    run = json.loads(r.cmd('gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/' + str(RUN)))
    r.require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == SOURCE
              and run['head_branch'] == r.BRANCH and run['path'] == '.github/workflows/infinity-combined-release.yml',
              'OFFICIAL_COMPLETED_SIGNING_RUN')
    apk = one(signed, 'Infinity-2103452-Combined-Original-Signer.apk')
    receipt = r.load(one(signed, 'BUILD-RECEIPT.json'))
    r.require(receipt['source'] == SOURCE and receipt['versionCode'] == r.VERSION and
              receipt['certificate_sha256'] == r.CERT_SHA and receipt['signed_apk_sha256'] == r.file_sha(apk)
              and receipt['physical_Fold'] == 'PENDING' and receipt['accepted_pointer_updated'] is False,
              'ACTUAL_APK_SIGNER_SOURCE_BINDING')
    signature = (signed / 'SIGNATURE.txt').read_text()
    r.require(re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]{64})', signature) == [r.CERT_SHA],
              'ORIGINAL_CERTIFICATE_EVIDENCE')
    for scheme in ('v1','v2','v3'):
        r.require(re.search('Verified using ' + scheme + r' scheme[^\n]*: true', signature) is not None,
                  'ORIGINAL_SDK_SIGNATURE_SCHEME:' + scheme)
    authority_path = one(signed, 'release-authority.json')
    r.require(authority_path.read_bytes() == __import__('subprocess').check_output(
        ['git','show',SOURCE+':'+str(r.AUTH.relative_to(r.REPO))]), 'PUBLISHED_SOURCE_AUTHORITY_EXACT')
    authority = r.load(authority_path)
    r.require(authority['owner_update_evidence']['Android'] == r.RUNTIME and
              authority['owner_update_evidence']['unknown_obligations'] == 'REMAIN_BLOCKING',
              'TRUTHFUL_PENDING_STATUS')
    status = r.load(one(signed, 'VERIFICATION-STATUS.json'))
    r.require(status['Android'] == r.RUNTIME and status['physical_Fold'] == 'PENDING' and
              status['application_tests_run_in_packaging'] is False and
              status['shutdown_tests_run_in_packaging'] is False and status['accepted_pointer_updated'] is False,
              'NO_FABRICATED_RUNTIME_OR_ACCEPTANCE')
    report = r.compare(baseline, apk, out)
    hashes = r.load(out / 'ALL-APK-MEMBER-HASHES.json')
    catalog = r.load(components / 'catalog.json')
    r.require(catalog == authority['bundle_catalog'], 'PUBLISHED_CATALOG_EXACT')
    metas = {}; component_report = {}
    for owner, row in catalog['bundles'].items():
        path = components / row['file']; meta = read_bundle(path, row); metas[owner] = meta
        with ZipFile(path) as z, ZipFile(apk) as app:
            r.require(z.testzip() is None, 'COMPONENT_CRC:' + owner)
            for name, entry in meta['members'].items():
                if name == 'AndroidManifest.xml':
                    r.require(r.normalize_manifest(z.read('payload/' + name))[0] ==
                              r.normalize_manifest(app.read(name))[0], 'VERSION_ONLY_COMPONENT_MANIFEST')
                else:
                    r.require(hashes[name]['after'] == entry['sha256'], 'COMPONENT_APK_MEMBER:' + name)
        component_report[owner] = dict(sha256=r.file_sha(path), matched_payload_members=len(meta['members']),
                                      matched_dex_partitions=len(meta['dex']))
    order = {o:i for i,o in enumerate(('CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA'))}
    dex = sorted(((owner,name) for owner,m in metas.items() for name in m['dex']), key=lambda x:(order[x[0]],x[1]))
    for index,(owner,name) in enumerate(dex,1):
        actual = 'classes' + (str(index) if index > 1 else '') + '.dex'
        r.require(hashes[actual]['after'] == metas[owner]['dex'][name], 'COMPONENT_APK_DEX:' + actual)
    prior = r.previous()
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
        r.require(component_report[owner]['sha256'] == prior['bundle_catalog']['bundles'][owner]['sha256'],
                  'FROZEN_EXACT_COMPONENT_ZIP:' + owner)
    sums = r.file_sha(apk) + '  ' + apk.name + '\n'
    sums += ''.join(component_report[o]['sha256'] + '  ' + catalog['bundles'][o]['file'] + '\n'
                    for o in ('INFINITY','COBRA','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT'))
    (out / 'SHA256SUMS').write_text(sums)
    r.save(out / 'PUBLISHED452-VERIFICATION.json', dict(
        status='PASS_PUBLISHED_SIGNED_APK_AND_ALL_COMPONENT_BYTES',versionCode=r.VERSION,package='com.projectinfinity.kodi',
        source_commit=SOURCE,signing_run=RUN,apk_sha256=r.file_sha(apk),certificate_sha256=r.CERT_SHA,
        original_SDK_signature_schemes=['v1','v2','v3'],published_components=component_report,
        member_preservation=report,native_sha256=r.NATIVE_SHA,native_build_source=r.NATIVE_SOURCE,
        native_build_run=r.NATIVE_RUN,Android=r.RUNTIME,physical_Fold='PENDING',
        historical_watched_route='UNKNOWN',unknown_obligations='REMAIN_BLOCKING',accepted_pointer_updated=False))
    print(json.dumps(dict(version=r.VERSION,apk_sha256=r.file_sha(apk),components=component_report,
                         Android=r.RUNTIME,physical_Fold='PENDING'),indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('signed','components','baseline','out'):p.add_argument('--'+name,type=Path,required=True)
    verify(**vars(p.parse_args()))
