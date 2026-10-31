"""Byte-preserving additions to signed436 skin; never rewrite original actions.

No provider prefetch, XML player edits, timer, original frame/geometry change,
or interception of implicit native directory actions.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from html import escape

HISTORICAL=Path(__file__).resolve().parents[1]/'infinity-seamless-loading-2103433/skin_loading.py'
spec=importlib.util.spec_from_file_location('loading_xml_bytes',HISTORICAL)
import sys
legacy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=legacy;spec.loader.exec_module(legacy)
MARKER='INFINITY_LOADING_V2'
PROTECTED=('DialogBusy','DialogProgress','DialogButtonMenu','Player','Fullscreen','OSD','Subtitle','Audio','Seek','Volume','Visualisation','Shutdown','Power')

def definitions(raw):
    assert raw==legacy.definitions(),'Signed436 loading definition preimage differs'
    current=' | '.join('[Window.IsActive(%s) + String.IsEqual(Window(Home).Property(Infinity.Loading.Window),%s)]'%(wid,wid) for wid in ('10000','10025','11193','10134'))
    owned='[[!$PARAM[inheritwindow] + String.IsEqual(Window(Home).Property(Infinity.Loading.Window),$PARAM[window])] | [$PARAM[inheritwindow] + ['+current+']]]'
    local='String.IsEqual(Window.Property(Infinity.Loading.OwnerToken),Window(Home).Property(Infinity.Loading.Token))'
    text=raw.decode();assert owned in text and '['+current+']' in text
    text=text.replace(owned,local).replace('['+current+']',local)
    # A native-owned projection remains visible even while the observer still
    # owns the selected item beneath the modal. Native lifetime is authoritative.
    old_global='!'+ '[String.IsEqual(Window(Home).Property(Infinity.Loading.Active),true) + '+local+']'
    assert old_global in text
    text=text.replace(old_global,'[$PARAM[nativebusy] | '+old_global+']')
    text=text.replace('<param name="inheritwindow" default="false" />','<param name="inheritwindow" default="false" /><param name="nativebusy" default="false" />')
    # The native modal owns its one visible cue. A selected/background cue must
    # not compete with native busy/progress UI underneath it.
    gate='[$PARAM[nativebusy] | [!Window.IsActive(busydialog) + !Window.IsActive(busydialognocancel) + !Window.IsActive(progressdialog)]] + '
    return text.replace('<visible>','<visible>'+gate,1).encode()

def transform(raw,name):
    leaf=Path(name).name
    if any(part.lower() in leaf.lower() for part in PROTECTED):return raw,dict(actions=0,frames=0,protected=True)
    tree=ET.fromstring(raw);parsed=legacy.nodes(raw);additions={};counts=dict(actions=0,frames=0,protected=False)
    def add(at,value):additions.setdefault(at,[]).append(value.encode() if isinstance(value,str) else value)
    def note(value):return '\n<!-- '+MARKER+' -->\n'+value+'\n'
    for node in parsed:
        if node.tag=='onclick':
            action=legacy.node_text(raw,node).strip()
            if not action.startswith(('ActivateWindow(','RunScript(','RunAddon(','RunPlugin(','PlayMedia(')):continue
            if any(s in action.lower() for s in ('shutdown','checkpoint','power','quit','reboot','restart','close','exit','hibernate','suspend')):continue
            target=hashlib.sha256(action.encode()).hexdigest()
            siblings=node.parent.children; index=siblings.index(node)
            if (index>0 and siblings[index-1].tag=='onclick'
                    and target in legacy.node_text(raw,siblings[index-1])
                    and 'seamless.loading' in legacy.node_text(raw,siblings[index-1])):
                continue  # This exact action already has its signed436 observer.
            cid=legacy.owner_id(node);container='Container('+cid+')' if cid!='0' else 'Container'
            owner=dict(window='$INFO[Window(Home).Property(Infinity.Loading.CurrentWindow)]',control=cid if cid!='0' else '$INFO[System.CurrentControlID]',item='$INFO['+container+'.CurrentItem]',epoch='$INFO[Window(Home).Property(Infinity.Loading.Context)]')
            for key,label in [('section','Property(section)'),('source','Property(hubsource)'),('addon','Property(Addon.ID)'),('dbid','DBID')]:owner[key]='$INFO['+container+'.ListItem.'+label+']'
            owner.update(home_section='$INFO[Container(9000).ListItem.Property(section)]',home_source='$INFO[Container(9000).ListItem.Property(hubsource)]')
            condition=('['+node.attrs['condition']+'] + ' if node.attrs.get('condition') else '')+'System.AddonIsEnabled(script.infinity.commandcenter)'
            for state,at in [('action',node.start),('dispatched',node.end)]:
                payload=json.dumps(dict(state=state,target=target,owner=owner),separators=(',',':')).replace('\\','\\\\').replace('"','\\"')
                command='NotifyAll(script.infinity.commandcenter,seamless.loading,"'+payload+'")'
                add(at,note('<onclick condition="'+escape(condition,quote=True)+'">'+escape(command)+'</onclick>'))
            counts['actions']+=1
        if node.tag=='control' and node.attrs.get('type')=='button' and node.attrs.get('id','').isdigit():
            focus=next((c for c in node.children if c.tag=='texturefocus'),None)
            cid=node.attrs['id']
            siblings=node.parent.children; index=siblings.index(node)
            following=siblings[index+1] if index+1<len(siblings) else None
            decorated=(following is not None and following.tag=='include'
                       and following.attrs.get('content')=='InfinityActionLoadingFrame')
            if not decorated and focus is not None and legacy.node_text(raw,focus).strip() in legacy.FRAMES:
                rect={c.tag:legacy.node_text(raw,c) for c in node.children if c.tag in ('left','top','width','height')}
                if set(rect)=={'left','top','width','height'}:
                    add(node.end,legacy.frame_call(rect,cid,window='0').replace(legacy.MARKER.encode(),MARKER.encode()))
                    counts['frames']+=1
        if node.tag=='focusedlayout':
            # Only an existing, explicit border rectangle is eligible. Filled
            # focus backgrounds and artwork are not substituted with new borders.
            if b'InfinityActionLoadingFrame' in raw[node.start:node.end]:continue
            cid=legacy.owner_id(node)
            if cid=='0':continue
            for frame in parsed:
                if frame.tag!='control' or frame.attrs.get('type')!='image' or node not in list(frame.ancestors()):continue
                texture=next((c for c in frame.children if c.tag=='texture'),None)
                if texture is None or legacy.node_text(raw,texture).strip() not in legacy.FRAMES:continue
                rect={c.tag:legacy.node_text(raw,c) for c in frame.children if c.tag in ('left','top','width','height')}
                fields={c.tag for c in frame.children}
                if not fields&{'left','right','centerleft'}:rect['left']='0'
                if not fields&{'top','bottom','centertop'}:rect['top']='0'
                if set(rect)!={'left','top','width','height'}:continue
                add(frame.parent.close,legacy.frame_call(rect,cid,window='0').replace(legacy.MARKER.encode(),MARKER.encode()));counts['frames']+=1;break
    result=raw
    for offset,values in sorted(additions.items(),reverse=True):result=result[:offset]+b''.join(values)+result[offset:]
    ET.fromstring(result)
    return result,counts

def native_busy_fallback(raw):
    """Native-owned drawer projection; native panel remains for other surfaces.

    Both replacement and fallback are in this same native dialog, so neither
    depends on a Python visibility lease or on an occluded underlying control.
    Native lifetime, Back and the independent progress/error dialogs are intact.
    """
    marker=b'<!-- INFINITY_ACTION_LOADING_V1 -->\n<visible>false</visible>'
    assert raw.count(marker)==1
    home='Window.IsActive(10000) + !Player.IsFullscreen'
    videos='Window.IsActive(10025) + String.IsEmpty(Window(Home).Property(MediaMenu)) + !Player.IsFullscreen'
    result=raw.replace(marker,('<!-- INFINITY_LOADING_V2 native-owned fallback -->\n<visible>![['+home+'] | ['+videos+']]</visible>').encode(),1)
    decorations=[]
    for condition,rect in [(home,dict(left='10',top='6',width='78',height='122')),
                           (videos,dict(left='18',top='160',width='96',height='100'))]:
        frame=legacy.frame_call(rect,'0',global_frame=True,window='0').decode()
        frame=frame.replace('</include>','<param name="nativebusy" value="true" /></include>')
        decorations.append('<control type="group"><description>Infinity native busy drawer projection</description><visible>'+escape(condition)+'</visible>'+frame+'</control>')
    return result.replace(b'</controls>',('\n'+''.join(decorations)+'\n</controls>').encode(),1)
