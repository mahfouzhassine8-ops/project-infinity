// Called only after a successful native namespace operation, while its exact
// writer/thread lease is still active. This is absence evidence, not fsync proof.
inline void RecordRemovedNamespace(uint64_t token, const std::string& raw)
{
  const auto path = Absolute(raw);
  if (path.empty() || path != raw || ProtectedCanonical(path) != path) return;
  struct stat st{};
  if (::lstat(path.c_str(), &st) == 0 || errno != ENOENT) return;
  auto& state = Get();
  std::lock_guard<std::mutex> lock(state.mutex);
  const auto found = state.protection.operations.find(token);
  if (found == state.protection.operations.end() ||
      found->second.thread != std::this_thread::get_id() ||
      found->second.paths.empty() || found->second.paths.front() != raw) return;
  const auto& operation = found->second.operation;
  if (operation != "rename" && operation != "replace" && operation != "remove" &&
      operation != "unlink" && operation != "rmdir") return;
  for (const auto& live : state.protection.operations)
    if (live.second.thread != found->second.thread &&
        live.second.namespaceEffect == NamespaceEffect::MAY_MUTATE)
    {
      if (live.second.paths.empty()) return;
      for (const auto& target : live.second.paths)
        if (target.empty() || Within(target,path) || Within(path,target)) return;
    }
  if (state.protection.removedNamespaces.size() >= 65536)
  { ProtectionFailureLocked(state.protection,"removed_namespace_inventory_exhausted"); return; }
  state.protection.removedNamespaces.insert(path);
}

// A vanished parent may be traversed only when every absent component has its
// own completed native removal/rename evidence. The first surviving directory
// is opened without following a final symlink, identity checked and fsynced.
// Unknown disappearance, a changed alias or an I/O failure remains a blocker.
inline bool SyncRemovedNamespace(const std::string& path,
                                 const std::set<std::string>& removed)
{
  std::string current = path;
  for (unsigned depth = 0; depth < 256; ++depth)
  {
    if (ProtectedCanonical(current) != current) return false;
    struct stat observed{};
    if (::lstat(current.c_str(), &observed) == 0)
    {
      if (!S_ISDIR(observed.st_mode) || S_ISLNK(observed.st_mode)) return false;
      const int fd = ::open(current.c_str(), O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
      if (fd < 0) return false;
      struct stat verified{};
      const bool same = ::fstat(fd,&verified) == 0 && S_ISDIR(verified.st_mode) &&
          observed.st_dev == verified.st_dev && observed.st_ino == verified.st_ino;
      int rc = -1;
      if (same) do { rc = ::fsync(fd); } while (rc < 0 && errno == EINTR);
      const int closed = ::close(fd);
      return same && rc == 0 && closed == 0;
    }
    if (errno != ENOENT || !removed.count(current)) return false;
    const auto slash = current.rfind('/');
    if (slash == std::string::npos || slash == 0) return false;
    current.resize(slash);
  }
  return false;
}
