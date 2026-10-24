"""Focused actual native resize predicate; no Android execution or shutdown."""
from __future__ import annotations
import hashlib, importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
import popup_native as implementation
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'universal'))
from test_information_native import HARNESS

CASES=r'''
void check(WindowXML value, int callbacks, int message=GUI_MSG_WINDOW_RESIZE) {
  value.window=&value; // copied test wrapper must refer to its own properties
  assert(!value.process({message})); assert(value.base_calls==1);
#if defined(TARGET_ANDROID)
  assert(value.callbacks==callbacks && value.pulses==callbacks);
#else
  assert(value.callbacks==0 && value.pulses==0);
#endif
}
int main() {
  const std::string cc="/data/addons/script.infinity.commandcenter";
  const std::string ui="/data/addons/script.infinity.uirepair";
  const std::string active="/data/addons/skin.infinity.diggz/unified/InfinityItemOptions.xml";
  WindowXML info; check(info,1); // retained exact CC34
  WindowXML popup;popup.xml=active;check(popup,0); // old popup gets no new callback
  manager.addon->version.value="0.3.5.35";
  check(info,1);check(popup,1);
  WindowXML fallback;fallback.xml=cc+"/resources/skins/Default/1080i/InfinityItemOptions.xml";check(fallback,1);
  WindowXML uiPopup;uiPopup.m_scriptPath=ui;uiPopup.xml=active;check(uiPopup,1);
  WindowXML uiFallback=uiPopup;uiFallback.xml=ui+"/resources/skins/Default/1080i/InfinityItemOptions.xml";check(uiFallback,1);
  WindowXML uiInfo=uiPopup;uiInfo.xml=ui+"/resources/skins/Default/1080i/InfinityInformation.xml";check(uiInfo,0);
  manager.uirepair->version.value="0.1.17";check(uiPopup,0);manager.uirepair->version.value="0.1.18";
  WindowXML wrong=popup;wrong.m_scriptPath="/data/addons/plugin.video.cobra";check(wrong,0);
  wrong=popup;wrong.xml="/data/other/InfinityItemOptions.xml";check(wrong,0);
  wrong=info;wrong.xml="/data/other/InfinityInformation.xml";check(wrong,0);
  wrong=popup;wrong.xml="/data/addons/skin.infinity.diggz/unified/DialogVideoInfo.xml";check(wrong,0);
  wrong=popup;wrong.xml="/data/addons/skin.infinity.diggz/unified/Cobra.xml";check(wrong,0);
  check(info,0,GUI_MSG_PAGE_CHANGE);check(popup,0,GUI_MSG_PAGE_CHANGE);
  skin.value="skin.cobra";check(info,0);check(popup,0);skin.value="skin.infinity.diggz";
  manager.enabled=false;check(info,0);check(popup,0);manager.enabled=true;
  manager.addon->version.value="0.3.5.33";check(info,0);check(popup,0);
}
'''

def harness():
    value=HARNESS[:HARNESS.index('int main()')]
    value=value.replace('std::string ID() const { return value; }','std::string ID() const { return value; } std::string Path() const { return "/data/addons/skin.infinity.diggz"; }')
    value=value.replace('  bool GetAddon(const char*, ADDON::AddonPtr& result, ADDON::OnlyEnabled) { result = addon; return enabled; }',
        '  ADDON::AddonPtr uirepair = [] { auto p=std::make_shared<ADDON::Addon>();p->path="/data/addons/script.infinity.uirepair";p->version.value="0.1.18";return p;}();\n'
        '  bool GetAddon(const char* id, ADDON::AddonPtr& result, ADDON::OnlyEnabled) { result=std::string(id)=="script.infinity.uirepair" ? uirepair : addon;return enabled; }')
    replacement=implementation.retained.REPLACEMENT.replace(implementation.ANCHOR,implementation.EXTENSION)
    return value.replace('__ACTUAL_REPLACEMENT__',replacement)+CASES

class PopupResize(unittest.TestCase):
    def test_preimage_and_retained_bridge_exact(self):
        source=Path(os.environ['INFINITY_REFERENCE_WINDOW_XML']);raw=source.read_bytes()
        current=implementation.retained.patch(raw);updated=implementation.patch(raw,current)
        self.assertEqual(updated.decode().replace(implementation.EXTENSION,implementation.ANCHOR,1).encode(),current)
        self.assertIn(implementation.retained.REPLACEMENT[:implementation.retained.REPLACEMENT.index(implementation.ANCHOR)],updated.decode())
        with self.assertRaises(RuntimeError):implementation.patch(raw,current+b'\n')
        with self.assertRaises(RuntimeError):implementation.patch(raw+b'\n',current)
    def test_compiled_actual_resize_body(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'resize.cpp';source.write_text(harness())
            for android in (False,True):
                binary=Path(temp)/('android' if android else 'other')
                command=['g++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-parameter',str(source),'-o',str(binary)]
                if android:command.insert(1,'-DTARGET_ANDROID')
                subprocess.run(command,check=True,capture_output=True,text=True,timeout=60)
                subprocess.run([str(binary)],check=True,timeout=10)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PopupResize))
    source=Path(os.environ['INFINITY_REFERENCE_WINDOW_XML']).read_bytes()
    sha=lambda b:hashlib.sha256(b).hexdigest()
    report=dict(host='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,
        scope='Actual native body compiled with controlled APIs; all predicates exercised; no GUI rendering claim',
        source_sha256=sha(source),patched_source_sha256=sha(implementation.patch(source,implementation.retained.patch(source))),
        patch_sha256=sha(Path(implementation.__file__).read_bytes()),test_sha256=sha(Path(__file__).read_bytes()),
        compiled_harness_sha256=sha(harness().encode()),android17='NOT RUN',physical_fold='NOT RUN',shutdown='NOT RUN')
    (HERE/'NATIVE-RESIZE-HOST.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
