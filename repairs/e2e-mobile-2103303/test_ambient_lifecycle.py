"""Exercise actual candidate resource owners with fake Kodi control handles."""
from pathlib import Path
import importlib.util,os,sys,types,unittest

skin=Path(sys.argv.pop(1))
sys.modules['xbmc']=types.SimpleNamespace(Player=object)
sys.modules['xbmcgui']=types.SimpleNamespace()
sys.modules['xbmcvfs']=types.SimpleNamespace()
spec=importlib.util.spec_from_file_location('ambient',skin/'resources/lib/infinity_native_ambient.py')
ambient=importlib.util.module_from_spec(spec);spec.loader.exec_module(ambient)

class Library:
    def __init__(self):self.destroyed=[];self.leases=[];self.resets=[]
    def infinity_ambient_create(self):return 123
    def infinity_ambient_destroy(self,handle):self.destroyed.append(handle)
    def infinity_ambient_reset(self,handle):self.resets.append(handle)
    def infinity_ambient_surface_request(self,enabled):self.leases.append(enabled);return enabled
    def infinity_ambient_memfd(self):return os.memfd_create('ambient-test')

class Control:
    def __init__(self):self.images=[]
    def setImage(self,*args):self.images.append(args)

class AmbientLifecycle(unittest.TestCase):
    def test_close_releases_native_session_and_sampling_exactly_once(self):
        lib=Library();session=ambient.Session(lib);session.surface.token=77
        session.capture=object();session.last_frame=bytearray(300)
        session.close();session.close()
        self.assertEqual([123],lib.destroyed);self.assertEqual([123],lib.resets)
        self.assertEqual([0],lib.leases);self.assertIsNone(session.capture)
        self.assertIsNone(session.last_frame);self.assertIsNone(session.handle)

    def test_hidden_material_releases_fd_ring_and_can_repaint_when_visible(self):
        lib=Library();control=Control();home=types.SimpleNamespace(getControl=lambda _:control)
        glass=ambient.Glass(home,{'overlay':1},lib);glass.allocate();fds=list(glass.fds)
        glass.presented=('old-bounds',);glass.close();glass.close()
        self.assertIsNone(glass.presented);self.assertEqual([],glass.fds)
        for fd in fds:
            with self.assertRaises(OSError):os.fstat(fd)
        glass.allocate();self.assertEqual(3,len(glass.fds));glass.close()

    def test_layout_reset_discards_capture_and_all_materials(self):
        lib=Library();control=Control();home=types.SimpleNamespace(getControl=lambda _:control)
        session=ambient.Session(lib);glass=ambient.Glass(home,{'overlay':1},lib)
        glass.allocate();session.glass.append(glass);session.ready=True;session.capture=object()
        session.reset()
        self.assertFalse(session.ready);self.assertEqual([],session.glass)
        self.assertIsNone(session.capture);self.assertEqual([],glass.fds);session.close()

if __name__=='__main__':unittest.main()
