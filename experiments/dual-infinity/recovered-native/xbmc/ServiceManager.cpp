/*
 *  Copyright (C) 2005-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "ServiceManager.h"
#include "platform/android/activity/InfinityShutdownTrace.h"

#include "ContextMenuManager.h"
#include "DatabaseManager.h"
#include "PlayListPlayer.h"
#include "addons/AddonManager.h"
#include "addons/BinaryAddonCache.h"
#include "addons/ExtsMimeSupportList.h"
#include "addons/RepositoryUpdater.h"
#include "addons/Service.h"
#include "addons/VFSEntry.h"
#include "addons/binary-addons/BinaryAddonManager.h"
#include "cores/DataCacheCore.h"
#include "cores/RetroPlayer/guibridge/GUIGameRenderManager.h"
#include "cores/playercorefactory/PlayerCoreFactory.h"
#include "favourites/FavouritesService.h"
#include "games/GameServices.h"
#include "games/controllers/ControllerManager.h"
#include "input/InputManager.h"
#include "interfaces/generic/ScriptInvocationManager.h"
#include "interfaces/python/XBPython.h"
#include "network/Network.h"
#include "peripherals/Peripherals.h"
#if defined(HAS_FILESYSTEM_SMB)
#include "network/IWSDiscovery.h"
#if defined(TARGET_WINDOWS)
#include "platform/win32/network/WSDiscoveryWin32.h"
#else // !defined(TARGET_WINDOWS)
#include "platform/posix/filesystem/SMBWSDiscovery.h"
#endif // defined(TARGET_WINDOWS)
#endif // HAS_FILESYSTEM_SMB
#include "powermanagement/PowerManager.h"
#include "profiles/ProfileManager.h"
#include "pvr/PVRManager.h"
#if !defined(TARGET_WINDOWS) && defined(HAS_OPTICAL_DRIVE)
#include "storage/DetectDVDType.h"
#endif
#include "pictures/SlideShowDelegator.h"
#include "storage/MediaManager.h"
#include "utils/FileExtensionProvider.h"
#include "utils/log.h"
#include "weather/WeatherManager.h"

#include <memory>

using namespace KODI;

CServiceManager::CServiceManager() = default;

CServiceManager::~CServiceManager()
{
  if (init_level > 2)
    DeinitStageThree();
  if (init_level > 1)
    DeinitStageTwo();
  if (init_level > 0)
    DeinitStageOne();
}

bool CServiceManager::InitForTesting()
{
  m_network = CNetworkBase::GetNetwork();

  m_databaseManager = std::make_unique<CDatabaseManager>();

  m_binaryAddonManager = std::make_unique<ADDON::CBinaryAddonManager>();
  m_addonMgr = std::make_unique<ADDON::CAddonMgr>();
  if (!m_addonMgr->Init())
  {
    CLog::Log(LOGFATAL, "CServiceManager::{}: Unable to start CAddonMgr", __FUNCTION__);
    return false;
  }

  m_extsMimeSupportList = std::make_unique<ADDONS::CExtsMimeSupportList>(*m_addonMgr);
  m_fileExtensionProvider = std::make_unique<CFileExtensionProvider>(*m_addonMgr);

  init_level = 1;
  return true;
}

void CServiceManager::DeinitTesting()
{
  init_level = 0;
  m_fileExtensionProvider.reset();
  m_extsMimeSupportList.reset();
  m_binaryAddonManager.reset();
  m_addonMgr.reset();
  m_databaseManager.reset();
  m_network.reset();
}

bool CServiceManager::InitStageOne()
{
  m_Platform.reset(CPlatform::CreateInstance());
  if (!m_Platform->InitStageOne())
    return false;

#ifdef HAS_PYTHON
  m_XBPython = std::make_unique<XBPython>();
  CScriptInvocationManager::GetInstance().RegisterLanguageInvocationHandler(m_XBPython.get(),
                                                                            ".py");
#endif

  m_playlistPlayer = std::make_unique<PLAYLIST::CPlayListPlayer>();
  m_slideShowDelegator = std::make_unique<CSlideShowDelegator>();

  m_network = CNetworkBase::GetNetwork();

  init_level = 1;
  return true;
}

bool CServiceManager::InitStageTwo(const std::string& profilesUserDataFolder)
{
  // Initialize the addon database (must be before the addon manager is init'd)
  m_databaseManager = std::make_unique<CDatabaseManager>();

  m_binaryAddonManager = std::make_unique<
      ADDON::
          CBinaryAddonManager>(); /* Need to constructed before, GetRunningInstance() of binary CAddonDll need to call them */
  m_addonMgr = std::make_unique<ADDON::CAddonMgr>();
  if (!m_addonMgr->Init())
  {
    CLog::Log(LOGFATAL, "CServiceManager::{}: Unable to start CAddonMgr", __FUNCTION__);
    return false;
  }

  m_repositoryUpdater = std::make_unique<ADDON::CRepositoryUpdater>(*m_addonMgr);

  m_extsMimeSupportList = std::make_unique<ADDONS::CExtsMimeSupportList>(*m_addonMgr);

  m_vfsAddonCache = std::make_unique<ADDON::CVFSAddonCache>();
  m_vfsAddonCache->Init();

  m_PVRManager = std::make_unique<PVR::CPVRManager>();

  m_dataCacheCore = std::make_unique<CDataCacheCore>();

  m_binaryAddonCache = std::make_unique<ADDON::CBinaryAddonCache>();
  m_binaryAddonCache->Init();

  m_favouritesService = std::make_unique<CFavouritesService>(profilesUserDataFolder);

  m_serviceAddons = std::make_unique<ADDON::CServiceAddonManager>(*m_addonMgr);

  m_contextMenuManager = std::make_unique<CContextMenuManager>(*m_addonMgr);

  m_gameControllerManager = std::make_unique<GAME::CControllerManager>(*m_addonMgr);
  m_inputManager = std::make_unique<CInputManager>();
  m_inputManager->InitializeInputs();

  m_peripherals =
      std::make_unique<PERIPHERALS::CPeripherals>(*m_inputManager, *m_gameControllerManager);

  m_gameRenderManager = std::make_unique<RETRO::CGUIGameRenderManager>();

  m_fileExtensionProvider = std::make_unique<CFileExtensionProvider>(*m_addonMgr);

  m_powerManager = std::make_unique<CPowerManager>();
  m_powerManager->Initialize();
  m_powerManager->SetDefaults();

  m_weatherManager = std::make_unique<CWeatherManager>();

  m_mediaManager = std::make_unique<CMediaManager>();
  m_mediaManager->Initialize();

