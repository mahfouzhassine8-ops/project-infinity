"""Actual signed source comparisons and dispatch tests; no fake trust acceptance.

Function execution below isolates the real direct_command from its AST. It does
NOT execute or mock-pass the authenticated bootstrap/Android native loader.
"""
import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as E

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SIGNED=Path('/tmp/infinity-signed456-payload-audit/assets/addons')
CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter'
SKIN=ROOT/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz'
sys.path.insert(0,str(CC.parents[3]))
sys.path.insert(0,str(ROOT/'repairs/infinity-master-corrective-20261105'))
import test_direct_navigation as prior
spec=importlib.util.spec_from_file_location('corrective_navigation_entry',CC/'library_navigation.py')
nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)

class EntryPreservation(unittest.TestCase):
    def test_only_five_callback_strings_change_and_all_drawer_geometry_survives(self):
        old=(SIGNED/'skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml').read_bytes()
        expected=old
        for action in ('movies','tv','sports','browse','downloads'):
            before=('RunScript(special://skin/resources/lib/infinity_library_navigation.py,'+action+')').encode()
            after=('RunScript(script.infinity.commandcenter,library-navigation,'+action+')').encode()
            self.assertEqual(expected.count(before),1)
            expected=expected.replace(before,after,1)
        self.assertEqual(expected,(SKIN/'unified/Custom_1198_InfinityNav.xml').read_bytes())
        # This exact comparison includes initial height, Power, scroll/focus,
        # loading notifications, Favorites, native libraries and Media Sources.

    def test_bootstrap_and_every_previous_command_remain_byte_identical(self):
        old=(SIGNED/'script.infinity.commandcenter/default.py').read_bytes()
        candidate=(CC/'default.py').read_bytes()
        addition=b"    if action == 'library-navigation':\n        from library_navigation import run\n        run(argv[2].strip().lower() if len(argv) > 2 else '', xbmc, xbmcgui)\n        return True\n"
        self.assertEqual(candidate.count(addition),1)
        self.assertEqual(candidate.replace(addition,b'',1),old)
        compile(candidate,str(CC/'default.py'),'exec')

    def test_existing_guarded_routes_are_copied_exactly_without_weakened_checks(self):
        self.assertEqual((CC/'library_navigation.py').read_bytes(),
                         (SIGNED/'skin.infinity.diggz/resources/lib/infinity_library_navigation.py').read_bytes())
        self.assertEqual((SKIN/'resources/lib/infinity_library_navigation.py').read_bytes(),
                         (SIGNED/'skin.infinity.diggz/resources/lib/infinity_library_navigation.py').read_bytes())

    def test_visible_controls_reach_one_registered_entry_and_native_destinations(self):
        root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot()
        ids={'1198102':'movies','1198103':'tv','1198110':'sports','1198112':'browse','1198113':'downloads'}
        for cid,action in ids.items():
            c=root.find('.//control[@id="'+cid+'"]')
            self.assertIsNotNone(c,cid)
            self.assertIn('RunScript(script.infinity.commandcenter,library-navigation,'+action+')',
                          [n.text for n in c.findall('onclick')])
        manifest=E.parse(SIGNED/'script.infinity.commandcenter/addon.xml').getroot()
        self.assertEqual(manifest.find('extension[@point="xbmc.python.script"]').get('library'),'default.py')
        fav=root.find('.//control[@id="1198301"]')
        self.assertIn('ActivateWindow(favouritesbrowser)',[n.text for n in fav.findall('onclick')])

class EntryDispatch(prior.DirectNavigation):
    def setUp(self):
        # Reuse existing provider safety fixtures, against the NEW module.
        p=patch.object(prior,'nav',nav);p.start();self.addCleanup(p.stop)
        super().setUp()

    def test_drawer_goes_directly_through_existing_helper_and_preserves_loading_pairs(self):
        root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot()
        for cid,action in [('1198102','movies'),('1198103','tv')]:
            callbacks=root.find('.//control[@id="'+cid+'"]').findall('onclick')
            self.assertIn('RunScript(script.infinity.commandcenter,library-navigation,'+action+')',[c.text for c in callbacks])
            self.assertEqual(len([c for c in callbacks if c.text.startswith('NotifyAll')]),2)

    def test_default_dispatch_executes_same_routes_and_never_opens_command_menu(self):
        tree=ast.parse((CC/'default.py').read_bytes())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='direct_command')
        env=dict(xbmc=self,xbmcgui=self)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-default-dispatch','exec'),env)
        with patch.dict(sys.modules,library_navigation=nav):
            for action,expected in [('movies','plugin://plugin.video.umbrella/?action=movieNavigator'),
                                    ('tv','plugin://plugin.video.umbrella/?action=tvNavigator'),
                                    ('sports','plugin://plugin.video.sporthdme/'),('browse','files')]:
                self.calls=[]
                self.assertTrue(env['direct_command'](['default.py','library-navigation',action]))
                self.assertEqual(self.activated(),[[expected,'return']])
            self.calls=[];self.provider['id']='plugin.video.unexpected'
            self.assertTrue(env['direct_command'](['default.py','library-navigation','movies']))
            self.assertEqual(self.activated(),[])
            self.assertTrue(self.errors)

if __name__=='__main__':unittest.main(verbosity=2)
