#!/usr/bin/env python3
"""Generate presentation-only .207 repairs from exact approved .204 sources."""
from pathlib import Path
import argparse, copy, hashlib, json, re
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parent
VERSION = '1.0.5.207'
POWER_SHA = '149b614b9dd96094e64c7b7a837fbc911bfceda40e4ecef84716f7a3a6220d78'
GEOMETRY = ('left','top','right','bottom','width','height','centerleft','centertop','posx','posy')
LEGACY = '$VAR[InfinityLegacy'

def tag(parent, element, value=None, **attrs):
    node=E.SubElement(parent,element,{k:str(v) for k,v in attrs.items()})
    if value is not None: node.text=str(value)
    return node

def setv(node, name, value):
    for old in node.findall(name): node.remove(old)
    return tag(node,name,value)

def geo(node, **values):
    for name in GEOMETRY:
        for old in node.findall(name): node.remove(old)
    for name,value in values.items(): tag(node,name,value)
    return node

def control(parent, kind, ident=None, **bounds):
    c=tag(parent,'control',type=kind,**({'id':ident} if ident is not None else {}))
    return geo(c,**bounds)

def label(parent, text, ident=None, font='InfinitySmall', color='Text', **bounds):
    c=control(parent,'label',ident,**bounds)
    tag(c,'font',font);tag(c,'label',text);tag(c,'textcolor',LEGACY+color+']')
    tag(c,'aligny','center');tag(c,'scroll','true')
    return c

def image(parent, texture, tint=None, ident=None, **bounds):
    c=control(parent,'image',ident,**bounds)
    tag(c,'texture',texture,**({'colordiffuse':tint} if tint else {}))
    return c

def surface(parent, ident=None):
    c=image(parent,'infinity_glass/surface.png','$VAR[InfinityUIRepairSurface]',ident,left=0,top=0,width='100%',height='100%')
    c.find('texture').set('border','24')
    if ident is None:
        rim=image(parent,'infinity_glass/rim.png','$VAR[InfinityGlassSpecular]',left=0,top=0,width='100%',height='100%')
        rim.find('texture').set('border','24')
    return c

def button_style(c):
    for name,tex,color in [('texturefocus','infinity_glass/focus.png','Accent'),('texturenofocus','infinity_glass/field.png','Field')]:
        n=setv(c,name,tex);n.set('border','16');n.set('colordiffuse',LEGACY+color+']')
    for name,color in [('textcolor','Text'),('focusedcolor','Text'),('disabledcolor','Disabled')]: setv(c,name,LEGACY+color+']')
    setv(c,'font','InfinitySmall');setv(c,'aligny','center');setv(c,'scroll','true')

def close(parent, ident, target, action='PreviousMenu'):
    c=control(parent,'button',ident,right=18,top=18,width=64,height=64)
    tag(c,'label','');tag(c,'onclick',action)
    for direction in ['onleft','onright','onup','ondown']: tag(c,direction,target)
    tag(c,'texturefocus','infinity_legacy/close_focus.png',colordiffuse=LEGACY+'Accent]')
    tag(c,'texturenofocus','infinity_legacy/close.png',colordiffuse=LEGACY+'Text]')
    return c

def scrollbar(parent, ident, target, **bounds):
    c=control(parent,'scrollbar',ident,**bounds)
    for name,color in [('texturesliderbackground','Field'),('texturesliderbar','Track'),('texturesliderbarfocus','Accent'),('textureslidernib','Track'),('textureslidernibfocus','Accent')]:
        tag(c,name,'infinity_legacy/track.png',border=6,colordiffuse=LEGACY+color+']')
    for direction in ['onleft','onright','onup','ondown']:tag(c,direction,target)
    tag(c,'showonepage','false');tag(c,'orientation','vertical')
    return c

def fresh_window(old):
    root=E.Element('window',old.attrib)
    for c in old:
        if c.tag!='controls':root.append(copy.deepcopy(c))
    return root,tag(root,'controls')

