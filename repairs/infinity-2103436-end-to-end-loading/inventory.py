"""Read exact signed436 payload; emit action inventory, never modify baseline."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

EXPECTED='a99e7bb789a0817fdfc9cc10b4e1649d52a2c78f0e3375f0735c55f4a91a0336'
SKIN='payload/assets/addons/skin.infinity.diggz/'
CC='payload/assets/addons/script.infinity.commandcenter/'

def inspect(component,out):
    with component.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==EXPECTED
    out.mkdir(parents=True,exist_ok=True)
    inventory=[];python=[];hashes={};errors=[]
    with ZipFile(component) as archive:
        for name in sorted(archive.namelist()):
            if name.startswith(SKIN+'unified/') and name.endswith('.xml'):
                raw=archive.read(name);hashes[name]=hashlib.sha256(raw).hexdigest()
                try:root=ET.fromstring(raw)
                except ET.ParseError as error:errors.append(dict(member=name,error=str(error)));continue
                parents={child:parent for parent in root.iter() for child in parent}
                records=[];frames=[]
                for node in root.iter():
                    if node.tag=='include' and node.get('content')=='InfinityActionLoadingFrame':
                        frames.append({p.get('name'):p.get('value') for p in node.findall('param')})
                    if node.tag not in ('onclick','onload','onunload','onback','content'):continue
                    action=''.join(node.itertext()).strip()
                    if not action or 'seamless.loading' in action:continue
                    owner=node;chain=[]
                    while owner in parents:
                        owner=parents[owner]
                        if owner.tag in ('control','include'):chain.append(dict(tag=owner.tag,**owner.attrib))
                    records.append(dict(event=node.tag,action=action,condition=node.get('condition',''),owners=chain,
                        dynamic=('$INFO[' in action or '$VAR[' in action or '$PARAM[' in action),
                        runtime='NOT_TESTED',readiness='UNCLASSIFIED; activation/content declaration is not completion'))
                inventory.append(dict(member=name,root=root.tag,window_attributes=root.attrib,actions=records,loading_frames=frames,
                    frame_registration=[n.text for n in root.findall('onload') if 'Infinity.Loading.FrameControls' in (n.text or '')]))
            if name.startswith(CC) and name.endswith('.py'):
                raw=archive.read(name);hashes[name]=hashlib.sha256(raw).hexdigest()
                try:tree=ast.parse(raw)
                except (SyntaxError,UnicodeError) as error:errors.append(dict(member=name,error=str(error)));continue
                calls=[]
                for node in ast.walk(tree):
                    if not isinstance(node,ast.Call):continue
                    label=ast.unparse(node.func)
                    if label.split('.')[-1] not in ('preparation','executebuiltin','executeJSONRPC','endOfDirectory','setResolvedUrl','activate','doModal'):continue
                    calls.append(dict(line=node.lineno,call=label,arguments=ast.unparse(node),runtime='NOT_TESTED'))
                if calls:python.append(dict(member=name,calls=calls))
    report=dict(baseline_component_sha256=EXPECTED,signed_source='7bbe08363b493146ca7ed67cb872e9a98b1d888b',
                scope='All201 active unified XML files and Command Center Python declarations; runtime routes and dynamic destinations still require classification',
                xml=inventory,python=python,member_sha256=hashes,parse_errors=errors,
                media='20741 original bytes not exposed; NOT REVIEWED',runtime='NOT_RUN',coverage_complete=False)
    (out/'SIGNED436-ACTION-INVENTORY.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(xml_files=len(inventory),actions=sum(len(v['actions']) for v in inventory),frames=sum(len(v['loading_frames']) for v in inventory),python_members=len(python),parse_errors=len(errors))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--component',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    inspect(**vars(parser.parse_args()))
