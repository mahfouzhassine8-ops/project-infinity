/*
 *  Copyright (C) 2016-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */
#include "FilesystemInstaller.h"
#if defined(TARGET_ANDROID)
#include "addons/InfinityAddonFileReceipt.h"
#endif

#include "FileItem.h"
#include "filesystem/Directory.h"
#include "filesystem/File.h"
#include "filesystem/SpecialProtocol.h"
#include "utils/FileOperationJob.h"
#include "utils/StringUtils.h"
#include "utils/URIUtils.h"
#include "utils/log.h"

using namespace XFILE;

CFilesystemInstaller::CFilesystemInstaller()
  : m_addonFolder(CSpecialProtocol::TranslatePath("special://home/addons/")),
    m_tempFolder(CSpecialProtocol::TranslatePath("special://home/addons/temp/"))
{
}

bool CFilesystemInstaller::InstallToFilesystem(const std::string& archive, const std::string& addonId)
{
  auto addonFolder = URIUtils::AddFileToFolder(m_addonFolder, addonId);
  auto newAddonData = URIUtils::AddFileToFolder(m_tempFolder, StringUtils::CreateUUID());
  auto oldAddonData = URIUtils::AddFileToFolder(m_tempFolder, StringUtils::CreateUUID());

#if defined(TARGET_ANDROID)
  InfinityAddonFileReceipt::ResourceLock resource(addonFolder);
  if (!resource.Valid()) return false;
  InfinityAddonFileReceipt::WriteScope proof;
  proof.Touch(addonFolder);
  proof.Touch(newAddonData);
  proof.Touch(oldAddonData);
  // The UUID namespace must actually be empty before this operation owns it.
  // A conflicting pre-existing path is retained, never deleted as cleanup.
  if (!proof.BeforeAbsent(newAddonData) || !proof.BeforeAbsent(oldAddonData))
  {
    proof.Restored(addonFolder); proof.Restored(newAddonData); proof.Restored(oldAddonData);
    return false;
  }
  const auto prior = InfinityAddonFileReceipt::Capture(addonFolder);
  if (!prior.valid && !(prior.exists ? InfinityAddonFileReceipt::Existing(addonFolder, true) :
                                     InfinityAddonFileReceipt::Removed(addonFolder)))
  {
    proof.Unknown(); // No restoration claim can be based on an incomplete preimage.
    return false;
  }
  bool oldMoved = false;
  bool newMoved = false;
  InfinityAddonFileReceipt::Image staged;
  const auto restore = [&]() {
    bool ok = true;
    if (newMoved)
    {
      if (!(InfinityAddonFileReceipt::Capture(addonFolder) == staged)) return false;
      ok = CDirectory::RemoveRecursive(addonFolder) && InfinityAddonFileReceipt::Removed(addonFolder);
    }
    if (oldMoved && ok)
      ok = CFile::Rename(oldAddonData, addonFolder);
    if (CDirectory::Exists(newAddonData))
      ok = CDirectory::RemoveRecursive(newAddonData) && ok;
    // Each result, including parent namespaces, must be independently durable.
    const bool original = proof.Restored(addonFolder);
    const bool staging = proof.Restored(newAddonData);
    const bool backup = proof.Restored(oldAddonData);
    return original && staging && backup && ok &&
        InfinityAddonFileReceipt::Directory(m_tempFolder) &&
        InfinityAddonFileReceipt::Directory(m_addonFolder);
  };
  if (!CDirectory::Create(newAddonData)) { restore(); return false; }
  if (!UnpackArchive(archive, newAddonData))
  {
    CLog::Log(LOGERROR, "Failed to unpack archive '{}' to '{}'", archive, newAddonData);
    restore(); return false;
  }
  staged = InfinityAddonFileReceipt::Capture(newAddonData);
  if (!staged.exists || (!staged.valid && !InfinityAddonFileReceipt::Existing(newAddonData, true)))
  { restore(); return false; }
  if (prior.exists)
  {
    if (!CFile::Rename(addonFolder, oldAddonData)) { restore(); return false; }
    oldMoved = true;
  }
  if (!CFile::Rename(newAddonData, addonFolder)) { restore(); return false; }
  newMoved = true;
  if (!proof.Committed(addonFolder, true) || !proof.Deleted(newAddonData) ||
      !InfinityAddonFileReceipt::Directory(m_tempFolder) ||
      !InfinityAddonFileReceipt::Directory(m_addonFolder))
  { restore(); return false; }
  if (oldMoved && !CDirectory::RemoveRecursive(oldAddonData))
  {
    CLog::Log(LOGERROR, "Addon installed but old installation cleanup remains unverified '{}'", oldAddonData);
    return false; // The valid new installation is preserved; residue remains required.
  }
  return proof.Deleted(oldAddonData) && InfinityAddonFileReceipt::Directory(m_tempFolder) &&
      InfinityAddonFileReceipt::Directory(m_addonFolder);
#else

  if (!CDirectory::Create(newAddonData))
    return false;

  if (!UnpackArchive(archive, newAddonData))
  {
    CLog::Log(LOGERROR, "Failed to unpack archive '{}' to '{}'", archive, newAddonData);
    return false;
  }

  bool hasOldData = CDirectory::Exists(addonFolder);
  if (hasOldData)
  {
    if (!CFile::Rename(addonFolder, oldAddonData))
    {
      CLog::Log(LOGERROR, "Failed to move old addon files from '{}' to '{}'", addonFolder,
                oldAddonData);
      return false;
    }
  }

  if (!CFile::Rename(newAddonData, addonFolder))
  {
    CLog::Log(LOGERROR, "Failed to move new addon files from '{}' to '{}'", newAddonData,
              addonFolder);
    return false;
  }

  if (hasOldData)
  {
    if (!CDirectory::RemoveRecursive(oldAddonData))
    {
      CLog::Log(LOGWARNING, "Failed to delete old addon files in '{}'", oldAddonData);
    }
  }
  return true;
#endif
}

