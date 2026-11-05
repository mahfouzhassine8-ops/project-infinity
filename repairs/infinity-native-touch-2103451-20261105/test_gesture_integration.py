"""Compile real touch/dispatcher bodies against explicit mocked UI boundaries."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
BASE=Path('/tmp/kodi451-restored-native')  # these two files are independently pinned

def region(text,start,end):return text[text.index(start):text.index(end,text.index(start))]

def build_run(native,label):
    container=(native/'xbmc/guilib/GUIBaseContainer.cpp').read_text()
    input_=(native/'xbmc/input/InputManager.cpp').read_text()
    helper=region(container,'enum class InfinityTouchDecision','} // No GUI, file I/O or callback')
    framing=region(container,'static void InfinitySelectionField(', 'bool CGUIBaseContainer::OnInfinityOptionBLongPress(')
    framing=framing[:framing.index('\n}')+2]
    body=region(container,'bool CGUIBaseContainer::OnInfinityMediaTouch(', 'bool CGUIBaseContainer::OnInfinityAddonBrowserTouch(')
    block=region(input_,'      // INFINITY_2103394_MEDIA_TOUCH:', '\n#endif\n\n      if (newEvent.touch.action == ACTION_TOUCH_TAP)')
    focus=region(container,'bool CGUIBaseContainer::OnMessage(CGUIMessage& message)\n{', '\n  if (message.GetControlId() == GetID() )').split('{',1)[1]
    source='#define TARGET_ANDROID\n'+(HERE/'gesture_fixture.hpp').read_text()+helper+framing
    source+='\nvoid CGUIBaseContainer::LoseFocusTo(int target){\nCGUIMessage message(GUI_MSG_LOSTFOCUS,GetID(),target);\n'+focus+'\nfocused=false;\n}\n'
    source+=body+'\nbool DispatchActualBlock(Event newEvent){bool consumed=true;do{\n'+block+'\nconsumed=false;}while(false);return consumed;}\n'
    source+=(HERE/'gesture_cases.cpp').read_text()
    with tempfile.TemporaryDirectory(prefix='infinity-touch-method-',dir='/tmp') as tmp:
        p=Path(tmp);(p/'fixture.cpp').write_text(source)
        command=['c++','-std=c++17','-pthread','-O0','-Wall','-Wextra','-Werror',str(p/'fixture.cpp'),'-o',str(p/'fixture')]
        compile_=subprocess.run(command,capture_output=True,text=True)
        (HERE/(label+'-COMPILE.txt')).write_text(compile_.stdout+compile_.stderr)
        if compile_.returncode:raise AssertionError(compile_.stderr)
        result=subprocess.run([str(p/'fixture')],capture_output=True,text=True)
        (HERE/(label+'-GESTURES.txt')).write_text(result.stdout+result.stderr)
        print(label+': '+result.stdout.strip())
        return result

class GestureIntegration(unittest.TestCase):
    def test_before_reports_original_touch_gaps(self):
        pins=json.loads((HERE/'APPLIED-SOURCE-DELTA.json').read_text())['changed_files']
        for name,row in pins.items():self.assertEqual(hashlib.sha256((BASE/name).read_bytes()).hexdigest(),row['before_sha256'])
        result=build_run(BASE,'BEFORE')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('FAIL untyped provider first tap selects only',result.stdout)
        self.assertIn('FAIL native Favorites first tap',result.stdout)

    def test_exact_candidate_method_dispatcher_and_negative_cases(self):
        result=build_run(HERE/'native','AFTER')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('0 failing',result.stdout)

if __name__=='__main__':unittest.main(verbosity=2)
