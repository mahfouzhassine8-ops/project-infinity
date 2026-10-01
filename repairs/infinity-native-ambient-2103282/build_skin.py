"""Build only from the exact locked .173 ZIP; preserve all existing control trees."""
import argparse, copy, hashlib, json, re, zipfile
from pathlib import Path
from lxml import etree as E

HERE=Path(__file__).resolve().parent
SHA='e70cbcc974dbb646c4061432ce458d513911108aad943cddcc663dc7b937b98e'
PROFILES=('16x9','20x9','6x5','5x6','portrait','fallback')
ACTIVE='String.IsEqual(Window(Home).Property(Infinity.NativeAmbient.Active),true) + Control.IsVisible(29900) + String.IsEqual(Window(Home).Property(Infinity.AmbientHome.Mode),immersive)'
MATCH=re.compile(r'Infinity(?:Glass(?:Surface|ControlSurface)|Board(?:Panel|Surface)|PaletteCardSurface)')

def native_image(base,cid):
    overlay=E.Element('control',type='image',id=str(cid))
    E.SubElement(overlay,'description').text='Infinity native video light on existing material'
    for key in ('left','top','right','bottom','width','height','animation'):
        for node in base.findall(key):overlay.append(copy.deepcopy(node))
    E.SubElement(overlay,'aspectratio').text='scale'
    E.SubElement(overlay,'fadetime').text='0'
    # Constant label allows Python setImage to replace only this texture.
    E.SubElement(overlay,'texture').text='infinity_ui/contract_white.png'
    visible=base.findtext('visible')
    E.SubElement(overlay,'visible').text=ACTIVE+(' + ['+visible+']' if visible else '')
    return overlay

