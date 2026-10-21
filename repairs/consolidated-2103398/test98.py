import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import components98 as c
import native98 as n

sys.path.insert(0,str(c.HERE/c.LATEST))
import identity
sys.modules['latest_identity']=identity
import home_option_b as ui
from khc_close_attempts import collect

APK=Path(os.environ.get('INFINITY_2103397_APK',str(c.ROOT.parent/'baseline97/Infinity-2103397-Fold-Corrective-EXPERIMENTAL.apk')))
NATIVE=Path(os.environ.get('INFINITY_2103397_NATIVE',str(c.ROOT.parent/'baseline97/source/native')))
ROUTE='plugin://plugin.video.umbrella/?'+urlencode({'action':'play','title':'Real returned title','year':'2026','imdb':'tt123456','tmdb':'456','meta':json.dumps({'plot':'Provider-returned metadata. '*800})})

class Corrective98(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.before=c.read_parent(APK);cls.after=c.components(cls.before)
  cls.native=n.patches({p:(NATIVE/p).read_bytes() for p in n.PATHS},cls.before,cls.after)

 def test_identity_keeps_the_original_long_provider_route(self):
  self.assertGreater(len(ROUTE),4096)
  path=identity.encode(ROUTE,'movie',{'imdb':'tt123456','tmdb':'456'})
  self.assertLess(len(path),4096);self.assertEqual(identity.decode(path)['route'],ROUTE)

 def test_identity_rejects_wrong_provider_ids_and_actions(self):
  for route,kind,ids in [(ROUTE.replace('umbrella','other'),'movie',{'imdb':'tt123456'}),(ROUTE,'movie',{'tmdb':'999'}),(ROUTE.replace('action=play','action=tools_clearCache'),'movie',{'imdb':'tt123456'}),(ROUTE,'tvshow',{'imdb':'tt123456'})]:
   with self.assertRaises(ValueError):identity.encode(route,kind,ids)

 def test_identity_rejects_forgery_and_noncanonical_payload(self):
  p=identity.encode(ROUTE,'movie',{'imdb':'tt123456'})
  for invalid in [p[:-1]+'0',p+'&action=open',p.replace('data=','data=AAAA'),p.replace('infinity.latestreleases','video.other')]:
   with self.assertRaises(ValueError):identity.decode(invalid)

 def test_feed_output_equivalence_is_lossless_and_ordered(self):
  rows=[{'file':ROUTE,'label':'Actual fixture title','title':'Actual fixture title','plot':'Fixture only','year':2026,'uniqueid':{'imdb':'tt123456','tmdb':'456'},'art':{'poster':'https://example.test/fixture.jpg'},'premiered':'2026-01-01'}, {'file':ROUTE.replace('tt123456','tt123457').replace('tmdb=456','tmdb=457'),'label':'Other fixture title','uniqueid':{'imdb':'tt123457','tmdb':'457'}}]
  wrapped=[identity.wrap(r,'movies') for r in rows]
  self.assertTrue(identity.equivalent(rows,wrapped));self.assertFalse(identity.equivalent(rows,list(reversed(wrapped))))
  forged=copy.deepcopy(wrapped);forged[0]['plot']='invented';self.assertFalse(identity.equivalent(rows,forged))

 def test_both_existing_feed_routes_and_provider_implementation_preserved(self):
  self.assertIn('5308818',identity.FEEDS['movies']);self.assertIn('trakttrending_recent',identity.FEEDS['tvshows'])
  default=self.after[c.LATEST+'/default.py'];self.assertIn(b"'Files.GetDirectory'",default);self.assertIn(b'if not equivalent(before, rows)',default)
  self.assertNotIn(b'requests.',default);self.assertNotIn(b'sqlite',default)
  for name in self.before:
   if name.startswith('script.infinity.rails/'):self.assertEqual(self.before[name],self.after[name])

 def test_native_scope_pins_and_no_global_eligibility_waiver(self):
  text=self.native[n.CONTAINER].decode()
  self.assertIn('infinity_source_identity_mismatch',text)
  for leaf in ('default.py','identity.py','addon.xml'):self.assertIn(c.sha(self.after[c.LATEST+'/'+leaf]),text)
  self.assertIn('GetID() != 8101 && GetID() != 8102 && GetID() != 8801 && GetID() != 8802',text)
  self.assertIn('infinityLatest ? 32768U : 4096U',text)
  self.assertIn('infinity_media_identity_mismatch',text)
  self.assertIn('GetSelectedItem() != selected',text)

 def test_actual_controller_fingerprints_match_all_seventeen_sources(self):
  pins=json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']);self.assertEqual(len(pins),17)
  for p,h in pins.items():self.assertEqual(c.sha(self.after[c.CC+'/'+p]),h)
  self.assertEqual(self.after[c.UI+'/CONTROLLER-PREIMAGES.json'],self.after[c.WB+'/CONTROLLER-PREIMAGES.json'])
  _,release,_=n.old_adapters()
  hashes={p:c.sha(b) for p,b in self.after.items()}
  for endpoint in (*release.coherence.ENDPOINTS,'default.py'):
   self.assertEqual(len(release.coherence.matching_variants(self.native[n.CONTRACT].decode(),c.CC,c.CC+'/'+endpoint,hashes)),1)

 def test_fold_geometry_actions_and_expanded_information(self):
  for pw,ph in [(1080,2520),(2184,1968),(2256,1244),(1244,2256),(720,1600)]:
   g=ui.geometry(1080,2400,pw,ph);expanded=ui.geometry(1080,2400,pw,ph,True)
   self.assertGreaterEqual(g['x'],0);self.assertGreaterEqual(g['y'],0)
   self.assertLessEqual(g['x']+g['width'],1080);self.assertLessEqual(g['y']+g['height'],2400)
   self.assertGreater(g['details']['synopsis'][3],80)
   self.assertGreater(expanded['height'],g['height'])
   self.assertEqual(len(g['buttons']),4)
   for x,y,w,h in g['buttons']:self.assertGreater(w,65);self.assertGreater(h,35);self.assertLessEqual(x+w,g['width'])

 def test_popup_close_is_real_icon_actions_complete_more_info_scrollable(self):
  root=ET.fromstring(self.after[c.SKIN+'/unified/InfinityHomeOptionB.xml'])
  self.assertEqual(root.find('.//control[@id="113"]/texture').text,'infinity_ui/icons/close.png')
  self.assertEqual([root.find('.//control[@id="%d"]/label'%i).text for i in (101,102,103,104)],['Play','Trailer','Favorite','More Info'])
  self.assertEqual(root.find('.//control[@id="126"]').get('type'),'textbox')
  code=self.after[c.UI+'/home_option_b.py'];self.assertIn(b'details.doModal()',code);self.assertNotIn(b"executebuiltin('Action(Info)')",code)
  self.assertIn(b"synopsis=info('Plot',65536)",code)

 def test_favorite_uses_existing_kodi_toggle_and_trailer_unavailable_is_explicit(self):
  s=ui.Selection(8101,0,'movies',ROUTE,'Fixture title')
  calls=[];fake=types.SimpleNamespace(executebuiltin=lambda x:calls.append(x), executeJSONRPC=lambda raw:(calls.append(json.loads(raw)) or '{"result":"OK"}'))
  gui=types.SimpleNamespace(Dialog=lambda:types.SimpleNamespace(ok=lambda *args:calls.append(args)))
  old=ui.capture;ui.capture=lambda *args:s
  try:
   self.assertTrue(ui._perform(fake,gui,s,'favorite'));self.assertTrue(ui._perform(fake,gui,s,'favorite'))
   self.assertEqual([x['method'] for x in calls],['Favourites.AddFavourite']*2)
   self.assertTrue(ui._perform(fake,gui,s,'trailer'));self.assertIn('No trailer is available',calls[-1][1])
  finally:ui.capture=old

 def test_ambient_layer_draws_above_opaque_home_and_never_over_video(self):
  root=ET.fromstring(self.after[c.SKIN+'/unified/Home.xml']);controls=list(root.find('controls'))
  owner=next(i for i,n in enumerate(controls) if n.get('id')=='40001')
  ambient=next(i for i,n in enumerate(controls) if n.get('content')=='InfinityExperienceBackdrop')
  self.assertGreater(ambient,owner)
  exp=self.after[c.SKIN+'/unified/Includes_InfinityExperience.xml']
  self.assertIn(b'!Player.HasMedia',exp);self.assertIn(b'40FFFFFF',exp);self.assertIn(b'20FFFFFF',exp)
  self.assertEqual(self.after[c.SKIN+'/resources/lib/infinity_native_ambient.py'],self.before[c.SKIN+'/resources/lib/infinity_native_ambient.py'])

 def test_oled_and_original_light_dark_values_retained(self):
  for n,b in self.before.items():
   if n.startswith(c.SKIN+'/') and n.endswith('.xml') and b'<variable ' in b:
    self.assertEqual(b,self.after[n],n)

 def test_browser_only_touch_excludes_search_and_uses_original_context_actions(self):
  text=self.native[n.CONTAINER].decode();part=text[text.index('bool CGUIBaseContainer::OnInfinityAddonBrowserTouch'):text.index('bool CGUIBaseContainer::OnInfinityUiTouch')]
  self.assertIn('addons://search',part);self.assertIn('WINDOW_DIALOG_FILE_BROWSER',part)
  self.assertIn('OnClick(ACTION_CONTEXT_MENU)',part);self.assertIn('OnClick(ACTION_SELECT_ITEM)',part)
  self.assertNotIn('DisableAddon',part);self.assertNotIn('InstallAddon',part)
  self.assertIn('ACTION_TOUCH_TAP',self.native[n.INPUT].decode())

 def test_each_native_close_attempt_has_distinct_terminal_receipt(self):
  raw=self.native[n.COORDINATOR].decode()
  self.assertIn('directory + "/attempt-" + key + ".json"',raw)
  self.assertIn('lock.unlock();',raw);self.assertIn('SaveProtocolRecord(',raw)
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for session,phase in [('failed-one','CHECKPOINT_FAILED'),('passed-two','SAFE_TO_TERMINATE')]:
    (root/('attempt-'+session+'-'+phase+'.json')).write_text(json.dumps({'session':session,'pid':123,'phase':phase,'owners':[],'essential_writes_durable':phase=='SAFE_TO_TERMINATE'}))
   report=collect(root);self.assertEqual(len(report['attempts']),2)
   self.assertEqual({r['checkpoint'] for r in report['attempts']},{'FAILED','NATIVE_SAFE_RECEIPT'})
   self.assertTrue(all(r['engine_termination'].startswith('NEEDS_') for r in report['attempts']))

 def test_actual_sqlite_baseline_reproduction_and_corrected_durability(self):
  include=Path(os.environ.get('INFINITY_SQLITE_INCLUDE',str(c.ROOT.parent/'native-host-deps')))
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);patched=root/'patched'
   for name,body in self.native.items():p=patched/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
   for mode,overlay in [('baseline',NATIVE),('fixed',patched)]:
    exe=root/mode;db=root/(mode+'-data');db.mkdir()
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-I'+str(include),'-I'+str(overlay/'xbmc'),'-I'+str(NATIVE/'xbmc'),str(c.HERE/'sqlite_inventory_test.cpp'),'-l:libsqlite3.so.0','-o',str(exe)],check=True)
    result=subprocess.run([str(exe),str(db),mode],check=True,capture_output=True,text=True)
    self.assertIn('SQLITE_READONLY=8' if mode=='baseline' else 'protected reopen exact',result.stdout)

if __name__=='__main__':unittest.main()
