#pragma once

// A persistence primitive, not a shutdown acknowledgement. The caller must hold
// the owning subsystem's writer/namespace fence for the entire call, serialize
// the authoritative dirty state, and clear its dirty generation only on success.
// Every component of path must be a real directory; the leaf must be absent or
// a regular file. New files are private (0600); replacements retain ownership,
// mode, ACLs and extended attributes (including SELinux labels). Failure to
// inspect or preserve metadata fails before rename; it never weakens access.

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
#include <sys/xattr.h>
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
  ReadMetadata,
  PreserveOwner,
  PreserveMode,
  PreserveMetadata,
  VerifyMetadata,
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
    case Stage::ReadMetadata: return "read_metadata";
    case Stage::PreserveOwner: return "preserve_owner";
    case Stage::PreserveMode: return "preserve_mode";
    case Stage::PreserveMetadata: return "preserve_metadata";
    case Stage::VerifyMetadata: return "verify_metadata";
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
  // Metadata diagnostics contain names only, never attribute values.
  const char* metadataOperation{nullptr};
  std::string metadataAttribute;
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
  virtual int Chown(int fd, uid_t uid, gid_t gid) { return ::fchown(fd, uid, gid); }
  virtual ssize_t ListAttributes(int fd, char* names, size_t size)
  { return ::flistxattr(fd, names, size); }
  virtual ssize_t GetAttribute(int fd, const char* name, void* value, size_t size)
  { return ::fgetxattr(fd, name, value, size); }
  virtual int SetAttribute(int fd, const char* name, const void* value, size_t size)
  { return ::fsetxattr(fd, name, value, size, 0); }
  virtual int RemoveAttribute(int fd, const char* name) { return ::fremovexattr(fd, name); }
  virtual int Sync(int fd) { return ::fsync(fd); }
  virtual int Close(int fd) { return ::close(fd); }
  virtual int RenameAt(int fromDir, const char* from, int toDir, const char* to)
  { return ::renameat(fromDir, from, toDir, to); }
  virtual int UnlinkAt(int dir, const char* path) { return ::unlinkat(dir, path, 0); }
};

