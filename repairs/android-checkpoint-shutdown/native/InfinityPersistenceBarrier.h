#pragma once

// Standalone protocol foundation, NOT a production Kodi persistence adapter.
// Every real persistent writer must participate before this can certify an exit.
// A successful CommitResult is supplied only after that owner's checked durable
// writes have finished. This registry does not itself perform or infer disk I/O.

#include <chrono>
#include <cstdint>
#include <functional>
#include <limits>
#include <memory>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace infinity::exit_checkpoint
{
struct Session
{
  const std::string id;
  const std::int64_t pid;
  const std::string engineOwner; // Stable token assigned to this engine instance.
  const std::uint64_t attemptEpoch; // Increases on retry; never replaces engine identity.

  bool operator==(const Session& other) const
  {
    return id == other.id && pid == other.pid && engineOwner == other.engineOwner &&
           attemptEpoch == other.attemptEpoch;
  }
};

enum class Phase
{
  Idle,
  Quiesce,
  CheckpointRequested,
  Persisting,
  SafeToTerminate,
  EngineTerminating,
  Complete,
  CheckpointFailed
};

enum class InitialState { Unknown, AuthoritativelyClean, Dirty };
enum class CommitResult { DurablyCommitted, Failed };

class PersistenceBarrier
{
public:
  using Clock = std::chrono::steady_clock;
  using Now = std::function<Clock::time_point()>;

private:
  struct Owner
  {
    bool registered = false;
    bool known = false;
    bool dirty = true;
    std::uint64_t generation = 0;
    std::size_t writers = 0;
    std::size_t commits = 0;
  };

  struct State
  {
    std::mutex mutex;
    std::shared_ptr<const Session> session;
    Phase phase = Phase::Idle;
    std::unordered_map<std::string, Owner> owners;
    std::string failure;
    Clock::time_point deadline = Clock::time_point::max();
    Now now;

    bool matches(const Session& candidate) const { return *session == candidate; }
    bool checkpointOpen() const
    {
      return phase == Phase::CheckpointRequested || phase == Phase::Persisting;
    }
    void fail(std::string reason)
    {
      phase = Phase::CheckpointFailed;
      failure = std::move(reason);
    }
    bool checkDeadline()
    {
      if ((phase == Phase::Quiesce || checkpointOpen() || phase == Phase::SafeToTerminate) &&
          now() >= deadline)
        fail("checkpoint deadline exceeded");
      return phase != Phase::CheckpointFailed;
    }
  };

public:
  // A token is the lifetime of an actual mutation, including asynchronous work.
  // It must not be released at enqueue time while a queued write can still run.
  // Destruction releases admission accounting but NEVER declares data clean.
  class WriteToken
  {
  public:
    WriteToken(const WriteToken&) = delete;
    WriteToken& operator=(const WriteToken&) = delete;
    WriteToken(WriteToken&& other) noexcept
      : state_(std::move(other.state_)), owner_(std::move(other.owner_)),
        session_(std::move(other.session_)), generation_(other.generation_) {}
    WriteToken& operator=(WriteToken&&) = delete;
    ~WriteToken() { finish(); }
    void finish()
    {
      auto state = std::move(state_);
      if (!state)
        return;
      std::lock_guard<std::mutex> lock(state->mutex);
      --state->owners.at(owner_).writers;
    }
    std::uint64_t generation() const { return generation_; }
    const Session& session() const { return *session_; }

  private:
    friend class PersistenceBarrier;
    WriteToken(std::shared_ptr<State> state, std::string owner,
               std::shared_ptr<const Session> session, std::uint64_t generation)
      : state_(std::move(state)), owner_(std::move(owner)),
        session_(std::move(session)), generation_(generation) {}
    std::shared_ptr<State> state_;
    std::string owner_;
    std::shared_ptr<const Session> session_;
    std::uint64_t generation_;
  };

  // This capability is explicitly issued to the checkpoint coordinator; normal
  // playback/providers/services must only use beginWrite(). It is invalidated on
  // failure, retry, or SAFE. It is not a substitute for a real ownership audit.
  class CheckpointAuthority
  {
  public:
    const Session& session() const { return *session_; }
  private:
    friend class PersistenceBarrier;
    CheckpointAuthority(std::shared_ptr<State> state, std::shared_ptr<const Session> session)
      : state_(std::move(state)), session_(std::move(session)) {}
    std::shared_ptr<State> state_;
    std::shared_ptr<const Session> session_;
  };

  // Outstanding disk commits are counted independently from state mutations.
  // Dropping a current ticket without completing it fails the checkpoint. Old
  // tickets still drain their counts after retry, but cannot clean a new attempt.
  class CommitTicket
  {
  public:
    CommitTicket(const CommitTicket&) = delete;
    CommitTicket& operator=(const CommitTicket&) = delete;
    CommitTicket(CommitTicket&& other) noexcept
      : state_(std::move(other.state_)), owner_(std::move(other.owner_)),
        session_(std::move(other.session_)), generation_(other.generation_) {}
    CommitTicket& operator=(CommitTicket&&) = delete;
    ~CommitTicket() { complete(CommitResult::Failed); }

    // True means this exact generation was durably committed for this attempt.
    // A late checkpoint writer makes an otherwise successful I/O result stale.
    bool complete(CommitResult result)
    {
      auto state = std::move(state_);
      if (!state)
        return false;
      std::lock_guard<std::mutex> lock(state->mutex);
      auto& owner = state->owners.at(owner_);
      --owner.commits;
      state->checkDeadline();
      if (!state->matches(*session_) || state->phase != Phase::Persisting)
        return false;
      if (result == CommitResult::Failed)
      {
        owner.dirty = true;
        state->fail("owner commit failed: " + owner_);
        return false;
      }
      if (owner.generation != generation_ || owner.writers != 0 || owner.commits != 0)
        return false;
      owner.dirty = false;
      return true;
    }
    std::uint64_t generation() const { return generation_; }
    const Session& session() const { return *session_; }

  private:
    friend class PersistenceBarrier;
    CommitTicket(std::shared_ptr<State> state, std::string owner,
                 std::shared_ptr<const Session> session, std::uint64_t generation)
      : state_(std::move(state)), owner_(std::move(owner)),
        session_(std::move(session)), generation_(generation) {}
    std::shared_ptr<State> state_;
    std::string owner_;
    std::shared_ptr<const Session> session_;
    std::uint64_t generation_;
  };

  struct OwnerSnapshot
  {
    std::string id;
    bool registered;
    bool authoritativeStateKnown;
    bool dirty;
    std::uint64_t generation;
    std::size_t inFlightWriters;
    std::size_t inFlightCommits;
  };
  struct Snapshot
  {
    std::shared_ptr<const Session> session;
    Phase phase;
    std::string failure;
    std::vector<OwnerSnapshot> owners;
  };

  PersistenceBarrier(Session session, const std::vector<std::string>& requiredOwners,
                     Now now = [] { return Clock::now(); }) : state_(std::make_shared<State>())
  {
    if (session.id.empty() || session.pid <= 0 || session.engineOwner.empty() ||
        session.attemptEpoch == 0 ||
        requiredOwners.empty() || !now)
      throw std::invalid_argument("session, clock and explicit required-owner manifest required");
    state_->session = std::make_shared<const Session>(std::move(session));
    state_->now = std::move(now);
    for (const auto& owner : requiredOwners)
      if (owner.empty() || !state_->owners.emplace(owner, Owner{}).second)
        throw std::invalid_argument("invalid or duplicate required owner");
  }
  PersistenceBarrier(const PersistenceBarrier&) = delete;
  PersistenceBarrier& operator=(const PersistenceBarrier&) = delete;

  bool registerOwner(const Session& session, const std::string& id, InitialState initial)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    auto found = state_->owners.find(id);
    if (!state_->matches(session) || state_->phase != Phase::Idle ||
        found == state_->owners.end() || found->second.registered)
      return false;
    found->second.registered = true;
    found->second.known = initial != InitialState::Unknown;
    found->second.dirty = initial != InitialState::AuthoritativelyClean;
    return true;
  }

  std::optional<WriteToken> beginWrite(const Session& session, const std::string& id)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    if (!state_->matches(session) || state_->phase != Phase::Idle)
      return std::nullopt;
    return admitWriteLocked(id);
  }

  bool quiesce(const Session& session, Clock::time_point deadline)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    if (!state_->matches(session) || state_->phase != Phase::Idle)
      return false;
    state_->phase = Phase::Quiesce; // The admission fence closes under this same mutex.
    state_->deadline = deadline;
    for (const auto& [id, owner] : state_->owners)
      if (!owner.registered || !owner.known)
      {
        state_->fail("required owner missing or state unknown: " + id);
        return false;
      }
    if (!state_->checkDeadline())
      return false;
    state_->phase = Phase::CheckpointRequested;
    return true;
  }

  std::optional<CheckpointAuthority> startPersistence(const Session& session)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    state_->checkDeadline();
    if (!state_->matches(session) || state_->phase != Phase::CheckpointRequested)
      return std::nullopt;
    state_->phase = Phase::Persisting;
    return CheckpointAuthority(state_, state_->session);
  }

  std::optional<WriteToken> beginCheckpointWrite(const CheckpointAuthority& authority,
                                                const std::string& id)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    state_->checkDeadline();
    if (authority.state_ != state_ || !state_->matches(*authority.session_) ||
        state_->phase != Phase::Persisting)
      return std::nullopt;
    return admitWriteLocked(id);
  }

  std::optional<CommitTicket> beginCommit(const CheckpointAuthority& authority,
                                         const std::string& id)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    state_->checkDeadline();
    auto found = state_->owners.find(id);
    if (authority.state_ != state_ || !state_->matches(*authority.session_) ||
        state_->phase != Phase::Persisting || found == state_->owners.end())
      return std::nullopt;
    auto& owner = found->second;
    if (!owner.registered || !owner.known || !owner.dirty || owner.writers || owner.commits)
      return std::nullopt;
    ++owner.commits;
    return CommitTicket(state_, id, state_->session, owner.generation);
  }

  bool tryMarkSafe(const Session& session)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    state_->checkDeadline();
    if (!state_->matches(session) || state_->phase != Phase::Persisting)
      return false;
    for (const auto& [id, owner] : state_->owners)
      if (!owner.registered || !owner.known || owner.dirty || owner.writers || owner.commits)
        return false;
    state_->phase = Phase::SafeToTerminate;
    return true;
  }

  bool failCheckpoint(const Session& session, const std::string& reason)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    if (!state_->matches(session) ||
        (!state_->checkpointOpen() && state_->phase != Phase::SafeToTerminate))
      return false;
    state_->fail(reason.empty() ? "checkpoint failed" : reason);
    return true;
  }

  // Retry preserves the CLOSED fence and every outstanding mutation/commit.
  // Never construct a fresh independent barrier to retry in the same process.
  bool retry(const Session& oldSession, Session next, Clock::time_point deadline)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    if (!state_->matches(oldSession) || state_->phase != Phase::CheckpointFailed ||
        next.pid != oldSession.pid || next.engineOwner != oldSession.engineOwner ||
        next.attemptEpoch <= oldSession.attemptEpoch ||
        next.id.empty() || next.id == oldSession.id)
      return false;
    for (const auto& [id, owner] : state_->owners)
      if (!owner.registered || !owner.known)
        return false; // An incomplete ownership audit cannot be repaired by retry.
    state_->session = std::make_shared<const Session>(std::move(next));
    state_->deadline = deadline;
    state_->failure.clear();
    state_->phase = Phase::CheckpointRequested;
    return state_->checkDeadline();
  }

  // A matching session token and SAFE phase are both mandatory. Neither an
  // Android lifecycle callback nor timeout can manufacture this transition.
  bool markEngineTerminating(const Session& session)
  {
    return advance(session, Phase::SafeToTerminate, Phase::EngineTerminating);
  }
  bool markComplete(const Session& session)
  {
    return advance(session, Phase::EngineTerminating, Phase::Complete);
  }
  Snapshot snapshot()
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    state_->checkDeadline(); // No hidden worker or blocking timeout thread.
    Snapshot result{state_->session, state_->phase, state_->failure, {}};
    for (const auto& [id, owner] : state_->owners)
      result.owners.push_back({id, owner.registered, owner.known, owner.dirty,
                              owner.generation, owner.writers, owner.commits});
    return result;
  }

private:
  std::optional<WriteToken> admitWriteLocked(const std::string& id)
  {
    auto found = state_->owners.find(id);
    if (found == state_->owners.end() || !found->second.registered || !found->second.known)
      return std::nullopt;
    auto& owner = found->second;
    if (owner.generation == std::numeric_limits<std::uint64_t>::max())
    {
      state_->fail("dirty generation exhausted: " + id);
      return std::nullopt;
    }
    ++owner.generation;
    ++owner.writers;
    owner.dirty = true;
    return WriteToken(state_, id, state_->session, owner.generation);
  }
  bool advance(const Session& session, Phase from, Phase to)
  {
    std::lock_guard<std::mutex> lock(state_->mutex);
    state_->checkDeadline(); // Revalidate SAFE at the final termination authorization gate.
    if (!state_->matches(session) || state_->phase != from)
      return false;
    state_->phase = to;
    return true;
  }
  const std::shared_ptr<State> state_;
};
} // namespace infinity::exit_checkpoint
