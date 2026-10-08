#pragma once

// A persistence primitive, not a shutdown acknowledgement. The caller must hold
// the owning subsystem's writer/namespace fence for the entire call, serialize
// the authoritative dirty state, and clear its dirty generation only on success.
// Every component of path must be a real directory; the leaf must be absent or
// a regular file. New files are private (0600); replacements retain mode bits.
// Ownership, ACLs, extended attributes and SELinux labels are NOT copied: callers
// must not use this helper for files whose metadata requires another save path.

#include <atomic>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <string>
#include <string_view>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <utility>
#include <vector>

namespace infinity::checkpoint::files
{
enum class Stage
{
  None,
  ValidatePath,
  OpenDirectory,
  CloseDirectory,
  OpenExisting,
  StatExisting,
  ValidateExisting,
  ReadExisting,
  SyncExisting,
  CloseExisting,
  CreateTemporary,
  WriteTemporary,
  PreserveMode,
  SyncTemporary,
  CloseTemporary,
  Rename,
  SyncDirectory,
  RemoveTemporary,
};

inline const char* StageName(Stage stage)
{
  switch (stage)
  {
    case Stage::None: return "none";
    case Stage::ValidatePath: return "validate_path";
    case Stage::OpenDirectory: return "open_directory";
    case Stage::CloseDirectory: return "close_directory";
    case Stage::OpenExisting: return "open_existing";
    case Stage::StatExisting: return "stat_existing";
    case Stage::ValidateExisting: return "validate_existing";
    case Stage::ReadExisting: return "read_existing";
    case Stage::SyncExisting: return "fsync_existing";
    case Stage::CloseExisting: return "close_existing";
    case Stage::CreateTemporary: return "create_temporary";
    case Stage::WriteTemporary: return "write_temporary";
    case Stage::PreserveMode: return "preserve_mode";
    case Stage::SyncTemporary: return "fsync_temporary";
    case Stage::CloseTemporary: return "close_temporary";
    case Stage::Rename: return "rename";
    case Stage::SyncDirectory: return "fsync_directory";
    case Stage::RemoveTemporary: return "remove_temporary";
  }
  return "unknown";
}

struct Result
{
  bool ok{false};
  Stage stage{Stage::None};
  int error{0};
  // The first additional cleanup failure is retained without masking the cause.
  Stage cleanupStage{Stage::None};
  int cleanupError{0};
  bool renameAttempted{false};
  bool replaced{false};
  bool dataAndDirectorySynced{false};
  // If renameAttempted && !replaced, rename returned an error; conservatively
  // treat visibility as uncertain. If replaced && !dataAndDirectorySynced, the
  // new bytes are visible but crash durability is unconfirmed. Neither is safe
  // to acknowledge. A matching dirty file still gets file AND directory fsync.
};

// Small syscall seam for failure-injection tests. Overrides must preserve POSIX
// return/errno conventions and fd lifetime semantics. In particular Close must
// consume its fd even when simulating an error; close is never retried because
// on Linux/Android the descriptor may already have been released.
class PosixIo
{
public:
  virtual ~PosixIo() = default;
  virtual int OpenAt(int dir, const char* path, int flags, mode_t mode)
  { return ::openat(dir, path, flags, mode); }
  virtual int Stat(int fd, struct stat* value) { return ::fstat(fd, value); }
  virtual ssize_t Read(int fd, void* data, size_t size) { return ::read(fd, data, size); }
  virtual ssize_t Write(int fd, const void* data, size_t size)
  { return ::write(fd, data, size); }
  virtual int Chmod(int fd, mode_t mode) { return ::fchmod(fd, mode); }
  virtual int Sync(int fd) { return ::fsync(fd); }
  virtual int Close(int fd) { return ::close(fd); }
  virtual int RenameAt(int fromDir, const char* from, int toDir, const char* to)
  { return ::renameat(fromDir, from, toDir, to); }
  virtual int UnlinkAt(int dir, const char* path) { return ::unlinkat(dir, path, 0); }
};

namespace detail
{
template<typename Function>
inline auto RetryInterrupted(Function call) -> decltype(call())
{
  decltype(call()) value;
  do { value = call(); } while (value < 0 && errno == EINTR);
  return value;
}

inline void Fail(Result& result, Stage stage, int error)
{
  if (result.stage == Stage::None)
  {
    result.stage = stage;
    result.error = error ? error : EIO;
  }
  else if (result.cleanupStage == Stage::None)
  {
    result.cleanupStage = stage;
    result.cleanupError = error ? error : EIO;
  }
}

inline bool Close(PosixIo& io, int& fd, Result& result, Stage stage)
{
  if (fd < 0)
    return true;
  const int closing = fd;
  fd = -1;
  if (io.Close(closing) == 0)
    return true;
  Fail(result, stage, errno);
  return false;
}

template<typename Function>
struct ScopeExit
{
  const Function& function;
  ~ScopeExit() { function(); }
};

// Open every parent with O_NOFOLLOW instead of silently following an ancestor
// symlink. Reject '..' to keep the caller's chosen namespace unambiguous.
inline int OpenParent(PosixIo& io, const std::string& path,
                      std::string& leaf, Result& result)
{
  if (path.empty() || path.back() == '/' || path.find('\0') != std::string::npos)
  {
    Fail(result, Stage::ValidatePath, EINVAL);
    return -1;
  }
  const auto lastSlash = path.rfind('/');
  leaf = lastSlash == std::string::npos ? path : path.substr(lastSlash + 1);
  if (leaf == "." || leaf == "..")
  {
    Fail(result, Stage::ValidatePath, EINVAL);
    return -1;
  }
  // Complete allocating/parsing before owning a descriptor, so allocation
  // failure cannot leak an open directory.
  std::vector<std::string> components;
  size_t start = path.front() == '/' ? 1 : 0;
  while (lastSlash != std::string::npos && start < lastSlash)
  {
    const size_t end = path.find('/', start);
    const std::string component = path.substr(start, end - start);
    start = end + 1;
    if (component.empty() || component == ".")
      continue;
    if (component == "..")
    {
      Fail(result, Stage::ValidatePath, EINVAL);
      return -1;
    }
    components.push_back(component);
  }
  constexpr int flags = O_RDONLY | O_CLOEXEC | O_DIRECTORY | O_NOFOLLOW;
  int directory = RetryInterrupted([&] {
    return io.OpenAt(AT_FDCWD, path.front() == '/' ? "/" : ".", flags, 0);
  });
  if (directory < 0)
  {
    Fail(result, Stage::OpenDirectory, errno);
    return -1;
  }
  for (const auto& component : components)
  {
    int next = RetryInterrupted([&] {
      return io.OpenAt(directory, component.c_str(), flags, 0);
    });
    if (next < 0)
    {
      Fail(result, Stage::OpenDirectory, errno);
      Close(io, directory, result, Stage::CloseDirectory);
      return -1;
    }
    if (!Close(io, directory, result, Stage::CloseDirectory))
    {
      Close(io, next, result, Stage::CloseDirectory);
      return -1;
    }
    directory = next;
  }
  return directory;
}
} // namespace detail

inline Result SaveDirty(const std::string& path, std::string_view bytes, PosixIo& io)
{
  Result result;
  std::string leaf;
  int directory = detail::OpenParent(io, path, leaf, result);
  if (directory < 0)
    return result;
  int existing = -1;
  int temporary = -1;
  std::string temporaryName;
  bool finished = false;
  const auto finish = [&]() {
    if (finished)
      return result;
    finished = true;
    detail::Close(io, existing, result, Stage::CloseExisting);
    detail::Close(io, temporary, result, Stage::CloseTemporary);
    if (!temporaryName.empty())
    {
      if (detail::RetryInterrupted([&] {
            return io.UnlinkAt(directory, temporaryName.c_str());
          }) != 0)
        detail::Fail(result, Stage::RemoveTemporary, errno);
    }
    detail::Close(io, directory, result, Stage::CloseDirectory);
    result.ok = result.stage == Stage::None;
    return result;
  };
  // Also releases descriptors/our temporary on C++ allocation exceptions. Such
  // exceptions propagate and must never be translated into a successful save.
  const detail::ScopeExit<decltype(finish)> cleanup{finish};

  existing = detail::RetryInterrupted([&] {
    return io.OpenAt(directory, leaf.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK, 0);
  });
  if (existing < 0 && errno != ENOENT)
  {
    detail::Fail(result, Stage::OpenExisting, errno);
    return finish();
  }
  mode_t mode = 0600;
  bool same = false;
  if (existing >= 0)
  {
    struct stat state{};
    if (detail::RetryInterrupted([&] { return io.Stat(existing, &state); }) != 0)
    {
      detail::Fail(result, Stage::StatExisting, errno);
      return finish();
    }
    if (!S_ISREG(state.st_mode))
    {
      detail::Fail(result, Stage::ValidateExisting, EINVAL);
      return finish();
    }
    mode = state.st_mode & 07777;
    same = state.st_size >= 0 &&
           static_cast<uintmax_t>(state.st_size) == static_cast<uintmax_t>(bytes.size());
    size_t offset = 0;
    char buffer[8192];
    while (same && offset < bytes.size())
    {
      const size_t remaining = bytes.size() - offset;
      const size_t length = remaining < sizeof(buffer) ? remaining : sizeof(buffer);
      const ssize_t count = detail::RetryInterrupted([&] {
        return io.Read(existing, buffer, length);
      });
      if (count < 0)
      {
        detail::Fail(result, Stage::ReadExisting, errno);
        return finish();
      }
      if (count == 0 || std::memcmp(buffer, bytes.data() + offset, static_cast<size_t>(count)) != 0)
        same = false;
      else
        offset += static_cast<size_t>(count);
    }
    if (same)
    {
      const ssize_t count = detail::RetryInterrupted([&] { return io.Read(existing, buffer, 1); });
      if (count < 0)
      {
        detail::Fail(result, Stage::ReadExisting, errno);
        return finish();
      }
      same = count == 0;
    }
    if (same && detail::RetryInterrupted([&] { return io.Sync(existing); }) != 0)
    {
      detail::Fail(result, Stage::SyncExisting, errno);
      return finish();
    }
    if (!detail::Close(io, existing, result, Stage::CloseExisting))
      return finish();
  }

  if (!same)
  {
    // O_EXCL prevents clobbering an existing sibling, including stale temps.
    static std::atomic<uint64_t> serial{0};
    for (unsigned int attempt = 0; attempt < 64; ++attempt)
    {
      std::string candidate = ".infinity-checkpoint-" + std::to_string(::getpid()) +
                              "-" + std::to_string(serial.fetch_add(1));
      temporary = detail::RetryInterrupted([&] {
        return io.OpenAt(directory, candidate.c_str(),
                         O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
      });
      if (temporary >= 0)
      {
        temporaryName = std::move(candidate);
        break;
      }
      if (errno != EEXIST)
      {
        detail::Fail(result, Stage::CreateTemporary, errno);
        return finish();
      }
    }
    if (temporary < 0)
    {
      detail::Fail(result, Stage::CreateTemporary, EEXIST);
      return finish();
    }
    size_t offset = 0;
    while (offset < bytes.size())
    {
      // Bounded writes are portable even when size_t exceeds ssize_t.
      constexpr size_t chunk = 1024 * 1024;
      const size_t remaining = bytes.size() - offset;
      const size_t length = remaining < chunk ? remaining : chunk;
      const ssize_t count = detail::RetryInterrupted([&] {
        return io.Write(temporary, bytes.data() + offset, length);
      });
      if (count <= 0)
      {
        detail::Fail(result, Stage::WriteTemporary, count == 0 ? EIO : errno);
        return finish();
      }
      offset += static_cast<size_t>(count);
    }
    if (detail::RetryInterrupted([&] { return io.Chmod(temporary, mode); }) != 0)
    {
      detail::Fail(result, Stage::PreserveMode, errno);
      return finish();
    }
    if (detail::RetryInterrupted([&] { return io.Sync(temporary); }) != 0)
    {
      detail::Fail(result, Stage::SyncTemporary, errno);
      return finish();
    }
    if (!detail::Close(io, temporary, result, Stage::CloseTemporary))
      return finish();
    result.renameAttempted = true;
    if (io.RenameAt(directory, temporaryName.c_str(), directory, leaf.c_str()) != 0)
    {
      detail::Fail(result, Stage::Rename, errno);
      return finish();
    }
    result.replaced = true;
    temporaryName.clear();
  }
  if (detail::RetryInterrupted([&] { return io.Sync(directory); }) != 0)
  {
    detail::Fail(result, Stage::SyncDirectory, errno);
    return finish();
  }
  result.dataAndDirectorySynced = true;
  return finish();
}

inline Result SaveDirty(const std::string& path, std::string_view bytes)
{
  PosixIo io;
  return SaveDirty(path, bytes, io);
}
} // namespace infinity::checkpoint::files
