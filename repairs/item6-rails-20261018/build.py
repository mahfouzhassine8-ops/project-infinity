#!/usr/bin/env python3
"""#6 only: hash-pinned Rails 0.2.6 and approved skin .228 -> Rails 0.2.7.

Mocha checked skin/unified/InfinityRailsOptions.xml but passed Rails' addon
root to WindowXMLDialog. That root lacks a script-owned Kodi XML resource.
Copy the exact approved skin layout into the expected helper resource path,
preflight it at runtime, and preserve the original safe Dialog.select fallback.
No keymap, native code, other add-on, profile, Cobra, or Store modification.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

RAILS_SHA='5e4ff64592d6f8660d17db1077ed85a368c02f4eb14442760797b1d133c08179'
SKIN_SHA='39f8f041376748fbe209868a33ef51e1cfd59082ee6ebb8ad095e6f85336bdef'
MOCHA_SHA='8509e5ec32eb377577b7bce500e54112d1c048b6bcb68114c0a3f6f107ec17fa'
XML_SHA='351a03286dd4e5b3d82dcba01974bdc5af082de3fb348bd581c2c0b70586e5ab'
ROOT='script.infinity.rails/'
RESOURCE=ROOT+'resources/skins/Default/720p/InfinityRailsOptions.xml'
MOCHA=ROOT+'resources/lib/mocha.py'
MANIFEST=ROOT+'addon.xml'
OLD="""        if version < (1,0,5,222) or not (base/'unified'/'InfinityRailsOptions.xml').is_file():
            raise RuntimeError('Mocha skin 1.0.5.222 is not installed')
        window=OptionsWindow('InfinityRailsOptions.xml',str(helper_path),'Default','720p')"""
NEW="""        approved = base/'unified'/'InfinityRailsOptions.xml'
        packaged = Path(helper_path)/'resources'/'skins'/'Default'/'720p'/'InfinityRailsOptions.xml'
        if version < (1,0,5,222) or not approved.is_file():
            raise RuntimeError('Mocha skin 1.0.5.222 is not installed')
        # WindowXMLDialog resolves the resource under the script's add-on
        # directory, not from the already-checked active skin/unified path.
        # Refuse a blank custom dialog and retain the original safe chooser.
        if not packaged.is_file() or packaged.read_bytes() != approved.read_bytes():
            raise RuntimeError('Mocha Rails XML missing or differs from the active skin')
        window=OptionsWindow('InfinityRailsOptions.xml',str(helper_path),'Default','720p')"""

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def correct_mocha(raw):
    if digest(raw)!=MOCHA_SHA or raw.count(OLD.encode())!=1:
        raise ValueError('Rails Mocha source preimage mismatch; refusing change')
    fixed=raw.replace(OLD.encode(),NEW.encode(),1)
    if fixed.replace(NEW.encode(),OLD.encode(),1)!=raw:
        raise ValueError('Rails Mocha diff out of scope')
    compile(fixed,MOCHA,'exec')
    return fixed

def build(rails,skin,target):
    rails=Path(rails);skin=Path(skin);target=Path(target)
    if digest(rails.read_bytes())!=RAILS_SHA:
        raise ValueError('Wrong approved Rails 0.2.6 parent ZIP')
    if digest(skin.read_bytes())!=SKIN_SHA:
        raise ValueError('Wrong approved skin 1.0.5.228 ZIP')
    with zipfile.ZipFile(rails) as before,zipfile.ZipFile(skin) as source:
        names=before.namelist()
        if before.testzip() is not None or len(names)!=14 or len(set(names))!=14 or RESOURCE in names:
            raise ValueError('Unexpected protected Rails member list')
        if source.testzip() is not None or len(set(source.namelist()))!=len(source.namelist()):
            raise ValueError('Unexpected skin source integrity')
        layout=source.read('skin.infinity.diggz/unified/InfinityRailsOptions.xml')
        layout_names=[n for n in source.namelist() if n.endswith('/InfinityRailsOptions.xml')]
        if len(layout_names)!=14 or any(source.read(n)!=layout for n in layout_names):
            raise ValueError('Fold rail layouts differ; no silent visual substitution')
        if digest(layout)!=XML_SHA or ET.fromstring(layout).tag!='window':
            raise ValueError('Approved skin XML mismatch')
        manifest=before.read(MANIFEST)
        if manifest.count(b'version="0.2.6"')!=1:
            raise ValueError('Unexpected original Rails version')
        changes={MOCHA:correct_mocha(before.read(MOCHA)),
                 MANIFEST:manifest.replace(b'version="0.2.6"',b'version="0.2.7"',1)}
        target.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(target,'w',allowZip64=True) as after:
            for info in before.infolist():
                after.writestr(copy.copy(info),changes.get(info.filename,before.read(info)))
            after.writestr(RESOURCE,layout,compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(rails) as before,zipfile.ZipFile(target) as after:
        if after.testzip() is not None or after.namelist()!=before.namelist()+[RESOURCE]:
            raise ValueError('Missing/reordered Rails members')
        changed=[n for n in before.namelist() if before.read(n)!=after.read(n)]
        if set(changed)!=set(changes):
            raise ValueError('Unauthorized change to protected Rails files')
        if after.read(RESOURCE)!=layout:
            raise ValueError('Mocha XML differs from approved skin')
        manifest=ET.fromstring(after.read(MANIFEST))
        if (manifest.get('id'),manifest.get('version'))!=('script.infinity.rails','0.2.7'):
            raise ValueError('Wrong Rails addon identity')
    receipt=dict(requirement=6,component='script.infinity.rails',version='0.2.7',
        file=target.name,sha256=digest(target.read_bytes()),
        parent_zip_sha256=RAILS_SHA,approved_skin_sha256=SKIN_SHA,
        original_members_preserved=14,unchanged_members=12,
        changed_members=sorted(changes),added_resource=RESOURCE,removed_members=[],
        keymap_changed=False,native_engine_changed=False,store_changed=False,
        cobra_changed=False,physical_fold_verified=False,final_apk=False,
        prior_item4_version_guard_requires_approval=True)
    target.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--rails',type=Path,required=True)
    p.add_argument('--skin',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    build(a.rails,a.skin,a.out)
