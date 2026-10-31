"""Exact signed input/generated XML and monitor fixtures; not a Kodi renderer."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import skin_coverage
from baseline_contract import SKIN
from test_task_ownership import loading, context

class Window:
    def __init__(self): self.values = {}; self.focus = 8801
    def setProperty(self, k, v): self.values[k] = v
    def getProperty(self, k): return self.values.get(k, '')
    def clearProperty(self, k): self.values.pop(k, None)
    def getFocusId(self): return self.focus

class Gui:
    def __init__(self): self.windows = {}; self.dialog = 9999
    def Window(self, n): return self.windows.setdefault(n, Window())
    def getCurrentWindowId(self): return 10000
    def getCurrentWindowDialogId(self): return self.dialog

class Xbmc:
    class Monitor: pass
    def getSkinDir(self): return 'skin.infinity.diggz'
    def getInfoLabel(self, s): return ''
    def getCondVisibility(self, s): return False

def tree_shape(node):
    return (node.tag, sorted(node.attrib.items()), (node.text or '').strip(),
            [tree_shape(child) for child in node])

def remove_additions(raw):
    # Remove only marker-bound new elements. Original signed V1 observers,
    # controls, geometry, conditions and onloads remain in this comparison.
    nodes = skin_coverage.legacy.nodes(raw)
    marker = ('<!-- ' + skin_coverage.MARKER + ' -->').encode()
    remove = []
    for node in nodes:
        if node.tag not in ('include', 'onclick', 'onload'): continue
        prefix = raw[:node.start].rstrip()
        if prefix.endswith(marker): remove.append((node.start, node.end))
    for a, b in sorted(remove, reverse=True): raw = raw[:a] + raw[b:]
    return raw

class CoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = ZipFile(os.environ['BASELINE_COMPONENT'])
        cls.staged = Path(os.environ['LOADING_STAGE'])
        cls.plan = json.loads((cls.staged/'PLAN.json').read_text())

    @classmethod
    def tearDownClass(cls): cls.archive.close()

    def candidate(self, name):
        path = self.staged/'members'/name.removeprefix('payload/')
        return path.read_bytes() if path.exists() else self.archive.read(name)

    def test_original_actions_controls_and_geometry_preserved(self):
        checked = 0
        for name in self.archive.namelist():
            if not name.startswith(SKIN+'unified/') or not name.endswith('.xml'): continue
            if name.endswith(('/DialogBusy.xml','/Includes_InfinityActionLoading.xml')): continue
            before = ET.fromstring(self.archive.read(name))
            after = ET.fromstring(remove_additions(self.candidate(name)))
            with self.subTest(name=name): self.assertEqual(tree_shape(before), tree_shape(after))
            checked += 1
        self.assertGreater(checked, 190)

    def test_protected_xml_members_identical(self):
        count = 0
        for name in self.archive.namelist():
            if not name.startswith(SKIN+'unified/') or not name.endswith('.xml'): continue
            if name.endswith('/DialogBusy.xml'): continue
            if any(p.lower() in Path(name).name.lower() for p in skin_coverage.PROTECTED):
                self.assertEqual(self.archive.read(name), self.candidate(name), name); count += 1
        self.assertGreater(count, 5)

    def test_native_busy_fallback_retains_controls(self):
        name = SKIN+'unified/DialogBusy.xml'
        before = ET.fromstring(self.archive.read(name)); after = ET.fromstring(self.candidate(name))
        group = before.find('./controls/control'); hidden = group.find('visible')
        self.assertEqual(hidden.text, 'false'); group.remove(hidden)
        candidate_group=after.find('./controls/control')
        self.assertIn('Window.IsActive(10025)',candidate_group.findtext('visible'))
        candidate_group.remove(candidate_group.find('visible'))
        for extra in list(after.find('controls'))[1:]:after.find('controls').remove(extra)
        self.assertEqual(tree_shape(before), tree_shape(after))
        self.assertIsNotNone(after.find('.//control[@type="progress"][@id="10"]'))

    def test_frame_motion_and_reduced_motion_unchanged(self):
        name = SKIN+'unified/Includes_InfinityActionLoading.xml'
        before = ET.fromstring(self.archive.read(name)); after = ET.fromstring(self.candidate(name))
        vb = before.findall('.//visible'); va = after.findall('.//visible')
        self.assertEqual(len(vb), len(va))
        self.assertIn('Window.Property(Infinity.Loading.OwnerToken)', va[0].text)
        self.assertIn('!Window.IsActive(progressdialog)',va[0].text)
        param=after.find('.//param[@name="nativebusy"]')
        self.assertEqual(param.get('default'),'false')
        after.find('include').remove(param)
        va[0].text = vb[0].text
        self.assertEqual(tree_shape(before), tree_shape(after))

    def test_duplicate_route_is_instrumented_per_control(self):
        raw = b'<window><controls><control type="button" id="10"><onclick>ActivateWindow(Videos)</onclick></control><control type="button" id="20"><onclick>ActivateWindow(Videos)</onclick></control></controls></window>'
        candidate, counts = skin_coverage.transform(raw, 'Example.xml')
        self.assertEqual(counts['actions'], 2)
        again, counts2 = skin_coverage.transform(candidate, 'Example.xml')
        self.assertEqual(again, candidate); self.assertEqual(counts2['actions'], 0)

    def test_registered_windows_match_reachable_frames(self):
        windows = self.plan['registered_windows']
        self.assertGreater(len(windows), 10)
        for name, ids in windows.items():
            root = ET.fromstring(self.candidate(name))
            self.assertEqual(root.tag, 'window')
            expected = 'SetProperty(Infinity.Loading.FrameControls,|'+'|'.join(ids)+'|)'
            self.assertEqual([n.text for n in root.findall('onload')].count(expected), 1)
            self.assertTrue(all(x.isdigit() and int(x)>0 for x in ids))
        # Registration uses real shared definitions, including native list views.
        self.assertIn('50', windows[SKIN+'unified/MyVideoNav.xml'])

    def fixture(self, ctx):
        gui = Gui(); monitor = loading.make_monitor(Xbmc(), gui)
        self.tick(monitor, ctx, 1)
        owner = {k:ctx[k] for k in loading.IDENTITY}; owner['epoch'] = monitor.epoch
        event = dict(state='action', target='a'*64, owner=owner)
        return gui, monitor, event

    def tick(self, monitor, ctx, now, event=None):
        with patch.object(loading, '_context', return_value=ctx), patch.object(loading.time, 'monotonic', return_value=now):
            if event: monitor.onNotification(loading.SENDER, loading.EVENT, json.dumps(event))
            monitor.tick()

    def test_window_local_token_isolation_and_cleanup(self):
        ctx = context(busy=True); gui, monitor, event = self.fixture(ctx)
        self.tick(monitor, ctx, 2, event); self.tick(monitor, ctx, 2.5)
        token = gui.Window(10000).getProperty(loading.PREFIX+'OwnerToken')
        self.assertTrue(token)
        self.assertEqual(gui.Window(10025).getProperty(loading.PREFIX+'OwnerToken'), '')
        self.tick(monitor, context(window=10025), 3)
        self.assertEqual(gui.Window(10000).getProperty(loading.PREFIX+'OwnerToken'), '')
        self.assertEqual(gui.Window(10000).getProperty(loading.PREFIX+'Active'), 'false')

    def test_busy_dispatch_remains_observed_until_native_end(self):
        ctx = context(busy=True); gui, monitor, event = self.fixture(ctx)
        self.tick(monitor, ctx, 2, event)
        self.tick(monitor, ctx, 2.5, dict(event, state='dispatched'))
        self.assertEqual(gui.Window(10000).getProperty(loading.PREFIX+'Active'), 'true')
        self.tick(monitor, context(busy=False), 3)
        self.assertEqual(gui.Window(10000).getProperty(loading.PREFIX+'Active'), 'false')

    def test_dispatch_without_busy_does_not_fake_readiness(self):
        ctx = context(); gui, monitor, event = self.fixture(ctx)
        self.tick(monitor, ctx, 2, event)
        self.tick(monitor, ctx, 2.5, dict(event, state='dispatched'))
        self.assertIsNone(monitor.state.action)
        self.assertEqual(gui.Window(10000).getProperty(loading.PREFIX+'Global'), 'false')

    def test_no_modal_native_sentinel_keeps_active_window(self):
        gui = Gui()
        self.assertEqual(loading._context(Xbmc(), gui)['window'], 10000)

    def test_modal_context_owns_its_controls(self):
        gui = Gui(); gui.dialog = 10140
        gui.Window(10140).focus = 45
        gui.Window(10140).setProperty(loading.PREFIX+'FrameControls', '|45|')
        ctx = loading._context(Xbmc(), gui)
        self.assertEqual(ctx['window'], 10140); self.assertEqual(ctx['control'], 45)
        self.assertTrue(ctx['framed'])
        gui.dialog = 10138
        self.assertEqual(loading._context(Xbmc(), gui)['window'], 10000)

if __name__ == '__main__':
    names = json.loads((ROOT/'SCOPE.json').read_text())['selected_coverage_tests']
    assert sorted(names) == unittest.defaultTestLoader.getTestCaseNames(CoverageTests)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(CoverageTests(n) for n in names))
    raise SystemExit(not result.wasSuccessful())
