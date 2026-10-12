#!/usr/bin/env python3
"""Read-only route/module evidence; absence from this graph is never deletion proof."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
from lxml import etree as ET

TOKENS=re.compile(r'script\.infinity\.live|(?:TV|PVR)(?:Guide|Channels|Recordings|Timers|Search|OSD)|infinity://multiview',re.I)

def scripts(root):
    rows=[]
    for p in sorted(root.rglob('*.py')):
        text=p.read_text();tree=ast.parse(text)
        imports=[];callbacks=[];builtins=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
            if isinstance(n,ast.ImportFrom):imports.append('.'*n.level+(n.module or '')+':'+','.join(x.name for x in n.names))
            if isinstance(n,ast.FunctionDef) and n.name.startswith(('on','run','launch','create_window')):callbacks.append(n.name)
            if isinstance(n,ast.Constant) and isinstance(n.value,str) and TOKENS.search(n.value):builtins.append(n.value)
        rows.append({'file':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                     'imports':imports,'callback_or_entry_names':callbacks,'route_literals':builtins})
    return rows

def scan(skin,live,historical,android,out):
    xml=[];routes=[];definitions={};refs={};dynamic_includes=[]
    for p in sorted(skin.rglob('*.xml')):
        data=p.read_bytes();r=ET.fromstring(data);rel=p.relative_to(skin).as_posix();active=rel.startswith('unified/')
        xml.append({'file':rel,'sha256':hashlib.sha256(data).hexdigest(),'active_resolution':active,
                    'root':r.tag,'window_id':r.get('id'),'controls':len(r.findall('.//control'))})
        for n in r.iter():
            if n.tag=='include':
                if n.get('name'):definitions.setdefault(n.get('name'),[]).append(rel)
                else:
                    v=n.get('content') or (n.text or '').strip()
                    if v:refs.setdefault(v,[]).append(rel)
                    if '$' in v:dynamic_includes.append({'file':rel,'expression':v})
            value=(n.text or '').strip()
            if value and TOKENS.search(value):
                ancestors=[]
                for a in n.iterancestors():
                    if a.tag in ('include','control','item'):ancestors.append({'tag':a.tag,'id':a.get('id'),'name':a.get('name'),'type':a.get('type')})
                routes.append({'file':rel,'line':n.sourceline,'active_resolution':active,'tag':n.tag,
                               'action':value,'condition':n.get('condition'),'owners':ancestors})
    android_hits=[]
    for p in sorted(android.rglob('*.java.in')):
        for i,line in enumerate(p.read_text().splitlines(),1):
            if any(s in line for s in ['script.infinity.live','infinity://multiview','multiview-request','InfinityMultiViewActivity']):
                android_hits.append({'file':p.name,'line':i,'text':line.strip()})
    identity=ET.parse(str(skin/'addon.xml')).getroot()
    result={'skin_identity':dict(identity.attrib),'xml_files':xml,'xml_count':len(xml),
            'active_xml_count':sum(x['active_resolution'] for x in xml),'routes':routes,
            'active_live_actions':[x for x in routes if x['active_resolution'] and 'script.infinity.live' in x['action']],
            'all_named_includes':definitions,'include_references':refs,'dynamic_include_expressions':dynamic_includes,
            'packaged_live_modules':scripts(live),'historical_013_modules':scripts(historical),'android_hits':android_hits,
            'classification':'B — Retain: current conditional routes plus owned data and playback; complete installed identity/retirement closure unresolved',
            'native_pvr_classification':'C — Preserve: shared guide, recordings, timeshift, channel, radio and checkpoint contracts',
            'installed_live_addon_version':'Not captured by the selected diagnostic code export',
            'not_removal_proof':['No direct reference','Legacy name','Different UI owner','Absent from selected diagnostics']}
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'xml':len(xml),'active_xml':result['active_xml_count'],'active_live_actions':len(result['active_live_actions']),
                      'packaged_python':len(result['packaged_live_modules']),'historical_python':len(result['historical_013_modules']),'android_hits':len(android_hits)}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['skin','live','historical','android','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();scan(a.skin,a.live,a.historical,a.android,a.out)
