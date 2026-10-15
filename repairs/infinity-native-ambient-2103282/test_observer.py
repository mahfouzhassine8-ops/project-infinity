"""Real Python observer + real native kernel; simulated Kodi presentation APIs.
These tests cannot certify Android Kodi's image loader or physical Fold output.
"""
import ast,ctypes,importlib.util,io,json,os,sys,tempfile,types,unittest
from pathlib import Path
from PIL import Image

HERE=Path(__file__).parent

class Harness:
    def __init__(self,steps=18,change=lambda h:None):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.tick=0;self.steps=steps;self.change=change;self.events=[];self.images=[]
        self.props={'Infinity.AmbientHome.Mode':'immersive','Infinity.NativeAmbient.Profile':'test','Infinity.SystemTheme':'oled'}
        self.paused=False;self.buffering=False;self.has_video=True;self.window=10000;self.title='movie-a'
        self.frames=0;self.captures=0;self.released=0;self.players=0;self.fail=False;self.blue=True;self.format='BGRA'
        self.lib=ctypes.CDLL(str(Path(os.environ.get('AMBIENT_HOST_LIB','engine/libinfinityambient-host.so')).resolve()))
        self.lib.infinity_ambient_set_active(1)
        recipes={'test':[{'overlay':40001,'parents':[],'probes':[40000],'radius':10}]}
        self.recipe=self.root/'recipe.json';self.recipe.write_text(json.dumps(recipes))
        h=self
        class Control:
            def __init__(s,cid):s.cid=cid
            def getWidth(s):return 1920 if s.cid==39799 else 400
            def getHeight(s):return 1080 if s.cid==39799 else 200
            def getPosition(s):return (0,100)
            def setImage(s,path,useCache):
                assert useCache is False
                if path:
                    assert path.startswith('/proc/self/fd/')
                    with open(path,'rb') as f:raw=f.read()
                    im=Image.open(io.BytesIO(raw)).convert('RGBA')
                    h.images.append((h.tick,h.title,im.getpixel((im.width//2,im.height//2)),raw))
        class Window:
            def __init__(s,wid):assert wid==10000
            def getControl(s,cid):return Control(cid)
            def getProperty(s,name):return h.props.get(name,'')
            def setProperty(s,name,value):h.props[name]=value
            def clearProperty(s,name):h.props.pop(name,None)
        class Player:
            def __init__(s):h.players+=1
            def __getattr__(s,name):raise AssertionError('Playback owner/transport was accessed: '+name)
        class Capture:
            def __init__(s):h.captures+=1
            def __del__(s):h.released+=1
            def getAspectRatio(s):return 1.5
            def capture(s,w,hh):assert w==144 and hh==96
            def getImageFormat(s):return h.format
            def getImage(s,timeout):
                assert timeout<=30
                if h.fail:raise RuntimeError('capture unavailable')
                h.frames+=1
                return bytearray(Image.new('RGBA',(144,96),'blue' if h.blue else 'lime').tobytes('raw','BGRA'))
        class Monitor:
            def abortRequested(s):return h.tick>=h.steps
            def waitForAbort(s,delay):
                assert delay>=.02
                h.events.append((h.tick,h.props.get('Infinity.NativeAmbient.Status'),h.props.get('Infinity.NativeAmbient.Active'),h.frames))
                h.tick+=1;h.change(h);return h.tick>=h.steps
        def cond(query):
            if query=='Player.HasVideo + Control.IsVisible(29900)':return h.has_video
            if query=='Player.Paused | Player.Caching':return h.paused or h.buffering
            if query.startswith('Control.IsVisible('):return True
            raise AssertionError(query)
        def translate(path):return str(h.recipe if path.endswith('infinity_native_glass.json') else h.root/'lock')
        self.saved={name:sys.modules.get(name) for name in ('xbmc','xbmcgui','xbmcvfs')}
        sys.modules.update(xbmc=types.SimpleNamespace(Player=Player,Monitor=Monitor,RenderCapture=Capture,getCondVisibility=cond,getInfoLabel=lambda key:h.title),
                           xbmcgui=types.SimpleNamespace(Window=Window,getCurrentWindowId=lambda:h.window),xbmcvfs=types.SimpleNamespace(translatePath=translate))
        spec=importlib.util.spec_from_file_location('observer_under_test',HERE/'infinity_native_ambient.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        # Initialize exactly the ctypes signatures in the production resolver.
        original=ctypes.CDLL
        try:
            ctypes.CDLL=lambda path:self.lib;self.module.native_library()
        finally:ctypes.CDLL=original
        self.module.native_library=lambda:self.lib
    def run(self):
        try:self.change(self);self.module.main()
        finally:
            for name,value in self.saved.items():
                if value is None:sys.modules.pop(name,None)
                else:sys.modules[name]=value
            self.tmp.cleanup()
        return self

class ObserverTests(unittest.TestCase):
    def test_live_output_and_no_additional_playback_owner(self):
        h=Harness().run();self.assertGreater(len(h.images),3);self.assertEqual(h.players,1)
        self.assertEqual(h.captures,h.released);self.assertNotIn('Infinity.NativeAmbient.Active',h.props)
    def test_paused_entry_obtains_then_freezes_one_valid_frame(self):
        h=Harness(change=lambda h:setattr(h,'paused',True)).run()
        self.assertEqual(h.frames,3);self.assertEqual(len(h.images),1);self.assertIn('held',[e[1] for e in h.events])
    def test_pause_resume_freezes_without_capture_worker(self):
        def change(h):h.paused=5<=h.tick<12
        h=Harness(change=change).run()
        frames=[e[3] for e in h.events if 5<=e[0]<12];self.assertEqual(len(set(frames)),1)
        self.assertEqual(len([i for i in h.images if 5<=i[0]<12]),0);self.assertGreater(h.frames,8)
        self.assertEqual(h.captures,h.released)
    def test_buffering_retains_previous_colors(self):
        def change(h):h.buffering=h.tick>=5
        h=Harness(change=change).run();self.assertEqual(len({e[3] for e in h.events if e[0]>=5}),1)
        self.assertTrue(all(e[2]=='true' for e in h.events if e[0]>=5))
    def test_new_session_capture_failure_clears_prior_color(self):
        def change(h):
            if h.tick>=6:h.title='movie-b';h.fail=True
        h=Harness(change=change).run();self.assertTrue(h.images)
        self.assertFalse(any(i[1]=='movie-b' for i in h.images))
        self.assertTrue(all(e[2] is None for e in h.events if e[0]>=6))
    def test_new_movie_receives_fresh_not_smoothed_old_movie_color(self):
        def change(h):
            if h.tick>=6:h.title='movie-b';h.blue=False
        h=Harness(change=change).run();new=[i for i in h.images if i[1]=='movie-b'];self.assertTrue(new)
        self.assertGreater(new[0][2][1],240);self.assertLess(new[0][2][2],5)
    def test_seek_same_session_transitions_smoothly(self):
        def change(h):
            if h.tick>=6:h.blue=False
        h=Harness(change=change).run();after=[i for i in h.images if i[0]>=6]
        self.assertGreater(after[0][2][1],40);self.assertGreater(after[0][2][2],40)
        self.assertGreater(after[-1][2][1],240)
    def test_off_and_subtle_never_capture(self):
        for mode in ('off','subtle'):
            h=Harness(change=lambda h:h.props.update({'Infinity.AmbientHome.Mode':mode})).run()
            self.assertEqual(h.frames,0);self.assertFalse(h.images)
    def test_stop_releases_and_clears(self):
        h=Harness(change=lambda h:setattr(h,'has_video',h.tick<6)).run()
        self.assertTrue(all(e[2] is None for e in h.events if e[0]>=6));self.assertEqual(h.captures,h.released)
    def test_background_and_pip_gate_stop_sampling_then_resume(self):
        def change(h):h.lib.infinity_ambient_set_active(not 6<=h.tick<12)
        h=Harness(change=change).run();self.assertTrue(all(e[2] is None for e in h.events if 6<=e[0]<12))
        self.assertTrue(any(i[0]>=14 for i in h.images))
    def test_fullscreen_home_cycle_remains_one_observer(self):
        h=Harness(change=lambda h:setattr(h,'window',12005 if 6<=h.tick<12 else 10000)).run()
        self.assertTrue(any(i[0]>=14 for i in h.images));self.assertEqual(h.players,1);self.assertEqual(h.captures,h.released)
    def test_layout_epoch_rebinds_while_paused(self):
        def change(h):
            h.paused=True
            if h.tick==8:h.props['Infinity.NativeAmbient.LayoutEpoch']='new-layout'
        h=Harness(change=change).run();self.assertEqual(h.frames,3);self.assertEqual(len(h.images),2)
    def test_appearance_updates_held_glass_without_recapture(self):
        def change(h):
            h.paused=True
            if h.tick==8:h.props['Infinity.SystemTheme']='light'
        h=Harness(change=change).run();self.assertEqual(h.frames,3);self.assertEqual(len(h.images),2)
        self.assertLess(h.images[-1][2][3],h.images[0][2][3])
    def test_unsupported_capture_format_fails_closed(self):
        h=Harness(change=lambda h:setattr(h,'format','RGBA')).run();self.assertFalse(h.images);self.assertEqual(h.frames,0)
    def test_no_transport_resolver_or_provider_calls_in_observer(self):
        tree=ast.parse((HERE/'infinity_native_ambient.py').read_text())
        forbidden={'play','stop','pause','seekTime','executeJSONRPC','executebuiltin','setAudioStream','setSubtitleStream'}
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls&forbidden)
    def test_missing_native_library_is_contained(self):
        h=Harness()
        def unavailable():raise OSError('unsupported device')
        h.module.native_library=unavailable;h.run();self.assertEqual(h.frames,0);self.assertFalse(h.images)

if __name__=='__main__':unittest.main()
