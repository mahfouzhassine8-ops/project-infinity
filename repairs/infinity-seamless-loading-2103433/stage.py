"""Stage selected Infinity members from exact original-key signed433 component.

No APK, owner approval, module signature, private data or native change here.
The original-key release must authenticate the revised source generation.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'repairs/infinity-final-closure-2103407'))
import module_bundle
from skin_loading import transform,definitions,glint_textures,SELECTED

CC='script.infinity.commandcenter'
SKIN='skin.infinity.diggz'
PREFIX='assets/addons/'
BASE_ZIP='16eeb91a24bf0cf99d558d9e3dd17aedfd127e9a1936dcce413341c48683cd6c'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def preserved(before,after,selected):
    old=ast.parse(before);new=ast.parse(after)
    def definitions(tree,raw):return {n.name:ast.get_source_segment(raw.decode(),n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    a,b=definitions(old,before),definitions(new,after)
    assert set(a)==set(b),'No existing source function removed/added'
    for name in a:
        if name not in selected:assert a[name]==b[name],name
    compile(after,'<staged-selected-Infinity-source>','exec',dont_inherit=True)
    return {'byte_identical_existing_definitions':len(set(a)-set(selected)),'selected':sorted(selected)}

def generate(baseline,out):
    with baseline.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE_ZIP,'Exact signed433 Infinity component required'
    assert not out.exists();out.mkdir(parents=True)
    candidate=out/'candidate-addons';candidate.mkdir()
    changes={};before={};sources={};xml_counts={}
    with ZipFile(baseline) as z:
        for name in z.namelist():
            if name.startswith('payload/'+PREFIX) and name[len('payload/'+PREFIX):].split('/')[0] in module_bundle.IDS:
                rel=name[len('payload/'+PREFIX):];p=candidate/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
        manifest,original=module_bundle.build(candidate)
        assert manifest==(candidate/CC/module_bundle.MANIFEST).read_bytes()
        verified=subprocess.run(['openssl','dgst','-sha256','-verify',str(REPO/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
            '-signature',str(candidate/CC/(module_bundle.MANIFEST+'.sig')),str(candidate/CC/module_bundle.MANIFEST)],check=True,capture_output=True,text=True)
        assert verified.stdout.strip()=='Verified OK'
        shutil.copytree(candidate,out/'input-addons')
        for p in sorted((HERE/'overlay'/CC).iterdir()):
            assert p.is_file() and p.name in {'action_loading.py','service.py','plugin.py','infinity_search.py','addon.xml'}
            key=CC+'/'+p.name;raw=p.read_bytes()
            if key in original:
                old=original[key];assert raw!=old
                if p.suffix=='.py':sources[p.name]=preserved(old,raw,{'main'} if p.name in ('service.py','plugin.py') else {'_open_search'})
                else:assert old.replace(b'version="0.3.5.51"',b'version="0.3.5.52"',1)==raw
            else:assert p.name=='action_loading.py';compile(raw,str(p),'exec',dont_inherit=True)
            (candidate/key).write_bytes(raw);changes[PREFIX+key]=raw;before[PREFIX+key]=sha(original[key]) if key in original else None
        # Exact reversible UI insertions, no protected service/checkpoint changes.
        service_original=original[CC+'/service.py'];service=(candidate/CC/'service.py').read_bytes()
        for old,new in [
          (b'    normal_return = NormalReturnController()',b'    from action_loading import make_monitor\n    loading = make_monitor(xbmc, xbmcgui)\n    normal_return = NormalReturnController()'),
          (b'        if not foreground_gate.visible():\n',b'        if not foreground_gate.visible():\n            loading.tick(foreground=False)\n'),
          (b'        _consume_home_observer_epoch()',b'        loading.tick()\n        _consume_home_observer_epoch()')]:
            assert service.count(new)==1;service=service.replace(new,old,1)
        assert service==service_original,'Every preexisting service byte must survive after three exact UI insertions are removed'
        assert (candidate/CC/'service.py').read_bytes().split(b'    if checkpoint.session is None:',1)[1]==service_original.split(b'    if checkpoint.session is None:',1)[1]
        for leaf in (module_bundle.MANIFEST,module_bundle.MANIFEST+'.sig'):(candidate/CC/leaf).unlink()
        module=module_bundle.prepare(candidate)
        changes[PREFIX+CC+'/'+module_bundle.MANIFEST]=(candidate/CC/module_bundle.MANIFEST).read_bytes()
        before[PREFIX+CC+'/'+module_bundle.MANIFEST]=sha(manifest)
        imported=[]
        skin_prefix='payload/'+PREFIX+SKIN+'/'
        for name in z.namelist():
            if not name.startswith(skin_prefix):continue
            rel=name[len(skin_prefix):]
            if Path(rel).name not in SELECTED:continue
            old=z.read(name);raw,count=transform(old,rel)
            original_skin=out/'input-skin'/SKIN/rel
            original_skin.parent.mkdir(parents=True,exist_ok=True);original_skin.write_bytes(old)
            if raw!=old:
                key=PREFIX+SKIN+'/'+rel;changes[key]=raw;before[key]=sha(old);xml_counts[rel]=count
            if Path(rel).name=='Includes.xml':imported.append(str(Path(rel).parent))
        assert 'unified' in imported
        for folder in imported:
            key=PREFIX+SKIN+'/'+folder+'/Includes_InfinityActionLoading.xml';changes[key]=definitions();before[key]=None
        for leaf,raw in glint_textures().items():
            key=PREFIX+SKIN+'/media/'+leaf;changes[key]=raw;before[key]=None
        key=PREFIX+SKIN+'/addon.xml';old=z.read('payload/'+key);raw=old.replace(b'version="1.0.5.248"',b'version="1.0.5.249"',1).replace(b'import addon="script.infinity.commandcenter" version="0.3.5.49"',b'import addon="script.infinity.commandcenter" version="0.3.5.52"',1)
        assert raw!=old;changes[key]=raw;before[key]=sha(old)
        for name in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
            key=PREFIX+SKIN+'/'+name;old=z.read('payload/'+key);meta=json.loads(old)
            for label in ('candidate',):meta[label]=249
            for label in ('version','candidate_version','skin_version'):
                if label in meta:meta[label]='1.0.5.249'
            if 'protected_files' in meta:
                for rel in meta['protected_files']:
                    member=PREFIX+SKIN+'/'+rel
                    if member in changes:meta['protected_files'][rel]=sha(changes[member])
            changes[key]=(json.dumps(meta,indent=2,sort_keys=True)+'\n').encode();before[key]=sha(old)
    for key,raw in changes.items():
        path=out/'members'/key;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    plan={key:dict(before=before[key],after=sha(raw)) for key,raw in sorted(changes.items())}
    save(out/'SOURCE-PLAN.json',plan)
    save(out/'STAGE.json',dict(status='STAGED_UNSIGNED_INFINITY_UI_ONLY',baseline_component_sha256=BASE_ZIP,
        original_module_signature=verified.stdout.strip(),module=module,changed_members=len(changes),
        source_definition_preservation=sources,protected_service='ALL_EXISTING_BYTES_EXACT_OUTSIDE3_UI_INSERTIONS',
        protected_shutdown='BYTE_IDENTICAL_NOT_RUN',xml=xml_counts,APK='NOT_BUILT',Cobra='UNCHANGED_OWNER',
        native='UNCHANGED',chooser='UNCHANGED',user_data='NO_ACCESS',module_signature='REQUIRES_ORIGINAL_KEY'))
    print(json.dumps({'staged':str(out),'changed_members':len(changes),'authenticated_source_files':module['file_count'],'APK':'NOT_BUILT'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    generate(**vars(p.parse_args()))
