"""Run against the exact 2103403 Command Center plus 2103404 patches."""
import ast, contextlib, hashlib, importlib.util, json, pathlib, sys, tempfile, types, unittest, urllib.parse, os
from unittest.mock import Mock
ROOT=pathlib.Path(__file__).parent
SRC=ROOT/'patched'
PARENT=ROOT/'parent_cc'

class Tag:
    def __init__(self,kind='tvshow',season=-1,episode=-1):self.kind=kind;self.season=season;self.episode=episode
    def getMediaType(self):return self.kind
    def getTitle(self):return 'Re:ZERO'
    def getSeason(self):return self.season
    def getEpisode(self):return self.episode
    def getPlayCount(self):return 0
class Item:
    def __init__(self,route,kind='tvshow',season=-1,episode=-1):self.route=route;self.tag=Tag(kind,season,episode)
    def getPath(self):return self.route
    def getVideoInfoTag(self):return self.tag
    def getLabel(self):return 'Re:ZERO'
    def getArt(self,key):return ''

def show_route(slug='re-zero',action='actionEpisodesMenu',host='www.wcostream.tv',extra=None):
    query={'action':action,'url':f'https://{host}/anime/{slug}'}
    if extra:query.update(extra)
    return 'plugin://plugin.video.watchnixtoons2/?'+urllib.parse.urlencode(query)

