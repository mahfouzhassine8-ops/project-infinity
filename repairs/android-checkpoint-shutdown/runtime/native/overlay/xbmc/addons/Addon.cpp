/*
 *  Copyright (C) 2005-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "Addon.h"

#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "platform/android/activity/InfinityCheckpointXml.h"
#endif

#include "ServiceBroker.h"
#include "addons/AddonManager.h"
#include "addons/RepositoryUpdater.h"
#include "addons/addoninfo/AddonInfo.h"
#include "addons/addoninfo/AddonType.h"
#include "addons/settings/AddonSettings.h"
#include "filesystem/Directory.h"
#include "filesystem/File.h"
#include "settings/Settings.h"
#include "settings/lib/Setting.h"
#include "utils/StringUtils.h"
#include "utils/URIUtils.h"
#include "utils/XMLUtils.h"
#include "utils/log.h"

#include <algorithm>
#include <ostream>
#include <string.h>
#include <utility>
#include <vector>
#if defined(TARGET_ANDROID)
#include <cstdint>
#include <map>
#include <mutex>
#include <set>
#endif

#ifdef HAS_PYTHON
#include "interfaces/python/XBPython.h"
#endif

using XFILE::CDirectory;
using XFILE::CFile;

#if defined(TARGET_ANDROID)
namespace
{
struct CheckpointAddonTree
{
  std::weak_ptr<ADDON::CAddonSettings> settings;
  std::shared_ptr<ADDON::CAddonSettings> dirtyOwner;
  const void* manager{nullptr};
  std::string path;
  std::string loadedBytes;
  bool loadedBaselineKnown{false};
  std::uint64_t committedGeneration{0};
};
struct CheckpointAddonSave
{
  std::shared_ptr<ADDON::CAddonSettings> settings;
  std::string bytes;
};
std::mutex g_checkpointAddonMutex;
std::vector<CheckpointAddonTree> g_checkpointAddonTrees;
std::map<std::string, CheckpointAddonSave> g_checkpointAddonSaves;
std::map<std::string, std::uint64_t> g_checkpointAddonSaveGenerations;
std::set<std::string> g_checkpointAddonDeletions;

void TrackCreatedAddonTree(const std::shared_ptr<ADDON::CAddonSettings>& settings,
                          const std::string& path)
{
  std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
  g_checkpointAddonTrees.erase(
      std::remove_if(g_checkpointAddonTrees.begin(), g_checkpointAddonTrees.end(),
                     [](const auto& entry) { return entry.settings.expired() && !entry.dirtyOwner; }),
      g_checkpointAddonTrees.end());
  g_checkpointAddonTrees.push_back({settings, {}, settings->GetSettingsManager(), path, {}, false});
}

bool CheckpointAddonBytes(const CXBMCTinyXML& doc, std::string& bytes)
{
  TiXmlPrinter printer;
  if (!doc.Accept(&printer))
    return false;
  bytes.assign(printer.CStr(), printer.Size());
  return true;
}

void TrackLoadedAddonTree(const std::shared_ptr<ADDON::CAddonSettings>& settings,
                         const std::string& path)
{
  if (!settings || !settings->IsLoaded())
    return;
  CXBMCTinyXML doc;
  std::string bytes;
  if (!settings->Save(doc) || !CheckpointAddonBytes(doc, bytes))
  {
    // An empty baseline forces a checked serialization attempt later. It does
    // not let an uninspectable loaded owner silently disappear from coverage.
    bytes.clear();
  }
  std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
  for (auto& entry : g_checkpointAddonTrees)
  {
    if (entry.settings.lock() == settings)
    {
      entry.loadedBytes = std::move(bytes);
      entry.loadedBaselineKnown = true;
      return;
    }
  }
  g_checkpointAddonTrees.push_back(
      {settings, {}, settings->GetSettingsManager(), path, std::move(bytes), true});
}

void TrackAddonSave(const std::shared_ptr<ADDON::CAddonSettings>& settings,
                    const std::string& path, const CXBMCTinyXML& doc)
{
  std::string bytes;
  if (!CheckpointAddonBytes(doc, bytes))
  {
    InfinityAndroidCheckpoint::RecordFailure("addon_settings", "serialize_save_evidence");
    return;
  }
  std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
  g_checkpointAddonDeletions.erase(path);
  g_checkpointAddonSaves[path] = {settings, std::move(bytes)};
}


bool ConfirmAddonSave(const std::shared_ptr<ADDON::CAddonSettings>& settings,
                      const std::string& path, const CXBMCTinyXML& doc)
{
  // Only a checked successful file save can rebase a settings instance.
  // Other loaded owners are never silently merged or considered durable.
  std::string bytes;
  if (!CheckpointAddonBytes(doc, bytes))
  {
    InfinityAndroidCheckpoint::RecordFailure("addon_settings", "committed_save_not_serializable");
    return false;
  }
  std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
  const std::uint64_t generation = ++g_checkpointAddonSaveGenerations[path];
  g_checkpointAddonDeletions.erase(path);
  g_checkpointAddonSaves[path] = {settings, bytes};
  for (auto& entry : g_checkpointAddonTrees)
  {
    if (entry.path == path && entry.settings.lock() == settings)
    {
      entry.loadedBytes = bytes;
      entry.loadedBaselineKnown = true;
      entry.committedGeneration = generation;
    }
  }
  return true;
}

void TrackAddonDeletion(const std::string& path)
{
  std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
  g_checkpointAddonSaves.erase(path);
  g_checkpointAddonSaveGenerations.erase(path);
  g_checkpointAddonDeletions.insert(path);
  g_checkpointAddonTrees.erase(
      std::remove_if(g_checkpointAddonTrees.begin(), g_checkpointAddonTrees.end(),
                     [&](const auto& entry) { return entry.path == path; }),
      g_checkpointAddonTrees.end());
}
} // namespace

void InfinityAndroidCheckpoint::MarkAddonSettingsManagerDirty(const void* manager)
{
  std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
  for (auto& entry : g_checkpointAddonTrees)
    if (entry.manager == manager)
      entry.dirtyOwner = entry.settings.lock();
}

bool InfinityAndroidCheckpoint::CheckpointAudioPolicyFile()
{
  CheckpointWriteGuard checkpointWrite("audio_policy");
  if (!checkpointWrite || !IsPersistingOnThisThread())
  {
    RecordFailure("audio_policy", "unauthorized_checkpoint");
    return false;
  }
  // Exact 2103335 embedded script.infinity.audiopolicy/default.py writes this
  // file synchronously with file fsync + replace. A running invocation is an
  // unresolved Python owner, so the coordinator cannot reach this save phase.
  return CheckpointExistingFile("special://profile/infinity-audio-policy.json", "audio_policy");
}

bool InfinityAndroidCheckpoint::CheckpointLoadedAddonSettings()
{
  CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite || !IsPersistingOnThisThread())
  {
    RecordFailure("addon_settings", "unauthorized_loaded_owner_checkpoint");
    return false;
  }
  std::vector<CheckpointAddonTree> trees;
  std::map<std::string, CheckpointAddonSave> pending;
  std::set<std::string> deletions;
  {
    std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
    trees = g_checkpointAddonTrees;
    pending = g_checkpointAddonSaves;
    deletions = g_checkpointAddonDeletions;
  }
  bool inventoryOk = true;
  for (const auto& entry : trees)
  {
    const auto settings = entry.dirtyOwner ? entry.dirtyOwner : entry.settings.lock();
    if (!settings)
      continue;
    if (!settings->IsLoaded())
      continue; // Definitions alone have no loaded persistent user values.
    if (!entry.loadedBaselineKnown)
    {
      const std::string detail = "loaded_owner_baseline_unknown;path=" + entry.path;
      RecordFailure("addon_settings", detail.c_str());
      inventoryOk = false;
      continue;
    }
    CXBMCTinyXML doc;
    std::string bytes;
    if (!settings->Save(doc) ||
        !CheckpointAddonBytes(doc, bytes))
    {
      const std::string detail = "loaded_owner_not_serializable;path=" + entry.path;
      RecordFailure("addon_settings", detail.c_str());
      inventoryOk = false;
      continue;
    }
    if (bytes == entry.loadedBytes)
      continue;
    const auto prior = pending.find(entry.path);
    if (prior != pending.end() && prior->second.settings != settings &&
        prior->second.bytes != bytes)
    {
      const std::string detail = "conflicting_loaded_owners;path=" + entry.path;
      RecordFailure("addon_settings", detail.c_str());
      inventoryOk = false;
      continue;
    }
    pending[entry.path] = {settings, std::move(bytes)};
  }
  if (!inventoryOk)
    return false;
  for (const auto& entry : pending)
  {
    const std::string addonDirectory = URIUtils::GetDirectory(entry.first);
    const std::string rootDirectory = URIUtils::GetParentPath(addonDirectory);
    if ((!CDirectory::Exists(rootDirectory) && !CDirectory::Create(rootDirectory)) ||
        (!CDirectory::Exists(addonDirectory) && !CDirectory::Create(addonDirectory)) ||
        !CheckpointCreatedDirectory(rootDirectory) ||
        !CheckpointCreatedDirectory(addonDirectory) ||
        !SaveCheckpointXml(entry.first, entry.second.bytes))
    {
      const std::string detail = "loaded_owner_save;path=" + entry.first;
      RecordFailure("addon_settings", detail.c_str());
      return false;
    }
  }
  for (const auto& path : deletions)
  {
    // Deletion is user intent, so only its directory entry is checkpointed.
    // Do not recreate the deleted settings using an old retained tree.
    if (CFile::Exists(path))
    {
      const std::string detail = "deleted_settings_reappeared;path=" + path;
      RecordFailure("addon_settings", detail.c_str());
      return false;
    }
    if (!CheckpointCreatedDirectory(path))
      return false;
  }
  std::lock_guard<std::mutex> lock(g_checkpointAddonMutex);
  for (auto& entry : g_checkpointAddonTrees)
  {
    const auto saved = pending.find(entry.path);
    if (saved != pending.end() && saved->second.settings == entry.settings.lock())
      entry.loadedBytes = saved->second.bytes;
    entry.dirtyOwner.reset();
  }
  g_checkpointAddonSaves.clear();
  g_checkpointAddonDeletions.clear();
  return true;
}
#endif

namespace ADDON
{

CAddon::CAddon(const AddonInfoPtr& addonInfo, AddonType addonType)
  : m_addonInfo(addonInfo),
    m_type(addonType == AddonType::UNKNOWN ? addonInfo->MainType() : addonType)
{
}

#if defined(TARGET_ANDROID)
CAddon::CAddon(const CAddon& other)
  : IAddon(other), m_addonInfo(other.m_addonInfo), m_type(other.m_type)
{
  // The settings map is per add-on, while its settings trees retain the original
  // shared identity and checkpoint registration. The new mutex starts unlocked.
  std::unique_lock<CCriticalSection> settingsLock(other.m_checkpointSettingsMutex);
  m_settings = other.m_settings;
}
#endif

AddonType CAddon::MainType() const
{
  return m_addonInfo->MainType();
}

bool CAddon::HasType(AddonType type) const
{
  return m_addonInfo->HasType(type);
}

bool CAddon::HasMainType(AddonType type) const
{
  return m_addonInfo->HasType(type, true);
}

const CAddonType* CAddon::Type(AddonType type) const
{
  return m_addonInfo->Type(type);
}

std::string CAddon::ID() const
{
  return m_addonInfo->ID();
}

std::string CAddon::Name() const
{
  return m_addonInfo->Name();
}

bool CAddon::IsBinary() const
{
  return m_addonInfo->IsBinary();
}

CAddonVersion CAddon::Version() const
{
  return m_addonInfo->Version();
}

CAddonVersion CAddon::MinVersion() const
{
  return m_addonInfo->MinVersion();
}

std::string CAddon::Summary() const
{
  return m_addonInfo->Summary();
}

std::string CAddon::Description() const
{
  return m_addonInfo->Description();
}

std::string CAddon::Path() const
{
  return m_addonInfo->Path();
}

std::string CAddon::Profile() const
{
  return m_addonInfo->ProfilePath();
}

std::string CAddon::Author() const
{
  return m_addonInfo->Author();
}

std::string CAddon::ChangeLog() const
{
  return m_addonInfo->ChangeLog();
}

std::string CAddon::Icon() const
{
  return m_addonInfo->Icon();
}

ArtMap CAddon::Art() const
{
  return m_addonInfo->Art();
}

std::vector<std::string> CAddon::Screenshots() const
{
  return m_addonInfo->Screenshots();
}

std::string CAddon::Disclaimer() const
{
  return m_addonInfo->Disclaimer();
}

AddonLifecycleState CAddon::LifecycleState() const
{
  return m_addonInfo->LifecycleState();
}

std::string CAddon::LifecycleStateDescription() const
{
  return m_addonInfo->LifecycleStateDescription();
}

CDateTime CAddon::InstallDate() const
{
  return m_addonInfo->InstallDate();
}

CDateTime CAddon::LastUpdated() const
{
  return m_addonInfo->LastUpdated();
}

CDateTime CAddon::LastUsed() const
{
  return m_addonInfo->LastUsed();
}

std::string CAddon::Origin() const
{
  return m_addonInfo->Origin();
}

std::string CAddon::OriginName() const
{
  return m_addonInfo->OriginName();
}

uint64_t CAddon::PackageSize() const
{
  return m_addonInfo->PackageSize();
}

const InfoMap& CAddon::ExtraInfo() const
{
  return m_addonInfo->ExtraInfo();
}

const std::vector<DependencyInfo>& CAddon::GetDependencies() const
{
  return m_addonInfo->GetDependencies();
}

std::string CAddon::FanArt() const
{
  auto it = m_addonInfo->Art().find("fanart");
  return it != m_addonInfo->Art().end() ? it->second : "";
}

bool CAddon::MeetsVersion(const CAddonVersion& versionMin, const CAddonVersion& version) const
{
  return m_addonInfo->MeetsVersion(versionMin, version);
}

/**
 * Settings Handling
 */

