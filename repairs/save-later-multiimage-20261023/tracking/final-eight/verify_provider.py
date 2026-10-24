"""One selected POV contract comparison; no live-provider/runtime success claim."""
import ast, hashlib, json, re
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
REPAIR=HERE.parents[1]
ARCHIVE_SHA='126b9fbe690dded613d0c2bab177babd6ce2235bc9d67fb25e1c79aefc9dc0d3'

def run(provider, archive, baseline):
    raw=archive.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==ARCHIVE_SHA
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='fde9f10672ac998157169ad296dc3ab6a1734b57'
    tree=ast.parse((REPAIR/'saved_navigation.py').read_text())
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('fingerprint','_source','capability')]
    env=dict(ast=ast,hashlib=hashlib,Path=Path,ET=ET,MAX_SOURCE=4*1024*1024)
    exec(compile(ast.Module(body=functions,type_ignores=[]),'locked-provider-verifier','exec'),env)
    old=json.loads(baseline.read_bytes());spec=old['contracts'][0]
    assert env['capability']('plugin.video.pov',provider,'tv',old['contracts']) is None
    assert env['capability']('plugin.video.pov',provider,'movie',old['contracts']) is None
    sources={name:env['fingerprint']((provider/name).read_bytes(),'plugin.video.pov') for name in spec['sources']}
    new=dict(spec,sources=sources)
    # Reviewed native API surfaces: dispatcher, exact ID directory routing,
    # media typing and unique IDs remain bound to the same generated rows.
    entry=(provider/'resources/lib/modules/entry.py').read_text()
    for mode,owner in [('build_movie_list','movies'),('build_tvshow_list','tvshows'),
                       ('build_season_list','seasons'),('build_episode_list','seasons')]:
        assert re.search(re.escape(repr(mode))+r":\s*lambda p: _import\('menus\."+owner+r"'",entry)
    shapes={}
    for file in ('movies','tvshows','seasons'):
        tree=ast.parse((provider/('resources/lib/menus/'+file+'.py')).read_text())
        route=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Dict):
                values={k.value:v for k,v in zip(node.keys,node.values) if isinstance(k,ast.Constant)}
                mode=values.get('mode')
                if isinstance(mode,ast.Constant) and mode.value in ('play_media','build_season_list','build_episode_list'):
                    assert 'tmdb_id' in values
                    route.append((mode.value,sorted(values)))
        assert route,file
        assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='setUniqueIDs' for n in ast.walk(tree))
        shapes[file]=route
    updated=dict(old,contracts=old['contracts']+[new],provenance=old['provenance']+[dict(
        addon='plugin.video.pov',version='6.10.22',archive='pov-6.10.22.zip',sha256=ARCHIVE_SHA,
        git_blob='fde9f10672ac998157169ad296dc3ab6a1734b57',
        url='https://raw.githubusercontent.com/kodifitzwell/repo/master/plugin.video.pov/plugin.video.pov-6.10.22.zip')])
    for media in ('movie','tv'):
        actual=env['capability']('plugin.video.pov',provider,media,updated['contracts'])
        assert actual and actual['family']==spec['family'] and len(actual['contract']['pins'])==8
    output=HERE/'overlay/script.infinity.commandcenter/NAVIGATION-CONTRACTS.json'
    output.write_text(json.dumps(updated,indent=2,sort_keys=True)+'\n')
    report=dict(provider='plugin.video.pov',version='6.10.22',reference='6.10.21',archive_sha256=ARCHIVE_SHA,
        old_contract_result='REJECT; six reviewed source fingerprints changed',
        new_additive_contract='PASS host capability for movie and TV; eight actual-file raw pins retained',
        old_contracts_unchanged=updated['contracts'][:3]==old['contracts'],reviewed_routes=shapes,
        provider_modified=False,trackit_implementation_modified=False,android='NOT RUN',physical_fold='NOT RUN')
    (HERE/'POV-COMPATIBILITY.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    import sys
    print(json.dumps(run(*map(Path,sys.argv[1:]))))
