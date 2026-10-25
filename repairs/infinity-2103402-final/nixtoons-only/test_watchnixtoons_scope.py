import ast
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from contextlib import contextmanager

BASE=pathlib.Path(__file__).parent
SOURCE=BASE/'patched'/'context.py'
PLUGIN=BASE/'patched'/'plugin.py'
ROUTE='plugin://plugin.video.watchnixtoons2/?action=show&slug=re:zero'
TITLE='Re:ZERO -Starting Life in Another World-'

def functions():
    t=ast.parse(SOURCE.read_text())
    picked={"_watchnixtoons_exact_previous","_watchnixtoons_confirmed_entry","_watchnixtoons_tracking","_unverified_anime_menu"}
    chunk=ast.Module([node for node in t.body if isinstance(node,ast.FunctionDef) and node.name in picked],type_ignores=[])
    return compile(ast.fix_missing_locations(chunk),str(SOURCE),'exec')

class Tag:
    def __init__(self,kind='tvshow',ids=None): self.kind=kind;self.ids=ids or {}
    def getMediaType(self):return self.kind
    def getTitle(self):return TITLE
    def getSeason(self):return -1
    def getEpisode(self):return -1
    def getPlayCount(self):return 0
    def getUniqueID(self,key):return self.ids.get(key,'')
class Item:
    def __init__(self,route=ROUTE,kind='tvshow'):
        self.route=route;self.tag=Tag(kind)
    def getPath(self):return self.route
    def getVideoInfoTag(self):return self.tag
    def getLabel(self):return TITLE
    def getArt(self,key):return 'https://image.invalid/poster' if key=='poster' else ''
    def isFolder(self):return True

class Hub:
    @staticmethod
    def verified_ids(values):
        return {k:str(v) for k,v in (values if isinstance(values,dict) else {}).items() if k in ('tmdb','imdb','tvdb') and str(v).isdigit()}
    @staticmethod
    def show_identity(kind,ids,season=-1):
        return {'kind':kind,'scope':'show','ids':ids} if ids and kind=='tvshow' else None
    @staticmethod
    def identity_key(identity):return 'a'*64 if identity else ''
    @staticmethod
    def entry_identity(entry):return entry.get('identity')
    @staticmethod
    def episode_number(n):return n if type(n)==int and n>=0 else -1
    @staticmethod
    def same_identity(a,b):return a==b and bool(a)
    @staticmethod
    def load_view(profile):return {key:{} for key in ('items','watched','watchlist','collection','later')}

class UI:
    selected=[]
    results=[]
    def __init__(self):self.calls=[]
    def input(self,*args):self.calls.append(('input',args));return TITLE
    def yesno(self,*args):self.calls.append(('yesno',args));return True
    def ok(self,*args):self.calls.append(('ok',args))