namespace detail
{
using Attributes = std::vector<std::pair<std::string, std::vector<char>>>;
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

inline bool ReadAttributes(PosixIo& io, int fd, Attributes& attributes,
                           Result& result, Stage stage)
{
  const auto failMetadata = [&](const char* operation, int error,
                                const std::string& attribute = std::string{}) {
    if (result.stage == Stage::None)
    {
      result.metadataOperation = operation;
      result.metadataAttribute = attribute;
    }
    Fail(result, stage, error);
    return false;
  };
  // Linux caps the list and each value at 64 KiB. Bound allocations and reject
  // a concurrently changing set: the caller must hold its namespace fence.
  const auto count = RetryInterrupted([&] { return io.ListAttributes(fd, nullptr, 0); });
  if (count < 0 || count > 65536)
  {
    return failMetadata("flistxattr_size", count < 0 ? errno : E2BIG);
  }
  if (!count)
    return true;
  std::vector<char> names(static_cast<size_t>(count));
  const auto actual = RetryInterrupted([&] { return io.ListAttributes(fd, names.data(), names.size()); });
  if (actual != count)
  {
    return failMetadata("flistxattr_names", actual < 0 ? errno : EBUSY);
  }
  for (size_t start = 0; start < names.size();)
  {
    size_t end = start;
    while (end < names.size() && names[end])
      ++end;
    if (end == names.size() || end == start)
    {
      return failMetadata("flistxattr_parse", EINVAL);
    }
    const std::string name(names.data() + start, end - start);
    const auto size = RetryInterrupted([&] { return io.GetAttribute(fd, name.c_str(), nullptr, 0); });
    if (size < 0 && errno == ENODATA && name == "system.posix_acl_access")
    {
      // A listed optional ACL with no readable value can be synthetic on
      // Android. Only a stable, demonstrably absent ACL may be omitted.
      // All real ACL/SELinux metadata and uncertain cases remain mandatory.
      struct stat before{}, after{};
      if (io.Stat(fd, &before) != 0 || !S_ISREG(before.st_mode))
        return failMetadata("acl_absence_stat", EBUSY, name);
      bool absent = true;
      for (unsigned retry = 0; retry < 2; ++retry)
      {
        const auto probe = RetryInterrupted([&] {
          return io.GetAttribute(fd, name.c_str(), nullptr, 0);
        });
        if (probe >= 0 || errno != ENODATA)
        {
          absent = false;
          break;
        }
      }
      const auto listedSize = RetryInterrupted([&] {
        return io.ListAttributes(fd, nullptr, 0);
      });
      std::vector<char> confirmedNames(names.size());
      const auto listed = listedSize == static_cast<ssize_t>(names.size()) ?
          RetryInterrupted([&] { return io.ListAttributes(fd, confirmedNames.data(), confirmedNames.size()); }) : -1;
      if (io.Stat(fd, &after) != 0 || !absent ||
          listed != static_cast<ssize_t>(names.size()) ||
          confirmedNames != names || before.st_dev != after.st_dev ||
          before.st_ino != after.st_ino || before.st_uid != after.st_uid ||
          before.st_gid != after.st_gid || before.st_mode != after.st_mode ||
          before.st_ctime != after.st_ctime || before.st_size != after.st_size)
        return failMetadata("acl_absence_not_verified", EBUSY, name);
      start = end + 1;
      continue;
    }
    if (size < 0 || size > 65536)
    {
      return failMetadata("fgetxattr_size", size < 0 ? errno : E2BIG, name);
    }
    std::vector<char> value(static_cast<size_t>(size));
    const auto read = RetryInterrupted([&] { return io.GetAttribute(fd, name.c_str(), value.data(), value.size()); });
    if (read != size)
    {
      return failMetadata("fgetxattr_value", read < 0 ? errno : EBUSY, name);
    }
    attributes.emplace_back(name, std::move(value));
    start = end + 1;
  }
  return true;
}

inline bool PreserveAttributes(PosixIo& io, int fd, const Attributes& required, Result& result)
{
  Attributes current;
  if (!ReadAttributes(io, fd, current, result, Stage::PreserveMetadata))
    return false;
  for (const auto& attribute : required)
  {
    bool same = false;
    for (const auto& present : current)
      if (present == attribute)
        same = true;
    // In particular do not reset an already matching SELinux label: an app
    // may read it and inherit it without being allowed to relabel the inode.
    if (!same && RetryInterrupted([&] {
          return io.SetAttribute(fd, attribute.first.c_str(), attribute.second.data(), attribute.second.size());
        }) != 0)
    {
      Fail(result, Stage::PreserveMetadata, errno);
      return false;
    }
  }
  for (const auto& present : current)
  {
    bool requiredName = false;
    for (const auto& attribute : required)
      if (present.first == attribute.first)
        requiredName = true;
    if (!requiredName && RetryInterrupted([&] { return io.RemoveAttribute(fd, present.first.c_str()); }) != 0)
    {
      Fail(result, Stage::PreserveMetadata, errno);
      return false;
    }
  }
  Attributes verified;
  if (!ReadAttributes(io, fd, verified, result, Stage::VerifyMetadata))
    return false;
  if (verified.size() != required.size())
  {
    Fail(result, Stage::VerifyMetadata, EIO);
    return false;
  }
  for (const auto& attribute : required)
  {
    bool found = false;
    for (const auto& actual : verified)
      if (actual == attribute)
        found = true;
    if (!found)
    {
      Fail(result, Stage::VerifyMetadata, EIO);
      return false;
    }
  }
  return true;
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

// Traverse ancestors without requiring permission to list them. Android can
// grant search access to an app's own directory while denying ancestor reads.
// O_PATH handles still pin each O_NOFOLLOW directory. Only the final parent is
// opened for reading, because its namespace must be fsynced after the save.
// Reject '..' to keep the caller's chosen namespace unambiguous.
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
  constexpr int flags = O_PATH | O_CLOEXEC | O_DIRECTORY | O_NOFOLLOW;
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
  int parent = RetryInterrupted([&] {
    return io.OpenAt(directory, ".", O_RDONLY | O_CLOEXEC | O_DIRECTORY | O_NOFOLLOW, 0);
  });
  if (parent < 0)
  {
    Fail(result, Stage::OpenDirectory, errno);
    Close(io, directory, result, Stage::CloseDirectory);
    return -1;
  }
  if (!Close(io, directory, result, Stage::CloseDirectory))
  {
    Close(io, parent, result, Stage::CloseDirectory);
    return -1;
  }
  return parent;
}
} // namespace detail

