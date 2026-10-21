import ast,copy,hashlib,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import nullcontext
import components95 as c,native95 as n
import xml.etree.ElementTree as ET

def funcs(raw,names,ns):
 tree=ast.parse(raw);exec(compile(ast.Module(body=[v for v in tree.body if isinstance(v,(ast.FunctionDef,ast.ClassDef)) and v.name in names],type_ignores=[]),'actual_candidate.py','exec'),ns);return ns
class Corrective(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.apk=Path(os.environ.get('INFINITY_2103394_APK',c.ROOT.parent/'delivery-2103394/files/Infinity-2103394-Fold-Corrective-EXPERIMENTAL.apk'))
  cls.before=c.read_parent(cls.apk);cls.after=c.components(cls.before)
 def test_release_scope(self):
  delta=c.ledger(self.before,self.after);self.assertFalse(delta['removed']);self.assertFalse(any('cobra' in n.lower() for n in delta['changed']))
  for aid,old,new in c.PACKAGES:self.assertEqual(ET.fromstring(self.after[aid+'/addon.xml']).get('version'),new)
  for name,body in self.before.items():
   if name.startswith('script.infinity.rails/') or name in {c.CC+'/'+n for n in ('persistence_participant.py','checkpoint_runtime.py','service.py','experience.py','resume_hub.py','infinity_trakt.py')}:self.assertEqual(body,self.after[name],name)
 def test_four_controls_and_identity_rejection(self):
  mod=types.ModuleType('option95');sys.modules[mod.__name__]=mod;exec(compile(self.after[c.UI+'/home_option_b.py'],'home_option_b.py','exec'),mod.__dict__)
  self.assertEqual(set(mod.CONTROLS),{8101,8102,8801,8802})
  for control in (8101,8102,8801,8802):
   path='plugin://plugin.video.umbrella/?action=play&id=123';label='Observed movie';proof=hashlib.sha256(f'{control}\n1\n{path}\n{label}'.encode()).hexdigest();fields=dict(Control=str(control),Index='1',Path=path,Label=label,Proof=proof)
   gui=types.SimpleNamespace(Window=lambda _:types.SimpleNamespace(getProperty=lambda k:fields.get(k.removeprefix('Infinity.HomeOptionB.Pending'),'')))
   self.assertIsNotNone(mod.read_native_hold(gui,(str(control),'1',proof)))
   self.assertIsNone(mod.read_native_hold(gui,(str(control),'2',proof)))
   fields['Path']+='&tampered=1';self.assertIsNone(mod.read_native_hold(gui,(str(control),'1',proof)))
  for cid in (8601,8602,8701,8702):self.assertIsNone(mod.read_native_hold(gui,(str(cid),'1',proof)))
  self.assertEqual(mod.APPROVED_ORDER,('Play','Trailer','Favorite','More Info'))
 def test_fresh_settings_readback(self):
  disk={'ambient_home':'subtle','motion_mode':'full'};properties={};notices=[]
  class Addon:
   def __init__(self,aid):self.snapshot=dict(disk)
   def getSetting(self,key):return self.snapshot[key]
  ns={'xbmcaddon':types.SimpleNamespace(Addon=Addon),'xbmcgui':types.SimpleNamespace(Window=lambda _:types.SimpleNamespace(setProperty=properties.__setitem__),Dialog=lambda:types.SimpleNamespace(ok=lambda *a:notices.append(a))), 'xbmc':types.SimpleNamespace(executebuiltin=lambda *a:None),'choose':lambda *a:2,'addon_set_setting':lambda aid,k,v:disk.update({k:v}) or True}
  funcs(self.after[c.CC+'/infinity_settings.py'],{'setting_choice'},ns)
  stale=Addon(c.CC);ns['setting_choice']('Ambient',c.CC,'ambient_home',('off','subtle','immersive'),('Off','Subtle','Immersive'),'subtle')
  self.assertEqual(stale.getSetting('ambient_home'),'subtle');self.assertEqual(disk['ambient_home'],'immersive');self.assertEqual(properties['Infinity.AmbientHome.Mode'],'immersive');self.assertFalse(notices)
  ns['addon_set_setting']=lambda *a:False;properties.clear();ns['setting_choice']('Ambient',c.CC,'ambient_home',('off','subtle','immersive'),('Off','Subtle','Immersive'),'subtle');self.assertFalse(properties);self.assertEqual(len(notices),1)
 def test_real_copy2_audit_events_removed_and_bytes_durable(self):
  import shutil
  events=[];sys.addaudithook(lambda event,args:events.append(event) if event in ('os.utime','os.chmod','os.setxattr') else None)
  ns={'Path':Path,'tempfile':tempfile,'hashlib':hashlib,'os':os};funcs(self.after[c.CC+'/common.py'],{'_copy_verified_bytes'},ns)
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);src=root/'source';dst=root/'target';src.write_bytes(b'protected UI bytes\x00'*100)
   shutil.copy2(src,dst);self.assertIn('os.utime',events);self.assertIn('os.chmod',events);events.clear()
   ns['_copy_verified_bytes'](src,dst);self.assertEqual(src.read_bytes(),dst.read_bytes());self.assertFalse(events)
   src.unlink();src.symlink_to(dst)
   with self.assertRaises(RuntimeError):ns['_copy_verified_bytes'](src,dst)
 def test_only_two_compact_geometry_fields_change(self):
  total=0
  for name,body in self.before.items():
   if not name.startswith(c.SKIN+'/') or not name.endswith('/Home.xml'):continue
   if name!=c.SKIN+'/unified/Home.xml':
    self.assertEqual(body,self.after[name]);continue
   old=ET.fromstring(body);new=ET.fromstring(self.after[name]);a=list(old.iter());b=list(new.iter());self.assertEqual(len(a),len(b))
   changed=[(x.tag,x.text,y.text) for x,y in zip(a,b) if x.text!=y.text];self.assertEqual(len(changed),3,name)
   self.assertEqual([x[0] for x in changed].count('left'),1);self.assertEqual([x[0] for x in changed].count('top'),2);total+=1
  self.assertEqual(total,1)
 def test_all_source_pins_include_settings_and_reject_mixing(self):
  pins=json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']);self.assertEqual(len(pins),17);self.assertIn('resources/settings.xml',pins)
  self.assertEqual(pins,json.loads(self.after[c.WB+'/CONTROLLER-PREIMAGES.json']))
  for name,pin in pins.items():self.assertEqual(pin,c.sha(self.after[c.CC+'/'+name]))
  self.assertNotEqual(pins['common.py'],c.sha(self.before[c.CC+'/common.py']))
 def test_native_scope_and_additive_complete_contracts(self):
  root=Path(os.environ.get('INFINITY_2103394_NATIVE',c.ROOT.parent/'protected-2103394/native'))
  source={name:(root/name).read_bytes() for name in n.PATHS};after=n.patches(source,self.before,self.after)
  self.assertEqual({p for p in source if source[p]!=after[p]},n.PATHS)
  block=after[n.CONTAINER].split(b'bool CGUIBaseContainer::OnInfinityOptionBLongPress(')[1].split(b'bool CGUIBaseContainer::OnInfinityRailLongPress(')[0]
  for cid in (8101,8102,8801,8802):self.assertIn(str(cid).encode(),block)
  for cid in (8601,8602,8701,8702):self.assertNotIn(str(cid).encode(),block)
  for source_path in (n.CONTAINER,n.INPUT):
   for line in after[source_path].splitlines():
    if b'CLog::Log' in line and b'[InfinityTouch]' in line:
     self.assertNotIn(bytes((92,92,34)),line,'double escaping invalidates C++ literal')
     self.assertIn(bytes((92,34)),line,'JSON quotes must remain C++ escaped')
  self.assertIn(b'InfinityScriptPersistence::Fail(context->id,"unclassified_native_persistence_operation",event)',after[n.AUDIT])
  _,r,_=n.old_adapters();hashes={k:c.sha(v) for k,v in self.after.items()}
  for endpoint in (*r.coherence.ENDPOINTS,'default.py'):
   variants=r.coherence.matching_variants(after[n.CONTRACT].decode(),c.CC,c.CC+'/'+endpoint,hashes);self.assertEqual(len(variants),1);self.assertEqual(len(variants[0]['pins']),17)
if __name__=='__main__':unittest.main()
