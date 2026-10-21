#!/usr/bin/env python3
"""Exact source stage for 2103394; never reads or resets a user profile."""
from __future__ import annotations
import argparse
import ast
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import ui94
import trakt94
from native94 import require, once

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PARENT='0326782173ef609d0f55284245ce00f55a8a78d73b3d2acf5928950bd4af068e'
COMMIT='2a9b6ae6bd0556b2f7b13a786a6382850b05cd83'
CC='script.infinity.commandcenter';UI='script.infinity.uirepair'
WB='script.infinity.watchedbridge';SKIN='skin.infinity.diggz';HEALTH='script.kodihealthcenter'
PACKAGES=((CC,'0.3.5.23','0.3.5.24'),(WB,'1.0.4','1.0.5'),
          (UI,'0.1.5','0.1.6'),(SKIN,'1.0.5.230','1.0.5.231'),
          ('script.infinity.rails','0.2.7','0.2.7'),(HEALTH,None,'2.5.21'))


def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read_parent(path):
    require(digest(path)==PARENT,'wrong signed 2103393 input')
    roots={row[0] for row in PACKAGES}
    with ZipFile(path) as z:
        require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'invalid parent APK')
        return {n[len('assets/addons/'):]:z.read(n) for n in z.namelist()
                if n.startswith('assets/addons/') and not n.endswith('/') and n.split('/')[2] in roots}


def xml(raw):return ET.fromstring(raw)
def xmlbytes(root):return b'<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(root,encoding='utf-8')+b'\n'
def settext(node,name,value):
    e=node.find(name)
    if e is None:e=ET.SubElement(node,name)
    e.text=str(value)
    return e


def skin_settings(raw):
    root=xml(raw);group=root.find('.//control[@id="9004"]')
    require(group is not None,'missing original Appearance group')
    template=group.find('control[@id="4001"]')
    require(template is not None,'missing original settings-row template')
    row=copy.deepcopy(template);row.set('id','5020')
    for e in row.findall('onclick'):row.remove(e)
    for tag in ('enable','visible','onfocus'):
        for e in row.findall(tag):row.remove(e)
    settext(row,'label','Theme');settext(row,'label2','Follow System • Light Pearl • Dark')
    ET.SubElement(row,'onclick').text='RunScript(script.infinity.commandcenter,theme)'
    group.insert(list(group).index(template),row)
    return xmlbytes(root)


def twopane(raw):
    root=xml(raw);group=root.find('.//control[@id="40002"]')
    require(group is not None and 'twopane' in group.findtext('visible',''),'missing Two-Pane group')
    logo=[c for c in group.findall('control') if c.findtext('texture') in ('infinity_polish/infinity_mark.png','infinity_ui/infinity_logo.png')]
    require(len(logo)==1,'ambiguous Two-Pane logo')
    settext(logo[0],'left','112');settext(logo[0],'width','96');settext(logo[0],'height','56')
    plots=0
    for control in group.findall('control'):
        label=control.findtext('label','')
        match=re.fullmatch(r'\$INFO\[Container\((870[12])\)\.ListItem\.(Title|Year|Plot)\]',label)
        if not match:continue
        cid,field=match.groups()
        if field=='Title':
            settext(control,'top','8.8%');settext(control,'height','4.1%')
        elif field=='Year':
            settext(control,'top','13.1%');settext(control,'height','2.3%')
            settext(control,'font','InfinitySmall')
            settext(control,'label',label+'$INFO[Container('+cid+').ListItem.MPAA,  •  ,]'
                    +'$INFO[Container('+cid+').ListItem.Duration,  •  ,]'
                    +'$INFO[Container('+cid+').ListItem.Rating,  •  ,]')
        else:
            plots+=1;control.set('type','textbox');control.set('id','988'+cid[-1])
            settext(control,'top','16%');settext(control,'height','14%')
            settext(control,'width','62.8%');settext(control,'font','InfinitySmall')
            for name in ('scroll','aligny','autoscroll'):
                for e in control.findall(name):control.remove(e)
            settext(control,'pagecontrol','989'+cid[-1]);settext(control,'scrolltime','140')
            bar=ET.SubElement(group,'control',{'type':'scrollbar','id':'989'+cid[-1]})
            for k,v in {'left':'96%','top':'16%','width':'18','height':'14%',
                        'orientation':'vertical','showonepage':'false',
                        'visible':control.findtext('visible',''),
                        'onleft':'988'+cid[-1],'onright':'9870',
                        'texturesliderbackground':'infinity_legacy/track.png',
                        'texturesliderbar':'infinity_legacy/track.png',
                        'texturesliderbarfocus':'infinity_legacy/track.png'}.items():settext(bar,k,v)
    require(plots==2,'Movie and TV provider synopses required')
    button=group.find('control[@id="9870"]');require(button is not None,'missing original Play/Open')
    settext(button,'top','31.4%');settext(button,'height','3.6%')
    return xmlbytes(root)