def modal(old):
    root,controls=fresh_window(old)
    image(controls,'infinity_ui/contract_white.png',LEGACY+'Scrim]',left=0,top=0,width='100%',height='100%')
    panel=control(controls,'group',9900,left='3.5%',right='3.5%',top='3.5%',bottom='3.5%')
    surface(panel)
    return root,panel

def textbox(parent, text, ident=None, font='InfinitySmall', **bounds):
    c=control(parent,'textbox',ident,**bounds)
    tag(c,'label',text);tag(c,'font',font);tag(c,'textcolor',LEGACY+'Text]');tag(c,'align','left')
    return c

def addon_info(old):
    root,panel=modal(old)
    tag(panel,'visible','!Window.isVisible(AddonSettings) + !Window.IsActive(TextViewer)')
    close(panel,995,9000)
    label(panel,'$LOCALIZE[24003]',2,font='InfinityBodyBold',left=24,top=18,right=106,height=60)
    art=image(panel,'$VAR[InfinityPolishIcon0]','$VAR[InfinityPolishIcon0Tint]',left=18,top=106,width='28%',height=150)
    tag(art,'aspectratio','keep')
    actions=control(panel,'grouplist',9000,left=18,top=274,width='28%',bottom=18)
    for name,value in [('orientation','vertical'),('itemgap',8),('scrolltime',140),('onleft',995),('onright',61),('onup',995),('ondown',995)]:tag(actions,name,value)
    for original in old.findall(".//control[@id='9000']/control"):
        c=copy.deepcopy(original);geo(c,width='100%',height=72)
        setv(c,'scroll','true');actions.append(c)
        if c.get('id')=='13':
            setv(c,'font','InfinityTiny');setv(c,'align','left');setv(c,'textoffsetx',78);setv(c,'radioposx',8)
    detail=control(panel,'group',9901,left='34%',right=24,top=106,bottom=18)
    label(detail,'[B]$INFO[ListItem.AddonName][/B]',font='InfinityBodyBold',left=0,top=0,width='100%',height=42)
    for y,caption,info in [(48,'$LOCALIZE[146]','$INFO[ListItem.AddonType]'),(82,'$LOCALIZE[21863]','$INFO[ListItem.AddonCreator]'),(116,'$LOCALIZE[24051]','$INFO[ListItem.AddonVersion]')]:
        label(detail,caption,font='InfinityTiny',color='Secondary',left=0,top=y,width='22%',height=32)
        label(detail,info,font='InfinitySmall',left='24%',top=y,right=0,height=32)
    textbox(detail,'$INFO[ListItem.AddonSummary]',left=0,top=158,width='100%',height=72)
    label(detail,'$VAR[AddonInfoHeading]',font='InfinitySmall',color='Accent',left=0,top=238,width='100%',height=34)
    extra='$INFO[ListItem.AddonDisclaimer,[CR][CR]$LOCALIZE[24052]:[CR]]$INFO[ListItem.AddonBroken,[CR][CR]$LOCALIZE[24096]:[CR]]'
    for ident,page,condition in [(400,60,'!String.IsEmpty(ListItem.AddonDisclaimer)'),(401,61,'String.IsEmpty(ListItem.AddonDisclaimer)')]:
        group=control(detail,'group',left=0,top=280,width='100%',bottom=0);tag(group,'visible',condition)
        text=textbox(group,'$INFO[ListItem.AddonSummary,$LOCALIZE[20037]:[CR],[CR][CR]]$VAR[AddonInfoDescription]'+extra,ident,left=0,top=0,right=34,height='100%')
        tag(text,'pagecontrol',page)
        scrollbar(group,page,9000,right=0,top=0,width=26,height='100%')
    setv(actions,'onright','61');actions.find('onright').set('condition','String.IsEmpty(ListItem.AddonDisclaimer)')
    tag(actions,'onright',60,condition='!String.IsEmpty(ListItem.AddonDisclaimer)')
    return root

