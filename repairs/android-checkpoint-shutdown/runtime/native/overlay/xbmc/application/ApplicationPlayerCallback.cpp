/*
 *  Copyright (C) 2005-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "ApplicationPlayerCallback.h"

#include "FileItem.h"
#include "GUIUserMessages.h"
#include "PlayListPlayer.h"
#include "ServiceBroker.h"
#include "URL.h"
#include "application/ApplicationComponents.h"
#include "application/ApplicationPlayer.h"
#include "application/ApplicationStackHelper.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIMessage.h"
#include "guilib/GUIWindowManager.h"
#include "guilib/StereoscopicsManager.h"
#include "interfaces/AnnouncementManager.h"
#include "interfaces/json-rpc/JSONUtils.h"
#include "interfaces/python/XBPython.h"
#include "profiles/ProfileManager.h"
#include "settings/AdvancedSettings.h"
#include "settings/MediaSettings.h"
#include "settings/SettingsComponent.h"
#include "utils/JobManager.h"
#include "utils/SaveFileStateJob.h"
#include "utils/URIUtils.h"
#include "utils/log.h"
#include "video/VideoDatabase.h"
#include "video/VideoInfoTag.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif

#include <memory>
#include <cmath>

namespace
{
bool SamePersistedVideoSettings(CVideoSettings actual, const CVideoSettings& expected)
{
  // These two fields are resolution/display settings, not columns in the
  // per-file video settings table. Their native settings owner saves them.
  actual.m_subtitleVerticalPosition = expected.m_subtitleVerticalPosition;
  actual.m_subtitleVerticalPositionSave = expected.m_subtitleVerticalPositionSave;
  const auto normalize = [](float& read, float wanted) {
    if (std::isfinite(read) && std::isfinite(wanted) && std::abs(read - wanted) <= 0.00001f)
      read = wanted; // SQLite SQL serializer uses six fractional digits.
  };
  normalize(actual.m_CustomZoomAmount, expected.m_CustomZoomAmount);
  normalize(actual.m_CustomPixelRatio, expected.m_CustomPixelRatio);
  normalize(actual.m_CustomVerticalShift, expected.m_CustomVerticalShift);
  normalize(actual.m_VolumeAmplification, expected.m_VolumeAmplification);
  normalize(actual.m_SubtitleDelay, expected.m_SubtitleDelay);
  normalize(actual.m_Brightness, expected.m_Brightness);
  normalize(actual.m_Contrast, expected.m_Contrast);
  normalize(actual.m_Gamma, expected.m_Gamma);
  normalize(actual.m_NoiseReduction, expected.m_NoiseReduction);
  normalize(actual.m_Sharpness, expected.m_Sharpness);
  normalize(actual.m_AudioDelay, expected.m_AudioDelay);
  normalize(actual.m_ToneMapParam, expected.m_ToneMapParam);
  return !(actual != expected);
}
} // namespace

CApplicationPlayerCallback::CApplicationPlayerCallback()
{
}

void CApplicationPlayerCallback::OnPlayBackEnded()
{
  CLog::LogF(LOGDEBUG, "CApplicationPlayerCallback::OnPlayBackEnded");

  CGUIMessage msg(GUI_MSG_PLAYBACK_ENDED, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnPlayBackStarted(const CFileItem& file)
{
  CLog::LogF(LOGDEBUG, "CApplication::OnPlayBackStarted");
  std::shared_ptr<CFileItem> itemCurrentFile;

  // check if VideoPlayer should set file item stream details from its current streams
  const bool isBlu_dvd_image_or_stream = (URIUtils::IsBluray(file.GetPath()) || file.IsDVDFile() ||
                                          file.IsDiscImage() || file.IsInternetStream());

  const bool hasNoStreamDetails =
      (!file.HasVideoInfoTag() || !file.GetVideoInfoTag()->HasStreamDetails());

  if (file.GetProperty("get_stream_details_from_player").asBoolean() ||
      (hasNoStreamDetails && isBlu_dvd_image_or_stream))
  {
    auto& components = CServiceBroker::GetAppComponents();
    const auto appPlayer = components.GetComponent<CApplicationPlayer>();
    appPlayer->SetUpdateStreamDetails();
  }

  auto& components = CServiceBroker::GetAppComponents();
  const auto stackHelper = components.GetComponent<CApplicationStackHelper>();

  if (stackHelper->IsPlayingISOStack() || stackHelper->IsPlayingRegularStack())
    itemCurrentFile = std::make_shared<CFileItem>(*stackHelper->GetRegisteredStack(file));
  else
    itemCurrentFile = std::make_shared<CFileItem>(file);

  /* When playing video pause any low priority jobs, they will be unpaused  when playback stops.
   * This should speed up player startup for files on internet filesystems (eg. webdav) and
   * increase performance on low powered systems (Atom/ARM).
   */
  if (file.IsVideo() || file.IsGame())
  {
    CServiceBroker::GetJobManager()->PauseJobs();
  }

  stackHelper->OnPlayBackStarted(file);

  CGUIMessage msg(GUI_MSG_PLAYBACK_STARTED, 0, 0, 0, 0, itemCurrentFile);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnPlayerCloseFile(const CFileItem& file,
                                                   const CBookmark& bookmarkParam)
{
#if defined(TARGET_ANDROID)
  PersistPlayerState(file, bookmarkParam, InfinityAndroidCheckpoint::IsActive());
#else
  PersistPlayerState(file, bookmarkParam, false);
#endif
}

