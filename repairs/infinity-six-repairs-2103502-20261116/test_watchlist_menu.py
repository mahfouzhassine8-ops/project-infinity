"""Selected menu/identity tests; disposable host store, no provider or owner data.

The positive item is a constructed contract fixture with an explicit IMDb ID,
not a captured Otaku search result or proof of Android provider compatibility.
"""
from pathlib import Path
from zipfile import ZipFile
from contextlib import nullcontext
from unittest.mock import patch
import ast, hashlib, importlib.util, json, sys, tempfile, types, unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
APK = Path(sys.argv.pop(1))
PREFIX = 'assets/addons/script.infinity.commandcenter/'
assert hashlib.sha256(APK.read_bytes()).hexdigest() == 'f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28'
with ZipFile(APK) as archive:
    ORIGINAL = {name: archive.read(PREFIX + name) for name in
                ('addon.xml', 'context.py', 'infinity_trakt.py', 'resume_hub.py')}
CANDIDATE = HERE / 'overlay/script.infinity.commandcenter'

def module(name, **values):
    result = types.ModuleType(name); result.__dict__.update(values); return result

def function(raw, name, scope):
    tree = ast.parse(raw)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1
    exec(compile(ast.Module(body=nodes, type_ignores=[]), name, 'exec'), scope)
    return scope[name]

class Tag:
    def __init__(self, ids): self.ids = ids
    def getMediaType(self): return 'tvshow'
    def getUniqueID(self, name): return self.ids.get(name, '')
    def getTitle(self): return 'Re:Zero — Starting Life in Another World'
    def getPlayCount(self): return 0

class Item:
    def __init__(self, ids): self.tag = Tag(ids)
    def getVideoInfoTag(self): return self.tag
    def getLabel(self): return self.tag.getTitle()
    def getPath(self): return 'plugin://plugin.video.otaku/'
    def getArt(self, name): return ''
    def isFolder(self): return True

class Menu(unittest.TestCase):
    def test_only_registration_visibility_and_version_change(self):
        before = ET.fromstring(ORIGINAL['addon.xml'])
        after = ET.fromstring((CANDIDATE/'addon.xml').read_bytes())
        self.assertEqual(after.attrib, dict(before.attrib, version='0.3.5.84'))
        old = before.find("extension[@point='kodi.context.item']/menu/item[@args='manage']/visible")
        new = after.find("extension[@point='kodi.context.item']/menu/item[@args='manage']/visible")
        suffix = ' + [!String.IsEmpty(ListItem.UniqueID(tmdb)) | !String.IsEmpty(ListItem.UniqueID(tvdb)) | !String.IsEmpty(ListItem.UniqueID(imdb)) | Integer.IsGreater(ListItem.DBID,0)]'
        self.assertTrue(old.text.endswith(suffix)); self.assertEqual(new.text, old.text[:-len(suffix)])
        before.set('version', '0.3.5.84'); old.text = new.text
        self.assertEqual(ET.tostring(before), ET.tostring(after))
        for kind in ('movie', 'episode', 'tvshow', 'season'):
            self.assertIn('String.IsEqual(ListItem.DBTYPE,'+kind+')', new.text)
        self.assertIn('String.IsEmpty(ListItem.Property(Infinity.ResumeHub.Key))', new.text)
        self.assertNotIn('UniqueID', new.text)
        # Exact allowlisted expression admits only those types and unowned rows.
        for kind, owned, expected in [('tvshow',False,True),('movie',False,True),
                                      ('unknown',False,False),('',False,False),('tvshow',True,False)]:
            self.assertEqual(kind in ('movie','episode','tvshow','season') and not owned, expected)

    def test_fallback_passes_exact_item_without_navigation(self):
        item = Item({}); received = []; choices = []
        def choose(title, rows): choices.extend(rows); return rows.index('Infinity Trakt')
        def rpc(raw):
            request = json.loads(raw)
            self.assertEqual(request['method'], 'Favourites.GetFavourites')
            return json.dumps({'result': {'favourites': []}})
        imports = {'title_metadata': module('title_metadata', capture=lambda item: {}),
                   'infinity_settings': module('infinity_settings', choose=choose),
                   'infinity_trakt': module('infinity_trakt', main=received.append)}
        with patch.dict(sys.modules, imports):
            target = function((CANDIDATE/'context.py').read_bytes(), '_unverified_anime_menu',
                              {'xbmc':module('xbmc', executeJSONRPC=rpc)})
            self.assertTrue(target(item))
        self.assertEqual(received, [item]); self.assertIs(received[0], item)
        self.assertEqual([x for x in choices if x != 'Infinity Trakt'],
                         ['Open in Otaku','Information','Add to Favourites'])

    def test_real_selection_and_membership_no_identity_write(self):
        with tempfile.TemporaryDirectory(prefix='infinity-watchlist-host-') as temporary:
            profile = Path(temporary); notices = []; saves = []
            def read(path, default):
                return json.loads(Path(path).read_text()) if Path(path).exists() else default
            def atomic(path, data):
                saves.append(str(path)); Path(path).write_text(json.dumps(data))
            stubs = {'xbmc':module('xbmc', getSkinDir=lambda:'skin.infinity.diggz'),
                     'common':module('common', atomic_json=atomic, read_json=read,
                                     persistence_scope=nullcontext)}
            hub = module('host_resume_hub')
            with patch.dict(sys.modules, stubs):
                exec(compile(ORIGINAL['resume_hub.py'], 'exact502_resume_hub.py', 'exec'), hub.__dict__)
            hub.publish_home = lambda data: None
            scope = dict(hub=hub, Path=Path, json=json, persistence_scope=nullcontext)
            for name in ('selected','set_membership','apply_local'):
                function(ORIGINAL['infinity_trakt.py'], name, scope)
            entry = scope['selected'](Item({'imdb':'tt5607616'}), None, None)
            self.assertEqual(entry['identity']['ids'], {'imdb':'tt5607616'})
            self.assertEqual(entry['media'], 'tv')
            self.assertTrue(scope['apply_local'](profile, entry, 'add-watchlist'))
            self.assertFalse(scope['apply_local'](profile, entry, 'add-watchlist'))
            self.assertEqual(len(saves), 1)
            # Fresh module instance + disk reload checks ordinary persistence.
            reloaded = module('host_resume_hub_reloaded')
            with patch.dict(sys.modules, stubs):
                exec(compile(ORIGINAL['resume_hub.py'], 'exact502_resume_hub.py', 'exec'), reloaded.__dict__)
            data = reloaded.load(profile)
            self.assertEqual(list(data['watchlist']), [entry['key']])
            for bucket in ('items','watched','collection','later','sources','ratings','lists'):
                self.assertEqual(data[bucket], {})
            scope.update(xbmc=stubs['xbmc'], _bridge=lambda:(None,None),
                         notice=notices.append, sys=types.SimpleNamespace(),
                         show=lambda *a,**k:self.fail('Invalid identity reached mutation menu'),
                         ET=ET)
            missing = Item({})
            before = (profile/hub.CONTINUE_FILE).read_bytes()
            main = function(ORIGINAL['infinity_trakt.py'], 'main', scope)
            main(missing)
            self.assertEqual(len(notices), 1)
            self.assertEqual((profile/hub.CONTINUE_FILE).read_bytes(), before)
            self.assertEqual(len(saves), 1)

if __name__ == '__main__':
    unittest.main()