def context_menu(old):
    root,controls=fresh_window(old)
    panel=control(controls,'group',9900,left=0,top=0,width='90%',height='90%')
    bg=surface(panel,999)
    tag(bg,'bordertexture','infinity_glass/rim.png',border=24,colordiffuse=LEGACY+'Border]');tag(bg,'bordersize',2)
    close(panel,995,996)
    label(panel,'Choose an action',font='InfinitySmall',color='Secondary',left=24,top=18,right=106,height=64)
    # Fixed chrome is supplied by the inset parent. Both native maximum sizes
    # derive from the same viewport: bg.Size - list.Size is exactly 104 units.
    inset=control(panel,'group',9901,left=18,right=18,top=88,bottom=16)
    group=control(inset,'grouplist',996,left=0,top=0,width='100%')
    tag(group,'height','auto',max='100%',min=1)
    for name,value in [('itemgap',6),('orientation','vertical'),('scrolltime',120),('onleft',995),('onright',995),('onup',996),('ondown',996)]:tag(group,name,value)
    template=copy.deepcopy(old.find(".//control[@id='1000']"))
    geo(template,left=0,top=0,width='100%',height=82)
    setv(template,'scroll','true')
    # No focus zoom may paint/hit beyond a clipped native row.
    for n in template.findall('animation'):template.remove(n)
    group.append(template)
    return root

def health(old):
    root,panel=modal(old)
    close(panel,1188199,1188101,'Dialog.Close(1188)')
    icon=image(panel,'infinity_health/icon_health.png',LEGACY+'Accent]',left=24,top=22,width=64,height=64);tag(icon,'aspectratio','keep')
    label(panel,'Kodi Health Center',font='InfinityBodyBold',left=108,top=18,right=270,height=44)
    label(panel,'Diagnose • Repair • Maintain',font='InfinityTiny',color='Secondary',left=108,top=64,right=270,height=32)
    scan=copy.deepcopy(old.find(".//control[@id='1188151']"));geo(scan,right=104,top=24,width=136,height=64)
    button_style(scan);setv(scan,'align','center');setv(scan,'onup',1188199);setv(scan,'ondown',1188101);panel.append(scan)
    group=control(panel,'grouplist',1188000,left=24,top=122,right=60,bottom=64)
    for name,value in [('orientation','vertical'),('itemgap',16),('scrolltime',140),('pagecontrol',1188060),('onleft',1188199),('onright',1188060),('onup',1188151),('ondown',1188151)]:tag(group,name,value)
    status=control(group,'group',height=310,width='100%');surface(status)
    label(status,'Reported system status',font='InfinityTiny',color='Secondary',left=20,top=14,right=20,height=30)
    state=label(status,'$VAR[InfinityUIHealthStatus]',font='InfinityBodyBold',left=20,top=50,right=20,height=40)
    setv(state,'textcolor','$VAR[InfinityUIHealthStatusColor]')
    text=textbox(status,'$INFO[Window(Home).Property(KHC.StatusDetail)]',font='InfinityTiny',left=20,top=98,right=20,height=76)
    label(status,'Saved scan: $INFO[Window(Home).Property(KHC.LastScan)]',font='InfinityTiny',color='Secondary',left=20,top=184,right=20,height=32)
    label(status,'Saved baseline (reported)',font='InfinityTiny',color='Secondary',left=20,top=224,right=20,height=28)
    textbox(status,'$INFO[Window(Home).Property(KHC.Baseline)]',font='InfinityTiny',left=20,top=260,right=20,height=44)
    order=[1188101,1188102,1188103,1188111,1188112,1188113,1188114,1188115,1188121,1188122,1188123,1188131,1188141]
    sections={0:('Diagnostics','Find and understand current issues.'),3:('Repair & Maintenance','Inspect and maintain your installation.'),8:('Export & Support','Create exports and support packages.'),11:('Tools & Help','More tools and practical guidance.')}
    originals={int(c.get('id')):c for c in old.findall('.//control') if c.get('id') and c.findall('onclick')}
    flat=list(old.find('controls'))
    for i,ident in enumerate(order):
        if i in sections:
            row=control(group,'group',width='100%',height=84);title,subtitle=sections[i]
            label(row,title,font='InfinityBodyBold',left=4,top=6,right=4,height=38)
            label(row,subtitle,font='InfinityTiny',color='Secondary',left=4,top=48,right=4,height=30)
        oldbutton=originals[ident];index=flat.index(oldbutton)
        desc=next(c for c in flat[index+1:] if c.get('type')=='label' and c.findtext('wrapmultiline')=='true')
        art=next(c for c in flat[index+1:] if c.get('type')=='image')
        row=control(group,'group',width='100%',height=156)
        button=copy.deepcopy(oldbutton);geo(button,left=0,top=0,width='100%',height=156)
        button_style(button);setv(button,'align','left');setv(button,'aligny','top');setv(button,'textoffsetx',82);setv(button,'textoffsety',14)
        for name,value in [('onup',order[i-1] if i else 1188151),('ondown',order[i+1] if i+1<len(order) else 1188151),('onleft',1188199),('onright',1188060)]:setv(button,name,value)
        row.append(button)
        icon=copy.deepcopy(art);geo(icon,left=20,top=20,width=44,height=44);row.append(icon)
        body=copy.deepcopy(desc);geo(body,left=82,top=60,right=22,height=80);setv(body,'font','InfinityTiny');setv(body,'aligny','top');row.append(body)
    scrollbar(panel,1188060,1188101,right=22,top=122,width=26,bottom=64)
    label(panel,'Health Center $INFO[Window(Home).Property(KHC.Version)]',font='InfinityTiny',color='Secondary',left=24,bottom=18,right=24,height=30)
    return root