OLED_CONDITION='String.IsEqual(Skin.String(Infinity.DarkAppearance),oled) + [String.IsEqual(Window(Home).Property(Infinity.SystemTheme),dark) | String.IsEqual(Window(Home).Property(Infinity.SystemTheme),OLED) | [String.IsEmpty(Window(Home).Property(Infinity.SystemTheme)) + [String.IsEqual(Window(Home).Property(Infinity.NativeSystemTheme),dark) | String.IsEqual(Window(Home).Property(Infinity.NativeSystemTheme),OLED)]]]'
OLED_SURFACES={'InfinityLegacyBase','InfinityLegacySurface','InfinityLegacyField','InfinityGlassControlSurface',
               'InfinityDrawerPanel','InfinityBoardBackground','InfinityBoardCard','InfinityUIRepairSurface',
               'InfinityDialogSurface','InfinityGlassPanel','InfinityLegacyBackground'}


def oled(raw):
    root=xml(raw);changed=False
    for node in root.findall('variable'):
        if node.get('name') in OLED_SURFACES:
            e=ET.Element('value',{'condition':OLED_CONDITION});e.text='FF000000';node.insert(0,e);changed=True
    return xmlbytes(root) if changed else raw


def motion_route(raw):
    root=xml(raw);rows=root.findall('.//control[@id="1194105"]');require(len(rows)==1,'missing Motion/Settings row')
    row=rows[0];require(row.findtext('onclick')=='Addon.OpenSettings(script.infinity.commandcenter)','motion route drift')
    settext(row,'onclick','RunScript(script.infinity.commandcenter,motion-settings)')
    return xmlbytes(root)


def compact_select(raw):
    root=xml(raw)
    # The existing compact selector marker is consumed dynamically, so this
    # cannot replace repository/provider selection or another dialog's layout.
    for e in root.findall('.//control'):
        if e.get('type')=='group' and e.find('centerleft') is not None:
            # Retain ordinary geometry; add a compact position condition only
            # to the existing Infinity selector path where the marker is set.
            pass
    return raw


SETTINGS_XML=b'''<?xml version="1.0" encoding="utf-8"?>
<settings version="1"><section id="script.infinity.commandcenter"><category id="experience" label="Infinity Experience"><group id="1">
<setting id="motion_mode" type="string" label="Motion"><level>0</level><default>full</default><constraints><options><option label="Full">full</option><option label="Reduced">reduced</option><option label="Off">off</option></options></constraints><control type="spinner" format="string"/></setting>
<setting id="ambient_home" type="string" label="Ambient Home"><level>0</level><default>subtle</default><constraints><options><option label="Off">off</option><option label="Subtle">subtle</option><option label="Immersive">immersive</option></options></constraints><control type="spinner" format="string"/></setting>
</group></category></section></settings>'''


