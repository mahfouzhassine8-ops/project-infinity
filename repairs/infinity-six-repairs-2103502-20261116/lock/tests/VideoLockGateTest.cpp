#include "InfinityVideoLockGate.h"
#include <cstdlib>
#include <iostream>
#include <thread>

using InfinityVideoLock::Gate;
static unsigned checks = 0;
static void require(bool value)
{
  ++checks;
  if (!value) { std::cerr << "FAIL gate assertion " << checks << '\n'; std::exit(1); }
}

int main()
{
  Gate gate;
  require(!gate.Begin(0));
  require(!gate.Begin(Gate::MAX_SESSION + 1));
  require(!gate.Begin(1, 0));
  require(!gate.Begin(1, Gate::MAX_GENERATION + 1));
  require(gate.Begin(1));
  require(!gate.Begin(2));
  require(!gate.Commit(1, gate.Value())); // Readiness is never an unlock grant.
  auto first = gate.Advance(1, true);
  require(first && (first & 1));
  require(!gate.Commit(2, first));
  require(gate.Value() == first);
  require(gate.Advance(1, false) != 0); // Rotation revokes the pending grant.
  require(!gate.Commit(1, first));
  auto retry = gate.Advance(1, true);
  require(retry && retry != first);
  require(!gate.Commit(1, first));
  require(gate.Commit(1, retry));
  require(!gate.Value());
  require(!gate.Advance(1, false)); // A late revoke cannot re-lock a committed session.
  require(!gate.Commit(1, retry));
  require(gate.Begin(2));
  require(!gate.Commit(1, retry));
  require(!gate.Retire(1));
  require(Gate::Session(gate.Value()) == 2);
  require(gate.Retire(2));
  require(!gate.Value());

  // Explicit exhaustion keeps a barrier and invalidates the final grant; it never wraps.
  require(gate.Begin(Gate::MAX_SESSION, Gate::MAX_GENERATION - 1));
  auto last = gate.Advance(Gate::MAX_SESSION, true);
  require(last && (last & 1));
  require(!gate.Advance(Gate::MAX_SESSION, false));
  require(gate.Value() && !(gate.Value() & 1));
  require(!gate.Commit(Gate::MAX_SESSION, last));
  require(gate.Retire(Gate::MAX_SESSION));

  // Adversarial publication versus commit: either the commit wins before revoke,
  // or the newer barrier survives. A stale grant must never clear that barrier.
  for (unsigned n = 0; n != 128; ++n)
  {
    Gate raced;
    require(raced.Begin(n + 1));
    auto grant = raced.Advance(n + 1, true);
    std::atomic<unsigned> ready{0};
    std::atomic<bool> go{false};
    bool committed = false;
    Gate::Word revoked = 0;
    std::thread a([&] { ++ready; while (!go.load()) std::this_thread::yield(); committed = raced.Commit(n + 1, grant); });
    std::thread b([&] { ++ready; while (!go.load()) std::this_thread::yield(); revoked = raced.Advance(n + 1, false); });
    while (ready.load() != 2) std::this_thread::yield();
    go.store(true);
    a.join(); b.join();
    require(committed ? (!revoked && !raced.Value()) : (revoked && raced.Value() == revoked));
    require(!raced.Commit(n + 1, grant));
  }
  std::cout << "PASS VideoLockGateTest " << checks << " assertions\n";
}
