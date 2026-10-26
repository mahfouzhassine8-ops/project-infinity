"""Metadata-only bridge for the actual signed internal408 APK; no byte changes."""
import json
import os
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from candidate_request import EXPECTED,validate
from prepare_signed407_fixture import digest


def prepare(root,request,baseline):
    validate(request)
    root=Path(root);baseline=Path(baseline)
    outputs=('CANDIDATE.json','SHA256SUMS','FIXTURE-METADATA-EVIDENCE.json')
    if any((root/n).exists() for n in outputs):raise ValueError('Existing fixture metadata must not be replaced')
    apks=list(root.rglob('*.apk'));reports=list(root.rglob('APK-PRESERVATION.json'))
    if len(apks)!=1 or len(reports)!=1 or digest(apks[0])!=EXPECTED['candidate_apk_sha256']:
        raise ValueError('Exact signed409APK andpreservationrecord required')
    report=json.loads(reports[0].read_text())
    if (report['source_commit']!=EXPECTED['candidate_source_commit'] or report['build']!=str(EXPECTED['candidate_build']) or
        report['candidate_APK_sha256']!=EXPECTED['candidate_apk_sha256'] or report['unexpected_differences']!=[] or
        report['original_certificate_sha256']!='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'):
        raise ValueError('Candidate source/packagepreservation binding differs')
    if digest(baseline)!='fc1d726fee8002da7cdccec6dd79a029f6536f0f1c3857791bec94c45d620e50':
        raise ValueError('Physicallytested408install-over baseline differs')
    sources={apks[0].name:apks[0]}
    for name,wanted in report['component_sha256'].items():
        found=list(root.rglob(name))
        if len(found)!=1 or digest(found[0])!=wanted:raise ValueError('Matchingcomponent differs: '+name)
        sources[name]=found[0]
    expected={'script.infinity.commandcenter':'0.3.5.41','script.infinity.uirepair':'0.1.23',
              'script.infinity.watchedbridge':'1.0.21','script.infinity.rails':'0.2.8'}
    with ZipFile(apks[0]) as archive:
        versions={aid:ET.fromstring(archive.read('assets/addons/'+aid+'/addon.xml')).get('version') for aid in expected}
    if versions!=expected:raise ValueError('Actualpackagedmodule versions differ')
    for name,path in sources.items():
        if path.parent==root or (root/name).exists():raise ValueError('Unexpected existing flatcandidate input')
    for name,path in sources.items():os.link(path,root/name)
    receipt=dict(source_commit=EXPECTED['candidate_source_commit'],apk_sha256=EXPECTED['candidate_apk_sha256'],
        matching_component_versions=versions,apk_bytes_changed=False,physical_fold_verified=False,release_accepted=False,
        protected_installover_baseline_sha256=digest(baseline),purpose='Featurefixturemetadata only; originalSDKsignature/source gates mandatory')
    (root/'CANDIDATE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (root/'SHA256SUMS').write_text(''.join(digest(path)+'  '+name+'\n' for name,path in sorted(sources.items())))
    (root/'FIXTURE-METADATA-EVIDENCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    import sys
    root=Path(sys.argv[1]);baseline=next(Path(sys.argv[2]).rglob('Infinity-2103408-Integrated-INTERNAL-VERIFICATION.apk'))
    request=json.loads(Path(os.environ['CANDIDATE_REQUEST_PATH']).read_text())
    print(json.dumps(prepare(root,request,baseline),indent=2))
    with Path(os.environ['GITHUB_ENV']).open('a') as output:output.write('TEST_BASELINE_APK='+str(baseline)+'\n')