def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert hashlib.sha256(a.parent.read_bytes()).hexdigest()==SHA
    a.out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.parent) as z:original={n:z.read(n) for n in z.namelist()}
    files=dict(original);recipes={};proof={};protected=[]
    for profile in PROFILES:
        name=f'skin.infinity.diggz/{profile}/Home.xml';root=E.fromstring(files[name]);before=E.tostring(root)
        used={int(n.get('id')) for n in root.iter('control') if (n.get('id') or '').isdigit()}
        assert not any(39000<=i<=39999 or 40000<=i<45000 for i in used),'ID collision'
        new_nodes=[];id_nodes=[];nextid=40000;rows=[]
        def ident(node):
            nonlocal nextid
            if node.get('id'):return int(node.get('id'))
            nextid+=1;node.set('id',str(nextid));id_nodes.append(node);return nextid
        for base in list(root.iter('control')):
            if base.get('type')!='image':continue
            texture=base.find('texture')
            if texture is None or not MATCH.search(texture.get('colordiffuse','')):continue
            ancestors=list(base.iterancestors())
            if any(n.tag in ('itemlayout','focusedlayout') or n.get('type') in ('panel','list','wraplist','fixedlist','grouplist') for n in ancestors):continue
            # Never add illumination to the root video/backdrop wash.
            if base.getparent().tag=='controls':continue
            groups=[n for n in reversed(ancestors) if n.tag=='control' and n.get('type')=='group']
            parents=[ident(g) for g in groups]
            probe=ident(base);nextid+=1;overlay=native_image(base,nextid)
            base.addnext(overlay);new_nodes.append(overlay)
            rows.append({'overlay':nextid,'parents':parents,'probes':parents+[probe],
                         'radius':18 if 'glass/' in (texture.text or '') or texture.get('border') else 0})
        dock=root.xpath('.//include[@content="InfinityHomePlaybackDock"]')
        assert len(dock)==(0 if profile=='fallback' else 1),(profile,'dock count',len(dock))
        if dock:rows.append({'overlay':39002,'parents':[29910],'probes':[29910,39001],'radius':18})
        back=root.xpath('.//include[@content="InfinityHomePlaybackBackground"]')
        assert len(back)==(0 if profile=='fallback' else 1),profile
        dims=back[0] if back else root.find('.//include[@content="InfinityExperienceBackdrop"]')
        sw=dims.find('param[@name="'+('screenwidth' if back else 'width')+'"]').get('value');sh=dims.find('param[@name="'+('screenheight' if back else 'height')+'"]').get('value')
        sentinel=E.Element('control',type='image',id='39799')
        for key,value in [('left','0'),('top','0'),('width',sw),('height',sh),('texture','infinity_ui/contract_white.png'),('visible','false')]:E.SubElement(sentinel,key).text=value
        root.find('controls').append(sentinel);new_nodes.append(sentinel)
        for action in [f'SetProperty(Infinity.NativeAmbient.Profile,{profile},Home)',
                       'RunScript(special://skin/resources/lib/infinity_native_ambient.py)']:
            n=E.Element('onload');n.text=action;root.insert(0,n);new_nodes.append(n)
        n=E.Element('onunload');n.text='ClearProperty(Infinity.NativeAmbient.Active,Home)';root.insert(0,n);new_nodes.append(n)
        files[name]=E.tostring(root,encoding='UTF-8',xml_declaration=True)
        # Acceptance: every original node, action, label, visibility and geometry
        # must survive. Strip only our nodes/assigned IDs then compare full tree.
        for n in new_nodes:n.getparent().remove(n)
        for n in id_nodes:del n.attrib['id']
        assert E.tostring(root)==before,(profile,'existing control tree changed')
        recipes[profile]=rows;proof[profile]={'surfaces':len(rows),'original_control_tree_unchanged':True,'gui':[sw,sh]}
    for profile in ('16x9','fallback'):
        name=f'skin.infinity.diggz/{profile}/Includes_InfinityHomePlayback.xml';root=E.fromstring(files[name]);before=E.tostring(root)
        group=root.find('.//control[@id="29910"]');base=group.find('control[@type="image"]');assert base.get('id') is None
        base.set('id','39001');overlay=native_image(base,39002);base.addnext(overlay)
        files[name]=E.tostring(root,encoding='UTF-8',xml_declaration=True)
        group.remove(overlay);del base.attrib['id'];assert E.tostring(root)==before,'playback control changed'
    root='skin.infinity.diggz/'
    files[root+'resources/lib/infinity_native_ambient.py']=(HERE/'infinity_native_ambient.py').read_bytes()
    files[root+'resources/lib/Infinity-Ambient-NOTICE.txt']=(HERE/'NOTICE.txt').read_bytes()
    files[root+'resources/lib/infinity_native_glass.json']=json.dumps(recipes,indent=2).encode()
    addon=files[root+'addon.xml'].decode();assert 'version="1.0.5.173"' in addon
    files[root+'addon.xml']=addon.replace('version="1.0.5.173"','version="1.0.5.175"',1).encode()
    manifest=json.loads(files[root+'Infinity-Protected-Manifest.json']);manifest['candidate']='Infinity Native Video Ambient 1.0.5.175 RC1'
    manifest['native_video_ambient']={'parent':SHA,'apk_parent':2103281,'requires_apk':2103282,'device_verified':False,'command_center_unchanged':'0.3.5.17'}
    meta=json.loads(files[root+'infinity-skin.json']);meta.update(candidate=175,candidate_name='Infinity Native Video Ambient RC1',native_video_ambient=manifest['native_video_ambient'])
    files[root+'infinity-skin.json']=json.dumps(meta,indent=2,sort_keys=True).encode()
    for path in manifest['protected_files']:
        if root+path in files:manifest['protected_files'][path]=hashlib.sha256(files[root+path]).hexdigest()
    files[root+'Infinity-Protected-Manifest.json']=json.dumps(manifest,indent=2,sort_keys=True).encode()
    changed=[n for n in original if files[n]!=original[n]];added=[n for n in files if n not in original]
    for name in original:
        if name not in changed:protected.append(name)
    for name,data in files.items():
        if name.endswith('.xml'):E.fromstring(data)
    dest=a.out/'Infinity-Mobile-1.0.5.175-Native-Video-Ambient-RC1.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in files.items():
            info=zipfile.ZipInfo(name,date_time=(2026,10,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data,compresslevel=6)
    report={'parent_sha256':SHA,'skin_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'modified_files':changed,'added_files':added,
            'unchanged_files':len(protected),'profiles':proof,'physical_device_verified':False,'no_transport_action_changes':True}
    (a.out/'skin-preservation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
