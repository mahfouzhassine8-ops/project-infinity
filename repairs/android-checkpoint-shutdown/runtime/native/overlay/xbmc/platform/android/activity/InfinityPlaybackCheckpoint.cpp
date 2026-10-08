#include "InfinityPlaybackCheckpoint.h"

#include "InfinityAndroidCheckpoint.h"
#include "application/ApplicationPlayer.h"
#include "application/ApplicationPlayerCallback.h"

namespace InfinityPlaybackCheckpoint
{
PollResult Poll(CApplicationPlayer& player, CApplicationPlayerCallback& callback,
                const std::string& session, std::string& failure)
{
  // Application-thread owner only. A failed save is never retried implicitly:
  // watched/playcount commits may have partially succeeded before a later error.
  struct Transaction
  {
    std::shared_ptr<Request> request;
    std::uint64_t errorGeneration{0};
    bool attempted{false};
    bool complete{false};
    std::string error;
  };
  static Transaction transaction;
  if (!InfinityAndroidCheckpoint::IsActive() || session.empty())
  {
    failure = "playback checkpoint has no active Android transaction";
    return PollResult::Failed;
  }
  if (!transaction.request)
  {
    transaction.request = std::make_shared<Request>(session);
    transaction.errorGeneration = InfinityAndroidCheckpoint::ErrorGeneration();
    if (!player.RequestInfinityCheckpoint(transaction.request))
      transaction.error = "active player backend has no audited persistence freeze";
  }
  if (transaction.request->session != session)
  {
    failure = "playback checkpoint cannot replay a different transaction in the same engine";
    return PollResult::Failed;
  }
  if (!transaction.error.empty())
  {
    failure = transaction.error;
    return PollResult::Failed;
  }
  if (transaction.complete)
    return PollResult::Complete;

  Snapshot snapshot;
  {
    std::lock_guard<std::mutex> lock(transaction.request->mutex);
    if (!transaction.request->failure.empty())
    {
      transaction.error = transaction.request->failure;
      failure = transaction.error;
      return PollResult::Failed;
    }
    if (!transaction.request->frozen)
      return PollResult::Pending;
    snapshot = transaction.request->snapshot;
  }
  if (!player.InfinityCheckpointCallbacksDrained())
    return PollResult::Pending;
  if (InfinityAndroidCheckpoint::HasFailureSince(transaction.errorGeneration))
  {
    transaction.error = "an accepted playback callback failed before snapshot persistence";
    failure = transaction.error;
    return PollResult::Failed;
  }
  if (transaction.attempted)
  {
    failure = "playback persistence did not complete; replay is prohibited";
    return PollResult::Failed;
  }
  transaction.attempted = true;
  bool saved = !snapshot.hasPlayback;
  try
  {
    if (snapshot.hasPlayback)
    {
      // The queue has drained and the decoder cannot generate a later close-file
      // callback, so the watched increment and final bookmark occur only once.
      saved = callback.CheckpointPlayerState(snapshot.item, snapshot.bookmark);
      if (snapshot.item.IsVideo())
        saved = callback.CheckpointVideoSettings(snapshot.item, snapshot.videoSettings) && saved;
    }
  }
  catch (...)
  {
    saved = false;
  }
  if (!saved || InfinityAndroidCheckpoint::HasFailureSince(transaction.errorGeneration))
  {
    transaction.error = "final playback state/settings commit or readback failed";
    InfinityAndroidCheckpoint::RecordPersistenceFailure("playback", transaction.error.c_str());
    failure = transaction.error;
    return PollResult::Failed;
  }
  transaction.complete = true;
  return PollResult::Complete;
}
} // namespace InfinityPlaybackCheckpoint
