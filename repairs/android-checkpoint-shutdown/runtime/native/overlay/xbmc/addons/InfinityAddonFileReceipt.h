/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

// Operation-local installer proof. No deletion, cancellation, process control
// or access to another owner's transaction. Unsupported paths fail closed.
#include <cerrno>
#include <cstdint>
#include <algorithm>
#include <dirent.h>
#include <fcntl.h>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include <functional>
#include <sys/stat.h>
#include <unistd.h>

namespace InfinityAddonFileReceipt
{
// Independent add-ons may run concurrently. The same target cannot be replaced
// while a failed operation verifies/restores its exact preimage.
class ResourceLock
{
public:
  explicit ResourceLock(const std::string& resource) : m_resource(Get(resource)),
      m_lock(m_resource ? std::unique_lock<std::mutex>(*m_resource) : std::unique_lock<std::mutex>()) {}
  bool Valid() const { return static_cast<bool>(m_resource); }
private:
  static std::shared_ptr<std::mutex> Get(const std::string& resource)
  {
    static std::mutex registryLock;
    static std::map<std::string, std::weak_ptr<std::mutex>> resources;
    std::lock_guard<std::mutex> lock(registryLock);
    if (resources.size() >= 1024)
    {
      for (auto i = resources.begin(); i != resources.end();)
      {
        if (i->second.expired()) i = resources.erase(i); else ++i;
      }
    }
    const auto found = resources.find(resource);
    auto value = found == resources.end() ? nullptr : found->second.lock();
    if (!value)
    {
      if (resources.size() >= 1024) return {};
      value = std::make_shared<std::mutex>(); resources[resource] = value;
    }
    return value;
  }
  std::shared_ptr<std::mutex> m_resource;
  std::unique_lock<std::mutex> m_lock;
};
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

// Exact bounded preimages, without title/version assumptions or hash shortcuts.
// Unsupported/large trees may still commit through Existing(), but cannot be
// called restored without a complete preimage. No symbolic links are followed.
struct ImageNode
{
  mode_t mode{0}; uid_t uid{0}; gid_t gid{0};
  std::vector<char> bytes;
  bool operator==(const ImageNode& other) const
  { return mode == other.mode && uid == other.uid && gid == other.gid && bytes == other.bytes; }
};
struct Image
{
  bool valid{false}; bool exists{false};
  std::map<std::string, ImageNode> nodes;
  bool operator==(const Image& other) const
  { return valid && other.valid && exists == other.exists && nodes == other.nodes; }
};
inline bool ReadImage(int fd, const std::string& relative, Image& image,
                      size_t& bytes, size_t& nodes, unsigned depth)
{
  if (depth > 64 || nodes == 0) return false;
  --nodes;
  struct stat before{}, after{};
  if (::fstat(fd, &before) != 0 || (!S_ISREG(before.st_mode) && !S_ISDIR(before.st_mode))) return false;
  auto& node = image.nodes[relative];
  node.mode = before.st_mode; node.uid = before.st_uid; node.gid = before.st_gid;
  if (S_ISREG(before.st_mode))
  {
    if (before.st_size < 0 || static_cast<uint64_t>(before.st_size) > bytes) return false;
    node.bytes.resize(static_cast<size_t>(before.st_size));
    bytes -= node.bytes.size();
    size_t position = 0;
    while (position < node.bytes.size())
    {
      const auto count = ::read(fd, node.bytes.data() + position, node.bytes.size() - position);
      if (count < 0 && errno == EINTR) continue;
      if (count <= 0) return false;
      position += static_cast<size_t>(count);
    }
  }
  else
  {
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
          !ReadImage(child.fd, relative + "/" + name, image, bytes, nodes, depth + 1) ||
          ::fstatat(fd, name.c_str(), &final, AT_SYMLINK_NOFOLLOW) != 0 || !Same(named, final))
      { ok = false; break; }
      errno = 0;
    }
    if (errno != 0) ok = false;
    if (::closedir(directory) != 0) ok = false;
    if (!ok) return false;
  }
  return ::fstat(fd, &after) == 0 && Same(before, after);
}
inline Image Capture(const std::string& raw, size_t budget = 32U * 1024U * 1024U)
{
  Image image;
  std::string path = raw;
  while (path.size() > 1 && path.back() == '/') path.pop_back();
  std::string name;
  Handle parent(OpenParent(path, name));
  if (parent.fd < 0) return image;
  struct stat named{}, opened{}, final{};
  if (::fstatat(parent.fd, name.c_str(), &named, AT_SYMLINK_NOFOLLOW) != 0)
  {
    if (errno == ENOENT && Removed(path)) image.valid = true;
    return image;
  }
  if (!S_ISREG(named.st_mode) && !S_ISDIR(named.st_mode)) return image;
  image.exists = true;
  Handle target(::openat(parent.fd, name.c_str(), O_RDONLY | O_NOFOLLOW | O_CLOEXEC |
                        (S_ISDIR(named.st_mode) ? O_DIRECTORY : 0)));
  size_t bytes = std::min(budget, size_t(32U * 1024U * 1024U)), nodes = 10000;
  if (target.fd >= 0 && ::fstat(target.fd, &opened) == 0 && Same(named, opened) &&
      ReadImage(target.fd, "", image, bytes, nodes, 0) &&
      ::fstatat(parent.fd, name.c_str(), &final, AT_SYMLINK_NOFOLLOW) == 0 && Same(named, final))
  { image.valid = true; }
  return image;
}