std::vector<AddonInstanceId> CAddon::GetKnownInstanceIds() const
{
  return m_addonInfo->GetKnownInstanceIds();
}

bool CAddon::SupportsMultipleInstances() const
{
  return m_addonInfo->SupportsMultipleInstances();
}

AddonInstanceSupport CAddon::InstanceUseType() const
{
  return m_addonInfo->InstanceUseType();
}

bool CAddon::SupportsInstanceSettings() const
{
  return m_addonInfo->SupportsInstanceSettings();
}

bool CAddon::DeleteInstanceSettings(AddonInstanceId instance)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return false;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  if (instance == ADDON_SETTINGS_ID)
    return false;

  const auto itr = m_settings.find(instance);
  if (itr == m_settings.end())
    return false;

  if (CFile::Exists(itr->second.m_userSettingsPath))
  {
    if (!CFile::Delete(itr->second.m_userSettingsPath))
    {
#if defined(TARGET_ANDROID)
      InfinityAndroidCheckpoint::RecordFailure("addon_settings", "delete_instance_settings");
#endif
      return false;
    }
  }
#if defined(TARGET_ANDROID)
  TrackAddonDeletion(itr->second.m_userSettingsPath);
#endif

  ResetSettings(instance);

  return true;
}

bool CAddon::CanHaveAddonOrInstanceSettings()
{
  return HasSettings(ADDON_SETTINGS_ID) || SupportsInstanceSettings();
}

