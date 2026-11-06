"""Focused frozen-source host proof; no Android or physical acceptance claim."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET

from prepare_candidate import HERE, ROOT, SKIN, prepare

NATIVE = Path('/tmp/kodi451-restored-native/xbmc/guilib')


def method(text, declaration):
    start = text.index(declaration)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


class InfoAndPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir='/dev/shm')
        cls.candidate = Path(cls.temp.name) / 'candidate'
        prepare(cls.candidate)
        cls.before = ET.parse(SKIN / 'DialogVideoInfo.xml').getroot()
        cls.after = ET.parse(cls.candidate / 'DialogVideoInfo.xml').getroot()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_native_initial_width_fails_before_and_passes_after(self):
        source_map = json.loads((ROOT/'repairs/infinity-2103460-nine-corrections-20261106/downloads-native/SIGNED460-NATIVE-SOURCE-MAP.json').read_text())
        for leaf in ('GUIControlGroupList.cpp','GUIWindow.cpp','GUIControlFactory.cpp',
                     'GUIControlGroup.cpp','GUIVideoControl.cpp'):
            self.assertEqual(hashlib.sha256((NATIVE/leaf).read_bytes()).hexdigest(),
                             source_map['xbmc/guilib/'+leaf],leaf)
        self.assertEqual(hashlib.sha256((NATIVE.parent/'video/dialogs/GUIDialogVideoInfo.cpp').read_bytes()).hexdigest(),
                         source_map['xbmc/video/dialogs/GUIDialogVideoInfo.cpp'])
        raw = (NATIVE / 'GUIControlGroupList.cpp').read_text()
        actual = '\n'.join(method(raw, signature) for signature in (
            'float CGUIControlGroupList::GetWidth() const',
            'void CGUIControlGroupList::SetMinSize(float minWidth, float minHeight)'))
        window = (NATIVE / 'GUIWindow.cpp').read_text()
        load = method(window, 'void CGUIWindow::LoadControl(')
        self.assertLess(load.index('grp->GetWidth()'), load.index('LoadControl(pSubControl'))
        factory = method((NATIVE/'GUIControlFactory.cpp').read_text(),
                         'bool CGUIControlFactory::GetDimension(')
        self.assertIn('min = ParsePosition(pNode->Attribute("min"), parentSize)', factory)
        ctor = method(raw, 'CGUIControlGroupList::CGUIControlGroupList(')
        self.assertIn('m_totalSize = 0', ctor)
        self.assertIn('m_minSize = 0', ctor)
        widths = []
        for logical_width in (1080, 2400, 1440, 1920):
            group = logical_width * .86
            widths.append((logical_width, group))
        checks = []
        for logical, group in widths:
            checks.append(f'''{{ CGUIControlGroupList b({group}f), a({group}f);
              b.SetMinSize(0,0); a.SetMinSize({group}f,0);
              assert(b.GetWidth()==0); assert(a.GetWidth()>0);
              const float button=a.GetWidth()*.23f;
              assert(button>100); assert(4*button+3*8<=a.GetWidth()); }}''')
        cpp = '''#include <cassert>
        enum { VERTICAL, HORIZONTAL };
        #define CLAMP(x,low,high) (((x)>(high))?(high):(((x)<(low))?(low):(x)))
        struct CGUIControlGroup { float m_width; float GetWidth() const {return m_width;} };
        struct CGUIControlGroupList : CGUIControlGroup {
          int m_orientation=HORIZONTAL; float m_totalSize=0,m_minSize=0;
          explicit CGUIControlGroupList(float w) {m_width=w;}
          float GetWidth() const; void SetMinSize(float,float);
        };
        ''' + actual + '\nint main(){' + '\n'.join(checks) + '}\n'
        source = Path(self.temp.name)/'actual-group-methods.cpp'
        source.write_text(cpp)
        # /dev/shm is noexec; use a tiny temporary executable, never a user file.
        fd, binary = tempfile.mkstemp(prefix='infinity-info-proof-', dir='/tmp')
        os.close(fd)
        try:
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',binary], check=True, capture_output=True)
            subprocess.run([binary], check=True, capture_output=True)
        finally:
            Path(binary).unlink(missing_ok=True)
        width = self.after.find('.//control[@id="9000"]/width')
        self.assertEqual((width.text,width.attrib),('auto',{'min':'86%','max':'86%'}))

    def test_video_cannot_preempt_buttons_or_cast_after_candidate(self):
        controls = self.after.find('controls')
        before = list(self.before.find('controls'))
        after = list(controls)
        video = controls.find('control[@type="videowindow"]')
        group = controls.find('control[@id="9000"]')
        cast = controls.find('control[@id="50"]')
        self.assertGreater(before.index(self.before.find('.//control[@type="videowindow"]')),
                           before.index(self.before.find('.//control[@id="9000"]')))
        self.assertLess(after.index(video),after.index(group))
        self.assertLess(after.index(video),after.index(cast))
        # Element tails are indentation at the new sibling position, not content.
        original_video = self.before.find('.//control[@type="videowindow"]')
        self.assertEqual((video.attrib,[(e.tag,e.attrib,e.text) for e in video]),
                         (original_video.attrib,[(e.tag,e.attrib,e.text) for e in original_video]))
        native = method((NATIVE/'GUIControlGroup.cpp').read_text(), 'EVENT_RESULT CGUIControlGroup::SendMouseEvent(')
        self.assertIn('m_children.rbegin()',native)
        hit = method((NATIVE/'GUIVideoControl.cpp').read_text(),'EVENT_RESULT CGUIVideoControl::OnMouseEvent(')
        self.assertIn('ACTION_MOUSE_LEFT_CLICK',hit)
        self.assertIn('GUI_MSG_FULLSCREEN',hit)

    def test_native_play_once_and_all_existing_actions_and_ids_preserved(self):
        for cid in ('8','9011','9012','9013','106','50','400','61'):
            old = self.before.find(f'.//control[@id="{cid}"]')
            new = self.after.find(f'.//control[@id="{cid}"]')
            self.assertIsNotNone(old,cid)
            self.assertEqual(ET.canonicalize(ET.tostring(old),strip_text=True),
                             ET.canonicalize(ET.tostring(new),strip_text=True),cid)
        self.assertEqual(self.after.findtext('defaultcontrol'),'8')
        self.assertEqual(self.after.findall('.//control[@id="8"]/onclick'),[])
        native = (NATIVE.parent/'video/dialogs/GUIDialogVideoInfo.cpp').read_text()
        self.assertIn('#define CONTROL_BTN_PLAY             8',native)
        self.assertIn('else if (iControl == CONTROL_BTN_PLAY)\n      {\n        Play();',native)

    def test_existing_watched_states_are_not_hidden(self):
        old = ET.parse(SKIN/'Includes_InfinityMediaLists.xml').getroot()
        new = ET.parse(self.candidate/'Includes_InfinityMediaLists.xml').getroot()
        xpath = './/include[@name="InfinityMedia_BrowserRow"]//control[texture="$VAR[ListItemOverlay]"]'
        a,b = old.find(xpath),new.find(xpath)
        self.assertIsNotNone(a)
        self.assertNotIn('OverlayWatched.png',a.findtext('visible'))
        self.assertIn('String.IsEqual(ListItem.Overlay,OverlayWatched.png)',b.findtext('visible'))
        self.assertIn('String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),true)',b.findtext('visible'))
        b.find('visible').text = a.findtext('visible')
        self.assertEqual(ET.tostring(old),ET.tostring(new))

    def test_existing_menu_retains_both_watched_actions_without_writer_changes(self):
        p = Path('/dev/shm/infinity2103460-reference/assets/addons/script.infinity.commandcenter/plugin.py')
        tree = ast.parse(p.read_bytes())
        fn = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_menu_rows')
        hub = SimpleNamespace(entry_identity=lambda e:e.get('identity'),
                              is_watched=lambda d,k:k in d.get('watched',{}),
                              bucket_has=lambda *a:False)
        env = dict(hub=hub,_later_keys=lambda *a:[],_menu_resume=lambda *a:None,number=float)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),env)
        entry = dict(key='fixture',identity={'kind':'movie'})
        self.assertIn(('Mark Watched','mark-watched',''),env['_menu_rows'](entry,{}))
        self.assertIn(('Mark Unwatched','mark-unwatched',''),env['_menu_rows'](entry,{'watched':{'fixture':{}}}))
        self.assertIn(('Mark Unwatched','mark-unwatched',''),env['_menu_rows'](dict(entry,_native_watched=True),{}))
        # This proves source availability only, not device touch or persistence.

    def test_all_four_physically_passed_features_and_runtime_sources_untouched(self):
        inventory = json.loads((ROOT/'repairs/infinity-2103460-nine-corrections-20261106/SOURCE-INVENTORY.json').read_text())
        for source,row in inventory['changed_source_files'].items():
            self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),row['candidate_sha256'],source)
        for relative in ('downloads-native/native/xbmc/video/windows/GUIWindowVideoNav.cpp',
                         'downloads-native/native/xbmc/video/windows/GUIWindowVideoNav.h',
                         'downloads-native/native/xbmc/dialogs/GUIDialogMediaSource.cpp',
                         'downloads-native/native/xbmc/dialogs/GUIDialogMediaSource.h'):
            source='repairs/infinity-2103460-nine-corrections-20261106/'+relative
            original=subprocess.check_output(['git','show','0aa597f1:'+source],cwd=ROOT)
            self.assertEqual((ROOT/source).read_bytes(),original,source)
        # Drawer and library actions are among the fourteen complete-file hashes.
        self.assertTrue(any('Custom_1198_InfinityNav.xml' in p for p in inventory['changed_source_files']))
        self.assertTrue(any('/library_navigation.py' in p for p in inventory['changed_source_files']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