def nav(old):
    root=copy.deepcopy(old);group=root.find(".//control[@id='1198899']")
    findrow=lambda ident:next(c for c in group if c.find(".//control[@id='%s']"%ident) is not None)
    group.remove(findrow('1198107'))
    hub=findrow('1198503');group.remove(hub);group.insert(list(group).index(findrow('1198304')),hub)
    # Existing extras remain in the same scrolling list after the primary Power slot.
    return root

def system_hub(old):
    root=copy.deepcopy(old);group=root.find(".//control[@id='1191888']")
    row=next(c for c in group if c.find(".//control[@id='1191105']") is not None);group.remove(row)
    for c in root.findall('.//control'):
        for name in ('onup','ondown','onleft','onright'):
            for target in c.findall(name):
                if target.text=='1191105':target.text='1191107'
        if c.get('id')=='1191199':
            for name in ('onleft','onright','onup','ondown'):setv(c,name,1191101)
        if c.get('type')=='label' and c.findtext('label'):
            setv(c,'scroll','true')
    return root

def settings(old, addon=False):
    root,panel=modal(old)
    close(panel,9002,3 if addon else 5,'Action(Back)')
    heading=copy.deepcopy(old.find(".//control[@id='2']")) if not addon else control(panel,'label',2)
    geo(heading,left=24,top=18,right=106,height=64);setv(heading,'font','InfinityBodyBold');setv(heading,'scroll','true');setv(heading,'textcolor',LEGACY+'Text]')
    if not addon:panel.append(heading)
    for ident in ([3,5,60,7,8,9,11,12,13,14,10,9001] if addon else [5,60,7,8,9,11,12,13,14,9001]):
        original=old.find(".//control[@id='%s']"%ident)
        c=copy.deepcopy(original);panel.append(c)
        if ident==3:
            geo(c,left=24,top=104,right=24,height=72);setv(c,'scrolltime',120)
            setv(c,'onup',9002);setv(c,'ondown',5)
        elif ident==5:
            geo(c,left=24,top=190 if addon else 104,right=62,bottom=112)
            setv(c,'scrolltime',140)
        elif ident==60:
            geo(c,right=22,top=190 if addon else 104,width=26,bottom=112)
        elif ident==9001:
            geo(c,left=24,bottom=22,right=24,height=72);setv(c,'itemgap',12)
            for b in c.findall('control'):
                geo(b,width='30%',height=72);setv(b,'scroll','true')
        elif ident==10:
            geo(c,width='24%',height=72);setv(c,'scroll','true')
        elif ident in [7,8,9,12,13]:
            geo(c,width='100%',height=88);setv(c,'scroll','true')
        elif ident==14:geo(c,width='100%',height=52)
        elif ident==11:geo(c,width='100%',height=3)
    return root

