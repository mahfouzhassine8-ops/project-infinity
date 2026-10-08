#pragma once

#include "InfinityAndroidCheckpoint.h"
#include "InfinityCheckpointFile.h"
#include "filesystem/SpecialProtocol.h"
#include "utils/log.h"

#include <cerrno>
#include <cstdlib>
#include <exception>
#include <memory>
#include <string>
#include <string_view>

namespace InfinityAndroidCheckpoint
{
// Android may expose /data/user/0 or external app storage through an ancestor
// symlink. Resolve the selected parent once, then keep the leaf under the
// checked helper's O_NOFOLLOW policy. Remote/VFS paths are never acknowledged
// as durable local files. Callers hold CheckpointWriteGuard throughout.
inline bool LocalCheckpointPath(const std::string& filename, std::string& resolved)
{
  const std::string translated = CSpecialProtocol::TranslatePath(filename);
  if (translated.empty() || translated.front() != '/' || translated.back() == '/' ||
      translated.find('\0') != std::string::npos)
  {
    RecordFailure("xml_files", "unsupported_checkpoint_file_path");
    return false;
  }
  const auto slash = translated.rfind('/');
  const std::string leaf = translated.substr(slash + 1);
  if (leaf == "." || leaf == "..")
  {
    RecordFailure("xml_files", "invalid_checkpoint_file_leaf");
    return false;
  }
  const std::string parent = slash == 0 ? "/" : translated.substr(0, slash);
  const std::unique_ptr<char, decltype(&std::free)> canonical(::realpath(parent.c_str(), nullptr),
                                                           &std::free);
  if (!canonical)
  {
    RecordFailure("xml_files", "resolve_checkpoint_parent");
    return false;
  }
  resolved = canonical.get();
  if (resolved.back() != '/')
    resolved.push_back('/');
  resolved += leaf;
  return true;
}

inline bool SaveCheckpointXml(const std::string& filename, std::string_view bytes)
{
  if (!IsPersistingOnThisThread())
  {
    RecordFailure("xml_files", "unauthorized_checkpoint_save");
    return false;
  }
  try
  {
    std::string path;
    if (!LocalCheckpointPath(filename, path))
      return false;
    const auto saved = infinity::checkpoint::files::SaveDirty(path, bytes);
    if (!saved.ok)
    {
      const char* stage = infinity::checkpoint::files::StageName(saved.stage);
      RecordFailure("xml_files", stage);
      CLog::Log(LOGERROR,
                "Infinity checkpoint XML failed: stage={} errno={} renamed={} durable={}",
                stage, saved.error, saved.replaced, saved.dataAndDirectorySynced);
      return false;
    }
    return true;
  }
  catch (const std::exception&)
  {
    RecordFailure("xml_files", "checkpoint_save_exception");
    return false;
  }
}

// Sync the parent entry of a directory in this checkpoint's targeted add-on
// settings hierarchy. Repeat on retries even if mkdir already succeeded during
// a failed attempt; existence alone does not prove the entry became durable.
inline bool CheckpointCreatedDirectory(const std::string& directory,
                                       const char* owner = "addon_settings")
{
  if (!IsPersistingOnThisThread())
    return true;
  std::string path;
  std::string normalized = directory;
  while (normalized.size() > 1 && normalized.back() == '/')
    normalized.pop_back();
  if (!LocalCheckpointPath(normalized, path))
    return false;
  const auto slash = path.rfind('/');
  const std::string parent = slash == 0 ? "/" : path.substr(0, slash);
  const int fd = ::open(parent.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0)
  {
    RecordFailure(owner, "open_created_directory_parent");
    return false;
  }
  int synced;
  do { synced = ::fsync(fd); } while (synced != 0 && errno == EINTR);
  const int closed = ::close(fd); // Linux close is never retried after EINTR.
  if (synced != 0 || closed != 0)
  {
    RecordFailure(owner, synced != 0 ? "sync_created_directory_parent" :
                                      "close_created_directory_parent");
    return false;
  }
  return true;
}
} // namespace InfinityAndroidCheckpoint
