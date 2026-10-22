"""Execute production corrections against protected source and real persistence."""
import ast,copy,hashlib,importlib,importlib.util,json,os,re,sys,tempfile,time,types,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
from urllib import parse
from zipfile import ZipFile
import components101 as c,native101 as n
APK=Path(os.environ.get('INFINITY_2103400_APK',str(c.ROOT.parent/'baseline/package/Infinity-2103400-Fold-Corrective-EXPERIMENTAL.apk')))
NATIVE=Path(os.environ.get('INFINITY_2103400_NATIVE',str(c.ROOT.parent/'baseline/native')))
SEREN=Path(os.environ.get('INFINITY_SEREN_SOURCE',str(c.ROOT.parent/'evidence/providers/plugin.video.seren')))
def module(name,raw,path=None):
 m=types.ModuleType(name);m.__file__=str(path or Path(name+'.py').absolute());sys.modules[name]=m;exec(compile(raw,m.__file__,'exec'),m.__dict__);return m

def node(raw,name):return next(x for x in ast.parse(raw).body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
class Corrective101(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.before=c.read_parent(APK);cls.after=c.components(cls.before);cls.temp=tempfile.TemporaryDirectory();cls.stage=Path(cls.temp.name)
  for name,body in cls.after.items():p=cls.stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
  cls.profile=cls.stage/'profile';cls.profile.mkdir();cls.versions=dict(c.VERSIONS)
  cls.xbmc=types.SimpleNamespace(LOGINFO=1,LOGWARNING=2,LOGERROR=3,log=lambda *a:None,getSkinDir=lambda:'skin.infinity.diggz',getCondVisibility=lambda v:True,getInfoLabel=lambda v:'',executebuiltin=lambda *a:None,executeJSONRPC=lambda raw:json.dumps({'result':{}}),Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:False))
  class Addon:
   def __init__(self,aid=c.CC):self.aid=aid
   def getAddonInfo(self,key):return {'id':self.aid,'version':cls.versions.get(self.aid,''),'path':str(cls.stage/self.aid),'profile':str(cls.profile),'icon':''}.get(key,'')
  cls.addon=types.SimpleNamespace(Addon=Addon)
  cls.gui=types.SimpleNamespace(Window=lambda _:types.SimpleNamespace(getProperty=lambda k:'',setProperty=lambda *a:None,clearProperty=lambda *a:None),Dialog=lambda:types.SimpleNamespace(ok=lambda *a:None))
  cls.vfs=types.SimpleNamespace(translatePath=lambda v:v)
  cls.stub=patch.dict(sys.modules,xbmc=cls.xbmc,xbmcaddon=cls.addon,xbmcgui=cls.gui,xbmcvfs=cls.vfs,xbmcplugin=types.SimpleNamespace());cls.stub.start()
  sys.path.insert(0,str(cls.stage/c.CC));sys.path.insert(0,str(cls.stage/c.UI))
  for name in ('common','checkpoint_runtime','persistence_participant','resume_hub','experience','context','infinity_trakt','infinity_search','latest_identity'):sys.modules.pop(name,None)
  cls.common=importlib.import_module('common');cls.hub=importlib.import_module('resume_hub');cls.trakt=importlib.import_module('infinity_trakt');cls.search=importlib.import_module('infinity_search');cls.ui=importlib.import_module('home_option_b')
  cls.part=importlib.import_module('persistence_participant');cls.checkpoint=importlib.import_module('checkpoint_runtime')
  cls.store=cls.part.PersistenceParticipant(cls.profile,cls.part.EngineOwner(os.getpid(),'infinity-101-host-test-owner'));cls.store.bind_engine();cls.checkpoint._stores[str(cls.profile.resolve())]=cls.store
 @classmethod
 def tearDownClass(cls):cls.stub.stop();cls.temp.cleanup()
 def reset(self,value=None):
  self.store.update('continue-watching.json',{},lambda _:copy.deepcopy(value or {'schema':2,'items':{},'sources':{'sentinel':{'route':'keep'}},'watched':{'keep':True},'foreign':{'preserve':[1,2,3]}}))
 def bridge(self):
  for name in ('controller','bridge_state','provider_contracts'):sys.modules.pop(name,None)
  return self.trakt._bridge()
 def test_01_exact_baseline_all_native_inputs_and_signed_identity_receipts(self):
  archive=APK.parent/'Infinity-2103400-Source-and-Build-Receipts.zip'
  self.assertEqual(c.digest(archive),'ec2d7552544a7fd84f5d71ee5dc6172d870c16ff37b845f56b063346d545151c')
  with ZipFile(archive) as z:
   pins=json.loads(z.read('NATIVE-SOURCE-MAP.json'));self.assertEqual(len(pins),9404)
   for p,h in pins.items():self.assertEqual(c.digest(NATIVE/p),h,p)
 def test_02_components_versions_pins_and_no_unapproved_delta(self):
  for addon,v in c.VERSIONS.items():self.assertEqual(ET.fromstring(self.after[addon+'/addon.xml']).get('version'),v)
  for name,pin in json.loads(self.after[c.WB+'/CONTROLLER-PREIMAGES.json']).items():self.assertEqual(c.sha(self.after[c.CC+'/'+name]),pin)
  self.assertEqual(json.loads(self.after[c.WB+'/CONTROLLER-PREIMAGES.json']),json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']))
  for name,body in self.before.items():
   if name.startswith((c.HEALTH+'/',c.LATEST+'/','script.infinity.rails/')) or '/colors/' in name or name.endswith(('/resume_hub.py','/common.py','/persistence_participant.py','/experience.py','/service.py','/plugin.py')):self.assertEqual(self.after[name],body,name)
  self.assertFalse(any('cobra' in p.lower() for p in c.ledger(self.before,self.after)['changed']))
 def test_03_obsolete_bridge_version_reproduced_exact_current_component_admitted(self):
  self.assertIn(b"!='1.0.5'",self.before[c.CC+'/infinity_trakt.py'])
  bridge,mods=self.bridge();self.assertEqual(Path(bridge.__file__).resolve(),self.stage/c.WB/'context.py');self.assertEqual(set(mods),{'common','context','resume_hub'})
  for name,mod in mods.items():self.assertEqual(Path(mod.__file__),self.stage/c.CC/(name+'.py'))
 def test_04_bridge_rejects_version_manifest_source_and_loaded_path_drift(self):
  self.bridge();self.versions[c.WB]='1.0.9'
  with self.assertRaises(RuntimeError):self.trakt._bridge()
  self.versions[c.WB]=c.VERSIONS[c.WB]
  for leaf in ('addon.xml','context.py','controller.py','provider_contracts.py'):
   path=self.stage/c.WB/leaf;before=path.read_bytes();path.write_bytes(before+b'\n')
   with self.assertRaises((RuntimeError,ET.ParseError)):self.trakt._bridge()
   path.write_bytes(before)
  wrong=types.SimpleNamespace(__file__='/unverified/controller.py')
  with patch.dict(sys.modules,controller=wrong):
   with self.assertRaises(RuntimeError):self.trakt._bridge()
  for leaf in ('addon.xml','resume_hub.py','infinity_search.py'):
   path=self.stage/c.CC/leaf;before=path.read_bytes();path.write_bytes(before+b'\n')
   with self.assertRaises(RuntimeError):self.trakt._bridge()
   path.write_bytes(before)
 def test_05_trakt_read_rejects_symlinked_bridge_and_does_not_touch_state(self):
  self.reset();before=(self.profile/'continue-watching.json').read_bytes();root=self.stage/c.WB
  path=root/'context.py';raw=path.read_bytes();target=self.stage/'other-context.py';target.write_bytes(raw);path.unlink();path.symlink_to(target)
  try:
   with self.assertRaises(RuntimeError):self.trakt._bridge()
   self.assertEqual((self.profile/'continue-watching.json').read_bytes(),before)
  finally:path.unlink();path.write_bytes(raw)
 def test_06_all_typed_tracking_operations_roundtrip_without_progress_reconstruction(self):
  bridge,mods=self.bridge();self.reset()
  for kind in ('movie','episode','tvshow','season'):
   identity=self.hub.media_identity('movie',{'tmdb':'123'}) if kind=='movie' else self.hub.media_identity('tv',{'tvdb':'456'},2,3) if kind=='episode' else self.hub.show_identity(kind,{'tmdb':'789'},2)
   entry=dict(key=self.hub.identity_key(identity),identity=identity,media='movie' if kind=='movie' else 'tv',source='videodb://movies/titles/1' if kind=='movie' else 'videodb://tvshows/titles/2',title='verified fixture',season=2,episode=3,dbid=-1)
   for action in ('add-watchlist','remove-watchlist','add-collection','remove-collection','save-later','remove-later','mark-watched','mark-unwatched'):
    if kind in ('movie','episode'):bridge.controller.apply(mods,self.profile,entry,action)
    else:self.trakt.apply_local(self.profile,entry,action)
    value=self.store.read('continue-watching.json',{});self.assertEqual(value['items'],{});self.assertEqual(value['foreign'],{'preserve':[1,2,3]})
    reopened=self.part.PersistenceParticipant(self.profile,self.store.owner);self.assertEqual(reopened.read('continue-watching.json',{}),value)
 def test_07_selection_identity_functions_and_other_three_option_b_actions_preserved(self):
  for name in ('selected','apply_local','set_membership'):
   self.assertEqual(ast.dump(node(self.before[c.CC+'/infinity_trakt.py'],name)),ast.dump(node(self.after[c.CC+'/infinity_trakt.py'],name)))
  for name in ('Selection','capture','read_native_hold','_perform','geometry','_wait_for_option_b_close'):
   self.assertEqual(ast.dump(node(self.before[c.UI+'/home_option_b.py'],name)),ast.dump(node(self.after[c.UI+'/home_option_b.py'],name)))
 def option_runtime(self,raw,empty=False):
  mod=module('option_fixture_'+str(time.time_ns()),raw);events=[];test=self
  selected=mod.Selection(8101,1,'movies','plugin://plugin.video.umbrella/?action=play_Item&tmdb=1','Verified selected movie',year='2026',synopsis='' if empty else 'Actual selected synopsis',rating='8.1',runtime='99 min',genres='Drama',release_date='' if empty else '2026-10-22',certification='PG-13',credits='' if empty else 'Verified returned credits')
  mod.capture=lambda *a:selected;mod._trace=lambda *a:None
  class Control:
   def __init__(self,ident):self.id=ident;self.width=1920 if ident==2 else 920;self.height=1080 if ident==2 else 580;self.label='';self.text='';self.visible=True
   def getWidth(self):return self.width
   def getHeight(self):return self.height
   def setWidth(self,v):self.width=v
   def setHeight(self,v):self.height=v
   def setPosition(self,*v):self.position=v
   def setLabel(self,v):self.label=v
   def setText(self,v):self.text=v
   def setVisible(self,v):self.visible=v
   def setImage(self,v):self.image=v
   def setAnimations(self,v):self.animations=v
  class Dialog:
   def __init__(self,*a):self.controls={};self.props={};events.append(self)
   def getControl(self,ident):
    if ident==128:raise RuntimeError('Unknown control type for python')
    return self.controls.setdefault(ident,Control(ident))
   def setProperty(self,k,v):self.props[k]=v
   def setFocusId(self,i):self.focus=i
   def close(self):self.closed=True
   def doModal(self):
    self.onInit();self.onClick(104);test.assertTrue(self.expanded);test.assertIn('Actual selected synopsis' if not empty else 'Rating: 8.1',self.getControl(126).text);test.assertEqual(self.focus,128);test.assertEqual(len(events),1)
    self.onAction(types.SimpleNamespace(getId=lambda:92));test.assertFalse(self.expanded);test.assertEqual(self.focus,104);test.assertTrue(self.getControl(101).visible)
    self.onClick(104);self.onClick(9);test.assertFalse(self.expanded);test.assertEqual(self.focus,104);self.onClick(9)
  gui=types.SimpleNamespace(WindowXMLDialog=Dialog,getCurrentWindowDialogId=lambda:13000)
  xbmc=types.SimpleNamespace(getInfoLabel=lambda k:'2160',log=lambda *a:None)
  mod._show_verified_hold(xbmc,self.addon,gui,self.vfs,mod.NativeHold(8101,1,selected.path,selected.title,'0'*64))
  return events
 def test_08_option_b_baseline_scrollbar_exception_reproduced(self):
  raw=(NATIVE/'xbmc/interfaces/legacy/Window.cpp').read_text();start=raw.index('Control* Window::GetControlById');end=raw.index('return pControl',start)
  self.assertNotIn('GUICONTROL_SCROLLBAR',raw[start:end]);self.assertIn('GUICONTROL_GROUP',raw[start:end])
  with self.assertRaisesRegex(RuntimeError,'Unknown control type'):self.option_runtime(self.before[c.UI+'/home_option_b.py'])
 def test_09_option_b_metadata_back_and_single_modal_runtime(self):self.option_runtime(self.after[c.UI+'/home_option_b.py'])
 def test_10_option_b_compact_empty_metadata_runtime(self):
  events=self.option_runtime(self.after[c.UI+'/home_option_b.py'],True);self.assertEqual(len(events),1)
 def test_11_popup_geometry_viewports_mode_and_theme_resources(self):
  for physical in [(1080,2520),(2160,2160),(2520,1080),(2160,1800),(600,1200),(900,900)]:
   for expanded in (False,True):
    g=self.ui.geometry(1920,1080,*map(str,physical),expanded)
    self.assertGreaterEqual(g['x'],0);self.assertGreaterEqual(g['y'],0);self.assertLessEqual(g['x']+g['width'],1920);self.assertLessEqual(g['y']+g['height'],1080)
    for k,rect in g['details'].items():self.assertTrue(all(x>=0 for x in rect),str((physical,k,rect)))
  for name in ('InfinityHomeOptionB.xml','InfinityTraktNotice.xml'):
   tree=ET.fromstring(self.after[c.SKIN+'/unified/'+name]);ids=[n.get('id') for n in tree.iter('control')];self.assertEqual(len(ids),len(set(ids)))
   for font in tree.iter('font'):self.assertIn(('<name>'+font.text+'</name>').encode(),self.after[c.SKIN+'/unified/Font.xml'])
   self.assertTrue(all('OptionalMotionAllowed' in x.get('condition','') for x in tree.findall('animation')))
 def test_12_header_only_label_changes_all_layouts_themes_modes(self):
  seen=0
  for n,b in self.before.items():
   if n.startswith(c.SKIN+'/') and n.endswith('/Home.xml'):
    self.assertEqual(self.after[n],b.replace(b'INFINITY 1.0.5',c.HEADER));self.assertNotIn(b'INFINITY 1.0.5',self.after[n]);seen+=1
  self.assertEqual(seen,14)
 def test_13_seren_exact_installed_interface_queries_no_secondary_keyboard(self):
  proof=json.loads((c.HERE/'SEREN-QUERY-CONTRACT.json').read_text())
  for name,pin in proof['files'].items():self.assertEqual(c.digest(SEREN/name),pin)
  tools=ast.parse((SEREN/'resources/lib/common/tools.py').read_text());decode=next(x for x in tools.body if isinstance(x,ast.FunctionDef) and x.name=='deconstruct_action_args');ns={'parse':parse,'json':json};exec(compile(ast.Module(body=[decode],type_ignores=[]),'verified-seren-decoder.py','exec'),ns)
  for media,leaf,method in [('movie','movieMenus.py','movies_search'),('tv','tvshowMenus.py','shows_search')]:
   contract=self.search.recipe(SEREN,media);self.assertEqual(contract['query_codec'],'seren_json')
   fn=next(x for x in ast.walk(ast.parse((SEREN/'resources/lib/gui'/leaf).read_text())) if isinstance(x,ast.FunctionDef) and x.name==method)
   calls=[];g=types.SimpleNamespace(get_keyboard_input=lambda *a,**kw:self.fail('secondary provider keyboard'),get_bool_setting=lambda *a:False);scope={'g':g};exec(compile(ast.Module(body=[fn],type_ignores=[]),'verified-seren-search.py','exec'),scope)
   receiver=types.SimpleNamespace(movies_search_results=lambda q:calls.append(q),shows_search_results=lambda q:calls.append(q))
   for query in ('Relationship Rehab','null','None','123','true','100%25','%22','été العربية 🎬','a "quoted" title'):
    route=self.search.route(dict(id='plugin.video.seren',root=str(SEREN),contract=contract),query)
    params=dict(parse.parse_qsl(parse.urlsplit(route).query));decoded=ns['deconstruct_action_args'](params['action_args']);self.assertEqual(decoded,query);scope[method](receiver,decoded);self.assertEqual(calls[-1],query)
  self.assertIsNone(self.search.recipe(self.stage/'missing-seren','movie'))
 def test_14_provider_routes_revalidate_changed_or_disabled_component(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);file=root/'router.py';file.write_text('verified fixture')
   p=dict(id='plugin.video.fixture',root=str(root),contract=dict(pins={'router.py':c.digest(file)},params={'action':'query'},query_key='name',history={'action':'history'}))
   self.assertIn('name=Dune',self.search.route(p,'Dune'));file.write_text('changed')
   with self.assertRaises(RuntimeError):self.search.route(p,'Dune')
   with patch.object(self.xbmc,'getCondVisibility',lambda _:False):
    with self.assertRaises(RuntimeError):self.search.route(p,'Dune')
 def test_15_history_real_protected_participant_roundtrip_dedup_context_and_clear(self):
  self.reset();before=self.store.read('continue-watching.json',{});provider_db=self.profile/'provider-history.db';provider_db.write_bytes(b'untouched provider sentinel')
  for media in ('movie','tv'):
   for provider in ('all','plugin.video.umbrella','plugin.video.pov','plugin.video.seren','plugin.video.future'):
    history=self.search.shared_history('Relationship Rehab',media,provider,provider)
  self.assertEqual(len(history),2);self.assertEqual(history[0]['provider'],'plugin.video.future');self.assertEqual({r['media'] for r in history},{'movie','tv'})
  new=self.part.PersistenceParticipant(self.profile,self.store.owner);self.assertEqual(new.read('continue-watching.json',{})[self.search.HISTORY_KEY],history)
  self.search.shared_history(clear=True);state=self.store.read('continue-watching.json',{});self.assertEqual(state[self.search.HISTORY_KEY],[])
  for key,value in before.items():self.assertEqual(state[key],value)
  self.assertEqual(provider_db.read_bytes(),b'untouched provider sentinel');self.assertEqual(state['items'],{})
 def test_16_history_limits_and_malformed_state_fails_without_reset(self):
  self.reset()
  for i in range(55):self.search.shared_history('Query '+str(i),'movie','all','Search All')
  self.assertEqual(len(self.search.shared_history()),50)
  for value in ({'schema':True,'items':{}},{'schema':99,'items':{}},{'schema':2,'items':{},self.search.HISTORY_KEY:'bad'}):
   self.reset(value);before=(self.profile/'continue-watching.json').read_bytes()
   with self.assertRaises(RuntimeError):self.search.shared_history(clear=True)
   self.assertEqual((self.profile/'continue-watching.json').read_bytes(),before)
 def test_17_no_history_save_on_cancel_or_history_selection_only(self):
  self.reset();submitted=[];responses=[None,{'token':'bad','query':'Dune','provider':'all'}]
  for response in responses:
   class Keyboard:
    def __init__(self,*a):pass
    def doModal(self):pass
    def isConfirmed(self):return response is not None
    def getText(self):return json.dumps(response)
   with patch.object(self.search,'providers',lambda media:([],[])),patch.object(self.xbmc,'Keyboard',Keyboard,create=True),patch.object(self.xbmc,'executebuiltin',lambda *a:submitted.append(a)):
    self.search.open_search('tv')
  self.assertEqual(submitted,[]);self.assertEqual(self.search.shared_history(),[])
 def test_18_history_preserved_by_original_hub_normalization_and_save(self):
  self.reset();rows=self.search.shared_history('Dune','movie','all','Search All');state=self.hub.load(self.profile);self.hub.save(self.profile,state);self.assertEqual(self.search.shared_history(),rows);self.assertEqual(self.hub.load(self.profile)['items'],{})
 def test_19_native_changes_are_only_additive_exact_owner_admission(self):
  before={p:(NATIVE/p).read_bytes() for p in n.PATHS};after=n.patches(before,self.before,self.after)
  self.assertEqual(n.PATHS,{n.CONTRACT,n.COORDINATOR})
  old,new=before[n.CONTRACT],after[n.CONTRACT];marker=b'    // INFINITY_2103401_CC29_EXACT_SOURCES\n';start=new.index(marker);end=new.index(b'  };\n  return *contracts;',start)
  self.assertEqual(new[:start]+new[end:],old)
  self.assertEqual(after[n.COORDINATOR].replace(b' && active["addon_version"].asString() != "0.3.5.29"',b''),before[n.COORDINATOR])
  for pin in json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']).values():self.assertIn(pin.encode(),after[n.CONTRACT])
 def test_20_popup_close_motion_and_all_unrelated_skin_resources_preserved(self):
  for n,b in self.before.items():
   if n.startswith(c.SKIN+'/') and not n.endswith(('/Home.xml','/InfinityHomeOptionB.xml','/addon.xml','/Infinity-Protected-Manifest.json','/infinity-skin.json')):self.assertEqual(self.after[n],b,n)
  for tag in ('WindowOpen','WindowClose'):
   a=ET.fromstring(self.before[c.UI+'/resources/skins/Default/1080i/InfinityHomeOptionB.xml']);b=ET.fromstring(self.after[c.UI+'/resources/skins/Default/1080i/InfinityHomeOptionB.xml']);self.assertEqual([ET.tostring(x) for x in a.findall('animation') if x.text==tag],[ET.tostring(x) for x in b.findall('animation') if x.text==tag])

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Corrective101);result=unittest.TextTestRunner(verbosity=2).run(suite)
 out=Path(os.environ.get('INFINITY_101_RESULTS','TARGETED-RESULTS.json'));out.write_text(json.dumps(dict(passed=result.wasSuccessful(),tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),physical_fold_verified=False),indent=2)+'\n');sys.exit(0 if result.wasSuccessful() else 1)
