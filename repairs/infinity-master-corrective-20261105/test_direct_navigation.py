"""Installed-source boundaries are fixtures; actual route verifier executes."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as E

from test_navigation_drawer import nav,SKIN
import test_search_correction as search

ROUTER=b'''def router(argv2):
    action = argv2
    if action == 'movieNavigator':
        from resources.lib.menus import navigator
        navigator.Navigator().movies(folderName=folderName)
    elif action == 'tvNavigator':
        from resources.lib.menus import navigator
        navigator.Navigator().tvshows(folderName=folderName)
'''


class DirectNavigation(unittest.TestCase):
    def setUp(self):
        self.b=search.shipped.StateDiagnosis();self.b.setUp();self.addCleanup(self.b.doCleanups)
        self.provider=copy.deepcopy(self.b.provider)
        self.provider.update(id='plugin.video.umbrella',family='action-list-v1')
        self.router=self.b.root/'resources/lib/modules/router.py';self.router.parent.mkdir(parents=True)
        self.router.write_bytes(ROUTER)
        import hashlib
        self.provider['contract']['pins']['resources/lib/modules/router.py']=hashlib.sha256(ROUTER).hexdigest()
        self.calls=[];self.errors=[];self.enabled=True;self.eligibility=[]
        self.sport=self.b.root/'sport';self.sport.mkdir()
        self.details={'addonid':'plugin.video.sporthdme','enabled':True,'name':'SportHD','version':'0.1.92','path':'special://fixture/sport'}
        self.manifest='<addon id="plugin.video.sporthdme" name="SportHD" version="0.1.92" provider-name="Bugatsinho"><extension point="xbmc.python.pluginsource" library="default.py"/></addon>'
        (self.sport/'addon.xml').write_text(self.manifest);(self.sport/'default.py').write_text('# fixture entrypoint, never executed')
        def eligible(media,**kwargs):self.eligibility.append((media,kwargs));return [self.provider],[]
        self.source_reads=[]
        def source(root,name):self.source_reads.append((root,name));return (root/name).read_bytes()
        mock=patch.object(nav,'_provider_tools',return_value=(eligible,self.b.env['route'],source));mock.start();self.addCleanup(mock.stop)
        mock=patch.dict(sys.modules,xbmcvfs=SimpleNamespace(translatePath=lambda p:str(self.sport) if p=='special://fixture/sport' else p));mock.start();self.addCleanup(mock.stop)
    def executeJSONRPC(self,raw):
        req=json.loads(raw);self.calls.append(req)
        if req['method']=='GUI.ActivateWindow':return json.dumps({'result':'OK'})
        if req['method']=='Addons.GetAddonDetails':return json.dumps({'result':{'addon':self.details}})
        raise AssertionError(req)
    def getCondVisibility(self,name):
        self.assertEqual(name,'System.AddonIsEnabled(plugin.video.sporthdme)');return self.enabled
    def Dialog(self):return self
    def ok(self,*args):self.errors.append(args)
    def activated(self):return [r['params']['parameters'] for r in self.calls if r['method']=='GUI.ActivateWindow']

    def test_movies_and_tv_use_verified_umbrella_menus_once(self):
        for action,media,menu in [('movies','movie','movieNavigator'),('tv','tv','tvNavigator')]:
            with self.subTest(action=action):
                self.calls=[]
                self.assertTrue(nav.run(action,self,self))
                self.assertEqual(self.activated(),[['plugin://plugin.video.umbrella/?action='+menu,'return']])
                self.assertEqual(self.eligibility[-1],(media,dict(operation='title_navigation',force=True,provider_id='plugin.video.umbrella')))

    def test_no_other_provider_or_family_is_substituted(self):
        for key,value in [('id','plugin.video.other'),('family','other-family')]:
            original=self.provider[key];self.provider[key]=value
            self.assertFalse(nav.run('movies',self,self));self.assertEqual(self.activated(),[])
            self.provider[key]=original

    def test_changed_installed_router_and_source_pins_refuse_navigation(self):
        self.router.write_bytes(ROUTER.replace(b'.movies(',b'.different('))
        self.assertFalse(nav.run('movies',self,self));self.assertEqual(self.activated(),[])
        self.router.write_bytes(ROUTER)
        (self.b.root/'main.py').write_text('# changed pinned source')
        self.assertFalse(nav.run('movies',self,self));self.assertEqual(self.activated(),[])

    def test_disabled_inventory_provider_is_rejected_by_final_route_check(self):
        self.b.enabled=False
        self.assertFalse(nav.run('tv',self,self));self.assertEqual(self.activated(),[])

    def test_public_reference_router_matches_expected_dispatch_without_execution(self):
        raw=Path('/tmp/infinity-direct-reference-1.py').read_bytes()
        self.assertTrue(nav._umbrella_menu(raw,'movieNavigator','movies'))
        self.assertTrue(nav._umbrella_menu(raw,'tvNavigator','tvshows'))
        self.assertFalse(nav._umbrella_menu(raw,'movieNavigator','tvshows'))

    def test_sporthd_existing_manifest_and_entrypoint_open_only_provider_root(self):
        self.assertTrue(nav.run('sports',self,self))
        self.assertEqual(self.activated(),[['plugin://plugin.video.sporthdme/','return']])
        self.assertEqual([r['method'] for r in self.calls],['Addons.GetAddonDetails','GUI.ActivateWindow'])

    def test_sporthd_translated_root_uses_existing_source_readers_canonical_path(self):
        actual=self.sport
        alias=self.b.root/'android-path-alias';alias.symlink_to(actual,target_is_directory=True)
        self.sport=alias
        self.assertTrue(nav.run('sports',self,self))
        self.assertEqual([root for root,_ in self.source_reads],[actual.resolve(),actual.resolve()])

    def test_missing_disabled_wrong_identity_or_unverified_entrypoint_do_not_navigate(self):
        for key,value in [('enabled',False),('addonid','plugin.video.other'),('name','Different')]:
            original=self.details[key];self.details[key]=value
            self.assertFalse(nav.run('sports',self,self));self.assertEqual(self.activated(),[])
            self.details[key]=original
        self.enabled=False
        self.assertFalse(nav.run('sports',self,self));self.assertEqual(self.activated(),[])

    def test_manifest_version_race_wrong_library_and_missing_entrypoint_fail_closed(self):
        for old,new in [('0.1.92','0.1.93'),('default.py','other.py'),('Bugatsinho','Other')]:
            (self.sport/'addon.xml').write_text(self.manifest.replace(old,new))
            self.assertFalse(nav.run('sports',self,self));self.assertEqual(self.activated(),[])
        (self.sport/'addon.xml').write_text(self.manifest)
        (self.sport/'default.py').unlink()
        self.assertFalse(nav.run('sports',self,self));self.assertEqual(self.activated(),[])

    def test_drawer_goes_directly_through_existing_helper_and_preserves_loading_pairs(self):
        root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot()
        for cid,action in [('1198102','movies'),('1198103','tv')]:
            nodes=root.find(".//control[@id='%s']"%cid).findall('onclick')
            self.assertIn('RunScript(special://skin/resources/lib/infinity_library_navigation.py,'+action+')',[n.text for n in nodes])
            notifications=[n.text for n in nodes if (n.text or '').startswith('NotifyAll')]
            self.assertEqual(len(notifications),2)
            for n in notifications:self.assertIn('script.infinity.commandcenter,seamless.loading',n)


if __name__=='__main__':unittest.main(verbosity=2)
