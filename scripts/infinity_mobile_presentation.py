#!/usr/bin/env python3
"""Build/verify an explicit Infinity skin layer over one matched, reusable engine.

Only allowlisted presentation resources change. Native libraries, DEX, binary
manifest, resources.arsc, stock code and databases are not rewritten here.
"""
from __future__ import annotations
import argparse, hashlib, io, json, re, tempfile, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import infinity71 as engine

SKIN = engine.SKIN
COLOR_TAGS = ('textcolor','focusedcolor','disabledcolor','selectedcolor','shadowcolor',
              'colordiffuse','backgroundcolor','texturenofocuscolor','texturefocuscolor')
EXCLUDED_XML = {'Custom_1199_InfinityVideoLock.xml', 'VideoOSD.xml', 'VideoFullScreen.xml',
                'FullscreenVideo.xml', 'DialogSeekBar.xml'}
RECIPE_VERSION = 3
RESUME = 'assets/addons/resource.language.en_gb/resources/strings.po'
EXTRA = {SKIN+'xml/Custom_1198_InfinityAppearance.xml', SKIN+'media/infinity/icon.png',
         SKIN+'colors/Infinity Light.xml', SKIN+'colors/Infinity Dark.xml',
         SKIN+'colors/Infinity OLED.xml', 'assets/media/splash.jpg', RESUME}
PORTRAIT_MOBILE = 'Integer.IsLess(System.ScreenWidth,System.ScreenHeight) + String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)'


def allowed(name: str) -> bool:
    return name in engine.OVERLAY_ALLOWLIST or name in EXTRA or (
        name.startswith(SKIN+'xml/') and '/' not in name[len(SKIN+'xml/'):] and name.endswith('.xml'))


def appearance_dialog() -> bytes:
    root = ET.Element('window', {'type':'dialog','id':'1198'})
    ET.SubElement(root,'defaultcontrol',{'always':'true'}).text='9911'
    controls=ET.SubElement(root,'controls')
    overlay=ET.SubElement(controls,'control',{'type':'image'})
    ET.SubElement(overlay,'include').text='FullScreenDimensions'
    ET.SubElement(overlay,'texture',{'colordiffuse':'E6000000'}).text='white.png'
    label=ET.SubElement(controls,'control',{'type':'label'})
    for tag,value in [('left','550'),('top','200'),('width','820'),('height','70'),('font','font20'),
                      ('textcolor','FFFFFFFF'),('label','Infinity appearance')]:
        ET.SubElement(label,tag).text=value
    for i,(policy,title) in enumerate([('system','Follow phone (Light / OLED)'),('light','Infinity Light'),
                                       ('dark','Infinity Dark'),('oled','Infinity OLED')]):
        control=ET.SubElement(controls,'control',{'type':'button','id':str(9911+i)})
        for tag,value in [('left','550'),('top',str(300+i*85)),('width','820'),('height','75'),
                          ('font','font13'),('label',title),('textcolor','FFFFFFFF'),
                          ('focusedcolor','FFFFFFFF'),('onup',str(9911+(i-1)%4)),
                          ('ondown',str(9911+(i+1)%4))]:ET.SubElement(control,tag).text=value
        ET.SubElement(control,'texturefocus',{'colordiffuse':'FF176080'}).text='white.png'
        ET.SubElement(control,'texturenofocus',{'colordiffuse':'FF202830'}).text='white.png'
        ET.SubElement(control,'onclick').text=f'Skin.SetString(Infinity.ThemePolicy,{policy})'
        ET.SubElement(control,'onclick').text='Dialog.Close(1198)'
    note=ET.SubElement(controls,'control',{'type':'label'})
    for tag,value in [('left','550'),('top','675'),('width','820'),('height','65'),('font','font12'),
                      ('textcolor','FFFFFFFF'),('label','Infinity Controller $INFO[Window(Home).Property(Infinity.BridgeVersion)] / System: $INFO[Window(Home).Property(Infinity.SystemTheme)]')]:
        ET.SubElement(note,tag).text=value
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def color_sets(source: bytes) -> dict[str,dict[str,str]]:
    defaults={e.attrib['name']:e.text for e in ET.fromstring(source).findall('color')}
    required={'primary_background','secondary_background','dialog_tint','background','black','white','grey'}
    if not required.issubset(defaults): raise ValueError('Unexpected Estuary color schema')
    dark=dict(defaults,primary_background='FF14202B',secondary_background='FF1C2933')
    oled=dict(dark,primary_background='FF000000',secondary_background='FF000000',
              dialog_tint='FF080808',background='FF000000',black='FF000000',bg_overlay='00000000')
    light=dict(defaults,
               primary_background='FFF0F4F8',
               secondary_background='FFE3EAF1',
               dialog_tint='FFF7F9FC',
               background='FFF4F7FA',
               black='FFF4F7FA',
               white='FF0F172A',
               grey='FF334155',
               blue='FF2563EB',
               button_focus='FFCFE8FF',
               button_alt_focus='A0CFE8FF',
               bg_image='FFF8FAFC',
               bg_overlay='08FFFFFF',
               text_shadow='18000000',
               border_alpha='50334155',
               disabled='B064748B',
               selected='FF8A5A00')
    return {'light':light,'dark':dark,'oled':oled}


