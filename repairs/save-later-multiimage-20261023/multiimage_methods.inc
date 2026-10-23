#if defined(TARGET_ANDROID)
CJob::CheckpointResponsibility CGUIMultiImage::CMultiImageJob::GetCheckpointResponsibility(
    const IJobCallback* callback) const
{
  m_checkpointInfinity = XBMCAddon::xbmc::getSkinDir() == "skin.infinity.diggz";
  if (!m_checkpointInfinity) return CJob::GetCheckpointResponsibility(callback);
  // The original callback copies a vector and changes directory-status memory.
  // A different implementation, including a derived control, is not covered.
  if (typeid(*this) != typeid(CMultiImageJob) || !callback ||
      typeid(*callback) != typeid(CGUIMultiImage))
    return CheckpointResponsibility::Unknown;
  const auto* control = static_cast<const CGUIMultiImage*>(callback);
  m_checkpointControl = control->GetID();
  m_checkpointWindow = control->GetParentID();
  return CheckpointResponsibility::Required;
}

CGUIMultiImage::CMultiImageJob::~CMultiImageJob()
{
  if (!m_checkpointInfinity) return;
  try
  {
    const auto record = CJobManager::CheckpointRecord(this);
    if (!record) return;
    std::string phase, failure;
    bool unchangedReceipt = false;
    {
      std::lock_guard<std::mutex> lock(JobCheckpoint::Get().mutex);
      phase = record->phase;
      failure = record->failureDetail;
      unchangedReceipt = record->completionRecorded && record->completionCallbackVerified &&
          !record->unknown && record->durability == CJobDurability::VerifiedUnchanged &&
          phase == "completion_receipt_verified";
    }
    CLog::Log(LOGINFO, "INFINITY_MULTIIMAGE_RETIRED token={} job={} unchanged_receipt={} phase={} reason={} resource={}",
        record->token, record->jobId, unchangedReceipt, phase, failure, GetCheckpointResource());
  }
  catch (...) { } // Keep original destruction semantics if observation fails.
}

bool CGUIMultiImage::CMultiImageJob::CheckpointSucceeded(bool success) const
{
  if (!m_checkpointInfinity) return CJob::CheckpointSucceeded(success);
  return success && m_checkpointReadOnly && typeid(*this) == typeid(CMultiImageJob);
}

bool CGUIMultiImage::CMultiImageJob::CheckpointCancelledWithoutWork() const
{
  if (!m_checkpointInfinity) return CJob::CheckpointCancelledWithoutWork();
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
  if (!m_checkpointInfinity) return CJob::GetCheckpointResource();
  const CURL url(m_path);
  const auto& protocol = url.GetProtocol();
  const std::string control = "window=" + std::to_string(m_checkpointWindow) +
      ";control=" + std::to_string(m_checkpointControl) + ";";
  if (protocol.empty() || protocol == "special") return control + m_path.substr(0, 1024);
  return control + "multiimage-protocol:" + protocol.substr(0, 40);
}
#endif