bool CAddon::HasSettings(AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return LoadSettings(false, true, id) && m_settings[id].m_addonSettings->HasSettings();
}

bool CAddon::SettingsInitialized(AddonInstanceId id /* = ADDON_SETTINGS_ID */) const
{
  const auto addonSettings = FindInstanceSettings(id);
  return addonSettings && addonSettings->IsInitialized();
}

bool CAddon::SettingsLoaded(AddonInstanceId id /* = ADDON_SETTINGS_ID */) const
{
  const auto addonSettings = FindInstanceSettings(id);
  return addonSettings && addonSettings->IsLoaded();
}

bool CAddon::LoadSettings(bool bForce,
                          bool loadUserSettings,
                          AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return false;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  if (SettingsInitialized(id) && !bForce)
    return true;

  const auto itr = m_settings.find(id);
  if (itr != m_settings.end())
  {
    if (itr->second.m_loadSettingsFailed)
      return false;
  }
  else
  {
    InitSettings(id);
  }

  // assume loading settings fails
  m_settings[id].m_loadSettingsFailed = true;

  // reset the settings if we are forced to
  if (SettingsInitialized(id) && bForce)
    GetSettings(id)->Uninitialize();

  // load the settings definition XML file
  const auto addonSettingsDefinitionFile = m_settings[id].m_addonSettingsPath;
  CXBMCTinyXML addonSettingsDefinitionDoc;
  if (!addonSettingsDefinitionDoc.LoadFile(addonSettingsDefinitionFile))
  {
    if (CFile::Exists(addonSettingsDefinitionFile))
    {
      CLog::Log(LOGERROR, "CAddon[{}]: unable to load: {}, Line {}\n{}", ID(),
                addonSettingsDefinitionFile, addonSettingsDefinitionDoc.ErrorRow(),
                addonSettingsDefinitionDoc.ErrorDesc());
    }

    return false;
  }

  // initialize the settings definition
  if (!GetSettings(id)->Initialize(addonSettingsDefinitionDoc))
  {
    CLog::Log(LOGERROR, "CAddon[{}]: failed to initialize addon settings", ID());
    return false;
  }

  // loading settings didn't fail
  m_settings[id].m_loadSettingsFailed = false;

  // load user settings / values
  if (loadUserSettings)
    LoadUserSettings(id);

  return true;
}

