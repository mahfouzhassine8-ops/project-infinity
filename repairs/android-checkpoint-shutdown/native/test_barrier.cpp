#include "InfinityPersistenceBarrier.h"

#include <atomic>
#include <cstdlib>
#include <future>
#include <iostream>
#include <thread>

using namespace infinity::exit_checkpoint;
using Barrier = PersistenceBarrier;
using Clock = Barrier::Clock;

#define CHECK(expression) do { if (!(expression)) { \
  std::cerr << __func__ << ':' << __LINE__ << " failed: " #expression "\n"; \
  std::abort(); }} while (false)

static Clock::time_point deadline() { return Clock::now() + std::chrono::seconds(30); }
static Session first() { return {"attempt-1", 4321, "engine-instance-1", 1}; }

static void required_manifest_and_authoritative_clean()
{
  auto session = first();
  Barrier missing(session, {"settings", "resume"});
  CHECK(missing.registerOwner(session, "settings", InitialState::AuthoritativelyClean));
  CHECK(!missing.registerOwner(session, "not-in-manifest", InitialState::AuthoritativelyClean));
  CHECK(!missing.quiesce(session, deadline()));
  CHECK(missing.snapshot().phase == Phase::CheckpointFailed);
  CHECK(!missing.beginWrite(session, "settings"));
  CHECK(!missing.tryMarkSafe(session));

  Barrier unknown(session, {"settings"});
  CHECK(unknown.registerOwner(session, "settings", InitialState::Unknown));
  CHECK(!unknown.beginWrite(session, "settings"));
  CHECK(!unknown.quiesce(session, deadline()));
  CHECK(!unknown.retry(session, {"attempt-2", 4321, "engine-instance-1", 2}, deadline()));

  Barrier clean(session, {"settings", "resume"});
  CHECK(clean.registerOwner(session, "settings", InitialState::AuthoritativelyClean));
  CHECK(clean.registerOwner(session, "resume", InitialState::AuthoritativelyClean));
  CHECK(!clean.markEngineTerminating(session));
  CHECK(clean.quiesce(session, deadline()));
  auto authority = clean.startPersistence(session);
  CHECK(authority);
  CHECK(!clean.beginCommit(*authority, "settings")); // No unnecessary clean-state save.
  CHECK(clean.tryMarkSafe(session));
  CHECK(!clean.beginWrite(session, "settings"));
  CHECK(!clean.beginCheckpointWrite(*authority, "settings"));
  CHECK(clean.markEngineTerminating(session));
  CHECK(!clean.beginCheckpointWrite(*authority, "resume"));
  CHECK(clean.markComplete(session));
  CHECK(!clean.beginWrite(session, "settings"));
}

static void active_writer_blocks_and_checkpoint_capability()
{
  auto session = first();
  Barrier barrier(session, {"settings", "resume"});
  CHECK(barrier.registerOwner(session, "settings", InitialState::AuthoritativelyClean));
  CHECK(barrier.registerOwner(session, "resume", InitialState::Dirty));
  auto writer = barrier.beginWrite(session, "settings");
  CHECK(writer && writer->generation() == 1);
  CHECK(barrier.quiesce(session, deadline()));
  auto authority = barrier.startPersistence(session);
  CHECK(authority);
  CHECK(!barrier.beginWrite(session, "resume"));
  CHECK(!barrier.beginCommit(*authority, "settings"));
  CHECK(!barrier.tryMarkSafe(session));
  writer.reset();
  auto settingsCommit = barrier.beginCommit(*authority, "settings");
  CHECK(settingsCommit);
  CHECK(!barrier.tryMarkSafe(session));
  CHECK(settingsCommit->complete(CommitResult::DurablyCommitted));
  CHECK(!barrier.tryMarkSafe(session)); // A second dirty owner still blocks global SAFE.
  auto resumeWriter = barrier.beginCheckpointWrite(*authority, "resume");
  CHECK(resumeWriter);
  resumeWriter.reset();
  auto resumeCommit = barrier.beginCommit(*authority, "resume");
  CHECK(resumeCommit && resumeCommit->generation() == 1);
  CHECK(resumeCommit->complete(CommitResult::DurablyCommitted));
  CHECK(!resumeCommit->complete(CommitResult::DurablyCommitted));
  CHECK(barrier.tryMarkSafe(session));
}