bool CFilesystemInstaller::UnInstallFromFilesystem(const std::string& addonFolder)
{
  auto tempFolder = URIUtils::AddFileToFolder(m_tempFolder, StringUtils::CreateUUID());
#if defined(TARGET_ANDROID)
  InfinityAddonFileReceipt::ResourceLock resource(addonFolder);
  if (!resource.Valid()) return false;
  InfinityAddonFileReceipt::WriteScope proof;
  proof.Touch(addonFolder); proof.Touch(tempFolder);
  const auto prior = InfinityAddonFileReceipt::Capture(addonFolder);
  if (!prior.exists || !proof.BeforeAbsent(tempFolder) ||
      (!prior.valid && !InfinityAddonFileReceipt::Existing(addonFolder, true)))
  { proof.Restored(addonFolder); proof.Restored(tempFolder); return false; }
  if (!CFile::Rename(addonFolder, tempFolder))
  { proof.Restored(addonFolder); proof.Restored(tempFolder); return false; }
  if (!CDirectory::RemoveRecursive(tempFolder))
  {
    // Restore only the complete, unchanged original, never a partial deletion.
    if (InfinityAddonFileReceipt::Capture(tempFolder) == prior)
      CFile::Rename(tempFolder, addonFolder);
    proof.Restored(addonFolder); proof.Restored(tempFolder);
    return false;
  }
  return proof.Deleted(addonFolder) && proof.Deleted(tempFolder) &&
      InfinityAddonFileReceipt::Directory(m_tempFolder) &&
      InfinityAddonFileReceipt::Directory(m_addonFolder);
#else
  if (!CFile::Rename(addonFolder, tempFolder))
  {
    CLog::Log(LOGERROR, "Failed to move old addon files from '{}' to '{}'", addonFolder,
              tempFolder);
    return false;
  }

  if (!CDirectory::RemoveRecursive(tempFolder))
  {
    CLog::Log(LOGWARNING, "Failed to delete old addon files in '{}'", tempFolder);
  }
  return true;
#endif
}

bool CFilesystemInstaller::UnpackArchive(std::string path, const std::string& dest)
{
  if (!URIUtils::IsProtocol(path, "zip"))
    path = URIUtils::CreateArchivePath("zip", CURL(path), "").Get();

  CFileItemList files;
  if (!CDirectory::GetDirectory(path, files, "", DIR_FLAG_DEFAULTS))
    return false;

  if (files.Size() == 1 && files[0]->m_bIsFolder)
  {
    path = files[0]->GetPath();
    files.Clear();
    if (!CDirectory::GetDirectory(path, files, "", DIR_FLAG_DEFAULTS))
      return false;
  }
  CLog::Log(LOGDEBUG, "Unpacking {} to {}", path, dest);

  for (auto i = 0; i < files.Size(); ++i)
    files[i]->Select(true);

  CFileOperationJob job(CFileOperationJob::ActionCopy, files, dest);
  return job.DoWork();
}