def variables(palettes: dict[str,dict[str,str]]) -> str:
    system='[String.IsEmpty(Skin.String(Infinity.ThemePolicy)) | String.IsEqual(Skin.String(Infinity.ThemePolicy),system)]'
    light='String.IsEqual(Skin.String(Infinity.ThemePolicy),light) | ['+system+' + String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light)]'
    oled='String.IsEqual(Skin.String(Infinity.ThemePolicy),oled) | ['+system+' + String.IsEqual(Window(Home).Property(Infinity.SystemTheme),dark)]'
    nodes=[]
    for color in sorted(palettes['dark']):
        node=ET.Element('variable',{'name':'InfinityColor_'+color})
        for condition,mode in [(light,'light'),(oled,'oled')]:
            ET.SubElement(node,'value',{'condition':condition}).text=palettes[mode][color]
        ET.SubElement(node,'value').text=palettes['dark'][color]
        nodes.append(ET.tostring(node,encoding='unicode'))
    return '\n'.join(nodes)


def add_portrait_scaling(name: str, xml: str) -> str:
    """Enlarge only the front/narrow portrait Home UI; inner/landscape stays unchanged."""
    if name.endswith('/Home.xml'):
        marker='<control type="fixedlist" id="9000">'
        zoom=f'<animation effect="zoom" center="231,540" start="100" end="114" time="0" condition="{PORTRAIT_MOBILE}">Conditional</animation>'
        if marker not in xml:
            raise ValueError('Missing Home menu portrait scaling insertion point')
        xml=xml.replace(marker, marker+zoom, 1)
    elif name.endswith('/Includes_Home.xml'):
        anchor='<include name="ImageWidget">'
        if anchor not in xml:
            raise ValueError('Missing ImageWidget portrait scaling include')
        start=xml.index(anchor)
        marker='<control type="group" id="$PARAM[button_id]889">'
        pos=xml.find(marker,start)
        if pos < 0:
            raise ValueError('Missing ImageWidget group portrait scaling insertion point')
        zoom=f'<animation effect="zoom" center="960,540" start="100" end="116" time="0" condition="{PORTRAIT_MOBILE}">Conditional</animation>'
        pos += len(marker)
        xml=xml[:pos]+zoom+xml[pos:]
    return xml


