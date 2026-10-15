#!/usr/bin/env python3
"""Reproducibly rebuild the existing skin/controller ZIPs from guarded parents."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,shutil,subprocess,sys,zipfile
from lxml import etree as ET

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unpack(archive, destination, addon, digest):
    assert sha(archive)==digest, 'Wrong companion preimage: '+str(archive)
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();assert len(names)==len(set(names)) and z.testzip() is None
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            assert not p.is_absolute() and '..' not in p.parts and p.parts[0]==addon
            assert (info.external_attr>>16)&0o170000 != 0o120000,'Symlink in add-on ZIP'
        z.extractall(destination)
    return destination/addon


def archive(root, target):
    files={str(p.relative_to(root.parent)):p for p in root.rglob('*') if p.is_file()}
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(files.items()):
            assert '__pycache__' not in p.parts and p.suffix!='.pyc'
            info=zipfile.ZipInfo(name,(2026,10,4,0,0,0));info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes(),compresslevel=9)
    with zipfile.ZipFile(target) as z:
        assert set(z.namelist())==set(files) and z.testzip() is None
        for name,p in files.items():assert z.read(name)==p.read_bytes(),name
    return {'name':target.name,'sha256':sha(target),'size_bytes':target.stat().st_size,'files':len(files)}


def validate_skin(root, baseline):
    xml=list(root.rglob('*.xml'))
    for p in xml:ET.parse(str(p))
    addon=ET.parse(str(root/'addon.xml')).getroot()
    assert addon.get('id')=='skin.infinity.diggz' and addon.get('name')=='Infinity'
    assert addon.get('version')=='1.0.5.191'
    assert [n.get('folder') for n in addon.findall("extension[@point='xbmc.gui.skin']/res")]==['unified']
    for name,digest in baseline['files'].items():
        repaired_observers={'resources/lib/infinity_native_ambient.py','resources/lib/infinity_continuity.py'}
        if name.startswith(('media/','resources/')) and name not in repaired_observers:
            assert sha(root/name)==digest,'Existing artwork/resource changed: '+name
    health=json.loads((root/'infinity-skin.json').read_text())['ui_health']
    for name,ids in health['required_ids'].items():
        tree=ET.parse(str(root/'unified'/name))
        actual={int(x.get('id')) for x in tree.findall('.//control[@id]')}
        assert set(ids)<=actual,(name,set(ids)-actual)
    for name in ('Home.xml','Custom_1198_InfinityNav.xml','DialogConfirm.xml',
                 'DialogContextMenu.xml','DialogVideoInfo.xml','VideoOSD.xml'):
        tree=ET.parse(str(root/'unified'/name))
        ids=[x.get('id') for x in tree.findall('.//control[@id]') if int(x.get('id'))>0]
        assert len(ids)==len(set(ids)),('Duplicate control IDs',name)
    return len(xml)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('baseline-skin-zip','baseline-controller-zip','work','out'):
        ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.work.mkdir(parents=True,exist_ok=False);a.out.mkdir(parents=True,exist_ok=True)
    skin_base=json.loads((HERE/'skin-baseline-sha256.json').read_text())
    controller_base=json.loads((HERE/'controller-baseline.json').read_text())
    skin=unpack(a.baseline_skin_zip,a.work,'skin.infinity.diggz',skin_base['source_archive_sha256'])
    controller=unpack(a.baseline_controller_zip,a.work,'script.infinity.commandcenter',controller_base['sha256'])
    subprocess.run([sys.executable,str(HERE/'repair_skin.py'),str(skin)],check=True)
    subprocess.run([sys.executable,str(HERE/'repair_controller.py'),str(controller)],check=True)
    xml_count=validate_skin(skin,skin_base)
    # Validate Python without writing bytecode into the distributable add-ons.
    for root in (skin,controller):
        for p in root.rglob('*.py'):compile(p.read_bytes(),str(p),'exec')
    # The excluded movie-video rectangle is exactly preserved.
    with zipfile.ZipFile(a.baseline_skin_zip) as z:
        before=ET.fromstring(z.read('skin.infinity.diggz/unified/DialogVideoInfo.xml'))
    after=ET.parse(str(skin/'unified/DialogVideoInfo.xml')).getroot()
    def rectangles(tree):
        return [{key:node.findtext(key) for key in ('left','top','right','bottom','width','height')}
                for node in tree.findall(".//control[@type='videowindow']")]
    assert rectangles(before)==rectangles(after),'Deferred video framing changed'
    outputs=[]
    for root,name in ((controller,'Infinity-Command-Center-0.3.5.20-Mobile-Repair-RC1.zip'),
                      (skin,'Infinity-1.0.5.191-Mobile-Repair-RC1.zip')):
        outputs.append(archive(root,a.out/name))
    report={'schema':1,'baseline_apk':2103302,'required_apk':2103303,
            'skin_id':'skin.infinity.diggz','skin_version':'1.0.5.191','controller_version':'0.3.5.20',
            'skin_source_sha256':skin_base['source_archive_sha256'],
            'controller_source_sha256':controller_base['sha256'],
            'parsed_skin_xml_files':xml_count,'artwork_and_non_observer_resources_unchanged':True,
            'deferred_movie_video_rectangle_unchanged':True,'providers_and_resume_hub_implementation_unchanged':True,
            'physical_device_tested':False,'accepted':False,'outputs':outputs}
    (a.out/'COMPANION-AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in ('skin-repair-receipt.json','controller-repair-receipt.json'):
        shutil.copy2(a.work/name,a.out/name)
    shutil.copy2(HERE/'DEVICE-TEST.md',a.out/'DEVICE-TEST.md')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
