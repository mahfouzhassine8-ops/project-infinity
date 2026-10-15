"""Build the paired skin delta from exact locked .176; no UI geometry changes."""
from pathlib import Path
import argparse,hashlib,json,zipfile,xml.etree.ElementTree as E

def main():
    a=argparse.ArgumentParser();a.add_argument('parent',type=Path);a.add_argument('observer',type=Path);a.add_argument('output',type=Path);a.add_argument('--evidence',type=Path,required=True);args=a.parse_args()
    expected='4263de3906ea0dc6e24f3c6f04c2f779b0c7a8bbdd31656b82e221402063d1c9'
    sha=lambda b:hashlib.sha256(b).hexdigest()
    assert sha(args.parent.read_bytes())==expected,'Not the exact locked .176 package'
    prefix='skin.infinity.diggz/'
    with zipfile.ZipFile(args.parent) as z:
        assert z.testzip() is None
        infos=z.infolist();old={i.filename:z.read(i) for i in infos}
    assert len(old)==len(infos),'Duplicate parent ZIP entries'
    data=dict(old);observer=args.observer.read_bytes();compile(observer,'infinity_native_ambient.py','exec')
    data[prefix+'resources/lib/infinity_native_ambient.py']=observer
    addon=data[prefix+'addon.xml'].decode();assert addon.count('version="1.0.5.176"')==1
    data[prefix+'addon.xml']=addon.replace('version="1.0.5.176"','version="1.0.5.178"',1).encode()
    release={'baseline':'1.0.5.176','controller':'0.3.5.17','requires_apk':2103284,'native_changed':True,'runtime_tested':False,'status':'device_acceptance_pending','title':'Infinity Kodi Ambient Surface Repair RC1','scope':'Existing Kodi video Surface sampling + retained RenderCapture warm-up; all layout XML unchanged'}
    for name in ['infinity-skin.json','Infinity-Protected-Manifest.json']:
        d=json.loads(data[prefix+name]);d['skin_version']='1.0.5.178';d['current_release']=release
        d['native_video_ambient'].update(apk_parent=2103282,requires_apk=2103284,parent=expected,device_verified=False,surface_api=1,capture='Existing Kodi XBMCVideoView PixelCopy; RenderCapture for non-Surface renderers')
        if name=='infinity-skin.json':d.update(candidate=178,candidate_name='Infinity Kodi Ambient Surface Repair RC1')
        else:
            d['candidate']='Infinity Kodi Ambient Surface Repair 1.0.5.178 RC1'
            for n,h in d['protected_files'].items():
                assert prefix+n in data,n
                assert sha(old[prefix+n])==h,('Parent protected hash mismatch',n)
                d['protected_files'][n]=sha(data[prefix+n])
            d['protected_files']['resources/lib/infinity_native_ambient.py']=sha(observer)
        data[prefix+name]=(json.dumps(d,indent=2,sort_keys=True)+'\n').encode()
    changed=[n for n in old if old[n]!=data[n]]
    allowed={prefix+n for n in ['addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json','resources/lib/infinity_native_ambient.py']}
    assert set(changed)==allowed,(changed,allowed)
    xml=[n for n in data if n.endswith('.xml')]
    for n in xml:E.fromstring(data[n])
    assert E.fromstring(data[prefix+'addon.xml']).attrib['version']=='1.0.5.178'
    manifest=json.loads(data[prefix+'Infinity-Protected-Manifest.json'])
    for n,h in manifest['protected_files'].items():assert sha(data[prefix+n])==h,n
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w') as z:
        for info in infos:z.writestr(info,data[info.filename])
    with zipfile.ZipFile(args.output) as z:assert z.testzip() is None
    report={'parent_sha256':expected,'skin_version':'1.0.5.178','requires_apk':2103284,'candidate_sha256':sha(args.output.read_bytes()),'modified_files':changed,'unchanged_zip_entries':len(old)-len(changed),'parsed_xml_files':len(xml),'protected_hashes_verified':len(manifest['protected_files']),'all_layout_xml_byte_identical':True,'command_center_unchanged':'0.3.5.17','observer_sha256':sha(observer),'physical_device_verified':False,'locked':False}
    args.evidence.parent.mkdir(parents=True,exist_ok=True);args.evidence.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