def textviewer(old):
    root,panel=modal(old)
    close(panel,995,61,'Dialog.Close(textviewer)')
    # Preserve the native paging receiver and content IDs.
    for ident in [62,1,5,61]:
        c=copy.deepcopy(old.find(".//control[@id='%s']"%ident));panel.append(c)
        if ident==1:geo(c,left=24,top=18,right=106,height=64);setv(c,'scroll','true')
        elif ident==5:geo(c,left=24,top=104,right=62,bottom=24);setv(c,'font','InfinityBody')
        elif ident==61:
            geo(c,right=22,top=104,width=26,bottom=24)
            setv(c,'onleft',995);setv(c,'onright',995)
    return root

def keyboard(old, legacy):
    root,panel=modal(old)
    tag(panel,'visible','!Window.IsVisible(numericinput)')
    close(panel,995,300)
    heading=label(panel,'',311,font='InfinityBodyBold',left=24,top=18,right=106,height=64)
    edit=copy.deepcopy(old.find(".//control[@id='312']"))
    geo(edit,left=24,top=100,right=24,height=72);panel.append(edit)
    # Keep the optional native suggestion headings within the panel, not above it.
    for ident,y in [(313,184),(314,216)]:
        c=copy.deepcopy(old.find(".//control[@id='%s']"%ident));geo(c,left=24,top=y,right=24,height=30)
        setv(c,'font','InfinityTiny');setv(c,'scroll','true');panel.append(c)
    area=copy.deepcopy(old.find(".//control[@id='4000']"))
    # Five equal tracks keep every native key inside the current usable panel.
    geo(area,left=24,right=24,top='40%',bottom=20);panel.append(area)
    key_style=legacy.find("include[@name='InfinityLegacy_KeyboardButton']")
    rows=area.findall("control[@type='grouplist']")
    for i,row in enumerate(rows):
        y=min(i,4)*20
        geo(row,left=0,top=str(y)+'%',width='100%',height='18%')
        setv(row,'itemgap',2);setv(row,'usecontrolcoords','false')
        for index,c in enumerate(row.findall('control')):
            for inc in list(c.findall('include')):
                if inc.text=='InfinityLegacy_KeyboardButton':
                    c.remove(inc)
                    for child in key_style:
                        if child.tag not in GEOMETRY and c.find(child.tag) is None:c.append(copy.deepcopy(child))
            ident=c.get('id')
            w='6.6%' if ident and 100<=int(ident)<=171 else '14.2%'
            if ident in ['307','304','305','306']:w='7.1%'
            if ident=='32':w='28.4%'
            # The second bottom track contains the optional text overlays.
            # Its empty fourth label spans the two cursor buttons.
            if i==5:w=['14.2%','28.4%','14.2%','14.2%','14.2%'][index]
            geo(c,width=w,height='100%');setv(c,'font','InfinitySmall');setv(c,'aligny','center')
            if c.find('label') is not None:setv(c,'scroll','true')
    for c in area.findall('control'):
        if c.get('type')=='label':
            y=20 if c.findtext('label')=='20178' else 40
            geo(c,left=0,top=str(y)+'%',width='14.2%',height='18%');setv(c,'font','InfinityTiny')
        elif c.get('type')=='image':
            y=20 if (c.findtext('top') or '').startswith('10.') else 40
            geo(c,centerleft='7.1%',top=str(y+2)+'%',width=36,height='14%');tag(c,'aspectratio','keep')
        elif c.get('type')=='group':
            geo(c,left=0,top='82%',width='100%',height='14%')
            for x,center in zip(c.findall('control'),['7.1%','28.4%','49.7%','78.1%']):
                geo(x,centerleft=center,top=0,width=36,height='100%');setv(x,'aspectratio','keep')
    return root