class WriteScope
{
public:
  WriteScope() : m_previous(s_current) { s_current = this; }
  ~WriteScope()
  {
    s_current = m_previous;
    if (m_previous)
    {
      try
      {
        for (auto& entry : m_before)
          m_previous->m_before.emplace(entry.first, std::move(entry.second));
        for (const auto& entry : m_settled) m_previous->m_settled[entry.first] = entry.second;
        m_previous->m_restored = m_previous->m_restored || m_restored;
        m_previous->m_unknown = m_previous->m_unknown || m_unknown;
      }
      catch (...) { m_previous->m_unknown = true; }
    }
  }
  static WriteScope* Current() { return s_current; }
  void Touch(const std::string& path)
  {
    if (m_before.find(path) == m_before.end())
    {
      if (m_before.size() >= 256) { m_unknown = true; return; }
      size_t available = m_remaining;
      for (auto* parent = m_previous; parent; parent = parent->m_previous)
        available = std::min(available, parent->m_remaining);
      auto image = Capture(path, available);
      size_t used = 0;
      for (const auto& node : image.nodes) used += node.second.bytes.size();
      for (auto* scope = this; scope; scope = scope->m_previous)
        scope->m_remaining -= std::min(scope->m_remaining, used);
      m_before.emplace(path, std::move(image));
    }
    m_settled[path] = false;
  }
  bool BeforeAbsent(const std::string& path) const
  {
    const auto found = m_before.find(path);
    return found != m_before.end() && found->second.valid && !found->second.exists;
  }
  bool Committed(const std::string& path, bool directory)
  { return m_settled[path] = Existing(path, directory); }
  bool Deleted(const std::string& path)
  { return m_settled[path] = Removed(path); }
  bool Restored(const std::string& path)
  {
    const auto found = m_before.find(path);
    if (found == m_before.end() || !found->second.valid) return false;
    const auto image = Capture(path);
    const bool same = image == found->second &&
        (image.exists ? Existing(path, S_ISDIR(image.nodes.at("").mode)) : Removed(path));
    m_settled[path] = same;
    m_restored = m_restored || same;
    return same;
  }
  void Unknown() { m_unknown = true; }
  bool Proven() const
  {
    if (m_unknown) return false;
    for (const auto& entry : m_settled) if (!entry.second) return false;
    return true;
  }
  bool Touched() const { return !m_settled.empty(); }
  bool WasRestored() const { return m_restored; }
  std::function<bool()> RestorationProof(size_t& bytes) const
  {
    bytes = 0;
    if (m_unknown) return {};
    std::map<std::string, Image> unresolved;
    for (const auto& scope : m_settled)
    {
      if (scope.second) continue;
      const auto before = m_before.find(scope.first);
      if (before == m_before.end() || !before->second.valid) return {};
      for (const auto& node : before->second.nodes) bytes += node.second.bytes.size();
      unresolved.emplace(before->first, before->second);
    }
    if (unresolved.empty()) return {};
    return [scopes = std::move(unresolved)]() {
      for (const auto& scope : scopes)
      {
        const auto current = Capture(scope.first);
        if (!(current == scope.second) || !(current.exists ?
            Existing(scope.first, S_ISDIR(current.nodes.at("").mode)) : Removed(scope.first))) return false;
      }
      return true;
    };
  }
  WriteScope(const WriteScope&) = delete;
  WriteScope& operator=(const WriteScope&) = delete;
private:
  WriteScope* m_previous;
  std::map<std::string, Image> m_before;
  std::map<std::string, bool> m_settled;
  bool m_restored{false}; bool m_unknown{false};
  size_t m_remaining{64U * 1024U * 1024U};
  static inline thread_local WriteScope* s_current{nullptr};
};
} // namespace InfinityAddonFileReceipt