static void late_checkpoint_write_invalidates_commit()
{
  auto session = first();
  Barrier barrier(session, {"resume"});
  CHECK(barrier.registerOwner(session, "resume", InitialState::Dirty));
  CHECK(barrier.quiesce(session, deadline()));
  auto authority = barrier.startPersistence(session);
  auto oldCommit = barrier.beginCommit(*authority, "resume");
  CHECK(oldCommit);
  std::promise<void> admitted;
  std::promise<void> release;
  auto releaseFuture = release.get_future();
  std::thread writer([&] {
    auto token = barrier.beginCheckpointWrite(*authority, "resume");
    CHECK(token);
    admitted.set_value();
    releaseFuture.wait();
  });
  admitted.get_future().wait();
  CHECK(!oldCommit->complete(CommitResult::DurablyCommitted));
  CHECK(!barrier.tryMarkSafe(session));
  CHECK(!barrier.beginCommit(*authority, "resume"));
  release.set_value();
  writer.join();
  auto newCommit = barrier.beginCommit(*authority, "resume");
  CHECK(newCommit && newCommit->generation() == 1);
  CHECK(newCommit->complete(CommitResult::DurablyCommitted));
  CHECK(barrier.tryMarkSafe(session));
}

static void drained_late_write_still_invalidates_generation()
{
  auto session = first();
  Barrier barrier(session, {"settings"});
  CHECK(barrier.registerOwner(session, "settings", InitialState::Dirty));
  CHECK(barrier.quiesce(session, deadline()));
  auto authority = barrier.startPersistence(session);
  auto commit = barrier.beginCommit(*authority, "settings");
  auto token = barrier.beginCheckpointWrite(*authority, "settings");
  CHECK(token);
  token.reset();
  CHECK(!commit->complete(CommitResult::DurablyCommitted));
  CHECK(!barrier.tryMarkSafe(session));
  auto latest = barrier.beginCommit(*authority, "settings");
  CHECK(latest->complete(CommitResult::DurablyCommitted));
  CHECK(barrier.tryMarkSafe(session));
}

static void failed_and_abandoned_commit_stay_fenced()
{
  auto session = first();
  for (bool explicitlyFail : {false, true})
  {
    Barrier barrier(session, {"settings"});
    CHECK(barrier.registerOwner(session, "settings", InitialState::Dirty));
    CHECK(barrier.quiesce(session, deadline()));
    auto authority = barrier.startPersistence(session);
    auto commit = barrier.beginCommit(*authority, "settings");
    CHECK(commit);
    if (explicitlyFail)
      CHECK(!commit->complete(CommitResult::Failed));
    else
      commit.reset();
    CHECK(barrier.snapshot().phase == Phase::CheckpointFailed);
    CHECK(!barrier.tryMarkSafe(session));
    CHECK(!barrier.beginWrite(session, "settings"));
    CHECK(!barrier.beginCheckpointWrite(*authority, "settings"));
    CHECK(!barrier.markEngineTerminating(session));
  }
}

static void deadline_is_failure_never_permission_to_kill()
{
  auto session = first();
  std::atomic<int> ticks{0};
  const auto epoch = Clock::time_point{};
  Barrier barrier(session, {"settings"}, [&] { return epoch + std::chrono::milliseconds(ticks.load()); });
  CHECK(barrier.registerOwner(session, "settings", InitialState::Dirty));
  CHECK(barrier.quiesce(session, epoch + std::chrono::milliseconds(100)));
  auto authority = barrier.startPersistence(session);
  auto commit = barrier.beginCommit(*authority, "settings");
  ticks.store(100);
  CHECK(!commit->complete(CommitResult::DurablyCommitted));
  CHECK(barrier.snapshot().phase == Phase::CheckpointFailed);
  CHECK(!barrier.tryMarkSafe(session));
  CHECK(!barrier.markEngineTerminating(session));
  CHECK(!barrier.beginCheckpointWrite(*authority, "settings"));
}

