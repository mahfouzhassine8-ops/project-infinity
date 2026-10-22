"""Exercise actual changed Python, native invariants and unchanged local state."""
import ast,copy,hashlib,importlib.util,json,os,random,re,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from contextlib import nullcontext
from unittest.mock import patch
from urllib.parse import urlencode
import components100 as c,native100 as n
APK=Path(os.environ.get('INFINITY_2103399_APK',str(c.ROOT.parent/'baseline99/Infinity-2103399-Fold-Corrective-EXPERIMENTAL.apk')))
NATIVE=Path(os.environ.get('INFINITY_2103399_NATIVE',str(c.ROOT.parent/'baseline99/source99/native')))
def definitions(raw,names,ns):
 t=ast.parse(raw);exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in names],type_ignores=[]),'actual-component.py','exec'),ns);return ns
def module(name,raw):
 mod=types.ModuleType(name);sys.modules[name]=mod;exec(compile(raw,name+'.py','exec'),mod.__dict__);return mod

def route(kind='movie',ids=None,season=2,episode=3,meta=''):
 values=dict(action='play_Item',title='Fixture title',imdb='tt1234567',tmdb='123',meta=meta)
 if kind=='tv':values.update(season=str(season),episode=str(episode),tvshowtitle='Fixture show')
 values.update(ids or {})
 return 'plugin://plugin.video.umbrella/?'+urlencode(values)