#if !defined(TARGET_WINDOWS) && defined(HAS_OPTICAL_DRIVE)
  m_DetectDVDType = std::make_unique<MEDIA_DETECT::CDetectDVDMedia>();
#endif

#if defined(HAS_FILESYSTEM_SMB)
  m_WSDiscovery = WSDiscovery::IWSDiscovery::GetInstance();
#endif

  if (!m_Platform->InitStageTwo())
    return false;

  init_level = 2;
  return true;
}

// stage 3 is called after successful initialization of WindowManager
bool CServiceManager::InitStageThree(const std::shared_ptr<CProfileManager>& profileManager)
{
#if !defined(TARGET_WINDOWS) && defined(HAS_OPTICAL_DRIVE)
  // Start Thread for DVD Mediatype detection
  CLog::Log(LOGINFO, "[Media Detection] starting service for optical media detection");
  m_DetectDVDType->Create(false);
#endif

  // Peripherals depends on strings being loaded before stage 3
  m_peripherals->Initialise();

  m_gameServices =
      std::make_unique<GAME::CGameServices>(*m_gameControllerManager, *m_gameRenderManager,
                                            *m_peripherals, *profileManager, *m_inputManager);

  m_contextMenuManager->Init();

  // Init PVR manager after login, not already on login screen
  if (!profileManager->UsingLoginScreen())
    m_PVRManager->Init();

  m_playerCoreFactory = std::make_unique<CPlayerCoreFactory>(*profileManager);

  if (!m_Platform->InitStageThree())
    return false;

  init_level = 3;
  return true;
}