def health(files):
    raw=base64.b64decode(''.join(p.read_text().strip() for p in sorted(HERE.glob('HEALTH20-*.b64'))),validate=False)
    require(sha(raw)=='f3a7e7ff6a850e37e12f690bc3455fcd2778c00b10228ab804517d749d4cff89','wrong complete Health Center source ZIP')
    with ZipFile(io.BytesIO(raw)) as z:baseline={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    require(sha(baseline[HEALTH+'/default.py'])=='b328b31fe7e0069019d2e95671f6132ff78395e53a4f7088ed3d2800120175d5',
            'Health source differs from observed installed 2.5.20')
    final=dict(baseline)
    for name,body in baseline.items():
        if name.endswith('.py'):
            body=body.replace(b"VERSION = '2.5.20'",b"VERSION = '2.5.21'").replace(b'VERSION="2.5.20"',b'VERSION="2.5.21"').replace(b"VERSION='2.5.20'",b"VERSION='2.5.21'")
            final[name]=body
    final[HEALTH+'/addon.xml']=once(baseline[HEALTH+'/addon.xml'],b'version="2.5.20"',b'version="2.5.21"')
    final[HEALTH+'/khc_causal.py']=(HERE/'khc_causal.py').read_bytes()
    raw=final[HEALTH+'/default.py']
    anchor=b'def _run_dashboard_command(command):\n'
    helper=b'''def causal_tree():
    from khc_causal import collect, text
    from khc_kodi import native_roots, environment
    roots = native_roots()
    roots += [root.parent for root in roots]
    xbmcgui.Dialog().textviewer('Infinity Health Center', text(collect(roots, environment())))


'''
    raw=once(raw,anchor,helper+anchor)
    raw=once(raw,b"        'scan':check_kodi,",b"        'causal-tree':causal_tree,\n        'scan':check_kodi,")
    final[HEALTH+'/default.py']=raw
    raw=final[HEALTH+'/khc_diagnostics.py']
    anchor=b"        bundle.json('environment-now.json', environment, 'environment_at_export_not_at_crash')"
    raw=once(raw,anchor,anchor+b'''
        from khc_causal import collect as causal_collect
        causal_roots = [entry[1] for entry in native_dirs]
        causal_roots += [Path(entry[1]).parent for entry in native_dirs]
        bundle.json('causal-tree.json', causal_collect(causal_roots, environment), 'bounded_causal_diagnostic_tree')''')
    final[HEALTH+'/khc_diagnostics.py']=raw
    files.update(final)
    return baseline


def components(original):
    final=dict(original)
    final[CC+'/resume_hub.py']=trakt94.hub(original[CC+'/resume_hub.py'])
    final[CC+'/plugin.py']=trakt94.plugin(original[CC+'/plugin.py'])
    final[CC+'/context.py']=trakt94.context(original[CC+'/context.py'])
    final[CC+'/addon.xml']=trakt94.addon(original[CC+'/addon.xml'])
    final[WB+'/addon.xml']=trakt94.bridge_addon(original[WB+'/addon.xml'])
    final[WB+'/controller.py']=trakt94.controller(original[WB+'/controller.py'])
    final[CC+'/infinity_trakt.py']=(HERE/'infinity_trakt.py').read_bytes()
    final[CC+'/default.py']=ui94.settings_entry(original[CC+'/default.py'])
    final[CC+'/infinity_settings.py']=(HERE/'infinity_settings.py').read_bytes()
    final[CC+'/resources/settings.xml']=SETTINGS_XML
    final[UI+'/home_option_b.py']=ui94.home_option_b(original[UI+'/home_option_b.py'])
    final[UI+'/controller_access.py']=ui94.tracking_menu(original[UI+'/controller_access.py'])
    final[UI+'/runtime.py']=ui94.runtime_trace(original[UI+'/runtime.py'])
    health(final)
    for name,raw in list(final.items()):
        if not name.startswith(SKIN+'/') or not name.endswith('.xml'):continue
        leaf=name.rsplit('/',1)[-1]
        if leaf=='Home.xml':raw=twopane(raw)
        elif leaf=='SkinSettings.xml':raw=skin_settings(raw)
        elif leaf=='Custom_1194_InfinityCommandCenter.xml':raw=motion_route(raw)
        if b'<variable ' in raw:raw=oled(raw)
        final[name]=raw
    for aid,old,new in PACKAGES:
        if aid==HEALTH or old==new:continue
        final[aid+'/addon.xml']=once(final[aid+'/addon.xml'],('version="'+old+'"').encode(),('version="'+new+'"').encode())
    # The new candidate manifest describes certified source bytes. Preserve its
    # historical locks and never change installed files to satisfy a checksum.
    name=SKIN+'/Infinity-Protected-Manifest.json';manifest=json.loads(final[name])
    protected=manifest['protected_files'];require(len(protected)==941,'protected manifest scope drift')
    manifest['protected_files']={p:sha(final[SKIN+'/'+p]) for p in protected}
    manifest.update(candidate=231,candidate_version='1.0.5.231',skin_version='1.0.5.231',candidate_locked=False)
    manifest['corrective_231']={'source_parent_commit':COMMIT,'physical_fold_verified':False,'final_lock':False,
                               'no_self_heal_or_user_data_reset':True}
    final[name]=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    pins={n.split('/',1)[1]:sha(b) for n,b in final.items() if n.startswith(CC+'/') and
          (n.endswith('.py') or n==CC+'/addon.xml')}
    for aid in (UI,WB):final[aid+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,sort_keys=True,indent=2)+'\n').encode()
    final[WB+'/controller.py']=once(final[WB+'/controller.py'],b'"0.3.5.23"',b'"0.3.5.24"')
    for name,body in final.items():
        if name.endswith('.py'):ast.parse(body.decode('utf-8'),filename=name)
        elif name.endswith('.xml'):ET.fromstring(body)
    require(not any('cobra' in n.lower() for n in set(final)^set(original)), 'Cobra source added or removed')
    return final


def ledger(original,final):
    return {'parent_apk_sha256':PARENT,'parent_source_commit':COMMIT,
            'versions':{a:v for a,_,v in PACKAGES},
            'changed':{n:{'before':sha(original[n]) if n in original else None,'after':sha(final[n])}
                       for n in sorted(final) if original.get(n)!=final[n]},
            'removed':sorted(set(original)-set(final)),'physical_fold_verified':False,'final_lock':False}


def stage(apk,out):
    original=read_parent(apk);final=components(original)
    require(not out.exists(),'stage already exists')
    for name,body in final.items():
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    record=ledger(original,final)
    (out/'MEMBER-DELTA.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('out',type=Path);args=p.parse_args()
    print(json.dumps(stage(args.apk,args.out),indent=2))