def replace_include(text, name, transform):
    start=text.index('<include name="'+name+'">');depth=0;end=None
    for m in re.finditer(r'</?include\b[^>]*>',text[start:]):
        if m.group().endswith('/>'):continue
        depth+=-1 if m.group().startswith('</') else 1
        if depth==0:end=start+m.end();break
    if end is None:raise ValueError('Unbalanced include '+name)
    node=transform(E.fromstring(text[start:end]));E.indent(node,space='  ')
    return text[:start]+E.tostring(node,encoding='unicode')+text[end:]

def directory(n):
    outer=n.find('control');inner=outer.find('control')
    geo(inner,left='3.3333%',right='3.3333%',top='15%',bottom='6%')
    children=list(inner);header=children[:7]
    for i,c in enumerate(header):
        if i==0:geo(c,left=0,top=0,width='100%',height=64)
        elif i==1:geo(c,left=16,top=16,width=32,height=32)
        elif i==2:geo(c,left=64,top=8,right=156,height=48);setv(c,'scroll','true')
        else:geo(c,right=116-(i-3)*40,top=18,width=28,height=28)
    for c in inner.findall('control'):
        if c.get('id')=='50':
            geo(c,left=0,top=84,right=30,bottom=0)
            for layout in list(c):
                if layout.tag not in ('itemlayout','focusedlayout'):continue
                compact=n.get('name').endswith('Compact');layout.set('height','82' if compact else '88')
                for x in layout.findall('control'):
                    if x.findtext('label')=='$INFO[ListItem.Label]':
                        geo(x,left=76,top=6,right=50,height=36)
                        setv(x,'scroll','true' if layout.tag=='focusedlayout' else 'false')
                        setv(x,'textcolor','$VAR[InfinityDiggzPrimaryText]')
                        for a in x.findall('animation'):a.set('end','0,16')
                    elif x.findtext('label')=='$INFO[ListItem.Label2]':
                        geo(x,left=76,top=48,right=50,height=28)
                        setv(x,'scroll','true' if layout.tag=='focusedlayout' else 'false')
                        setv(x,'textcolor','$VAR[InfinityDiggzSecondaryText]')
                    elif x.get('type')=='image':
                        tex=x.find('texture');value=tex.text if tex is not None else ''
                        if x.findtext('width')=='100%':geo(x,left=0,top=2,width='100%',bottom=4)
                        elif value in ['infinity_ui/icons/next.png','infinity_ui/icons/play.png'] and (x.findtext('left') or '').startswith('96.'):
                            geo(x,right=14,top=28,width=24,height=24)
                        elif value=='infinity_ui/contract_white.png':geo(x,left=10,top=12,width=52,height=56)
                        else:geo(x,left=18,top=18,width=36,height=44)
        elif c.get('id')=='95060':geo(c,right=0,top=84,width=18,bottom=0)
    return n

def cinema(n):
    for panel in n.findall(".//control[@id='50']"):
        for layout in list(panel):
            if layout.tag not in ('itemlayout','focusedlayout'):continue
            layout.set('height','88');layout.attrib.pop('aspectratio',None)
            for c in layout.findall('control'):
                if c.get('type')=='label' and c.findtext('label')=='$INFO[ListItem.Label]':
                    geo(c,left='2.2727%',top=6,right=66,height=36)
                    setv(c,'scroll','true' if layout.tag=='focusedlayout' else 'false')
                    if c.findtext('visible')=='String.IsEmpty(ListItem.Label2)':setv(c,'top',22)
                elif c.findtext('label')=='$INFO[ListItem.Label2]':geo(c,left='2.2727%',top=48,right=66,height=28)
                elif c.findtext('label')=='›':geo(c,right=14,top=22,width=30,height=44)
                elif c.get('type')=='image' and c.findtext('texture')=='$VAR[ListItemOverlay]':geo(c,right=14,top=22,width=30,height=44)
    return n

