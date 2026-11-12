"""Selected Cast clock/identity tests; no Kodi, profile, network or Android PASS."""
from pathlib import Path
import importlib.util,json,multiprocessing,os,socket,threading,time,types,unittest,uuid
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cast_runtime',HERE/'overlay/script.infinity.commandcenter/cast_runtime.py')
cast=importlib.util.module_from_spec(spec);spec.loader.exec_module(cast)
class CastClock(unittest.TestCase):
 def setUp(self):
  self.token=uuid.uuid4().hex;self.occurrence=uuid.uuid4().hex
  self.name='infinity-cast-'+str(os.getpid())+'-'+self.token
  self.expected=dict(session=self.token,file_sha256=cast.digest('https://media.invalid/public.mp4'),origin_sha256=cast.digest(''))
  self.value=dict(schema=1,controller='InfinityCastV1',pid=os.getpid(),at_ms=time.monotonic()*1000,
   **self.expected,occurrence=self.occurrence,connected=True,owned=True,media_matches=True,
   ever_played=True,completed=False,position=258.,duration=7200.)
  self.props={'Infinity.Cast.Channel':self.name}
  home=types.SimpleNamespace(getProperty=lambda n:self.props.get(n,''),setProperty=lambda n,v:self.props.__setitem__(n,v),
                            clearProperty=lambda n:self.props.pop(n,None))
  self.xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz')
  self.gui=types.SimpleNamespace(Window=lambda n:home)
  self.player=types.SimpleNamespace(cw_occurrence=self.occurrence,isPlayingVideo=lambda:True,
   getPlayingFile=lambda:'https://media.invalid/public.mp4',
   getPlayingItem=lambda:types.SimpleNamespace(getProperty=lambda n:''))
 def test_valid_same_actual_item_clock(self):
  clock=cast.Clock(self.xbmc,self.gui)
  with patch.object(cast,'_read',return_value=self.value):self.assertEqual(258.,clock.sample(self.player)['position'])
  self.assertEqual('true',self.props['Infinity.Cast.Connected'])
 def test_never_played_receiver_does_not_create_progress(self):
  self.value['ever_played']=False
  with patch.object(cast,'_read',return_value=self.value):self.assertEqual({'hold':True},cast.Clock(self.xbmc,self.gui).sample(self.player))
 def test_wrong_owner_session_source_occurrence_staleness_and_types_are_rejected(self):
  for field,wrong in [('pid',os.getpid()+1),('session',uuid.uuid4().hex),('file_sha256','0'*64),
    ('origin_sha256','0'*64),('occurrence',uuid.uuid4().hex),('at_ms',time.monotonic()*1000-3000),
    ('position',float('nan')),('duration',float('inf')),('owned',1)]:
   value=dict(self.value,**{field:wrong})
   with self.assertRaises(ValueError):cast.validate(value,self.expected,self.occurrence,time.monotonic()*1000)
 def test_completed_requires_actual_playback(self):
  with self.assertRaises(ValueError):cast.validate(dict(self.value,completed=True,ever_played=False),self.expected,self.occurrence,time.monotonic()*1000)
 def test_lost_channel_holds_old_phone_clock_but_replay_cannot_reuse_it(self):
  clock=cast.Clock(self.xbmc,self.gui)
  with patch.object(cast,'_read',return_value=self.value):clock.sample(self.player)
  clock.next_poll=0
  with patch.object(cast,'_read',side_effect=TimeoutError()):self.assertEqual({'hold':True},clock.sample(self.player))
  self.player.cw_occurrence=uuid.uuid4().hex
  with patch.object(cast,'_read',side_effect=ValueError()):self.assertIsNone(clock.sample(self.player))
 def test_home_property_reload_preserves_clock_and_explicit_release_restores_phone_clock(self):
  clock=cast.Clock(self.xbmc,self.gui)
  with patch.object(cast,'_read',return_value=self.value):clock.sample(self.player)
  self.props.clear();clock.next_poll=0
  with patch.object(cast,'_read',return_value=self.value):self.assertEqual(258.,clock.sample(self.player)['position'])
  cast.register(self.name,True,self.xbmc,self.gui)
  self.assertIsNone(clock.sample(self.player));self.assertFalse(clock.owned)
 def test_optional_window_failure_cannot_escape_into_existing_service(self):
  clock=cast.Clock(self.xbmc,self.gui);clock.owned=True
  self.gui.Window=lambda n:(_ for _ in ()).throw(RuntimeError('Window id does not exist'))
  self.assertEqual({'hold':True},clock.sample(self.player))
 def test_source_change_during_read_is_not_used(self):
  names=iter(['https://media.invalid/public.mp4','https://media.invalid/another.mp4'])
  self.player.getPlayingFile=lambda:next(names)
  with patch.object(cast,'_read',return_value=self.value):self.assertIsNone(cast.Clock(self.xbmc,self.gui).sample(self.player))
 def test_non_cast_and_non_infinity_are_inert(self):
  self.props.clear()
  with patch.object(cast,'_read',side_effect=AssertionError('must not connect')):self.assertIsNone(cast.Clock(self.xbmc,self.gui).sample(self.player))
  self.props['Infinity.Cast.Channel']=self.name;self.xbmc.getSkinDir=lambda:'skin.cobra'
  with patch.object(cast,'_read',side_effect=AssertionError('must not connect')):self.assertIsNone(cast.Clock(self.xbmc,self.gui).sample(self.player))
 def test_registration_has_no_other_commands_and_old_clear_cannot_remove_new_session(self):
  self.assertFalse(cast.register('arbitrary-socket',False,self.xbmc,self.gui))
  self.assertTrue(cast.register(self.name,False,self.xbmc,self.gui))
  other='infinity-cast-'+str(os.getpid())+'-'+uuid.uuid4().hex
  cast.register(other,False,self.xbmc,self.gui);cast.register(self.name,True,self.xbmc,self.gui)
  self.assertEqual(other,self.props['Infinity.Cast.Channel'])
 def test_real_same_process_socket_is_bounded_and_acknowledges_only_hashes(self):
  listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind('\0'+self.name);listener.listen(1)
  received=[]
  def serve():
   with listener:
    client,_=listener.accept()
    with client:
     client.settimeout(1);client.sendall((json.dumps(self.value)+'\n').encode());received.append(client.recv(513))
  worker=threading.Thread(target=serve,daemon=True);worker.start()
  value=cast._read(self.name,self.expected,self.occurrence)
  worker.join(1);self.assertFalse(worker.is_alive());self.assertEqual(258.,value['position'])
  ack=json.loads(received[0]);self.assertEqual({'session','file_sha256','origin_sha256','occurrence'},set(ack))
  self.assertNotIn(b'http',received[0])
 def test_same_uid_other_process_cannot_supply_clock(self):
  ready,parent=multiprocessing.Pipe(duplex=False)
  def serve():
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as listener:
    listener.bind('\0'+self.name);listener.listen(1);parent.send(True)
    client,_=listener.accept()
    with client:
     try:client.sendall((json.dumps(self.value)+'\n').encode())
     except OSError:pass
  worker=multiprocessing.Process(target=serve);worker.start()
  try:
   self.assertTrue(ready.poll(2));ready.recv()
   with self.assertRaisesRegex(ValueError,'peer owner mismatch'):cast._read(self.name,self.expected,self.occurrence)
   worker.join(2);self.assertFalse(worker.is_alive())
  finally:
   if worker.is_alive():worker.terminate();worker.join(1)
   ready.close();parent.close()
if __name__=='__main__':unittest.main()
