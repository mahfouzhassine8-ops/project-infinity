"""Selected host checks only: no Kodi launch, provider requests or user data."""
import ast,hashlib,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2]
SKIN=ROOT/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz'
CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter'
BASE=Path('/dev/shm/infinity2103460-reference/assets/addons')
RESULTS=[]
def xml(name):return E.parse(SKIN/'unified'/name).getroot()
def node(name,id):return xml(name).find('.//control[@id="'+id+'"]')
def baseline(name):return E.parse(BASE/'skin.infinity.diggz/unified'/name).getroot()
def loadhelper():
 spec=importlib.util.spec_from_file_location('nine_library_navigation',CC/'library_navigation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Selected(unittest.TestCase):
 def test_signed_baseline_matches_source_parent(self):
  for name in ('Custom_1198_InfinityNav.xml','DialogVideoInfo.xml','Includes_InfinityMediaLists.xml','Variables.xml'):
   p=SKIN/'unified'/name;old=subprocess.check_output(['git','show','f25dbcb6:'+str(p.relative_to(ROOT))],cwd=ROOT);self.assertEqual(old,(BASE/'skin.infinity.diggz/unified'/name).read_bytes())
  for name in ('default.py','library_navigation.py'):
   p=CC/name;old=subprocess.check_output(['git','show','f25dbcb6:'+str(p.relative_to(ROOT))],cwd=ROOT);self.assertEqual(old,(BASE/'script.infinity.commandcenter'/name).read_bytes())
 def test_power_final(self):
  group=xml('Custom_1198_InfinityNav.xml').find('.//control[@id="1198899"]');ids=[c.get('id') for c in group.findall('.//control') if c.find('onclick') is not None];self.assertEqual(ids[-1],'1198304');self.assertEqual(ids.count('1198304'),1)
 def test_drawer_actions_and_sizes_preserved(self):
  old=baseline('Custom_1198_InfinityNav.xml');new=xml('Custom_1198_InfinityNav.xml')
  for c in old.findall('.//control[@id]'):
   n=new.find('.//control[@id="'+c.get('id')+'"]');self.assertIsNotNone(n)
   for t in ('width','height','onclick'):self.assertEqual([E.tostring(x) for x in c.findall(t)],[E.tostring(x) for x in n.findall(t)])
 def test_shortcuts_use_actual_home_targets(self):
  m=loadhelper();calls=[];xb=types.SimpleNamespace(executeJSONRPC=lambda raw:(calls.append(json.loads(raw)) or '{"result":"OK"}'));gui=types.SimpleNamespace(Dialog=lambda:None)
  home=(BASE/'skin.infinity.diggz/unified/Home.xml').read_text()
  for action,route in [('library-movies','movies'),('library-tv','tv')]:
   self.assertTrue(m.run(action,xb,gui));path='plugin://script.infinity.commandcenter/?action='+route;self.assertIn(path,home);self.assertEqual(calls[-1]['params'],{'window':'videos','parameters':[path,'return']})
 def test_native_touch_unchanged(self):
  changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True);self.assertNotIn('InputManager.cpp',changed);self.assertNotIn('GUIBaseContainer.cpp',changed)
 def test_guide_has_no_controls_or_decorations(self):
  inc=xml('Includes_InfinityMediaLists.xml').find('./include[@name="InfinityMedia_TouchGuide"]');self.assertEqual(inc.findall('.//control'),[]);self.assertNotIn('Tap = Select',E.tostring(inc,encoding='unicode'))
 def test_cast_custom_control_avoids_native_toggle(self):
  r=xml('DialogVideoInfo.xml');self.assertIsNone(r.find('.//control[@id="5"]'));self.assertIsNotNone(r.find('.//control[@id="9013"]'));self.assertIsNotNone(r.find('.//control[@id="50"]'))
 def test_cast_actual_thumbnail(self):
  c=node('DialogVideoInfo.xml','50');textures=c.findall('.//texture');self.assertEqual(sum(x.text=='$INFO[ListItem.Thumb]' for x in textures),2);self.assertFalse(any('InfinityPolishIcon0' in (x.text or '') for x in textures))
 def test_play_and_back_preserved(self):
  old=baseline('DialogVideoInfo.xml');new=xml('DialogVideoInfo.xml')
  for id in ('8','9011'):
   a=old.find('.//control[@id="'+id+'"]');b=new.find('.//control[@id="'+id+'"]')
   self.assertEqual(a.get('type'),b.get('type'))
   for tag in ('label','onclick','enable','visible','onup','ondown','onleft','onright','altclick','usealttexture'):
    self.assertEqual([E.tostring(x) for x in a.findall(tag)],[E.tostring(x) for x in b.findall(tag)])
 def test_more_fallback_enabled(self):
  c=node('DialogVideoInfo.xml','106');self.assertIn('System.AddonIsEnabled(script.infinity.commandcenter)',c.findtext('enable'));self.assertTrue(any('media-details' in (a.text or '') and '!System.AddonIsEnabled(script.extendedinfo)'==a.get('condition') for a in c.findall('onclick')))
 def test_trailer_existing_bridge_and_native_fallback(self):
  c=node('DialogVideoInfo.xml','9012');actions=[a.text for a in c.findall('onclick')];self.assertIn('PlayerControl(Stop)',actions);self.assertTrue(any(a.startswith('RunScript(script.trailer.bridge') for a in actions));self.assertIn('PlayMedia($ESCINFO[ListItem.Trailer])',actions)
 def test_metadata_empty_and_available(self):
  tree=ast.parse((CC/'default.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_media_details_fallback');module=ast.Module(body=[f],type_ignores=[]);out=[];labels={'ListItem.Title':'Movie','ListItem.Plot':'A real plot'};env={'xbmc':types.SimpleNamespace(getInfoLabel=lambda key:labels.get(key,'')),'xbmcgui':types.SimpleNamespace(Dialog=lambda:types.SimpleNamespace(textviewer=lambda *a:out.append(a)))};exec(compile(module,'actual_default_function','exec'),env);env['_media_details_fallback']();self.assertIn('A real plot',out[-1][1]);labels.clear();env['_media_details_fallback']();self.assertEqual(out[-1][1],'No additional metadata is available for this item.')
 def test_parse_and_unique_dialog_ids(self):
  for p in (CC/'default.py',CC/'library_navigation.py'):ast.parse(p.read_text())
  for p in ('DialogVideoInfo.xml','Custom_1198_InfinityNav.xml','Includes_InfinityMediaLists.xml','Variables.xml'):xml(p)
  ids=[c.get('id') for c in xml('DialogVideoInfo.xml').findall('.//control[@id]')];self.assertEqual(len(ids),len(set(ids)))
 def test_no_search_or_native_guess(self):
  changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True);self.assertNotIn('infinity_search.py',changed);self.assertNotIn('GUIWindowVideoNav.cpp',changed)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Selected);r=unittest.TextTestRunner(verbosity=2).run(suite);Path(__file__).with_name('FOCUSED-RESULT.json').write_text(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'Android':'NOT_RUN','physical_Fold':'PENDING','scope':'selected host navigation/XML/control/source cases only'},indent=2)+'\n');sys.exit(not r.wasSuccessful())
