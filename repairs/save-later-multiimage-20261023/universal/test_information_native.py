"""Selected native branch test for the isolated Information resize callback."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import information_native as implementation


HARNESS = r'''
#include <cassert>
#include <memory>
#include <string>
constexpr int GUI_MSG_PAGE_CHANGE = 1;
constexpr int GUI_MSG_WINDOW_RESIZE = 2;
struct Message { int value; int GetParam1() const { return value; } };
struct Property { std::string value; std::string asString() const { return value; } };
struct Skin { std::string value = "skin.infinity.diggz"; std::string ID() const { return value; } };
Skin skin;
Skin* g_SkinInfo = &skin;
namespace URIUtils {
std::string GetFileName(const std::string& p) { return p.substr(p.find_last_of('/') + 1); }
void RemoveSlashAtEnd(std::string& p) { while (!p.empty() && p.back() == '/') p.pop_back(); }
std::string AddFileToFolder(const std::string& p, const std::string& f) { return p + "/" + f; }
}
namespace CSpecialProtocol { std::string TranslatePath(const std::string& p) { return p; } }
namespace ADDON {
enum class OnlyEnabled { CHOICE_YES };
struct Version { std::string value = "0.3.5.34"; std::string asString() const { return value; } };
struct Addon { ADDON::Version version; std::string path = "/data/addons/script.infinity.commandcenter";
  ADDON::Version Version() const { return version; } std::string Path() const { return path; } };
using AddonPtr = std::shared_ptr<Addon>;
}
struct Manager {
  bool enabled = true;
  ADDON::AddonPtr addon = std::make_shared<ADDON::Addon>();
  bool GetAddon(const char*, ADDON::AddonPtr& result, ADDON::OnlyEnabled) { result = addon; return enabled; }
} manager;
namespace CServiceBroker { Manager& GetAddonMgr() { return manager; } }
struct CGUIMediaWindow { int base_calls = 0; bool OnMessage(Message&) { ++base_calls; return false; } };
template <class T> struct CallbackFunction { CallbackFunction(T*, void(T::*)()) {} };
template <class T> T* ref(T* value) { return value; }
struct WindowXML : CGUIMediaWindow {
  WindowXML* window = this;
  std::string m_scriptPath = "/data/addons/script.infinity.commandcenter";
  std::string xml = m_scriptPath + "/resources/skins/Default/1080i/InfinityInformation.xml";
  int callbacks = 0, pulses = 0;
  Property GetProperty(const char*) { return {xml}; }
  void onInit() {}
  void invokeCallback(CallbackFunction<WindowXML>* call) { ++callbacks; delete call; }
  void PulseActionEvent() { ++pulses; }
  bool process(Message message) {
#define A(x) x
__ACTUAL_REPLACEMENT__
    return true;
  }
};
int main() {
  WindowXML target;
  assert(!target.process({GUI_MSG_WINDOW_RESIZE}));
  assert(target.base_calls == 1);
#if defined(TARGET_ANDROID)
  assert(target.callbacks == 1 && target.pulses == 1);
#else
  assert(target.callbacks == 0 && target.pulses == 0);
#endif
  WindowXML page;
  assert(!page.process({GUI_MSG_PAGE_CHANGE})); assert(page.callbacks == 0 && page.base_calls == 1);
  for (const std::string name : {"Cobra.xml", "DialogVideoInfo.xml", "InfinitySearch.xml", "InfinityHomeOptionB.xml"}) {
    WindowXML other; other.xml = "/data/addons/script.infinity.commandcenter/resources/skins/Default/1080i/" + name;
    assert(!other.process({GUI_MSG_WINDOW_RESIZE})); assert(other.callbacks == 0 && other.base_calls == 1);
  }
  WindowXML foreign; foreign.m_scriptPath = "/data/addons/plugin.video.cobra";
  assert(!foreign.process({GUI_MSG_WINDOW_RESIZE})); assert(foreign.callbacks == 0);
  WindowXML wrongxml; wrongxml.xml = "/data/other/InfinityInformation.xml";
  assert(!wrongxml.process({GUI_MSG_WINDOW_RESIZE})); assert(wrongxml.callbacks == 0);
  skin.value = "skin.estuary"; WindowXML wrongskin;
  assert(!wrongskin.process({GUI_MSG_WINDOW_RESIZE})); assert(wrongskin.callbacks == 0); skin.value = "skin.infinity.diggz";
  manager.enabled = false; WindowXML disabled;
  assert(!disabled.process({GUI_MSG_WINDOW_RESIZE})); assert(disabled.callbacks == 0); manager.enabled = true;
  manager.addon->version.value = "0.3.5.33"; WindowXML old;
  assert(!old.process({GUI_MSG_WINDOW_RESIZE})); assert(old.callbacks == 0);
}
'''


class NativeInformationTests(unittest.TestCase):
    def test_exact_actual_source_preimage_and_no_other_method_changes(self):
        path = os.environ.get('INFINITY_REFERENCE_WINDOW_XML')
        self.assertTrue(path, 'Exact signed-reference WindowXML.cpp required')
        raw = Path(path).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), implementation.BEFORE)
        fixed = implementation.patch(raw)
        undone = fixed.decode().replace(implementation.REPLACEMENT, implementation.ORIGINAL)
        undone = undone.replace('#include "addons/Addon.h"\n#include "addons/AddonManager.h"\n#include "filesystem/SpecialProtocol.h"',
                                '#include "addons/Addon.h"')
        self.assertEqual(undone.encode(), raw)
        with self.assertRaises(RuntimeError):
            implementation.patch(raw + b'\n')

    def test_compiled_actual_branch_android_owner_and_untouched_others(self):
        with tempfile.TemporaryDirectory(prefix='information-resize-') as temp:
            source = Path(temp) / 'native.cpp'
            source.write_text(HARNESS.replace('__ACTUAL_REPLACEMENT__', implementation.REPLACEMENT))
            for android in (False, True):
                output = Path(temp) / ('android' if android else 'other')
                command = ['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(output)]
                if android:
                    command.insert(1, '-DTARGET_ANDROID')
                compiled = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                subprocess.run([str(output)], check=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
