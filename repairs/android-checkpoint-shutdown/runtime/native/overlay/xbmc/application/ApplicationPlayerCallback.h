/*
 *  Copyright (C) 2005-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#pragma once

#include "cores/IPlayerCallback.h"
#include "threads/Event.h"

#include <memory>
#include <mutex>

class CApplicationStackHelper;
class CFileItem;

class CApplicationPlayerCallback : public IPlayerCallback
{
public:
  CApplicationPlayerCallback();

  void OnPlayBackEnded() override;
  void OnPlayBackStarted(const CFileItem& file) override;
  void OnPlayerCloseFile(const CFileItem& file, const CBookmark& bookmark) override;
  void OnPlayBackPaused() override;
  void OnPlayBackResumed() override;
  void OnPlayBackStopped() override;
  void OnPlayBackError() override;
  void OnQueueNextItem() override;
  void OnPlayBackSeek(int64_t iTime, int64_t seekOffset) override;
  void OnPlayBackSeekChapter(int iChapter) override;
  void OnPlayBackSpeedChanged(int iSpeed) override;
  void OnAVChange() override;
  void OnAVStarted(const CFileItem& file) override;
  void RequestVideoSettings(const CFileItem& fileItem) override;
  void StoreVideoSettings(const CFileItem& fileItem, const CVideoSettings& vs) override;
  bool CheckpointPlayerState(const CFileItem& file, const CBookmark& bookmark);
  bool CheckpointVideoSettings(const CFileItem& fileItem, const CVideoSettings& vs);

private:
  bool PersistPlayerState(const CFileItem& file, const CBookmark& bookmark, bool checked);
  bool PersistVideoSettings(const CFileItem& fileItem, const CVideoSettings& vs, bool checked);
  std::mutex m_checkpointSaveMutex;
};
