#!/usr/bin/env python3
"""Package a separate browser-focus candidate, not a Source Select fix ZIP."""
import argparse
from copy import deepcopy
import difflib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from delta import BASELINE_ZIP_SHA256, HERE, TARGET, repair, require, sha

ADDON='skin.infinity.diggz'
VERSION='1.0.5.197'
METADATA={'addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'}


def dump(data):return (json.dumps(data,indent=2,sort_keys=True)+'\n').encode()


def archive_files(path):
    files={}
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None,'ZIP CRC failure')
        for info in z.infolist():
            name=PurePosixPath(info.filename)
            require(not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename,'Unsafe member')
            require(name.parts and name.parts[0]==ADDON,'Wrong add-on root')
            require(not stat.S_ISLNK(info.external_attr>>16),'Symlink ZIP member')
            if info.is_dir():continue
            relative=str(PurePosixPath(*name.parts[1:]))
            require(relative not in files,'Duplicate member')
            files[relative]=z.read(info)
    return files


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    loaded=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    require(sha(args.baseline.read_bytes())==BASELINE_ZIP_SHA256,'Wrong locked 196 ZIP')
    original=archive_files(args.baseline)
    identity=ET.fromstring(original['addon.xml'])
    require(identity.get('id')==ADDON and identity.get('version')=='1.0.5.196','Wrong identity')
    prior=json.loads(original['Infinity-Protected-Manifest.json'])
    for name,h in prior['protected_files'].items():require(sha(original[name])==h,'Stale protected file: '+name)
    candidate=repair(original)
    release=dict(version=VERSION,title='Browser Focus RC1',baseline='exact locked skin 1.0.5.196 / APK 2103305',
                 requires_apk=2103305,profiles=['unified'],native_responsive_marker_enabled=False,
                 status='source/package verified; physical acceptance pending',
                 scope=['stable focused Add-on Browser typography','palette-following focused text and surface','existing cyan focus rim'],
                 source_select_repaired_by_skin=False,back_freeze_resolved=False,shutdown_changed=False,
                 deferred_movie_video_framing_changed=False,physical_device_verified=False)
    addon=original['addon.xml'].decode()
    require(addon.count('version="1.0.5.196"')==1,'Ambiguous version')
    addon=addon.replace('version="1.0.5.196"','version="'+VERSION+'"',1)
    description=('Infinity 1.0.5.197 Browser Focus RC1. Exact skin 196 base; only active AddonBrowser.xml '
                 'presentation refined for stable selected typography, theme-aware text and existing cyan rim. '
                 'All drawer, player, provider, weather, artwork and other profiles preserved. '
                 'This skin ZIP alone does not repair provider Source Select coordinates or Back freezes. '
                 'Source Select native candidate 2103306 requires its separate engine build and device validation.')
    addon,count=re.subn(r'(<description lang="en_GB">).*?(</description>)',lambda m:m[1]+description+m[2],addon,flags=re.S)
    require(count==1,'Ambiguous description')
    candidate['addon.xml']=addon.encode()
    meta=json.loads(original['infinity-skin.json'])
    meta['delivery_197_previous_release']=deepcopy(meta['current_release'])
    meta.update(candidate=197,candidate_name=release['title'],skin_version=VERSION,version=VERSION,
                release=release['title'],current_release=release,requires_apk=2103305,
                candidate_locked=False,physical_device_verified=False)
    candidate['infinity-skin.json']=dump(meta)
    manifest=deepcopy(prior)
    manifest['delivery_197_previous_release']=deepcopy(manifest['current_release'])
    manifest.update(candidate=197,candidate_version=VERSION,skin_version=VERSION,current_release=release,candidate_locked=False)
    for name in manifest['protected_files']:
        require(name!='Infinity-Protected-Manifest.json','Self-referential manifest')
        manifest['protected_files'][name]=sha(candidate[name])
    candidate['Infinity-Protected-Manifest.json']=dump(manifest)
    require(set(candidate)==set(original),'File set changed')
    changed={n for n in original if original[n]!=candidate[n]}
    require(changed=={TARGET}|METADATA,'Unexpected package delta')
    require(ET.fromstring(candidate['addon.xml']).find('./extension[@point="xbmc.gui.skin"]').attrib==
            identity.find('./extension[@point="xbmc.gui.skin"]').attrib,'Skin extension changed')
    xml_count=0
    for name,b in candidate.items():
        if name.endswith('.xml'):ET.fromstring(b);xml_count+=1
    profiles=lambda b:[n.attrib for n in ET.fromstring(b).findall('./extension[@point="xbmc.gui.skin"]/res')]
    require(profiles(candidate['addon.xml'])==profiles(original['addon.xml']),'Profile architecture changed')
    tests=module(HERE/'test_delta.py','browser197tests')
    tests.ORIGINAL={TARGET:original[TARGET]};tests.CANDIDATE={TARGET:candidate[TARGET]}
    suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
    with tempfile.TemporaryDirectory(prefix='infinity-browser197-') as temp:
        skin=Path(temp)/ADDON
        for name,b in candidate.items():
            f=skin/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        parent=module(HERE.parent/'skin-followup-1.0.5.196/test_preserved_contracts.py','preserved196')
        parent.SKIN=skin;suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(parent))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        require(result.wasSuccessful(),'Candidate/preserved contracts failed')
        from PIL import Image
        rim=Image.open(skin/'media/infinity_polish/focus_rim.png').convert('RGBA')
        require(rim.getpixel((rim.width//2,rim.height//2))[3]==0,'Focus rim is filled')
        variables=ET.fromstring(candidate['unified/IncludesVariables.xml'])
        color=lambda name: [v.text for v in variables.findall('./variable[@name="'+name+'"]/value')]
        require(color('InfinityPaletteTextPrimary')==['FF0C2036','FFFFFFFF'],'Unreviewed theme text')
        require(color('InfinityPaletteSurfaceElevated')==['FFF1F6FB','FF000000'],'Unreviewed theme surface')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    output=args.output_dir/(ADDON+'-'+VERSION+'-Browser-Focus-RC1.zip')
    require(not output.exists(),'Refusing to overwrite a deliverable')
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,b in sorted(candidate.items()):
            i=zipfile.ZipInfo(ADDON+'/'+name,(2026,10,4,0,0,0));i.create_system=3
            i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16
            z.writestr(i,b,compresslevel=9)
    require(archive_files(output)==candidate,'Exact archive readback failed')
    patch=''.join(difflib.unified_diff(original[TARGET].decode().splitlines(True),candidate[TARGET].decode().splitlines(True),
                                    fromfile='a/'+ADDON+'/'+TARGET,tofile='b/'+ADDON+'/'+TARGET))
    (args.output_dir/'skin-196-browser.patch').write_text(patch)
    proof=dict(schema=1,file=output.name,sha256=sha(output.read_bytes()),size_bytes=output.stat().st_size,
               version=VERSION,skin_id=ADDON,baseline_zip_sha256=BASELINE_ZIP_SHA256,files=len(candidate),
               changed={n:dict(before=sha(original[n]),after=sha(candidate[n])) for n in sorted(changed)},
               byte_identical_files=len(candidate)-len(changed),all_xml_files_parsed=xml_count,
               source_geometry_contract_tests_passed=result.testsRun,protected_files_verified=len(manifest['protected_files']),
               crc_passed=True,exact_archive_readback_passed=True,player_files_identical=True,drawer_files_identical=True,
               media_files_identical=True,provider_and_weather_configuration_changed=False,apk_modified=False,
               native_changed=False,source_select_repaired_by_skin=False,back_freeze_resolved=False,
               physical_device_verified=False,deferred_movie_video_framing_changed=False)
    (args.output_dir/'package-proof.json').write_bytes(dump(proof))
    print(json.dumps({k:proof[k] for k in ('file','sha256','files','byte_identical_files','all_xml_files_parsed',
                                         'source_geometry_contract_tests_passed','source_select_repaired_by_skin')},indent=2))


if __name__=='__main__':main()