bool CAddon::HasUserSettings(AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  if (!LoadSettings(false, true, id))
    return false;

  return SettingsLoaded(id) && m_settings[id].m_hasUserSettings;
}

bool CAddon::ReloadSettings(AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return LoadSettings(true, true, id);
}

void CAddon::ResetSettings(AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  m_settings.erase(id);
}

bool CAddon::LoadUserSettings(AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return false;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  if (!SettingsInitialized(id) && !InitSettings(id))
    return false;

  CSettingsData& data = m_settings[id];

  data.m_hasUserSettings = false;

  // there are no user settings
  if (!CFile::Exists(data.m_userSettingsPath))
  {
    // mark the settings as loaded
    GetSettings(id)->SetLoaded();
#if defined(TARGET_ANDROID)
    TrackLoadedAddonTree(data.m_addonSettings, data.m_userSettingsPath);
#endif
    return true;
  }

  CXBMCTinyXML doc;
  if (!doc.LoadFile(data.m_userSettingsPath))
  {
    CLog::Log(LOGERROR, "CAddon[{}]: failed to load addon settings from {}", ID(),
              data.m_userSettingsPath);
    return false;
  }

  const bool loaded = SettingsFromXML(doc, false, id);
#if defined(TARGET_ANDROID)
  if (loaded)
    TrackLoadedAddonTree(data.m_addonSettings, data.m_userSettingsPath);
#endif
  return loaded;
}