bool CApplicationPlayerCallback::CheckpointPlayerState(const CFileItem& file,
                                                       const CBookmark& bookmark)
{
  return PersistPlayerState(file, bookmark, true);
}

bool CApplicationPlayerCallback::PersistPlayerState(const CFileItem& file,
                                                    const CBookmark& bookmarkParam,
                                                    bool checked)
{
  std::lock_guard<std::mutex> saveLock(m_checkpointSaveMutex);
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard write("playback");
  if (!write)
  {
    InfinityAndroidCheckpoint::RecordPersistenceFailure("playback", "accepted file-state save was rejected");
    return false;
  }
#endif
  auto& components = CServiceBroker::GetAppComponents();
  const auto stackHelper = components.GetComponent<CApplicationStackHelper>();

  std::unique_lock<CCriticalSection> lock(stackHelper->m_critSection);

  CFileItem fileItem(file);
  CBookmark bookmark = bookmarkParam;
  CBookmark resumeBookmark;
  bool playCountUpdate = false;
  float percent = 0.0f;

  // Make sure we don't reset existing bookmark etc. on eg. player start failure
  if (bookmark.timeInSeconds == 0.0 && !checked)
    return true;

  // Live channels have no resume/playcount checkpoint. Per-file settings have
  // their separate checked owner, while PVR channel/timer state belongs to PVR.
  if (checked && (fileItem.IsLiveTV() || fileItem.IsPVRChannel()))
    return true;

  if (stackHelper->GetRegisteredStack(fileItem) != nullptr &&
      stackHelper->GetRegisteredStackTotalTimeMs(fileItem) > 0)
  {
    // regular stack case: we have to save the bookmark on the stack
    fileItem = *stackHelper->GetRegisteredStack(file);
    // the bookmark coming from the player is only relative to the current part, thus needs to be corrected with these attributes (start time will be 0 for non-stackparts)
    bookmark.timeInSeconds += stackHelper->GetRegisteredStackPartStartTimeMs(file) / 1000.0;
    if (stackHelper->GetRegisteredStackTotalTimeMs(file) > 0)
      bookmark.totalTimeInSeconds = stackHelper->GetRegisteredStackTotalTimeMs(file) / 1000.0;
    bookmark.partNumber = stackHelper->GetRegisteredStackPartNumber(file);
  }

  if (checked && bookmark.totalTimeInSeconds <= 0.0)
  {
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::RecordPersistenceFailure("playback", "unknown final duration");
#endif
    return false;
  }
  percent = bookmark.timeInSeconds / bookmark.totalTimeInSeconds * 100;

  const std::shared_ptr<CAdvancedSettings> advancedSettings =
      CServiceBroker::GetSettingsComponent()->GetAdvancedSettings();

  if ((fileItem.IsAudio() && advancedSettings->m_audioPlayCountMinimumPercent > 0 &&
       percent >= advancedSettings->m_audioPlayCountMinimumPercent) ||
      (fileItem.IsVideo() && advancedSettings->m_videoPlayCountMinimumPercent > 0 &&
       percent >= advancedSettings->m_videoPlayCountMinimumPercent))
  {
    playCountUpdate = true;
  }

  if (advancedSettings->m_videoIgnorePercentAtEnd > 0 &&
      bookmark.totalTimeInSeconds - bookmark.timeInSeconds <
          0.01 * static_cast<double>(advancedSettings->m_videoIgnorePercentAtEnd) *
              bookmark.totalTimeInSeconds)
  {
    resumeBookmark.timeInSeconds = -1.0;
  }
  else if (bookmark.timeInSeconds > advancedSettings->m_videoIgnoreSecondsAtStart)
  {
    resumeBookmark = bookmark;
    if (stackHelper->GetRegisteredStack(file) != nullptr)
    {
      // also update video info tag with total time
      fileItem.GetVideoInfoTag()->m_streamDetails.SetVideoDuration(
          0, resumeBookmark.totalTimeInSeconds);
    }
  }
  else
  {
    resumeBookmark.timeInSeconds = 0.0;
  }

  if (CServiceBroker::GetSettingsComponent()
          ->GetProfileManager()
          ->GetCurrentProfile()
          .canWriteDatabases())
  {
    if (checked)
      return CSaveFileState::DoWorkChecked(fileItem, resumeBookmark, playCountUpdate);
    CSaveFileState::DoWork(fileItem, resumeBookmark, playCountUpdate);
    return true;
  }
#if defined(TARGET_ANDROID)
  if (checked)
    InfinityAndroidCheckpoint::RecordPersistenceFailure("playback", "profile database is read-only");
#endif
  return !checked;
}

