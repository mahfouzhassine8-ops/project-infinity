// Bounded provenance for absence evidence. Diagnostics cannot grant permission,
// manufacture removal proof, or change the native operation's result.
inline std::string NamespaceLease(const State& state, const ProtectedResource& resource)
{
  std::ostringstream out;
  out << "operation=" << resource.operation << ";writer_id=" << resource.writer
      << ";thread=" << resource.thread;
  const auto writer=state.writers.find(resource.writer);
  if(writer!=state.writers.end())
    for(const auto& invocation:writer->second.admissions)
      out << ";invocation=" << invocation.first;
  return out.str().substr(0,768);
}
inline void NamespaceEvidenceLocked(WriteProtection& protection,
                                    const std::string& path, const std::string& detail)
{
  if(protection.namespaceEvidence.size()>=65536 && !protection.namespaceEvidence.count(path))
  { ProtectionFailureLocked(protection,"namespace_evidence_inventory_exhausted");return; }
  protection.namespaceEvidence[path]=detail.substr(0,1024);
}
inline std::string NamespaceFailureEvidence(const std::string& path,int error)
{
  auto& state=Get();std::lock_guard<std::mutex> lock(state.mutex);
  std::ostringstream out;out << ";errno=" << error;
  std::string current=path;
  for(unsigned depth=0;depth<256 && out.str().size()<1400;++depth)
  {
    const auto evidence=state.protection.namespaceEvidence.find(current);
    if(evidence!=state.protection.namespaceEvidence.end())
      out << ";namespace=" << current << ";absence_verified="
          << state.protection.removedNamespaces.count(current) << ";" << evidence->second;
    const auto slash=current.rfind('/');if(slash==std::string::npos || !slash)break;
    current.resize(slash);
  }
  return out.str().substr(0,1700);
}