def select_layout(n):
    original=n.find('control');panel=copy.deepcopy(original)
    geo(panel,left='3.5%',right='3.5%',top='3.5%',bottom='3.5%')
    # Old item-count slides belonged to the old partial-height backgrounds.
    # They must not move the new full, viewport-bounded panel or page label.
    for owner in panel.iter():
        for animation in list(owner.findall('animation')):
            if animation.get('effect')=='slide' and 'NumItems' in animation.get('condition',''):
                owner.remove(animation)
    # Keep all native lists, labels and actions; replace conditional partial backgrounds.
    for c in list(panel):
        if c.get('type')=='image':panel.remove(c)
    surface(panel)
    # Move surfaces beneath controls.
    for c in list(panel)[-2:]:panel.remove(c);panel.insert(0,c)
    for c in panel.findall('control'):
        ident=c.get('id')
        if c.get('type')=='button' and ident is None:
            geo(c,right=18,top=18,width=64,height=64)
            for inc in c.findall('include'):
                if inc.text=='InfinityLegacy_DialogCloseButton':inc.text='InfinityLegacy_DialogCloseButtonClassic'
        elif ident=='1':geo(c,left=24,top=18,right=106,height=64);setv(c,'scroll','true')
        elif ident=='4':geo(c,left=24,top=112,right=64,height=80)
        elif ident in ['3','6']:
            geo(c,left=24,top=112,right=64,bottom=150)
            for layout in list(c):
                if layout.tag not in ['itemlayout','focusedlayout']:continue
                layout.set('height','156' if ident=='6' else '76');layout.set('width','100%');layout.attrib.pop('aspectratio',None)
                for x in layout.findall('control'):
                    if x.get('type')=='label':
                        geo(x,left=108 if ident=='6' else 18,top=12,right=18,height=40)
                        setv(x,'scroll','true' if layout.tag=='focusedlayout' else 'false')
                    elif x.get('type')=='textbox':geo(x,left=108,top=60,right=18,height=80)
                    elif x.get('type')=='image' and x.findtext('texture') in ['$INFO[ListItem.Icon]','$VAR[DialogSelectImage]']:geo(x,left=12,top=12,width=80,height=120)
                    elif x.get('type')=='image':geo(x,left=0,top=0,width='100%',height='96%')
        elif ident=='61':geo(c,right=22,top=112,width=26,bottom=150)
        elif ident=='90':
            geo(c,left=24,bottom=22,right=24,height=72);setv(c,'orientation','horizontal');setv(c,'itemgap',12)
            for x in c.findall('control'):geo(x,width='46%',height=72);setv(x,'scroll','true')
        elif c.get('type')=='group':
            for x in c.findall('control'):
                if x.get('type')=='label':geo(x,left=24,bottom=104,right=24,height=32)
                elif x.get('id')=='90':
                    geo(x,left=24,bottom=22,right=24,height=72);setv(x,'orientation','horizontal');setv(x,'itemgap',12)
                    for b in x.findall('control'):geo(b,width='46%',height=72);setv(b,'scroll','true')
    n.remove(original);n.append(panel);return n

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,default=HERE/'skin-delta');a=p.parse_args()
    expected=json.loads((HERE/'source-inventory.json').read_text())['approved_file_hashes']
    actual={str(x.relative_to(a.baseline)):hashlib.sha256(x.read_bytes()).hexdigest() for x in a.baseline.rglob('*') if x.is_file()}
    if actual!=expected:raise ValueError('Input is not the complete verified .204 baseline')
    if actual['unified/DialogButtonMenu.xml']!=POWER_SHA:raise ValueError('Protected Power source mismatch')
    def write(path,tree):
        out=a.out/path;out.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(tree,str):out.write_text(tree)
        else:E.indent(tree,space='  ');out.write_bytes(E.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n')
    repairs={'DialogAddonInfo.xml':addon_info,'DialogContextMenu.xml':context_menu,'Custom_1188_InfinityHealthCenter.xml':health,'Custom_1198_InfinityNav.xml':nav,'Custom_1191_InfinitySystemHub.xml':system_hub,'DialogAddonSettings.xml':lambda r:settings(r,True),'DialogSettings.xml':settings,'DialogTextViewer.xml':textviewer}
    for path,transform in repairs.items():write('unified/'+path,transform(E.parse(a.baseline/'unified'/path).getroot()))
    legacy_root=E.parse(a.baseline/'unified/Includes_InfinityLegacy.xml').getroot()
    write('unified/DialogKeyboard.xml',keyboard(E.parse(a.baseline/'unified/DialogKeyboard.xml').getroot(),legacy_root))
    text=(a.baseline/'unified/View_50_List.xml').read_text()
    for name in ['InfinityPluginDirectoryCompact','InfinityPluginDirectoryRegular','InfinityCoreDirectory']:text=replace_include(text,name,directory)
    write('unified/View_50_List.xml',text)
    text=(a.baseline/'unified/Includes_CinemaBrowse.xml').read_text();write('unified/Includes_CinemaBrowse.xml',replace_include(text,'InfinityCinemaBrowseList',cinema))
    text=(a.baseline/'unified/Includes_InfinityLegacy.xml').read_text();write('unified/Includes_InfinityLegacy.xml',replace_include(text,'InfinityLegacy_DefaultDialogSelectLayout',select_layout))
    helper=E.Element('includes')
    legacy=E.parse(a.baseline/'unified/Includes_InfinityLegacy.xml').getroot()
    var=copy.deepcopy(legacy.find("variable[@name='InfinityLegacySurface']"));var.set('name','InfinityUIRepairSurface')
    for v in var.findall('value'):v.text='FF'+v.text[2:]
    helper.append(var)
    var=tag(helper,'variable',name='InfinityUIHealthStatus')
    tag(var,'value','$INFO[Window(Home).Property(KHC.Status)]',condition='!String.IsEmpty(Window(Home).Property(KHC.Status))')
    tag(var,'value','Unknown / not verified')
    var=tag(helper,'variable',name='InfinityUIHealthStatusColor')
    tag(var,'value',LEGACY+'Danger]',condition='String.IsEqual(Window(Home).Property(KHC.Status),Needs attention)')
    tag(var,'value',LEGACY+'Secondary]')
    # Prepared visual only. There is no consumer until backend identity is verified.
    inc=tag(helper,'include',name='InfinityUIVerifiedWatchedBadge')
    for name in ['verified','completed']:tag(inc,'param',name=name,default='false')
    definition=tag(inc,'definition');badge=image(definition,'infinity_legacy/check_on.png','FF24A8FF',right=8,top=8,width=24,height=24)
    tag(badge,'visible','$PARAM[verified] + $PARAM[completed]');tag(badge,'aspectratio','keep')
    write('unified/Includes_InfinityUIRepair.xml',helper)
    text=(a.baseline/'unified/Includes.xml').read_text();write('unified/Includes.xml',text.replace('<includes>','<includes>\n  <include file="Includes_InfinityUIRepair.xml"/>',1))
    text=(a.baseline/'addon.xml').read_text().replace('version="1.0.5.204"','version="'+VERSION+'"',1)
    text=re.sub(r'Infinity 1\.0\.5\.204 Closing Status Polish RC1\.[^<]+','Infinity '+VERSION+' UI Stability RC1. Built directly from approved 1.0.5.204 Closing Status Polish RC1; protected locked parent .201. Bounded dialogs, readable Health Center, approved drawer cleanup and responsive presentation repairs. Approved Power XML unchanged. Physical Fold acceptance pending.',text,count=1)
    write('addon.xml',text)
    print(json.dumps({'version':VERSION,'delta_files':len(list(a.out.rglob('*.xml'))),'power_unchanged':True,'backend_edits':False}))

if __name__=='__main__':main()
