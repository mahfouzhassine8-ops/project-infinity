"""Actual resident service/common/hub/plugin integration with Kodi API doubles."""
import copy
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--runtime', required=True, help='Actual Command Center source directory under test')
arguments, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0]] + remaining
RUNTIME = Path(arguments.runtime).resolve(strict=True)
sys.path.insert(0, str(RUNTIME))
PROFILE = None
RPC = []
RPC_FAILURE = False
RPC_PLAYCOUNT = 0


class Window:
    properties = {}
    def __init__(self, number=10000): self.number = number
    def getProperty(self, key): return self.properties.get(key, '')
    def setProperty(self, key, value): self.properties[key] = str(value)
    def clearProperty(self, key): self.properties.pop(key, None)
    def getFocusId(self): return 0


class Player:
    def __init__(self): self.playing = True; self.position = 417.125; self.duration = 900.0
    def isPlaying(self): return self.playing
    def isPlayingVideo(self): return self.playing
    def getTime(self): return self.position
    def getTotalTime(self): return self.duration


class Monitor:
    def __init__(self): pass
    def abortRequested(self): return False
    def waitForAbort(self, seconds): return False


class Addon:
    settings = {}
    version = '0.3.5.19'
    def __init__(self, *args): pass
    def getAddonInfo(self, name): return {'profile': str(PROFILE), 'version': self.version, 'icon': ''}.get(name, '')
    def getSetting(self, key): return self.settings.get(key, '')
    def setSetting(self, key, value): self.settings[key] = value


class Dialog:
    before_selection = None
    def notification(self, *args, **kwargs): pass
    def select(self, *args, **kwargs):
        if self.before_selection: self.before_selection()
        return 4
    def input(self, *args, **kwargs): return 'List'


def rpc(raw):
    global RPC_PLAYCOUNT
    payload = json.loads(raw)
    RPC.append(payload)
    if payload['method'].startswith('VideoLibrary.Set') and RPC_FAILURE:
        return json.dumps({'error': {'message': 'injected database failure'}})
    if payload['method'] in ('VideoLibrary.GetMovieDetails', 'VideoLibrary.GetEpisodeDetails'):
        field = 'moviedetails' if payload['method'].endswith('MovieDetails') else 'episodedetails'
        return json.dumps({'result': {field: {'playcount': RPC_PLAYCOUNT}}})
    if payload['method'].startswith('VideoLibrary.Set'):
        RPC_PLAYCOUNT = payload['params']['playcount']
    return json.dumps({'result': 'OK'})


xbmc = types.ModuleType('xbmc')
xbmc.Player, xbmc.Monitor = Player, Monitor
xbmc.LOGINFO, xbmc.LOGWARNING, xbmc.LOGERROR = 1, 2, 3
xbmc.log = lambda *args: None
xbmc.getSkinDir = lambda: 'skin.infinity.diggz'
xbmc.getInfoLabel = lambda key: ''
xbmc.getCondVisibility = lambda key: False
xbmc.executebuiltin = lambda *args: None
xbmc.executeJSONRPC = rpc
gui = types.ModuleType('xbmcgui')
gui.Window, gui.Dialog = Window, Dialog
gui.NOTIFICATION_INFO = 'info'
gui.NOTIFICATION_WARNING = 'warning'
gui.getCurrentWindowId = lambda: 10000
gui.getCurrentWindowDialogId = lambda: 9999
addon = types.ModuleType('xbmcaddon'); addon.Addon = Addon
vfs = types.ModuleType('xbmcvfs'); vfs.translatePath = lambda path: str(PROFILE) if path.startswith('special://profile') else path
plugin_api = types.ModuleType('xbmcplugin')
plugin_api.endOfDirectory = lambda *args, **kwargs: None
for name, module in [('xbmc', xbmc), ('xbmcgui', gui), ('xbmcaddon', addon), ('xbmcvfs', vfs), ('xbmcplugin', plugin_api)]:
    sys.modules[name] = module

import checkpoint_runtime as runtime
import common
import resume_hub as hub
import service
import experience
old_argv = sys.argv
sys.argv = ['plugin.py', '1', '']
import plugin
sys.argv = old_argv

