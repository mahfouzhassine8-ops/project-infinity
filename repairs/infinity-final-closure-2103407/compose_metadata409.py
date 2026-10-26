"""Stage the preserved four-ID composition and only three metadata repairs.

Build-only source composition. Signing, APK generation, the authenticated
installed-generation update and Android/Fold acceptance remain separate gates.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import compose_firstparty as original
from patch_result_metadata import patch

CC='script.infinity.commandcenter'
VERSION='0.3.5.41'
SEARCH='f34f14e7103a8451d108061b5b7c0d3450e95ea43f95404ffc61254f4b3bdf2f'
FILES=('infinity_search.py','information.py','title_metadata.py')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def compose(sources,destination):
    destination=Path(destination)
    previous=original.VERSION
    try:
        original.VERSION=VERSION
        report=original.compose(Path(sources),destination)
    finally:original.VERSION=previous
    before=dict(report['source_inventory'])
    if before[CC+'/infinity_search.py']!=SEARCH:
        raise ValueError('The previously verified Search lifetime repair must remain exact')
    changed={}
    for name in FILES:
        file=destination/CC/name;raw=file.read_bytes()
        revised=patch(name,raw,require_preimage=name!='infinity_search.py')
        file.write_bytes(revised)
        changed[CC+'/'+name]=dict(before=digest(raw),after=digest(revised))
    after={p.relative_to(destination).as_posix():digest(p.read_bytes()) for p in destination.rglob('*') if p.is_file()}
    if set(before)!=set(after) or set(name for name in before if before[name]!=after[name])!=set(changed):
        raise ValueError('An unrelated composed source changed')
    if ET.parse(destination/CC/'addon.xml').getroot().get('version')!=VERSION:
        raise ValueError('Corrective component version mismatch')
    for file in destination.rglob('*.py'):compile(file.read_bytes(),str(file),'exec',dont_inherit=True)
    newly_changed=set(changed)-set(report['changed_members'])-set(report['added_members'])
    report['changed_members']=sorted(set(report['changed_members'])|set(changed))
    report['preserved_members']-=len(newly_changed)
    report.update(source_inventory=after,corrective_version=VERSION,metadata_changes=changed,
        metadata_transforms_only=True,installed408_upgrade_verified=False,
        Android17='NOT RUN',physical_Fold='NOT RUN')
    return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('sources',type=Path);parser.add_argument('destination',type=Path)
    args=parser.parse_args();receipt=compose(args.sources,args.destination)
    (args.destination.parent/'METADATA409-COMPOSITION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='source_inventory'},indent=2))
