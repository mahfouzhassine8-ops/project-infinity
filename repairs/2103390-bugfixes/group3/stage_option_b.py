#!/usr/bin/env python3
"""Read-only proof & separate staging of Group #3's Option B modal components.

Never installs, packages, signs, or alters the immutable 2103390 APK. The
native Group3 source overlay provides the constrained gesture dispatch;
this stage validates its two additive UI assets and one runtime action hook.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
from runtime_option_b_patch import patch_runtime, ENTRY as RUNTIME_ENTRY

PARENT_SHA256 = '778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb'
PARENT_MEMBERS = 7430
ADDON_PREFIX = 'assets/addons/script.infinity.uirepair/'
NEW_FILES = {
    ADDON_PREFIX+'home_option_b.py':'home_option_b.py',
    ADDON_PREFIX+'resources/skins/Default/1080i/InfinityHomeOptionB.xml':'InfinityHomeOptionB.xml',
}
EXISTING_HASHES = {
    ADDON_PREFIX+'addon.xml': '802e311aca8428da0cc69b2adb37635fb1d255625f2dee269b1c928eee576677',
    ADDON_PREFIX+'runtime.py':'c45b4aa5e13bac125b9b7722472d00b33769fec4961767025ef649b7e457f7fd',
    ADDON_PREFIX+'popup.py':'2f365a992a864391e2c938c4440c0c36c8ed2887b1ef702449cb507bc3662246',
}
HOME_PANELS = ('8101','8102')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(original: Path, source_dir: Path) -> dict:
    original,source_dir = Path(original),Path(source_dir)
    if digest(original.read_bytes()) != PARENT_SHA256:
        raise ValueError('Refusing a different or modified 2103390 signed APK')
    new = {n:(source_dir/source).read_bytes() for n,source in NEW_FILES.items()}
    edited_runtime = None
    with zipfile.ZipFile(original) as z:
        names = z.namelist()
        if len(names) != PARENT_MEMBERS or len(set(names)) != PARENT_MEMBERS:
            raise ValueError('Unexpected original signed members')
        if any(n in names for n in NEW_FILES):
            raise ValueError('Option B components already present in original package')
        for name,want in EXISTING_HASHES.items():
            if digest(z.read(name)) != want:
                raise ValueError('Original first-party UI Repair dependency changed: '+name)
        edited_runtime = patch_runtime(z.read(RUNTIME_ENTRY))
        if edited_runtime == z.read(RUNTIME_ENTRY):
            raise ValueError('Missing Option B script action integration')
        homes=[n for n in names if n.startswith('assets/addons/skin.infinity.diggz/') and n.endswith('/Home.xml')]
        if len(homes) != 14:
            raise ValueError('Missing original 14 Home variant baselines')
        from xml.etree import ElementTree as ET
        for home in homes:
            root=ET.fromstring(z.read(home))
            for cid in HOME_PANELS:
                widget=root.find(f".//control[@id='{cid}']")
                if widget is None or widget.get('type')!='panel':
                    raise ValueError('Original provider Home top rail missing: '+home+' '+cid)
                if widget.find('onclick') is not None:
                    raise ValueError('Original top tap already overridden: '+home+' '+cid)
        for n in new:
            if not n.startswith(ADDON_PREFIX) or 'cobra' in n.lower():
                raise ValueError('Out-of-Group #3 output path')
        return dict(signed_parent_sha256=PARENT_SHA256,
                    original_members=len(names),original_members_unchanged=len(names)-1,
                    proposed_added_members=len(new),modified_members=1,removed_members=0,
                    candidate_total_members=len(names)+len(new),
                    proposed_additions=[{'path':n,'sha256':digest(b),'size':len(b)} for n,b in sorted(new.items())],
                    original_home_variants_unchanged=len(homes),
                    proposed_modified=[{'path':RUNTIME_ENTRY,
                                        'before_sha256':digest(z.read(RUNTIME_ENTRY)),
                                        'after_sha256':digest(edited_runtime)}],
                    native_input_dispatch='SOURCE_PATCHED_NO_ANDROID_COMPILE',
                    runtime_action_dispatch='GUARDED_OPTION_B_REGISTERED_IN_PROPOSED_RUNTIME',
                    ready_for_signed_apk=False,physical_fold_verified=False)


def stage(original: Path, source_dir: Path, dest: Path) -> dict:
    original,source_dir,dest=Path(original).resolve(),Path(source_dir).resolve(),Path(dest).resolve()
    if dest == original.parent or original.is_relative_to(dest) or dest.is_relative_to(source_dir):
        raise ValueError('Refusing input/source overwrite or adjacent staging')
    result = audit(original,source_dir)  # fail closed BEFORE writing output
    for name,source in NEW_FILES.items():
        output=dest/name
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes((source_dir/source).read_bytes())
    with zipfile.ZipFile(original) as z:
        runtime = patch_runtime(z.read(RUNTIME_ENTRY))
    output=dest/RUNTIME_ENTRY
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(runtime)
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('original_apk',type=Path)
    p.add_argument('source_dir',type=Path);p.add_argument('--stage-to',type=Path)
    args=p.parse_args()
    result=(stage(args.original_apk,args.source_dir,args.stage_to) if args.stage_to
            else audit(args.original_apk,args.source_dir))
    print(json.dumps(result,indent=2))
