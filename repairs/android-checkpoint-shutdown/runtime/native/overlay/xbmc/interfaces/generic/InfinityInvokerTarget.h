/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <atomic>
#include <cstdint>

// Diagnostic state only. Written by the invoker's own worker thread; read by
// the stopping thread. It must never decide admission, cancellation or liveness.
// One atomic word prevents combining an old thread ID with a newer stage.
class InfinityInvokerTarget
{
public:
  enum class Stage : std::uint8_t
  {
    NotStarted = 0,
    Startup,
    ProcessMutex,
    Execute,
    ReuseWait,
    Finalizer,
    ManagerCallback,
    ExitReported,
    ExceptionFinalizer,
    ExceptionManagerCallback,
    ExceptionReported
  };
  struct Snapshot
  {
    std::uint32_t tid;
    Stage stage;
  };

  void Start(std::uint32_t tid) noexcept
  {
    m_value.store((static_cast<std::uint64_t>(tid) << 8) |
                      static_cast<std::uint8_t>(Stage::Startup),
                  std::memory_order_release);
  }

  // Sole-writer operation: only call from this invoker's native worker.
  void Mark(Stage stage) noexcept
  {
    const auto prior = m_value.load(std::memory_order_relaxed);
    if ((prior >> 8) == 0)
      return;
    m_value.store((prior & ~std::uint64_t{0xff}) | static_cast<std::uint8_t>(stage),
                  std::memory_order_release);
  }

  Snapshot Read() const noexcept
  {
    const auto value = m_value.load(std::memory_order_acquire);
    return {static_cast<std::uint32_t>(value >> 8), static_cast<Stage>(value & 0xff)};
  }

  static const char* Name(Stage stage) noexcept
  {
    switch (stage)
    {
      case Stage::NotStarted: return "not_started";
      case Stage::Startup: return "startup";
      case Stage::ProcessMutex: return "process_mutex";
      case Stage::Execute: return "execute";
      case Stage::ReuseWait: return "reuse_wait";
      case Stage::Finalizer: return "finalizer";
      case Stage::ManagerCallback: return "manager_callback";
      case Stage::ExitReported: return "exit_reported";
      case Stage::ExceptionFinalizer: return "exception_finalizer";
      case Stage::ExceptionManagerCallback: return "exception_manager_callback";
      case Stage::ExceptionReported: return "exception_reported";
    }
    return "unknown";
  }

private:
  static_assert(std::atomic<std::uint64_t>::is_always_lock_free,
                "Invoker diagnostics require lock-free 64-bit atomics on this target");
  std::atomic<std::uint64_t> m_value{0};
};
