/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

// Shutdown evidence only. No Kodi, Python, registry or logger locks, and no
// extra worker, retained descriptor, timeout, kill or lifecycle callback.
#if defined(TARGET_ANDROID) || defined(INFINITY_SHUTDOWN_TRACE_TEST)
#include <atomic>
#include <cerrno>
#include <cstdio>
#include <cstdint>
#include <fcntl.h>
#include <string>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#if defined(TARGET_ANDROID)
#include <android/log.h>
#endif
namespace InfinityShutdownTrace
{
constexpr int BUILD = 2103314;
constexpr off_t FILE_LIMIT = 2 * 1024 * 1024;
inline int64_t ClockMs(clockid_t clock)
{
  timespec value{};
  if (clock_gettime(clock, &value) != 0) return 0;
  return static_cast<int64_t>(value.tv_sec) * 1000 + value.tv_nsec / 1000000;
}
inline int64_t BootMs() { return ClockMs(CLOCK_BOOTTIME); }
struct State
{
  std::string path;
  std::atomic<int> active{0};
  std::atomic<uint64_t> sequence{1};
  int64_t began{0};
};
inline State& GetState()
{
  // Remains available to final static destructors called by exit(0).
  static State* state = new State;
  return *state;
}
inline void Configure(const char* directory)
{
  if (directory && *directory && GetState().path.empty())
    GetState().path = std::string(directory) + "/infinity-native-shutdown.jsonl";
}
inline bool Enabled() { return GetState().active.load(std::memory_order_acquire) == 2; }
inline void Event(const char* event, const char* stage, uint64_t span = 0,
                  int invoker = -1, int64_t duration = -1) noexcept
{
  struct ErrnoGuard { int value{errno}; ~ErrnoGuard() { errno = value; } } errnoGuard;
  try
  {
    auto& state = GetState();
    if (!Enabled() || state.path.empty()) return;
    // All labels are source literals; no paths, URLs, accounts or media names.
    char row[1024];
    const int count = std::snprintf(row, sizeof(row),
        "{\"schema\":1,\"build\":%d,\"pid\":%d,\"tid\":%ld,\"session\":%lld,"
        "\"epoch_ms\":%lld,\"boottime_ms\":%lld,\"event\":\"%s\",\"stage\":\"%s\","
        "\"span\":%llu,\"invoker_id\":%d,\"duration_ms\":%lld}\n",
        BUILD, getpid(), syscall(SYS_gettid), static_cast<long long>(state.began),
        static_cast<long long>(ClockMs(CLOCK_REALTIME)), static_cast<long long>(BootMs()),
        event, stage, static_cast<unsigned long long>(span), invoker,
        static_cast<long long>(duration));
    if (count <= 0 || static_cast<size_t>(count) >= sizeof(row)) return;
    const int fd = open(state.path.c_str(), O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600);
    if (fd >= 0)
    {
      struct stat info{};
      if (fstat(fd, &info) == 0 && info.st_size < FILE_LIMIT)
      {
        ssize_t result;
        do { result = write(fd, row, static_cast<size_t>(count)); } while (result < 0 && errno == EINTR);
      }
      close(fd);
    }
#if defined(TARGET_ANDROID)
    __android_log_write(ANDROID_LOG_INFO, "InfinityShutdown", row);
#endif
  }
  catch (...) { /* Evidence must not break shutdown. */ }
}
inline void Begin() noexcept
{
  struct ErrnoGuard { int value{errno}; ~ErrnoGuard() { errno = value; } } errnoGuard;
  try
  {
    auto& state = GetState();
    int expected = 0;
    if (!state.active.compare_exchange_strong(expected, 1)) return;
    state.began = BootMs();
    if (!state.path.empty())
    {
      const std::string previous = state.path + ".previous";
      // Keep the prior run. Start the current file only on a real shutdown.
      rename(state.path.c_str(), previous.c_str());
    }
    state.active.store(2, std::memory_order_release);
    Event("milestone", "shutdown.begin");
  }
  catch (...) { GetState().active.store(0); }
}
class Scope
{
  const char* m_stage;
  int m_invoker;
  uint64_t m_span{0};
  int64_t m_began{0};
public:
  explicit Scope(const char* stage, int invoker = -1) noexcept
    : m_stage(stage), m_invoker(invoker)
  {
    if (Enabled())
    {
      m_span = GetState().sequence.fetch_add(1);
      m_began = BootMs();
      Event("begin", m_stage, m_span, m_invoker);
    }
  }
  Scope(const Scope&) = delete;
  Scope& operator=(const Scope&) = delete;
  void End() noexcept
  {
    if (m_span)
    {
      Event("end", m_stage, m_span, m_invoker, BootMs() - m_began);
      m_span = 0;
    }
  }
  ~Scope() { End(); }
};
}
#else
namespace InfinityShutdownTrace
{
inline void Configure(const char*) {}
inline void Begin() {}
inline void Event(const char*, const char*, unsigned long long = 0, int = -1, long long = -1) {}
class Scope
{
public:
  explicit Scope(const char*, int = -1) {}
  void End() {}
};
}
#endif