namespace detail
{
inline Result SaveDirtyImpl(const std::string& path, std::string_view bytes, PosixIo& io,
                            bool freshProtocolRecord)
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
  struct stat original{};
  detail::Attributes attributes;
  const bool replacing = existing >= 0;
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
    if (!freshProtocolRecord)
      mode = state.st_mode & 07777;
    original = state;
    same = !freshProtocolRecord && state.st_size >= 0 &&
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
    if (!same && !freshProtocolRecord &&
        !detail::ReadAttributes(io, existing, attributes, result, Stage::ReadMetadata))
      return finish();
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
    if (replacing && !freshProtocolRecord)
    {
      struct stat created{};
      if (detail::RetryInterrupted([&] { return io.Stat(temporary, &created); }) != 0)
      {
        detail::Fail(result, Stage::PreserveOwner, errno);
        return finish();
      }
      if ((created.st_uid != original.st_uid || created.st_gid != original.st_gid) &&
          detail::RetryInterrupted([&] { return io.Chown(temporary, original.st_uid, original.st_gid); }) != 0)
      {
        detail::Fail(result, Stage::PreserveOwner, errno);
        return finish();
      }
    }
    if (detail::RetryInterrupted([&] { return io.Chmod(temporary, mode); }) != 0)
    {
      detail::Fail(result, Stage::PreserveMode, errno);
      return finish();
    }
    if (replacing && !freshProtocolRecord)
    {
      if (!detail::PreserveAttributes(io, temporary, attributes, result))
        return finish();
      struct stat verified{};
      if (detail::RetryInterrupted([&] { return io.Stat(temporary, &verified); }) != 0 ||
          verified.st_uid != original.st_uid || verified.st_gid != original.st_gid ||
          (verified.st_mode & 07777) != mode)
      {
        detail::Fail(result, Stage::VerifyMetadata, EIO);
        return finish();
      }
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
} // namespace detail

inline Result SaveDirty(const std::string& path, std::string_view bytes, PosixIo& io)
{
  return detail::SaveDirtyImpl(path, bytes, io, false);
}

// These two native-generated control records are fresh messages, not user
// settings. Publish a newly created 0600 sibling exactly as the Python
// participant publishes its protocol JSON. Do not transplant metadata from a
// retired message inode. All path, write, close, rename and durability checks
// are shared with SaveDirty; user files always retain its strict metadata policy.
inline Result SaveProtocolRecord(const std::string& path, std::string_view bytes, PosixIo& io)
{
  const auto slash = path.rfind('/');
  const std::string leaf = slash == std::string::npos ? std::string{} : path.substr(slash + 1);
  const std::string parent = slash == std::string::npos ? std::string{} : path.substr(0, slash);
  constexpr const char* control = "/.android-checkpoint";
  const size_t length = std::strlen(control);
  if ((leaf != "engine.json" && leaf != "request.json") || parent.size() < length ||
      parent.compare(parent.size() - length, length, control) != 0)
  {
    Result result;
    detail::Fail(result, Stage::ValidatePath, EINVAL);
    return result;
  }
  return detail::SaveDirtyImpl(path, bytes, io, true);
}

inline Result SaveProtocolRecord(const std::string& path, std::string_view bytes)
{
  PosixIo io;
  return SaveProtocolRecord(path, bytes, io);
}

inline Result SaveDirty(const std::string& path, std::string_view bytes)
{
  PosixIo io;
  return SaveDirty(path, bytes, io);
}
} // namespace infinity::checkpoint::files
