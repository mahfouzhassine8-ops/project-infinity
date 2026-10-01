/* SPDX-License-Identifier: GPL-2.0-or-later
 * Android socket readiness without the fixed-size fd_set ABI.
 * This adapter owns no descriptors, changes no resource limits, and never
 * suppresses FORTIFY. Other platforms retain their existing select backend.
 */
#pragma once

#include <cstdint>

#if defined(__ANDROID__) || defined(INFINITY_SOCKET_POLL_TEST)
#include <algorithm>
#include <cerrno>
#include <climits>
#include <new>
#include <poll.h>
#include <sys/time.h>
#include <time.h>
#include <vector>
#if defined(__ANDROID__)
#include <android/log.h>
#include <atomic>
#endif

namespace InfinitySocketPoll
{
struct FdSet
{
  std::vector<int> descriptors;
  int error{0};
};

inline void Clear(FdSet* set) noexcept
{
  set->descriptors.clear();
  set->error = 0;
}

template<class Descriptor>
inline void Add(Descriptor value, FdSet* set) noexcept
{
  const auto fd = static_cast<intptr_t>(value);
  if (fd < 0 || fd > INT_MAX)
  {
    set->error = EBADF;
    return;
  }
  if (std::find(set->descriptors.begin(), set->descriptors.end(), fd) !=
      set->descriptors.end())
    return;
  try { set->descriptors.push_back(static_cast<int>(fd)); }
  catch (const std::bad_alloc&) { set->error = ENOMEM; }
}

template<class Descriptor>
inline bool Contains(Descriptor value, const FdSet* set) noexcept
{
  const auto fd = static_cast<intptr_t>(value);
  return fd >= 0 && fd <= INT_MAX &&
         std::find(set->descriptors.begin(), set->descriptors.end(), fd) !=
             set->descriptors.end();
}

inline void SubtractElapsed(timeval& remaining, const timespec& before,
                            const timespec& after) noexcept
{
  time_t seconds = after.tv_sec - before.tv_sec;
  long nanos = after.tv_nsec - before.tv_nsec;
  if (nanos < 0) { --seconds; nanos += 1000000000L; }
  if (seconds < 0) return;
  const long micros = nanos / 1000;
  if (seconds > remaining.tv_sec ||
      (seconds == remaining.tv_sec && micros >= remaining.tv_usec))
  { remaining.tv_sec = 0; remaining.tv_usec = 0; return; }
  remaining.tv_sec -= seconds;
  remaining.tv_usec -= micros;
  if (remaining.tv_usec < 0)
  { --remaining.tv_sec; remaining.tv_usec += 1000000; }
}

inline short ReadEvents() noexcept
{
  short mask = POLLIN | POLLHUP | POLLERR;
#ifdef POLLRDNORM
  mask |= POLLRDNORM;
#endif
#ifdef POLLRDBAND
  mask |= POLLRDBAND;
#endif
  return mask;
}
inline short WriteEvents() noexcept
{
  short mask = POLLOUT | POLLERR;
#ifdef POLLWRNORM
  mask |= POLLWRNORM;
#endif
#ifdef POLLWRBAND
  mask |= POLLWRBAND;
#endif
  return mask;
}

inline void ReportBackend(const std::vector<pollfd>& descriptors) noexcept
{
#if defined(__ANDROID__)
  int largest = -1;
  for (const auto& p : descriptors) largest = std::max(largest, p.fd);
  if (largest >= 1024)
  {
    static std::atomic<bool> reported{false};
    if (!reported.exchange(true))
      __android_log_print(ANDROID_LOG_INFO, "InfinityNativeFd",
                          "INFINITY_FD_POLL_V1 high_fd=%d watched=%zu; no fd_set used",
                          largest, descriptors.size());
  }
#else
  (void)descriptors;
#endif
}

// select-compatible result count (ready bits, not merely ready descriptors).
// EINTR/EBADF leave requested sets intact. A finite timeout is decremented,
// so callers which retry EINTR cannot accidentally extend a deadline forever.
inline int Wait(intptr_t nfds, FdSet* reads, FdSet* writes, FdSet* exceptions,
                timeval* timeout) noexcept
{
  if (nfds < 0 || nfds > INT_MAX ||
      (timeout && (timeout->tv_sec < 0 || timeout->tv_usec < 0 ||
                   timeout->tv_usec >= 1000000)))
  { errno = EINVAL; return -1; }
  FdSet* sets[] = {reads, writes, exceptions};
  const short requested[] = {POLLIN, POLLOUT, POLLPRI};
  const short readyMasks[] = {ReadEvents(), WriteEvents(), POLLPRI};
  for (const auto* set : sets)
    if (set && set->error) { errno = set->error; return -1; }

  try
  {
    std::vector<pollfd> descriptors;
    for (unsigned k = 0; k != 3; ++k)
    {
      if (!sets[k]) continue;
      for (const int fd : sets[k]->descriptors)
      {
        if (fd >= nfds) continue;
        auto it = std::find_if(descriptors.begin(), descriptors.end(),
                               [fd](const pollfd& p) { return p.fd == fd; });
        if (it == descriptors.end()) descriptors.push_back({fd, requested[k], 0});
        else it->events |= requested[k];
      }
    }
    ReportBackend(descriptors);
    for (;;)
    {
      timespec before{}, after{}, wait{};
      if (timeout)
      {
        wait.tv_sec = timeout->tv_sec;
        wait.tv_nsec = timeout->tv_usec * 1000;
        if (::clock_gettime(CLOCK_MONOTONIC, &before) != 0) return -1;
      }
      const int result = ::ppoll(descriptors.data(), descriptors.size(),
                                 timeout ? &wait : nullptr, nullptr);
      const int savedErrno = errno;
      if (timeout && ::clock_gettime(CLOCK_MONOTONIC, &after) == 0)
        SubtractElapsed(*timeout, before, after);
      errno = savedErrno;
      if (result < 0) return -1;
      for (const auto& p : descriptors)
        if (p.revents & POLLNVAL) { errno = EBADF; return -1; }

      int count = 0;
      for (unsigned k = 0; k != 3; ++k)
      {
        if (!sets[k]) continue;
        for (const int fd : sets[k]->descriptors)
        {
          auto it = std::find_if(descriptors.begin(), descriptors.end(),
                                 [fd](const pollfd& p) { return p.fd == fd; });
          if (it != descriptors.end() && (it->revents & readyMasks[k])) ++count;
        }
      }
      if (result == 0 || count > 0)
      {
        for (unsigned k = 0; k != 3; ++k)
        {
          if (!sets[k]) continue;
          auto& values = sets[k]->descriptors;
          values.erase(std::remove_if(values.begin(), values.end(), [&](int fd) {
            auto it = std::find_if(descriptors.begin(), descriptors.end(),
                                   [fd](const pollfd& p) { return p.fd == fd; });
            return it == descriptors.end() || !(it->revents & readyMasks[k]);
          }), values.end());
        }
        return count;
      }
      // poll reports HUP/ERR even for an exception-only watch. select does
      // not. Ignore those nonrequested terminal events instead of busy-looping.
      for (auto& p : descriptors)
      {
        if (p.revents) p.fd = -1;
        p.revents = 0;
      }
    }
  }
  catch (const std::bad_alloc&) { errno = ENOMEM; return -1; }
}
} // namespace InfinitySocketPoll
#else
// Types/system declarations come from the caller's existing platform headers.
namespace InfinitySocketPoll
{
using FdSet = fd_set;
inline void Clear(FdSet* set) { FD_ZERO(set); }
template<class Descriptor> inline void Add(Descriptor fd, FdSet* set) { FD_SET(fd, set); }
template<class Descriptor> inline bool Contains(Descriptor fd, const FdSet* set)
{ return FD_ISSET(fd, const_cast<FdSet*>(set)) != 0; }
inline int Wait(intptr_t nfds, FdSet* reads, FdSet* writes, FdSet* exceptions,
                timeval* timeout)
{ return ::select(static_cast<int>(nfds), reads, writes, exceptions, timeout); }
}
#endif