bool CAddon::HasSettingsToSave(AddonInstanceId id /* = ADDON_SETTINGS_ID */) const
{
  return SettingsLoaded(id);
}

bool CAddon::SaveSettings(AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return false;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  if (!HasSettingsToSave(id))
    return false; // no settings to save

  CSettingsData& data = m_settings[id];

  // break down the path into directories
  const std::string strAddon = URIUtils::GetDirectory(data.m_userSettingsPath);
  const std::string strRoot = URIUtils::GetParentPath(strAddon);

  // create the individual folders
  const bool createRoot = !CDirectory::Exists(strRoot);
  const bool createAddon = !CDirectory::Exists(strAddon);
  if ((createRoot && !CDirectory::Create(strRoot)) ||
      (createAddon && !CDirectory::Create(strAddon)))
  {
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::RecordFailure("addon_settings", "create_directory");
#endif
    return false;
  }
#if defined(TARGET_ANDROID)
  if (!InfinityAndroidCheckpoint::CheckpointCreatedDirectory(strRoot) ||
      !InfinityAndroidCheckpoint::CheckpointCreatedDirectory(strAddon))
    return false;
#endif

  // create the XML file
  CXBMCTinyXML doc;
  if (!SettingsToXML(doc, id))
  {
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::RecordFailure("addon_settings", "serialize");
#endif
    return false;
  }
#if defined(TARGET_ANDROID)
  TrackAddonSave(data.m_addonSettings, data.m_userSettingsPath, doc);
#endif
  if (!doc.SaveFile(data.m_userSettingsPath))
  {
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::RecordFailure("addon_settings", "save");
#endif
    return false;
  }

#if defined(TARGET_ANDROID)
  if (!ConfirmAddonSave(data.m_addonSettings, data.m_userSettingsPath, doc))
    return false;
#endif
  data.m_hasUserSettings = true;

#if defined(TARGET_ANDROID)
  // The checkpoint persists existing state; it must not restart settings
  // notifications or Python work after the writer admission fence is closed.
  if (InfinityAndroidCheckpoint::IsActive())
    return true;
  settingsLock.unlock();
#endif

  //push the settings changes to the running addon instance
  CServiceBroker::GetAddonMgr().ReloadSettings(ID(), id);
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().OnSettingsChanged(ID());
#endif
  return true;
}

