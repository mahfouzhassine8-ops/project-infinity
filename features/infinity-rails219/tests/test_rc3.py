"""RC3 host tests. These do not simulate touch recognition or render Kodi frames."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from zipfile import ZipFile

WORK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORK/'addons/script.infinity.rails/resources'))
sys.path.insert(0,str(WORK/'tools'))
from lib import menu, runtime, store
import build_rc3 as build
import test_runtime as existing_runtime_tests

BASE=Path(__import__('os').environ['RAILS_BASELINE'])
CANDIDATE=Path(__import__('os').environ['RAILS_CANDIDATE'])
HELPER=Path(__import__('os').environ['RAILS_HELPER'])


def semantic(node):
    return node.tag, dict(node.attrib), node.text if node.text and node.text.strip() else None, tuple(semantic(c) for c in node)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(BASE) as z:cls.before={n[len(build.ROOT):]:z.read(n) for n in z.namelist()}
        with ZipFile(CANDIDATE) as z:cls.after={n[len(build.ROOT):]:z.read(n) for n in z.namelist()}

    def test_exact_authoritative_215_identity(self):
        self.assertEqual(hashlib.sha256(BASE.read_bytes()).hexdigest(), build.BASE_SHA)

    def test_219_required_helper_dependency(self):
        root=ET.fromstring(self.after['addon.xml']);self.assertEqual(root.get('version'),'1.0.5.219')
        self.assertEqual(root.find("requires/import[@addon='script.infinity.rails']").get('version'),'0.2.1')

    def test_no_deleted_baseline_files(self):self.assertTrue(set(self.before)<=set(self.after))

    def test_only_authorized_integration_points_change(self):
        allowed={'addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'}
        for p in build.PROFILES:allowed.update(p+'/'+n for n in ('Home.xml','Includes.xml','DialogContextMenu.xml','Includes_InfinityRails.xml','InfinityRailsOptions.xml'))
        actual={n for n in self.after if self.after[n]!=self.before.get(n)}
        self.assertEqual(actual,allowed)

    def test_2937_original_files_byte_identical(self):
        same=[n for n in self.before if self.before[n]==self.after[n]];self.assertEqual(len(same),2937)

    def test_command_center_and_settings_repairs_preserved(self):
        paths=[n for n in self.before if 'DialogAddonSettings.xml' in n or 'Custom_1194_' in n]
        self.assertEqual(len(paths),27)
        for n in paths:self.assertEqual(self.before[n],self.after[n],n)

    def test_all_original_python_shutdown_and_provider_sources_preserved(self):
        for n in self.before:
            if n.endswith(('.py','.xbt','.ttf','.otf')) or 'Resume' in n or 'HealthCenter' in n:
                self.assertEqual(self.before[n],self.after[n],n)

    def test_all_original_shortcuts_preserved(self):
        for n in self.before:
            if n.endswith('script-skinshortcuts-includes.xml'):self.assertEqual(self.before[n],self.after[n])

    def test_complete_skin_crc_and_xml(self):
        with ZipFile(CANDIDATE) as z:self.assertIsNone(z.testzip())
        for n,b in self.after.items():
            if n.endswith('.xml'):ET.fromstring(b)

    def test_full_zip_is_one_skin_not_patcher_or_bundle(self):
        with ZipFile(CANDIDATE) as z:
            self.assertTrue(all(n.startswith(build.ROOT) for n in z.namelist()))
        with ZipFile(HELPER) as z:
            self.assertIsNone(z.testzip())
            self.assertFalse(any('skin216' in n or 'installer.py' in n or 'rails.json' in n or n.endswith('.pyc') for n in z.namelist()))
            addon=ET.fromstring(z.read('script.infinity.rails/addon.xml'))
            self.assertEqual(addon.get('version'),'0.2.1')
            self.assertNotIn('xbmc.service',{n.get('point') for n in addon.findall('extension')})
            for n in z.namelist():
                if n.endswith('.py'):ast.parse(z.read(n), feature_version=(3,11))

    def test_protected_hashes_match_changed_sources(self):
        old=json.loads(self.before['Infinity-Protected-Manifest.json'])['protected_files']
        new=json.loads(self.after['Infinity-Protected-Manifest.json'])['protected_files']
        self.assertEqual(set(old),set(new))
        for n,h in new.items():
            if self.before.get(n)!=self.after.get(n):self.assertEqual(h,hashlib.sha256(self.after[n]).hexdigest())
            else:self.assertEqual(h,old[n])

    def test_helper_store_and_catalog_byte_identical_to_rc2(self):
        source=Path(__import__('os').environ['RAILS_RC2'])
        with ZipFile(source) as z:
            for n in ('resources/lib/store.py','resources/lib/catalog.py','resources/defaults.xml'):
                self.assertEqual(z.read('script.infinity.rails/'+n),(WORK/'addons/script.infinity.rails'/n).read_bytes())

    def test_no_resource_writes_or_native_actions_in_new_runtime(self):
        source=(WORK/'addons/script.infinity.rails/resources/lib/runtime.py').read_text()
        for text in ('Installer','ReloadSkin','UpdateLocalAddons','Container.Refresh','PlayMedia','Stop()','Player.Stop','Thread','sleep('):self.assertNotIn(text,source)

    def test_all_bounded_dialog_shapes_have_consistent_control_bounds(self):
        tree=ET.fromstring(self.after['unified/Includes_InfinityRails.xml'])
        for width in (192,320,480,720,900):
            for rows in range(1,9):
                inc=tree.find("include[@name='InfinityRailsShape%dRows%d']" % (width,rows))
                group=inc.find('control');height=144+82*rows
                self.assertEqual(group.findtext('centerleft'),'50%');self.assertEqual(group.findtext('centertop'),'50%')
                self.assertEqual(int(group.findtext('width')),width);self.assertEqual(int(group.findtext('height')),height)
                ids=[c.get('id') for c in group.findall('control')];self.assertEqual(len(ids),len(set(ids)))
                for control in group.findall('control'):
                    x,y,w,h=[int(control.findtext(k)) for k in ('left','top','width','height')]
                    self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                    self.assertLessEqual(x+w,width);self.assertLessEqual(y+h,height)
                listing=group.find("control[@id='6']")
                self.assertEqual(int(listing.findtext('height')),82*rows)
                self.assertEqual(listing.find('itemlayout').get('height'),'82')


def profile_test(profile):
    def test(self):
        old_home=self.before[profile+'/Home.xml'].decode()
        new_home=self.after[profile+'/Home.xml'].decode()
        recovered=re.sub(r'\n\s*<onfocus>SetProperty\(Infinity.Rails.ContextControl,\d+,home\)</onfocus>','',new_home)
        recovered=re.sub(r'\n\s*<onunfocus>ClearProperty\(Infinity.Rails.ContextControl,home\)</onunfocus>','',recovered)
        dynamic='<content target="videos" sortby="none" limit="0" browse="never">$VAR[InfinityRailsContent]</content>'
        recovered=re.sub(r'\n\s*'+re.escape(dynamic),'',recovered).replace('<include>InfinityRailsFallback</include>','<include>skinshortcuts-submenu-2</include>')
        self.assertEqual(recovered,old_home, 'Unrelated home layout/action changed')
        new=ET.fromstring(self.after[profile+'/Home.xml'])
        for mode,cid in zip(('normal','compact','twopane','cinema'),build.CONTROLS):
            c=new.find('.//control[@id="'+str(cid)+'"]')
            self.assertEqual(len([x for x in c.findall('content') if x.text=='$VAR[InfinityRailsContent]']),1)
            self.assertTrue(c.findtext('onfocus').startswith('SetProperty'))
            if mode=='cinema':self.assertEqual(c.findtext('content/include'),'skinshortcuts-submenu')
        old_ctx=ET.fromstring(self.before[profile+'/DialogContextMenu.xml'])
        new_ctx=ET.fromstring(self.after[profile+'/DialogContextMenu.xml'])
        include=ET.fromstring(self.after[profile+'/Includes_InfinityRails.xml'])
        legacy=include.find("include[@name='InfinityRailsLegacyContext']")
        self.assertEqual(tuple(semantic(n) for n in legacy),tuple(semantic(n) for n in old_ctx.find('controls')))
        self.assertEqual(len(new_ctx.findall('onload')),4)
        for node in new_ctx.findall('onload'):
            self.assertIn('Infinity.Rails.Item',node.get('condition'));self.assertIn('Window.IsActive(home)',node.get('condition'))
            self.assertTrue(node.text.startswith('RunScript(script.infinity.rails,options,'))
        # No menu creation belongs to Home focus, scroll, visibility or mode events.
        self.assertNotIn('RunScript(script.infinity.rails,options,',new_home)
        dialog=ET.fromstring(self.after[profile+'/InfinityRailsOptions.xml'])
        self.assertEqual(dialog.findtext('defaultcontrol'),'6')
        self.assertEqual([a.get('time') for a in dialog.findall('animation')],['190','140'])
        for a in dialog.findall('animation'):self.assertIn('Infinity.OptionalMotionAllowed',a.get('condition'))
        for theme in ('Surface','Text','Secondary','Field','Accent','Border'):
            var=include.find("variable[@name='InfinityRails"+theme+"']")
            self.assertEqual(len(var.findall('value')),3)
            self.assertIn('OLED',var[0].get('condition'));self.assertIn('NativeSystemTheme',var[1].get('condition'))
        self.assertEqual(include.find("variable[@name='InfinityRailsSurface']")[0].text,'FF000000')
    return test

for p in build.PROFILES:setattr(PackageTests,'test_profile_'+p.replace('/','_'),profile_test(p))


class RuntimeRC3Tests(unittest.TestCase):
    setUp = existing_runtime_tests.RuntimeTests.setUp
    tearDown = existing_runtime_tests.RuntimeTests.tearDown
    plugin = existing_runtime_tests.RuntimeTests.plugin
    def test_root_plugin_never_opens_a_modal_or_patches_skin(self):
        runtime.plugin(['plugin://script.infinity.rails','1',''])
        self.assertFalse(self.dialogs);self.assertEqual(len(self.listing),2)
        self.assertFalse([x for x in self.calls if isinstance(x,str)])

    def test_remove_invalidates_only_its_rail(self):
        store.Store(self.profile).add('plugin.video.fixture',list(store.SECTIONS),{})
        self.answers=[0];runtime.remove_card('movies','c:plugin.video.fixture')
        self.assertIn('Infinity.Rails.movies.Revision',self.properties);self.assertNotIn('Infinity.Rails.tvshows.Revision',self.properties)

    def test_duplicate_does_not_trigger_any_refresh(self):
        store.Store(self.profile).add('plugin.video.fixture',['movies'],{})
        self.answers=[0];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse(self.properties)

    def test_destination_cancel_button_does_not_write(self):
        self.answers=[3];runtime.do_add(explicit_id='plugin.video.fixture');self.assertFalse((self.profile/'rails.json').exists())

    def test_cancel_reorder_keeps_exact_state(self):
        state=store.Store(self.profile);state.add('plugin.video.fixture',['movies'],{});before=state.path.read_bytes()
        self.answers=[11];runtime.move_card('movies','c:plugin.video.fixture');self.assertEqual(state.path.read_bytes(),before)

    def test_reorder_can_move_custom_before_defaults(self):
        state=store.Store(self.profile);state.add('plugin.video.fixture',['movies'],{});self.answers=[0]
        runtime.move_card('movies','c:plugin.video.fixture');self.plugin();self.assertEqual(self.listing[0][1].props['Infinity.Rails.Key'],'c:plugin.video.fixture')

    def test_open_option_uses_original_builtin_deep_link(self):
        rows=runtime.defaults(WORK/'addons/script.infinity.rails')['movies']
        runtime.open_card('movies',rows[1]['key']);self.assertIn('movieNavigator',self.calls[-1]);self.assertIn('ActivateWindow(Videos',self.calls[-1])

    def test_settings_offered_only_when_supported(self):
        row=runtime.defaults(WORK/'addons/script.infinity.rails')['movies'][0]
        self.assertNotIn('Add-on Settings',[x[0] for x in runtime.commands(row,'movies',self.xa,self.vfs)])
        (self.installed/'resources').mkdir();(self.installed/'resources/settings.xml').write_text('<settings/>')
        self.assertIn('Add-on Settings',[x[0] for x in runtime.commands(row,'movies',self.xa,self.vfs)])

    def test_options_cancel_closes_native_and_does_not_launch(self):
        rows=runtime.defaults(WORK/'addons/script.infinity.rails')['movies'];self.answers=[-1]
        runtime.options('movies',rows[0]['key']);self.assertEqual(self.calls,['Dialog.Close(contextmenu,true)'])

    def test_stale_token_cannot_launch(self):
        with self.assertRaises(store.RailError):runtime.open_card('movies','c:plugin.video.deleted')
        self.assertFalse(self.calls)

    def test_disabled_custom_cannot_launch(self):
        store.Store(self.profile).add('plugin.video.fixture',['movies'],{});self.enabled=False
        with self.assertRaises(store.RailError):runtime.open_card('movies','c:plugin.video.fixture')
        self.assertFalse(self.calls)

    def test_default_cannot_be_removed_by_forged_script(self):
        with self.assertRaises(store.RailError):runtime.remove_card('movies','b:0123456789abcdef')
        self.assertFalse(self.dialogs)


class GeometryTests(unittest.TestCase):
    def test_bounds_and_content_sizing_across_viewports(self):
        # Representative logical viewport shapes, not measured Fold surfaces.
        for width,height in [(1080,2400),(2400,1080),(1536,2152),(2152,1536),(640,900),(900,640),(360,640),(640,360),(300,280)]:
            for count in (2,4,5,12,257):
                with self.subTest(width=width,height=height,count=count):
                    b=menu.geometry(width,height,count);self.assertGreater(b.width,0);self.assertGreater(b.list_height,0)
                    self.assertGreaterEqual(b.x,0);self.assertGreaterEqual(b.y,0)
                    self.assertLessEqual(b.x+b.width,width);self.assertLessEqual(b.y+b.height,height)
                    self.assertLessEqual(b.list_height,count*82)

    def test_unusable_window_dismisses_safely(self):
        for w,h in [(100,800),(1000,150),(219,1000),(1000,251)]:self.assertIsNone(menu.geometry(w,h,5))

    def test_native_context_geometry_is_not_reused(self):
        source=(WORK/'addons/script.infinity.rails/resources/lib/menu.py').read_text()
        self.assertIn('self.getWidth(), self.getHeight()',source)
        self.assertNotIn('System.ScreenWidth',source)
        self.assertNotIn('control.setPosition',source)
        self.assertNotIn('control.setWidth',source)


class DialogCallbackTests(unittest.TestCase):
    def setUp(self):
        self.windows=[];self.event=('click',6);self.resize=False;test=self
        class Control:
            def __init__(obj):obj.items=[];obj.selected=1
            def setPosition(obj,x,y):obj.position=(x,y)
            def setWidth(obj,w):obj.width=w
            def setHeight(obj,h):obj.height=h
            def reset(obj):obj.items=[]
            def addItems(obj,items):obj.items=items
            def selectItem(obj,i):pass
            def getSelectedPosition(obj):return obj.selected
        class WindowXML:
            def __init__(obj,*args):obj.controls={i:Control() for i in (999,1,3,2,6)};obj.properties={};obj.closed=0;obj.w=1080;obj.h=2400;test.windows.append(obj)
            def getWidth(obj):return obj.w
            def getHeight(obj):return obj.h
            def getControl(obj,i):return obj.controls[i]
            def setProperty(obj,k,v):obj.properties[k]=v
            def setFocusId(obj,i):obj.focus=i
            def close(obj):obj.closed+=1
            def doModal(obj):
                obj.onInit()
                if test.resize:obj.w=700
                if test.event[0]=='click':obj.onClick(test.event[1])
                else:obj.onAction(types.SimpleNamespace(getId=lambda:test.event[1]))
        class Home:
            def getProperty(obj,key):return test.properties.get(key,'')
            def setProperty(obj,key,value):test.properties[key]=value
            def clearProperty(obj,key):test.properties.pop(key,None)
        self.properties={}
        self.gui=types.SimpleNamespace(WindowXMLDialog=WindowXML,ListItem=lambda label:label,Window=lambda _:Home())
        xbmc=types.SimpleNamespace(log=lambda *a:None,LOGERROR=3,LOGDEBUG=0)
        self.modules=patch.dict(sys.modules,{'xbmc':xbmc,'xbmcaddon':types.SimpleNamespace(),'xbmcvfs':types.SimpleNamespace()});self.modules.start()

    def tearDown(self):self.modules.stop()
    def choose(self):return menu.choose(self.gui,'INFINITY — RAIL OPTIONS',['Open','Move','Remove','Settings','Cancel'],'Empflix',root='/fixture')
    def test_selection_returns_index(self):self.assertEqual(self.choose(),1)
    def test_x_dismisses(self):self.event=('click',2);self.assertEqual(self.choose(),-1)
    def test_back_dismisses(self):
        for code in (9,10,92,117):
            self.event=('action',code);self.assertEqual(self.choose(),-1)
    def test_configuration_change_cannot_execute_stale_selection(self):self.resize=True;self.assertEqual(self.choose(),-1)
    def test_shape_property_cleans_up_after_cancel(self):
        self.event=('click',2);self.choose();self.assertEqual(self.properties,{})
    def test_no_extra_controls_or_blank_list(self):
        self.choose();w=self.windows[-1];self.assertEqual(len(w.controls[6].items),5);self.assertEqual(w.focus,6)
    def test_repeated_open_close_releases_dialog(self):
        for _ in range(100):self.choose()
        self.assertTrue(all(w.closed>=2 for w in self.windows))


if __name__=='__main__':unittest.main(verbosity=2)
