"""Connected WatchNixtoons2 context->original popup->Resume Hub local writer test."""
import ast,contextlib,importlib.util,json,os,pathlib,sys,tempfile,types

root=pathlib.Path(os.environ["CC_ROOT"])
patched=pathlib.Path(os.environ["PATCHED_CONTEXT"])
xbmc=types.SimpleNamespace(LOGINFO=1,getSkinDir=lambda:'skin.infinity.diggz',
  getCondVisibility=lambda *a:False,log=lambda *a:None,
  getInfoLabel=lambda *a:'',executebuiltin=lambda *a:None)
xbmcgui=types.SimpleNamespace(getCurrentWindowId=lambda:10000,
  Dialog=lambda:types.SimpleNamespace(input=lambda *a:'Anime'),
  Window=lambda n:None)
common=types.SimpleNamespace(persistence_scope=contextlib.nullcontext,
  addon_profile=lambda:None,atomic_json=lambda path,data:path.write_text(json.dumps(data)),
  read_json=lambda path,default:json.loads(path.read_text()) if path.exists() else default)
sys.modules.update({'xbmc':xbmc,'xbmcgui':xbmcgui,'common':common})
spec=importlib.util.spec_from_file_location('resume_hub',root/'resume_hub.py')
hub=importlib.util.module_from_spec(spec)
sys.modules['resume_hub']=hub
spec.loader.exec_module(hub)
hub.flush_kodi_sync=lambda *a,**kw:True
hub.queue_kodi_sync=lambda *a,**kw:None

popup=ast.parse((root/'plugin.py').read_text())
wanted={'show_item_menu','_mutate_locked','_menu_rows','_selected_menu_entry',
        '_menu_resume','_menu_progress_state','_later_keys'}
popup_ns={'hub':hub,'xbmc':xbmc,'xbmcgui':xbmcgui,'nullcontext':contextlib.nullcontext,
          'persistence_scope':contextlib.nullcontext,
          '_favourite':lambda *a,**kw:(None,None),
          '_menu_play_available':lambda *a,**kw:True,
          'navigation_target':lambda *a,**kw:'plugin://plugin.video.watchnixtoons2/'}
exec(compile(ast.fix_missing_locations(ast.Module([
  node for node in popup.body if isinstance(node,ast.FunctionDef) and node.name in wanted
],type_ignores=[])),'plugin.py','exec'),popup_ns)

context=ast.parse(patched.read_text())
wanted={'_watchnixtoons_identity_slot','_watchnixtoons_verified_link',
  '_watchnixtoons_owned_records','_watchnixtoons_store_verified_link',
  '_watchnixtoons_exact_previous','_watchnixtoons_tracking'}
class Tag:
    def getTitle(self):return 'Re:ZERO'
    def getMediaType(self):return 'tvshow'
    def getSeason(self):return -1
    def getEpisode(self):return -1
    def getPlayCount(self):return 0
class Item:
    def getPath(self):return 'plugin://plugin.video.watchnixtoons2/?slug=rezero'
    def getVideoInfoTag(self):return Tag()
    def getLabel(self):return 'Re:ZERO'
    def getArt(self,key):return ''
context_ns={'hub':hub,'persistence_scope':contextlib.nullcontext,
            'xbmcgui':xbmcgui,'addon_profile':None,
            '_popup_module':lambda:types.SimpleNamespace(show_item_menu=popup_ns['show_item_menu'])}
exec(compile(ast.fix_missing_locations(ast.Module([
  node for node in context.body if isinstance(node,ast.FunctionDef) and node.name in wanted
],type_ignores=[])),'context.py','exec'),context_ns)

with tempfile.TemporaryDirectory() as directory:
    profile=pathlib.Path(directory)
    popup_ns['PROFILE']=profile
    context_ns['addon_profile']=lambda:profile
    item=Item()
    route=item.getPath()
    identity=hub.show_identity('tvshow',{'tmdb':'65942'})
    entry=dict(key=hub.identity_key(identity),identity=identity,media='tv',
      source=route,stable_source=route,title=item.getLabel(),label=item.getLabel(),
      season=-1,episode=-1,tmdb='65942')
    assert context_ns['_watchnixtoons_store_verified_link'](item,route,'tvshow',entry)
    checks=[('Add to Watchlist','toggle-watchlist','watchlist'),
        ('Add to Collection','toggle-collection','collection'),
        ('Save for Later','save-later','later'),
        ('Mark Watched','mark-watched','watched'),
        ('Add to Custom List','add-list','lists')]
    for label,operation,bucket in checks:
        assert context_ns['_watchnixtoons_tracking'](
          item,route,'tvshow',entry['title'],label,operation),operation
        data=hub.load(profile)
        row=data[bucket]['Anime'][entry['key']] if bucket=='lists' else data[bucket][entry['key']]
        assert row['source']==route
        assert row['stable_source']==route
        assert hub.same_identity(hub.entry_identity(row),identity)
        print('PASS',operation,'context->popup->writer->persisted JSON')
print('PASS complete five-operation host dispatch integration')