std::string CAddon::GetSetting(const std::string& key, AddonInstanceId id)
{
  if (key.empty() || !LoadSettings(false, true, id))
    return ""; // no settings available

  auto setting = m_settings[id].m_addonSettings->GetSetting(key);
  if (setting != nullptr)
    return setting->ToString();

  return "";
}

template<class TSetting>
bool GetSettingValue(CAddon& addon,
                     AddonInstanceId instanceId,
                     const std::string& key,
                     typename TSetting::Value& value)
{
  if (key.empty() || !addon.HasSettings(instanceId))
    return false;

  auto setting = addon.GetSettings(instanceId)->GetSetting(key);
  if (setting == nullptr || setting->GetType() != TSetting::Type())
    return false;

  value = std::static_pointer_cast<TSetting>(setting)->GetValue();
  return true;
}

bool CAddon::GetSettingBool(const std::string& key,
                            bool& value,
                            AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return GetSettingValue<CSettingBool>(*this, id, key, value);
}

bool CAddon::GetSettingInt(const std::string& key,
                           int& value,
                           AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return GetSettingValue<CSettingInt>(*this, id, key, value);
}

bool CAddon::GetSettingNumber(const std::string& key,
                              double& value,
                              AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return GetSettingValue<CSettingNumber>(*this, id, key, value);
}

bool CAddon::GetSettingString(const std::string& key,
                              std::string& value,
                              AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return GetSettingValue<CSettingString>(*this, id, key, value);
}

void CAddon::UpdateSetting(const std::string& key,
                           const std::string& value,
                           AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  if (key.empty() || !LoadSettings(false, true, id))
    return;

  // try to get the setting
  auto setting = m_settings[id].m_addonSettings->GetSetting(key);

  // if the setting doesn't exist, try to add it
  if (setting == nullptr)
  {
    setting = m_settings[id].m_addonSettings->AddSetting(key, value);
    if (setting == nullptr)
    {
      CLog::Log(LOGERROR, "CAddon[{}]: failed to add undefined setting \"{}\"", ID(), key);
      return;
    }
  }

  setting->FromString(value);
}

template<class TSetting>
bool UpdateSettingValue(CAddon& addon,
                        AddonInstanceId instanceId,
                        const std::string& key,
                        typename TSetting::Value value)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return false;
#endif
  if (key.empty() || !addon.HasSettings(instanceId))
    return false;

  // try to get the setting
  auto setting = addon.GetSettings(instanceId)->GetSetting(key);

  // if the setting doesn't exist, try to add it
  if (setting == nullptr)
  {
    setting = addon.GetSettings(instanceId)->AddSetting(key, value);
    if (setting == nullptr)
    {
      CLog::Log(LOGERROR, "CAddon[{}]: failed to add undefined setting \"{}\"", addon.ID(), key);
      return false;
    }
  }

  if (setting->GetType() != TSetting::Type())
    return false;

  return std::static_pointer_cast<TSetting>(setting)->SetValue(value);
}

bool CAddon::UpdateSettingBool(const std::string& key,
                               bool value,
                               AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return UpdateSettingValue<CSettingBool>(*this, id, key, value);
}

bool CAddon::UpdateSettingInt(const std::string& key,
                              int value,
                              AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return UpdateSettingValue<CSettingInt>(*this, id, key, value);
}

bool CAddon::UpdateSettingNumber(const std::string& key,
                                 double value,
                                 AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return UpdateSettingValue<CSettingNumber>(*this, id, key, value);
}

bool CAddon::UpdateSettingString(const std::string& key,
                                 const std::string& value,
                                 AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  return UpdateSettingValue<CSettingString>(*this, id, key, value);
}

