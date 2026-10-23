#if defined(TARGET_ANDROID)
CJob::CheckpointResponsibility CGUIMultiImage::CMultiImageJob::GetCheckpointResponsibility(
    const IJobCallback* callback) const
{
  // The original callback copies a vector and changes directory-status memory.
  // A different implementation, including a derived control, is not covered.
  return typeid(*this) == typeid(CMultiImageJob) && callback &&
      typeid(*callback) == typeid(CGUIMultiImage) ?
      CheckpointResponsibility::Required : CheckpointResponsibility::Unknown;
}

bool CGUIMultiImage::CMultiImageJob::CheckpointSucceeded(bool success) const
{
  return success && m_checkpointReadOnly && typeid(*this) == typeid(CMultiImageJob);
}

bool CGUIMultiImage::CMultiImageJob::CheckpointCancelledWithoutWork() const
{
  const auto record = CJobManager::CheckpointRecord(this);
  if (typeid(*this) != typeid(CMultiImageJob) || !record || record->unknown)
    return false;
  // Called by the existing manager only for a queued job whose DoWork never
  // ran. Construction and destruction contain only strings/vectors/base state.
  JobCheckpoint::WorkResult(record, CJobDurability::VerifiedUnchanged, false);
  return true;
}

std::string CGUIMultiImage::CMultiImageJob::GetCheckpointResource() const
{
  const CURL url(m_path);
  const auto& protocol = url.GetProtocol();
  if (protocol.empty() || protocol == "special") return m_path.substr(0, 1024);
  return "multiimage-protocol:" + protocol.substr(0, 40);
}
#endif
