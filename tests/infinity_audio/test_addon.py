#!/usr/bin/env python3
"""One-shot utility behavior with mocked Kodi UI; no device runtime claim."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[2]

class PolicyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'infinity-audio-policy.json'
  self.messages=[];self.choice=0;self.playing=False;self.api='1'
  dialog=SimpleNamespace(ok=lambda *v:self.messages.append(v),textviewer=lambda *v:self.messages.append(v),select=lambda *v:self.choice)
  sys.modules['xbmc']=SimpleNamespace(Player=lambda:SimpleNamespace(isPlaying=lambda:self.playing),log=lambda *v:None,LOGERROR=1)
  sys.modules['xbmcgui']=SimpleNamespace(Dialog=lambda:dialog,Window=lambda *a:SimpleNamespace(getProperty=lambda *a:self.api))
  sys.modules['xbmcvfs']=SimpleNamespace(translatePath=lambda v:str(self.path))
  spec=importlib.util.spec_from_file_location('policy_addon',ROOT/'addons/script.infinity.audiopolicy/default.py')
  self.addon=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.addon)
 def tearDown(self):self.temp.cleanup()
 def test_auto(self):
  self.addon.main();self.assertEqual(json.loads(self.path.read_text()),self.addon.AUTO)
 def test_legacy(self):
  self.choice=1;self.addon.main();self.assertEqual(json.loads(self.path.read_text()),self.addon.LEGACY)
 def test_paused_or_playing_blocked(self):
  self.playing=True;self.addon.main();self.assertFalse(self.path.exists());self.assertIn('Stop playback first',str(self.messages))
 def test_missing_api_no_write(self):
  self.api='';self.addon.main();self.assertFalse(self.path.exists())
 def test_cancel_no_write(self):
  self.choice=-1;self.addon.main();self.assertFalse(self.path.exists())
 def test_replace_atomic_and_no_temporary_files(self):
  self.addon.write_policy(str(self.path),self.addon.LEGACY);self.addon.write_policy(str(self.path),self.addon.AUTO)
  self.assertEqual(list(Path(self.temp.name).iterdir()),[self.path]);self.assertEqual(json.loads(self.path.read_text()),self.addon.AUTO)
 def test_play_started_during_dialog_blocked(self):
  def select(*v):self.playing=True;return 0
  sys.modules['xbmcgui'].Dialog=lambda:SimpleNamespace(select=select,ok=lambda *v:self.messages.append(v))
  self.addon.main();self.assertFalse(self.path.exists())

if __name__=='__main__':unittest.main()
