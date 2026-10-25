"""End-to-end host: WatchNixtoons2 exact route -> popup -> actual Hub mutation."""
import ast,contextlib,importlib.util,json,pathlib,sys,tempfile,types,urllib.parse
ROOT=pathlib.Path(__file__).parent
SRC=ROOT/'patched';PARENT=ROOT/'parent_cc'
xbmc=types.SimpleNamespace(LOGINFO=1,getSkinDir=lambda:'skin.infinity.diggz',
  getCondVisibility=lambda *a:False,log=lambda *a:None,
  getInfoLabel=lambda *a:'',executebuiltin=lambda *a:None)
xbmcgui=types.SimpleNamespace(getCurrentWindowId=lambda:10000,
  Dialog=lambda:types.SimpleNamespace(input=lambda *a:'Anime',notification=lambda *a:None,
    ok=lambda *a:None),NOTIFICATION_INFO=1)
common=types.SimpleNamespace(persistence_scope=contextlib.nullcontext,
  addon_profile=lambda:None,atomic_json=lambda path,data:path.write_text(json.dumps(data)),
  read_json=lambda path,default:json.loads(path.read_text()) if path.exists() else default)
sys.modules.update({'xbmc':xbmc,'xbmcgui':xbmcgui,'common':common})
spec=importlib.util.spec_from_file_location('resume_hub',SRC/'resume_hub.py')
hub=importlib.util.module_from_spec(spec);sys.modules['resume_hub']=hub;spec.loader.exec_module(hub)
hub.publish_home=lambda *a:None
hub.flush_kodi_sync=lambda *a,**k:True
class Tag:
  def getMediaType(self):return 'tvshow'
  def getTitle(self):return 'Re:ZERO'
  def getSeason(self):return -1
  def getEpisode(self):return -1
  def getPlayCount(self):return 0
class Item:
  def __init__(self,route):self.route=route
  def getPath(self):return self.route
  def getVideoInfoTag(self):return Tag()
  def getLabel(self):return 'Re:ZERO'
  def getArt(self,kind):return ''
route='plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url='+urllib.parse.quote_plus('https://www.wcostream.tv/anime/re-zero-starting-life')

with tempfile.TemporaryDirectory() as path:
  profile=pathlib.Path(path)
  popup=ast.parse((PARENT/'plugin.py').read_text())
  wanted={'show_item_menu','_mutate_locked','_menu_rows','_selected_menu_entry',
    '_menu_resume','_menu_progress_state','_later_keys'}
  chosen=[n for n in popup.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
  ns={'hub':hub,'xbmc':xbmc,'xbmcgui':xbmcgui,'nullcontext':contextlib.nullcontext,
    'persistence_scope':contextlib.nullcontext,'PROFILE':profile,
    '_favourite':lambda *a,**k:(None,None),
    '_menu_play_available':lambda *a,**k:True,
    'navigation_target':lambda entry,*a,**k:entry.get('source')}
  exec(compile(ast.fix_missing_locations(ast.Module(chosen,type_ignores=[])),'plugin.py','exec'),ns)
  context=ast.parse((SRC/'context.py').read_text())
  cfunc={'_watchnixtoons_source_entry','_watchnixtoons_tracking',
    '_watchnixtoons_exact_previous','_watchnixtoons_identity_slot',
    '_watchnixtoons_verified_link','_watchnixtoons_owned_records'}
  funcs=[n for n in context.body if isinstance(n,ast.FunctionDef) and n.name in cfunc]
  cns={'hub':hub,'xbmcgui':xbmcgui,'addon_profile':lambda:profile,
    '_popup_module':lambda:types.SimpleNamespace(show_item_menu=ns['show_item_menu'])}
  exec(compile(ast.fix_missing_locations(ast.Module(funcs,type_ignores=[])),'context.py','exec'),cns)
  item=Item(route)
  for label,operation,bucket in [
      ('Add to Watchlist','toggle-watchlist','watchlist'),
      ('Add to Collection','toggle-collection','collection'),
      ('Save for Later','save-later','later'),
      ('Mark Watched','mark-watched','watched'),
      ('Add to Custom List','add-list','lists')]:
    assert cns['_watchnixtoons_tracking'](item,route,'tvshow','Re:ZERO',label,operation),operation
    data=hub.load(profile)
    key=next(iter(data['nixtoons_verified_links']),None) if False else hub.identity_key(hub.watchnixtoons_source_identity(route,'tvshow'))
    saved=data[bucket]['Anime'][key] if bucket=='lists' else data[bucket][key]
    assert saved['source']==route and saved['stable_source']==route
    assert hub.entry_identity(saved)['scope']=='watchnixtoons_local'
    print('PASS',operation,'menu→real writer→disk→identity')
  assert len(hub.load(profile)['later'])==1
  assert len(hub.load(profile)['watchlist'])==1
  assert len(hub.load(profile)['collection'])==1
  assert len(hub.load(profile)['watched'])==1
  assert len(hub.load(profile)['lists']['Anime'])==1
  print('PASS all five actions, one persistent local source identity, original route')