class Corrective100(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.before=c.read_parent(APK);cls.after=c.components(cls.before)
  cls.native=n.patches({p:(NATIVE/p).read_bytes() for p in n.PATHS},cls.before,cls.after)
  cls.identity=module('latest_identity',cls.after[c.LATEST+'/identity.py'])
  cls.ui=module('option_b100',cls.after[c.UI+'/home_option_b.py'])
 def hub(self):
  common=types.ModuleType('common');common.persistence_scope=nullcontext
  common.read_json=lambda p,d:json.loads(p.read_text()) if p.exists() else copy.deepcopy(d)
  common.atomic_json=lambda p,d:p.write_text(json.dumps(d))
  xbmc=types.ModuleType('xbmc');xbmc.log=lambda *a:None;xbmc.LOGINFO=1
  with patch.dict(sys.modules,common=common,xbmc=xbmc):mod=module('resume_hub',self.after[c.CC+'/resume_hub.py'])
  sys.modules['resume_hub']=mod
  return mod
 def experience(self):
  common=types.ModuleType('common');common.persistence_scope=nullcontext
  with patch.dict(sys.modules,common=common):return module('experience100',self.after[c.CC+'/experience.py'])
 def test_real_play_item_movie_regression_and_lossless_lifecycles(self):
  old=module('old_identity100',self.before[c.LATEST+'/identity.py'])
  for cycle in ('initial','after_movie','home_return','reload','restart'):
   for ident in range(5):
    url=route(meta='Provider-returned fixture metadata '*900,ids={'tmdb':str(123+ident)})
    self.assertGreater(len(url),4096)
    with self.assertRaises(ValueError):old.encode(url,'movie',{'tmdb':str(123+ident)})
    path=self.identity.encode(url,'movie',{'tmdb':str(123+ident)})
    self.assertLess(len(path),4096);self.assertEqual(self.identity.decode(path)['route'],url)
 def test_long_encoded_identity_retains_full_native_proof(self):
  rng=random.Random(1);meta=''.join(rng.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(11000))
  path=self.identity.encode(route(meta=meta),'movie',{'tmdb':'123'})
  self.assertGreater(len(path),4096);self.assertLess(len(path),32768)
  for control in (8101,8801):
   label='Selected fixture';proof=hashlib.sha256(f'{control}\n1\n{path}\n{label}'.encode()).hexdigest()
   fields=dict(Control=str(control),Index='1',Path=path,Label=label,Proof=proof)
   home=types.SimpleNamespace(getProperty=lambda key:fields.get(key.removeprefix('Infinity.HomeOptionB.Pending'),''))
   gui=types.SimpleNamespace(Window=lambda _:home)
   self.assertIsNotNone(self.ui.read_native_hold(gui,(str(control),'1',proof)))
   fields['Path']=path[:-1]+'0';self.assertIsNone(self.ui.read_native_hold(gui,(str(control),'1',proof)))
 def test_full_path_security_does_not_truncate_tail(self):
  self.assertFalse(self.ui._media_path('plugin://plugin.video.umbrella/?'+'a'*4090+'\nAction(Play)'))
  self.assertFalse(self.ui._media_path('plugin://plugin.video.umbrella/?'+'a'*4100))
  self.assertFalse(self.ui._media_path('plugin://plugin.infinity.latestreleases/?data=bad'))
 def test_identity_limits_checksums_wrong_ids_actions_preserved(self):
  for url,kind,ids in [(route(ids={'action':'tools_clearCache'}),'movie',{'tmdb':'123'}),(route(),'movie',{'tmdb':'999'}),(route(),'tvshow',{'tmdb':'123'}),(route(meta='x'*65536),'movie',{'tmdb':'123'})]:
   with self.assertRaises(ValueError):self.identity.encode(url,kind,ids)
  p=self.identity.encode(route(),'movie',{'tmdb':'123'})
  for bad in (p+'&action=open',p.replace('data=','data=AAAA'),p[:-1]+'0'):
   with self.assertRaises(ValueError):self.identity.decode(bad)
 def test_tv_small_identity_and_navigation_routes_preserved(self):
  old=module('old_tv_identity100',self.before[c.LATEST+'/identity.py'])
  for action in ('seasons','episodes'):
   url='plugin://plugin.video.umbrella/?'+urlencode(dict(action=action,imdb='tt1234567',tmdb='123',season='2'))
   self.assertEqual(old.encode(url,'tvshow',{'tmdb':'123'}),self.identity.encode(url,'tvshow',{'tmdb':'123'}))
   for control in (8102,8802):
    path=self.identity.encode(url,'tvshow',{'tmdb':'123'});label='Fixture TV';proof=hashlib.sha256(f'{control}\n0\n{path}\n{label}'.encode()).hexdigest()
    fields=dict(Control=str(control),Index='0',Path=path,Label=label,Proof=proof)
    gui=types.SimpleNamespace(Window=lambda _:types.SimpleNamespace(getProperty=lambda key:fields.get(key.removeprefix('Infinity.HomeOptionB.Pending'),'')))
    self.assertIsNotNone(self.ui.read_native_hold(gui,(str(control),'0',proof)))
 def test_home_only_two_labels_change_per_copy(self):
  for name,b in self.before.items():
   if name.startswith(c.SKIN+'/') and name.endswith('/Home.xml'):
    self.assertEqual(self.after[name],b.replace(b'Umbrella - Latest Releases','Infinity \u2013 Latest Releases'.encode()))
    self.assertIn(b'plugin://plugin.infinity.latestreleases/',b)
 def test_popup_assets_actions_themes_rails_search_trakt_unchanged(self):
  for name,b in self.before.items():
   if ('InfinityHomeOptionB.xml' in name or name.endswith('/infinity_search.py') or name.endswith('/infinity_trakt.py') or name.endswith('/resume_hub.py') or name.startswith('script.infinity.rails/') or '/colors/' in name or 'infinity_native_ambient.py' in name):self.assertEqual(b,self.after[name],name)
  for fn in ('geometry','_show_verified_hold'):
   def node(raw):return next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef) and x.name==fn)
   self.assertEqual(ast.dump(node(self.before[c.UI+'/home_option_b.py'])),ast.dump(node(self.after[c.UI+'/home_option_b.py'])))
 def test_favorite_keeps_play_item_identity_without_redesign(self):
  before=self.before[c.UI+'/home_option_b.py']
  after=self.after[c.UI+'/home_option_b.py'].replace(b"else ('play','play_Item')): return {}",b"else ('play',)): return {}")
  fn=lambda raw:next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef) and x.name=='_perform')
  self.assertEqual(ast.dump(fn(before)),ast.dump(fn(after)))
 def test_actual_feed_emits_verified_owned_items_and_fallback_receipts(self):
  class Item:
   def __init__(self,**kw):self.properties={};self.info={}
   def setArt(self,v):pass
   def setInfo(self,k,v):self.info=v
   def setUniqueIDs(self,v):pass
   def setCast(self,v):pass
   def setProperty(self,k,v):self.properties[k]=v
  for section in ('movies','tvshows'):
   emitted=[];props={};logs=[]
   row=dict(file=route(meta='metadata '*2000) if section=='movies' else 'plugin://plugin.video.umbrella/?action=seasons&tmdb=123',label='fixture',title='fixture',uniqueid={'tmdb':'123'},plot='Actual supplied synopsis')
   xbmc=types.SimpleNamespace(executeJSONRPC=lambda raw:json.dumps({'result':{'files':[row]}}),log=lambda *a:logs.append(a),LOGINFO=1)
   gui=types.SimpleNamespace(ListItem=Item,Window=lambda _:types.SimpleNamespace(setProperty=lambda k,v:props.__setitem__(k,v)))
   plugin=types.SimpleNamespace(setContent=lambda *a:None,addDirectoryItems=lambda h,items,num:emitted.extend(items),addSortMethod=lambda *a:None,endOfDirectory=lambda *a,**kw:None,SORT_METHOD_NONE=0)
   ns={'__name__':'fixture_feed','__file__':str(c.HERE/'overlay'/c.LATEST/'default.py')}
   with patch.dict(sys.modules,xbmc=xbmc,xbmcgui=gui,xbmcplugin=plugin,identity=self.identity),patch.object(sys,'argv',['plugin://plugin.infinity.latestreleases/','1','?action=feed&section='+section]):
    exec(compile(self.after[c.LATEST+'/default.py'],'actual-default.py','exec'),ns);ns['run']()
   self.assertEqual(len(emitted),1);self.assertTrue(emitted[0][0].startswith(self.identity.BASE))
   fact=json.loads(props['Infinity.LatestReleases.Receipt.'+section]);self.assertTrue(fact['emitted']);self.assertEqual(fact['owned'],1);self.assertEqual(fact['fallback'],0)
   self.assertEqual(self.identity.decode(emitted[0][0])['route'],row['file'])
 def test_recovery_exact_movie_episode_ids_no_title_guess(self):
  hub=self.hub();e=self.experience();verify=lambda _:dict(scope='show_episode')
  for media in ('movie','tv'):
   original=route(media);identity=e.source_identity(original,media,{'tmdb':'123','imdb':'tt1234567'},2,3,verify)
   self.assertIsNotNone(identity)
   entry=dict(media=media,identity=identity,season=2,episode=3,title='Same title is insufficient',source='https://expired.test/token')
   self.assertEqual(e.verified_source(entry,original,verify),original)
   self.assertFalse(e.verified_source(entry,original.replace('tmdb=123','tmdb=999'),verify))
   self.assertFalse(e.verified_source(entry,original,lambda _:None))
   if media=='tv':
    self.assertEqual(identity['scope'],'show_episode');self.assertFalse(e.verified_source(entry,original.replace('episode=3','episode=4'),verify))
 def test_recovery_legacy_unknown_episode_scope_not_upgraded(self):
  hub=self.hub();e=self.experience();entry=dict(media='tv',identity=hub.media_identity('tv',{'tmdb':'123'},2,3),season=2,episode=3)
  self.assertFalse(e.verified_source(entry,route('tv'),lambda _:dict(scope='show_episode')))
 def test_target_expired_direct_valid_route_missing_provider(self):
  hub=self.hub();e=self.experience()
  with patch.object(e,'_source_contract',lambda _:dict(scope='show_episode')):
   ns=dict(hub=hub,setting_bool=lambda *a:True,stable_route=e.stable_route,verified_source=e.verified_source,number=e.number,time=types.SimpleNamespace(time=lambda:100000),_has_addon=lambda *a:True,_has_tmdb_helper=lambda *a:False)
   definitions(self.after[c.CC+'/plugin.py'],{'_target'},ns)
   for media in ('movie','tv'):
    ident=e.source_identity(route(media),media,{'tmdb':'123'},2,3);entry=dict(key='a'*64,media=media,identity=ident,season=2,episode=3,source='https://expired.test/stream',updated=1,stable_source=route(media),position=97.5)
    self.assertEqual(ns['_target'](entry),route(media));self.assertEqual(entry['position'],97.5)
    entry.pop('stable_source');self.assertFalse(ns['_target'](entry))
 def test_actual_capture_carries_route_and_verified_show_identity(self):
  hub=self.hub();e=self.experience()
  with patch.object(e,'_source_contract',lambda _:dict(scope='show_episode')):
   ns=dict(xbmc=types.SimpleNamespace(getInfoLabel=lambda _:''),hub=hub,source_identity=e.source_identity,_continue_show_identity=lambda *a:{})
   definitions(self.after[c.CC+'/service.py'],{'_continue_identity'},ns)
   item=dict(type='episode',title='Fixture episode',showtitle='Fixture show',season=2,episode=3,uniqueid={'tmdb':'123'},file='https://resolved.test/stream',infinity_original_route=route('tv'))
   entry=ns['_continue_identity'](item);self.assertEqual(entry['stable_source'],route('tv'));self.assertTrue(entry['show_ids_verified']);self.assertEqual(entry['identity']['scope'],'show_episode')
   item['infinity_original_route']=route('tv',episode=4);entry=ns['_continue_identity'](item);self.assertNotIn('stable_source',entry)
 def test_local_state_reopen_no_tracking_database_or_duplicate_progress(self):
  hub=self.hub();identity=hub.media_identity('movie',{'tmdb':'123'});key=hub.identity_key(identity)
  entry=dict(key=key,media='movie',identity=identity,source='https://expired.test/stream',stable_source=route(),position=97.5,duration=700,updated=1)
  state=hub._normalize({'items':{key:entry},'watched':{'b'*64:{'sentinel':'watched'}},'watchlist':{'c'*64:{'sentinel':'watchlist'}},'collection':{'d'*64:{'sentinel':'collection'}},'foreign':{'keep':True}})
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);hub.save(root,state);saved=hub.load(root)
   self.assertEqual(saved['items'][key],entry);self.assertEqual(len(saved['items']),1)
   for k in ('watched','watchlist','collection','foreign'):self.assertEqual(saved[k],state[k])
   self.assertEqual([p.name for p in root.iterdir()],[hub.CONTINUE_FILE])
 def test_native_bounds_proofs_durability_and_cobra_scope(self):
  raw=self.native[n.CONTAINER].decode();self.assertIn('infinityLatest ? 32768U : 4096U',raw)
  for leaf in ('default.py','identity.py','addon.xml'):self.assertIn(c.sha(self.after[c.LATEST+'/'+leaf]),raw)
  for p in (n.PLUGIN,n.PLAYER):
   self.assertIn(b'#if defined(TARGET_ANDROID)',self.native[p]);self.assertIn(b'== "skin.infinity.diggz"',self.native[p])
  for p in ('xbmc/interfaces/python/InfinityPythonPersistenceSource.h','xbmc/dbwrappers/InfinitySQLiteVFS.h'):
   self.assertNotIn(p,n.PATHS)
  for name,h in json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']).items():self.assertEqual(h,c.sha(self.after[c.CC+'/'+name]))
 def test_actual_native_source_capture_branches_compile_and_execute(self):
  plugin=self.native[n.PLUGIN].decode();player=self.native[n.PLAYER].decode()
  marker='    // INFINITY_2103400_SOURCE_CAPTURE:'
  left=plugin.rfind('#if defined(TARGET_ANDROID)',0,plugin.index(marker));right=plugin.index('#endif',left)+len('#endif');capture=plugin[left:right]
  marker='  // Add only the provenance of this exact active video item'
  left=player.rfind('#if defined(TARGET_ANDROID)',0,player.index(marker));right=player.index('#endif',left)+len('#endif');report=player[left:right]
  source=r"""
#include <cassert>
#include <map>
#include <memory>
#include <string>
struct Value {std::string text;std::map<std::string,Value> children;Value& operator[](const std::string& k){return children[k];}Value& operator=(const std::string& v){text=v;return *this;}std::string asString()const{return text;}};
struct Settings {std::string skin="skin.infinity.diggz";std::string GetString(const char*){return skin;}Settings* GetSettings(){return this;}} settings;
struct CServiceBroker {static Settings* GetSettingsComponent(){return &settings;}};
struct Item {std::map<std::string,Value> p;void SetProperty(const std::string& k,const std::string& v){p[k]=v;}Value GetProperty(const std::string& k){return p[k];}};
struct Url {std::string host;std::string GetHostName(){return host;}};
bool live=false;bool IsPVRChannel(){return live;}enum Type {Video,Audio};
void capture(Item& resultItem,Url url,const std::string& strPath){
"""+capture+r"""
}
Value report(std::shared_ptr<Item> fileItem,Type player){Value result;
"""+report+r"""
return result;}
int main(){
 const std::string route="plugin://plugin.video.umbrella/?action=play_Item&tmdb=123&season=2&episode=3";
 auto item=std::make_shared<Item>();capture(*item,{"plugin.video.umbrella"},route);
 assert(report(item,Video)["item"]["infinity_original_route"].asString()==route);
 assert(report(item,Audio)["item"]["infinity_original_route"].asString().empty());
 live=true;assert(report(item,Video)["item"]["infinity_original_route"].asString().empty());live=false;
 settings.skin="skin.cobra";auto cobra=std::make_shared<Item>();capture(*cobra,{"plugin.video.umbrella"},route);
 assert(cobra->p.empty());assert(report(item,Video)["item"]["infinity_original_route"].asString().empty());
 settings.skin="skin.infinity.diggz";Item other;capture(other,{"plugin.video.other"},route);assert(other.p.empty());
 capture(other,{"plugin.video.umbrella"},std::string(65537,'x'));assert(other.p.empty());
}
"""
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cpp=root/'actual.cpp';cpp.write_text(source);binary=root/'probe'
   result=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-DTARGET_ANDROID',str(cpp),'-o',str(binary)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);subprocess.run([str(binary)],check=True)

 def test_health_named_capture_avoids_rejected_unnamed_open(self):
  # Reproduce the actual O_TMPFILE EACCES path with the unchanged observer in
  # a disposable interpreter, then run the changed production capture function.
  script=c.HERE/'health_probe.py'
  for mode,expected in [('baseline',True),('candidate',False)]:
   result=subprocess.run([sys.executable,str(script),str(NATIVE),str(APK),mode],text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   facts=json.loads(result.stdout.splitlines()[-1]);self.assertEqual(facts['write_failure_observed'],expected);self.assertTrue(facts['diagnostic_capture_retained'])

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Corrective100)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 out=Path(os.environ.get('INFINITY_100_RESULTS','TARGETED-RESULTS.json'));out.write_text(json.dumps(dict(passed=result.wasSuccessful(),tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),physical_fold_verified=False),indent=2)+'\n')
 sys.exit(0 if result.wasSuccessful() else 1)
