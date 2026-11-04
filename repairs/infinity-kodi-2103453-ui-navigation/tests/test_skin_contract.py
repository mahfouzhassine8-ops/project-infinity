import copy
import os
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get('BASE_SKIN', '/tmp/kodi453-ui-baseline/assets/addons/skin.infinity.diggz'))
ROOT = Path(os.environ.get('TEST_SKIN', HERE / 'overlay/assets/addons/skin.infinity.diggz'))


def path(name):
    p = ROOT / 'unified' / name
    return p if p.exists() else BASE / 'unified' / name


def read(name):
    return E.parse(path(name)).getroot()


def condition(text, content='', plugin='', mode='auto', slim=False):
    # Bounded evaluator for the four existing List-routing include predicates.
    atoms = {
        'String.IsEqual(Skin.String(Infinity.HomeView),cinema)': mode == 'cinema',
        'String.IsEqual(Skin.String(Infinity.HomeView),compact)': mode == 'compact',
        'String.IsEmpty(Container.PluginName)': not plugin,
        'Skin.HasSetting(Enable.SlimList)': slim,
    }
    text = re.sub(r'Container.Content\(([^)]*)\)', lambda m: str(content == m[1]), text)
    for token, value in atoms.items():text = text.replace(token, str(value))
    text = text.replace('[', '(').replace(']', ')').replace('+', ' and ').replace('|', ' or ').replace('!', ' not ')
    if re.sub(r'True|False|and|or|not|[()\s]', '', text):
        raise ValueError('Unexpected expression: ' + text)
    return bool(eval(text, {'__builtins__': {}}, {}))


def owners(content, plugin='', mode='auto', slim=False):
    choices = {'InfinityPluginDirectoryCompact', 'InfinityPluginDirectoryRegular',
               'InfinityCoreDirectory', 'VideoList', 'SlimVideoList', 'InfinityCinemaBrowseList'}
    return [n.text for n in read('MyVideoNav.xml').iter('include')
            if n.text in choices and condition(n.get('condition', ''), content, plugin, mode, slim)]


def scoped_dialog(old, suffix):
    new = old + 6
    p = ROOT / 'unified' / ('custom_%s_InfinityVideo%s.xml' % (new, suffix))
    return E.parse(p).getroot() if p.exists() else read('custom_%s_%s.xml' % (old, suffix))


