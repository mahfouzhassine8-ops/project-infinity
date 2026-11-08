"""Run the real extracted API and GuiLock functions against a host test adapter.

This tests the observed access boundary and existing lock ordering. It is not
an Android native crash replay or evidence of a completed production repair.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def function(text, marker):
    start = text.index(marker)
    opening = text.index('{', start)
    depth = 1
    position = opening + 1
    while depth:
        if text[position] == '{':
            depth += 1
        elif text[position] == '}':
            depth -= 1
        position += 1
    return text[start:position]


ADAPTER = r'''
#include <algorithm>
#include <atomic>
#include <cassert>
#include <chrono>
#include <cctype>
#include <future>
#include <iostream>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <vector>
using String = std::string;
#define XBMC_TRACE
thread_local int depth = 0;
thread_local std::vector<std::string> events;
std::atomic<int> attempted{0};
std::recursive_mutex frame;
struct Application {
  void LockFrameMoveGuard() { ++attempted; frame.lock(); ++depth; events.push_back("lock_frame_graphics"); }
  void UnlockFrameMoveGuard() { events.push_back("unlock_frame_graphics"); --depth; frame.unlock(); }
} g_application;
namespace XBMCAddon {
struct LanguageHook {
  static LanguageHook* GetLanguageHook() { static LanguageHook hook; return &hook; }
  void DelayedCallOpen() { events.push_back("release_python"); }
  void DelayedCallClose() { events.push_back("restore_python"); }
};
}
namespace XBMCAddonUtils {
class GuiLock {
public:
  GuiLock(XBMCAddon::LanguageHook*, bool);
  ~GuiLock();
  XBMCAddon::LanguageHook* m_languageHook = nullptr;
  bool m_offScreen = false;
};
@CONSTRUCTOR@
@DESTRUCTOR@
}
struct CSettings { static constexpr const char* SETTING_LOOKANDFEEL_SKIN = "lookandfeel.skin"; };
std::string skin = "skin.infinity.diggz";
struct Settings { std::string GetString(const char*) { return skin; } };
struct SettingsComponent { std::shared_ptr<Settings> GetSettings() { static auto s = std::make_shared<Settings>(); return s; } };
struct StringUtils {
  static void ToLower(std::string& s) { std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){return std::tolower(c);}); }
};
struct CGUIInfoManager {
  int TranslateString(const char* s) { return s[0]=='$' ? 0 : 1; }
  std::string GetLabel(int, int) { events.push_back(depth ? "guarded_item_read" : "unguarded_read"); return "real_label"; }
};
struct GUI { CGUIInfoManager& GetInfoManager() { static CGUIInfoManager i; return i; } };
struct CServiceBroker {
  static GUI* GetGUI() { static GUI g; return &g; }
  static SettingsComponent* GetSettingsComponent() { static SettingsComponent s; return &s; }
};
namespace INFO { constexpr int DEFAULT_CONTEXT = 0; }
namespace GUILIB { namespace GUIINFO {
struct CGUIInfoLabel {
  static String GetLabel(const char*, int) { events.push_back(depth ? "guarded_item_read" : "unguarded_read"); return "expression_label"; }
};
}}
namespace XBMCAddon { namespace xbmc {
@API@
}}
int main() {
  const std::vector<std::string> guardedEvents = {"release_python", "lock_frame_graphics", "guarded_item_read", "unlock_frame_graphics", "restore_python"};
  const std::vector<const char*> labels = {"Container(50).ListItem.FileNameAndPath", "Container.ListItemAbsolute(0).Property(Infinity.Search.Provider)", "listitem.Label", "$INFO[Container(50).ListItem.Label]"};
  int guarded = 0;
  for (const auto* label : labels) {
    events.clear(); assert(!XBMCAddon::xbmc::getInfoLabel(label).empty());
    if (events == guardedEvents) ++guarded;
    assert(depth == 0);
  }
  // The negative/control cases must retain the previous unguarded path.
  skin = "skin.cobra.test"; events.clear();
  assert(!XBMCAddon::xbmc::getInfoLabel(labels[0]).empty());
  assert(events == std::vector<std::string>{"unguarded_read"});
  skin = "skin.infinity.diggz"; events.clear();
  assert(!XBMCAddon::xbmc::getInfoLabel("Container.FolderPath").empty());
  assert(events == std::vector<std::string>{"unguarded_read"});
  events.clear(); assert(XBMCAddon::xbmc::getInfoLabel(nullptr).empty()); assert(events.empty());
  bool completedDuringGuiMutation;
  {
    std::unique_lock<std::recursive_mutex> writer(frame);
    const int oldAttempts = attempted.load();
    auto read = std::async(std::launch::async, [&] {
      events.clear(); auto result = XBMCAddon::xbmc::getInfoLabel(labels[0]);
      return std::make_pair(result, events);
    });
    // Real GuiLock increments attempted before waiting. Old API never calls it.
    const auto end = std::chrono::steady_clock::now()+std::chrono::seconds(2);
    while(attempted.load()==oldAttempts && read.wait_for(std::chrono::milliseconds(0))!=std::future_status::ready && std::chrono::steady_clock::now()<end) {}
    completedDuringGuiMutation = read.wait_for(std::chrono::milliseconds(25)) == std::future_status::ready;
    writer.unlock(); auto result = read.get(); assert(!result.first.empty());
    if (guarded) assert(result.second == guardedEvents);
  }
  std::cout << "guarded_item_cases=" << guarded << "\nread_completed_while_GUI_mutation_guard_held=" << completedDuringGuiMutation << "\ncontrols_unchanged=1\n";
  if (@AFTER@) { assert(guarded == 4); assert(!completedDuringGuiMutation); }
  else { assert(guarded == 0); assert(completedDuringGuiMutation); }
}
'''


def main(native, out):
    original = native / 'xbmc/interfaces/legacy/ModuleXbmc.cpp'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == '215726b011de58f5cfb7cc1c33c42adfeb29f5f4c85a98864ab36a1819b8d888'
    utility = native / 'xbmc/interfaces/legacy/AddonUtils.cpp'
    assert hashlib.sha256(utility.read_bytes()).hexdigest() == '559e29c7f5921613e3355e3596493531ad958bf7491d8d0994d002fdaa14498d'
    before = original.read_text()
    after = (HERE / 'native/xbmc/interfaces/legacy/ModuleXbmc.cpp').read_text()
    before_fn = function(before, 'String getInfoLabel(const char* cLine)')
    after_fn = function(after, 'String getInfoLabel(const char* cLine)')
    # This one-function body and one include are the complete source delta.
    assert after.replace(after_fn, before_fn).replace('#include <optional>\n', '') == before
    ctor = function(utility.read_text(), 'GuiLock::GuiLock(')
    dtor = function(utility.read_text(), 'GuiLock::~GuiLock(')
    results = {}
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='info-label-host-') as temporary:
        temp = Path(temporary)
        for label, api, changed in [('before', before_fn, False), ('after', after_fn, True)]:
            text = ADAPTER.replace('@CONSTRUCTOR@', ctor).replace('@DESTRUCTOR@', dtor).replace('@API@', api).replace('@AFTER@', str(int(changed)))
            source = temp / (label + '.cpp')
            source.write_text(text)
            binary = temp / label
            subprocess.run(['g++', '-std=c++17', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-pthread', str(source), '-o', str(binary)], check=True)
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
            (out / (label + '.txt')).write_text(run.stdout + run.stderr)
            assert run.returncode == 0, (label, run.stdout, run.stderr)
            results[label] = run.stdout
    report = dict(status='PASS_EXTRACTED_PRODUCTION_API_ACCESS_BOUNDARY_CONTRACT_ONLY',
                  results=results, native_candidate_sha256=hashlib.sha256(after.encode()).hexdigest(),
                  original_api_source_sha256=hashlib.sha256(before.encode()).hexdigest(),
                  exact_original_GuiLock_source=True, original_GuiLock_implementation_changed=False,
                  all_other_ModuleXbmc_functions_byte_identical=True,
                  full_CGUIContainer_or_Android_execution=False, original_Scudo_crash_reproduced_by_this_test=False,
                  ARM64_compile='NOT_RUN', Android_Search_replay='NOT_RUN', production_repair_proven=False)
    (out / 'HOST-API-BOUNDARY.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    main(args.native, args.out)