static void retry_rejects_old_commit_and_authority()
{
  auto old = first();
  Session next{"attempt-2", 4321, "engine-instance-1", 2};
  Barrier barrier(old, {"resume"});
  CHECK(barrier.registerOwner(old, "resume", InitialState::Dirty));
  CHECK(barrier.quiesce(old, deadline()));
  auto oldAuthority = barrier.startPersistence(old);
  auto oldCommit = barrier.beginCommit(*oldAuthority, "resume");
  CHECK(barrier.failCheckpoint(old, "owner callback timed out"));
  CHECK(!barrier.retry(old, {"attempt-2", 9999, "engine-instance-1", 2}, deadline()));
  CHECK(!barrier.retry(old, {"attempt-2", 4321, "engine-instance-2", 2}, deadline()));
  CHECK(!barrier.retry(old, {"attempt-2", 4321, "engine-instance-1", 1}, deadline()));
  CHECK(!barrier.retry(old, {"attempt-1", 4321, "engine-instance-1", 2}, deadline()));
  CHECK(barrier.retry(old, next, deadline()));
  auto authority = barrier.startPersistence(next);
  CHECK(authority);
  CHECK(!barrier.beginWrite(next, "resume")); // Retry cannot reopen ordinary writes.
  CHECK(!barrier.beginCheckpointWrite(*oldAuthority, "resume"));
  CHECK(!barrier.beginCommit(*authority, "resume")); // Old I/O still owns its count.
  CHECK(!barrier.tryMarkSafe(next));
  CHECK(!oldCommit->complete(CommitResult::DurablyCommitted));
  CHECK(!barrier.tryMarkSafe(next)); // A stale ACK never makes current data clean.
  auto commit = barrier.beginCommit(*authority, "resume");
  CHECK(commit && commit->complete(CommitResult::DurablyCommitted));
  CHECK(!barrier.tryMarkSafe(old));
  CHECK(barrier.tryMarkSafe(next));
  CHECK(!barrier.markEngineTerminating(old));
  CHECK(barrier.markEngineTerminating(next));
}

static void retry_preserves_old_active_writer()
{
  auto old = first();
  Session next{"attempt-2", 4321, "engine-instance-1", 2};
  Barrier barrier(old, {"settings"});
  CHECK(barrier.registerOwner(old, "settings", InitialState::AuthoritativelyClean));
  std::promise<void> admitted;
  std::promise<void> release;
  auto releaseFuture = release.get_future();
  std::thread writer([&] {
    auto token = barrier.beginWrite(old, "settings");
    CHECK(token);
    admitted.set_value();
    releaseFuture.wait();
  });
  admitted.get_future().wait();
  CHECK(barrier.quiesce(old, deadline()));
  CHECK(barrier.failCheckpoint(old, "write did not finish"));
  CHECK(barrier.retry(old, next, deadline()));
  auto authority = barrier.startPersistence(next);
  CHECK(!barrier.beginWrite(old, "settings"));
  CHECK(!barrier.beginWrite(next, "settings"));
  CHECK(!barrier.beginCommit(*authority, "settings"));
  CHECK(!barrier.tryMarkSafe(next));
  release.set_value();
  writer.join();
  auto commit = barrier.beginCommit(*authority, "settings");
  CHECK(commit && commit->complete(CommitResult::DurablyCommitted));
  CHECK(barrier.tryMarkSafe(next));
}

static void mutation_admission_races_quiesce()
{
  // Either the writer enters before the fence and blocks SAFE, or the fence wins
  // and the writer receives no token. There is no untracked success outcome.
  for (int iteration = 0; iteration < 200; ++iteration)
  {
    auto session = first();
    Barrier barrier(session, {"resume"});
    CHECK(barrier.registerOwner(session, "resume", InitialState::AuthoritativelyClean));
    std::promise<void> start;
    auto startFuture = start.get_future().share();
    std::promise<bool> admitted;
    std::promise<void> release;
    auto releaseFuture = release.get_future();
    std::thread writer([&] {
      startFuture.wait();
      auto token = barrier.beginWrite(session, "resume");
      admitted.set_value(token.has_value());
      releaseFuture.wait();
    });
    std::thread closer([&] {
      startFuture.wait();
      CHECK(barrier.quiesce(session, deadline()));
    });
    start.set_value();
    closer.join();
    bool writerWon = admitted.get_future().get();
    auto authority = barrier.startPersistence(session);
    CHECK(authority);
    CHECK(!barrier.beginWrite(session, "resume"));
    CHECK(barrier.tryMarkSafe(session) == !writerWon);
    release.set_value();
    writer.join();
    if (writerWon)
    {
      auto commit = barrier.beginCommit(*authority, "resume");
      CHECK(commit && commit->complete(CommitResult::DurablyCommitted));
      CHECK(barrier.tryMarkSafe(session));
    }
  }
}

