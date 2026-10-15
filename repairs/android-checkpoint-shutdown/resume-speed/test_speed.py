"""Exercise actual Resume Hub scripts, cached views and rendering with Kodi API doubles."""
import argparse,copy,json,os,runpy,sys,threading,time,unittest
from pathlib import Path
from unittest import mock
p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);args=p.parse_args()
sys.argv=[sys.argv[0],'--runtime',args.runtime]
f=runpy.run_path(str(Path(__file__).parents[1]/'runtime-tests/test_runtime_checkpoint.py'),run_name='speed_fixtures')
hub,service,plugin,common,runtime=[f[x] for x in ('hub','service','plugin','common','runtime')]
Window,KEY=f['Window'],f['KEY']
class Item:
 def __init__(self,**kwargs):self.info={};self.props={};self.art={};self.kwargs=kwargs
 def setInfo(self,kind,info):self.info=info
 def setProperty(self,k,v):self.props[k]=v
 def setUniqueIDs(self,ids):self.ids=ids
 def setArt(self,art):self.art=art
 def addContextMenuItems(self,menu):self.menu=menu
class SpeedTests(f['RuntimeTests']):
 def setUp(self):
  super().setUp();hub._view_cache=None
 def seed(self):
  entry=dict(self.player.cw_item,position=417.125,duration=900,percentage=46.35)
  return hub.save(self.profile,dict(items={KEY:entry},revision=0))
 def test_idle_poll_avoids_gate_without_skipping_real_queue(self):
  self.seed()
  with mock.patch.object(hub,'load',wraps=hub.load) as reads:
   for _ in range(100):self.assertTrue(hub.poll_kodi_sync(self.profile))
   self.assertEqual(reads.call_count,1)
  data=hub.load(self.profile);hub.queue_kodi_sync(data,self.player.cw_item,True);hub.save(self.profile,data)
  with mock.patch.object(hub,'flush_kodi_sync',wraps=hub.flush_kodi_sync) as flush:
   self.assertTrue(hub.poll_kodi_sync(self.profile));self.assertEqual(flush.call_count,1)
  self.assertFalse(hub.load(self.profile)['pending_kodi_sync'])
 def test_failed_queued_rpc_remains_durable(self):
  self.seed();hub.load_view(self.profile)
  data=hub.load(self.profile);hub.queue_kodi_sync(data,self.player.cw_item,True);hub.save(self.profile,data)
  with mock.patch.object(hub,'sync_kodi_playcount',return_value=False):
   self.assertFalse(hub.poll_kodi_sync(self.profile))
  self.assertTrue(hub.load(self.profile)['pending_kodi_sync'])
 def test_private_copy_and_profile_separation(self):
  self.seed();a=hub.load_view(self.profile);a['items'][KEY]['position']=0
  self.assertEqual(hub.load_view(self.profile)['items'][KEY]['position'],417.125)
  other=self.profile/'other';other.mkdir()
  self.assertFalse(hub.load_view(other)['items'])
  self.assertEqual(hub.load_view(self.profile)['items'][KEY]['position'],417.125)
 def test_external_participant_update_invalidates_view(self):
  self.seed();hub.load_view(self.profile)
  # Independent participant object models a separate plugin interpreter.
  peer=f['runtime'].PersistenceParticipant(self.profile,f['runtime'].EngineOwner(os.getpid(),f['OWNER']))
  peer.bind_engine()
  def edit(data):data['items'][KEY]['position']=500.125;return data
  peer.update(hub.CONTINUE_FILE,{},edit)
  self.assertEqual(hub.load_view(self.profile)['items'][KEY]['position'],500.125)
 def test_same_size_atomic_replace_bypass_still_fails_verification(self):
  self.seed();hub.load_view(self.profile);p=self.profile/hub.CONTINUE_FILE
  before=p.stat();raw=p.read_bytes();other=p.with_suffix('.replacement')
  other.write_bytes(raw.replace(b'417.125',b'418.125'));os.utime(other,ns=(before.st_atime_ns,before.st_mtime_ns));other.replace(p)
  with self.assertRaises(f['runtime'].PersistenceError):hub.load_view(self.profile)
 def test_journal_owner_change_invalidates_view(self):
  self.seed();hub.load_view(self.profile);p=self.control/'participant.json';value=json.loads(p.read_text());value['owner']['token']='foreign-owner-token-123456';p.write_text(json.dumps(value))
  with self.assertRaises(f['runtime'].PersistenceError):hub.load_view(self.profile)
 def test_signature_race_is_not_cached(self):
  self.seed();hub.load_view(self.profile);hub._view_cache=None
  with mock.patch.object(hub,'_view_signature',side_effect=[('before',),('after',)]):hub.load_view(self.profile)
  self.assertIsNone(hub._view_cache)
 def test_no_display_lock_held_when_waiting_for_writer_gate(self):
  self.seed();entered=threading.Event();completed=threading.Event();errors=[]
  store=runtime.store_for(self.profile)
  original=hub.load
  def slow(profile):entered.set();return original(profile)
  def view():
   try:hub.load_view(self.profile)
   except Exception as e:errors.append(e)
   completed.set()
  with store.transaction():
   with mock.patch.object(hub,'load',side_effect=slow):
    t=threading.Thread(target=view,daemon=True);t.start();self.assertTrue(entered.wait(1))
    self.seed()  # save() must acquire the display lock while already holding the writer gate.
  self.assertTrue(completed.wait(2));t.join(1);self.assertFalse(errors)
 def test_startup_publishes_before_maintenance_and_after_skin_reload(self):
  self.seed();events=[]
  def skin():
   self.assertEqual(Window.properties['Infinity.ContinueWatchingMovies'],'1');events.append('skin');Window.properties.clear();return 'unchanged'
  def guardian(profile):events.append('guardian')
  with mock.patch.object(service.skin_upgrade,'apply_and_reload',side_effect=skin),mock.patch.object(service,'scan_guardian',side_effect=guardian),mock.patch.object(service,'publish_refresh_state'),mock.patch.object(service,'publish_runtime_capabilities'),mock.patch.object(service,'StabilityController'),mock.patch.object(service,'InfinityPlayer'),mock.patch.object(service,'ExperienceController'),mock.patch.object(service,'NormalReturnController'),mock.patch.object(service,'DisplayReflowController'),mock.patch.object(service,'ResidentCheckpoint'),mock.patch.object(service,'CheckpointMonitor') as monitor:
   monitor.return_value.abortRequested.return_value=True
   service.main()
  self.assertEqual(events,['skin','guardian']);self.assertEqual(Window.properties['Infinity.ContinueWatchingMovies'],'1')
 def test_rendering_reuses_checks_and_preserves_visible_state(self):
  data=self.seed();entry=data['items'][KEY];entry['poster']='poster';entry['fanart']='fanart';entry['stable_source']='plugin://plugin.video.umbrella/?action=play'
  data['watched']={KEY:dict(entry)};checks=[];settings=[];arts=[];captured=[]
  def exists(q):checks.append(q);return True
  def setting(k,default):settings.append(k);return True
  def art(url,tier,fanart=False):arts.append((url,tier,fanart));return url
  with mock.patch.object(plugin.hub,'load_view',return_value=data),mock.patch.object(plugin,'_values_for',return_value=[entry]*100),mock.patch.object(plugin.xbmc,'getCondVisibility',side_effect=exists),mock.patch.object(plugin,'setting_bool',side_effect=setting),mock.patch.object(plugin,'artwork',side_effect=art),mock.patch.object(plugin.xbmcgui,'ListItem',Item,create=True),mock.patch.object(plugin.xbmcplugin,'setContent',create=True),mock.patch.object(plugin.xbmcplugin,'addDirectoryItem',side_effect=lambda h,t,li,**k:captured.append((t,li)),create=True):
   plugin.listing()
  self.assertEqual(len(checks),1);self.assertEqual(len(settings),1);self.assertEqual(len(arts),200)
  self.assertEqual(len(captured),100)
  for target,li in captured:
   self.assertTrue(target.startswith('plugin://plugin.video.umbrella/'));self.assertEqual(li.info['playcount'],1);self.assertEqual(li.props['ResumeTime'],'417.125');self.assertEqual(li.art['poster'],li.art['thumb'])
 def test_render_provider_check_cache_is_per_listing(self):
  entry=dict(self.player.cw_item,stable_source='plugin://plugin.video.umbrella/?action=play',tmdb='123',updated=0)
  with mock.patch.object(plugin.xbmc,'getCondVisibility',return_value=True):
   render=dict(source_memory=True,tier='standard',installed={});self.assertIn('umbrella',plugin._target(entry,{},render))
  with mock.patch.object(plugin.xbmc,'getCondVisibility',return_value=False):
   render=dict(source_memory=True,tier='standard',installed={});self.assertEqual(plugin._target(entry,{},render),'')
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(SpeedTests)
 result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(0 if result.wasSuccessful() else 1)
