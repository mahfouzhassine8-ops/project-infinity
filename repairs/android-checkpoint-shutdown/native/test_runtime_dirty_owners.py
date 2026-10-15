#!/usr/bin/env python3
"""Compile production skin/favourites/peripheral checkpoint bodies with fixtures."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

RUNTIME = Path(os.environ.get("INFINITY_RUNTIME_NATIVE", "/workspace/scratch/a86210039ee8/runtime-native"))


def extract(source, signature):
    start = source.index(signature)
    return source[start:source.index("\n}\n", start) + 3]


class DirtyOwnerTests(unittest.TestCase):
    def test_production_addon_copy_preserves_settings_and_ownership(self):
        source = (RUNTIME / "xbmc/addons/Addon.cpp").read_text()
        header = (RUNTIME / "xbmc/addons/Addon.h").read_text()
        signature = "CAddon(const CAddon& other)"
        clean_header = re.sub(r'/\*.*?\*/|//[^\n]*', '', header, flags=re.S)
        self.assertEqual(clean_header.count(signature), 1)
        access = re.findall(r'^\s*(public|protected|private)\s*:',
                            clean_header[:clean_header.index(signature)], flags=re.M)
        self.assertEqual(access[-1], "public")
        self.assertRegex(clean_header, r'#if\s+defined\(TARGET_ANDROID\)\s*' +
                         re.escape(signature) + r';\s*#endif')
        constructor = extract(source, "CAddon::" + signature)
        for registration in ("TrackCreatedAddonTree", "TrackLoadedAddonTree",
                             "MarkAddonSettingsManagerDirty"):
            self.assertNotIn(registration, constructor)
        # Production data layout and constructor are retained. Only the unrelated
        # IAddon virtual interface and add-on metadata/settings services are stubs.
        data_start = header.index("struct CSettingsData")
        data_end = header.index("\n  };", data_start) + len("\n  };")
        fields = []
        for name in ("m_addonInfo", "m_checkpointSettingsMutex", "m_settings", "m_type"):
            matches = re.findall(r'^\s*(?:const |mutable )?[^\n;{}]+\b' + name + r';',
                                 header, flags=re.M)
            self.assertEqual(len(matches), 1, name)
            fields.append(matches[0].strip())
        code = ADDON_COPY_TEST.replace("// @SETTINGS_DATA@", header[data_start:data_end]).replace(
            "// @FIELDS@", "\n".join(fields)).replace("// @COPY_DECLARATION@", signature + ";").replace(
            "// @COPY_CONSTRUCTOR@", constructor)
        with tempfile.TemporaryDirectory(prefix="infinity-addon-copy-") as directory:
            cpp, binary = Path(directory) / "copy.cpp", Path(directory) / "copy"
            cpp.write_text(code)
            compiled = subprocess.run([shutil.which("c++") or "c++", "-std=c++17", "-DTARGET_ANDROID",
                                       "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2", "-pthread",
                                       str(cpp), "-o", str(binary)],
                                      text=True, capture_output=True, timeout=60)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(binary)], text=True, capture_output=True, timeout=10)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertIn("PASS production addon copy", tested.stdout)

    def test_production_dirty_owner_callbacks(self):
        peripheral = (RUNTIME / "xbmc/peripherals/devices/Peripheral.cpp").read_text()
        favourite = (RUNTIME / "xbmc/favourites/FavouritesService.cpp").read_text()
        skin = (RUNTIME / "xbmc/addons/Skin.cpp").read_text()
        bodies = []
        for signature in ["bool CPeripheral::CheckpointSavedFilesForAndroidExit()",
                          "bool CPeripheral::CheckpointForAndroidExit()",
                          "bool CPeripheral::PersistSettingsChecked(bool bExiting)"]:
            bodies.append(extract(peripheral, signature))
        for signature in ["bool CFavouritesService::Persist()", "bool CFavouritesService::CheckpointForAndroidExit()"]:
            bodies.append(extract(favourite, signature))
        for signature in ["void CSkinInfo::SetString(int setting, const std::string &label)",
                          "void CSkinInfo::SetBool(int setting, bool set)",
                          "void CSkinInfo::Reset()", "bool CSkinInfo::CheckpointForAndroidExit()"]:
            bodies.append(extract(skin, signature))
        with tempfile.TemporaryDirectory(prefix="infinity-dirty-owner-tests-") as directory:
            cpp = Path(directory) / "owners.cpp"
            cpp.write_text(PRELUDE + "\n".join(bodies) + TESTS)
            binary = Path(directory) / "owners"
            compiled = subprocess.run([shutil.which("c++") or "c++", "-std=c++17", "-DTARGET_ANDROID",
                                       "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2", "-pthread",
                                       str(cpp), "-o", str(binary)],
                                      text=True, capture_output=True, timeout=60)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(binary)], text=True, capture_output=True, timeout=30)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertIn("PASS", tested.stdout)


ADDON_COPY_TEST = r'''
#include <chrono>
#include <cstdint>
#include <future>
#include <iostream>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
using CCriticalSection = std::recursive_mutex;
#define CHECK(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while(false)
namespace ADDON {
enum class AddonType { UNKNOWN, SCREENSAVER };
using AddonInstanceId = std::uint32_t;
struct CAddonInfo {};
using AddonInfoPtr = std::shared_ptr<CAddonInfo>;
struct CAddonSettings { bool dirty = true; };
class IAddon : public std::enable_shared_from_this<IAddon> {
public:
  virtual ~IAddon() = default;
};
class CAddon : public IAddon {
public:
  CAddon(const AddonInfoPtr& info, AddonType type) : m_addonInfo(info), m_type(type) {}
  // @COPY_DECLARATION@
  // Fields are public only in this fixture so the preserved state can be observed.
  // @SETTINGS_DATA@
  // @FIELDS@
};
// @COPY_CONSTRUCTOR@
}
int main() {
 try {
  using namespace ADDON;
  auto source = std::make_shared<CAddon>(std::make_shared<CAddonInfo>(), AddonType::SCREENSAVER);
  auto settings = std::make_shared<CAddonSettings>();
  CAddon::CSettingsData global;
  global.m_loadSettingsFailed = true;
  global.m_hasUserSettings = true;
  global.m_addonSettingsPath = "resources/settings.xml";
  global.m_userSettingsPath = "profile/settings.xml";
  global.m_addonSettings = settings;
  source->m_settings[0] = global;
  source->m_settings[23] = {};

  std::unique_lock<CCriticalSection> sourceLock(source->m_checkpointSettingsMutex);
  std::promise<void> entering;
  auto entered = entering.get_future();
  auto copying = std::async(std::launch::async, [&] {
    entering.set_value();
    return std::make_shared<CAddon>(*source);
  });
  entered.get();
  const bool waited = copying.wait_for(std::chrono::milliseconds(30)) == std::future_status::timeout;
  source->m_settings[23].m_userSettingsPath = "profile/instance-settings-23.xml";
  sourceLock.unlock();
  auto copy = copying.get();
  CHECK(waited);
  CHECK(copy->m_addonInfo == source->m_addonInfo && copy->m_type == source->m_type);
  CHECK(copy->m_settings.size() == 2);
  const auto& copied = copy->m_settings.at(0);
  CHECK(copied.m_loadSettingsFailed && copied.m_hasUserSettings);
  CHECK(copied.m_addonSettingsPath == "resources/settings.xml");
  CHECK(copied.m_userSettingsPath == "profile/settings.xml");
  CHECK(copied.m_addonSettings == settings && settings->dirty);
  CHECK(!copy->m_settings.at(23).m_loadSettingsFailed);
  CHECK(!copy->m_settings.at(23).m_hasUserSettings);
  CHECK(copy->m_settings.at(23).m_userSettingsPath == "profile/instance-settings-23.xml");
  CHECK(!copy->m_settings.at(23).m_addonSettings);
  CHECK(&copy->m_settings != &source->m_settings);
  copy->m_settings.erase(23);
  copy->m_settings.at(0).m_hasUserSettings = false;
  CHECK(source->m_settings.size() == 2 && source->m_settings.at(0).m_hasUserSettings);

  sourceLock.lock();
  auto independentLock = std::async(std::launch::async, [&] {
    std::unique_lock<CCriticalSection> lock(copy->m_checkpointSettingsMutex);
  });
  const bool independent = independentLock.wait_for(std::chrono::seconds(1)) == std::future_status::ready;
  sourceLock.unlock();
  independentLock.get();
  CHECK(independent && &copy->m_checkpointSettingsMutex != &source->m_checkpointSettingsMutex);
  CHECK(source->shared_from_this().get() == source.get());
  CHECK(copy->shared_from_this().get() == copy.get());
  CAddon detached(*source);
  CHECK(detached.weak_from_this().expired());
  std::weak_ptr<CAddonSettings> registered = settings;
  settings.reset();
  global.m_addonSettings.reset();
  detached.m_settings.clear();
  source->m_settings.clear();
  source.reset();
  CHECK(!registered.expired());
  CHECK(registered.lock() == copy->m_settings.at(0).m_addonSettings);
  CHECK(registered.lock()->dirty);
  std::cout << "PASS production addon copy preserves flags, paths, shared dirty owner, separate map/mutex and fresh shared ownership\n";
  return 0;
 } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
'''


PRELUDE = r'''
#include <cassert>
#include <chrono>
#include <future>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
using CCriticalSection = std::recursive_mutex;
#define CHECK(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while(false)
namespace InfinityAndroidCheckpoint {
bool persist = true, admit = true, fileAllowed = true;
bool directoryAllowed = true;
int failures = 0, fileSaves = 0;
bool IsPersistingOnThisThread() { return persist; }
void RecordFailure(const char*, const char*) { ++failures; }
bool SaveCheckpointXml(const std::string&, const std::string&) { ++fileSaves; return fileAllowed; }
bool CheckpointCreatedDirectory(const std::string&, const char*) { return directoryAllowed; }
struct CheckpointWriteGuard { explicit CheckpointWriteGuard(const char*) {} explicit operator bool() const { return admit; } };
}
constexpr int LOGFATAL = 1;
struct CLog { template<class... T> static void Log(int, const char*, T...) {} };
struct StringUtils { template<class T> static std::string Format(const char*, T value) { return std::to_string(value); } };
struct Node {
  template<class T> void SetAttribute(const char*, T) {}
  Node* InsertEndChild(Node* value) { return value; }
};
namespace tinyxml2 { struct XMLPrinter { const char* CStr() const { return "<saved/>"; } int CStrSize() const { return 9; } }; }
struct CXBMCTinyXML2 {
  static bool saveAllowed, nodeAllowed;
  static int saves;
  Node node;
  Node* NewElement(const char*) { return nodeAllowed ? &node : nullptr; }
  Node* NewText(const char*) { return &node; }
  Node* InsertEndChild(Node* value) { return value; }
  Node* RootElement() { return &node; }
  bool Accept(tinyxml2::XMLPrinter*) const { return nodeAllowed; }
  bool SaveFile(const std::string&) { ++saves; return saveAllowed; }
};
bool CXBMCTinyXML2::saveAllowed = true;
bool CXBMCTinyXML2::nodeAllowed = true;
int CXBMCTinyXML2::saves = 0;
enum class SettingType { String, Integer, Number, Boolean };
struct CSetting { virtual ~CSetting() = default; virtual SettingType GetType() const = 0; };
template<class T, SettingType type> struct Setting : CSetting { T value{}; T GetValue() const { return value; } SettingType GetType() const override { return type; } };
using CSettingString = Setting<std::string, SettingType::String>;
using CSettingInt = Setting<int, SettingType::Integer>;
using CSettingNumber = Setting<double, SettingType::Number>;
using CSettingBool = Setting<bool, SettingType::Boolean>;
struct PeripheralDeviceSetting { std::shared_ptr<CSetting> m_setting; };
std::recursive_mutex g_checkpointPeripheralFilesMutex;
std::map<std::string, std::string> g_checkpointPeripheralFiles;
std::set<std::string> g_checkpointPeripheralSerializationFailed;
struct CPeripheral {
  CCriticalSection m_settingsMutex;
  bool m_checkpointDirty = false, m_checkpointLoaded = true;
  std::vector<std::shared_ptr<CPeripheral>> m_subDevices;
  std::string m_strSettingsFile = "peripheral.xml";
  std::map<std::string, PeripheralDeviceSetting> m_settings;
  std::set<std::string> m_changedSettings;
  int notifications = 0;
  void OnSettingChanged(const std::string&) { ++notifications; }
  static bool CheckpointSavedFilesForAndroidExit();
  bool CheckpointForAndroidExit();
  bool PersistSettingsChecked(bool);
};
struct Item {
  std::string GetLabel() const { return "title"; }
  bool HasArt(const char*) const { return false; }
  std::string GetArt(const char*) const { return {}; }
  std::string GetPath() const { return "PlayMedia(title)"; }
};
struct CFavouritesURL { explicit CFavouritesURL(const std::string&) {} std::string GetExecString() const { return "PlayMedia(title)"; } };
struct URIUtils {
  static std::string AddFileToFolder(const std::string& folder, const char* file) { return folder + "/" + file; }
  static std::string GetDirectory(const std::string& path) { return path.substr(0, path.rfind('/') + 1); }
};
struct CFavouritesService {
  CCriticalSection m_criticalSection;
  std::vector<std::shared_ptr<Item>> m_favourites;
  std::string m_userDataFolder = "profile";
  bool m_checkpointDirty = false, m_checkpointLoaded = true;
  bool Persist();
  bool CheckpointForAndroidExit();
};
struct SkinString { std::string value; };
struct SkinBool { bool value = false; };
struct Timer {
  CCriticalSection* mutex;
  void TriggerSave() {
    auto callback = std::async(std::launch::async, [&] { std::unique_lock<CCriticalSection> lock(*mutex); });
    // Restart() joins the save timer in production. The setter must release
    // the settings mutex before triggering that join.
    CHECK(callback.wait_for(std::chrono::seconds(1)) == std::future_status::ready);
  }
};
struct CSkinInfo {
  CCriticalSection m_checkpointSettingsMutex;
  bool m_checkpointDirty = false, saveAllowed = true;
  int saves = 0;
  std::map<int, std::shared_ptr<SkinString>> m_strings;
  std::map<int, std::shared_ptr<SkinBool>> m_bools;
  std::unique_ptr<Timer> m_settingsUpdateHandler;
  CSkinInfo() : m_settingsUpdateHandler(std::make_unique<Timer>(Timer{&m_checkpointSettingsMutex})) {}
  bool SaveSettings() { ++saves; return saveAllowed; }
  void SetString(int, const std::string&);
  void SetBool(int, bool);
  void Reset();
  bool CheckpointForAndroidExit();
};
'''

TESTS = r'''
int main() {
 try {
  CPeripheral peripheral;
  auto boolean = std::make_shared<CSettingBool>();
  peripheral.m_settings["enabled"] = {boolean};
  CHECK(peripheral.CheckpointForAndroidExit()); CHECK(CXBMCTinyXML2::saves == 0);
  peripheral.m_checkpointDirty = true; peripheral.m_changedSettings.insert("enabled");
  CXBMCTinyXML2::saveAllowed = false;
  CHECK(!peripheral.CheckpointForAndroidExit()); CHECK(peripheral.m_checkpointDirty);
  CHECK(!peripheral.m_changedSettings.empty()); CHECK(!g_checkpointPeripheralFiles.empty());
  CXBMCTinyXML2::saveAllowed = true;
  CHECK(peripheral.CheckpointForAndroidExit()); CHECK(!peripheral.m_checkpointDirty);
  CHECK(peripheral.m_changedSettings.empty()); CHECK(peripheral.notifications == 0);
  CHECK(g_checkpointPeripheralFiles.empty());
  peripheral.m_checkpointDirty = true;
  InfinityAndroidCheckpoint::directoryAllowed = false;
  CHECK(!peripheral.CheckpointForAndroidExit()); CHECK(peripheral.m_checkpointDirty);
  CHECK(!CPeripheral::CheckpointSavedFilesForAndroidExit());
  InfinityAndroidCheckpoint::directoryAllowed = true;
  CHECK(peripheral.CheckpointForAndroidExit());
  peripheral.m_checkpointDirty = true; peripheral.m_checkpointLoaded = false;
  const int prior = CXBMCTinyXML2::saves;
  CHECK(!peripheral.CheckpointForAndroidExit()); CHECK(CXBMCTinyXML2::saves == prior);
  peripheral.m_checkpointLoaded = true;
  auto child = std::make_shared<CPeripheral>(); child->m_checkpointDirty = true;
  child->m_strSettingsFile = "child.xml"; peripheral.m_subDevices.push_back(child);
  CHECK(peripheral.CheckpointForAndroidExit()); CHECK(!child->m_checkpointDirty);

  InfinityAndroidCheckpoint::persist = false;
  peripheral.m_checkpointDirty = true;
  CHECK(peripheral.PersistSettingsChecked(false)); CHECK(peripheral.m_checkpointDirty);
  CHECK(g_checkpointPeripheralFiles.count("peripheral.xml") == 1);
  InfinityAndroidCheckpoint::persist = true; InfinityAndroidCheckpoint::fileAllowed = false;
  CHECK(!CPeripheral::CheckpointSavedFilesForAndroidExit()); CHECK(!g_checkpointPeripheralFiles.empty());
  InfinityAndroidCheckpoint::fileAllowed = true;
  CHECK(CPeripheral::CheckpointSavedFilesForAndroidExit()); CHECK(g_checkpointPeripheralFiles.empty());

  CXBMCTinyXML2::nodeAllowed = false;
  CHECK(!peripheral.CheckpointForAndroidExit()); CHECK(peripheral.m_checkpointDirty);
  CHECK(!CPeripheral::CheckpointSavedFilesForAndroidExit());
  CXBMCTinyXML2::nodeAllowed = true;
  CHECK(peripheral.CheckpointForAndroidExit());
  CHECK(CPeripheral::CheckpointSavedFilesForAndroidExit());

  CFavouritesService favourites;
  favourites.m_favourites.push_back(std::make_shared<Item>());
  CHECK(favourites.CheckpointForAndroidExit());
  favourites.m_checkpointDirty = true; favourites.m_checkpointLoaded = false;
  CHECK(!favourites.CheckpointForAndroidExit());
  favourites.m_checkpointLoaded = true; CXBMCTinyXML2::saveAllowed = false;
  CHECK(!favourites.CheckpointForAndroidExit()); CHECK(favourites.m_checkpointDirty);
  CXBMCTinyXML2::saveAllowed = true;
  CHECK(favourites.CheckpointForAndroidExit()); CHECK(!favourites.m_checkpointDirty);

  CSkinInfo skin;
  skin.m_bools[1] = std::make_shared<SkinBool>();
  skin.m_strings[2] = std::make_shared<SkinString>();
  CHECK(skin.CheckpointForAndroidExit()); CHECK(skin.saves == 0);
  skin.SetBool(1, false); CHECK(!skin.m_checkpointDirty);
  skin.SetBool(1, true); CHECK(skin.m_checkpointDirty);
  skin.saveAllowed = false; CHECK(!skin.CheckpointForAndroidExit()); CHECK(skin.m_checkpointDirty);
  skin.saveAllowed = true; CHECK(skin.CheckpointForAndroidExit()); CHECK(!skin.m_checkpointDirty);
  skin.SetString(2, "changed"); CHECK(skin.m_checkpointDirty);
  CHECK(skin.CheckpointForAndroidExit()); skin.Reset(); CHECK(skin.m_checkpointDirty);
  InfinityAndroidCheckpoint::admit = false;
  CHECK(!skin.CheckpointForAndroidExit()); CHECK(!favourites.CheckpointForAndroidExit());
  CHECK(!peripheral.CheckpointForAndroidExit());
  std::cout << "PASS production dirty owner failure/retry, retired snapshots and timer lock scenarios\n";
  return 0;
 } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
'''


if __name__ == "__main__":
    unittest.main()
