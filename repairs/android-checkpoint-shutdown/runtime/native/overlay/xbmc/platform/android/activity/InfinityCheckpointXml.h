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
      const std::string detail = std::string(stage) + "_errno_" + std::to_string(saved.error);
      RecordFailure("xml_files", detail.c_str());
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

// For an audited synchronous producer which has already committed its bytes
// and has no live writer. Preserve the exact file and metadata; check both the
// inode and its namespace entry without parsing, rewriting or inventing state.
// The caller must establish producer quiescence before invoking this helper.
inline bool CheckpointExistingFile(const std::string& filename, const char* owner,
                                   infinity::checkpoint::files::PosixIo& io)
{
  if (!IsPersistingOnThisThread())
  {
    RecordFailure(owner, "unauthorized_existing_file_checkpoint");
    return false;
  }
  using namespace infinity::checkpoint::files;
  std::string path;
  if (!LocalCheckpointPath(filename, path))
    return false;
  Result result;
  std::string leaf;
  int directory = detail::OpenParent(io, path, leaf, result);
  int file = -1;
  const auto finish = [&]() {
    detail::Close(io, file, result, Stage::CloseExisting);
    detail::Close(io, directory, result, Stage::CloseDirectory);
    if (result.stage != Stage::None)
    {
      RecordFailure(owner, StageName(result.stage));
      CLog::Log(LOGERROR, "Infinity checkpoint existing file failed: owner={} stage={} errno={}",
                owner, StageName(result.stage), result.error);
      return false;
    }
    return true;
  };
  if (directory < 0)
    return finish();
  file = detail::RetryInterrupted([&] {
    return io.OpenAt(directory, leaf.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK, 0);
  });
  if (file < 0)
  {
    if (errno != ENOENT)
      detail::Fail(result, Stage::OpenExisting, errno);
    return finish(); // Absence is valid; do not create a default configuration.
  }
  struct stat state{};
  if (detail::RetryInterrupted([&] { return io.Stat(file, &state); }) != 0)
  {
    detail::Fail(result, Stage::StatExisting, errno);
    return finish();
  }
  if (!S_ISREG(state.st_mode))
  {
    detail::Fail(result, Stage::ValidateExisting, EINVAL);
    return finish();
  }
  if (detail::RetryInterrupted([&] { return io.Sync(file); }) != 0)
  {
    detail::Fail(result, Stage::SyncExisting, errno);
    return finish();
  }
  if (!detail::Close(io, file, result, Stage::CloseExisting))
    return finish();
  if (detail::RetryInterrupted([&] { return io.Sync(directory); }) != 0)
  {
    detail::Fail(result, Stage::SyncDirectory, errno);
    return finish();
  }
  return finish();
}

inline bool CheckpointExistingFile(const std::string& filename, const char* owner)
{
  infinity::checkpoint::files::PosixIo io;
  return CheckpointExistingFile(filename, owner, io);
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