static void foreign_barrier_authority_is_rejected()
{
  auto session = first();
  Barrier a(session, {"settings"});
  Barrier b(session, {"settings"});
  for (auto* barrier : {&a, &b})
  {
    CHECK(barrier->registerOwner(session, "settings", InitialState::Dirty));
    CHECK(barrier->quiesce(session, deadline()));
  }
  auto authority = a.startPersistence(session);
  auto bAuthority = b.startPersistence(session);
  CHECK(!b.beginCheckpointWrite(*authority, "settings"));
  CHECK(!b.beginCommit(*authority, "settings"));
  CHECK(!a.beginCheckpointWrite(*bAuthority, "settings"));
}

static void safe_can_be_revoked_before_termination()
{
  auto session = first();
  Barrier barrier(session, {"settings"});
  CHECK(barrier.registerOwner(session, "settings", InitialState::AuthoritativelyClean));
  CHECK(barrier.quiesce(session, deadline()));
  auto authority = barrier.startPersistence(session);
  CHECK(authority && barrier.tryMarkSafe(session));
  CHECK(barrier.failCheckpoint(session, "coordinator receipt write failed"));
  CHECK(barrier.snapshot().phase == Phase::CheckpointFailed);
  CHECK(!barrier.markEngineTerminating(session));
  CHECK(!barrier.beginWrite(session, "settings"));
  CHECK(!barrier.beginCheckpointWrite(*authority, "settings"));
  Session next{"attempt-2", 4321, "engine-instance-1", 2};
  CHECK(barrier.retry(session, next, deadline()));
  auto nextAuthority = barrier.startPersistence(next);
  CHECK(nextAuthority && barrier.tryMarkSafe(next));
  CHECK(!barrier.markEngineTerminating(session));
  CHECK(barrier.markEngineTerminating(next));
}

static void expired_safe_cannot_authorize_termination()
{
  auto session = first();
  std::atomic<int> ticks{0};
  const auto epoch = Clock::time_point{};
  Barrier barrier(session, {"settings"}, [&] { return epoch + std::chrono::milliseconds(ticks.load()); });
  CHECK(barrier.registerOwner(session, "settings", InitialState::AuthoritativelyClean));
  CHECK(barrier.quiesce(session, epoch + std::chrono::milliseconds(100)));
  auto authority = barrier.startPersistence(session);
  CHECK(authority && barrier.tryMarkSafe(session));
  ticks.store(100);
  // This gate must itself check expiration; no preceding snapshot or poll helps it.
  CHECK(!barrier.markEngineTerminating(session));
  CHECK(barrier.snapshot().phase == Phase::CheckpointFailed);
  CHECK(!barrier.markComplete(session));
  CHECK(!barrier.beginWrite(session, "settings"));
  CHECK(!barrier.beginCheckpointWrite(*authority, "settings"));
}

int main()
{
  required_manifest_and_authoritative_clean();
  active_writer_blocks_and_checkpoint_capability();
  late_checkpoint_write_invalidates_commit();
  drained_late_write_still_invalidates_generation();
  failed_and_abandoned_commit_stay_fenced();
  deadline_is_failure_never_permission_to_kill();
  retry_rejects_old_commit_and_authority();
  retry_preserves_old_active_writer();
  mutation_admission_races_quiesce();
  foreign_barrier_authority_is_rejected();
  safe_can_be_revoked_before_termination();
  expired_safe_cannot_authorize_termination();
  std::cout << "PASS: 12 barrier scenarios, including 200 admission races\n";
}