class BrowserSource(unittest.TestCase):
    def test_plugin_movie_list_retains_existing_detail_layout(self):
        for mode in ['auto', 'normal', 'compact', 'twopane']:
            for slim in [False, True]:
                with self.subTest(mode=mode, slim=slim):
                    self.assertEqual(owners('movies', 'plugin.video.fixture', mode, slim),
                                     ['SlimVideoList' if slim else 'VideoList'])

    def test_other_list_routes_unchanged(self):
        for content in ['', 'files', 'playlists', 'addons', 'tvshows', 'episodes']:
            for plugin in ['', 'plugin.video.fixture']:
                for mode in ['auto', 'compact', 'cinema']:
                    for slim in [False, True]:
                        selected = owners(content, plugin, mode, slim)
                        if mode == 'cinema':wanted = 'InfinityCinemaBrowseList'
                        elif plugin:wanted = 'InfinityPluginDirectoryCompact' if mode == 'compact' else 'InfinityPluginDirectoryRegular'
                        elif content in ['', 'files', 'playlists', 'addons']:wanted = 'InfinityCoreDirectory'
                        else:wanted = 'SlimVideoList' if slim else 'VideoList'
                        self.assertEqual(selected, [wanted], (content, plugin, mode, slim))

    def test_original_movie_layout_and_metadata_not_rewritten(self):
        self.assertFalse((ROOT / 'unified/View_50_List.xml').exists() and ROOT != BASE)
        source = read('View_50_List.xml')
        detailed = E.tostring(source.find("include[@name='VideoList']"), encoding='unicode')
        # The unchanged detailed layout refers through VideoPlotVar, rather
        # than embedding the ListItem.Plot label literally. Visibility remains
        # the original layout's contract; this is not a rendered synopsis test.
        self.assertIn('$VAR[VideoPlotVar]', detailed)
        variables = read('Variables.xml')
        plot = E.tostring(variables.find("variable[@name='VideoPlotVar']"), encoding='unicode')
        self.assertIn('ListItem.Plot', plot)
        self.assertIn('ListItem.Title', detailed)
        self.assertIn('ListItem.Year', detailed)
        self.assertIn('poster', detailed.lower())
        for name in ['View_51_InfoWall.xml', 'View_55_TriPanel.xml', 'View_56_Posters.xml']:
            self.assertEqual(path(name).read_bytes(), (BASE / 'unified' / name).read_bytes())

    def test_view54_is_non_video_not_a_movie_registration_repair(self):
        selector = read('custom_1130_Views.xml')
        item = next(n for n in selector.findall('.//content/item')
                    if n.findtext('onclick') == 'Container.SetViewMode(54)')
        self.assertIn('!Window.IsActive(videos)', item.findtext('visible'))
        self.assertNotIn('54', read('MyVideoNav.xml').findtext('views').split(','))

    def test_all_original_view_actions_and_filters_retained(self):
        old = read('custom_1130_Views.xml').findall('.//content/item')
        new = scoped_dialog(1130, 'Views').findall('.//content/item')
        self.assertEqual(len(old), len(new))
        for a, b in zip(old, new):
            self.assertEqual(a.findtext('label'), b.findtext('label'))
            self.assertIn(a.findtext('onclick'), [n.text for n in b.findall('onclick')])
            self.assertEqual([v.text for v in a.findall('visible')], [v.text for v in b.findall('visible')])

    def test_selection_applies_then_returns_to_selected_view_once(self):
        root = scoped_dialog(1130, 'Views')
        for item in root.findall('.//content/item'):
            actions = [a.text for a in item.findall('onclick')]
            native = next((a for a in actions if a.startswith('Container.SetViewMode(')), None)
            if native:
                view = native.split('(')[1].rstrip(')')
                self.assertEqual(actions, ['Skin.SetString(Infinity.MediaView.Default,%s)' % view,
                                          native, 'ClearProperty(MediaMenu,Home)',
                                          'Dialog.Close(1136)', 'SetFocus(%s)' % view])
                save = item.find('onclick')
                predicate = save.get('condition', '')
                self.assertTrue(predicate.startswith('Window.IsActive(videos) + ['))
                media = set(re.findall(r'Container.Content\(([^)]*)\)', predicate))
                self.assertEqual(media, {'movies','tvshows','seasons','episodes','sets','musicvideos'})

    def test_close_and_back_only_dismiss_intended_layer(self):
        for old, suffix, content in [(1130, 'Views', '9000'), (1131, 'ViewSettings', '9011'), (1132, 'DisableViews', '9012')]:
            root = scoped_dialog(old, suffix)
            close = [n for n in root.iter('control') if n.get('id') == '8999']
            self.assertEqual(len(close), 1)
            self.assertEqual(close[0].findtext('onclick'), 'Dialog.Close(%s)' % (old + 6))
            self.assertEqual(root.findtext('onback'), 'Dialog.Close(%s)' % (old + 6))
            self.assertIsNone(close[0].find('visible'))
            self.assertEqual(close[0].findtext('ondown'), content)
            self.assertNotIn('ActivateWindow(Home)', E.tostring(root, encoding='unicode'))
            self.assertNotIn('Container.Refresh', E.tostring(root, encoding='unicode'))

    def test_nested_panel_bounds_and_nonoverlapping_rows(self):
        for old, suffix in [(1130, 'Views'), (1131, 'ViewSettings'), (1132, 'DisableViews')]:
            root = scoped_dialog(old, suffix)
            panel = root.find('./controls/control')
            self.assertEqual(panel.findtext('width'), '92%')
            close = root.find(".//control[@id='8999']")
            self.assertGreaterEqual(float(close.findtext('top')), 0)
            self.assertGreaterEqual(float(close.findtext('width')), 128)
            self.assertGreaterEqual(float(close.findtext('height')), 128)
            # Source-coordinate model, not physical dp or a rendered touch claim.
            for width, height in [(1080, 2520), (2160, 2250), (2520, 1080), (2250, 2160)]:
                pw = min(width * .92, 840)
                self.assertLess(18 + pw, width)
                self.assertGreater(pw - 36, 600)
                self.assertLess(18 + 128, 176)
                self.assertGreater(height - 36 - 176 - 128, 0)

    def test_shared_dialogs_and_rows_unchanged(self):
        for name in ['custom_1130_Views.xml', 'custom_1131_ViewSettings.xml', 'custom_1132_DisableViews.xml',
                     'Includes_CommonValues.xml', 'Includes_InfinityLegacy.xml', 'Includes_ViewSettings.xml']:
            self.assertEqual(path(name).read_bytes(), (BASE / 'unified' / name).read_bytes())
        before = (BASE / 'unified/Includes.xml').read_bytes()
        after = path('Includes.xml').read_bytes()
        addition = b'  <include file="Includes_InfinityVideoOptions.xml" />\n'
        self.assertEqual(after.replace(addition, b''), before)

    def test_main_video_menu_has_one_close_and_full_width_rows(self):
        p = ROOT / 'unified/Includes_InfinityVideoOptions.xml'
        self.assertTrue(p.exists(), 'Videos-specific menu missing')
        root = E.parse(p).getroot()
        side = root.find("include[@name='InfinityVideoSideBladeLeft']")
        self.assertEqual(len(side.findall(".//control[@id='8999']")), 1)
        self.assertEqual(len(side.findall(".//control[@id='9002']")), 0)
        row = root.find("include[@name='InfinityVideoMenuRow']")
        self.assertEqual(row.findtext('width'), '100%')
        self.assertEqual(row.findtext('textwidth'), '0')


