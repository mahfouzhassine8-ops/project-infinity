"""Exercise the original Resume Hub's persistence across all five tracking operations.

Only the Kodi I/O boundary is mocked; resume_hub.py and plugin.py are the
unmodified files extracted from the signed 2103402 parent APK.
"""
import ast, contextlib, hashlib, importlib.util, json, os, pathlib, sys, tempfile, types, unittest

SOURCE = pathlib.Path(os.environ["CC_ROOT"])
xbmc=types.SimpleNamespace(LOGINFO=1,log=lambda *a:None,getCondVisibility=lambda *a:False)
common=types.SimpleNamespace(persistence_scope=contextlib.nullcontext,addon_profile=lambda:None,
    atomic_json=lambda path,data:path.write_text(json.dumps(data)),
    read_json=lambda path,default:json.loads(path.read_text()) if path.exists() else default)
sys.modules['xbmc']=xbmc
sys.modules['common']=common
spec=importlib.util.spec_from_file_location('resume_hub',SOURCE/'resume_hub.py')
hub=importlib.util.module_from_spec(spec)
sys.modules['resume_hub']=hub
spec.loader.exec_module(hub)

tree=ast.parse((SOURCE/'plugin.py').read_text())
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_mutate_locked','_later_keys')]
namespace={'hub':hub,'persistence_scope':contextlib.nullcontext}
with tempfile.TemporaryDirectory() as path:
    namespace['PROFILE']=pathlib.Path(path)
    exec(compile(ast.fix_missing_locations(ast.Module(selected,type_ignores=[])),'plugin.py','exec'),namespace)
    identity=hub.show_identity('tvshow',{'tmdb':'65942'})
    route='plugin://plugin.video.watchnixtoons2/?action=show&slug=rezero'
    entry=dict(key=hub.identity_key(identity),identity=identity,media='tv',
        title='Re:ZERO',label='Re:ZERO',source=route,stable_source=route,
        season=-1,episode=-1,dbid=-1,tmdb='65942')
    key=entry['key']
    checks=[
      ('mark-watched','watched',{}),
      ('toggle-watchlist','watchlist',{}),
      ('toggle-collection','collection',{}),
      ('add-list','lists',{'name':'Anime'}),
      ('save-later','later',{})]
    for action,bucket,extra in checks:
        storage=namespace['PROFILE']/hub.CONTINUE_FILE
        if storage.exists():storage.unlink()
        changed,notice=namespace['_mutate_locked'](action,key,'',incoming=entry,**extra)
        saved=hub.load(namespace['PROFILE'])
        found=saved[bucket]['Anime'][key] if bucket=='lists' else saved[bucket][key]
        assert changed,(action,notice)
        assert found['source']==route,(action,'source changed')
        assert found['stable_source']==route,(action,'stable route changed')
        assert hub.same_identity(hub.entry_identity(found), identity),(action,'identity changed')
        print('PASS',action,'durable local data, exact route, typed identity')
print('PASS 5 real Resume Hub mutation paths')
