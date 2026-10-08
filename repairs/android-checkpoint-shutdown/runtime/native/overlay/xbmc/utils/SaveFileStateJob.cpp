/*
 *  Copyright (C) 2010-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "SaveFileStateJob.h"

#include "FileItem.h"
#include "GUIUserMessages.h"
#include "ServiceBroker.h"
#include "StringUtils.h"
#include "URIUtils.h"
#include "URL.h"
#include "Util.h"
#include "application/ApplicationComponents.h"
#include "application/ApplicationStackHelper.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIMessage.h"
#include "guilib/GUIWindowManager.h"
#include "interfaces/AnnouncementManager.h"
#include "log.h"
#include "music/MusicDatabase.h"
#include "music/Song.h"
#include "music/tags/MusicInfoTag.h"
#include "network/upnp/UPnP.h"
#include "utils/Variant.h"
#include "video/Bookmark.h"
#include "video/VideoDatabase.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif

#include <cmath>
#include <limits>

namespace
{
bool SaveFileState(CFileItem& item, CBookmark& bookmark, bool updatePlayCount, bool checked)
{
  if (checked && !item.IsVideo() && !item.IsAudio())
    return false;
  bool saved = true;
  std::string progressTrackingFile = item.GetPath();

  if (item.HasVideoInfoTag() && StringUtils::StartsWith(item.GetVideoInfoTag()->m_strFileNameAndPath, "removable://"))
    progressTrackingFile = item.GetVideoInfoTag()->m_strFileNameAndPath; // this variable contains removable:// suffixed by disc label+uniqueid or is empty if label not uniquely identified
  else if (item.HasVideoInfoTag() && item.IsVideoDb())
    progressTrackingFile = item.GetVideoInfoTag()->m_strFileNameAndPath; // we need the file url of the video db item to create the bookmark
  else if (item.HasProperty("original_listitem_url"))
  {
    // only use original_listitem_url for Python, UPnP and Bluray sources
    std::string original = item.GetProperty("original_listitem_url").asString();
    if (URIUtils::IsPlugin(original) || URIUtils::IsUPnP(original) || URIUtils::IsBluray(item.GetPath()))
      progressTrackingFile = original;
  }

  if (!progressTrackingFile.empty())
  {
#ifdef HAS_UPNP
    if (checked && URIUtils::IsUPnP(progressTrackingFile))
      return false; // No audited remote persistence acknowledgment contract.
    // checks if UPnP server of this file is available and supports updating
    if (URIUtils::IsUPnP(progressTrackingFile)
        && UPNP::CUPnP::SaveFileState(item, bookmark, updatePlayCount))
    {
      return true;
    }
#endif
    if (item.IsVideo())
    {
      std::string redactPath = CURL::GetRedacted(progressTrackingFile);
      CLog::Log(LOGDEBUG, "{} - Saving file state for video item {}", __FUNCTION__, redactPath);

      CVideoDatabase videodatabase;
      if (!videodatabase.Open())
      {
        CLog::Log(LOGWARNING, "{} - Unable to open video database. Can not save file state!",
                  __FUNCTION__);
        saved = false;
      }
      else
      {
        videodatabase.BeginTransaction();

        if (URIUtils::IsPlugin(progressTrackingFile) && !(item.HasVideoInfoTag() && item.GetVideoInfoTag()->m_iDbId >= 0))
        {
          // FileItem from plugin can lack information, make sure all needed fields are set
          CVideoInfoTag *tag = item.GetVideoInfoTag();
          CStreamDetails streams = tag->m_streamDetails;
          if (videodatabase.LoadVideoInfo(progressTrackingFile, *tag))
          {
            item.SetPath(progressTrackingFile);
            item.ClearProperty("original_listitem_url");
            tag->m_streamDetails = streams;
          }
        }

        const int priorPlayCount = checked ? videodatabase.GetPlayCount(progressTrackingFile) : 0;
        bool updateListing = false;
        // No resume & watched status for livetv
        if (!item.IsLiveTV())
        {
          if (updatePlayCount)
          {
            // no watched for not yet finished pvr recordings
            if (!item.IsInProgressPVRRecording())
            {
              CLog::Log(LOGDEBUG, "{} - Marking video item {} as watched", __FUNCTION__,
                        redactPath);

              // consider this item as played
              const CDateTime newLastPlayed = videodatabase.IncrementPlayCount(item);
              if (checked && !newLastPlayed.IsValid())
                saved = false;

              item.SetOverlayImage(CGUIListItem::ICON_OVERLAY_WATCHED);
              updateListing = true;

              if (item.HasVideoInfoTag())
              {
                item.GetVideoInfoTag()->IncrementPlayCount();

                if (newLastPlayed.IsValid())
                  item.GetVideoInfoTag()->m_lastPlayed = newLastPlayed;

                CVariant data;
                data["id"] = item.GetVideoInfoTag()->m_iDbId;
                data["type"] = item.GetVideoInfoTag()->m_type;
                CServiceBroker::GetAnnouncementManager()->Announce(ANNOUNCEMENT::VideoLibrary,
                                                                   "OnUpdate", data);
              }
            }
          }
          else
          {
            const CDateTime newLastPlayed = videodatabase.UpdateLastPlayed(item);
            if (checked && !newLastPlayed.IsValid())
              saved = false;

            if (item.HasVideoInfoTag() && newLastPlayed.IsValid())
              item.GetVideoInfoTag()->m_lastPlayed = newLastPlayed;
          }

          if (checked || !item.HasVideoInfoTag() ||
              item.GetVideoInfoTag()->GetResumePoint().timeInSeconds != bookmark.timeInSeconds)
          {
            if (bookmark.timeInSeconds <= 0.0)
              videodatabase.ClearBookMarksOfFile(progressTrackingFile, CBookmark::RESUME);
            else
              videodatabase.AddBookMarkToFile(progressTrackingFile, bookmark, CBookmark::RESUME);
            if (item.HasVideoInfoTag())
              item.GetVideoInfoTag()->SetResumePoint(bookmark);

            // UPnP announce resume point changes to clients
            // however not if playcount is modified as that already announces
            if (item.HasVideoInfoTag() && !updatePlayCount)
            {
              CVariant data;
              data["id"] = item.GetVideoInfoTag()->m_iDbId;
              data["type"] = item.GetVideoInfoTag()->m_type;
              CServiceBroker::GetAnnouncementManager()->Announce(ANNOUNCEMENT::VideoLibrary,
                                                                 "OnUpdate", data);
            }

            updateListing = true;
          }
        }

        if (item.HasVideoInfoTag() && item.GetVideoInfoTag()->HasStreamDetails())
        {
          CFileItem dbItem(item);

          // Check whether the item's db streamdetails need updating
          if (!videodatabase.GetStreamDetails(dbItem) ||
              dbItem.GetVideoInfoTag()->m_streamDetails != item.GetVideoInfoTag()->m_streamDetails)
          {
            videodatabase.SetStreamDetailsForFile(item.GetVideoInfoTag()->m_streamDetails, progressTrackingFile);
            updateListing = true;
          }
        }

        const bool committed = videodatabase.CommitTransaction();
        if (!committed)
          saved = false;
        if (checked && committed && !item.IsLiveTV())
        {
          CBookmark persisted;
          const bool hasResume = videodatabase.GetResumeBookMark(progressTrackingFile, persisted);
          if (bookmark.timeInSeconds > 0.0)
          {
            if (!hasResume || std::abs(persisted.timeInSeconds - bookmark.timeInSeconds) > 0.001 ||
                std::abs(persisted.totalTimeInSeconds - bookmark.totalTimeInSeconds) > 0.001 ||
                persisted.playerState != bookmark.playerState || persisted.player != bookmark.player)
              saved = false;
          }
          else if (hasResume)
            saved = false;
          if (updatePlayCount && !item.IsInProgressPVRRecording() &&
              (priorPlayCount < 0 || videodatabase.GetPlayCount(progressTrackingFile) != priorPlayCount + 1))
            saved = false;
        }
        if (checked && committed && item.HasVideoInfoTag() &&
            item.GetVideoInfoTag()->HasStreamDetails())
        {
          CFileItem persisted(progressTrackingFile, false);
          if (!videodatabase.GetStreamDetails(persisted) ||
              persisted.GetVideoInfoTag()->m_streamDetails != item.GetVideoInfoTag()->m_streamDetails)
            saved = false;
        }

        if (updateListing)
        {
          CUtil::DeleteVideoDatabaseDirectoryCache();
          CFileItemPtr msgItem(new CFileItem(item));
          if (item.HasProperty("original_listitem_url"))
            msgItem->SetPath(item.GetProperty("original_listitem_url").asString());

          // Could be part of an ISO stack. In this case the bookmark is saved onto the part.
          // In order to properly update the list, we need to refresh the stack's resume point
          const auto& components = CServiceBroker::GetAppComponents();
          const auto stackHelper = components.GetComponent<CApplicationStackHelper>();
          if (stackHelper->HasRegisteredStack(item) &&
              stackHelper->GetRegisteredStackTotalTimeMs(item) == 0)
            videodatabase.GetResumePoint(*(msgItem->GetVideoInfoTag()));

          CGUIMessage message(GUI_MSG_NOTIFY_ALL, CServiceBroker::GetGUI()->GetWindowManager().GetActiveWindow(), 0, GUI_MSG_UPDATE_ITEM, 0, msgItem);
          CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(message);
        }

        videodatabase.Close();
      }
    }

    if (item.IsAudio())
    {
      std::string redactPath = CURL::GetRedacted(progressTrackingFile);
      CLog::Log(LOGDEBUG, "{} - Saving file state for audio item {}", __FUNCTION__, redactPath);

      CMusicDatabase musicdatabase;
      if (updatePlayCount)
      {
        if (!musicdatabase.Open())
        {
          CLog::Log(LOGWARNING, "{} - Unable to open music database. Can not save file state!",
                    __FUNCTION__);
          saved = false;
        }
        else
        {
          // consider this item as played
          CLog::Log(LOGDEBUG, "{} - Marking audio item {} as listened", __FUNCTION__, redactPath);

          CSong before;
          const bool knownSong = !checked || musicdatabase.GetSongByFileName(item.GetPath(), before);
          musicdatabase.IncrementPlayCount(item);
          if (checked)
          {
            CSong after;
            if (!knownSong || !musicdatabase.GetSongByFileName(item.GetPath(), after) ||
                after.iTimesPlayed != before.iTimesPlayed + 1)
              saved = false;
          }
          musicdatabase.Close();

          // UPnP announce resume point changes to clients
          // however not if playcount is modified as that already announces
          if (item.IsMusicDb())
          {
            CVariant data;
            data["id"] = item.GetMusicInfoTag()->GetDatabaseId();
            data["type"] = item.GetMusicInfoTag()->GetType();
            CServiceBroker::GetAnnouncementManager()->Announce(ANNOUNCEMENT::AudioLibrary,
                                                               "OnUpdate", data);
          }
        }
      }

      if (item.IsAudioBook())
      {
        if (!musicdatabase.Open())
          saved = false;
        else
        {
          const auto rawPosition = item.GetStartOffset() + CUtil::ConvertSecsToMilliSecs(bookmark.timeInSeconds);
          const bool positionFits = rawPosition >= 0 && rawPosition <= std::numeric_limits<int>::max();
          const int position = positionFits ? static_cast<int>(rawPosition) : 0;
          if (!positionFits || !musicdatabase.SetResumeBookmarkForAudioBook(item, position))
            saved = false;
          if (checked)
          {
            int actual = -1;
            if (!musicdatabase.GetResumeBookmarkForAudioBook(item, actual) || actual != position)
              saved = false;
          }
          musicdatabase.Close();
        }
      }
    }
  }
  else if (checked)
    saved = false;
  return saved;
}
} // namespace

void CSaveFileState::DoWork(CFileItem& item, CBookmark& bookmark, bool updatePlayCount)
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive())
  {
    DoWorkChecked(item, bookmark, updatePlayCount);
    return;
  }
#endif
  SaveFileState(item, bookmark, updatePlayCount, false);
}

bool CSaveFileState::DoWorkChecked(CFileItem& item, CBookmark& bookmark, bool updatePlayCount)
{
  bool saved = false;
  try
  {
    saved = SaveFileState(item, bookmark, updatePlayCount, true);
  }
  catch (...)
  {
    saved = false;
  }
#if defined(TARGET_ANDROID)
  if (!saved)
    InfinityAndroidCheckpoint::RecordPersistenceFailure("playback", "file state commit/readback failed");
#endif
  return saved;
}
