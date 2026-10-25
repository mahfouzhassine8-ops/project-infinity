"""Signed-2103402 scope mock for the new exact-route identity binding."""
import ast,copy,hashlib,os,pathlib,sys,types,unittest
from unittest.mock import Mock,patch
from contextlib import contextmanager

SOURCE=pathlib.Path(os.environ["PATCHED_CONTEXT"])
ROUTE='plugin://plugin.video.watchnixtoons2/?action=show&slug=re:zero'
TITLE='Re:ZERO -Starting Life in Another World-'
IDENTITY={'schema':1,'kind':'tvshow','scope':'show','ids':{'tmdb':'65942'}}
KEY=hashlib.sha256(b'show|tmdb:65942').hexdigest()
class Tag:
    def getMediaType(self):return 'tvshow'
    def getTitle(self):return TITLE
    def getSeason(self):return -1
    def getEpisode(self):return -1
    def getPlayCount(self):return 0
class Item:
    def getPath(self):return ROUTE
    def getVideoInfoTag(self):return Tag()
    def getLabel(self):return TITLE
    def getArt(self,k):return ''
class Hub:
    @staticmethod
    def reset():
        Hub.data={name:{} for name in ('items','watched','watchlist','collection','later','lists')}
        Hub.saved=0
    @staticmethod
    def load(profile):return copy.deepcopy(Hub.data)
    @staticmethod
    def load_view(profile):return Hub.load(profile)
    @staticmethod
    def save(profile,data,publish,retain_records=True):
        assert retain_records
        Hub.data=copy.deepcopy(data);Hub.saved+=1
        return data
    @staticmethod
    def publish_home(data):pass
    @staticmethod
    def entry_identity(row):
        v=row.get('identity') if isinstance(row,dict) else None
        return v if isinstance(v,dict) and v.get('schema')==1 and v.get('kind')=='tvshow' and v.get('scope')=='show' and v.get('ids') else None
    @staticmethod
    def identity_key(i):return hashlib.sha256(('show|tmdb:'+i['ids']['tmdb']).encode()).hexdigest()
    @staticmethod
    def same_identity(a,b):return bool(a and b and a==b)
    @staticmethod
    def episode_number(n):return n if isinstance(n,int) and n>=0 else -1
    @staticmethod
    def verified_ids(ids):return {k:v for k,v in ids.items() if k=='tmdb' and str(v).isdigit()}
    @staticmethod
    def show_identity(kind,ids,season=-1):return dict(IDENTITY,ids=ids)
@contextmanager
def scope():yield
class LinkTests(unittest.TestCase):
    def setUp(self):
        Hub.reset()
        self.ui=types.SimpleNamespace(input=lambda *a:TITLE,yesno=lambda *a:True,ok=Mock())
        self.choices=[0,0]
        self.modules={'infinity_settings':types.SimpleNamespace(choose=lambda *a:self.choices.pop(0))}
        self.patch=patch.dict(sys.modules,self.modules);self.patch.start()
        names={'_watchnixtoons_identity_slot','_watchnixtoons_verified_link','_watchnixtoons_owned_records',
            '_watchnixtoons_store_verified_link','_watchnixtoons_exact_previous',
            '_watchnixtoons_confirmed_entry','_watchnixtoons_tracking'}
        tree=ast.parse(SOURCE.read_text())
        chosen=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        self.ns={'hub':Hub,'addon_profile':lambda:'/tmp/test',
                 'persistence_scope':scope,
                 'xbmcgui':types.SimpleNamespace(Dialog=lambda:self.ui,Window=lambda _:object(),
                     DialogProgress=lambda:types.SimpleNamespace(create=lambda *a:None,close=lambda:None)),
                 '_popup_module':lambda:types.SimpleNamespace(show_item_menu=lambda *a,**k:True)}
        exec(compile(ast.fix_missing_locations(ast.Module(chosen,type_ignores=[])),'patched.py','exec'),self.ns)
        self.search=types.SimpleNamespace(
            providers=lambda media,force=True:([{'id':'plugin.video.seren','name':'Seren','contract':{}}],[]),
            _provider_result=lambda p,q,h,c:(p,'completed',{'result':{'files':[
                dict(type='tvshow',file='plugin://plugin.video.seren/?action=show&id=1',
                     uniqueid={'tmdb':'65942'},title=TITLE,year=2016)]}},''),
            _Cancellation=lambda:types.SimpleNamespace(cancel=lambda:None))
        sys.modules['infinity_search']=self.search
    def tearDown(self):self.patch.stop()
    def confirmed(self):
        return self.ns['_watchnixtoons_confirmed_entry'](Item(),ROUTE,'tvshow',TITLE)
    def test_binding_is_separate_from_watchlist_and_later(self):
        entry=self.confirmed()
        self.assertEqual(entry['key'],KEY)
        self.assertEqual(Hub.saved,1)
        self.assertEqual(len(Hub.data['nixtoons_verified_links']),1)
        self.assertEqual(Hub.data['watchlist'],{})
        self.assertEqual(Hub.data['later'],{})
    def test_second_action_reuses_exact_link_without_search(self):
        self.confirmed()
        self.ns['_watchnixtoons_confirmed_entry']=Mock(side_effect=AssertionError('unnecessary provider lookup'))
        self.assertTrue(self.ns['_watchnixtoons_tracking'](Item(),ROUTE,'tvshow',TITLE,'Save for Later','save-later'))
    def test_custom_list_only_legacy_link_recovered(self):
        Hub.data['lists']={'Anime':{KEY:dict(key=KEY,source=ROUTE,stable_source=ROUTE,
                                media='tv',identity=IDENTITY)}}
        self.assertEqual(self.ns['_watchnixtoons_exact_previous'](Item(),ROUTE,'tvshow')['key'],KEY)
    def test_cancellation_writes_nothing(self):
        self.ui.yesno=lambda *a:False
        self.assertIsNone(self.confirmed())
        self.assertEqual(Hub.saved,0)
    def test_conflicting_route_identity_blocks_binding(self):
        Hub.data['later'][KEY]=dict(key=KEY,source=ROUTE,stable_source=ROUTE,
                                    media='tv',identity=dict(IDENTITY,ids={'tmdb':'111'}))
        self.assertIsNone(self.confirmed())
        self.assertNotIn('nixtoons_verified_links',Hub.data)
    def test_corrupted_link_not_reused(self):
        self.confirmed()
        slot=next(iter(Hub.data['nixtoons_verified_links']))
        Hub.data['nixtoons_verified_links'][slot]['identity']['ids']['tmdb']='999'
        self.assertIsNone(self.ns['_watchnixtoons_exact_previous'](Item(),ROUTE,'tvshow'))
    def test_route_drift_never_aliases_verified_link(self):
        self.confirmed()
        self.assertIsNone(self.ns['_watchnixtoons_exact_previous'](Item(),ROUTE+'&different=1','tvshow'))
if __name__=='__main__':unittest.main(verbosity=2)
