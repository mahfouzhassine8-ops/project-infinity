"""Read-only native Umbrella/POV route recognition regressions.

Run against exact publicly published input archives downloaded to a disposable
GitHub runner. No provider code imports, execution, user profile or APK edit.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT/'repairs/infinity-only-performance-2103425/overlay/script.infinity.commandcenter/native_search_compatibility.py'
spec = importlib.util.spec_from_file_location("native_search_compatibility", HELPER)
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)

POV = Path(os.environ["POV_ARCHIVE"])
UMBRELLA = Path(os.environ["UMBRELLA_ROOT"])
POV_ROOT = "plugin.video.pov/"


def contract(kind):
    if kind == "umbrella":
        return {
            "family": "action-list-v1", "entrypoint": "umbrella.py",
            "search": {
                "movie": {"params":{"action":"movieSearchterm"},"query_key":"name"},
                "tv": {"params":{"action":"tvSearchterm"},"query_key":"name"}}
        }
    return {
        "family": "mode-list-v1", "entrypoint":"resources/lib/router.py",
        "search": {
            "movie":{"params":{"mode":"build_movie_list","action":"tmdb_movies_search"},"query_key":"query"},
            "tv":{"params":{"mode":"build_tvshow_list","action":"tmdb_tv_search"},"query_key":"query"}}
    }


def fixtures():
    with ZipFile(POV) as z:
        pov={n.removeprefix(POV_ROOT):z.read(n) for n in z.namelist()
             if n.startswith(POV_ROOT) and not n.endswith("/") and
             n.endswith((".py","addon.xml")) and z.getinfo(n).file_size <= 512*1024}
    umb={p.relative_to(UMBRELLA).as_posix():p.read_bytes()
         for p in UMBRELLA.rglob("*.py")}
    return pov,umb


class NativeRouteCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pov, cls.umbrella=fixtures()
        assert len(cls.pov)>=5
        assert set(("umbrella.py","resources/lib/modules/router.py",
                    "resources/lib/menus/movies.py",
                    "resources/lib/menus/tvshows.py"))<=cls.umbrella.keys()

    def invoke(self,kind, modifications=None, specs=None):
        files=dict(self.umbrella if kind=="umbrella" else self.pov)
        if modifications:
            for name, update in modifications.items():
                if callable(update):
                    files[name]=update(files[name])
                elif update is None:
                    files.pop(name,None)
                else:
                    files[name]=update
        consulted=[]
        def reader(path):
            consulted.append(path)
            return files[path]
        active_spec=specs or contract(kind)
        result=compat.recognize('plugin.video.'+kind,Path("/read-only/"+kind),
                                [active_spec],reader)
        if kind == "pov" and len(result) < 2 and not modifications:
            for media in ("movie","tv"):
                get,pins=compat._reading(reader)
                try:
                    compat._pov(get,active_spec["search"][media],media)
                except Exception as error:
                    print("POV_HOST_DIAGNOSTIC",media,type(error).__name__,str(error))
                    import ast
                    src=ast.parse(files["resources/lib/menus/"+("movies" if media=="movie" else "tvshows")+".py"])
                    for item in src.body:
                        if isinstance(item,ast.ClassDef) and item.name=="Menu":
                            for node in item.body:
                                if isinstance(node,ast.FunctionDef) and node.name=="run":
                                    for branch in ast.walk(node):
                                        if isinstance(branch,ast.If) and isinstance(branch.test,ast.Compare):
                                            if ("tmdb_movies_search" if media=="movie" else "tmdb_tv_search") in ast.unparse(branch.test):
                                                print("POV_SEARCH_BRANCH_SOURCE",media,ast.unparse(branch)[:1200])
        return result,files,consulted

    def test_umbrella_current_natural_movie_and_tv_routes_both_recognized(self):
        a,files,consulted=self.invoke("umbrella")
        self.assertEqual(set(a),{("movie","search"),("tv","search")})
        for media in ("movie","tv"):
            row=a[(media,"search")]["contract"]
            self.assertEqual(row["params"],contract("umbrella")["search"][media]["params"])
            self.assertEqual(row["query_key"],"name")
            self.assertTrue(all(hashlib.sha256(files[k]).hexdigest()==v
                                for k,v in row["pins"].items()))
            self.assertNotIn("resources/lib/modules/control.py",row["pins"])

    def test_pov_current_natural_movie_and_tv_routes_both_recognized(self):
        a,files,consulted=self.invoke("pov")
        self.assertEqual(set(a),{("movie","search"),("tv","search")})
        for media in ("movie","tv"):
            row=a[(media,"search")]["contract"]
            self.assertEqual(row["params"],contract("pov")["search"][media]["params"])
            self.assertEqual(row["query_key"],"query")
            self.assertTrue(all(hashlib.sha256(files[k]).hexdigest()==v
                                for k,v in row["pins"].items()))
            self.assertNotIn("resources/lib/indexers/metadata.py",row["pins"])

    def test_unrelated_umbrella_menu_updates_do_not_remove_native_search(self):
        a,_,_=self.invoke("umbrella",{
            "resources/lib/menus/movies.py":lambda b:b+b"\n# compatible update\n"})
        self.assertEqual(set(a),{("movie","search"),("tv","search")})

    def test_unrelated_pov_extra_route_does_not_break_native_search(self):
        def add_extra(raw):
            token=b"POV_ROUTES = {"
            assert raw.count(token)==1
            return raw.replace(token,token+b"\n    'unrelated_future': lambda p: 42,",1)
        a,_,_=self.invoke("pov",{"resources/lib/modules/entry.py":add_extra})
        self.assertEqual(set(a),{("movie","search"),("tv","search")})

    def test_changed_umbrella_movie_search_destination_is_rejected_isolated(self):
        def change(raw):
            before=b"movies.Movies().search_term(name)"
            assert raw.count(before)==1
            return raw.replace(before,b"movies.Movies().open_other(name)")
        a,_,_=self.invoke("umbrella",{"resources/lib/modules/router.py":change})
        self.assertNotIn(("movie","search"),a)
        self.assertIn(("tv","search"),a)

    def test_changed_pov_movie_mode_destination_rejected_independently(self):
        def change(raw):
            before=b"_import('menus.movies', 'Menu')(p).run()"
            assert raw.count(before)==1
            return raw.replace(before,b"_import('menus.other', 'Menu')(p).run()")
        a,_,_=self.invoke("pov",{"resources/lib/modules/entry.py":change})
        self.assertNotIn(("movie","search"),a)
        self.assertIn(("tv","search"),a)

    def test_umbrella_wrong_query_key_is_not_recognized(self):
        altered=contract("umbrella")
        altered["search"]["movie"]["query_key"]="title"
        a,_,_=self.invoke("umbrella",specs=altered)
        self.assertNotIn(("movie","search"),a)
        self.assertIn(("tv","search"),a)

    def test_pov_wrong_mode_is_not_recognized(self):
        altered=contract("pov")
        altered["search"]["movie"]["params"]["mode"]="build_episode_list"
        a,_,_=self.invoke("pov",specs=altered)
        self.assertNotIn(("movie","search"),a)
        self.assertIn(("tv","search"),a)

    def test_duplicate_pov_mode_keys_do_not_get_granted(self):
        def duplicate(raw):
            old=b"'build_movie_list': lambda p:"
            assert raw.count(old)==1
            return raw.replace(old,old+b" _import('menus.movies', 'Menu')(p).run(),\n"+
                               old,1)
        a,_,_=self.invoke("pov",{"resources/lib/modules/entry.py":duplicate})
        self.assertEqual(a,{})

    def test_missing_pov_routing_module_stays_unverified(self):
        a,_,_=self.invoke("pov",{"resources/lib/modules/entry.py":None})
        self.assertEqual(a,{})

    def test_unsupported_family_or_random_provider_code_never_granted(self):
        a,_,_=self.invoke("umbrella",specs={"family":"unknown-provider","entrypoint":"umbrella.py",
                                            "search":contract("umbrella")["search"]})
        self.assertEqual(a,{})

    def test_same_source_hash_pinned_then_changed_bytes_detectable_at_dispatch(self):
        a,files,_=self.invoke("pov")
        pins=a[("movie","search")]["contract"]["pins"]
        path="resources/lib/modules/entry.py"
        self.assertEqual(pins[path],hashlib.sha256(files[path]).hexdigest())
        files[path]+=b"\n# modified after verification"
        self.assertNotEqual(pins[path],hashlib.sha256(files[path]).hexdigest())

    def test_no_navigation_or_identity_granted_to_search_only_fallback(self):
        for kind in ("umbrella","pov"):
            with self.subTest(kind=kind):
                a,_,_=self.invoke(kind)
                self.assertEqual({op for m,op in a},{"search"})

if __name__=="__main__":
    unittest.main(verbosity=2)