void CApplicationPlayerCallback::OnPlayBackPaused()
{
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().OnPlayBackPaused();
#endif

  CGUIMessage msg(GUI_MSG_PLAYBACK_PAUSED, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnPlayBackResumed()
{
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().OnPlayBackResumed();
#endif

  CGUIMessage msg(GUI_MSG_PLAYBACK_RESUMED, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnPlayBackStopped()
{
  CLog::LogF(LOGDEBUG, "CApplication::OnPlayBackStopped");

  CGUIMessage msg(GUI_MSG_PLAYBACK_STOPPED, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnPlayBackError()
{
  //@todo Playlists can be continued by calling OnPlaybackEnded instead
  // open error dialog
  CGUIMessage msg(GUI_MSG_PLAYBACK_ERROR, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
  OnPlayBackStopped();
}

void CApplicationPlayerCallback::OnQueueNextItem()
{
  CLog::LogF(LOGDEBUG, "CApplication::OnQueueNextItem");

  // informs python script currently running that we are requesting the next track
  // (does nothing if python is not loaded)
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().OnQueueNextItem(); // currently unimplemented
#endif

  CGUIMessage msg(GUI_MSG_QUEUE_NEXT_ITEM, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnPlayBackSeek(int64_t iTime, int64_t seekOffset)
{
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().OnPlayBackSeek(static_cast<int>(iTime),
                                               static_cast<int>(seekOffset));
#endif

  CGUIMessage msg(GUI_MSG_PLAYBACK_SEEKED, 0, 0, iTime, seekOffset);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnPlayBackSeekChapter(int iChapter)
{
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().OnPlayBackSeekChapter(iChapter);
#endif
}

void CApplicationPlayerCallback::OnPlayBackSpeedChanged(int iSpeed)
{
#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().OnPlayBackSpeedChanged(iSpeed);
#endif

  CGUIMessage msg(GUI_MSG_PLAYBACK_SPEED_CHANGED, 0, 0, iSpeed);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnAVChange()
{
  CLog::LogF(LOGDEBUG, "CApplication::OnAVChange");

  CServiceBroker::GetGUI()->GetStereoscopicsManager().OnStreamChange();

  CGUIMessage msg(GUI_MSG_PLAYBACK_AVCHANGE, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::OnAVStarted(const CFileItem& file)
{
  CLog::LogF(LOGDEBUG, "CApplication::OnAVStarted");

  CGUIMessage msg(GUI_MSG_PLAYBACK_AVSTARTED, 0, 0);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg);
}

void CApplicationPlayerCallback::RequestVideoSettings(const CFileItem& fileItem)
{
  CVideoDatabase dbs;
  if (dbs.Open())
  {
    CLog::Log(LOGDEBUG, "Loading settings for {}", CURL::GetRedacted(fileItem.GetPath()));

    // Load stored settings if they exist, otherwise use default
    CVideoSettings vs;
    if (!dbs.GetVideoSettings(fileItem, vs))
      vs = CMediaSettings::GetInstance().GetDefaultVideoSettings();

    auto& components = CServiceBroker::GetAppComponents();
    const auto appPlayer = components.GetComponent<CApplicationPlayer>();
    appPlayer->SetVideoSettings(vs);

    dbs.Close();
  }
}

void CApplicationPlayerCallback::StoreVideoSettings(const CFileItem& fileItem,
                                                    const CVideoSettings& vs)
{
#if defined(TARGET_ANDROID)
  PersistVideoSettings(fileItem, vs, InfinityAndroidCheckpoint::IsActive());
#else
  PersistVideoSettings(fileItem, vs, false);
#endif
}

bool CApplicationPlayerCallback::CheckpointVideoSettings(const CFileItem& fileItem,
                                                         const CVideoSettings& vs)
{
  return PersistVideoSettings(fileItem, vs, true);
}

bool CApplicationPlayerCallback::PersistVideoSettings(const CFileItem& fileItem,
                                                      const CVideoSettings& vs, bool checked)
{
  std::lock_guard<std::mutex> saveLock(m_checkpointSaveMutex);
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard write("playback-settings");
  if (!write)
  {
    InfinityAndroidCheckpoint::RecordPersistenceFailure("playback-settings", "accepted video-settings save was rejected");
    return false;
  }
#endif
  bool saved = false;
  CVideoDatabase dbs;
  if (dbs.Open())
  {
    if (vs != CMediaSettings::GetInstance().GetDefaultVideoSettings())
    {
      dbs.SetVideoSettings(fileItem, vs);
    }
    else
    {
      dbs.EraseVideoSettings(fileItem);
    }
    saved = true;
    if (checked)
    {
      CVideoSettings actual;
      const bool exists = dbs.GetVideoSettings(fileItem, actual);
      saved = vs != CMediaSettings::GetInstance().GetDefaultVideoSettings()
                  ? exists && SamePersistedVideoSettings(actual, vs) : !exists;
    }
    dbs.Close();
  }
#if defined(TARGET_ANDROID)
  if (checked && !saved)
    InfinityAndroidCheckpoint::RecordPersistenceFailure("playback-settings", "video settings save/readback failed");
#endif
  return saved;
}
