#pragma once

#include <cstdint>
#include <string>

class CApplication;

namespace InfinityAndroidCheckpoint
{
// Android's default-process guard is the sole shutdown coordinator. This native
// participant never destroys the Activity, stops Kodi, or terminates a process.
bool RegisterStartupOwner(const std::string& owner, int pid, const std::string& filesDirectory);
bool PublishStartupOwner();
bool Request(const std::string& session, const std::string& owner, int pid);
std::string Status(const std::string& session, const std::string& owner, int pid);
bool AuthorizeTermination(const std::string& session, const std::string& owner, int pid);
void NotifyLegacyTeardown(const char* operation);
void Pump(CApplication& application);
bool IsActive();
bool IsRequiredOwner(const std::string& owner);
bool IsPersistingOnThisThread();
bool IsAcceptedPlaybackWorkOnThisThread();
bool AllowNativeWrite(const char* owner);
void RecordPersistenceFailure(const char* owner, const char* detail);
inline void RecordFailure(const char* owner, const char* detail)
{
  RecordPersistenceFailure(owner, detail);
}
std::uint64_t ErrorGeneration();
bool HasFailureSince(std::uint64_t generation);
bool CheckpointLoadedAddonSettings();
bool CheckpointSkinSettings();
bool CheckpointAudioPolicyFile();
bool CheckpointDeferredDialogState();
bool CheckpointPendingSettingsDialogs();
bool CheckpointPendingGameDialogs();
void MarkAddonSettingsManagerDirty(const void* manager);
std::string ClassifyScript(const std::string& script, const std::string& addon);

class CheckpointWriteGuard
{
public:
  explicit CheckpointWriteGuard(const char* owner);
  ~CheckpointWriteGuard();
  CheckpointWriteGuard(const CheckpointWriteGuard&) = delete;
  CheckpointWriteGuard& operator=(const CheckpointWriteGuard&) = delete;
  explicit operator bool() const { return m_admitted; }
private:
  bool m_admitted{false};
};

class CoordinatorWriteScope
{
public:
  CoordinatorWriteScope();
  ~CoordinatorWriteScope();
  CoordinatorWriteScope(const CoordinatorWriteScope&) = delete;
  CoordinatorWriteScope& operator=(const CoordinatorWriteScope&) = delete;
};

// For the decoder's already-admitted command/close callbacks only. It preserves
// their outbound persistence jobs during QUIESCE and never reopens a sealed exit.
class AcceptedPlaybackWorkScope
{
public:
  AcceptedPlaybackWorkScope();
  ~AcceptedPlaybackWorkScope();
  AcceptedPlaybackWorkScope(const AcceptedPlaybackWorkScope&) = delete;
  AcceptedPlaybackWorkScope& operator=(const AcceptedPlaybackWorkScope&) = delete;
private:
  bool m_counted{false};
};
} // namespace InfinityAndroidCheckpoint