def drawer_rows(root):
    section = None
    result = {}
    for group in root.find(".//control[@id='1198899']").findall('control'):
        label = group.find("control[@type='label']")
        button = group.find("control[@type='button']")
        if button is not None:result.setdefault(section, []).append(button)
        elif label is not None and group.findtext('height') == '38':section = label.findtext('label')
    return result


class DrawerSource(unittest.TestCase):
    def test_navigation_order(self):
        rows = drawer_rows(read('Custom_1198_InfinityNav.xml'))
        self.assertEqual([b.findtext('label') for b in rows['NAVIGATION']],
                         ['Home', 'Movies', 'TV Shows', 'Sports', 'Favorites'])

    def test_library_uses_native_collections_and_sources(self):
        rows = drawer_rows(read('Custom_1198_InfinityNav.xml'))['LIBRARY']
        by_label = {b.findtext('label'): [n.text for n in b.findall('onclick')] for b in rows}
        self.assertEqual(list(by_label)[:5], ['Infinity Movies', 'Infinity TV Shows', 'Browse Files', 'Downloads', 'Media Sources'])
        self.assertIn('ActivateWindow(Videos,videodb://movies/titles/,return)', by_label['Infinity Movies'])
        self.assertIn('ActivateWindow(Videos,videodb://tvshows/titles/,return)', by_label['Infinity TV Shows'])
        self.assertIn('ActivateWindow(Videos,files,return)', by_label['Media Sources'])
        for label in ['Browse Files', 'Downloads']:
            self.assertTrue(any('infinity_library_navigation.py' in a for a in by_label[label]))

    def test_original_routes_system_actions_and_styling_preserved(self):
        base = E.parse(BASE / 'unified/Custom_1198_InfinityNav.xml').getroot()
        new = read('Custom_1198_InfinityNav.xml')
        for cid in ['1198101', '1198102', '1198103', '1198105', '1198303', '1198310', '1198503', '1198304',
                    '1198108', '1198109', '1198201', '1198202', '1198203', '1198204', '1198410']:
            a = base.find(".//control[@id='%s']" % cid)
            b = new.find(".//control[@id='%s']" % cid)
            self.assertEqual(E.tostring(a), E.tostring(b), cid)
        fav = new.find(".//control[@id='1198301']")
        self.assertIn('ActivateWindow(favouritesbrowser)', [n.text for n in fav.findall('onclick')])
        ids = [n.get('id') for n in new.iter('control') if n.get('id')]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == '__main__':unittest.main()
