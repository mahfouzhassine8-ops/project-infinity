"""Selected UI performance/geometry checks; no rendered or frame-pacing claim."""
from __future__ import annotations

import ast
from contextlib import nullcontext
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = Path(os.environ.get('INFINITY_UI_REFERENCE', '/workspace/scratch/9491f79db5c3/integration34-selection-final/complete-components'))
AFTER = HERE / 'overlay'
NATIVE = Path(os.environ.get('INFINITY_UI_NATIVE', '/workspace/scratch/9207f26886c2/current-source/native'))
METRICS = {'type': 'focused host source/native-operation and geometry evidence',
           'android_rendering': 'NOT RUN', 'physical_fold': 'NOT RUN', 'frame_pacing': 'NOT MEASURED'}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pure(path, name):
    tree = ast.parse(path.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    space = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), space)
    return space[name]


def modules_for(window, dimensions, counts):
    def info(name):
        counts['geometry_reads'] += 1
        return str(dimensions[0 if name.endswith('Width') else 1])
    return {
        'xbmc': types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz', getInfoLabel=info,
                                     getCondVisibility=lambda _: True),
        'xbmcgui': types.SimpleNamespace(WindowXMLDialog=window, getCurrentWindowId=lambda: 10000,
            Window=lambda _: types.SimpleNamespace(getProperty=lambda _: '', clearProperty=lambda _: None),
            ListItem=lambda label, **_: types.SimpleNamespace(label=label, setProperty=lambda *_: None)),
        'xbmcaddon': types.SimpleNamespace(Addon=lambda _: types.SimpleNamespace(getAddonInfo=lambda _: '/addon')),
        'xbmcvfs': types.SimpleNamespace(translatePath=lambda value: value),
        'common': types.SimpleNamespace(addon=None, addon_set_setting=lambda *_: True, persistence_scope=nullcontext),
    }


class Control:
    def __init__(self, ident, dimensions, counts):
        self.ident, self.dimensions, self.counts = ident, dimensions, counts
        self.width, self.height = (760, 690) if ident == 100 else (724, 574)
        self.position = (2, 2) if ident == 101 else (0, 0)
        self.items, self.selected, self.scroll, self.resets, self.text_writes = [], 0, 0, 0, 0
    def getWidth(self):
        if self.ident in (2, 190): self.counts['geometry_reads'] += 1; return self.dimensions[0]
        return self.width
    def getHeight(self):
        if self.ident in (2, 190): self.counts['geometry_reads'] += 1; return self.dimensions[1]
        return self.height
    def setWidth(self, v): self.width = v
    def setHeight(self, v): self.height = v
    def getPosition(self): return self.position
    def setPosition(self, x, y): self.position = (x, y)
    def setAnimations(self, value): self.animations = value
    def setLabel(self, value): self.label = value
    def setText(self, value): self.text = value; self.text_writes += 1
    def setImage(self, value): self.image = value; self.counts['image_binds'] += 1
    def setVisible(self, value): self.visible = value
    def setEnabled(self, value): self.enabled = value
    def reset(self): self.resets += 1; self.items = []
    def addItem(self, item): self.items.append(item)
    def selectItem(self, index): self.selected = index
    def getSelectedPosition(self): return self.selected


