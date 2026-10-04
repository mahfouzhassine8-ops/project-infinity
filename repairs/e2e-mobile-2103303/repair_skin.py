#!/usr/bin/env python3
"""Guarded edits to the confirmed existing Infinity skin; never rename its ID.

Run against a COPY of the .190 skin directory. Native fixes are separate.
The immutable input archive and skin-baseline-sha256.json are the rollback.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from lxml import etree as E

HERE = Path(__file__).resolve().parent
MARK = 'infinity_polish/infinity_mark.png'
MOTION = '!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)'
WIDE = 'Integer.IsGreater(Window(Home).Property(Infinity.LogicalWidth),1280)'


def put(node, key, value, **attrs):
    children = node.findall(key)
    child = children[0] if children else E.SubElement(node, key)
    for extra in children[1:]:
        node.remove(extra)
    child.text = str(value)
    child.attrib.update(attrs)
    return child


def remove(node, *keys):
    for key in keys:
        for child in node.findall(key):
            node.remove(child)


def control(parent, kind, cid=None, **values):
    c = E.SubElement(parent, 'control', type=kind)
    if cid is not None:
        c.set('id', str(cid))
    for k, v in values.items():
        put(c, k, v)
    return c


def image(parent, texture, **bounds):
    return control(parent, 'image', texture=texture, **bounds)


def glass(parent):
    for asset, color in [('surface.png', '$VAR[InfinityDrawerPanel]'),
                         ('rim.png', '$VAR[InfinityGlassBorderSoft]')]:
        c = image(parent, 'infinity_polish/' + asset, left=0, top=0, width='100%', height='100%')
        c.find('texture').attrib.update({'border':'24', 'colordiffuse':color})


def label(parent, value, cid=None, **bounds):
    return control(parent, 'label', cid, label=value, font='InfinityBody',
                   textcolor='$VAR[InfinityGlassTextPrimary]', aligny='center', **bounds)


def button(parent, cid, value='', **bounds):
    c = control(parent, 'button', cid, label=value, font='InfinitySmall', align='center',
                aligny='center', textcolor='$VAR[InfinityGlassTextPrimary]',
                focusedcolor='$VAR[InfinityGlassTextPrimary]', **bounds)
    put(c, 'texturefocus', 'infinity_polish/field.png', border='20',
        colordiffuse='$VAR[InfinityDrawerFocusWash]')
    put(c, 'texturenofocus', 'infinity_polish/field.png', border='20',
        colordiffuse='$VAR[InfinityDrawerQuietRow]')
    return c


def close(parent, cid, action='Action(Back)', native=False):
    c = button(parent, cid, right=16, top=16, width=88, height=88)
    if native:
        # Native DialogSelect uses id 7 for cancellation and assigns its label.
        # Keep that action contract, render the approved close image instead.
        put(c, 'textcolor', '00000000')
        put(c, 'focusedcolor', '00000000')
    else:
        put(c, 'onclick', action)
    image(parent, 'infinity_polish/close.png', right=44, top=44, width=32, height=32)
    return c


def scrim(parent):
    c = image(parent, 'infinity_ui/contract_white.png', left=0, top=0, width='100%', height='100%')
    c.find('texture').set('colordiffuse', '$VAR[InfinityDrawerScrim]')


def panel(parent, height):
    c = control(parent, 'group', centerleft='50%', centertop='50%', width='86%', height=height)
    c.find('width').set('max','960')
    c.find('height').set('max','1100')
    glass(c)
    return c


def read(root, name):
    return E.parse(str(root / 'unified' / name))


def write(root, name, tree):
    E.indent(tree, space='  ')
    (root / 'unified' / name).write_bytes(E.tostring(tree, encoding='utf-8', xml_declaration=True) + b'\n')


def home(root):
    t = read(root, 'Home.xml'); r = t.getroot(); cs = r.find('controls')
    main = cs.find("control[@id='40001']")
    assert main is not None
    # Only the rail block and its two trailing frame images are removed.
    started = False
    for c in list(cs):
        if c is main:
            started = False
        if c.get('type') == 'image' and c.findtext('width') == '82.0':
            started = True
        if started or (c.tag == 'control' and c.findtext('texture') == 'infinity_ui/frame_soft.png'
                       and c.findtext('height') == '100%'):
            cs.remove(c)
    for c in list(cs):
        if c.findtext('left') == '9.2593%' and c.findtext('height') == '2':
            cs.remove(c)
    put(main, 'left', 18)
    put(r, 'defaultcontrol', '9000', always='false')
    # Existing alternative headers reserve the capsule's area, content keeps its width.
    for g in [main] + main.findall("control[@type='group']"):
        for c in g.findall('control'):
            if c.get('type') not in ('image', 'label') or c.findtext('visible') == 'false':
                continue
            top = c.findtext('top', '')
            if top not in ('0.4167%', '0.5833%', '1.5%', '2.9167%', '5.5%'):
                continue
            if c.findtext('texture') == MARK:
                g.remove(c)
            elif c.get('type') == 'label' and c.findtext('align') != 'right':
                put(c, 'left', 268); remove(c, 'width'); put(c, 'right', 24)
    capsule = control(cs, 'group', '19080', left=18, top=18, width=232, height=104)
    glass(capsule)
    image(capsule, MARK, left=20, top=28, width=96, height=48, aspectratio='keep')
    b = button(capsule, 9090, left=128, top=8, width=96, height=88)
    put(b, 'onclick', 'ActivateWindow(1198)'); put(b, 'ondown', 9000); put(b, 'onright', 9000)
    image(capsule, 'infinity_ui/icons/menu.png', left=158, top=34, width=36, height=36)
    active = image(capsule, 'infinity_polish/focus_rim.png', left=0, top=0, width='100%', height='100%')
    put(active, 'visible', 'String.IsEqual(Window(Home).Property(Infinity.DrawerOpen),true)')
    active.find('texture').attrib.update({'border':'24', 'colordiffuse':'$VAR[InfinityGlassFocus]'})
    # References to the removed shortcuts now return to the single capsule button.
    for el in r.iter():
        if el.tag in ('onleft', 'onright', 'onup', 'ondown') and el.text in map(str, range(9091, 9099)):
            el.text = '9090'
    # Cinema overlay offsets previously compensated for the rail width.
    for g in main.findall('control'):
        if g.get('id') in ('19593', '19594', '19590'):
            put(g, 'left', -18)
    write(root, 'Home.xml', t)


def drawer(root):
    t = read(root, 'Custom_1198_InfinityNav.xml'); r = t.getroot()
    g = r.find("controls/control[@id='1198888']")
    put(g, 'width', '92%', max='680')
    remove(g, 'bottom');put(g, 'height', '88%', max='1040')
    for a in g.findall('animation'):
        g.remove(a)
    for event, start, end, ms in [('WindowOpen', '34.12,10', '100,100', 210),
                                   ('WindowClose', '100,100', '34.12,10', 165)]:
        a = E.SubElement(g, 'animation', effect='zoom', start=start, end=end, center='0,0',
                         time=str(ms), tween='cubic', easing='out' if event == 'WindowOpen' else 'in',
                         condition=MOTION)
        a.text = event
    for cid, action in [(1198102, 'movies'), (1198103, 'tv')]:
        b = g.find(f".//control[@id='{cid}']")
        b.findall('onclick')[1].text = 'ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action=' + action + ',return)'
    # Return focus to real content when closed; keyboard/remote can focus the capsule again.
    u = E.SubElement(r, 'onunload', condition='Window.IsActive(home)'); u.text = 'SetFocus(9000)'
    write(root, 'Custom_1198_InfinityNav.xml', t)


def confirm(root):
    r = E.Element('window'); put(r, 'depth', 'DepthDialog+')
    put(r, 'onload', 'SetFocus(9010)', condition='Window.IsActive(okdialog)')
    cs = E.SubElement(r, 'controls'); scrim(cs); g = panel(cs, 520)
    image(g, MARK, left=28, top=32, width=96, height=48, aspectratio='keep')
    label(g, '', 1, left=144, right=120, top=24, height=72)
    close(g, 9010)
    control(g, 'textbox', 9, left=32, right=32, top=122, bottom=144, font='InfinityBody',
            textcolor='$VAR[InfinityGlassTextPrimary]', label='')
    p = control(g, 'progress', 20, left=32, right=32, bottom=126, height=12, info='System.Progressbar')
    put(p, 'texturebg', 'infinity_legacy/track.png', colordiffuse='$VAR[InfinityLegacyTrack]')
    put(p, 'midtexture', 'infinity_legacy/track.png', colordiffuse='$VAR[InfinityLegacyAccent]')
    a = control(g, 'grouplist', 9000, left=24, right=24, bottom=24, height=88,
                orientation='horizontal', align='center', itemgap=8)
    for cid in (10, 11, 12):
        b = button(a, cid, width='32%', height=88)
        put(b, 'onup', 9010)
        # OK informational/failure messages use their X; confirmation buttons remain native.
        put(b, 'visible', '!Window.IsActive(okdialog)')
    write(root, 'DialogConfirm.xml', r)


def busy(root):
    r = E.Element('window'); cs = E.SubElement(r, 'controls')
    g = control(cs, 'group', centerleft='50%', centertop='50%', width=420, height=164)
    glass(g)
    image(g, MARK, left=28, top=40, width=112, height=56, aspectratio='keep')
    label(g, 'Loading…', left=164, top=38, right=24, height=60)
    p = control(g, 'progress', 10, left=28, right=28, bottom=24, height=10)
    put(p, 'texturebg', 'infinity_legacy/track.png', colordiffuse='$VAR[InfinityLegacyTrack]')
    put(p, 'midtexture', 'infinity_legacy/track.png', colordiffuse='$VAR[InfinityLegacyAccent]')
    write(root, 'DialogBusy.xml', r)


def settings(root):
    t = read(root, 'Settings.xml'); r = t.getroot(); cs = r.find('controls')
    title = cs.find("control[@type='label']")
    put(title, 'label', 'Settings'); put(title, 'left', 156); remove(title, 'width')
    put(title, 'right', 32); put(title, 'height', 72)
    image(cs, MARK, left=32, top=36, width=96, height=48, aspectratio='keep')
    p = cs.find("control[@id='9000']")
    for tag in ('itemlayout', 'focusedlayout'):
        old = p.find(tag); index = p.index(old); p.remove(old)
        for condition, width in [(WIDE, '50%'), ('!' + WIDE, '100%')]:
            layout = E.Element(tag, width=width, height='144', condition=condition)
            tile = control(layout, 'group', left=8, top=8, right=8, bottom=8)
            glass(tile)
            label(tile, '$INFO[ListItem.Label]', left=24, right=24, top=0, height='100%')
            if tag == 'focusedlayout':
                rim = image(tile, 'infinity_polish/focus_rim.png', left=0, top=0, width='100%', height='100%')
                rim.find('texture').attrib.update({'border':'24', 'colordiffuse':'$VAR[InfinityGlassFocus]'})
            p.insert(index, layout); index += 1
    write(root, 'Settings.xml', t)
    # Anchor switches to row ends. Native RadioButton text reservation is a required companion.
    for f in (root / 'unified').glob('*.xml'):
        tree = E.parse(str(f)); changed = False
        for c in tree.findall('.//control[@type="radiobutton"]'):
            if c.find('radioposx') is not None:
                put(c, 'radioposx', 0); changed = True
        if changed:
            write(root, f.name, tree)


def context(root):
    t = read(root, 'DialogContextMenu.xml'); r = t.getroot(); cs = r.find('controls')
    bg = cs.find("control[@id='999']")
    for k, v in dict(left=0, top=0, width=640, height=928).items(): put(bg, k, v)
    gl = cs.find("control[@id='996']")
    for k, v in dict(left=24, top=100, width=592, itemgap=8).items(): put(gl, k, v)
    put(gl, 'height', 'auto', max='804'); put(gl, 'orientation', 'vertical')
    template = cs.find("control[@id='1000']")
    for k, v in dict(left=0, top=0, width=592, height=104).items(): put(template, k, v)
    remove(template, 'animation')
    for c in list(cs):
        if c.get('type') == 'button' and c.get('id') is None: cs.remove(c)
    # Context native positioning clamps this 640-unit surface to current window bounds.
    image(cs, MARK, left=28, top=24, width=96, height=48, aspectratio='keep')
    x = button(cs, 990, left=528, top=8, width=88, height=88)
    put(x, 'onclick', 'Action(Back)'); put(x, 'ondown', 996)
    image(cs, 'infinity_polish/close.png', left=556, top=36, width=32, height=32)
    write(root, 'DialogContextMenu.xml', t)


def select(root):
    t = read(root, 'Includes_InfinityLegacy.xml'); r = t.getroot()
    inc = r.find("include[@name='InfinityLegacy_DefaultDialogSelectLayout']")
    old = copy.deepcopy(inc)
    for c in list(inc): inc.remove(c)
    # Includes are chosen when the dialog loads, before the native title is populated.
    # The caller marks Ambient Home explicitly; do not identify dialogs by translated labels.
    for compact in (False, True):
        name = 'InfinityRepairSelectCompact' if compact else 'InfinityRepairSelectStandard'
        use = E.SubElement(inc, 'include', condition=('' if compact else '!') +
                           'String.IsEqual(Window(Home).Property(Infinity.Select.Compact),true)')
        use.text = name
        new = E.SubElement(r, 'include', name=name)
        g = panel(new, 476 if compact else '76%')
        image(g, MARK, left=28, top=32, width=96, height=48, aspectratio='keep')
        label(g, '', 1, left=144, right=120, top=24, height=72)
        close(g, 7, native=True)
        for cid in (3, 6):
            lst = copy.deepcopy(old.find(f".//control[@id='{cid}']"))
            remove(lst, 'width', 'height')
            for k, v in dict(left=24, right=60, top=124, bottom=32 if compact else 132).items(): put(lst, k, v)
            put(lst, 'onright', 61); put(lst, 'onleft', 7)
            for layout in lst.findall('itemlayout') + lst.findall('focusedlayout'):
                layout.set('height', '104' if cid == 3 else '138')
                layout.set('width', '100%')
                if cid == 3:
                    for lb in layout.findall("control[@type='label']"):
                        put(lb, 'height', 96)
            g.append(lst)
        sb = copy.deepcopy(old.find(".//control[@id='61']")); remove(sb, 'left', 'height')
        for k, v in dict(right=24, top=124, width=24, bottom=32 if compact else 132, onright=7).items(): put(sb, k, v)
        g.append(sb)
        label(g, '', 2, left=32, bottom=28, height=64, right=32, visible='false')
        label(g, '', 4, left=32, top=124, right=60, height=80)
        for cid, side in [(5, 'left'), (8, 'right')]:
            b = button(g, cid, **{side:24}, bottom=24, width='44%', height=88)
            put(b, 'onup', 3)
            if compact: put(b, 'visible', 'false')
    write(root, 'Includes_InfinityLegacy.xml', t)


def branding(root):
    for f in (root / 'unified').glob('*.xml'):
        t = E.parse(str(f)); changed = False
        for c in t.findall('.//control[@type="label"]'):
            text = c.findtext('label', '').strip()
            if text == '∞':
                c.set('type', 'image')
                remove(c, 'label', 'font', 'textcolor', 'align', 'aligny')
                put(c, 'texture', MARK); put(c, 'aspectratio', 'keep'); changed = True
        if changed: write(root, f.name, t)


def player(root):
    t = read(root, 'VideoOSD.xml'); r = t.getroot(); cs = r.find('controls')
    originals = {c.get('id'):copy.deepcopy(c) for c in cs.findall('control') if c.get('id')}
    old_drawer = copy.deepcopy(cs.find("control[@type='group']"))
    for c in list(cs): cs.remove(c)
    volume = 'String.IsEqual(Window(Home).Property(Infinity.PlayerVolumeMode),true)'
    normal = '!' + volume
    for event in ('onload', 'onunload'):
        E.SubElement(r, event).text = 'ClearProperty(Infinity.PlayerVolumeMode,Home)'
    header = control(cs, 'group', left='2.5%', top=18, width='95%', height=152, visible=normal)
    glass(header)
    title = label(header, '$INFO[Player.Title]', left=28, right=224, top=18, height=62)
    put(title, 'font', 'InfinityTitle')
    metadata = label(header, '$INFO[VideoPlayer.Year]  •  $INFO[Player.Duration]  •  $INFO[Player.Chapter,Chapter ]$INFO[Player.ChapterCount, / ]',
                     left=28, right=224, top=84, height=44)
    put(metadata, 'font', 'InfinitySmall')
    label(header, '$INFO[System.Time]', right=28, top=24, width=180, height=92, align='right')
    # Scrubber and timestamps have their own vertical band. A horizontal rail pan
    # cannot start inside the scrubber's hit rectangle.
    seek = control(cs, 'group', left='5%', width='90%', bottom=168, height=122, visible=normal)
    label(seek, '$INFO[Player.Time(hh:mm:ss)]', left=0, top=0, width='45%', height=48)
    label(seek, '$INFO[Player.Duration(hh:mm:ss)]', right=0, top=0, width='45%', height=48, align='right')
    s = originals['87']; remove(s, 'right', 'bottom')
    for k, v in dict(left=0, top=54, width='100%', height=64, onup=202, ondown=202).items(): put(s, k, v)
    seek.append(s)
    # Native adaptive canvas width is published by the existing reflow owner.
    # A compact centred maximum on wide canvases; safe gutters on narrow ones.
    rail = control(cs, 'group', centerleft='50%', width='94%', bottom=24, height=128, visible=normal)
    rail.find('width').set('max','1360')
    glass(rail)
    rows = control(rail, 'grouplist', 290, left=12, right=12, top=12, bottom=12,
                   orientation='horizontal', itemgap=8, scrolltime=140, usecontrolcoords='false')
    order = [257, 264, 201, 200, 202, 205, 204, 253, 250, 255, 265, 262]
    icons = {257:'list.png',264:'volume.png',200:'prev.png',202:'pause.png',205:'next.png',
             253:'stop.png',250:'subtitles.png',255:'display.png'}
    names = {257:'Drawer',264:'Volume',201:'Back 30',200:'Previous',202:'Play/Pause',205:'Next',
             204:'Forward 30',253:'Stop',250:'Subtitles',255:'Display',265:'Repeat',262:'Lock'}
    for index, cid in enumerate(order):
        cell = control(rows, 'group', width=104, height=104)
        if str(cid) in originals:
            b = originals[str(cid)]; cell.append(b)
            remove(b, 'right', 'bottom', 'onup', 'ondown', 'onleft', 'onright')
            for k,v in dict(left=0, top=0, width=104, height=104).items(): put(b,k,v)
        else:
            b = button(cell,cid,left=0,top=0,width=104,height=104)
        put(b,'description',names[cid]); put(b,'onup',87); put(b,'ondown',87)
        put(b,'onleft',order[max(0,index-1)]); put(b,'onright',order[min(len(order)-1,index+1)])
        put(b,'enable','!Skin.HasSetting(Infinity.PlayerDrawerOpen)')
        if cid in (201,204):
            put(b,'onclick','Seek(-30)' if cid==201 else 'Seek(30)')
            put(b,'label','−30' if cid==201 else '+30'); put(b,'font','InfinitySmall')
        elif cid==264:
            put(b,'onclick','SetProperty(Infinity.PlayerVolumeMode,true,Home)')
            E.SubElement(b,'onclick').text='SetFocus(260)'
        elif cid==265:
            put(b,'onclick','PlayerControl(Repeat)'); put(b,'label','Repeat'); put(b,'font','InfinityTiny')
        if cid in icons:
            if cid==202:
                for texture,vis in [('play.png','Player.Paused'),('pause.png','!Player.Paused')]:
                    image(cell,'infinity_reference/'+texture,left=32,top=32,width=40,height=40,visible=vis)
            else:
                image(cell,'infinity_reference/'+icons[cid],left=32,top=32,width=40,height=40)
        if cid==262: image(cell,'infinity_ui/icons/lock.png',left=32,top=32,width=40,height=40)
    capsule=control(cs,'group',right='5%',centertop='50%',width=180,height=620,visible=volume)
    glass(capsule)
    label(capsule,'$INFO[Control.GetLabel(260)]',left=12,right=12,top=16,height=52,align='center')
    plus=button(capsule,266,'+',left=46,top=76,width=88,height=72)
    put(plus,'onclick','Action(VolumeUp)'); put(plus,'ondown',260)
    slider=originals['260']; remove(slider,'right','bottom','onup','ondown','onleft','onright')
    for k,v in dict(left=62,top=172,width=56,height=256,orientation='vertical',onleft=266,onright=267).items(): put(slider,k,v)
    put(slider,'texturesliderbar','infinity_legacy/track.png',border='6',colordiffuse='$VAR[InfinityLegacyTrack]')
    capsule.append(slider)
    minus=button(capsule,267,'−',left=46,top=452,width=88,height=64)
    put(minus,'onclick','Action(VolumeDown)'); put(minus,'onup',260); put(minus,'ondown',261)
    mute=originals['261']; remove(mute,'top','right','onup','ondown','onleft','onright')
    for k,v in dict(left=46,bottom=16,width=88,height=88,onup=267).items(): put(mute,k,v)
    capsule.append(mute)
    for tex,vis in [('volume.png','!Player.Muted'),('mute.png','Player.Muted')]:
        image(capsule,'infinity_reference/'+tex,left=70,bottom=40,width=40,height=40,visible=vis)
    for b in capsule.findall('control'):
        if b.get('type') in ('button','slider'):
            put(b,'onback','ClearProperty(Infinity.PlayerVolumeMode,Home)')
            E.SubElement(b,'onback').text='SetFocus(264)'
            E.SubElement(b,'onback').text='Skin.TimerStart(autoclosevideoosd)'
    # Existing drawer commands stay available in a bounded scroll area.
    overlay=control(cs,'group',visible='Skin.HasSetting(Infinity.PlayerDrawerOpen) + '+normal)
    scrim(overlay); drawer_panel=panel(overlay,'82%')
    image(drawer_panel,MARK,left=28,top=32,width=96,height=48,aspectratio='keep')
    label(drawer_panel,'Playback',left=144,right=120,top=24,height=72)
    x=close(drawer_panel,271,'Skin.Reset(Infinity.PlayerDrawerOpen)')
    E.SubElement(x,'onclick').text='SetFocus(257)';put(x,'ondown',270)
    commands=control(drawer_panel,'grouplist',291,left=24,right=24,top=120,bottom=24,
                     orientation='vertical',itemgap=8,scrolltime=140)
    buttons=[b for b in old_drawer.findall('control') if b.get('type')=='button' and b.get('id')!='271']
    buttons += [originals['252'], originals['263']]
    for b in buttons:
        remove(b,'left','top','bottom','right','onup','ondown','onleft','onright')
        put(b,'width','100%');put(b,'height',96);put(b,'align','left');put(b,'textoffsetx',24)
        put(b,'font','InfinitySmall')
        if b.get('id')=='252':put(b,'label','Audio settings')
        if b.get('id')=='263':
            put(b,'label','Rotation policy')
            for e in b.findall('onclick'):
                if e.get('condition'):e.set('condition',e.get('condition').replace(' + !Skin.HasSetting(Infinity.PlayerDrawerOpen)',''))
        if b.find('enable') is not None:
            put(b,'enable',b.findtext('enable').replace('!Skin.HasSetting(Infinity.PlayerDrawerOpen)','true'))
        put(b,'onback','Skin.Reset(Infinity.PlayerDrawerOpen)');E.SubElement(b,'onback').text='SetFocus(257)'
        commands.append(b)
    write(root,'VideoOSD.xml',t)
    timers=read(root,'Timers.xml'); tr=timers.getroot()
    auto=next(x for x in tr if x.findtext('name')=='autoclosevideoosd')
    guard='!Skin.HasSetting(Infinity.PlayerDrawerOpen) + '+normal
    put(auto,'start','['+auto.findtext('start')+'] + '+guard,reset='true')
    put(auto,'stop','['+auto.findtext('stop')+'] | '+volume+' | Skin.HasSetting(Infinity.PlayerDrawerOpen)')
    for onstop in auto.findall('onstop'):onstop.set('condition','['+onstop.get('condition','true')+'] + '+guard)
    timer=E.SubElement(tr,'timer');put(timer,'name','infinityplayervolume')
    put(timer,'start','Window.IsActive(videoosd) + '+volume)
    put(timer,'reset','!System.IdleTime(1) + '+volume)
    put(timer,'stop','!Window.IsActive(videoosd) | !'+volume+' | Integer.IsGreaterOrEqual(Skin.TimerElapsedSecs(infinityplayervolume),5)')
    E.SubElement(timer,'onstop').text='ClearProperty(Infinity.PlayerVolumeMode,Home)'
    E.SubElement(timer,'onstop',condition='Window.IsActive(videoosd)').text='SetFocus(264)'
    E.SubElement(timer,'onstop',condition='Window.IsActive(videoosd)').text='Skin.TimerStart(autoclosevideoosd)'
    write(root,'Timers.xml',timers)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('skin', type=Path); args = ap.parse_args()
    root = args.skin.resolve(); baseline = json.loads((HERE / 'skin-baseline-sha256.json').read_text())
    for name, expected in baseline['files'].items():
        p = root / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise SystemExit('Baseline mismatch: ' + name)
    for repair in (home, drawer, confirm, busy, settings, context, select, branding, player): repair(root)
    addon = E.parse(str(root / 'addon.xml'))
    assert addon.getroot().get('id') == 'skin.infinity.diggz'
    assert addon.getroot().get('name') == 'Infinity'
    changes = {}
    for name, before in baseline['files'].items():
        after = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if before != after: changes[name] = {'before':before, 'after':after}
    (root.parent / 'skin-repair-receipt.json').write_text(json.dumps({'baseline':baseline['source_archive_sha256'],
        'skin_id':'skin.infinity.diggz', 'status':'source candidate; runtime validation required', 'changes':changes}, indent=2)+'\n')
    print(json.dumps({'changed_files':len(changes), 'skin':str(root)}))


if __name__ == '__main__': main()
