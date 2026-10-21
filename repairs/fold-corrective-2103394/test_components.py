import ast,copy,hashlib,json,os,re,sys,tempfile,types,unittest,subprocess
from pathlib import Path
from contextlib import nullcontext
from unittest.mock import patch
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import components94 as c,native94 as n,ui94,dex94,art94


def definitions(raw,names,namespace):
 t=ast.parse(raw);nodes=[x for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in names]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_component.py','exec'),namespace)
 return namespace

class Components(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.apk=Path(os.environ.get('INFINITY_2103393_APK',str(c.ROOT.parent/'protected-2103393/delivery/Infinity-2103393-Fold-Corrective-EXPERIMENTAL.apk')))
  cls.before=c.read_parent(cls.apk);cls.after=c.components(cls.before)
 def hub(self):
  common=types.ModuleType('common');common.persistence_scope=nullcontext
  common.read_json=lambda p,d:json.loads(p.read_text()) if p.exists() else copy.deepcopy(d)
  common.atomic_json=lambda p,d:p.write_text(json.dumps(d))
  xbmc=types.ModuleType('xbmc');xbmc.log=lambda *a:None;xbmc.LOGINFO=1
  mod=types.ModuleType('resume_hub')
  with patch.dict(sys.modules,common=common,xbmc=xbmc):exec(compile(self.after[c.CC+'/resume_hub.py'],'resume_hub.py','exec'),mod.__dict__)
  return mod
 def test_exact_component_versions_and_protected_owners(self):
  delta=c.ledger(self.before,self.after)
  self.assertFalse(delta['removed']);self.assertFalse(any('cobra' in p.lower() for p in delta['changed']))
  for aid,_,version in c.PACKAGES:self.assertEqual(ET.fromstring(self.after[aid+'/addon.xml']).get('version'),version)
  for name in ('common.py','persistence_participant.py','checkpoint_runtime.py','service.py','experience.py'):
   self.assertEqual(self.before[c.CC+'/'+name],self.after[c.CC+'/'+name])
  for name,body in self.before.items():
   if name.startswith('script.infinity.rails/'):self.assertEqual(body,self.after[name])
  pins=json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json'])
  self.assertEqual(len(pins),16);self.assertEqual(pins,json.loads(self.after[c.WB+'/CONTROLLER-PREIMAGES.json']))
  for p,h in pins.items():self.assertEqual(h,c.sha(self.after[c.CC+'/'+p]))
 def test_additive_save_later_schema_preserves_all_other_records(self):
  hub=self.hub();data={'schema':2,'foreign':{'sentinel':'preserve'},'pending_kodi_sync':[{'old':True}],
    'items':{'legacy-progress':{'media':'movie','position':30}},'watchlist':{'old-watchlist':{'title':'saved'}},
    'collection':{'old-collection':{'title':'saved'}},'lists':{'Custom':{'c'*64:{'title':'custom'}}}}
  original=copy.deepcopy(data)
  ident=hub.show_identity('tvshow',{'tmdb':'123'});key=hub.identity_key(ident)
  entry=dict(key=key,identity=ident,media='tv',title='Observed Show',source='plugin://plugin.video.umbrella/?show=123')
  ns={'hub':hub};definitions(self.after[c.CC+'/infinity_trakt.py'],{'set_membership'},ns)
  data=hub._normalize(data);self.assertTrue(ns['set_membership'](data,entry,'save-later'))
  self.assertFalse(ns['set_membership'](data,entry,'save-later'))
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);hub.save(root,data);saved=hub.load(root)
   for field,value in original.items():
    if field!='schema':self.assertEqual(saved[field],value)
   self.assertEqual(saved['later'][key]['identity'],ident)
   self.assertEqual(hub.find_entry(saved,key)['key'],key)
   self.assertEqual(hub.entries(saved,'tv','later')[0]['key'],key)
   self.assertTrue(ns['set_membership'](saved,entry,'remove-later'));hub.save(root,saved)
   self.assertFalse(hub.load(root)['later'])
 def test_exact_show_season_episode_namespaces_never_collide(self):
  hub=self.hub();ids={'tmdb':'123'}
  show=hub.show_identity('tvshow',ids);s1=hub.show_identity('season',ids,1);s2=hub.show_identity('season',ids,2)
  self.assertEqual(len({hub.identity_key(x) for x in (show,s1,s2)}),3)
  self.assertFalse(hub.same_identity(s1,s2));self.assertFalse(hub.same_identity(show,s1))
  for identity in (show,s1,s2):
   entry={'media':'tv','identity':identity,'season':identity.get('season',-1),'source':'plugin://provider/same'}
   self.assertEqual(hub.entry_identity(entry),identity)
   self.assertEqual(hub.compatible_key({'watchlist':{'a'*64:{'media':'tv','source':entry['source'],'tmdb':'123'}}},entry),hub.identity_key(identity))
 def test_eight_explicit_actions_independent_idempotent_membership(self):
  hub=self.hub();ns={'hub':hub};definitions(self.after[c.CC+'/infinity_trakt.py'],{'set_membership'},ns)
  tree=ast.parse(self.after[c.CC+'/infinity_trakt.py']);actions=next(ast.literal_eval(x.value) for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ACTIONS' for t in x.targets))
  self.assertEqual(len(actions),8);self.assertEqual(len(set(v for _,v in actions)),8)
  data=hub._normalize({});entry={'key':'b'*64,'media':'movie'}
  for action in ('add-watchlist','add-collection','save-later'):self.assertTrue(ns['set_membership'](data,entry,action))
  for bucket in ('watchlist','collection','later'):self.assertIn(entry['key'],data[bucket])
  for action in ('remove-watchlist','remove-collection','remove-later'):self.assertTrue(ns['set_membership'](data,entry,action));self.assertFalse(ns['set_membership'](data,entry,action))
 def test_option_b_actual_xml_panel_has_no_python_vecitems(self):
  mod=types.ModuleType('option_b94');sys.modules[mod.__name__]=mod
  exec(compile(self.after[c.UI+'/home_option_b.py'],'home_option_b.py','exec'),mod.__dict__)
  class Panel:
   def getSelectedPosition(self):return -1 # actual legacy XML wrapper behavior
  home=types.SimpleNamespace(getFocusId=lambda:8101,getControl=lambda _:Panel())
  gui=types.SimpleNamespace(getCurrentWindowId=lambda:10000,getCurrentWindowDialogId=lambda:9999,Window=lambda _:home)
  labels={'Container(9000).ListItem.Property(section)':'movies','Container(8101).CurrentItem':'2',
     'Container(8101).NumItems':'3','Container(8101).NumAllItems':'3','Container(8101).ListItem.Title':'Real title',
     'Container(8101).ListItem.Label':'Real title','Container(8101).ListItem.FileNameAndPath':'plugin://plugin.video.umbrella/?action=play&id=1'}
  xbmc=types.SimpleNamespace(getInfoLabel=lambda k:labels.get(k,''),getCondVisibility=lambda _:False,log=lambda *a:None,LOGINFO=1)
  native=mod.NativeHold(8101,1,labels['Container(8101).ListItem.FileNameAndPath'],'Real title','a'*64)
  self.assertEqual(mod.capture(xbmc,gui,native).index,1)
  labels['Container(8101).CurrentItem']='1';self.assertIsNone(mod.capture(xbmc,gui,native))
  labels['Container(8101).NumAllItems']='4';self.assertEqual(mod.capture(xbmc,gui,native).index,1)
  labels['Container(8101).ListItem.FileNameAndPath']='plugin://plugin.video.umbrella/?id=wrong';self.assertIsNone(mod.capture(xbmc,gui,native))
 def test_skin_actions_player_anchors_synopsis_and_no_reload(self):
  count=0
  for path,body in self.after.items():
   if path.endswith('/Home.xml') and path.startswith(c.SKIN+'/'):
    count+=1;t=ET.fromstring(body);group=t.find('.//control[@id="40002"]')
    self.assertEqual(len(group.findall('control[@type="textbox"]')),2)
    self.assertEqual(ET.tostring(t.find('.//control[@id="8830"]')),ET.tostring(ET.fromstring(self.before[path]).find('.//control[@id="8830"]')))
   if path.endswith('/InfinitySubtitleSettings.xml'):
    panel=ET.fromstring(body).find('.//control[@id="9900"]');self.assertEqual(panel.findtext('right'),'4%');self.assertEqual(panel.findtext('bottom'),'14%')
  self.assertEqual(count,14)
  self.assertNotIn(b"executebuiltin('ReloadSkin",self.after[c.CC+'/infinity_settings.py'])
  self.assertNotIn(b'Infinity.Select.Compact',self.after[c.CC+'/infinity_settings.py'])
  self.assertIn(b'InfinityItemOptions.xml',self.after[c.CC+'/infinity_settings.py'])
 def test_curated_manifest_matches_actual_source_no_heal(self):
  m=json.loads(self.after[c.SKIN+'/Infinity-Protected-Manifest.json'])
  self.assertEqual(len(m['protected_files']),941)
  self.assertFalse(m['candidate_locked'])
  for p,h in m['protected_files'].items():self.assertEqual(c.sha(self.after[c.SKIN+'/'+p]),h,p)
 def test_actual_ui_health_contract_catches_old_ids_and_accepts_retained_audio(self):
  raw=self.after[c.CC+'/common.py'];ns={'Path':Path,'read_json':lambda p,d:json.loads(p.read_text()) if p.exists() else d,
       'DEFAULT_CRITICAL_UI':(),'DEFAULT_REQUIRED_IDS':{}}
  definitions(raw,{'_skin_resolution_dirs','_skin_manifest','_skin_version','_health_contract','_xml_ids','ui_health'},ns)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);ns['_skin_root']=lambda:root
   for name,body in self.after.items():
    if name.startswith(c.SKIN+'/'):
     dest=root/name.split('/',1)[1];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
   self.assertTrue(ns['ui_health']()['healthy'])
   (root/'infinity-skin.json').write_bytes(self.before[c.SKIN+'/infinity-skin.json'])
   old=ns['ui_health']();self.assertFalse(old['healthy'])
   self.assertTrue(any('252,265' in issue for issue in old['issues']))
 def test_actual_native_classifier_retains_all_old_variants(self):
  root=Path(os.environ['INFINITY_2103393_NATIVE']);before=(root/n.CONTRACT).read_bytes()
  after=n.classifier(before,self.before,self.after)
  self.assertTrue(after.startswith(before.split(b'  };\n  return *contracts;')[0]))
  for endpoint in ('default.py','context.py','plugin.py','service.py'):
   self.assertIn(('"'+c.CC+'/'+endpoint+'", "'+c.CC+'",').encode(),after)
  with self.assertRaises(ValueError):n.classifier(after,self.before,self.after)
 def test_execute_actual_native_classifier_rejects_each_modified_pin(self):
  root=Path(os.environ['INFINITY_2103393_NATIVE']);before=(root/n.CONTRACT).read_bytes()
  after=n.classifier(before,self.before,self.after)
  peers=n.module('_infinity94_classifier_peer',c.ROOT/'repairs/2103390-bugfixes/group7/finish92/test_release92.py')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);addons=p/'addons';addons.mkdir()
   pins=json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json'])
   for name in pins:
    dest=addons/c.CC/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(self.after[c.CC+'/'+name])
   peer=type('ActualSourcePeer',(),dict(root=p,before=before,after=after))
   peers.Coherent92.compile_cpp.__func__(peer)
   def classify(endpoint,label='after'):
    return subprocess.check_output([str(p/'cpp'/label),'special://home/addons/'+c.CC+'/'+endpoint,c.CC],env=dict(os.environ,TEST_ADDONS=str(addons)),text=True)
   for endpoint in ('service.py','plugin.py','context.py','default.py'):
    self.assertEqual(classify(endpoint),'command_center' if endpoint=='service.py' else 'command_center_client')
    self.assertEqual(classify(endpoint,'before'),'')
   for name in pins:
    dest=addons/c.CC/name;raw=dest.read_bytes();dest.write_bytes(raw+b'\n')
    for endpoint in ('service.py','plugin.py','context.py','default.py'):self.assertEqual(classify(endpoint),'')
    dest.write_bytes(raw)
 def test_art_matrix_tests_all_sixteen_negative_files(self):
  pins=json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']);self.assertEqual(len(art94.expected(pins)),43)
  source=art94.probe_source('a'*64);self.assertIn('original.size() == 16',source);self.assertIn('PASSED.size() == 43',source)
  _,helper=dex94.java_router(self.before,self.after)
  for p,h in pins.items():self.assertIn(p.encode(),helper);self.assertIn(h.encode(),helper)

if __name__=='__main__':unittest.main()
