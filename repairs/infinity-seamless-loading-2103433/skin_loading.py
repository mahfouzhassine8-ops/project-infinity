"""Add-only loading decorations on the actual installed Infinity XML.

Original routing, implicit Kodi container actions, frame rectangles and all
other controls remain intact. No provider XML, player or shutdown skin touched.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from html import escape
from io import BytesIO
import json
from pathlib import Path
from xml.parsers import expat
import xml.etree.ElementTree as ET

MARKER = 'INFINITY_ACTION_LOADING_V1'
TEMPLATES = ('InfinityHomeAddonCardFocused', 'InfinityCompactContinueCardFocused')
FRAMES = ('infinity_ui/frame.png', 'infinity_ui/osd_focus.png', 'infinity_polish/focus_rim.png',
          'infinity_glass/focus.png', 'infinity_glass/rim.png')
SELECTED = frozenset(('Home.xml', 'Includes_InfinityHomeUnified.xml', 'Includes_InfinityRails.xml',
                     'Custom_1193_InfinityBrowse.xml', 'MyVideoNav.xml', 'DialogFavourites.xml',
                     'Includes_InfinityBrowser223.xml', 'Includes_Views.xml', 'Includes.xml', 'DialogBusy.xml'))


@dataclass
class Node:
    tag: str
    attrs: dict
    start: int
    open_end: int
    parent: Node | None
    children: list = field(default_factory=list)
    close: int = 0
    end: int = 0

    def ancestors(self):
        node = self.parent
        while node:
            yield node
            node = node.parent


def nodes(raw):
    parser = expat.ParserCreate()
    stack, result = [], []

    def start(tag, attrs):
        offset = parser.CurrentByteIndex
        node = Node(tag, attrs, offset, raw.index(b'>', offset) + 1, stack[-1] if stack else None)
        if stack:
            stack[-1].children.append(node)
        stack.append(node)
        result.append(node)

    def end(tag):
        node = stack.pop()
        if raw[node.open_end - 2:node.open_end] == b'/>':
            node.close = node.open_end
            node.end = node.open_end
        else:
            node.close = parser.CurrentByteIndex
            node.end = raw.index(b'>', node.close) + 1

    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.Parse(raw, True)
    return result


def node_text(raw, node):
    return ET.fromstring(raw[node.start:node.end]).text or ''


def owner_id(node):
    return next((a.attrs['id'] for a in node.ancestors()
                 if a.tag == 'control' and a.attrs.get('id', '').isdigit()), '0')


def frame_call(rect, control, *, global_frame=False, window="10000"):
    params = dict(rect)
    params.update(control=control, window=window, globalframe='true' if global_frame else 'false')
    return ('\n<!-- ' + MARKER + ' -->\n<include content="InfinityActionLoadingFrame">' +
            ''.join('<param name="%s" value="%s" />' % (k, escape(v, quote=True)) for k, v in params.items()) +
            '</include>\n').encode()


def transform(raw, name):
    if Path(name).name == 'DialogBusy.xml':
        parsed = nodes(raw)
        group = next(n for n in parsed if n.tag == 'control' and n.attrs.get('type') == 'group')
        assert not any(c.tag == 'visible' for c in group.children)
        note = ('<!-- '+MARKER+' -->\n<visible>!String.IsEqual(Window(Home).Property(Infinity.Loading.DrawerReady),true)</visible>').encode()
        return raw[:group.open_end]+note+raw[group.open_end:], dict(actions=0, frames=0, imports=0)
    if Path(name).name not in SELECTED:
        return raw, dict(actions=0, frames=0, imports=0)
    if MARKER.encode() in raw:
        raise ValueError('Only exact unmodified signed433 XML may be transformed')
    parsed = nodes(raw)
    window = {'MyVideoNav.xml':'10025','Custom_1193_InfinityBrowse.xml':'11193',
              'Includes_InfinityBrowser223.xml':'11193','DialogFavourites.xml':'10134'}.get(Path(name).name,'10000')
    additions = {}
    counts = dict(actions=0, frames=0, imports=0)
    frame_controls = set()

    def add(offset, text):
        additions.setdefault(offset, []).append(text)

    if Path(name).name == 'Includes.xml':
        add(parsed[0].open_end, ('\n<!-- ' + MARKER + ' -->\n<include file="Includes_InfinityActionLoading.xml" />\n').encode())
        counts['imports'] += 1
    if Path(name).name == 'Home.xml':
        add(parsed[0].open_end, ('\n<!-- '+MARKER+' --><onload>SetProperty(Infinity.Loading.DrawerReady,true,Home)</onload><onunload>ClearProperty(Infinity.Loading.DrawerReady,Home)</onunload>\n').encode())
    for node in parsed:
        if node.tag == 'onclick':
            action = node_text(raw, node).strip()
            if not action.startswith(('ActivateWindow(', 'RunScript(', 'RunAddon(', 'RunPlugin(', 'PlayMedia(')):
                continue
            if any(part in action.lower() for part in ('shutdown', 'checkpoint', 'powerdown', 'quit', 'reboot', 'restartapp')):
                continue
            # An existing explicit action is preserved exactly and still invoked
            # exactly once. Never add an onclick to an implicitly routed list.
            payload = dict(state='action', target=sha256(action.encode()).hexdigest(), owner=dict(
                window='$INFO[Window(Home).Property(Infinity.Loading.CurrentWindow)]',
                control=owner_id(node) if owner_id(node) != '0' else '$INFO[System.CurrentControlID]',
                item='$INFO[Container(%s).CurrentItem]' % owner_id(node) if owner_id(node) != '0' else '$INFO[Container.CurrentItem]',
                epoch='$INFO[Window(Home).Property(Infinity.Loading.Context)]'))
            container = 'Container(%s)' % owner_id(node) if owner_id(node) != '0' else 'Container'
            for key, label in (('section','Property(section)'), ('source','Property(hubsource)'),
                               ('addon','Property(Addon.ID)'), ('dbid','DBID')):
                payload['owner'][key] = '$INFO[%s.ListItem.%s]' % (container, label)
            payload['owner']['home_section'] = '$INFO[Container(9000).ListItem.Property(section)]'
            payload['owner']['home_source'] = '$INFO[Container(9000).ListItem.Property(hubsource)]'
            data = json.dumps(payload, separators=(',', ':')).replace('\\', '\\\\').replace('"', '\\"')
            command = 'NotifyAll(script.infinity.commandcenter,seamless.loading,"' + data + '")'
            condition = node.attrs.get('condition')
            condition = '[' + condition + '] + ' if condition else ''
            condition += 'System.AddonIsEnabled(script.infinity.commandcenter)'
            add(node.start, ('<!-- ' + MARKER + ' -->\n<onclick condition="' + escape(condition, quote=True) + '">' + escape(command) + '</onclick>\n').encode())
            # Kodi has started this original action, not necessarily prepared a
            # third-party destination. End only this unobservable launch cue;
            # genuine first-party preparation has its own independent token.
            dispatched = dict(payload, state='dispatched')
            data = json.dumps(dispatched, separators=(',', ':')).replace('\\', '\\\\').replace('"', '\\"')
            command = 'NotifyAll(script.infinity.commandcenter,seamless.loading,"' + data + '")'
            add(node.end, ('\n<!-- ' + MARKER + ' -->\n<onclick condition="' + escape(condition, quote=True) + '">' + escape(command) + '</onclick>\n').encode())
            counts['actions'] += 1
        if node.tag == 'include' and node.attrs.get('content') in TEMPLATES:
            cid = owner_id(node)
            if cid != '0':
                frame_controls.add(cid)
                add(node.close, ('<!-- ' + MARKER + ' --><param name="loadingcontrol" value="' + cid + '" />').encode())
        if node.tag == 'include' and node.attrs.get('name') in TEMPLATES:
            add(node.open_end, ('<!-- ' + MARKER + ' --><param name="loadingcontrol" default="0" />').encode())
            definition = next(child for child in node.children if child.tag == 'definition')
            add(definition.close, frame_call(dict(left='$PARAM[frameleft]', top='$PARAM[frametop]',
                width='$PARAM[framewidth]', height='$PARAM[frameheight]'), '$PARAM[loadingcontrol]'))
            counts['frames'] += 1
        if node.tag == 'focusedlayout':
            frame = None
            for child in parsed:
                if child.tag != 'control' or child.attrs.get('type') != 'image' or node not in list(child.ancestors()):
                    continue
                texture = next((c for c in child.children if c.tag == 'texture'), None)
                if texture and node_text(raw, texture).strip() in FRAMES:
                    frame = child
                    break
            cid = owner_id(node)
            if frame and cid != '0':
                rect = {c.tag: node_text(raw, c) for c in frame.children if c.tag in ('left', 'top', 'width', 'height')}
                if set(rect) == {'left', 'top', 'width', 'height'}:
                    # A frame's local coordinate plane must be the layout itself.
                    # Nested translated groups need their own explicit mapping.
                    if frame.parent is node:
                        frame_controls.add(cid)
                        add(node.close, frame_call(rect, cid, window=window))
                        counts['frames'] += 1
        if node.tag == 'control' and node.attrs.get('type') == 'button' and node.attrs.get('id','').isdigit():
            focus = next((c for c in node.children if c.tag == 'texturefocus'), None)
            if focus and node_text(raw, focus).strip() in FRAMES:
                rect = {c.tag: node_text(raw, c) for c in node.children if c.tag in ('left','top','width','height')}
                if set(rect) == {'left','top','width','height'}:
                    cid=node.attrs['id'];frame_controls.add(cid)
                    add(node.end,frame_call(rect,cid,window=window));counts['frames']+=1
        if Path(name).name == 'Home.xml' and node.tag == 'control' and node.attrs.get('id') == '19080':
            add(node.close, frame_call(dict(left='0', top='0', width='100%', height='100%'), '9090', global_frame=True))
            counts['frames'] += 1
    if parsed[0].tag == 'window' and frame_controls:
        owner_map = '|' + '|'.join(sorted(frame_controls,key=int)) + '|'
        add(parsed[0].open_end, ('\n<!-- '+MARKER+' -->\n<onload>SetProperty(Infinity.Loading.FrameControls.'+window+','+owner_map+',Home)</onload>\n').encode())
    revised = raw
    for offset, fragments in sorted(additions.items(), reverse=True):
        revised = revised[:offset] + b''.join(fragments) + revised[offset:]
    ET.fromstring(revised)
    return revised, counts


def definitions():
    """One shared animated texture, not Python-driven per-frame UI writes."""
    return b'''<?xml version="1.0" encoding="utf-8"?>
<includes>
  <!-- INFINITY_ACTION_LOADING_V1: original frame rectangles, additive glint only -->
  <include name="InfinityActionLoadingFrame">
    <param name="left" /><param name="top" /><param name="width" /><param name="height" />
    <param name="control" default="0" /><param name="window" default="10000" /><param name="globalframe" default="false" />
    <definition>
      <control type="group">
        <description>Infinity current action loading</description>
        <left>$PARAM[left]</left><top>$PARAM[top]</top><width>$PARAM[width]</width><height>$PARAM[height]</height>
        <visible>Window.IsActive($PARAM[window]) + [[!$PARAM[globalframe] + String.IsEqual(Window(Home).Property(Infinity.Loading.Active),true) + String.IsEqual(Window(Home).Property(Infinity.Loading.Control),$PARAM[control]) + Control.IsVisible($PARAM[control]) + Control.HasFocus($PARAM[control]) + String.IsEqual(Container($PARAM[control]).CurrentItem,Window(Home).Property(Infinity.Loading.Item)) + String.IsEqual(Container($PARAM[control]).ListItem.Property(section),Window(Home).Property(Infinity.Loading.Section)) + String.IsEqual(Container($PARAM[control]).ListItem.Property(hubsource),Window(Home).Property(Infinity.Loading.Source)) + String.IsEqual(Container($PARAM[control]).ListItem.Property(Addon.ID),Window(Home).Property(Infinity.Loading.Addon)) + String.IsEqual(Container($PARAM[control]).ListItem.DBID,Window(Home).Property(Infinity.Loading.Dbid)) + String.IsEqual(Container(9000).ListItem.Property(section),Window(Home).Property(Infinity.Loading.HomeSection)) + String.IsEqual(Container(9000).ListItem.Property(hubsource),Window(Home).Property(Infinity.Loading.HomeSource))] | [$PARAM[globalframe] + !String.IsEqual(Window(Home).Property(Infinity.Loading.Active),true) + [String.IsEqual(Window(Home).Property(Infinity.Loading.Global),true) | Window.IsActive(busydialog) | Window.IsActive(busydialognocancel)]]] + !Player.IsFullscreen</visible>
        <control type="image">
          <left>0</left><top>0</top><width>100%</width><height>100%</height>
          <texture border="18" background="true" colordiffuse="$VAR[InfinityCollectiveFrameColor]">infinity_ui/action_loading.gif</texture>
          <visible>!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false) + !String.IsEqual(Window(Home).Property(Infinity.RefreshBatterySaver),true)</visible>
        </control>
        <control type="image">
          <left>0</left><top>0</top><width>100%</width><height>100%</height>
          <texture border="18" background="true" colordiffuse="$VAR[InfinityCollectiveFrameColor]">infinity_ui/action_loading_still.png</texture>
          <visible>String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false) | String.IsEqual(Window(Home).Property(Infinity.RefreshBatterySaver),true)</visible>
        </control>
      </control>
    </definition>
  </include>
</includes>
'''


def glint_textures():
    """Procedural cyan-only UI resource; no user screenshot or logo modified.

    20 shared 128px frames, one restrained perimeter segment. Animated image
    decoding belongs to Kodi's existing texture renderer; no added Python loop.
    """
    from PIL import Image, ImageDraw
    import math
    size = 128
    points = []
    r = 17
    for cx, cy, angle in ((size-r-2, r+1, -90), (size-r-2, size-r-2, 0),
                          (r+1, size-r-2, 90), (r+1, r+1, 180)):
        for deg in range(angle, angle+91, 3):
            points.append((cx + r*math.cos(math.radians(deg)), cy + r*math.sin(math.radians(deg))))
    # Interpolate every straight and corner segment into equal arc steps.
    perimeter = []
    for left, right in zip(points, points[1:]+points[:1]):
        length = max(1, round(math.dist(left, right)))
        perimeter.extend((left[0]+(right[0]-left[0])*i/length, left[1]+(right[1]-left[1])*i/length) for i in range(length))
    frames = []
    for phase in range(20):
        image = Image.new('P', (size, size), 0)
        palette = [0,0,0] + [255,255,255]*255
        image.putpalette(palette)
        draw = ImageDraw.Draw(image)
        start = phase*len(perimeter)//20
        for step in range(max(5, len(perimeter)//12)):
            x,y = perimeter[(start+step)%len(perimeter)]
            draw.ellipse((round(x)-1,round(y)-1,round(x)+1,round(y)+1),fill=1)
        image.info['transparency'] = 0
        frames.append(image)
    output = BytesIO()
    frames[0].save(output, format='GIF', save_all=True, append_images=frames[1:], duration=80,
                   loop=0, transparency=0, disposal=2, optimize=False)
    still = BytesIO()
    frames[0].convert('RGBA').save(still, format='PNG')
    return {'infinity_ui/action_loading.gif': output.getvalue(),
            'infinity_ui/action_loading_still.png': still.getvalue()}
