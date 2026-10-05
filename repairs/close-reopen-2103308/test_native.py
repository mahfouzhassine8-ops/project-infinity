#!/usr/bin/env python3
"""Compile the transformed production Stop method, with explicit dependency fakes.

This tests ordering/reentrancy, not Android responsiveness or real add-on timing.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path
import native_patch as patch

HARNESS = r'''
#include <atomic>
#include <cassert>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <vector>
constexpr int LOGINFO = 1;
struct CLog { template<class... T> static void Log(T...) {} };
std::vector<int> events;
std::function<void()> duringScripts;
struct Guard {
  bool locked = true;
  void unlock() { assert(locked); locked = false; events.push_back(20); }
  void lock() { assert(!locked); locked = true; events.push_back(21); }
};
struct CSingleExit {
  Guard& guard;
  explicit CSingleExit(Guard& g) : guard(g) { guard.unlock(); }
  ~CSingleExit() { guard.lock(); }
};
struct CVariant {
  enum { VariantTypeObject }; int value{};
  explicit CVariant(int) {}
  int& operator[](const char*) { return value; }
};
namespace ANNOUNCEMENT { constexpr int System = 1; }
struct Announcer { void Announce(int, const char*, const CVariant&) { events.push_back(4); } };
struct Settings { void Save() { events.push_back(5); } };
struct Profiles { const char* GetSettingsFile() { return "settings.xml"; } };
struct SettingsComponent {
  Settings settings; Profiles profiles;
  Settings* GetSettings() { return &settings; }
  Profiles* GetProfileManager() { return &profiles; }
};
bool settingsExists = true;
struct CFile { static bool Exists(const char*) { return settingsExists; } };
struct Skin { void SaveSettings() { events.push_back(6); } } skin;
Skin* g_SkinInfo = &skin;
struct Services { void Stop() { events.push_back(1); } };
struct CServiceBroker {
  static Services& GetServiceAddons() { static Services s; return s; }
  static Announcer* GetAnnouncementManager() { static Announcer s; return &s; }
  static SettingsComponent* GetSettingsComponent() { static SettingsComponent s; return &s; }
};
struct CScriptInvocationManager {
  static CScriptInvocationManager& GetInstance() { static CScriptInvocationManager s; return s; }
  void StopRunningScripts() { events.push_back(2); if (duringScripts) duringScripts(); }
};
struct CApplication {
  Guard m_frameMoveGuard; bool m_infinityQuitAnnounced = false;
  void AnnounceQuit(int);
  void PrepareAndroidShutdownScripts(int);
} g_application;
@PREPARE@
void ANativeActivity_finish(void*) { events.push_back(3); }
struct CXBMCApp {
  std::atomic<bool> m_exiting{false};
  std::atomic<bool> m_finishRequested{false};
  bool m_shutdownPreparing{false};
  int m_exitCode{0}; void* m_activity{};
  bool Stop(int);
};
@METHOD@
int main() {
  const std::vector<int> prepared{20,4,5,6,1,2,21};
  auto complete = prepared; complete.push_back(3);
  // Cooperative cleanup completes before destruction is requested.
  { CXBMCApp a; assert(!a.Stop(42)); assert(a.m_exitCode == 42);
    assert(events == complete); assert(g_application.m_frameMoveGuard.locked);
    events.clear(); assert(!a.Stop(43)); assert(events.empty()); assert(a.m_exitCode == 42); }
  g_application.m_infinityQuitAnnounced = false;
  // Script stop pumps Kodi messages: another Quit must not recurse or finish early.
  { CXBMCApp a; duringScripts = [&] {
      assert(!g_application.m_frameMoveGuard.locked);
      assert((events == std::vector<int>{20,4,5,6,1,2}));
      assert(!a.Stop(99)); assert(a.m_exitCode == 7);
      assert((events == std::vector<int>{20,4,5,6,1,2}));
    };
    assert(!a.Stop(7)); assert(events == complete); }
  events.clear(); duringScripts = {};
  // Original stage two does not prepare again or request Android finish again.
  { CXBMCApp a; a.m_exiting = true; assert(a.Stop(9)); assert(events.empty()); }
  // External destruction during preparation continues original stage two.
  { CXBMCApp a; g_application.m_infinityQuitAnnounced = false;
    duringScripts = [&] {
      a.m_exiting = true;
      assert(!a.Stop(99));
      assert(!g_application.m_frameMoveGuard.locked);
    };
    assert(a.Stop(5)); assert(events == prepared); }
  // The final Stop announcement must not emit OnQuit twice.
  events.clear(); g_application.AnnounceQuit(5); assert(events.empty());
  // A teardown exception still reacquires the frame guard; never finish early.
  { CXBMCApp a; duringScripts = [] { throw std::runtime_error("script failure"); };
    try { a.Stop(5); assert(false); } catch (const std::runtime_error&) {}
    assert(g_application.m_frameMoveGuard.locked);
    assert(!a.m_shutdownPreparing);
    assert(events.back() == 21);
    for (int event : events) assert(event != 3); }
  // No settings file/no skin is respected, without inventing defaults or resetting data.
  events.clear(); duringScripts = {}; settingsExists = false; g_SkinInfo = nullptr;
  g_application.PrepareAndroidShutdownScripts(5);
  assert((events == std::vector<int>{20,1,2,21}));
  std::cout << "PASS: production prepare/Stop, lock/save order, one OnQuit, reentrancy, stage two, errors\n";
}
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    a = p.parse_args()
    before = (a.source / patch.CPP).read_text()
    if patch.digest(before.encode()) != patch.PREIMAGES[patch.CPP]:
        raise ValueError('Test requires exact inherited XBMCApp.cpp')
    cpp = patch.transform(patch.CPP, before)
    start = cpp.index('bool CXBMCApp::Stop(int exitCode)')
    end = cpp.index('\nvoid CXBMCApp::Quit()', start)
    method = cpp[start:end]
    header = (a.source / patch.HEADER).read_text()
    assert patch.digest(header.encode()) == patch.PREIMAGES[patch.HEADER]
    assert 'std::atomic<bool> m_finishRequested{false};' in patch.transform(patch.HEADER, header)
    app = (a.source / patch.APP).read_text()
    assert patch.digest(app.encode()) == patch.PREIMAGES[patch.APP]
    app_header = (a.source / patch.APP_HEADER).read_text()
    assert patch.digest(app_header.encode()) == patch.PREIMAGES[patch.APP_HEADER]
    assert 'void PrepareAndroidShutdownScripts(int exitCode);' in patch.transform(patch.APP_HEADER, app_header)
    transformed_app = patch.transform(patch.APP, app)
    prepare = transformed_app[transformed_app.index('void CApplication::AnnounceQuit(int exitCode)'):
                              transformed_app.index('bool CApplication::Stop(int exitCode)')]
    # Entire original Stop/Cleanup stays identical except its now-idempotent announcement.
    original_stop = app[app.index('bool CApplication::Stop(int exitCode)'):]
    announcement = '''    CVariant vExitCode(CVariant::VariantTypeObject);
    vExitCode["exitcode"] = exitCode;
    CServiceBroker::GetAnnouncementManager()->Announce(ANNOUNCEMENT::System, "OnQuit", vExitCode);
'''
    assert transformed_app[transformed_app.index('bool CApplication::Stop(int exitCode)'):] == original_stop.replace(announcement, '    AnnounceQuit(exitCode);\n', 1)
    # Original second stage and native event-loop ownership are byte-identical.
    assert cpp[end:] == before[before.index('\nvoid CXBMCApp::Quit()', start):]
    with tempfile.TemporaryDirectory(prefix='infinity-close-host-') as tmp:
        root = Path(tmp)
        (root / 'test.cpp').write_text(HARNESS.replace('@METHOD@', method).replace('@PREPARE@', prepare))
        subprocess.run(['c++', '-DTARGET_ANDROID', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                        str(root / 'test.cpp'), '-o', str(root / 'test')], check=True)
        subprocess.run([str(root / 'test')], check=True, timeout=10)
    try:
        patch.transform(patch.CPP, cpp)
    except ValueError:
        pass
    else:
        raise AssertionError('Patch must fail closed on an already-modified owner')


if __name__ == '__main__':
    main()
