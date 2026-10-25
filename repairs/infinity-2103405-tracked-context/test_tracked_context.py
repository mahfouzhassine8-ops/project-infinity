"""2103405 native Kodi context registration and exact selected WatchNixtoons2 handoff."""
import ast, hashlib, os, sys, types, unittest
from pathlib import Path
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

ORIGINAL=Path(os.environ["CC_PARENT"])
PATCHED=Path(os.environ["CC_PATCHED"])

class Tag:
    def getMediaType(self): return "tvshow"
    def getUniqueID(self,name): return ""

class Item:
    def __init__(self,path):self.path=path
    def getPath(self):return self.path
    def getVideoInfoTag(self):return Tag()
    def getProperty(self,key):return ""
    def getLabel(self):return "Mob Psycho 100"

class NativeContextTests(unittest.TestCase):
    def setUp(self):
        root=ET.fromstring((PATCHED/"addon.xml").read_text())
        self.assertEqual(root.get("version"),"0.3.5.38")
        menu=root.find("./extension[@point='kodi.context.item']/menu")
        self.assertEqual(menu.get("id"),"kodi.core.main")
        self.items=menu.findall("item")
    def test_visible_even_without_verified_cross_provider_id(self):
        self.assertEqual(len(self.items),2)
        first,existing=self.items
        self.assertEqual(first.get("library"),"context.py")
        self.assertEqual(first.get("args"),"infinity-item-menu-v1")
        self.assertEqual(first.findtext("label"),"Infinity Tracked")
        expr=first.findtext("visible")
        self.assertIn("ListItem.FileNameAndPath,plugin://plugin.video.watchnixtoons2/",expr)
        self.assertIn("ListItem.Path,plugin://plugin.video.watchnixtoons2/",expr)
        self.assertNotIn("UniqueID",expr)
        self.assertNotIn("DBID",expr)
        self.assertNotIn("ListItem.DBTYPE",expr)
        self.assertEqual(existing.get("args"),"manage")
        self.assertEqual(existing.findtext("label"),"Infinity Trakt")
        self.assertNotEqual((first.get("library"),first.get("args")),
                            (existing.get("library"),existing.get("args")))
    def test_real_signed_2103404_title_popup_receives_exact_item(self):
        text=(ORIGINAL/"context.py").read_text()
        tree=ast.parse(text)
        functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)
                   and n.name in ("title_popup","main")]
        target="plugin://plugin.video.watchnixtoons2/?action=actionEpisodesMenu&url=https%3A%2F%2Fwww.wcostream.tv%2Fanime%2Fmob-psycho-100"
        item=Item(target)
        menu=Mock(return_value=True)
        context_argv=types.SimpleNamespace(argv=["context.py","infinity-item-menu-v1"],listitem=item)
        ns={"sys":context_argv,"xbmc":types.SimpleNamespace(getSkinDir=lambda:"skin.infinity.diggz"),
            "hub":types.SimpleNamespace(verified_ids=lambda supplied:{}),
            "_unverified_anime_menu":menu}
        modules={"infinity_trakt":types.SimpleNamespace(_bridge=Mock(),selected=Mock(),notice=Mock()),
                 "selection_contract":types.SimpleNamespace(read=lambda row:None)}
        with patch.dict(sys.modules,modules):
            exec(compile(ast.fix_missing_locations(ast.Module(functions,type_ignores=[])),
                         "context.py","exec"),ns)
            self.assertTrue(ns["main"]())
        menu.assert_called_once_with(item)
        self.assertEqual(item.getPath(),target)
    def test_no_provider_or_core_changes(self):
        self.assertFalse((PATCHED/"context.py").exists())
        self.assertFalse((PATCHED/"resume_hub.py").exists())
        self.assertFalse((PATCHED/"plugin.py").exists())
        self.assertIn("return _unverified_anime_menu(item)",(ORIGINAL/"context.py").read_text())
    def test_component_contract_versions(self):
        self.assertIn('ADDON_VERSION = "0.3.5.38"',(PATCHED/"checkpoint_runtime.py").read_text())
        trakt=(PATCHED/"infinity_trakt.py").read_text()
        self.assertIn("'script.infinity.commandcenter','0.3.5.38'",trakt)
        self.assertIn("'script.infinity.watchedbridge','1.0.19'",trakt)

if __name__=="__main__":unittest.main(verbosity=2)
