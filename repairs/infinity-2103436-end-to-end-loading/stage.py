"""Stage Infinity-only bytes from exact signed436; no APK or signing action."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from baseline_contract import EXPECTED,SKIN,CC
import skin_coverage

def digest(raw):return hashlib.sha256(raw).hexdigest()

def stage(component,out):
    with component.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==EXPECTED
    assert not out.exists();out.mkdir(parents=True)
    roots={};originals={};changed={};counts={}
    with ZipFile(component) as archive:
        # Native projections must match exact signed drawer geometry, including
        # the Videos parent offset. Never infer coordinates from screen size.
        home=ET.fromstring(archive.read(SKIN+'unified/Home.xml'))
        drawer=home.find('./controls/control[@id="19080"]')
        assert drawer is not None
        assert {k:drawer.findtext(k) for k in ('left','top','width','height')}==dict(left='10',top='6',width='78',height='122')
        assert drawer.find('animation') is None and drawer.find('visible') is None
        includes=ET.fromstring(archive.read(SKIN+'unified/Includes.xml'))
        button=includes.find('./include[@name="SideBladeLeft"]/definition/control[@id="9001"]')
        assert {k:button.findtext(k) for k in ('left','top','width','height')}==dict(left='0',top='142',width='96',height='100')
        assert button.findtext('visible')=='String.IsEmpty(Window(Home).Property(MediaMenu))'
        video=ET.fromstring(archive.read(SKIN+'unified/MyVideoNav.xml'));parents={c:p for p in video.iter() for c in p}
        calls=[n for n in video.iter('include') if (n.text or '').strip()=='SideBladeLeft'];assert len(calls)==1
        parent=parents[calls[0]];assert parent.findtext('left')=='18' and parent.findtext('top')=='18'
        assert parent.find('animation') is None and parent.find('visible') is None
        outer=parents[parent];assert outer.findtext('visible')=='true'
        assert not any(outer.find(k) is not None for k in ('left','top','animation'))
        assert parents[outer].tag=='controls'
        for name in archive.namelist():
            if name.startswith(SKIN+'unified/') and name.endswith('.xml'):
                raw=archive.read(name);originals[name]=raw
                if name.endswith('/Includes_InfinityActionLoading.xml'):revised=skin_coverage.definitions(raw)
                elif name.endswith('/DialogBusy.xml'):revised=skin_coverage.native_busy_fallback(raw)
                else:revised,counts[name]=skin_coverage.transform(raw,name)
                roots[name]=ET.fromstring(revised)
                if revised!=raw:changed[name]=revised
        definitions={}
        for root in roots.values():
            for inc in root.findall('include'):
                if inc.get('name'):definitions[inc.get('name')]=inc
        def frames(node,env=None,stack=()):
            env=env or {};result=set()
            def value(v):
                for k,t in env.items():v=v.replace('$PARAM['+k+']',t)
                return v
            if node.tag=='include':
                name=node.get('content') or (node.text or '').strip()
                params={p.get('name'):value(p.get('value','')) for p in node.findall('param')}
                if name=='InfinityActionLoadingFrame':
                    cid=params.get('control','');global_frame=params.get('globalframe','false')
                    if cid.isdigit() and int(cid)>0 and global_frame!='true':result.add(cid)
                    return result
                if name in definitions and name not in stack:
                    definition=definitions[name];defaults={p.get('name'):p.get('default','') for p in definition.findall('param')};defaults.update(params)
                    return frames(definition,defaults,stack+(name,))
            for child in node:result.update(frames(child,env,stack))
            return result
        registration={}
        for name,root in roots.items():
            if root.tag!='window' or any(p.lower() in Path(name).name.lower() for p in skin_coverage.PROTECTED):continue
            ids=frames(root)
            if not ids:continue
            raw=changed.get(name,originals[name]);parsed=skin_coverage.legacy.nodes(raw)
            addition=('\n<!-- INFINITY_LOADING_V2 -->\n<onload>SetProperty(Infinity.Loading.FrameControls,|'+ '|'.join(sorted(ids,key=int))+'|)</onload>\n').encode()
            at=parsed[0].open_end;changed[name]=raw[:at]+addition+raw[at:];registration[name]=sorted(ids,key=int)
        python=Path(__file__).parent/'overlay/script.infinity.commandcenter/action_loading.py'
        key=CC+'action_loading.py';originals[key]=archive.read(key);changed[key]=python.read_bytes();compile(changed[key],key,'exec')
        plan={}
        for name,raw in changed.items():
            assert name.startswith((SKIN+'unified/',CC+'action_loading.py'))
            rel=name.removeprefix('payload/');dest=out/'members'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
            plan[rel]=dict(before=digest(originals[name]),after=digest(raw),owner='INFINITY')
    report=dict(status='UNAUTHENTICATED_STAGING_ONLY_NOT_INSTALLABLE',baseline_component=EXPECTED,changes=plan,counts=counts,registered_windows=registration,
        unchanged='All other original component members; signed modules and skin metadata NOT regenerated yet',Cobra='NOT_OPENED_OR_CHANGED',shutdown='NOT_CHANGED_NOT_TESTED')
    (out/'PLAN.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(changed=len(plan),windows_registered=len(registration),new_action_wrappers=sum(c.get('actions',0) for c in counts.values()),new_frames=sum(c.get('frames',0) for c in counts.values()))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--component',type=Path,required=True);p.add_argument('--out',type=Path,required=True);stage(**vars(p.parse_args()))
