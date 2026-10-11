/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

// Operation-local installer proof. No deletion, cancellation, process control
// or access to another owner's transaction. Unsupported paths fail closed.
#include <cerrno>
#include <dirent.h>
#include <fcntl.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>

namespace InfinityAddonFileReceipt
{
struct Handle
{
  int fd{-1};
  explicit Handle(int value) : fd(value) {}
  ~Handle() { if (fd >= 0) ::close(fd); }
  Handle(const Handle&) = delete;
  Handle& operator=(const Handle&) = delete;
};
inline bool Same(const struct stat& a, const struct stat& b)
{
  return a.st_dev == b.st_dev && a.st_ino == b.st_ino && a.st_mode == b.st_mode &&
      a.st_size == b.st_size && a.st_mtim.tv_sec == b.st_mtim.tv_sec &&
      a.st_mtim.tv_nsec == b.st_mtim.tv_nsec && a.st_ctim.tv_sec == b.st_ctim.tv_sec &&
      a.st_ctim.tv_nsec == b.st_ctim.tv_nsec;
}
inline bool Sync(int fd)
{
  for (unsigned attempt = 0; attempt < 4; ++attempt)
  {
    if (::fsync(fd) == 0) return true;
    if (errno != EINTR) return false;
  }
  return false;
}
inline int OpenParent(const std::string& path, std::string& name)
{
  if (path.empty() || path.front() != '/' || path.back() == '/') return -1;
  const auto split = path.find_last_of('/');
  name = path.substr(split + 1);
  if (name.empty() || name == "." || name == "..") return -1;
  int fd = ::open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
  if (fd < 0) return -1;
  size_t pos = 1;
  while (pos < split)
  {
    auto end = path.find('/', pos);
    if (end == std::string::npos || end > split) end = split;
    const auto part = path.substr(pos, end - pos);
    if (!part.empty())
    {
      if (part == "." || part == "..") { ::close(fd); return -1; }
      const int next = ::openat(fd, part.c_str(), O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
      ::close(fd);
      fd = next;
      if (fd < 0) return -1;
    }
    pos = end + 1;
  }
  return fd;
}
inline bool Tree(int fd, unsigned depth, size_t& remaining)
{
  if (depth > 64 || remaining == 0) return false;
  --remaining;
  struct stat before{}, after{};
  if (::fstat(fd, &before) != 0) return false;
  if (S_ISREG(before.st_mode))
    return Sync(fd) && ::fstat(fd, &after) == 0 && Same(before, after);
  if (!S_ISDIR(before.st_mode)) return false;
  DIR* directory = ::fdopendir(::dup(fd));
  if (!directory) return false;
  bool ok = true;
  errno = 0;
  while (auto* entry = ::readdir(directory))
  {
    const std::string name(entry->d_name);
    if (name == "." || name == "..") { errno = 0; continue; }
    struct stat named{}, opened{}, final{};
    if (::fstatat(fd, name.c_str(), &named, AT_SYMLINK_NOFOLLOW) != 0 ||
        (!S_ISREG(named.st_mode) && !S_ISDIR(named.st_mode))) { ok = false; break; }
    Handle child(::openat(fd, name.c_str(), O_RDONLY | O_NOFOLLOW | O_CLOEXEC |
                         (S_ISDIR(named.st_mode) ? O_DIRECTORY : 0)));
    if (child.fd < 0 || ::fstat(child.fd, &opened) != 0 || !Same(named, opened) ||
        !Tree(child.fd, depth + 1, remaining) ||
        ::fstatat(fd, name.c_str(), &final, AT_SYMLINK_NOFOLLOW) != 0 || !Same(named, final))
    { ok = false; break; }
    errno = 0;
  }
  if (errno != 0) ok = false;
  if (::closedir(directory) != 0) ok = false;
  return ok && Sync(fd) && ::fstat(fd, &after) == 0 && Same(before, after);
}
inline bool Existing(const std::string& path, bool tree)
{
  std::string name;
  Handle parent(OpenParent(path, name));
  if (parent.fd < 0) return false;
  struct stat named{}, opened{}, final{};
  if (::fstatat(parent.fd, name.c_str(), &named, AT_SYMLINK_NOFOLLOW) != 0) return false;
  if (tree ? !S_ISDIR(named.st_mode) : !S_ISREG(named.st_mode)) return false;
  Handle target(::openat(parent.fd, name.c_str(), O_RDONLY | O_NOFOLLOW | O_CLOEXEC |
                        (tree ? O_DIRECTORY : 0)));
  size_t remaining = 100000;
  return target.fd >= 0 && ::fstat(target.fd, &opened) == 0 && Same(named, opened) &&
      Tree(target.fd, 0, remaining) && Sync(parent.fd) &&
      ::fstatat(parent.fd, name.c_str(), &final, AT_SYMLINK_NOFOLLOW) == 0 && Same(named, final);
}
inline bool Directory(const std::string& raw)
{
  std::string path = raw;
  while (path.size() > 1 && path.back() == '/') path.pop_back();
  std::string name;
  Handle parent(OpenParent(path, name));
  if (parent.fd < 0) return false;
  Handle directory(::openat(parent.fd, name.c_str(), O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC));
  struct stat named{}, opened{}, final{};
  return directory.fd >= 0 && ::fstatat(parent.fd, name.c_str(), &named, AT_SYMLINK_NOFOLLOW) == 0 &&
      ::fstat(directory.fd, &opened) == 0 && Same(named, opened) && Sync(directory.fd) && Sync(parent.fd) &&
      ::fstatat(parent.fd, name.c_str(), &final, AT_SYMLINK_NOFOLLOW) == 0 && Same(named, final);
}
inline bool Removed(const std::string& raw)
{
  std::string path = raw;
  while (path.size() > 1 && path.back() == '/') path.pop_back();
  std::string name;
  Handle parent(OpenParent(path, name));
  if (parent.fd < 0) return false;
  struct stat value{};
  if (::fstatat(parent.fd, name.c_str(), &value, AT_SYMLINK_NOFOLLOW) == 0 || errno != ENOENT) return false;
  return Sync(parent.fd) && ::fstatat(parent.fd, name.c_str(), &value, AT_SYMLINK_NOFOLLOW) != 0 && errno == ENOENT;
}
} // namespace InfinityAddonFileReceipt
