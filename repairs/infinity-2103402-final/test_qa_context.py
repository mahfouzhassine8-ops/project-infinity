"""Host acceptance for exact Otaku/Nixtoons nontracking title menu and 25-file pins."""
from pathlib import Path
from unittest.mock import patch
import ast,json,sys,types,unittest
from zipfile import ZipFile
import qa_component_holds as scope

ROOT=Path(__file__).parent
class Tag:
    def __init__(self,kind='tvshow'):self.kind=kind
    def getMediaType(self):return self.kind
    def getTitle(self):return 'Re:ZERO'
class Item:
    def __init__(self,path,kind='tvshow'):
        self.path=path;self.tag=Tag(kind);self.folder=kind=='tvshow'
    def getPath(self):return self.path
    def getLabel(self):return 'Re:ZERO'
    def getVideoInfoTag(self):return self.tag
    def isFolder(self):return self.folder
    def getArt(self,name):return ''

class ContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        cls.apk=Path(os.environ["INFINITY_BASELINE_APK"])
        cls.changed=scope.changes(cls.apk)
        context=ast.parse(cls.changed[scope.CONTEXT].decode())
        functions=[x for x in context.body if isinstance(x,ast.FunctionDef)
                   and x.name=='_unverified_anime_menu']
        assert len(functions)==1
        cls.code=compile(ast.Module(body=functions,type_ignores=[]),'context.py','exec')
    def setUp(self):
        self.calls=[];self.answers=[0]
        kodi=types.ModuleType('xbmc')
        def rpc(payload):
            data=json.loads(payload);self.calls.append(data)
            if data['method']=='Favourites.GetFavourites':
                return json.dumps({'result':{'favourites':[]}})
            return json.dumps({'result':'OK'})
        kodi.executeJSONRPC=rpc
        class Player:
            def play(_,url,item):self.calls.append({'method':'Player.play','url':url})
        kodi.Player=Player
        meta=types.ModuleType('title_metadata');meta.capture=lambda item:{'plot':'kept'}
        select=types.ModuleType('infinity_settings');select.choose=lambda t,r:self.answers.pop(0)
        info=types.ModuleType('information')
        info.show_information=lambda i,e,play_available=False:self.calls.append({
            'method':'info','enabled':play_available,'entry':e})
        self.modules=patch.dict(sys.modules,{'xbmc':kodi,'title_metadata':meta,
                       'infinity_settings':select,'information':info})
        self.modules.start()
        self.global_scope={'xbmc':kodi,'json':json}
        exec(self.code,self.global_scope)
    def tearDown(self):self.modules.stop()
    def menu(self,item):return self.global_scope['_unverified_anime_menu'](item)
    def test_otaku_navigation_uses_selected_original_route(self):
        route='plugin://plugin.video.otaku/search_tv_show/re%3Azero'
        self.assertTrue(self.menu(Item(route)))
        self.assertEqual(self.calls[-1]['method'],'GUI.ActivateWindow')
        self.assertEqual(self.calls[-1]['params']['parameters'][0],route)
    def test_watchnixtoons_original_favourite(self):
        self.answers=[2];route='plugin://plugin.video.watchnixtoons2/?action=series&title=re%3Azero'
        self.assertTrue(self.menu(Item(route)))
        self.assertEqual(self.calls[-1]['method'],'Favourites.AddFavourite')
        self.assertEqual(self.calls[-1]['params']['windowparameter'],route)
    def test_information_nontracking_no_user_data_writes(self):
        self.answers=[1]
        self.assertTrue(self.menu(Item('plugin://plugin.video.otaku/search_tv_show/re%3Azero')))
        self.assertEqual(self.calls[-1]['method'],'info')
        self.assertFalse(self.calls[-1]['enabled'])
    def test_cancel_does_not_update_favourites(self):
        self.answers=[-1]
        self.assertFalse(self.menu(Item('plugin://plugin.video.watchnixtoons2/?action=search')))
        self.assertEqual([x['method'] for x in self.calls],['Favourites.GetFavourites'])
    def test_wrong_provider_and_command_injection_rejected(self):
        for s in ('plugin://plugin.video.umbrella/?q=foo',
                  'plugin://plugin.video.otaku/?q=\nCommand',
                  'http://plugin.video.watchnixtoons2/'):
            self.assertFalse(self.menu(Item(s)))
        self.assertEqual(self.calls,[])
    def test_exact_version_and_pins_include_old_passing_controls(self):
        with ZipFile(self.apk) as z:
            for name in scope.PINS:
                mapping=json.loads(self.changed[name])
                self.assertEqual(len(mapping),25)
                for leaf,expected in mapping.items():
                    source=(self.changed[scope.CONTEXT] if leaf=='context.py'
                         else z.read(scope.PREFIX+scope.CC+leaf))
                    self.assertEqual(scope.sha(source),expected)
            self.assertIn(b'0.3.5.35',z.read('assets/addons/script.infinity.commandcenter/addon.xml'))
            self.assertEqual(len(self.changed),3)

if __name__=='__main__':unittest.main(verbosity=2)