class NixTests(unittest.TestCase):
    def setUp(self):
        self.choose_calls=[]
        self.selections=[]
        self.ui=UI();self.events=[]
        self.ns={'hub':Hub,'addon_profile':lambda:'mock-profile','xbmcgui':types.SimpleNamespace(Dialog=lambda:self.ui,Window=lambda x:object(),DialogProgress=lambda:types.SimpleNamespace(create=lambda *a:None,close=lambda:None)),
          'xbmc':types.SimpleNamespace(executeJSONRPC=lambda text:'{"result":{"favourites":[]}}',getSkinDir=lambda:'skin.infinity.diggz',Player=lambda:types.SimpleNamespace(play=lambda *a:self.events.append('play'))),
          'json':__import__('json'),'urlsplit':__import__('urllib.parse',fromlist=['urlsplit']).urlsplit,
          '_popup_module':lambda:types.SimpleNamespace(show_item_menu=lambda *args,**kw:self.events.append(('shared_menu',args,kw)) or True)}
        exec(functions(),self.ns)
        def choose(title,labels):
            self.choose_calls.append((title,labels))
            return self.selections.pop(0) if self.selections else -1
        self.choose=choose
        self.modules={'title_metadata':types.SimpleNamespace(capture=lambda item:{'title':TITLE}),
                     'infinity_settings':types.SimpleNamespace(choose=choose),
                     'information':types.SimpleNamespace(show_information=lambda *a,**kw:None)}
        self.modpatch=patch.dict(sys.modules,self.modules)
        self.modpatch.start()
    def tearDown(self):self.modpatch.stop()
    def test_otaku_fallback_keeps_exact_original_three_actions(self):
        self.selections=[-1]
        item=Item(route='plugin://plugin.video.otaku/search_tv_show/Re:ZERO')
        got=self.ns['_unverified_anime_menu'](item)
        self.assertFalse(got)
        self.assertEqual(self.choose_calls[0][1],['Open in Otaku','Information','Add to Favourites'])
    def test_watchnixtoons_shows_existing_universal_tracking_actions(self):
        self.selections=[-1]
        got=self.ns['_unverified_anime_menu'](Item())
        self.assertFalse(got)
        self.assertEqual(self.choose_calls[0][1],[
            'Open in WatchNixtoons2','Mark Watched','Add to Watchlist',
            'Add to Favourites','Add to Collection','Add to Custom List',
            'Save for Later','Information'])
    def test_watchnixtoons_track_invokes_resolver_only_after_action(self):
        self.selections=[1]
        self.ns['_watchnixtoons_tracking']=Mock(return_value=False)
        self.assertFalse(self.ns['_unverified_anime_menu'](Item()))
        self.ns['_watchnixtoons_tracking'].assert_called_once()
        self.assertEqual(self.ns['_watchnixtoons_tracking'].call_args.args[-2:],('Mark Watched','mark-watched'))
    def test_unknown_provider_route_cannot_ever_run_nixtoons_tracking(self):
        self.selections=[1]
        item=Item(route='plugin://plugin.video.otaku/show/1')
        self.ns['_watchnixtoons_tracking']=Mock(side_effect=AssertionError('Must not call'))
        self.ns['_unverified_anime_menu'](item)
        self.assertEqual(len(self.choose_calls[0][1]),3)
    def mock_provider(self,ids=None,typ='tvshow',path='plugin://plugin.video.seren/?action=show&id=1'):
        self.search=types.SimpleNamespace(
            providers=lambda media,force:([{'id':'plugin.video.seren','name':'Seren','contract':{}},
                                           {'id':'plugin.video.watchnixtoons2','name':'WatchNixtoons2','contract':{}}],[]),
            _provider_result=lambda provider,query,home,cancel:(provider,'completed',{'result':{'files':[
                dict(type=typ,file=path,title='Re:ZERO - Starting Life in Another World',
                     year=2016,uniqueid=ids or {'tmdb':'65942'})]}},path),
            _Cancellation=lambda:types.SimpleNamespace(cancel=lambda:None))
        self.modules['infinity_search']=self.search
        sys.modules['infinity_search']=self.search
    def test_identity_choice_requires_explicit_provider_and_candidate_and_consent(self):
        self.mock_provider()
        self.selections=[0,0]
        item=Item()
        result=self.ns['_watchnixtoons_confirmed_entry'](item,ROUTE,'tvshow',TITLE)
        self.assertEqual(result['key'],'a'*64)
        self.assertEqual(result['source'],ROUTE)
        self.assertEqual(result['identity']['ids'],{'tmdb':'65942'})
        self.assertEqual(self.choose_calls[0][0],'Choose verified metadata provider')
        self.assertIn('TMDB:65942',self.choose_calls[1][1][0])
        self.assertEqual(len([x for x in self.ui.calls if x[0]=='yesno']),1)
        self.assertFalse(any(x[0]=='ok' for x in self.ui.calls))
    def test_absent_id_never_creates_infinity_tracking_record(self):
        self.mock_provider(ids={'mal_id':123})
        self.selections=[0]
        result=self.ns['_watchnixtoons_confirmed_entry'](Item(),ROUTE,'tvshow',TITLE)
        self.assertIsNone(result)
        self.assertEqual(len([c for c in self.ui.calls if c[0]=='yesno']),0)
    def test_wrong_original_candidate_kind_rejected(self):
        self.mock_provider(typ='movie')
        self.selections=[0]
        self.assertIsNone(self.ns['_watchnixtoons_confirmed_entry'](Item(),ROUTE,'tvshow',TITLE))
    def test_metadata_route_not_verified_for_provider_is_rejected(self):
        self.mock_provider(path='plugin://plugin.video.malicious/tv/123')
        self.selections=[0]
        self.assertIsNone(self.ns['_watchnixtoons_confirmed_entry'](Item(),ROUTE,'tvshow',TITLE))
    def test_user_cancellation_keeps_saved_state_unchanged(self):
        self.mock_provider()
        self.selections=[0,0]
        self.ui.yesno=lambda *args:False
        self.assertIsNone(self.ns['_watchnixtoons_confirmed_entry'](Item(),ROUTE,'tvshow',TITLE))
    def test_existing_exact_nixtoons_id_reuses_shared_menu(self):
        row={'source':ROUTE,'stable_source':ROUTE,'media':'tv','identity':{'kind':'tvshow','scope':'show','ids':{'tmdb':'65942'}},'title':TITLE,'label':TITLE}
        old=Hub.load_view
        Hub.load_view=staticmethod(lambda profile:{'items':{},'watched':{'a'*64:row},'watchlist':{},'collection':{},'later':{}})
        try:
            self.selections=[]
            got=self.ns['_unverified_anime_menu'](Item())
            self.assertTrue(got)
            self.assertEqual(self.events[0][0],'shared_menu')
            self.assertEqual(len(self.choose_calls),0)
        finally:Hub.load_view=old
    def test_preselected_path_gated_to_nixtoons_only(self):
        text=PLUGIN.read_text()
        self.assertIn("incoming.get('source','').startswith('plugin://plugin.video.watchnixtoons2/')",text)
        self.assertIn("r==nixtoons_confirmed_row",text)
        self.assertIn("if nixtoons_confirmed_row is not None",text)
        self.assertIn("with nullcontext() if read_only else persistence_scope():",text)
    def test_no_change_to_otaku_else_branch(self):
        orig=(BASE/'script.infinity.commandcenter'/'context.py').read_text()
        patched=SOURCE.read_text()
        source_tail=orig[orig.index("    else:\n        rows=[('Open in '+sources"):] if "    else:\n        rows=[('Open in '+sources" in orig else orig[orig.index("    rows=[('Open in '+sources"):]
        self.assertIn("('Information','information')",source_tail)
        self.assertIn("    else:\n        rows=[('Open in '+sources[parsed.netloc],'open'),",patched)

if __name__=='__main__':unittest.main(verbosity=2)