OWNER = 'native-engine-owner-token-123456'
SESSION = 'native-checkpoint-session-123456'
KEY = 'a' * 64


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        global PROFILE, RPC_FAILURE, RPC_PLAYCOUNT
        self.temp = tempfile.TemporaryDirectory()
        PROFILE = Path(self.temp.name)
        self.profile = PROFILE
        self.control = PROFILE / '.android-checkpoint'; self.control.mkdir()
        runtime.durable_json(self.control / 'engine.json', {'schema': 1, 'native_api': 1, 'pid': os.getpid(), 'owner': OWNER})
        runtime._stores.clear(); RPC.clear(); RPC_FAILURE = False; RPC_PLAYCOUNT = 0
        Window.properties.clear(); Addon.settings.clear(); Addon.version = '0.3.5.19'
        plugin.PROFILE = self.profile
        self.player = service.InfinityPlayer(self.profile)
        self.player.key, self.player.readable = 'audio-key', 'movie'
        self.player.cw_key = KEY
        self.player.cw_item = {'key': KEY, 'media': 'movie', 'dbid': 42, 'title': 'Movie', 'label': 'Movie'}
        self.experience = experience.ExperienceController(self.profile, self.player, {
            'xbmc': xbmc, 'gui': gui, 'read': common.read_json, 'atomic': common.atomic_json,
            'bool': common.setting_bool, 'str': common.setting_str, 'set': service._set,
            'progress_lock': service.PROGRESS_LOCK, 'load_continue': service._load_continue,
            'save_continue': service._save_continue, 'rpc': common.jsonrpc})
        self.stability = service.StabilityController.__new__(service.StabilityController)
        self.stability.profile = self.profile
        common.atomic_json(self.profile / 'boot-marker.json', {'stage': 'ready'})
        self.checkpoint = runtime.ResidentCheckpoint(self.profile, self.player, self.experience, self.stability, {
            'version': lambda: Addon.version, 'live': lambda: False, 'enabled': common.setting_bool,
            'hub': hub, 'publish': service._publish_resume_hub, 'log': lambda message: None,
            'player_properties': lambda: {'currentaudiostream': {'index': 0, 'language': 'eng'},
                                         'currentsubtitle': {}, 'subtitleenabled': False, 'speed': 0},
            'progress_lock': service.PROGRESS_LOCK})
        self.player.shutdown_checkpoint = self.checkpoint
        self.monitor = service.CheckpointMonitor(self.checkpoint)

    def tearDown(self):
        runtime._stores.clear()
        Dialog.before_selection = None
        self.temp.cleanup()

    def request(self, phase, **extra):
        runtime.durable_json(self.control / 'request.json', dict(schema=1, pid=os.getpid(), owner=OWNER,
                             session=SESSION, phase=phase, **extra))

    def response(self):
        return json.loads((self.control / 'response.json').read_text())

    def prepare(self):
        self.request('PREPARE')
        self.assertTrue(self.checkpoint.poll())
        self.assertEqual(self.response()['status'], 'PLAYBACK_CHECKPOINTED')

    def marker(self):
        self.monitor.onNotification('Infinity', 'Other.InfinityCheckpointDrain',
                                    json.dumps({'pid': os.getpid(), 'owner': OWNER, 'session': SESSION}))

    def test_actual_player_state_saved_and_frozen_player_can_remain_alive(self):
        self.prepare()
        saved = hub.load(self.profile)
        self.assertEqual(saved['items'][KEY]['position'], 417.125)
        memory = common.read_json(self.profile / 'playback-memory.json', {})
        self.assertFalse(memory['titles']['audio-key']['subtitle_enabled'])
        final_resume_bytes = (self.profile / 'continue-watching.json').read_bytes()
        self.request('FINALIZE', player_freeze_complete=True)
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PLAYBACK_CHECKPOINTED')
        self.marker(); self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PARTICIPANT_COMPLETE')
        self.assertFalse(self.response()['global_safe_to_terminate'])
        self.assertTrue(self.player.isPlaying())
        self.assertFalse((self.profile / 'boot-marker.json').exists())
        self.assertEqual((self.profile / 'continue-watching.json').read_bytes(), final_resume_bytes)

    def test_pending_real_ended_callback_removes_resume_and_commits_watched(self):
        self.prepare()
        self.player.onPlayBackEnded()
        self.player.onPlayBackEnded()  # duplicate callbacks must not duplicate playcount
        self.marker(); self.request('FINALIZE', player_freeze_complete=True)
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PARTICIPANT_COMPLETE')
        data = hub.load(self.profile)
        self.assertNotIn(KEY, data['items'])
        self.assertEqual(data['watched'][KEY]['play_count'], 1)
        self.assertFalse(data.get('pending_kodi_sync'))
        self.assertTrue(any(p['method'] == 'VideoLibrary.SetMovieDetails' for p in RPC))

    def test_failed_kodi_watched_commit_blocks_completion(self):
        global RPC_FAILURE
        self.prepare(); self.player.onPlayBackEnded(); RPC_FAILURE = True
        self.marker(); self.request('FINALIZE', player_freeze_complete=True)
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'CHECKPOINT_FAILED')
        self.assertTrue(hub.load(self.profile)['pending_kodi_sync'])

    def test_ended_callback_queued_after_clock_release_retains_watched_identity(self):
        self.player.persist_continue(force=False)
        self.player.playing = False
        self.prepare()
        self.player.onPlayBackEnded()
        self.marker(); self.request('FINALIZE', player_freeze_complete=True)
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PARTICIPANT_COMPLETE')
        self.assertIn(KEY, hub.load(self.profile)['watched'])
        self.assertNotIn(KEY, hub.load(self.profile)['items'])

    def test_missing_clock_for_pending_stop_does_not_claim_resume_saved(self):
        self.player.persist_continue(force=False)
        self.player.playing = False
        self.prepare()
        self.player.onPlayBackStopped()
        self.marker(); self.request('FINALIZE', player_freeze_complete=True)
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'CHECKPOINT_FAILED')

    def test_existing_native_playcount_is_not_reset_or_incremented_again(self):
        global RPC_PLAYCOUNT
        RPC_PLAYCOUNT = 7  # Already committed by the native frozen-player owner.
        self.prepare(); self.player.onPlayBackEnded()
        self.marker(); self.request('FINALIZE', player_freeze_complete=True)
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PARTICIPANT_COMPLETE')
        self.assertEqual(RPC_PLAYCOUNT, 7)
        self.assertFalse(any(p['method'].startswith('VideoLibrary.Set') for p in RPC))

    def test_nonseekable_stream_has_no_required_resume_clock(self):
        self.player.duration = 0.0
        self.player.cw_item = None; self.player.cw_key = None
        self.checkpoint.api['player_properties'] = lambda: {'speed': 0, 'canseek': False, 'subtitleenabled': False}
        self.prepare(); self.marker(); self.request('FINALIZE', player_freeze_complete=True)
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PARTICIPANT_COMPLETE')
        self.assertEqual(self.checkpoint.snapshot['resume_exclusion'], 'unseekable-without-duration')

    def test_seekable_video_missing_clock_fails_instead_of_guessing(self):
        self.player.duration = 0.0
        self.checkpoint.api['player_properties'] = lambda: {'speed': 0, 'canseek': True, 'subtitleenabled': False}
        self.request('PREPARE'); self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'CHECKPOINT_FAILED')

    def test_actual_plugin_mutations_and_common_writes_are_fenced(self):
        self.prepare()
        before = (self.profile / 'continue-watching.json').read_bytes()
        plugin.PARAMS = {'op': 'mark-watched', 'key': KEY}
        plugin.mutate()
        self.assertEqual((self.profile / 'continue-watching.json').read_bytes(), before)
        with self.assertRaises(runtime.AdmissionClosed):
            common.atomic_json(self.profile / 'session.json', {'new': 'not admitted'})

    def test_plugin_dialog_reloads_progress_written_during_user_input(self):
        self.player.persist_continue(force=False)
        def while_dialog_open():
            self.player.position = 444.0
            self.player.cw_last_save = 0
            self.player.persist_continue(force=False)
        Dialog.before_selection = staticmethod(while_dialog_open)
        plugin.PARAMS = {'op': 'rate', 'key': KEY}
        plugin.mutate()
        data = hub.load(self.profile)
        self.assertEqual(data['items'][KEY]['position'], 444.0)
        self.assertEqual(data['ratings'][KEY]['rating'], 4)

    def test_unknown_version_never_registers_active_or_receipt(self):
        Addon.version = '9.9.9'
        self.request('PREPARE')
        self.assertFalse(self.checkpoint.poll())
        self.assertFalse((self.control / 'active.json').exists())
        self.assertFalse((self.control / 'response.json').exists())

    def test_wrong_session_marker_cannot_complete(self):
        self.prepare(); self.request('FINALIZE', player_freeze_complete=True)
        self.monitor.onNotification('Infinity', 'Other.InfinityCheckpointDrain',
            json.dumps({'pid': os.getpid(), 'owner': OWNER, 'session': 'wrong-session-123456'}))
        self.checkpoint.poll()
        self.assertEqual(self.response()['status'], 'PLAYBACK_CHECKPOINTED')

    def test_actual_service_loop_parks_normal_observers_and_keeps_callback_pump(self):
        self.request('PREPARE')
        class ExitAfterCheckpoint(service.CheckpointMonitor):
            waits = []
            def waitForAbort(self, seconds):
                self.waits.append(seconds)
                return True
        with mock.patch.object(service, 'InfinityPlayer', return_value=self.player), \
             mock.patch.object(service, 'ExperienceController', return_value=self.experience), \
             mock.patch.object(service, 'StabilityController', return_value=self.stability), \
             mock.patch.object(service, 'CheckpointMonitor', ExitAfterCheckpoint), \
             mock.patch.object(service.skin_upgrade, 'apply_and_reload', return_value='unchanged'), \
             mock.patch.object(service, 'scan_guardian'), \
             mock.patch.object(service, 'publish_refresh_state'), \
             mock.patch.object(service, 'publish_runtime_capabilities'), \
             mock.patch.object(service, '_active_video_player_id', return_value=1), \
             mock.patch.object(service, '_player_props', return_value={'speed': 0, 'subtitleenabled': False}), \
             mock.patch.object(self.player, 'poll') as playback_poll, \
             mock.patch.object(self.experience, 'tick') as observer_tick:
            service.main()
        self.assertEqual(self.response()['status'], 'PLAYBACK_CHECKPOINTED')
        playback_poll.assert_not_called()
        observer_tick.assert_not_called()
        self.assertEqual(ExitAfterCheckpoint.waits, [0.05])


if __name__ == '__main__':
    unittest.main()
