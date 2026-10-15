#!/usr/bin/env python3
"""Complete normal Kodi ZIP from pinned .215 plus the recovered .216 feature.
No skin updater/patch runner is delivered. All baseline bytes are retained except
owned Rails integrations and release metadata; original dialog branches survive.
"""
import argparse, copy, hashlib, importlib.util, json, re, os, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
HERE=Path(__file__).resolve().parents[1]
ROOT='skin.infinity.diggz/'
BASE_SHA='486aa86c8f8dcda31d80c6d058f4b96154dcb2b3f1a18cfa464c65e280ec7e70'
VERSION='1.0.5.218'
PROFILES=['16x9','20x9','5x6','6x5','fallback','portrait','unified']+['responsive/'+x for x in ['base','landscape','portrait','square','tall','ultrawide','wide']]
OWNED='String.IsEqual(ListItem.Property(Infinity.Rails.Item),true) | !String.IsEmpty(ListItem.Property(Addon.ID))'
ACTIVE='String.IsEqual(Window(Home).Property(Infinity.Rails.ContextActive),true)'
MOTION='!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)'
spec=importlib.util.spec_from_file_location('legacy_delta',HERE/'tools/legacy_delta.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)

def sha(b): return hashlib.sha256(b).hexdigest()
def xml(root):
    ET.indent(root,space='  ')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'
def child(parent,tag,text=None,**attrs):
    el=ET.SubElement(parent,tag,attrs)
    if text is not None: el.text=str(text)
    return el

def palette(root):
    light='[String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light) | [String.IsEmpty(Window(Home).Property(Infinity.SystemTheme)) + String.IsEqual(Window(Home).Property(Infinity.NativeSystemTheme),light)]]'
    oled='String.IsEqual(Window(Home).Property(Infinity.SystemTheme),OLED)'
    for name,values in {'Surface':('F7FFFFFF','FF000000','F20A111A'),'Text':('FF102237','FFFFFFFF','FFF2F6FB'),'Secondary':('FF50647A','FFA5B7C8','FF9EB2C4'),'Field':('F4EAF1F7','FF000000','F0131D29'),'Border':('FFB8C9D8','FF223A50','FF29445C'),'Accent':('FF006DCB','FF24A8FF','FF24A8FF'),'FocusedText':('FFFFFFFF','FF071725','FF071725')}.items():
        var=child(root,'variable',name='InfinityRails'+name)
        child(var,'value',values[0],condition=light); child(var,'value',values[1],condition=oled);child(var,'value',values[2])
    var=child(root,'variable',name='InfinityRailsContextTitle')
    child(var,'value','INFINITY — RAIL OPTIONS',condition='Window.IsActive(home)')
    child(var,'value','INFINITY — ADD-ON OPTIONS')

def geometry(control,left,top,width,height):
    for key,value in zip(('left','top','width','height'),(left,top,width,height)): child(control,key,value)

def context_controls():
    # All 3 native contract controls are top-level siblings: background 999,
    # dynamic grouplist 996 and template 1000. Kodi owns content-height/clamping.
    root=ET.Element('include',{'name':'InfinityRailsContextControls'})
    image=child(root,'control',type='image',id='999')
    geometry(image,'0','0','88%','75%')
    child(image,'texture','infinity_glass/surface.png',border='24',colordiffuse='$VAR[InfinityRailsSurface]')
    child(image,'bordertexture','infinity_glass/rim.png',border='24',colordiffuse='$VAR[InfinityRailsBorder]'); child(image,'bordersize','2')
    close=child(root,'control',type='button',id='995');geometry(close,'78%','2%','7%','5%')
    child(close,'label','');child(close,'onclick','PreviousMenu')
    for direction in ['onleft','onright','onup','ondown']:child(close,direction,'996')
    child(close,'texturefocus','infinity_legacy/close_focus.png',colordiffuse='$VAR[InfinityRailsAccent]')
    child(close,'texturenofocus','infinity_legacy/close.png',colordiffuse='$VAR[InfinityRailsText]')
    for top,height,label,font,color in [('2%','4%','$VAR[InfinityRailsContextTitle]','InfinitySmall','Text'),('6%','4%','$INFO[Control.GetLabel(1001)]','InfinitySmall','Secondary')]:
        item=child(root,'control',type='label');geometry(item,'4%',top,'72%',height)
        for k,v in [('font',font),('label',label),('textcolor','$VAR[InfinityRails'+color+']'),('aligny','center'),('scroll','true')]:child(item,k,v)
    group=child(root,'control',type='grouplist',id='996')
    child(group,'left','4%');child(group,'top','12%');child(group,'width','80%');child(group,'height','auto',min='1',max='60%')
    child(group,'itemgap','6');child(group,'orientation','vertical');child(group,'scrolltime','100')
    child(group,'onleft','995');child(group,'onright','995');child(group,'onup','996');child(group,'ondown','996')
    button=child(root,'control',type='button',id='1000');geometry(button,'0','0','80%','5%')
    for k,v in [('font','InfinityBody'),('align','left'),('aligny','center'),('textoffsetx','24'),('textcolor','$VAR[InfinityRailsText]'),('focusedcolor','$VAR[InfinityRailsFocusedText]'),('disabledcolor','$VAR[InfinityLegacyDisabled]'),('scroll','true')]:child(button,k,v)
    child(button,'texturefocus','infinity_glass/focus.png',border='16',colordiffuse='$VAR[InfinityRailsAccent]')
    child(button,'texturenofocus','infinity_glass/field.png',border='16',colordiffuse='$VAR[InfinityRailsField]')
    return root

def scoped_context(original):
    tree=ET.fromstring(original)
    controls=tree.find('controls')
    backup=ET.Element('include',{'name':'InfinityRailsOriginalContextControls'})
    for node in list(controls):backup.append(copy.deepcopy(node))
    controls.clear()
    child(controls,'include','InfinityRailsContextControls',condition=OWNED)
    child(controls,'include','InfinityRailsOriginalContextControls',condition='!['+OWNED+']')
    lifecycle=child(tree,'include','InfinityRailsContextLifecycle',condition=OWNED)
    # Preserve original animation behavior outside Rails/add-on browser only.
    for node in tree.findall('animation'):
        node.set('condition','['+node.get('condition','true')+'] + !['+OWNED+']')
    for node in tree.findall('include'):
        if node.text=='InfinityLegacy_dialogeffect':node.set('condition','!['+OWNED+']')
    for event,start,end,time in [('WindowOpen','0','100','180'),('WindowClose','100','0','130')]:
        child(tree,'animation',event,effect='fade',start=start,end=end,time=time,condition='['+OWNED+' | '+ACTIVE+'] + '+MOTION)
    return xml(tree),backup

def chooser():
    root=ET.Element('window',{'type':'dialog'})
    child(root,'defaultcontrol','6',always='true')
    for event,start,end,time in [('WindowOpen','0','100','180'),('WindowClose','100','0','130')]:child(root,'animation',event,effect='fade',start=start,end=end,time=time,condition=MOTION)
    controls=child(root,'controls')
    group=child(controls,'control',type='group');geometry(group,'6%','32%','88%','36%')
    surface=child(group,'control',type='image');geometry(surface,'0','0','100%','100%')
    child(surface,'texture','infinity_glass/surface.png',border='24',colordiffuse='$VAR[InfinityRailsSurface]');child(surface,'bordertexture','infinity_glass/rim.png',border='24',colordiffuse='$VAR[InfinityRailsBorder]');child(surface,'bordersize','2')
    for top,label,color in [('3%','$INFO[Window.Property(Infinity.Rails.Title)]','Text'),('14%','$INFO[Window.Property(Infinity.Rails.Subtitle)]','Secondary')]:
        item=child(group,'control',type='label');geometry(item,'4%',top,'78%','10%');child(item,'font','InfinitySmall');child(item,'textcolor','$VAR[InfinityRails'+color+']');child(item,'label',label);child(item,'aligny','center');child(item,'scroll','true')
    close=child(group,'control',type='button',id='7');geometry(close,'87%','3%','9%','14%');child(close,'label','');child(close,'texturefocus','infinity_legacy/close_focus.png',colordiffuse='$VAR[InfinityRailsAccent]');child(close,'texturenofocus','infinity_legacy/close.png',colordiffuse='$VAR[InfinityRailsText]')
    for k in ['onleft','onright','onup','ondown']:child(close,k,'6')
    listing=child(group,'control',type='list',id='6');geometry(listing,'4%','28%','92%','68%')
    for k,v in [('orientation','vertical'),('scrolltime','100'),('onleft','7'),('onright','7')]:child(listing,k,v)
    for tag in ['itemlayout','focusedlayout']:
        layout=child(listing,tag,width='100%',height='24%')
        bg=child(layout,'control',type='image');geometry(bg,'0','2%','100%','94%');child(bg,'texture','infinity_glass/focus.png' if tag=='focusedlayout' else 'infinity_glass/field.png',border='16',colordiffuse='$VAR[InfinityRailsAccent]' if tag=='focusedlayout' else '$VAR[InfinityRailsField]')
        label=child(layout,'control',type='label');geometry(label,'4%','0','92%','100%');child(label,'font','InfinityBody');child(label,'textcolor','$VAR[InfinityRailsFocusedText]' if tag=='focusedlayout' else '$VAR[InfinityRailsText]');child(label,'label','$INFO[ListItem.Label]');child(label,'aligny','center');child(label,'scroll','true')
    return xml(root)

def build(baseline,out):
    if sha(baseline.read_bytes())!=BASE_SHA:raise ValueError('Not exact approved .215 package')
    with ZipFile(baseline) as z:before={n[len(ROOT):]:z.read(n) for n in z.namelist() if n.startswith(ROOT) and not n.endswith('/')}
    after=dict(before)
    helper=HERE/'addons/script.infinity.rails'
    (helper/'resources/icon.png').write_bytes(before['resources/icon.png'])
    expected=legacy.default_catalog(before['unified/script-skinshortcuts-includes.xml'])
    if legacy.default_catalog((helper/'resources/defaults.xml').read_bytes()) != expected:
        raise ValueError('Recovered RC2 defaults do not match the exact .215 shortcuts')
    for profile in PROFILES:
        after[profile+'/Home.xml']=legacy.patch_home(before[profile+'/Home.xml'])
        inc=before.get(profile+'/Includes.xml',before['16x9/Includes.xml'])
        after[profile+'/Includes.xml']=inc.replace(b'<includes>',b'<includes>\n  <include file="Includes_InfinityRails.xml"/>',1)
        source=before.get(profile+'/script-skinshortcuts-includes.xml',before['16x9/script-skinshortcuts-includes.xml'])
        if legacy.default_catalog(source) != expected:raise ValueError('Default shortcuts differ at '+profile)
        includes=ET.fromstring(legacy.rails_include(source))
        for sec in ['movies','tvshows']:
            includes.find('./variable[@name="InfinityRailsContent"]/value[@condition="System.AddonIsEnabled(script.infinity.rails) + String.IsEqual(Container(9000).ListItem.Property(section),'+sec+')"]').text='plugin://script.infinity.rails/?section='+sec+'&revision=$INFO[Window(Home).Property(Infinity.Rails.'+sec+'.Revision)]'
        palette(includes)
        context,original=scoped_context(before[profile+'/DialogContextMenu.xml'])
        includes.append(context_controls());includes.append(original)
        lifecycle=child(includes,'include',name='InfinityRailsContextLifecycle')
        child(lifecycle,'onload','SetProperty(Infinity.Rails.ContextActive,true,Home)')
        child(lifecycle,'onunload','ClearProperty(Infinity.Rails.ContextActive,Home)')
        after[profile+'/Includes_InfinityRails.xml']=xml(includes)
        after[profile+'/DialogContextMenu.xml']=context
        after[profile+'/script-infinity-rails-select.xml']=chooser()
    addon=ET.fromstring(before['addon.xml']);addon.set('version',VERSION)
    child(addon.find('requires'),'import',addon='script.infinity.rails',version='0.2.0')
    addon.find('./extension[@point="xbmc.addon.metadata"]/description').text='Infinity '+VERSION+' Custom Rails RC3 TEST. Exact .215 foundation with saved .216 rail customization compatibility. Complete skin ZIP. Helper 0.2.0 required; install its ZIP once first. No resource patch runner, native changes or lock. Physical Fold acceptance pending.'
    after['addon.xml']=xml(addon)
    changed={p:sha(b) for p,b in after.items() if p not in before or b!=before[p]}
    for name in ['infinity-skin.json','Infinity-Protected-Manifest.json']:
        data=json.loads(before[name]);data.update(skin_version=VERSION,candidate=218,candidate_locked=False)
        for key,value in [('version',VERSION),('candidate_version',VERSION),('candidate_name','Custom Rails RC3 TEST')]:
            if key in data:data[key]=value
        data['custom_addon_rails_218']={'base_version':'1.0.5.215','base_sha256':BASE_SHA,'baseline_record_commit':'85b1305ef7a220dd23aaeb40c7d38150b8da4a92','rails_source_record_commit':'faae58d7594b8be1e423e119ddd1e1c9839767fd','rc2_helper_sha256':'b0d0b293cc66d937cb82dd6c8ac9e97956e67f88efec10e764d4631540f7a9da','helper_version':'0.2.0','modes':['normal','cinema','compact','twopane'],'menu_owner':'DialogContextMenu.xml, scoped Rails/add-on branch; original non-add-on branch retained','full_skin_zip':True,'physical_device_verified':False,'locked':False,'apk_changed':False}
        for p in data.get('protected_files',{}):
            if p in after and after[p] != before.get(p):data['protected_files'][p]=sha(after[p])
        after[name]=(json.dumps(data,sort_keys=True,indent=2)+'\n').encode()
    out.mkdir(parents=True,exist_ok=True)
    path=out/('skin.infinity.diggz-'+VERSION+'-Custom-Rails-RC3-TEST.zip')
    pack(path,{ROOT+k:v for k,v in after.items()})
    helper=HERE/'addons/script.infinity.rails'
    helperpath=out/'script.infinity.rails-0.2.0-Custom-Rails-RC3-TEST.zip'
    pack(helperpath,{helper.name+'/'+str(p.relative_to(helper)):p.read_bytes() for p in helper.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')})
    report={'baseline_version':'1.0.5.215','baseline_sha256':BASE_SHA,'candidate_version':VERSION,'original_files':len(before),'changed_existing_files':sum(p in before and after[p]!=before[p] for p in after),'new_files':sum(p not in before for p in after),'unchanged_original_files':sum(after[p]==before[p] for p in before),'deleted_files':0,'changed_paths':[p for p in after if p not in before or before[p]!=after[p]],'packages':{p.name:{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in [path,helperpath]},'profiles':PROFILES,'native_changed':False,'device_verified':False,'locked':False}
    (HERE/'evidence/PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return path

def pack(path,files):
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    os.close(fd)
    try:
        with ZipFile(temporary,'w',ZIP_DEFLATED,compresslevel=9) as z:
            for name,raw in sorted(files.items()):
                zi=ZipInfo(name,date_time=(2026,10,14,0,0,0));zi.compress_type=ZIP_DEFLATED;zi.external_attr=0o100644<<16
                z.writestr(zi,raw)
        with ZipFile(temporary) as z:
            if z.testzip() is not None:raise ValueError('Package CRC validation failed')
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('baseline',type=Path);parser.add_argument('--output',type=Path,default=HERE.parent/'delivery');args=parser.parse_args();build(args.baseline,args.output)
