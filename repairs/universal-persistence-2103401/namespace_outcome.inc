// Called only after a successful native namespace operation, while its exact
// writer/thread lease is still active. This is absence evidence, not fsync proof.
inline void RecordRemovedNamespace(uint64_t token)
{
  auto& state = Get();
  std::lock_guard<std::mutex> lock(state.mutex);
  const auto found = state.protection.operations.find(token);
  if (found == state.protection.operations.end() ||
      found->second.thread != std::this_thread::get_id() ||
      found->second.actualPaths.empty()) return;
  const auto& raw=found->second.actualPaths.front();
  const auto path=Absolute(raw);
  const auto& operation = found->second.operation;
  if (operation != "rename" && operation != "replace" && operation != "remove" &&
      operation != "unlink" && operation != "rmdir") return;
  // Inspect and record under the admission mutex. A new mutator cannot finish
  // between the absence check and insertion; an already admitted overlapping
  // mutator remains visible below until it ends under the same mutex.
  const auto canonical=ProtectedCanonical(path);
  std::string rejection;
  if (path.empty() || path != raw || canonical != path)
    rejection="removal_identity_unverified;canonical="+canonical;
  struct stat st{};
  if(rejection.empty())
  {
    const int result=::lstat(path.c_str(),&st),error=errno;
    if(result==0 || error!=ENOENT)
      rejection="removal_absence_unverified;lstat="+std::to_string(result)+";errno="+std::to_string(error);
  }
  if(!rejection.empty())
  { NamespaceEvidenceLocked(state.protection,path,rejection+";"+NamespaceLease(state,found->second));return; }
  for (const auto& live : state.protection.operations)
    if (live.second.thread != found->second.thread &&
        live.second.namespaceEffect == NamespaceEffect::MAY_MUTATE)
    {
      if (live.second.paths.empty())
      { NamespaceEvidenceLocked(state.protection,path,"concurrent_unknown_target;"+NamespaceLease(state,live.second));return; }
      for (const auto& target : live.second.paths)
        if (target.empty() || Within(target,path) || Within(path,target))
        { NamespaceEvidenceLocked(state.protection,path,"concurrent_overlap;target="+target+";"+NamespaceLease(state,live.second));return; }
    }
  if (state.protection.removedNamespaces.size() >= 65536)
  { ProtectionFailureLocked(state.protection,"removed_namespace_inventory_exhausted"); return; }
  state.protection.removedNamespaces.insert(path);
  NamespaceEvidenceLocked(state.protection,path,"observed_absent;"+NamespaceLease(state,found->second));
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