def make_changes(apk: zipfile.ZipFile) -> dict[str,bytes]:
    changes={}
    palettes=color_sets(apk.read(SKIN+'colors/defaults.xml'))
    names='|'.join(re.escape(c) for c in palettes['dark'])
    for name in apk.namelist():
        if not name.startswith(SKIN+'xml/') or not name.endswith('.xml'): continue
        if Path(name).name in EXCLUDED_XML: continue
        before=apk.read(name).decode('utf-8'); after=before
        for tag in COLOR_TAGS:
            after=re.sub(r'(<'+tag+r'(?:\s[^>]*)?>)('+names+r')(</'+tag+r'>)',
                         lambda m:m[1]+'$VAR[InfinityColor_'+m[2]+']'+m[3],after)
        after=re.sub(r'(colordiffuse=")('+names+r')(")',
                     lambda m:m[1]+'$VAR[InfinityColor_'+m[2]+']'+m[3],after)
        after=re.sub(r'(name="colordiffuse"\s+value=")('+names+r')(")',
                     lambda m:m[1]+'$VAR[InfinityColor_'+m[2]+']'+m[3],after)
        after=re.sub(r'\[COLOR ('+names+r')\]',lambda m:'[COLOR $VAR[InfinityColor_'+m[1]+']]',after)
        if name.endswith('/Variables.xml'):
            if 'name="InfinityColor_' in after: raise ValueError('Unexpected pre-existing theme implementation')
            after=after.replace('</includes>',variables(palettes)+'\n</includes>')
        if name.endswith('/Home.xml'):
            after=after.replace('special://xbmc/media/vendor_logo.png','infinity/icon.png')
        after=add_portrait_scaling(name,after)
        if name.endswith('/SkinSettings.xml'):
            marker='<control type="radiobutton" id="701">'
            if after.count(marker)!=1: raise ValueError('Missing exact skin settings insertion point')
            button='''<control type="button" id="7190"><label>Infinity appearance</label><include>DefaultSettingButton</include><onclick>ActivateWindow(1198)</onclick></control>'''
            after=after.replace(marker,button+marker,1)
            init='''<onload condition="!Skin.HasSetting(Infinity.TouchInitialized) + String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)">Skin.SetBool(touchmode)</onload><onload condition="!Skin.HasSetting(Infinity.TouchInitialized) + String.IsEqual(Window(Home).Property(Infinity.DeviceMode),mobile)">Skin.SetBool(Infinity.TouchInitialized)</onload>'''
            after=after.replace('<controls>',init+'\n<controls>',1)
        ET.fromstring(after)
        if after!=before: changes[name]=after.encode('utf-8')
    for mode,palette in palettes.items():
        colors=ET.Element('colors')
        for name,value in palette.items(): ET.SubElement(colors,'color',{'name':name}).text=value
        title={'light':'Light','dark':'Dark','oled':'OLED'}[mode]
        changes[SKIN+'colors/Infinity '+title+'.xml']=ET.tostring(colors,encoding='utf-8',xml_declaration=True)
    changes[SKIN+'xml/Custom_1198_InfinityAppearance.xml']=appearance_dialog()
    icon=(engine.ASSETS/'project_infinity_icon.png').read_bytes()
    changes[SKIN+'media/infinity/icon.png']=icon
    from PIL import Image
    art=Image.open(io.BytesIO(icon)).convert('RGBA');art.thumbnail((660,660),getattr(Image,'Resampling',Image).LANCZOS)
    splash=Image.new('RGB',(1920,1080),(0,0,0))
    splash.paste(art,((1920-art.width)//2,(1080-art.height)//2),art)
    out=io.BytesIO();splash.save(out,'JPEG',quality=95,subsampling=0)
    changes['assets/media/splash.jpg']=out.getvalue()
    if RESUME in apk.namelist():
        text=apk.read(RESUME).decode('utf-8')
        for number,value in [(12021,'Start Over'),(12022,'Continue from {0:s}')]:
            pattern=r'(msgctxt "#'+str(number)+r'"\n)msgid "[^"\n]*"'
            text,count=re.subn(pattern,lambda m:m[1]+'msgid "'+value+'"',text)
            if count!=1: raise ValueError('Unexpected native resume label '+str(number))
        changes[RESUME]=text.encode('utf-8')
    if not all(allowed(n) for n in changes):raise ValueError('Recipe exceeded presentation boundary')
    return changes


def build(apk: Path, manifest: Path, output: Path, receipt: Path) -> None:
    if output.exists() or receipt.exists():raise ValueError('Never overwrite a candidate or receipt')
    baseline=engine.check_engine(apk,manifest)
    with tempfile.TemporaryDirectory(prefix='infinity-presentation-') as tmp:
        locked=Path(tmp)/'locked.apk';engine.overlay(apk,manifest,locked)
        with zipfile.ZipFile(locked) as src:
            additions=make_changes(src)
            output.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(output,'w',allowZip64=True) as dst:
                for item in src.infolist():
                    if engine.signing_member(item.filename) or item.filename in additions:continue
                    dst.writestr(item,src.read(item.filename))
                for name,data in additions.items():dst.writestr(name,data,compress_type=zipfile.ZIP_DEFLATED)
    after=engine.apk_hashes(output)
    changes={n:h for n,h in after.items() if baseline['files'].get(n)!=h}
    receipt.write_text(json.dumps({'schema':RECIPE_VERSION,'engine_base_sha256':baseline['base_apk_sha256'],
        'bridge_version':engine.contract()['bridge_version'],'recipe_sha256':engine.sha(Path(__file__).read_bytes()),
        'changes':changes,'device_accepted':False,'signing':'unsigned',
        'tools_inventory':'Profile-installed Infinity tools are not reconstructed or silently claimed present.'},indent=2)+'\n')
    verify(output,manifest,receipt)


def verify(apk: Path, manifest: Path, receipt: Path) -> None:
    base=json.loads(manifest.read_text());engine.validate_engine_metadata(base)
    record=json.loads(receipt.read_text())
    if record.get('schema')!=RECIPE_VERSION or record.get('engine_base_sha256')!=base['base_apk_sha256']:
        raise ValueError('Presentation receipt does not match the pinned engine')
    if record.get('recipe_sha256')!=engine.sha(Path(__file__).read_bytes()):raise ValueError('Wrong presentation recipe')
    changes=record.get('changes',{})
    if not changes or not all(allowed(n) for n in changes):raise ValueError('Protected member in presentation receipt')
    expected=dict(base['files']);expected.update(changes)
    actual=engine.apk_hashes(apk)
    if actual!=expected:raise ValueError('Final package content differs from engine + exact presentation receipt')
    for name,path in engine.LOCK_FILES.items():
        if actual.get(path)!=engine.sha((engine.ASSETS/name).read_bytes()):raise ValueError('Original lock asset changed')
    if actual.get(SKIN+'media/infinity/icon.png')!=engine.sha((engine.ASSETS/'project_infinity_icon.png').read_bytes()):
        raise ValueError('Approved Infinity icon missing')
    with zipfile.ZipFile(apk) as z:
        for name in changes:
            if name.endswith('.xml'):ET.fromstring(z.read(name))
        settings=z.read(SKIN+'xml/SkinSettings.xml').decode()
        if settings.count('id="7190"')!=1 or 'ActivateWindow(1198)' not in settings:
            raise ValueError('Missing appearance settings connection')
        home=z.read(SKIN+'xml/Home.xml').decode()
        ihome=z.read(SKIN+'xml/Includes_Home.xml').decode()
        if PORTRAIT_MOBILE not in home or PORTRAIT_MOBILE not in ihome:
            raise ValueError('Missing front-display portrait scaling rules')
        for name in (SKIN+'xml/Variables.xml',SKIN+'xml/Custom_1198_InfinityAppearance.xml'):
            if name not in actual:raise ValueError('Missing theme consumer')
    engine.check_apk_contract(apk)
    print('PASS: Infinity 1.0 themes + front-display portrait scaling with native engine protected. Device acceptance pending.')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','verify'])
    p.add_argument('--apk',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.command=='build':
        if a.output is None:p.error('--output is required to build')
        build(a.apk,a.manifest,a.output,a.receipt)
    else:verify(a.apk,a.manifest,a.receipt)
if __name__=='__main__':main()
