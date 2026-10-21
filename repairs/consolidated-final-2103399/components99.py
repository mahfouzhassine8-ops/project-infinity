"""Final Option B reference details over the compiled, tested 2103398 candidate.

Only popup presentation, its close-animation barrier and two versions change.
Native/DEX, selected-item validation, action handlers and provider code are reused.
"""
import ast
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent/'consolidated-2103398'))
import components98 as c

VERSIONS = {a:v for a,_,v in c.PACKAGES}
VERSIONS.update({c.UI:'0.1.10', c.SKIN:'1.0.5.236'})
META = {121:'YearAndEpisode',122:'Certification',123:'Runtime',124:'Rating',125:'Genres'}
ICONS = {101:'play',102:'movie',103:'favourite',104:'info'}
INK = 'FF00111C'
PRIMARY_INK = '$VAR[InfinityOptionBPrimaryInk]'
MODAL_BARRIER = b'''
def _wait_for_option_b_close(xbmc, gui, modal_id, return_modal=None):
    """A closing Kodi dialog is still modal; wait without weakening capture."""
    if not isinstance(modal_id, int) or not 13000 <= modal_id <= 13099:
        return False
    monitor = xbmc.Monitor()
    deadline = time.monotonic() + 1.0
    while gui.getCurrentWindowDialogId() == modal_id:
        if time.monotonic() >= deadline or monitor.waitForAbort(0.02):
            return False
    target = gui.getCurrentWindowDialogId()
    expected = (target in (0, -1, 9999) if return_modal is None else
                isinstance(return_modal, int) and 13000 <= return_modal <= 13099 and
                return_modal != modal_id and target == return_modal)
    return not monitor.abortRequested() and gui.getCurrentWindowId() == 10000 and expected

'''
MODAL_DETAILS_OLD=b'                finally: details.close();del details'
MODAL_DETAILS_NEW=b'''                finally:
                    details_id=getattr(details,'modal_id',0)
                    details.close();del details
                _wait_for_option_b_close(xbmc,xbmcgui,details_id,self.modal_id)'''
INFO_OLD=b"                extra = ' \xe2\x80\xa2 '.join(v for v in (snapshot.release_date, snapshot.credits) if v)"
INFO_NEW=b'''                extra = '\\n'.join(label+': '+value for label,value in (
                    ('Year / episode', props['YearAndEpisode']), ('Release date', snapshot.release_date),
                    ('Rating', props['Rating']), ('Certification', snapshot.certification),
                    ('Genres', snapshot.genres), ('Runtime', props['Runtime']),
                    ('Credits', snapshot.credits)) if value)'''


def popup(raw):
    root = ET.fromstring(raw)
    group = root.find('.//control[@id="100"]')
    for ident, prop in META.items():
        label = group.find('control[@id="%d"]'%ident)
        c.require(label is not None, 'actual metadata label missing')
        at = list(group).index(label)
        # Existing rounded fill/rim assets, no artwork or invented metadata.
        for offset, texture, color in [(80,'field','InfinityLegacyField'),(90,'rim','InfinityLegacyBorder')]:
            image = ET.Element('control', {'type':'image','id':str(ident+offset)})
            ET.SubElement(image,'visible').text='!String.IsEmpty(Window.Property(Infinity.HomeOptionB.'+prop+'))'
            ET.SubElement(image,'texture',{'border':'8','colordiffuse':'$VAR['+color+']'}).text='infinity_glass/'+texture+'.png'
            group.insert(at,image);at+=1
        align=label.find('align')
        if align is None:align=ET.SubElement(label,'align')
        align.text='center'
        label.find('textcolor').text='$VAR[InfinityLegacyText]'
    for ident, icon in ICONS.items():
        button=group.find('control[@id="%d"]'%ident)
        caption=button.find('label')
        c.require(caption.text in ('Play','Trailer','Favorite','More Info'),'complete original action label required')
        caption.text='    '+caption.text
        if ident==101:
            # The approved primary action stays cyan when focus moves away.
            for tag in ('texturefocus','texturenofocus'):
                button.find(tag).text='infinity_glass/field.png'
                button.find(tag).set('colordiffuse','$VAR[InfinityLegacyAccent]')
            button.find('textcolor').text=PRIMARY_INK
            ET.SubElement(button,'focusedcolor').text=PRIMARY_INK
        image=ET.SubElement(group,'control',{'type':'image','id':str(ident+50)})
        ET.SubElement(image,'visible').text='!String.IsEqual(Window.Property(Infinity.HomeOptionB.Expanded),true)'
        ET.SubElement(image,'aspectratio').text='keep'
        ET.SubElement(image,'texture',{'colordiffuse':PRIMARY_INK if ident==101 else '$VAR[InfinityLegacyText]'}).text='infinity_ui/icons/'+icon+'.png'
    return c.xml(root)


