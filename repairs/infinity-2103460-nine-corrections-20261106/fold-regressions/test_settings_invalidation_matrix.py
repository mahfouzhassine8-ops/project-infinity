"""Diagnostic-only Search settings-stamp matrix for frozen 86d5b5e2.

This test deliberately demonstrates a remaining FALSE REJECTION for an
illustrative provider bookkeeping write. A PASS is NOT a product-fix PASS.
No provider, Kodi, Android or actual plugin is invoked.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import types
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py'

def load_selected(names, env):
    raw = SOURCE.read_text()
    selected = [node for node in ast.parse(raw).body
                if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), env)
    return env

class Home:
    def __init__(self): self.properties = {}
    def getProperty(self, key): return self.properties.get(key, '')
    def setProperty(self, key, value): self.properties[key] = value

class Cancel:
    def iscanceled(self): return False

class Matrix(unittest.TestCase):
    def exercise(self, mutation):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = root/'profile'
            cc_profile = root/'commandcenter'
            addons = root/'addons'
            pid = 'plugin.video.watchnixtoons2'
            provider_root = addons/pid
            settings = profile/'addon_data'/pid/'settings.xml'
            settings.parent.mkdir(parents=True)
            provider_root.mkdir(parents=True)
            cc_profile.mkdir(parents=True)
            (provider_root/'addon.xml').write_text('<addon id="plugin.video.watchnixtoons2"/>')
            original = '<settings><setting id="searchHistory">none</setting><setting id="provider_mode">enabled</setting></settings>'
            settings.write_text(original)
            addon = types.SimpleNamespace(getAddonInfo=lambda field: {'profile':str(cc_profile),'version':'0.3.5.61'}[field])
            env = dict(Path=Path, hashlib=hashlib, json=json, time=time,
                xbmcvfs=types.SimpleNamespace(translatePath=lambda key: str(profile) if key=='special://profile' else key),
                xbmcaddon=types.SimpleNamespace(Addon=lambda _:addon),
                _query_cache_entries=lambda raw,now:[],
                _VisibleCancellation=lambda *args:None,
                _remember_query_answer=lambda *args:None,
                _state_rejection_trace=lambda *args:None)
            load_selected(('_query_file_stamp','_query_signature','_provider_result'),env)
            provider = dict(id=pid, name='WatchNixtoons2', root=str(provider_root),
                            contract=dict(pins={},dependencies=[]))
            path = 'plugin://'+pid+'/?action=actionSearchMenu&searchType=series&query=Re%3AZero'
            env['route'] = lambda p,q:path
            files = [dict(file='plugin://'+pid+'/?action=title&id='+str(i),
                          label='Synthetic title') for i in range(31)]
            def native(directory, home, progress):
                if mutation=='bookkeeping':
                    settings.write_text(original.replace('none','example history'))
                elif mutation=='meaningful':
                    settings.write_text(original.replace('enabled','disabled'))
                elif mutation=='aba':
                    settings.write_text(original.replace('enabled','disabled'))
                    settings.write_text(original)
                    stamp = settings.stat()
                    os.utime(settings,ns=(stamp.st_atime_ns,stamp.st_mtime_ns+1000000000))
                return 'completed', {'result':{'files':files}}
            env['_leased_directory'] = native
            return env['_provider_result'](provider,'Re:Zero',Home(),Cancel())

    def test_no_settings_mutation_preserves_31_rows(self):
        provider,status,answer,path=self.exercise('none')
        self.assertEqual(status,'completed')
        self.assertEqual(len(answer['result']['files']),31)

    def test_known_gap_harmless_bookkeeping_write_rejects_31_legitimate_rows(self):
        provider,status,answer,path=self.exercise('bookkeeping')
        self.assertEqual(status,'state_changed')
        self.assertEqual(answer,{})
        print('KNOWN PRODUCT GAP: representative harmless settings write discards 31 synthetic rows')

    def test_meaningful_settings_change_stays_rejected(self):
        provider,status,answer,path=self.exercise('meaningful')
        self.assertEqual(status,'state_changed')
        self.assertEqual(answer,{})

    def test_observed_intermediate_aba_rewrite_stays_rejected(self):
        provider,status,answer,path=self.exercise('aba')
        self.assertEqual(status,'state_changed')
        self.assertEqual(answer,{})
        print('LIMIT: metadata catches this observed ABA fixture, not every unobserved external rewrite')

if __name__=='__main__':
    unittest.main(verbosity=2)