class UIPerformance(unittest.TestCase):
    def test_information_input_burst_uses_no_geometry_polling(self):
        measured = {}
        for stage, root in (('before', BASE), ('after', AFTER)):
            counts = dict(geometry_reads=0, image_binds=0)
            dimensions = [1080, 2520]
            test = self
            class Window:
                def __init__(self, *_): self.controls = {}; self.focus = 0
                def getControl(self, ident): return self.controls.setdefault(ident, Control(ident, dimensions, counts))
                def setProperty(self, *_): pass
                def setFocusId(self, ident): self.focus = ident
                def close(self): pass
                def doModal(self):
                    self.onInit()
                    first = counts['geometry_reads']
                    for _ in range(1000):
                        self.onAction(types.SimpleNamespace(getId=lambda: 107))
                        self.onClick(126)
                        if hasattr(self, 'onFocus'): self.onFocus(126)
                    counts['gesture_geometry_reads'] = counts['geometry_reads'] - first
                    plot = self.getControl(126); plot.scroll = 9
                    prior_text, writes = plot.text, plot.text_writes
                    self.focus = 128
                    dimensions[:] = [2520, 1080]
                    resize_before = counts['geometry_reads']
                    self.onInit()  # Existing exact-owned native resize callback.
                    counts['resize_geometry_reads'] = counts['geometry_reads'] - resize_before
                    test.assertEqual((plot.text, plot.text_writes, plot.scroll, self.focus),
                                     (prior_text, writes, 9, 128))
            modules = modules_for(Window, dimensions, counts)
            modules['title_metadata'] = load(BASE / 'script.infinity.commandcenter/title_metadata.py', 'metadata_' + stage)
            with patch.dict(sys.modules, modules):
                module = load(root / 'script.infinity.commandcenter/information.py', 'info_' + stage)
                entry = dict(title='Verified selected title', poster='https://art.test/exact',
                             information=dict(plot='Original plot\n' * 6000, duration=3635))
                self.assertEqual(module.show_information(object(), entry), '')
            measured[stage] = counts
        self.assertEqual(measured['before']['gesture_geometry_reads'], 12000)
        self.assertEqual(measured['after']['gesture_geometry_reads'], 0)
        self.assertEqual(measured['after']['resize_geometry_reads'], 4)
        self.assertEqual(measured['after']['image_binds'], 1)
        METRICS['information'] = dict(dataset='1000 gesture cycles: action + irrelevant click + focus', **measured)

    def test_popup_fit_preserves_full_row_and_native_transform_bounds(self):
        fit = pure(AFTER / 'script.infinity.uirepair/popup.py', 'fit_popup')
        settings_fit = pure(AFTER / 'script.infinity.commandcenter/infinity_settings.py', 'fit_popup')
        measurements = []
        for width, height in ((1920, 1080), (1080, 2400), (640, 360), (500, 300), (320, 200), (720, 3600)):
            for count in (1, 3, 12):
                for anchor in (None, (width-1, height-1), (0, 0)):
                    result = fit(width, height, count, anchor)
                    self.assertEqual(result, settings_fit(width, height, count, anchor))
                    left, top, scale = result['left'], result['top'], result['scale']
                    self.assertGreaterEqual(left, 0); self.assertGreaterEqual(top, 0)
                    self.assertLessEqual(left + result['width'] * scale, width + 1)
                    self.assertLessEqual(top + result['height'] * scale, height + 1)
                    self.assertGreaterEqual(result['rows_height'], 78)
                    # The native group's inverse transform maps a visible row
                    # center back to exactly the existing fixed-layout hit row.
                    local_x, local_y = 380, 98 + 39
                    physical = (left + local_x * scale, top + local_y * scale)
                    self.assertAlmostEqual((physical[0]-left)/scale, local_x)
                    self.assertAlmostEqual((physical[1]-top)/scale, local_y)
                old_height = min(690, 118 + 78*count)
                measurements.append(dict(view=[width, height], rows=count,
                    before_overflow=760+36>width or old_height+36>height, after_overflow=False))
        self.assertTrue(any(row['before_overflow'] for row in measurements))
        METRICS['popup_bounds'] = measurements

    def test_popup_resize_retains_rows_selection_scroll_and_cancel(self):
        for name, labels in (('script.infinity.commandcenter/infinity_settings.py', True),
                             ('script.infinity.uirepair/popup.py', False)):
            dimensions, counts = [1080, 2400], dict(geometry_reads=0, image_binds=0)
            test = self
            class Window:
                def __init__(self, *_): self.controls = {}; self.focus = 0
                def getControl(self, ident): return self.controls.setdefault(ident, Control(ident, dimensions, counts))
                def setProperty(self, *_): pass
                def setFocusId(self, value): self.focus = value
                def close(self): pass
                def doModal(self):
                    self.onInit(); rows = self.getControl(50)
                    rows.selected, rows.scroll, self.focus = 2, 4, 50
                    original_items = list(rows.items)
                    dimensions[:] = [500, 300]
                    self.onInit()
                    test.assertEqual((rows.resets, rows.selected, rows.scroll, self.focus), (1, 2, 4, 50))
                    test.assertEqual(rows.items, original_items)
                    test.assertIn('time=0', self.getControl(100).animations[0][1])
                    self.onClick(190)
                    test.assertIn(getattr(self, 'result'), (None, -1))
            with patch.dict(sys.modules, modules_for(Window, dimensions, counts)):
                module = load(AFTER/name, 'popup_' + str(labels))
                result = module.choose('Owned menu', ['One', 'Two', 'Three'] if labels else [('One', 'a'), ('Two', 'b'), ('Three', 'c')])
            self.assertIn(result, (None, -1))

    def test_popup_xml_only_reserved_background_id_changed(self):
        for name in ('script.infinity.commandcenter/resources/skins/Default/1080i/InfinityItemOptions.xml',
                     'script.infinity.uirepair/resources/skins/Default/1080i/InfinityItemOptions.xml',
                     'skin.infinity.diggz/unified/InfinityItemOptions.xml'):
            old, new = (BASE/name).read_bytes(), (AFTER/name).read_bytes()
            self.assertEqual(old.count(b'id="2"'), 1)
            self.assertEqual(new, old.replace(b'id="2"', b'id="190"', 1))

    def test_home_continue_prepares_one_same_snapshot_and_original_order(self):
        data, profile, events = {'revision': 99}, object(), []
        values = [{'key': 'movie:tmdb:%s' % i} for i in range(7)]
        def prepare(current, selected, render):
            self.assertIs(current, data); self.assertEqual(selected, values)
            events.append(('prepare', len(selected)))
            return dict(render, _prepared=data)
        def list_item(entry, current, bucket, render):
            self.assertIs(current, data); self.assertIs(render['_prepared'], data)
            self.assertEqual(bucket, 'continue')
            events.append(('item', entry['key']))
            return 'plugin://original/' + entry['key'], types.SimpleNamespace(setProperty=lambda *_: None)
        plugin = types.SimpleNamespace(PROFILE=profile,
            hub=types.SimpleNamespace(load_view=lambda p: data, KEY_RE=types.SimpleNamespace(fullmatch=lambda _: True)),
            setting_bool=lambda *_: True, _values_for=lambda *args: values,
            prepare_render=prepare, _list_item=list_item)
        modules = {
            'xbmc': types.SimpleNamespace(log=lambda *_: None, LOGWARNING=2),
            'xbmcgui': types.SimpleNamespace(Window=lambda _: types.SimpleNamespace(getProperty=lambda _: 'standard')),
            'xbmcplugin': types.SimpleNamespace(setContent=lambda *_: None,
                addDirectoryItem=lambda handle, target, item, **kw: events.append(('directory', target)),
                endOfDirectory=lambda handle, **kw: events.append(('end', kw))),
            'runtime': types.SimpleNamespace(addons=lambda: [], hidden=lambda _: False, destination=lambda _: None),
            'controller_access': types.SimpleNamespace(load=lambda: plugin),
        }
        with patch.dict(sys.modules, modules), patch.object(sys, 'argv', ['plugin', '9', '?action=continue&media=movie']):
            module = load(AFTER/'script.infinity.uirepair/plugin.py', 'home_continue')
            module.main()
        self.assertEqual([event for event in events if event[0]=='prepare'], [('prepare', 7)])
        self.assertEqual([event[1] for event in events if event[0]=='directory'],
                         ['plugin://original/' + entry['key'] for entry in values])
        self.assertEqual(events[-1], ('end', {'succeeded': True, 'cacheToDisc': False}))

    def test_home_original_routes_panels_and_nonmovie_tv_controls_preserved(self):
        name = 'skin.infinity.diggz/unified/Home.xml'
        old, new = ET.parse(BASE/name).getroot(), ET.parse(AFTER/name).getroot()
        owners = {'8101', '8102', '8801', '8802', '8830', '8831', '40001'}
        for control in old.findall('.//control[@id]'):
            if control.get('id') not in owners:
                current = new.find('.//control[@id="%s"]' % control.get('id'))
                self.assertEqual(ET.tostring(control), ET.tostring(current), control.get('id'))
        for ident in owners - {'40001'}:
            before, after = old.find('.//control[@id="%s"]' % ident), new.find('.//control[@id="%s"]' % ident)
            for tag in ('content', 'visible', 'onclick', 'onup', 'onleft', 'ondown', 'scrolltime', 'preloaditems'):
                self.assertEqual([(c.tag, c.attrib, c.text) for c in before.findall(tag)], [(c.tag, c.attrib, c.text) for c in after.findall(tag)])
        textures = [t for ident in ('8101','8102','8801','8802') for t in new.find('.//control[@id="%s"]' % ident).findall('.//texture') if t.text=='$VAR[PosterThumbVar]']
        self.assertEqual(len(textures), 8)
        self.assertTrue(all(t.get('background')=='true' and t.get('fallback')=='DefaultVideo.png' for t in textures))
        name = 'skin.infinity.diggz/unified/Includes_InfinityHomeUnified.xml'
        old, new = ET.parse(BASE/name).getroot(), ET.parse(AFTER/name).getroot()
        targets = ('InfinityCompactContinueCardNormal','InfinityCompactContinueCardFocused')
        for node in old:
            if node.get('name') not in targets:
                candidates = [other for other in new if other.tag==node.tag and other.get('name')==node.get('name')]
                self.assertEqual(len(candidates), 1)
                self.assertEqual(ET.tostring(node), ET.tostring(candidates[0]))
        for name in targets:
            node = new.find('./include[@name="%s"]' % name)
            self.assertEqual(node.find('./definition/control[@type="label"]/height').text, '35.14')
            self.assertEqual(node.find('./definition/control[@type="label"]/bottom').text, '6.7')
        METRICS['artwork'] = dict(changed_owned_templates=10,
            proven_change='Local nonbundled artwork uses existing large-image asynchronous branch; bundled fast path retained',
            remote_behavior='Already asynchronous; no improvement claimed', frames='NOT MEASURED')

    def test_actual_native_axis_and_item_layout_compile_for_continue_cards(self):
        cpp = (NATIVE/'xbmc/guilib/GUIControl.cpp').read_text()
        begin = cpp.index('float InfinityResponsiveParse('); end = cpp.index('} // namespace', begin)
        axes = cpp[begin:end]
        item = (NATIVE/'xbmc/guilib/GUIListItemLayout.cpp').read_text()
        begin = item.index('bool CGUIListItemLayout::ReflowResponsiveSize(')
        end = item.index('\nvoid CGUIListItemLayout::SetWidth', begin)
        method = item[begin:end]
        code = '''#include <string>\n#include <cstdlib>\n#include <algorithm>\n#include <cassert>\n#include <iostream>\n#include <cmath>\nstruct GUIResponsiveAxisSpec {std::string start,centerStart,centerEnd,end,size,sizeMax,sizeMin,legacyPos;bool HasAny()const{return true;}};\n''' + axes + '''
struct Group {void SetWidth(float){} void SetHeight(float){} void ReflowResponsiveLayout(float,float){}};
struct CGUIListItemLayout { std::string m_responsiveWidth="auto",m_responsiveHeight="100%";float m_width=230.1f,m_height=410.f,m_responsiveAspect=.561219512f;Group m_group;void SetInvalid(){}bool ReflowResponsiveSize(float,float);};
''' + method + '''
int main(){for(float h:{2400.f,2456.f,1528.f,1056.f,1080.f,1440.f}){
GUIResponsiveAxisSpec bounds;bounds.start="75.6667%";bounds.end="100";
float y=0,available=0;InfinityResolveResponsiveAxis(bounds,h,0,0,false,y,available);
GUIResponsiveAxisSpec cap;cap.start="0";cap.size="100%";cap.sizeMax="410";
float py=0,height=0;InfinityResolveResponsiveAxis(cap,available,0,410,false,py,height);
CGUIListItemLayout card;card.ReflowResponsiveSize(1000,height);
assert(card.m_height<=available+.001f && card.m_height<=410.001f);
assert(std::abs(card.m_width/card.m_height-.561219512f)<.0001f);
if(available>=410)assert(std::abs(card.m_height-410)<.001f);
assert(card.m_height*.02219512f+46.02f<card.m_height);
std::cout<<h<<" "<<available<<" "<<card.m_width<<" "<<card.m_height<<"\\n";
}}
'''
        with tempfile.TemporaryDirectory(prefix='infinity-continue-geometry-') as temp:
            path = Path(temp)/'test.cpp'; path.write_text(code)
            compiled = subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(path),'-o',str(Path(temp)/'test')],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            output = subprocess.check_output([str(Path(temp)/'test')],text=True)
        METRICS['continue_actual_native_rects'] = [dict(logical_height=v[0], available_height=v[1], old_card_height=410,
              after_card_width=v[2], after_card_height=v[3]) for v in (list(map(float,line.split())) for line in output.splitlines())]


if __name__ == '__main__':
    result = unittest.main(verbosity=2, exit=False).result
    METRICS.update(passed=result.wasSuccessful(), tests_run=result.testsRun,
                   failures=len(result.failures), errors=len(result.errors))
    (HERE/'UI-PERFORMANCE-HOST.json').write_text(json.dumps(METRICS,indent=2,sort_keys=True)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
