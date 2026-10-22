// A procfs " (deleted)" annotation is not itself namespace evidence. FUSE can
// retain it on a live descriptor whose original named file still has one link.
// Resolve it only by proving the live descriptor and a no-follow opened name
// identify the same object. Never guess from the spelling or an add-on name.
inline bool SameDescriptorObject(const struct stat& a,const struct stat& b)
{
  return a.st_dev==b.st_dev && a.st_ino==b.st_ino && a.st_mode==b.st_mode &&
      a.st_uid==b.st_uid && a.st_gid==b.st_gid && a.st_nlink==b.st_nlink;
}
inline bool VerifiedDescriptorName(int descriptor,const struct stat& original,
                                   const std::string& path)
{
  if(path.empty() || path.front()!='/' || ProtectedCanonical(path)!=path)return false;
  struct stat named{},opened{},current{};
  if(::lstat(path.c_str(),&named)!=0 || S_ISLNK(named.st_mode) ||
     !SameDescriptorObject(original,named))return false;
  if((S_ISREG(named.st_mode) && named.st_nlink!=1) ||
     (!S_ISREG(named.st_mode) && !S_ISDIR(named.st_mode)))return false;
  // A second ordinary descriptor's close would release this process's POSIX
  // record locks on the inode. O_PATH inspects identity without that effect.
  // It still requires the same no-follow metadata and live-fd checks below.
  const int probe=::open(path.c_str(),O_PATH|O_CLOEXEC|O_NOFOLLOW|
      (S_ISDIR(named.st_mode)?O_DIRECTORY:0));
  if(probe<0)return false;
  const bool matched=::fstat(probe,&opened)==0 && SameDescriptorObject(original,opened) &&
      ::fstat(descriptor,&current)==0 && SameDescriptorObject(original,current);
  const int closed=::close(probe);
  return matched && closed==0;
}
inline std::string VerifiedDescriptorLink(int descriptor,const std::string& reported)
{
  static const std::string suffix=" (deleted)";
  if(reported.size()<=suffix.size() ||
      reported.compare(reported.size()-suffix.size(),suffix.size(),suffix)!=0)return reported;
  const int savedErrno=errno;
  std::string result=reported;
  struct stat original{};
  if(::fstat(descriptor,&original)==0 && original.st_nlink>0 &&
      (S_ISREG(original.st_mode) || S_ISDIR(original.st_mode)))
  {
    // A real filename can end in this suffix. Preserve it when it names the fd.
    const auto candidate=reported.substr(0,reported.size()-suffix.size());
    if(!VerifiedDescriptorName(descriptor,original,reported) &&
        VerifiedDescriptorName(descriptor,original,candidate))result=candidate;
  }
  errno=savedErrno;
  return result;
}

inline bool VerifiedBufferNamespaceTransition(int writer,const std::string& key,
    int descriptor,const std::vector<std::string>& paths,std::string& unresolved)
{
  if(paths.size()!=1 || paths.front()!=NonPersistentTarget())return true;
  auto& state=Get();std::lock_guard<std::mutex> lock(state.mutex);
  const auto found=state.protection.buffers.find(std::to_string(writer)+":"+key);
  if(found==state.protection.buffers.end())return true;
  const int savedErrno=errno;
  struct stat actual{};
  const bool unlinked=descriptor>=0 && ::fstat(descriptor,&actual)==0 &&
      S_ISREG(actual.st_mode) && actual.st_nlink==0;
  errno=savedErrno;
  if(found->second.paths.empty()){unresolved="<unresolved>";return false;}
  for(const auto& previous:found->second.paths)
    if(previous!=NonPersistentTarget() &&
        (!unlinked || !state.protection.removedNamespaces.count(Absolute(previous))))
    {unresolved=previous;return false;}
  return true;
}
