"""Global preference policy and Kodi API boundary tests; not Android evidence."""
import importlib.util
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parents[1]
OWNER = HERE / 'overlay/assets/addons/script.infinity.commandcenter'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('media_view_candidate', OWNER / 'media_view.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Kodi:
    def __init__(self, saved=None):
        self.saved = saved if saved is not None else {}
        self.skin = 'skin.infinity.diggz'
        self.window = 10025
        self.dialog = 9999
        self.content = 'movies'
        self.path = 'plugin://provider.a/movies?page=1'
        self.current = 50
        self.updating = False
        self.controls = set(module.REGISTERED)
        self.disabled = set()
        self.commands = []
        self.queue = []
        self.focus = 'channel-independent-item-7'
        self.scroll = 7

    def getSkinDir(self):return self.skin
    def getCurrentWindowId(self):return self.window
    def getCurrentWindowDialogId(self):return self.dialog
    def Window(self, number):
        assert number == 10025
        return self
    def getControl(self, number):
        if number not in self.controls:raise RuntimeError('not included')
        return object()
    def getInfoLabel(self, label):
        if label == 'Skin.String(%s)' % module.PREFERENCE:return self.saved.get(module.PREFERENCE, '')
        if label == 'Container.FolderPath':return self.path
        raise AssertionError(label)
    def getCondVisibility(self, expression):
        if expression == 'Container.IsUpdating':return self.updating
        expression = re.sub(r'Container.Content\(([^)]+)\)', lambda m: str(self.content == m[1]), expression)
        expression = re.sub(r'Control.IsVisible\((\d+)\)', lambda m: str(self.current == int(m[1])), expression)
        expression = re.sub(r'Skin.HasSetting\(([^)]+)\)', lambda m: str(m[1] in self.disabled), expression)
        expression = re.sub(r'Window.IsActive\(([^)]+)\)', lambda m: str(m[1] == 'videos' and self.window == 10025), expression)
        expression = re.sub(r'String.Contains\([^)]*\)', 'False', expression)
        expression = expression.replace('[', '(').replace(']', ')').replace('!', ' not ').replace('+', ' and ').replace('|', ' or ')
        assert not re.sub(r'True|False|and|or|not|[()\s]', '', expression), expression
        return bool(eval(expression, {'__builtins__': {}}, {}))
    def executebuiltin(self, command, *args):
        # Any synchronous call, file/setting/refresh/player action fails this seam.
        assert not args
        match = re.fullmatch(r'Container.SetViewMode\((\d+)\)', command)
        assert match, command
        self.commands.append(command)
        self.queue.append(int(match[1]))
    def acknowledge(self):
        if self.queue:self.current = self.queue.pop(0)
    def select(self, view):
        # Native selector stores the skin setting then applies the local view.
        self.saved[module.PREFERENCE] = str(view)
        self.current = view


class GlobalMediaPreference(unittest.TestCase):
    def setUp(self):
        self.k = Kodi()
        self.c = module.MediaViewPreference(self.k, self.k)

    def settle(self, target):
        self.c.tick();self.k.acknowledge();self.c.tick()
        self.assertEqual(self.k.current, target)

    def test_one_choice_across_providers_pages_categories_back_and_refresh(self):
        for view in (50, 56, 55, 51, 53, 500, 503, 504):
            self.k.select(view)
            for provider, page, category in [('a', 1, 'theaters'), ('a', 2, 'theaters'),
                    ('a', 1, 'theaters'), ('a', 1, 'theaters'), ('a', 1, 'popular'),
                    ('b', 1, 'movies'), ('b', 2, 'movies'), ('c', 1, 'movies')]:
                with self.subTest(view=view, provider=provider, page=page, category=category):
                    self.k.path = 'plugin://provider.%s/%s?page=%s' % (provider, category, page)
                    self.k.current = 500 if view == 50 else 50  # old path preference/provider default
                    self.settle(view)
                    self.assertEqual(self.k.saved[module.PREFERENCE], str(view))

    def test_recreated_resident_reads_same_persistent_setting(self):
        self.k.select(55)
        reopened = Kodi(self.k.saved)
        restored = module.MediaViewPreference(reopened, reopened)
        restored.tick();reopened.acknowledge()
        self.assertEqual(reopened.current, 55)

    def test_explicit_new_selection_replaces_old_global_default(self):
        self.k.select(55);self.c.tick()
        self.k.select(51);self.k.path = 'plugin://provider.b/tv'
        self.k.content = 'tvshows';self.k.current = 50
        self.settle(51)

    def test_incompatible_episode_fallback_does_not_overwrite_movie_choice(self):
        self.k.select(51);saved = dict(self.k.saved)
        self.k.content = 'episodes';self.k.current = 500
        self.settle(50)
        self.assertEqual(self.k.saved, saved)
        self.k.content = 'movies';self.settle(51)

    def test_disabled_or_missing_control_falls_back_and_recovers(self):
        self.k.select(55);self.k.disabled.add('Disable.TriPanelView')
        self.settle(50)
        self.k.disabled.clear();self.k.controls.remove(55)
        self.settle(50)
        self.k.controls.add(55);self.settle(55)
        self.assertEqual(self.k.saved[module.PREFERENCE], '55')

    def test_loading_and_modal_panels_defer_enforcement(self):
        self.k.select(56);self.k.current = 50;self.k.updating = True
        self.assertEqual(self.c.tick(), 'inactive');self.assertFalse(self.k.commands)
        self.k.updating = False;self.k.dialog = 11136
        self.assertEqual(self.c.tick(), 'inactive');self.assertFalse(self.k.commands)
        self.k.dialog = 9999;self.settle(56)

    def test_delayed_provider_override_cannot_replace_explicit_preference(self):
        self.k.select(55);self.c.tick()
        self.k.current = 500;self.settle(55)
        self.assertEqual(self.k.saved[module.PREFERENCE], '55')

    def test_pending_command_is_not_repeated_and_matching_view_writes_nothing(self):
        self.k.select(51);self.k.current = 50
        self.assertEqual(self.c.tick(), 'requested')
        for _ in range(20):self.assertEqual(self.c.tick(), 'pending')
        self.assertEqual(len(self.k.commands), 1)
        self.k.acknowledge()
        for _ in range(20):self.assertEqual(self.c.tick(), 'matched')
        self.assertEqual(len(self.k.commands), 1)

    def test_unset_and_invalid_preferences_preserve_legacy_state(self):
        for value in ('', 'not-an-id', '54', '50);Quit()', '-1'):
            self.k.saved[module.PREFERENCE] = value
            self.assertEqual(self.c.tick(), 'unset')
        self.assertFalse(self.k.commands)

    def test_system_specialized_windows_and_non_media_directories_unchanged(self):
        self.k.select(55);self.k.current = 50
        for window in (10000, 10001, 10002, 10024, 10028, 12005, 10040):
            self.k.window = window;self.assertEqual(self.c.tick(), 'inactive')
        self.k.window = 10025
        for content in ('', 'files', 'addons', 'songs', 'games', 'artists'):
            self.k.content = content;self.assertEqual(self.c.tick(), 'non-media')
        self.k.content = 'movies';self.k.skin = 'skin.estuary'
        self.assertEqual(self.c.tick(), 'inactive');self.assertFalse(self.k.commands)

    def test_native_transfer_is_used_without_focus_scroll_or_directory_actions(self):
        self.k.select(56);self.k.current = 50
        original = (self.k.focus, self.k.scroll, self.k.path)
        self.settle(56)
        self.assertEqual((self.k.focus, self.k.scroll, self.k.path), original)
        self.assertEqual(self.k.commands, ['Container.SetViewMode(56)'])

    def test_no_command_when_registered_list_is_missing_or_view_not_ready(self):
        self.k.select(55);self.k.controls.clear()
        self.assertEqual(self.c.tick(), 'unsupported')
        self.k.controls = set(module.REGISTERED);self.k.current = None
        self.assertEqual(self.c.tick(), 'not-ready');self.assertFalse(self.k.commands)

    def test_state_changed_before_dispatch_is_deferred(self):
        self.k.select(55);self.k.current = 50
        original = self.k.getCurrentWindowId
        calls = []
        def switched():
            calls.append(1)
            return original() if len(calls) == 1 else 10002
        self.k.getCurrentWindowId = switched
        self.assertEqual(self.c.tick(), 'changed');self.assertFalse(self.k.commands)

    def test_integration_leaves_entire_original_resident_byte_identical(self):
        base = Path('/tmp/kodi453-ui-baseline/assets/addons/script.infinity.commandcenter/service.py').read_bytes()
        candidate = (OWNER / 'service.py').read_bytes()
        stripped = candidate.replace(b'    from media_view import MediaViewPreference\n    media_views = MediaViewPreference(xbmc, xbmcgui)\n', b'')
        stripped = stripped.replace(b'        media_views.tick()\n', b'')
        self.assertEqual(stripped, base)
        loop = candidate[candidate.index(b'    while not monitor.abortRequested():'):]
        self.assertLess(loop.index(b'if checkpoint.poll():'), loop.index(b'media_views.tick()'))
        self.assertLess(loop.index(b'if not foreground_gate.visible():'), loop.index(b'media_views.tick()'))

    def test_rules_and_registered_ids_come_from_exact_signed_skin(self):
        skin = Path('/tmp/kodi453-ui-baseline/assets/addons/skin.infinity.diggz/unified')
        ids = tuple(map(int, E.parse(skin / 'MyVideoNav.xml').getroot().findtext('views').split(',')))
        self.assertEqual(module.REGISTERED, ids)
        self.assertNotIn(54, ids)
        self.assertEqual(module.RULES[50], [()])


if __name__ == '__main__':unittest.main()
