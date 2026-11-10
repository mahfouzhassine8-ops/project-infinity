#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "owned_lookup.h"
#include <cerrno>
#include <chrono>
#include <climits>
#include <cstring>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <poll.h>
#include <pthread.h>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>
#if defined(__aarch64__) || defined(__x86_64__)
#ifndef SYS_pidfd_open
#define SYS_pidfd_open 434
#endif
#ifndef SYS_pidfd_send_signal
#define SYS_pidfd_send_signal 424
#endif
#endif

namespace {
using Clock = std::chrono::steady_clock;
constexpr unsigned long ClonePidfd = 0x00001000;
constexpr int PidfdKind = 3;
std::atomic<unsigned> slots{0};
struct Fd {
  int value = -1;
  ~Fd() { if (value >= 0) close(value); }
};
struct Slot {
  bool held = false;
  ~Slot() { if (held) --slots; }
};
struct LinuxDirent {
  uint64_t inode;
  int64_t offset;
  unsigned short length;
  unsigned char type;
  char name[1];
};

// Only raw syscalls between clone and exec. No inherited libc/ART locks,
// fdsan callbacks, allocation, logging, resolver, or application callbacks.
[[noreturn]] void Child(const char* path, int channel, int nullFd,
                         pid_t parent, char* const* arguments, char* const* environment,
                         int64_t deadlineNs, const sigset_t* childMask,
                         const struct sigaction* alarmAction)
{
  if (syscall(SYS_prctl, PR_SET_PDEATHSIG, SIGKILL, 0, 0, 0) ||
      syscall(SYS_getppid) != parent) syscall(SYS_exit_group, 121);
  // The child alone gets a deadline signal. No parent/global handler changes.
  // This also bounds cleanup if Android refuses a parent-to-child signal.
  timespec now{};
  if (clock_gettime(CLOCK_MONOTONIC, &now)) syscall(SYS_exit_group, 120);
  int64_t left = deadlineNs - (static_cast<int64_t>(now.tv_sec) * 1000000000 + now.tv_nsec);
  if (left <= 0) syscall(SYS_exit_group, 120);
  itimerval timer{};
  timer.it_value.tv_sec = left / 1000000000;
  timer.it_value.tv_usec = (left % 1000000000 + 999) / 1000;
  if (timer.it_value.tv_usec == 1000000) {
    ++timer.it_value.tv_sec; timer.it_value.tv_usec = 0;
  }
  if (sigaction(SIGALRM, alarmAction, nullptr) ||
      sigprocmask(SIG_SETMASK, childMask, nullptr) || setitimer(ITIMER_REAL, &timer, nullptr))
    syscall(SYS_exit_group, 120);
  if (channel != 0 && syscall(SYS_dup3, channel, 0, 0) < 0) syscall(SYS_exit_group, 122);
  for (int target = 1; target <= 2; ++target) {
    if (nullFd != target && syscall(SYS_dup3, nullFd, target, 0) < 0)
      syscall(SYS_exit_group, 123);
    syscall(SYS_fcntl, target, F_SETFD, 0);
  }
  syscall(SYS_fcntl, 0, F_SETFD, 0);
  const int directory = static_cast<int>(syscall(SYS_openat, AT_FDCWD,
      "/proc/self/fd", O_RDONLY | O_DIRECTORY | O_CLOEXEC, 0));
  if (directory < 0) syscall(SYS_exit_group, 124);
  char buffer[4096];
  for (;;) {
    long n = syscall(SYS_getdents64, directory, buffer, sizeof(buffer));
    if (n < 0 && errno == EINTR) continue;
    if (n < 0) syscall(SYS_exit_group, 125);
    if (!n) break;
    for (long at = 0; at < n;) {
      auto* row = reinterpret_cast<LinuxDirent*>(buffer + at);
      if (row->length < 20 || at + row->length > n) syscall(SYS_exit_group, 126);
      int fd = 0; bool number = row->name[0] != 0;
      for (unsigned i = 0; i + 19 < row->length && row->name[i]; ++i) {
        if (row->name[i] < '0' || row->name[i] > '9') { number = false; break; }
        fd = fd * 10 + row->name[i] - '0';
      }
      if (number && fd > 2 && fd != directory) syscall(SYS_close, fd);
      at += row->length;
    }
  }
  syscall(SYS_close, directory);
  syscall(SYS_execve, path, arguments, environment);
  const int execError = errno;
  static_assert(offsetof(dns_reply, addresses) == 24, "Versioned IPC prefix");
  const int32_t error[] = {static_cast<int32_t>(DNS_MAGIC), 0, EAI_SYSTEM, execError, 0, 0};
  syscall(SYS_sendto, 0, error, sizeof(error), MSG_NOSIGNAL, nullptr, 0);
  syscall(SYS_exit_group, 127);
  __builtin_unreachable();
}
} // namespace