bool CAddon::SettingsFromXML(const CXBMCTinyXML& doc,
                             bool loadDefaults,
                             AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
  if (doc.RootElement() == nullptr)
    return false;

  // if the settings haven't been initialized yet, try it from the given XML
  if (!SettingsInitialized(id))
  {
    if (!GetSettings(id)->Initialize(doc))
    {
      CLog::Log(LOGERROR, "CAddon[{}]: failed to initialize addon settings", ID());
      return false;
    }
  }

  // reset all setting values to their default value
  if (loadDefaults)
    GetSettings(id)->SetDefaults();

  // try to load the setting's values from the given XML
  if (!GetSettings(id)->Load(doc))
  {
    CLog::Log(LOGERROR, "CAddon[{}]: failed to load user settings", ID());
    return false;
  }

  m_settings[id].m_hasUserSettings = true;

  return true;
}

bool CAddon::SettingsToXML(CXBMCTinyXML& doc, AddonInstanceId id /* = ADDON_SETTINGS_ID */) const
{
  if (!SettingsInitialized(id))
    return false;

  if (!m_settings[id].m_addonSettings->Save(doc))
  {
    CLog::Log(LOGERROR, "CAddon[{}]: failed to save addon settings", ID());
    return false;
  }

  return true;
}

bool CAddon::InitSettings(AddonInstanceId id)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("addon_settings");
  if (!checkpointWrite)
    return false;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  // initialize addon settings if necessary
  if (!FindInstanceSettings(id))
  {
    CSettingsData data;

    data.m_addonSettings =
        std::make_shared<CAddonSettings>(enable_shared_from_this::shared_from_this(), id);
    if (id == ADDON_SETTINGS_ID)
    {
      data.m_addonSettingsPath =
          URIUtils::AddFileToFolder(m_addonInfo->Path(), "resources", "settings.xml");
      data.m_userSettingsPath = URIUtils::AddFileToFolder(Profile(), "settings.xml");
    }
    else
    {
      data.m_addonSettingsPath =
          URIUtils::AddFileToFolder(m_addonInfo->Path(), "resources", "instance-settings.xml");
      data.m_userSettingsPath =
          URIUtils::AddFileToFolder(Profile(), StringUtils::Format("instance-settings-{}.xml", id));
    }

#if defined(TARGET_ANDROID)
    TrackCreatedAddonTree(data.m_addonSettings, data.m_userSettingsPath);
#endif
    m_settings[id] = std::move(data);
    return true;
  }

  return false;
}

std::shared_ptr<CAddonSettings> CAddon::FindInstanceSettings(AddonInstanceId id) const
{
  const auto itr = m_settings.find(id);
  if (itr == m_settings.end())
    return nullptr;

  return itr->second.m_addonSettings;
}

std::shared_ptr<CAddonSettings> CAddon::GetSettings(AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
#if defined(TARGET_ANDROID)
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  if (InitSettings(id))
    LoadSettings(false, true, id);

  const auto found = m_settings.find(id);
  return found == m_settings.end() ? nullptr : found->second.m_addonSettings;
}

std::string CAddon::LibPath() const
{
  // Get library related to given type on construction
  std::string libName = m_addonInfo->Type(m_type)->LibName();
  if (libName.empty())
  {
    // If not present fallback to master library
    libName = m_addonInfo->LibName();
    if (libName.empty())
      return "";
  }
  return URIUtils::AddFileToFolder(m_addonInfo->Path(), libName);
}

CAddonVersion CAddon::GetDependencyVersion(const std::string& dependencyID) const
{
  return m_addonInfo->DependencyVersion(dependencyID);
}

void OnPreInstall(const AddonPtr& addon)
{
  //Fallback to the pre-install callback in the addon.
  //! @bug If primary extension point have changed we're calling the wrong method.
  addon->OnPreInstall();
}

void OnPostInstall(const AddonPtr& addon, bool update, bool modal)
{
  addon->OnPostInstall(update, modal);
}

void OnPreUnInstall(const AddonPtr& addon)
{
  addon->OnPreUnInstall();
}

void OnPostUnInstall(const AddonPtr& addon)
{
  addon->OnPostUnInstall();
}

} // namespace ADDON
