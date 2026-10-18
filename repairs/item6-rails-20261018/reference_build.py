#!/usr/bin/env python3
"""#6 fallback SOURCE INPUT ONLY: exact signed Rails .026 members from 2103388.

Never build from the rejected all-in-one APK. Read only its 14 verified Rails
source members, whose original standalone ZIP SHA is preserved in its pinned
FULL-STACK-INPUTS receipt. Emit only a new, separate Rails 0.2.7 helper ZIP.
No other APK components, Cobra, skin, runtime settings, keymaps or data reused.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('item6_original_pin',HERE/'build.py')
pinned=importlib.util.module_from_spec(spec);spec.loader.exec_module(pinned)
APK_SHA='500b9e6824f45d0d34e871aa1d480f2fc21642b67b9bb21b34c5422a5179009b'
ROOT='assets/addons/script.infinity.rails/'
NAMES=frozenset((
    'addon.xml','context_add.py','default.py','plugin.py',
    'resources/defaults.xml',
    'resources/language/resource.language.en_gb/strings.po',
    'resources/lib/__init__.py','resources/lib/catalog.py',
    'resources/lib/dialog.py','resources/lib/input_status.py',
    'resources/lib/mocha.py','resources/lib/runtime.py',
    'resources/lib/stability_probe.py','resources/lib/store.py'
))

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(apk,provenance,skin,target):
    apk,provenance,skin,target=map(Path,(apk,provenance,skin,target))
    if digest(apk.read_bytes())!=APK_SHA:
        raise ValueError('Signed 2103388 reference SHA mismatch; nothing can be built')
    proof=json.loads(provenance.read_text())
    if proof.get('rails_sha256')!=pinned.RAILS_SHA:
        raise ValueError('Original Rails .026 ZIP receipt SHA mismatch')
    if digest(skin.read_bytes())!=pinned.SKIN_SHA:
        raise ValueError('Approved #1 skin source SHA mismatch')
    with zipfile.ZipFile(apk) as original,zipfile.ZipFile(skin) as approved:
        infos=[i for i in original.infolist() if i.filename.startswith(ROOT)]
        if original.testzip() is not None or len(infos)!=14 or {i.filename[len(ROOT):] for i in infos}!=NAMES:
            raise ValueError('Original Rails content inventory mismatch')
        rawmocha=original.read(ROOT+'resources/lib/mocha.py')
        fixed=pinned.correct_mocha(rawmocha)  # Exact pinned 0.2.6 source hash
        manifest=original.read(ROOT+'addon.xml')
        if manifest.count(b'version="0.2.6"')!=1:
            raise ValueError('Original Rails manifest mismatch')
        layout=approved.read('skin.infinity.diggz/unified/InfinityRailsOptions.xml')
        layoutnames=[n for n in approved.namelist() if n.endswith('/InfinityRailsOptions.xml')]
        if (approved.testzip() is not None or len(layoutnames)!=14 or
                any(approved.read(n)!=layout for n in layoutnames) or
                digest(layout)!=pinned.XML_SHA or ET.fromstring(layout).tag!='window'):
            raise ValueError('Approved Mocha XML/Fold layout mismatch')
        changed={pinned.MOCHA:fixed,
                 pinned.MANIFEST:manifest.replace(b'version="0.2.6"',b'version="0.2.7"',1)}
        target.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(target,'w',allowZip64=True) as out:
            for info in infos:
                name=info.filename[len('assets/addons/'):]
                copyinfo=copy.copy(info);copyinfo.filename=name
                out.writestr(copyinfo,changed.get(name,original.read(info)))
            out.writestr(pinned.RESOURCE,layout,compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(apk) as before,zipfile.ZipFile(target) as after:
        if after.testzip() is not None or len(after.namelist())!=15 or len(set(after.namelist()))!=15:
            raise ValueError('Corrupt/incomplete helper source')
        for name in NAMES:
            targetname=pinned.ROOT+name
            if targetname not in changed and before.read(ROOT+name)!=after.read(targetname):
                raise ValueError('Unapproved replacement of existing Rails member: '+name)
        if after.read(pinned.RESOURCE)!=layout:
            raise ValueError('Mocha layout was changed')
        root=ET.fromstring(after.read(pinned.MANIFEST))
        if (root.get('id'),root.get('version'))!=('script.infinity.rails','0.2.7'):
            raise ValueError('Wrong Rails identity/version')
    receipt=dict(requirement=6,sha256=digest(target.read_bytes()),
        source_signed_apk_sha256=APK_SHA,original_rails_zip_sha256=pinned.RAILS_SHA,
        approved_skin_sha256=pinned.SKIN_SHA,files_retained=14,
        changed_files=sorted(changed),unchanged_files=12,
        added_file=pinned.RESOURCE,deleted_files=[],
        native_or_cobra_files_changed=False,rail_store_changed=False,
        physical_fold_verified=False,final_apk=False,
        item4_version_compatibility_pending=True)
    target.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apk',required=True,type=Path)
    parser.add_argument('--provenance',required=True,type=Path)
    parser.add_argument('--skin',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    a=parser.parse_args()
    build(a.apk,a.provenance,a.skin,a.out)