extern char** environ;
static DnsResult PerformLookup(const std::string& helper, const dns_request& request,
                      Clock::time_point began, Clock::time_point deadline,
                      const std::atomic<bool>* cancelled)
{
  DnsResult result;
  if (helper.empty() || helper[0] != '/' || began >= deadline) return result;
  // Capability checks create no child and send no signal. No PID fallback.
  Fd self{static_cast<int>(syscall(SYS_pidfd_open, getpid(), 0))};
  if (self.value < 0) {
    result.wait_error = errno; result.outcome = DnsOutcome::Unsupported; return result;
  }
  siginfo_t check{};
  errno = 0;
  syscall(SYS_waitid, PidfdKind, self.value, &check, WEXITED | WNOHANG, nullptr);
  if (errno != ECHILD || syscall(SYS_pidfd_send_signal, self.value, 0, nullptr, 0)) {
    result.wait_error = errno; result.outcome = DnsOutcome::Unsupported; return result;
  }
  close(self.value); self.value = -1;
  Slot slot;
  unsigned current = slots.load();
  while (current < 4 && !slots.compare_exchange_weak(current, current + 1)) {}
  if (current >= 4) { result.outcome = DnsOutcome::Capacity; return result; }
  slot.held = true;
  int pair[2];
  if (socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, pair)) return result;
  Fd channel{pair[0]}, childChannel{pair[1]}, nullFd{open("/dev/null", O_RDWR | O_CLOEXEC)};
  if (nullFd.value < 0) return result;
  const char* path = helper.c_str();
  char* arguments[] = {const_cast<char*>(path), nullptr};
  sigset_t blocked, original;
  sigfillset(&blocked);
  sigset_t childMask = blocked;
  sigdelset(&childMask, SIGALRM);
  struct sigaction alarmAction{};
  alarmAction.sa_handler = SIG_DFL;
  sigemptyset(&alarmAction.sa_mask);
  const auto deadlineNs = std::chrono::duration_cast<std::chrono::nanoseconds>(
      deadline.time_since_epoch()).count();
  if (pthread_sigmask(SIG_SETMASK, &blocked, &original)) return result;
  int pidfd = -1;
  const pid_t parent = getpid();
  const long child = syscall(SYS_clone, ClonePidfd | SIGCHLD, nullptr, &pidfd, nullptr, 0);
  if (!child) Child(path, childChannel.value, nullFd.value, parent, arguments, environ,
                    deadlineNs, &childMask, &alarmAction);
  const int spawnError = errno;
  const int maskError = pthread_sigmask(SIG_SETMASK, &original, nullptr);
  Fd identity{pidfd};
  if (child < 0) {
    errno = spawnError;
    result.outcome = DnsOutcome::Unsupported;
    return result;
  }
  // A successfully cloned child is owned through pidfd until reaped, even if
  // subsequent setup fails. No operation below signals a numeric PID.
  close(childChannel.value); childChannel.value = -1;
  result.spawn_seconds = std::chrono::duration<double>(Clock::now() - began).count();
  bool terminate = maskError != 0;
  if (fcntl(channel.value, F_SETFL, O_NONBLOCK) < 0) terminate = true;
  size_t sent = 0, received = 0;
  bool dead = false, failed = false;
  bool waitConsumed = false;
  siginfo_t status{};
  int waited = -1;
  while (!dead) {
    if (!terminate && cancelled && cancelled->load()) {
      result.outcome = DnsOutcome::Cancelled; terminate = true;
    }
    if (!terminate && Clock::now() >= deadline) {
      result.outcome = DnsOutcome::Timeout; terminate = true;
    }
    if (terminate) {
      if (syscall(SYS_pidfd_send_signal, identity.value, SIGKILL, nullptr, 0) < 0 && errno != ESRCH)
        failed = true;
      // Retain ownership until kernel exit is observable. Time spent here is
      // included in return_seconds, never hidden after the reported deadline.
      pollfd descriptor{identity.value, POLLIN, 0};
      int polled;
      do { polled = poll(&descriptor, 1, 10); } while (polled < 0 && errno == EINTR);
      if (polled > 0 && descriptor.revents & POLLIN) dead = true;
      else if (polled < 0 || descriptor.revents & (POLLNVAL | POLLERR)) {
        // Do not spin on an invalid descriptor or poll failure. The child
        // self-timer remains armed across exec; preserve the wait error.
        failed = true;
        do { waited = static_cast<int>(syscall(SYS_waitid, PidfdKind, identity.value,
                    &status, WEXITED, nullptr)); } while (waited < 0 && errno == EINTR);
        waitConsumed = true; dead = true;
      }
      continue;
    }
    pollfd descriptors[] = {{channel.value, static_cast<short>(POLLIN | (sent < sizeof(request) ? POLLOUT : 0)), 0},
                            {identity.value, POLLIN, 0}};
    const int polled = poll(descriptors, 2, 10);
    if (polled < 0 && errno == EINTR) continue;
    if (polled < 0) { failed = terminate = true; continue; }
    if (descriptors[0].revents & POLLOUT) {
      const ssize_t n = send(channel.value, reinterpret_cast<const char*>(&request) + sent,
                             sizeof(request) - sent, MSG_NOSIGNAL);
      if (n > 0) sent += static_cast<size_t>(n);
      else if (n < 0 && errno != EAGAIN && errno != EINTR) { failed = terminate = true; }
    }
    if (descriptors[0].revents & (POLLIN | POLLHUP)) {
      ssize_t n = 0;
      do {
        if (received == sizeof(result.reply)) break;
        n = recv(channel.value, reinterpret_cast<char*>(&result.reply) + received,
                 sizeof(result.reply) - received, MSG_DONTWAIT);
        if (n > 0) received += static_cast<size_t>(n);
      } while (n > 0);
      if (n < 0 && errno != EAGAIN && errno != EINTR) { failed = terminate = true; }
    }
    dead = descriptors[1].revents & POLLIN;
  }
  const auto exitObserved = Clock::now();
  // Completion can race the initial socket poll. Drain after observing exit.
  while (received < sizeof(result.reply)) {
    const ssize_t n = recv(channel.value, reinterpret_cast<char*>(&result.reply) + received,
                           sizeof(result.reply) - received, MSG_DONTWAIT);
    if (n > 0) received += static_cast<size_t>(n);
    else if (n < 0 && errno == EINTR) continue;
    else break;
  }
  char excess;
  if (recv(channel.value, &excess, 1, MSG_DONTWAIT) > 0) failed = true;
  if (!waitConsumed)
    do { waited = static_cast<int>(syscall(SYS_waitid, PidfdKind, identity.value, &status,
                                          WEXITED, nullptr)); } while (waited < 0 && errno == EINTR);
  if (waited < 0) result.wait_error = errno;
  else { result.child_code = status.si_code; result.child_status = status.si_status; }
  if (!waited && status.si_code == CLD_KILLED && status.si_status == SIGALRM &&
      result.outcome != DnsOutcome::Cancelled &&
      Clock::now() >= deadline - std::chrono::milliseconds(1))
    result.outcome = DnsOutcome::Timeout;
  // ECHILD after pidfd exit readiness is already reaped, not a successful answer.
  const size_t expected = offsetof(dns_reply, addresses) +
      result.reply.count * sizeof(dns_address);
  bool valid = result.reply.magic == DNS_MAGIC && result.reply.count <= DNS_MAX_ADDRESSES &&
               received == expected && result.reply.extra_fds == 0 &&
               (result.reply.gai_error == 0 || result.reply.count == 0);
  for (unsigned i = 0; valid && i < result.reply.count; ++i) {
    const auto& row = result.reply.addresses[i];
    valid = ((row.family == AF_INET && row.length == sizeof(sockaddr_in)) ||
             (row.family == AF_INET6 && row.length == sizeof(sockaddr_in6))) &&
            row.address.ss_family == row.family &&
            (request.family == AF_UNSPEC || request.family == row.family) &&
            (!request.socktype || request.socktype == row.socktype) &&
            std::memchr(row.canonical, 0, sizeof(row.canonical));
  }
  if (!terminate && !failed && !waited && status.si_code == CLD_EXITED && status.si_status == 0 && valid)
    result.outcome = DnsOutcome::Answer;
  for (Fd* descriptor : {&channel, &identity, &nullFd}) {
    if (descriptor->value >= 0) close(descriptor->value);
    descriptor->value = -1;
  }
  --slots; slot.held = false;
  result.cleanup_seconds = std::chrono::duration<double>(Clock::now() - exitObserved).count();
  result.return_seconds = std::chrono::duration<double>(Clock::now() - began).count();
  return result;
}

DnsResult OwnedLookup(const std::string& helper, const dns_request& request,
                      int deadlineMs, const std::atomic<bool>* cancelled)
{
  const auto began = Clock::now();
  const auto deadline = began + std::chrono::milliseconds(deadlineMs);
  DnsResult result;
  if (cancelled && cancelled->load()) result.outcome = DnsOutcome::Cancelled;
  else result = PerformLookup(helper, request, began, deadline, cancelled);
  // This point is after every owned descriptor, slot and child has been
  // cleaned up. A late answer cannot bypass timeout/cancellation precedence.
  if (cancelled && cancelled->load()) result.outcome = DnsOutcome::Cancelled;
  else if (Clock::now() >= deadline && deadlineMs > 0) result.outcome = DnsOutcome::Timeout;
  result.return_seconds = std::chrono::duration<double>(Clock::now() - began).count();
  return result;
}
