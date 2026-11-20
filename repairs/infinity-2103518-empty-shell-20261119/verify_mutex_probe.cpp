#define INFINITY_STARTUP_TRACE_HOST
#define INFINITY_PERSISTENCE_WAIT_TRACE_HOST
#include "platform/android/activity/InfinityScriptPersistence.h"

#include <cassert>
#include <chrono>
#include <cstdio>
#include <thread>

namespace Probe = InfinityPersistenceWaitTrace;
namespace Ledger = InfinityScriptPersistence;
using namespace std::chrono_literals;

int main()
{
  auto& mutex = Ledger::Get().mutex;
  errno = EINVAL;
  { Probe::Guard untouched(mutex, Probe::Site::Ledger, __LINE__); }
  assert(errno == EINVAL && Probe::nextId.load() == 2);
  InfinityStartupTrace::hostInfinity = true;

  std::atomic<unsigned> waiterTid{0};
  std::thread waiter;
  Probe::PendingWait sample{};
  const auto releasingTid = Probe::Tid();
  {
    Probe::Guard holder(mutex, Probe::Site::Ledger, __LINE__);
    const auto holderTicket = Probe::owner.id.load();
    assert(holderTicket && Probe::owner.tid.load() == releasingTid);
    waiter = std::thread([&] {
      waiterTid.store(Probe::Tid());
      Probe::Guard entry(mutex, Probe::Site::ProtectedWrite, __LINE__);
      assert(Probe::owner.tid.load() == waiterTid.load());
    });
    const auto deadline = Probe::Now() + 3000000;
    while (sample.observed == 0 && Probe::Now() < deadline)
    {
      for (const auto& slot : Probe::waits)
        if (Probe::ReadWait(slot, sample, Probe::Now()))
          break;
      std::this_thread::sleep_for(1ms);
    }
    assert(sample.observed && sample.holder.tid == releasingTid);
    assert(sample.holder.id == holderTicket && sample.holder.site == 1);
    assert(sample.waiter.tid == waiterTid.load() && sample.waiter.site == 2);
    assert(sample.holder.started <= sample.waiter.started);
    assert(sample.observed - sample.waiter.started >= Probe::SLOW_US);
  }
  waiter.join();
  assert(Probe::owner.id.load() == 0);
  for (const auto& slot : Probe::waits)
    assert(slot.id.load() == 0);

  Probe::Completion holder{}, finished{};
  for (auto& slot : Probe::completions)
  {
    if (slot.state.load(std::memory_order_acquire) != 2)
      continue;
    if (slot.record.ticket.id == sample.holder.id)
      holder = slot.record;
    if (slot.record.ticket.id == sample.waiter.id)
      finished = slot.record;
    slot.state.store(0);
  }
  assert(holder.released >= sample.observed && holder.acquired == sample.holder.started);
  assert(finished.acquired >= sample.observed && finished.released >= finished.acquired);
  assert(finished.acquired - finished.ticket.started >= Probe::SLOW_US);
  // Physical unlock precedes the release timestamp. The waiter may acquire
  // during that boundary, so no ordering is asserted across the two samples.
  assert(Probe::lostWait.load() == 0 && Probe::lostCompletion.load() == 0);

  // Collector-only control for a same-thread reentrant attempt. Never
  // attempt an actual second acquisition of the non-recursive mutex.
  {
    Probe::Guard holder(mutex, Probe::Site::Ledger, __LINE__);
    const auto started = Probe::owner.acquired.load();
    const auto contender = Probe::nextId.load() + Probe::WAIT_SLOTS;
    assert(Probe::PublishWait({contender, started, Probe::Tid(), 1, 1}));
    auto& slot = Probe::waits[contender % Probe::WAIT_SLOTS];
    Probe::PendingWait reentrant{};
    assert(Probe::ReadWait(slot, reentrant, started + Probe::SLOW_US));
    assert(reentrant.waiter.tid == reentrant.holder.tid);
    assert(reentrant.waiter.id != reentrant.holder.id);
    slot.id.store(0);
    // Reject a sample whose timestamp precedes the published acquisition.
    assert(Probe::PublishWait({contender, 1, Probe::Tid(), 1, 1}));
    assert(!Probe::ReadWait(slot, reentrant, started - 1));
    slot.id.store(0);
  }

  const auto ticket = Probe::nextId.load();
  const Probe::Ticket collision{ticket, Probe::Now(), Probe::Tid(), 1, 1};
  assert(Probe::PublishWait(collision));
  assert(!Probe::PublishWait({ticket + Probe::WAIT_SLOTS, Probe::Now(), Probe::Tid(), 1, 2}));
  assert(Probe::lostWait.load() == 1);
  assert(Probe::waits[ticket % Probe::WAIT_SLOTS].id.load() == ticket);

  for (unsigned index = 0; index <= Probe::COMPLETED_SLOTS; ++index)
    Probe::PublishCompletion(finished);
  assert(Probe::lostCompletion.load() == 1);

  errno = ERANGE;
  { Probe::Guard reused(mutex, Probe::Site::Ledger, __LINE__); }
  assert(errno == ERANGE && Probe::owner.id.load() == 0);
  std::puts("{\"result\":\"PASS\",\"owner_and_waiter_bound\":true,"
            "\"timestamps_checked\":true,\"loss_checked\":true,\"disabled_path_checked\":true}");
}
