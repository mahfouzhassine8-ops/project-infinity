"""Approved presentation changes; retain all original media/menu actions."""
from __future__ import annotations
import copy
import xml.etree.ElementTree as ET
from native94 import require


def parse(raw):return ET.fromstring(raw)
def encode(root):return b'<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(root,encoding='utf-8')+b'\n'
def text(node,key,value,**attrs):
    child=node.find(key)
    if child is None:child=ET.SubElement(node,key)
    child.text=str(value);child.attrib.update(attrs);return child
def remove(node,*keys):
    for key in keys:
        for child in node.findall(key):node.remove(child)


def player_drawer(raw):
    root=parse(raw)
    groups=[g for g in root.findall('.//control[@type="group"]')
            if 'Skin.HasSetting(Infinity.PlayerDrawerOpen)' in g.findtext('visible','') and g.find('control[@type="group"]') is not None]
    require(len(groups)==1,'original inline Playback drawer is missing or ambiguous')
    panel=groups[0].find('control[@type="group"]')
    require(panel.find('control[@id="291"]') is not None,'native Playback action group missing')
    remove(panel,'centerleft','centertop')
    text(panel,'left','4%');text(panel,'bottom','14%')
    text(panel,'width','78%',max='560');text(panel,'height','68%',max='700')
    for control in panel.findall('control'):
        if control.get('id')=='271':
            for k,v in {'right':'12','top':'12','width':'56','height':'56'}.items():text(control,k,v)
        elif control.findtext('label')=='Playback':
            for k,v in {'left':'112','right':'80','top':'16','height':'48','font':'InfinitySmall'}.items():text(control,k,v)
        elif control.findtext('texture')=='infinity_polish/infinity_mark.png':
            for k,v in {'left':'20','top':'22','width':'72','height':'36'}.items():text(control,k,v)
        elif control.findtext('texture')=='infinity_polish/close.png':
            for k,v in {'right':'32','top':'32','width':'16','height':'16'}.items():text(control,k,v)
    rows=panel.find('control[@id="291"]');text(rows,'top','88');text(rows,'itemgap','8')
    for row in rows.findall('control'):
        if row.get('type') in ('button','radiobutton'):
            text(row,'height','64');text(row,'font','InfinityTiny')
    return encode(root)


def player_settings(raw,kind):
    root=parse(raw);panel=root.find('.//control[@id="9900"]')
    require(panel is not None and root.find('.//control[@id="5"]') is not None,'native settings controls missing')
    remove(panel,'centerleft','centertop','left','right','top','bottom')
    text(panel,'bottom','14%')
    text(panel,'left' if kind=='playback' else 'right','4%' if kind!='video' else '12%')
    text(panel,'width','78%',max='560');text(panel,'height','68%',max='700')
    for node in panel.findall('control'):
        ident=node.get('id')
        if ident=='2':
            text(node,'top','12');text(node,'height','48');text(node,'font','InfinitySmall')
        elif ident=='9002':
            text(node,'top','12');text(node,'right','12');text(node,'width','48');text(node,'height','48')
        elif ident in ('5','60'):
            text(node,'top','76');text(node,'bottom','82')
            if ident=='5':text(node,'itemgap','8')
        elif ident in ('7','8','9','10'):
            text(node,'height','64');text(node,'font','InfinityTiny')
    return encode(root)


def browser(raw):
    root=parse(raw);changed=0
    for layout in root.findall('.//itemlayout')+root.findall('.//focusedlayout'):
        two_lines=any('Label2' in node.findtext('label','') for node in layout.findall('.//control'))
        for node in layout.findall('.//control'):
            label=node.findtext('label','')
            if node.get('type') not in ('label','textbox') or not any(key in label for key in ('ListItem.Label','ListItem.Property(Addon.Name)')):continue
            changed+=1;node.set('type','label');remove(node,'right','bottom','autoscroll','wrapmultiline')
            secondary='Label2' in label
            for k,v in {'left':'21%','top':'52%' if secondary else '8%','width':'66%',
                        'height':'34%' if secondary else ('40%' if two_lines else '84%'),'font':'InfinityTiny',
                        'aligny':'center','scroll':'false'}.items():text(node,k,v)
        for node in layout.findall('.//control[@type="image"]'):
            texture=node.findtext('texture','')
            if 'chevron' in texture or texture.endswith('/arrow_right.png'):
                remove(node,'right');text(node,'left','91%');text(node,'width','5%')
    require(changed>0,'browser data-row labels missing')
    return encode(root)


def search_routes(raw):
    root=parse(raw);changed=0
    for item in root.findall('.//item'):
        for field in list(item):
            value=field.text or ''
            if field.tag not in ('onclick','property'):continue
            if field.tag=='property' and field.get('name')!='path':continue
            if 'plugin://plugin.video.umbrella/?action=movieSearch&folderName=Search+Movies...' in value:
                field.text='RunScript(script.infinity.commandcenter,universal-search,movie)';changed+=1
            elif 'plugin://plugin.video.umbrella/?action=tvSearch&folderName=Search+Shows...' in value:
                field.text='RunScript(script.infinity.commandcenter,universal-search,tv)';changed+=1
    return encode(root) if changed else raw


def health_dashboard(raw):
    root=parse(raw);target=root.find('.//control[@id="1188151"]')
    require(target is not None and target.findtext('onclick')=='RunScript(script.kodihealthcenter,scan)',
            'duplicate Health scan shortcut missing')
    require(root.find('.//control[@id="1188101"]/onclick').text=='RunScript(script.kodihealthcenter,scan)',
            'original Scan Kodi function must remain reachable')
    text(target,'label','DIAGNOSTIC TREE');text(target,'onclick','RunScript(script.kodihealthcenter,causal-tree)')
    return encode(root)
