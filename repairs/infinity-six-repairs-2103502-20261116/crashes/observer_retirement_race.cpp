#include "InfinityActivityObserver.h"
#include <atomic>
#include <chrono>
#include <iostream>
#include <memory>
#include <thread>

int main()
{
  // This exercises the private registry, not concurrent CXBMCApp factories.
  // No claim that every scheduler interleaving occurs in each iteration.
  for (int iteration = 0; iteration < 100; ++iteration)
  {
    InfinityActivityObserver<int> gate;
    int oldOwner = 1, replacement = 2;
    if (!gate.Publish(&oldOwner)) return 1;
    auto held = std::make_unique<InfinityActivityObserver<int>::Lease>(gate.Acquire());
    std::atomic<int> entering{0}, completed{0};
    std::atomic<bool> published{false};
    std::thread first([&] {
      ++entering;
      gate.Retire(&oldOwner);
      published = gate.Publish(&replacement);
      ++completed;
    });
    std::thread second([&] {
      ++entering;
      gate.Retire(&oldOwner);
      ++completed;
    });
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
    while (entering != 2)
    {
      if (std::chrono::steady_clock::now() > deadline) std::abort();
      std::this_thread::yield();
    }
    for (;;)
    {
      auto lease = gate.Acquire();
      if (!lease) break;
      if (std::chrono::steady_clock::now() > deadline) std::abort();
      std::this_thread::yield();
    }
    if (completed != 0) std::abort(); // Both must respect the live reader.
    held.reset();
    first.join();
    second.join();
    if (!published || completed != 2) return 2;
    {
      auto lease = gate.Acquire();
      if (!lease || lease.Get() != &replacement || *lease.Get() != 2) return 3;
    }
    gate.Retire(&oldOwner); // A late duplicate cannot remove the replacement.
    {
      auto lease = gate.Acquire();
      if (!lease || lease.Get() != &replacement) return 4;
    }
    gate.Retire(&replacement);
    if (gate.Acquire()) return 5;
  }
  std::cout << "PASS 100 bounded duplicate-retirement/replacement races\n";
}