void CServiceManager::DeinitStageThree()
{
  InfinityShutdownTrace::Scope methodEvidence("services.deinit3", -1, nullptr, nullptr);
  init_level = 2;
#if !defined(TARGET_WINDOWS) && defined(HAS_OPTICAL_DRIVE)
  m_DetectDVDType->StopThread();
  {
    InfinityShutdownTrace::Scope evidence("services.deinit3.m_DetectDVDType", -1, nullptr, nullptr);
    m_DetectDVDType.reset();
  }
#endif
  {
    InfinityShutdownTrace::Scope evidence("services.deinit3.m_playerCoreFactory", -1, nullptr, nullptr);
    m_playerCoreFactory.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit3.m_PVRManager", -1, nullptr, nullptr);
    m_PVRManager->Deinit();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit3.m_contextMenuManager", -1, nullptr, nullptr);
    m_contextMenuManager->Deinit();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit3.m_gameServices", -1, nullptr, nullptr);
    m_gameServices.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit3.m_peripherals", -1, nullptr, nullptr);
    m_peripherals->Clear();
  }

  {
    InfinityShutdownTrace::Scope evidence("services.deinit3.m_Platform", -1, nullptr, nullptr);
    m_Platform->DeinitStageThree();
  }
}

void CServiceManager::DeinitStageTwo()
{
  InfinityShutdownTrace::Scope methodEvidence("services.deinit2", -1, nullptr, nullptr);
  init_level = 1;

#if defined(HAS_FILESYSTEM_SMB)
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_WSDiscovery", -1, nullptr, nullptr);
    m_WSDiscovery.reset();
  }
#endif

  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_weatherManager", -1, nullptr, nullptr);
    m_weatherManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_powerManager", -1, nullptr, nullptr);
    m_powerManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_fileExtensionProvider", -1, nullptr, nullptr);
    m_fileExtensionProvider.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_gameRenderManager", -1, nullptr, nullptr);
    m_gameRenderManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_peripherals", -1, nullptr, nullptr);
    m_peripherals.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_inputManager", -1, nullptr, nullptr);
    m_inputManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_gameControllerManager", -1, nullptr, nullptr);
    m_gameControllerManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_contextMenuManager", -1, nullptr, nullptr);
    m_contextMenuManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_serviceAddons", -1, nullptr, nullptr);
    m_serviceAddons.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_favouritesService", -1, nullptr, nullptr);
    m_favouritesService.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_binaryAddonCache", -1, nullptr, nullptr);
    m_binaryAddonCache.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_dataCacheCore", -1, nullptr, nullptr);
    m_dataCacheCore.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_PVRManager", -1, nullptr, nullptr);
    m_PVRManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_extsMimeSupportList", -1, nullptr, nullptr);
    m_extsMimeSupportList.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_vfsAddonCache", -1, nullptr, nullptr);
    m_vfsAddonCache.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_repositoryUpdater", -1, nullptr, nullptr);
    m_repositoryUpdater.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_binaryAddonManager", -1, nullptr, nullptr);
    m_binaryAddonManager.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_addonMgr", -1, nullptr, nullptr);
    m_addonMgr.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_databaseManager", -1, nullptr, nullptr);
    m_databaseManager.reset();
  }

  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_mediaManager", -1, nullptr, nullptr);
    m_mediaManager->Stop();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_mediaManager", -1, nullptr, nullptr);
    m_mediaManager.reset();
  }

  {
    InfinityShutdownTrace::Scope evidence("services.deinit2.m_Platform", -1, nullptr, nullptr);
    m_Platform->DeinitStageTwo();
  }
}

void CServiceManager::DeinitStageOne()
{
  InfinityShutdownTrace::Scope methodEvidence("services.deinit1", -1, nullptr, nullptr);
  init_level = 0;

  {
    InfinityShutdownTrace::Scope evidence("services.deinit1.m_network", -1, nullptr, nullptr);
    m_network.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit1.m_playlistPlayer", -1, nullptr, nullptr);
    m_playlistPlayer.reset();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit1.m_slideShowDelegator", -1, nullptr, nullptr);
    m_slideShowDelegator.reset();
  }
#ifdef HAS_PYTHON
  CScriptInvocationManager::GetInstance().UnregisterLanguageInvocationHandler(m_XBPython.get());
  {
    InfinityShutdownTrace::Scope evidence("services.deinit1.m_XBPython", -1, nullptr, nullptr);
    m_XBPython.reset();
  }
#endif

  {
    InfinityShutdownTrace::Scope evidence("services.deinit1.m_Platform", -1, nullptr, nullptr);
    m_Platform->DeinitStageOne();
  }
  {
    InfinityShutdownTrace::Scope evidence("services.deinit1.m_Platform", -1, nullptr, nullptr);
    m_Platform.reset();
  }
}

