"""Exact-source onload equivalence and protected-source boundaries, not device timing."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import patch_playlist_home as change


class PlaylistHomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apk=Path(os.environ['INFINITY_PLAYLIST_PARENT_APK'])
        with ZipFile(apk) as z:
            cls.before={n[len(change.PREFIX):]:z.read(n) for n in z.namelist()
                        if n.startswith(change.PREFIX) and not n.endswith('/')}
        cls.after,cls.proof=change.skin_sources(cls.before)

    def test_absent_provider_native_output_matches_original_helper_and_invalidates_stale_request(self):
        values={'Infinity.Playlist.TVPath':'stale','Infinity.Playlist.SportsPath':'stale',
                'Infinity.Playlist.Request':'old-inflight','Infinity.Playlist.Ready':'old'}
        def setp(key,value):values[key]=value
        def clear(key):values.pop(key,None)
        home=SimpleNamespace(setProperty=setp,clearProperty=clear,getProperty=lambda k:values.get(k,''))
        fake={'xbmc':SimpleNamespace(getSkinDir=lambda:change.SKIN,getCondVisibility=lambda q:False,log=lambda *a:None,LOGINFO=1),
              'xbmcaddon':SimpleNamespace(Addon=lambda *a:(_ for _ in ()).throw(AssertionError('Absent provider must not construct Addon'))),
              'xbmcgui':SimpleNamespace(Window=lambda w:home),'xbmcvfs':SimpleNamespace(),
              'infinity_playlist_registry':SimpleNamespace(PROVIDER=change.PROVIDER,ROOT='plugin://'+change.PROVIDER+'/',resolve=lambda *a:None)}
        scope={'__name__':'test_exact_helper','__file__':'/verified/skin/resources/lib/infinity_playlist_routes.py'}
        with patch.dict(sys.modules,fake):
            exec(compile(self.before['resources/lib/infinity_playlist_routes.py'],scope['__file__'],'exec'),scope)
            scope['main']()
        original=dict(values);values.clear();values.update({'Infinity.Playlist.Request':'old-inflight','Infinity.Playlist.Ready':'old'})
        clear('Infinity.Playlist.Ready')  # Original unconditional first Home action.
        for action in change.ABSENT_ACTIONS:
            function,args=action.split('(',1);parts=args[:-1].split(',')
            self.assertEqual(parts[-1],'Home')
            if function=='ClearProperty':clear(parts[0])
            elif function=='SetProperty':setp(parts[0],parts[1])
            else:self.fail('Unexpected native action')
        # The request token is an internal stale-publication fence, not UI data.
        self.assertNotIn('Infinity.Playlist.Request',values)
        self.assertTrue(original['Infinity.Playlist.Request'])
        original.pop('Infinity.Playlist.Request')
        self.assertEqual({k:values.get(k,'') for k in set(values)|set(original)},
                         {k:original.get(k,'') for k in set(values)|set(original)})
        self.assertEqual(change.ABSENT_ACTIONS[-1],'SetProperty(Infinity.Playlist.Ready,v1,Home)')

    def test_every_profile_keeps_installed_script_and_exact_inverse(self):
        homes=[n for n in self.before if n.endswith('/Home.xml')]
        self.assertEqual(len(homes),14)
        for name in homes:
            revised=self.after[name].decode()
            self.assertEqual(revised.replace(change.NEW,change.OLD,1),self.before[name].decode())
            root=ET.fromstring(revised)
            scripts=[node for node in root.findall('onload') if node.text=='RunScript(special://skin/resources/lib/infinity_playlist_routes.py)']
            self.assertEqual(len(scripts),1);self.assertEqual(scripts[0].get('condition'),change.PRESENT)
            absent=[node.text for node in root.findall('onload') if node.get('condition')=='!'+change.PRESENT]
            self.assertEqual(absent,change.ABSENT_ACTIONS)
        self.assertEqual(self.proof['changed_members'],sorted(homes+['addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json']))
        self.assertEqual(self.after['resources/lib/infinity_playlist_routes.py'],self.before['resources/lib/infinity_playlist_routes.py'])

    def test_changed_source_missing_profile_or_protected_pin_refused(self):
        for bad in (dict(self.before,**{'16x9/Home.xml':self.before['16x9/Home.xml']+b' '}),
                    {n:v for n,v in self.before.items() if n!='16x9/Home.xml'},
                    dict(self.before,**{'resources/lib/infinity_playlist_routes.py':b'changed'})):
            with self.assertRaises(ValueError):change.skin_sources(bad)
        protected=json.loads(self.after['Infinity-Protected-Manifest.json'])
        self.assertEqual(len(protected['protected_files']),942)
        self.assertTrue(all(change.digest(self.after[n])==pin for n,pin in protected['protected_files'].items()))
        self.assertFalse(protected['candidate_locked'])


if __name__=='__main__':unittest.main(verbosity=2)
