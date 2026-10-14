"""Package, exact-source, interaction routing and renderer-independent checks."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK / 'tools'))
sys.path.insert(0, str(WORK / 'addons/script.infinity.rails/resources'))
import build_rc3 as build
from lib import runtime, menu_geometry, store, menu
import test_runtime as fixtures


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(build.BASE) as z:
            cls.before = {n[20:]:z.read(n) for n in z.namelist() if not n.endswith('/')}
        cls.after = {p.relative_to(build.SKIN).as_posix():p.read_bytes() for p in build.SKIN.rglob('*') if p.is_file()}
        cls.report = json.loads((build.OUT / 'preservation.json').read_text())

    def test_exact_215_baseline(self):
        self.assertEqual(hashlib.sha256(build.BASE.read_bytes()).hexdigest(), build.BASE_SHA)

    def test_no_deleted_original_file(self):
        self.assertTrue(set(self.before) <= set(self.after))

    def test_change_scope(self):
        allowed = {'addon.xml', 'infinity-skin.json', 'Infinity-Protected-Manifest.json'}
        for p in build.PROFILES:
            allowed.update(p + '/' + n for n in ['Home.xml','Includes.xml','Includes_InfinityRails.xml','DialogContextMenu.xml','DialogInfinityRails.xml'])
        actual = {n for n in self.after if self.after[n] != self.before.get(n)}
        self.assertEqual(actual, allowed)

    def test_every_original_python_file_unchanged(self):
        for n in self.before:
            if n.endswith('.py'):
                self.assertEqual(self.before[n], self.after[n], n)

    def test_command_center_resume_shutdown_player_settings_unchanged(self):
        targets = [n for n in self.before if any(t in n.lower() for t in ['commandcenter','healthcenter','resume','shutdown','videoosd','addonsettings','filepreview'])]
        self.assertGreater(len(targets), 60)
        for n in targets:
            self.assertEqual(self.before[n], self.after[n], n)

    def test_all_original_art_fonts_shortcuts_preserved(self):
        for n in self.before:
            if n.startswith(('media/','fonts/')) or 'skinshortcuts-includes' in n:
                self.assertEqual(self.before[n], self.after[n], n)

    def test_every_xml_parses(self):
        for n, raw in self.after.items():
            if n.endswith('.xml'):
                ET.fromstring(raw)

    def test_complete_skin_upgrade_and_dependency(self):
        root = ET.fromstring(self.after['addon.xml'])
        self.assertEqual(root.get('id'), 'skin.infinity.diggz')
        self.assertEqual(root.get('version'), '1.0.5.217')
        self.assertEqual(root.find('./requires/import[@addon="script.infinity.rails"]').get('version'), '0.1.2')
        old = ET.fromstring(self.before['addon.xml'])
        for i in old.findall('./requires/import'):
            self.assertEqual(root.find('./requires/import[@addon="'+i.get('addon')+'"]').attrib, i.attrib)

    def test_installable_zip_tree_and_checksums(self):
        for name, row in self.report['packages'].items():
            p = build.OUT / name
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), row['sha256'])
            with ZipFile(p) as z:
                self.assertIsNone(z.testzip())
                roots = {n.split('/')[0] for n in z.namelist()}
                self.assertEqual(len(roots),1)
                self.assertIn(next(iter(roots)) + '/addon.xml',z.namelist())
                self.assertFalse(any('userdata' in n or n.endswith(('.pyc','.pyo','.apk')) for n in z.namelist()))
                if name.startswith('skin.'):
                    self.assertEqual({n[20:] for n in z.namelist()}, set(self.after))

    def test_helper_has_no_patcher_payload_or_startup_service(self):
        root = ET.parse(build.HELPER / 'addon.xml')
        self.assertEqual(root.getroot().get('version'),'0.1.2')
        self.assertNotIn('xbmc.service',{e.get('point') for e in root.findall('extension')})
        self.assertFalse((build.HELPER / 'resources/lib/installer.py').exists())
        self.assertFalse((build.HELPER / 'resources/skin216').exists())
        self.assertNotIn('Installer(', (build.HELPER / 'resources/lib/runtime.py').read_text())

    def test_state_schema_and_store_bytes_preserved(self):
        self.assertEqual((build.HELPER / 'resources/lib/store.py').read_bytes(),
                         (WORK.parent / 'helper-before/resources/lib/store.py').read_bytes())
        self.assertEqual(store.SCHEMA,1)

    def test_stock_context_controls_are_identical_outside_route(self):
        for profile in build.PROFILES:
            raw = self.after[profile + '/DialogContextMenu.xml'].decode()
            raw = raw.replace('\n  <onload condition="' + build.ROUTE + '">RunScript(script.infinity.rails,context)</onload>','',1)
            raw = raw.replace('<controls>\n    <control type="group">\n      <visible>![' + build.ROUTE + ']</visible>', '<controls>',1)
            raw = raw.replace('    </control>\n  </controls>','</controls>',1)
            self.assertEqual(raw.encode(), self.before[profile + '/DialogContextMenu.xml'])

    def test_theme_colors_dynamic_with_oled_priority(self):
        for profile in build.PROFILES:
            root = ET.fromstring(self.after[profile + '/Includes_InfinityRails.xml'])
            for key in ['Surface','Text','Secondary','Field','Focus','Border','Accent']:
                values = root.find('./variable[@name="InfinityRails'+key+'"]').findall('value')
                self.assertIn('OLED', values[0].get('condition'))
                self.assertIn('NativeSystemTheme', values[1].get('condition'))
                self.assertEqual(len(values),3)
            self.assertEqual(root.find('./variable[@name="InfinityRailsSurface"]/value').text,'FF000000')

    def test_motion_respects_optional_motion_flag(self):
        root = ET.fromstring(build.dialog_xml())
        animations = root.findall('animation')
        self.assertEqual([a.get('time') for a in animations], ['180','140'])
        for a in animations:
            self.assertIn('OptionalMotionAllowed',a.get('condition'))

    def test_no_startup_or_focus_opens_menu(self):
        for profile in build.PROFILES:
            root = ET.fromstring(self.after[profile + '/Home.xml'])
            for c in root.findall('.//control'):
                for n in ['onfocus','onunfocus','onclick']:
                    for a in c.findall(n):
                        self.assertNotIn('script.infinity.rails',a.text or '')
            self.assertFalse(any('script.infinity.rails' in (x.text or '') for x in root.findall('onload')))


def mode_case(profile, cid):
    def check(self):
        before = ET.fromstring(self.before[profile + '/Home.xml']).find('.//control[@id="'+str(cid)+'"]')
        after = ET.fromstring(self.after[profile + '/Home.xml']).find('.//control[@id="'+str(cid)+'"]')
        dynamic = [x for x in after.findall('content') if x.text == '$VAR[InfinityRailsContent]']
        self.assertEqual(len(dynamic),1)
        self.assertEqual(dynamic[0].get('target'),'videos')
        for tag in ['itemlayout','focusedlayout','left','top','width','height','visible','orientation','onup','ondown','onleft','onright','onback','scrolltime','preloaditems']:
            def semantic(n):
                return n.tag,dict(n.attrib),(n.text or '').strip(),tuple(semantic(c) for c in n)
            self.assertEqual([semantic(n) for n in before.findall(tag)],[semantic(n) for n in after.findall(tag)],tag)
        self.assertEqual(after.findtext('onfocus'),'SetProperty(Infinity.Rails.Focused,'+str(cid)+',home)')
    return check

for p in build.PROFILES:
    for mode, cid in [('normal',9200),('compact',8820),('twopane',8720),('cinema',19600)]:
        setattr(PackageTests, 'test_' + p.replace('/','_') + '_' + mode, mode_case(p,cid))


class Rc3RuntimeTests(unittest.TestCase):
    # Additional runtime tests use the existing fake Kodi fixture, not a device.
    setUp = fixtures.RuntimeTests.setUp
    tearDown = fixtures.RuntimeTests.tearDown
    plugin = fixtures.RuntimeTests.plugin
    def test_root_listing_opens_no_dialog(self):
        self.plugin('')
        self.assertEqual(len(self.listing),2)
        self.assertEqual(self.dialogs,[])

    def test_duplicate_add_causes_no_refresh(self):
        self.answers=[0,0]
        runtime.do_add(explicit_id='plugin.video.fixture')
        saved = dict(self.properties)
        runtime.do_add(explicit_id='plugin.video.fixture')
        self.assertEqual(saved,self.properties)

    def test_add_refreshes_only_movie_rail(self):
        self.answers=[0]
        runtime.do_add(explicit_id='plugin.video.fixture')
        self.assertIn('Infinity.Rails.movies.Revision',self.properties)
        self.assertNotIn('Infinity.Rails.tvshows.Revision',self.properties)

    def test_custom_option_menu_contains_exact_section_remove(self):
        store.Store(self.profile).add('plugin.video.fixture',['movies'],{})
        with unittest.mock.patch.object(runtime,'choose',return_value=None) as choice:
            runtime.options('movies','c:plugin.video.fixture')
        self.assertIn(('remove','Remove from Movie Add-ons'),choice.call_args.args[4])

    def test_builtin_options_protect_removal_and_preserve_deeplink(self):
        row=runtime.defaults(runtime.setup()[4])['movies'][1]
        with unittest.mock.patch.object(runtime,'choose',return_value='open') as choice:
            runtime.options('movies',row['key'])
        self.assertNotIn('remove',[key for key,label in choice.call_args.args[4]])
        self.assertIn(row['action'],self.calls)

    def test_settings_action_only_if_settings_definition_exists(self):
        store.Store(self.profile).add('plugin.video.fixture',['movies'],{})
        with unittest.mock.patch.object(runtime,'choose',return_value=None) as choice:
            runtime.options('movies','c:plugin.video.fixture')
        self.assertNotIn('settings',[k for k,l in choice.call_args.args[4]])
        (self.installed/'resources').mkdir()
        (self.installed/'resources/settings.xml').write_text('<settings/>')
        with unittest.mock.patch.object(runtime,'choose',return_value='settings'):
            runtime.options('movies','c:plugin.video.fixture')
        self.assertIn(('settings','plugin.video.fixture'),self.calls)

    def test_context_requires_focused_supported_rail(self):
        self.focus=9100
        with unittest.mock.patch.object(runtime,'options') as option:
            runtime.context_options()
        option.assert_not_called()
        self.assertEqual(self.calls,[])

    def test_context_captures_selected_card_and_closes_native_popup(self):
        self.info={'Container(9200).ListItem.Property(Infinity.Rails.Section)':'movies',
                   'Container(9200).ListItem.Property(Infinity.Rails.Key)':'c:plugin.video.fixture'}
        with unittest.mock.patch.object(runtime,'options') as option:
            runtime.context_options()
        option.assert_called_once_with('movies','c:plugin.video.fixture')
        self.assertEqual(self.calls,['Dialog.Close(contextmenu,true)'])

    def test_context_missing_item_never_opens(self):
        with unittest.mock.patch.object(runtime,'options') as option:
            runtime.context_options()
        option.assert_not_called()

    def test_removed_stale_token_rejected_without_launch(self):
        with self.assertRaises(store.RailError):
            runtime.options('movies','c:plugin.video.missing')
        self.assertEqual(self.calls,[])

    def test_cancel_options_does_not_write_or_refresh(self):
        s=store.Store(self.profile)
        s.add('plugin.video.fixture',['movies'],{})
        raw=s.path.read_bytes()
        with unittest.mock.patch.object(runtime,'choose',return_value=None):
            runtime.options('movies','c:plugin.video.fixture')
        self.assertEqual(raw,s.path.read_bytes())
        self.assertEqual(self.properties,{})

    def test_duplicate_destination_request_does_not_stack_modals(self):
        self.inst.stop()
        with menu.menu_lock(self.profile,'rails-modal.lock') as acquired:
            self.assertTrue(acquired)
            with unittest.mock.patch.object(menu,'select') as select:
                result=runtime.choose(self.gui,self.xbmc,runtime.setup()[4],'ADD TO INFINITY RAILS',[(0,'Movie Add-ons')])
            self.assertIsNone(result)
            select.assert_not_called()


class GeometryTests(unittest.TestCase):
    def test_all_fold_split_float_orientations_bounded(self):
        for dw,dh in [(384,832),(832,384),(690,780),(780,690),(320,780),(780,320),(220,440),(440,220),(160,160)]:
            for count in [2,3,4,5,10,256]:
                for lw,lh in [(1080,2400),(1920,1080),(1100,1000)]:
                    g=menu_geometry.layout(lw,lh,dw,dh,count)
                    self.assertGreaterEqual(g['left'],0)
                    self.assertGreaterEqual(g['top'],0)
                    self.assertLessEqual(g['left']+g['width'],lw)
                    self.assertLessEqual(g['top']+g['height'],lh)
                    self.assertGreater(g['width_dp'],0)
                    self.assertGreaterEqual(g['capacity'],1)
                    self.assertLessEqual(g['capacity'],5)

    def test_short_window_pages_instead_of_clipping(self):
        g=menu_geometry.layout(1920,1080,832,250,5)
        self.assertLess(g['capacity'],5)
        self.assertTrue(g['paged'])

    def test_normal_window_full_touch_rows(self):
        g=menu_geometry.layout(1080,2400,384,832,5)
        self.assertEqual(g['capacity'],5)
        self.assertGreater(g['fit'],.9)

    def test_unverified_dp_fallback_is_explicit(self):
        self.assertFalse(menu_geometry.layout(1920,1080,'','')['dp_verified'])

    def test_bad_bounds_rejected(self):
        for value in [0,-1,'nan','inf','garbage']:
            with self.assertRaises(ValueError):
                menu_geometry.layout(value,1080)


if __name__ == '__main__':
    unittest.main()