#if defined(HAS_FILESYSTEM_SMB)
WSDiscovery::IWSDiscovery& CServiceManager::GetWSDiscovery()
{
  return *m_WSDiscovery;
}
#endif

ADDON::CAddonMgr& CServiceManager::GetAddonMgr()
{
  return *m_addonMgr;
}

ADDONS::CExtsMimeSupportList& CServiceManager::GetExtsMimeSupportList()
{
  return *m_extsMimeSupportList;
}

ADDON::CBinaryAddonCache& CServiceManager::GetBinaryAddonCache()
{
  return *m_binaryAddonCache;
}

ADDON::CBinaryAddonManager& CServiceManager::GetBinaryAddonManager()
{
  return *m_binaryAddonManager;
}

ADDON::CVFSAddonCache& CServiceManager::GetVFSAddonCache()
{
  return *m_vfsAddonCache;
}

ADDON::CServiceAddonManager& CServiceManager::GetServiceAddons()
{
  return *m_serviceAddons;
}

ADDON::CRepositoryUpdater& CServiceManager::GetRepositoryUpdater()
{
  return *m_repositoryUpdater;
}

#ifdef HAS_PYTHON
XBPython& CServiceManager::GetXBPython()
{
  return *m_XBPython;
}
#endif

#if !defined(TARGET_WINDOWS) && defined(HAS_OPTICAL_DRIVE)
MEDIA_DETECT::CDetectDVDMedia& CServiceManager::GetDetectDVDMedia()
{
  return *m_DetectDVDType;
}
#endif

PVR::CPVRManager& CServiceManager::GetPVRManager()
{
  return *m_PVRManager;
}

CContextMenuManager& CServiceManager::GetContextMenuManager()
{
  return *m_contextMenuManager;
}

CDataCacheCore& CServiceManager::GetDataCacheCore()
{
  return *m_dataCacheCore;
}

CPlatform& CServiceManager::GetPlatform()
{
  return *m_Platform;
}

PLAYLIST::CPlayListPlayer& CServiceManager::GetPlaylistPlayer()
{
  return *m_playlistPlayer;
}

GAME::CControllerManager& CServiceManager::GetGameControllerManager()
{
  return *m_gameControllerManager;
}

GAME::CGameServices& CServiceManager::GetGameServices()
{
  return *m_gameServices;
}

KODI::RETRO::CGUIGameRenderManager& CServiceManager::GetGameRenderManager()
{
  return *m_gameRenderManager;
}

PERIPHERALS::CPeripherals& CServiceManager::GetPeripherals()
{
  return *m_peripherals;
}

CFavouritesService& CServiceManager::GetFavouritesService()
{
  return *m_favouritesService;
}

CInputManager& CServiceManager::GetInputManager()
{
  return *m_inputManager;
}

CFileExtensionProvider& CServiceManager::GetFileExtensionProvider()
{
  return *m_fileExtensionProvider;
}

CPowerManager& CServiceManager::GetPowerManager()
{
  return *m_powerManager;
}

CNetworkBase& CServiceManager::GetNetwork()
{
  return *m_network;
}

CWeatherManager& CServiceManager::GetWeatherManager()
{
  return *m_weatherManager;
}

CPlayerCoreFactory& CServiceManager::GetPlayerCoreFactory()
{
  return *m_playerCoreFactory;
}

CDatabaseManager& CServiceManager::GetDatabaseManager()
{
  return *m_databaseManager;
}

CMediaManager& CServiceManager::GetMediaManager()
{
  return *m_mediaManager;
}

CSlideShowDelegator& CServiceManager::GetSlideShowDelegator()
{
  return *m_slideShowDelegator;
}