class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xbmc=types.SimpleNamespace(LOGINFO=1,getSkinDir=lambda:'skin.infinity.diggz',
            getCondVisibility=lambda *a:False,log=lambda *a:None,getInfoLabel=lambda *a:'',
            executebuiltin=lambda *a:None)
        cls.xbmcgui=types.SimpleNamespace(getCurrentWindowId=lambda:10000,
            Dialog=lambda:types.SimpleNamespace(input=lambda *a:'Anime',notification=lambda *a:None,
                ok=lambda *a:None),NOTIFICATION_INFO=1)
        cls.common=types.SimpleNamespace(persistence_scope=contextlib.nullcontext,
            addon_profile=lambda:None,atomic_json=lambda path,data:path.write_text(json.dumps(data)),
            read_json=lambda path,default:json.loads(path.read_text()) if path.exists() else default)
        sys.modules.update({'xbmc':cls.xbmc,'xbmcgui':cls.xbmcgui,'common':cls.common})
        spec=importlib.util.spec_from_file_location('resume_hub',SRC/'resume_hub.py')
        hub=importlib.util.module_from_spec(spec);sys.modules['resume_hub']=hub;spec.loader.exec_module(hub)
        cls.hub=hub
    def entry(self,route,kind='tvshow',season=-1,episode=-1):
        token=self.hub.watchnixtoons_source_identity(route,kind,season,episode)
        if not token:return None
        return dict(key=self.hub.identity_key(token),identity=token,media='movie' if kind=='movie' else 'tv',
            title='Re:ZERO',label='Re:ZERO',source=route,stable_source=route,
            season=season,episode=episode,dbid=-1)
    def test_exact_location_known_and_title_ignored(self):
        route=show_route()
        self.assertEqual(self.hub.watchnixtoons_source_identity(route,'tvshow')['scope'],'watchnixtoons_local')
        entry=self.entry(route)
        self.assertEqual(self.hub.entry_identity(entry),entry['identity'])
        self.assertEqual(len(entry['key']),64)
        self.assertFalse(self.hub.verified_ids(entry['identity']['ids']))
    def test_same_url_query_parameter_order_and_title_do_not_create_extra_identity(self):
        route=show_route()
        parts=urllib.parse.urlsplit(route)
        other='plugin://plugin.video.watchnixtoons2/?url='+urllib.parse.quote_plus('https://www.wcostream.tv/anime/re-zero')+'&action=actionEpisodesMenu'
        a=self.entry(route);b=self.entry(other)
        self.assertEqual(a['key'],b['key'])
        self.assertTrue(self.hub.same_identity(self.hub.entry_identity(a),self.hub.entry_identity(b)))
    def test_different_website_page_cannot_alias(self):
        a=self.entry(show_route('re-zero'));b=self.entry(show_route('rezero-season-two'))
        self.assertNotEqual(a['key'],b['key'])
        self.assertFalse(self.hub.same_identity(a['identity'],b['identity']))
    def test_never_canonical_trakt_identity(self):
        a=self.entry(show_route())
        typed=self.hub.show_identity('tvshow',{'tmdb':'65942'})
        self.assertFalse(self.hub.same_identity(a['identity'],typed))
        self.assertNotEqual(self.hub.identity_key(typed),a['key'])
    def test_corrupted_record_or_changed_route_rejected(self):
        a=self.entry(show_route());a['source']=show_route('another-show')
        self.assertIsNone(self.hub.entry_identity(a))
        a=self.entry(show_route());a['identity']['ids']['wnt2']='bad'
        self.assertIsNone(self.hub.entry_identity(a))
    def test_untrusted_or_ambiguous_source_urls_fail_closed(self):
        bad=[
          'plugin://plugin.video.other/?action=actionEpisodesMenu&url=%2Fanime%2Fre-zero',
          'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu',
          'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=%2Fa&url=%2Fb',
          'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=javascript%3Aalert%281%29',
          'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=//bad',
          'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=https%3A%2F%2Fuser%3Apass%40example.com%2Fre-zero',
          'plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=https%3A%2F%2Fexample.com%3Anotaport%2Fa',
        ]
        for route in bad:
            with self.subTest(route=route):
                self.assertIsNone(self.hub.watchnixtoons_source_identity(route,'tvshow'))
    def test_episode_same_title_different_page(self):
        left=self.entry(show_route('ep1','actionResolve'),'episode',-1,-1)
        right=self.entry(show_route('ep2','actionResolve'),'episode',-1,-1)
        self.assertIsNotNone(left)
        self.assertNotEqual(left['key'],right['key'])
    def test_persistent_save_for_later_and_watchlist_on_original_path(self):
        route=show_route()
        entry=self.entry(route)
        with tempfile.TemporaryDirectory() as root:
            profile=pathlib.Path(root)
            data=self.hub.load(profile)
            data['later'][entry['key']]=self.hub._stamp(entry,'added_at')
            self.hub.save(profile,data,retain_records=True)
            self.assertEqual(self.hub.load(profile)['later'][entry['key']]['source'],route)
            data=self.hub.load(profile)
            data,added,changed=self.hub.toggle_watchlist_data(data,entry['key'],incoming=entry)
            self.assertTrue(added)
            self.hub.save(profile,data,retain_records=True)
            self.assertEqual(self.hub.load(profile)['watchlist'][entry['key']]['stable_source'],route)
            self.assertEqual(len(self.hub.entries(self.hub.load(profile),'tv','later')),1)
    def test_context_dispatch_no_provider_search(self):
        names={'_watchnixtoons_source_entry','_watchnixtoons_tracking','_watchnixtoons_exact_previous',
          '_watchnixtoons_identity_slot','_watchnixtoons_verified_link','_watchnixtoons_owned_records'}
        tree=ast.parse((SRC/'context.py').read_text()); funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        with tempfile.TemporaryDirectory() as root:
            popup=Mock(return_value=True); dialog=self.xbmcgui.Dialog()
            ns={'hub':self.hub,'addon_profile':lambda:pathlib.Path(root),
                '_popup_module':lambda:types.SimpleNamespace(show_item_menu=popup),
                'xbmcgui':self.xbmcgui}
            exec(compile(ast.fix_missing_locations(ast.Module(funcs,type_ignores=[])),'context.py','exec'),ns)
            source=show_route(); item=Item(source)
            self.assertTrue(ns['_watchnixtoons_tracking'](item,source,'tvshow','Re:ZERO','Save for Later','save-later'))
            original=popup.call_args
            self.assertEqual(original.kwargs['incoming']['source'],source)
            self.assertEqual(original.kwargs['incoming']['identity']['scope'],'watchnixtoons_local')
            self.assertEqual(original.kwargs['nixtoons_confirmed_row'],('Save for Later','save-later',''))

if __name__=='__main__':unittest.main(verbosity=2)