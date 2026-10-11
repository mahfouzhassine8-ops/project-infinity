/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "utils/log.h"
#include <atomic>
#include <chrono>
#include <string>
#if defined(TARGET_ANDROID)
#include <unistd.h>
#endif

// Observations only. The unchanged provider URL remains the cache/job identity;
// the correlation option is added only to the local Command Center request.
namespace InfinityResumeTiming
{
inline std::atomic<unsigned long long> serial{0};
inline double ClockMs()
{
  return std::chrono::duration<double, std::milli>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
}
class Observation
{
public:
  explicit Observation(const std::string& url)
    : m_started(ClockMs())
  {
    const std::string prefix = "plugin://script.infinity.commandcenter/";
    if (url.compare(0, prefix.size(), prefix) != 0) return;
    m_request = "n" + std::to_string(++serial);
    m_media = url.find("media=tv") != std::string::npos ? "tv" :
              (url.find("media=movie") != std::string::npos ? "movie" : "all");
    Mark("native_queued");
  }
  std::string RequestUrl(const std::string& url) const
  {
    return m_request.empty() ? url : url + (url.find('?') == std::string::npos ? "?" : "&") +
        "infinity_trace=" + m_request;
  }
  void Mark(const char* stage, size_t items = 0) const
  {
    if (m_request.empty()) return;
    const double now = ClockMs();
#if defined(TARGET_ANDROID)
    const long pid = ::getpid();
#else
    const long pid = 0;
#endif
    try { CLog::Log(LOGINFO, "INFINITY_RESUME_TIMING {{\"schema\":1,\"pid\":{},\"stage\":\"{}\",\"request\":\"{}\",\"media\":\"{}\",\"monotonic_ms\":{},\"elapsed_ms\":{},\"items\":{}}}",
              pid, stage, m_request, m_media, now, now - m_started, items); }
    catch (...) { /* Observations never alter directory completion. */ }
  }
private:
  std::string m_request;
  std::string m_media;
  double m_started;
};
} // namespace InfinityResumeTiming