def runtime(raw):
    before=ast.parse(raw)
    old=b"            self.setProperty('Infinity.HomeOptionB.Expanded', 'true' if self.expanded else 'false')"
    code=b'''            # Reference chips and action glyphs share the existing responsive geometry.
            self.modal_id=xbmcgui.getCurrentWindowDialogId()
            for ident,key in ((121,'year'),(122,'certification'),(123,'runtime'),(124,'rating'),(125,'genres')):
                xx,yy,ww,hh=bounds['details'][key]
                for decoration in (ident+80,ident+90):
                    ctrl=self.getControl(decoration)
                    ctrl.setPosition(xx,yy);ctrl.setWidth(ww);ctrl.setHeight(hh)
                label=self.getControl(ident)
                label.setPosition(xx+4,yy);label.setWidth(max(1,ww-8))
            # Widths are measured from the actual existing Roboto 22 px action font.
            for ident,coords,caption_width in zip((151,152,153,154),bounds['buttons'],(41,61,78,94)):
                xx,yy,ww,hh=coords
                icon=self.getControl(ident)
                side=22
                icon.setPosition(round(xx+ww/2-caption_width/2-18),round(yy+(hh-side)/2))
                icon.setWidth(side);icon.setHeight(side)
'''+old
    result=c.once(raw,old,code)
    anchor=b'def _show_verified_hold('
    result=c.once(result,anchor,MODAL_BARRIER+anchor)
    closed=b"        choice=window.selected_action\n"
    observed=closed+b"        modal_id=window.modal_id\n"
    result=c.once(result,closed,observed)
    dispatch=b'    return bool(choice and _perform(xbmc,xbmcgui,snapshot,choice,native))'
    guarded=b'    return bool(choice and _wait_for_option_b_close(xbmc,xbmcgui,modal_id) and\n                _perform(xbmc,xbmcgui,snapshot,choice,native))'
    result=c.once(result,dispatch,guarded)
    result=c.once(result,MODAL_DETAILS_OLD,MODAL_DETAILS_NEW)
    result=c.once(result,INFO_OLD,INFO_NEW)
    after=ast.parse(result)
    # Every capture/validation/action function is byte-for-byte AST equivalent.
    b={n.name:ast.dump(n) for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    a={n.name:ast.dump(n) for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    for name in b:
        if name!='_show_verified_hold':c.require(a[name]==b[name],'nonpresentation function changed '+name)
    restored=result.replace(code,old,1).replace(MODAL_BARRIER+anchor,anchor,1).replace(observed,closed,1).replace(guarded,dispatch,1).replace(MODAL_DETAILS_NEW,MODAL_DETAILS_OLD,1).replace(INFO_NEW,INFO_OLD,1)
    c.require(restored==raw,'unexpected runtime edit outside presentation/close barrier')
    return result


def components(before):
    after=dict(before)
    popup_key=c.UI+'/resources/skins/Default/1080i/InfinityHomeOptionB.xml'
    after[popup_key]=popup(before[popup_key])
    after[c.SKIN+'/unified/InfinityHomeOptionB.xml']=after[popup_key]
    after[c.UI+'/home_option_b.py']=runtime(before[c.UI+'/home_option_b.py'])
    palettes=0
    for name,body in before.items():
        if not name.startswith(c.SKIN+'/') or not name.endswith('.xml') or b'name="InfinityLegacyAccent"' not in body:
            continue
        root=ET.fromstring(body);accent=root.find('variable[@name="InfinityLegacyAccent"]')
        if accent is None:continue
        c.require(root.find('variable[@name="InfinityOptionBPrimaryInk"]') is None,'popup foreground already declared')
        light=next(v.get('condition') for v in accent.findall('value') if 'Infinity.NativeSystemTheme),light)' in v.get('condition',''))
        var=ET.SubElement(root,'variable',{'name':'InfinityOptionBPrimaryInk'})
        ET.SubElement(var,'value',{'condition':light}).text='FFFFFFFF'
        ET.SubElement(var,'value').text=INK
        after[name]=c.xml(root);palettes+=1
    c.require(palettes==10,'all ten actual legacy palette declarations required')
    for addon,old in ((c.UI,'0.1.9'),(c.SKIN,'1.0.5.235')):
        key=addon+'/addon.xml'
        after[key]=c.once(before[key],('version="'+old+'"').encode(),('version="'+VERSIONS[addon]+'"').encode())
    for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
        key=c.SKIN+'/'+leaf;value=json.loads(before[key])
        value.update(candidate=236,skin_version=VERSIONS[c.SKIN],candidate_locked=False)
        for field in ('version','candidate_version'):
            if field in value:value[field]=VERSIONS[c.SKIN]
        if 'protected_files' in value:value['protected_files']={p:c.sha(after[c.SKIN+'/'+p]) for p in value['protected_files']}
        after[key]=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    changed={n:b for n,b in after.items() if before[n]!=b}
    c.require(len(changed)==17 and all(n.startswith((c.UI+'/',c.SKIN+'/')) for n in changed),'final presentation scope changed')
    c.require(not any('cobra' in n.lower() for n in changed),'Cobra change prohibited')
    for n,b in changed.items():
        if n.endswith('.xml'):ET.fromstring(b)
        if n.endswith('.py'):ast.parse(b)
    return after,changed
