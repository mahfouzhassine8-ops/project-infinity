/*
 * Infinity crash forensics recorder.
 * Diagnostic-only companion library; does not modify Kodi/libkodi behavior.
 * It writes a bounded register record, then restores/re-raises to Android's
 * previous fatal-signal handler so debuggerd/tombstone handling is preserved.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <ucontext.h>
#include <unistd.h>

#define INFINITY_CRASH_SCHEMA 1
#define INFINITY_DIAG_DIR_NAME "infinity-native-diagnostics"
#define INFINITY_NATIVE_ENGINE_SHA "704834f42e49a2eea0a36ad41b5f79345f5e4108dcd339213899ea3c6ff045a0"

static char g_crash_path[PATH_MAX];
static char g_diag_dir[PATH_MAX];
static volatile sig_atomic_t g_handling = 0;
static const int g_signals[] = { SIGSEGV, SIGABRT, SIGBUS, SIGILL, SIGFPE };
static struct sigaction g_previous[sizeof(g_signals) / sizeof(g_signals[0])];
static unsigned char g_altstack_mem[64 * 1024];

static size_t append_char(char* out, size_t cap, size_t at, char c)
{
  if (at < cap) out[at] = c;
  return at + 1;
}

static size_t append_str(char* out, size_t cap, size_t at, const char* s)
{
  if (!s) return at;
  while (*s) at = append_char(out, cap, at, *s++);
  return at;
}

static size_t append_u64_dec(char* out, size_t cap, size_t at, uint64_t value)
{
  char tmp[32];
  size_t n = 0;
  do {
    tmp[n++] = (char)('0' + (value % 10u));
    value /= 10u;
  } while (value && n < sizeof(tmp));
  while (n) at = append_char(out, cap, at, tmp[--n]);
  return at;
}

static size_t append_i64_dec(char* out, size_t cap, size_t at, int64_t value)
{
  if (value < 0) {
    at = append_char(out, cap, at, '-');
    return append_u64_dec(out, cap, at, (uint64_t)(-(value + 1)) + 1u);
  }
  return append_u64_dec(out, cap, at, (uint64_t)value);
}

static size_t append_hex(char* out, size_t cap, size_t at, uintptr_t value)
{
  static const char hex[] = "0123456789abcdef";
  char tmp[2 * sizeof(uintptr_t)];
  size_t n = 0;
  do {
    tmp[n++] = hex[value & 0xfu];
    value >>= 4u;
  } while (value && n < sizeof(tmp));
  at = append_str(out, cap, at, "0x");
  while (n) at = append_char(out, cap, at, tmp[--n]);
  return at;
}

static size_t append_kv_dec(char* out, size_t cap, size_t at, const char* key, int64_t value)
{
  at = append_str(out, cap, at, key);
  at = append_i64_dec(out, cap, at, value);
  return append_char(out, cap, at, '\n');
}

static size_t append_kv_hex(char* out, size_t cap, size_t at, const char* key, uintptr_t value)
{
  at = append_str(out, cap, at, key);
  at = append_hex(out, cap, at, value);
  return append_char(out, cap, at, '\n');
}

static int signal_index(int sig)
{
  size_t i;
  for (i = 0; i < sizeof(g_signals) / sizeof(g_signals[0]); ++i)
    if (g_signals[i] == sig) return (int)i;
  return -1;
}

static void restore_and_reraise(int sig, pid_t tid)
{
  int idx = signal_index(sig);
  if (idx >= 0) (void)sigaction(sig, &g_previous[idx], NULL);
  else {
    struct sigaction dfl;
    dfl.sa_handler = SIG_DFL;
    sigemptyset(&dfl.sa_mask);
    dfl.sa_flags = 0;
    (void)sigaction(sig, &dfl, NULL);
  }

  sigset_t unblocked;
  sigemptyset(&unblocked);
  sigaddset(&unblocked, sig);
  (void)sigprocmask(SIG_UNBLOCK, &unblocked, NULL);
  (void)syscall(__NR_tgkill, getpid(), tid, sig);
  _exit(128 + sig);
}

static void crash_handler(int sig, siginfo_t* info, void* opaque);

static void forward_original_signal(int sig, pid_t tid, siginfo_t* info, void* opaque)
{
  int idx = signal_index(sig);
  if (idx >= 0) {
    struct sigaction previous = g_previous[idx];
    if ((previous.sa_flags & SA_SIGINFO) &&
        previous.sa_handler != SIG_DFL && previous.sa_handler != SIG_IGN &&
        previous.sa_sigaction != crash_handler && info && opaque &&
        sigaction(sig, &previous, NULL) == 0) {
      /* Android's debuggerd consumes these original arguments. Sending tgkill
       * first replaces the fault PC, si_code and address with our syscall.
       * Restore the disposition too: debuggerd checks its SA_SIGINFO flag. */
      (void)sigprocmask(SIG_BLOCK, &previous.sa_mask, NULL);
      previous.sa_sigaction(sig, info, opaque);

      /* The recorder has always terminated fatal signals. If the previous
       * handler returns (debuggerd may queue the fatal signal), do not restore
       * it again or call it twice. Keep the original fatal signal/exit status. */
      struct sigaction dfl = {0};
      dfl.sa_handler = SIG_DFL;
      sigemptyset(&dfl.sa_mask);
      (void)sigaction(sig, &dfl, NULL);
      sigset_t unblocked;
      sigemptyset(&unblocked);
      sigaddset(&unblocked, sig);
      (void)sigprocmask(SIG_UNBLOCK, &unblocked, NULL);
      (void)syscall(__NR_tgkill, getpid(), tid, sig);
      _exit(128 + sig);
    }
  }
  /* Retain the original legacy/default/ignore and reentrant fallback. */
  restore_and_reraise(sig, tid);
}

static void crash_handler(int sig, siginfo_t* info, void* opaque)
{
  pid_t tid = (pid_t)syscall(__NR_gettid);
  if (g_handling) restore_and_reraise(sig, tid);
  g_handling = 1;

  if (g_crash_path[0] != '\0') {
    char out[4096];
    size_t at = 0;
    struct timespec ts;
    uint64_t timestamp_ms = 0;
    uintptr_t pc = 0, sp = 0, fp = 0, lr = 0, pstate = 0;

    if (clock_gettime(CLOCK_REALTIME, &ts) == 0)
      timestamp_ms = (uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u;

#if defined(__aarch64__)
    if (opaque) {
      ucontext_t* uc = (ucontext_t*)opaque;
      pc = (uintptr_t)uc->uc_mcontext.pc;
      sp = (uintptr_t)uc->uc_mcontext.sp;
      fp = (uintptr_t)uc->uc_mcontext.regs[29];
      lr = (uintptr_t)uc->uc_mcontext.regs[30];
      pstate = (uintptr_t)uc->uc_mcontext.pstate;
    }
#endif

    at = append_kv_dec(out, sizeof(out), at, "schema=", INFINITY_CRASH_SCHEMA);
    at = append_kv_dec(out, sizeof(out), at, "timestamp_ms=", (int64_t)timestamp_ms);
    at = append_kv_dec(out, sizeof(out), at, "pid=", (int64_t)getpid());
    at = append_kv_dec(out, sizeof(out), at, "tid=", (int64_t)tid);
    at = append_kv_dec(out, sizeof(out), at, "signal=", (int64_t)sig);
    at = append_kv_dec(out, sizeof(out), at, "si_code=", info ? (int64_t)info->si_code : 0);
    at = append_kv_hex(out, sizeof(out), at, "fault_address=",
                       info ? (uintptr_t)info->si_addr : (uintptr_t)0);
    at = append_kv_hex(out, sizeof(out), at, "pc=", pc);
    at = append_kv_hex(out, sizeof(out), at, "sp=", sp);
    at = append_kv_hex(out, sizeof(out), at, "fp=", fp);
    at = append_kv_hex(out, sizeof(out), at, "lr=", lr);
    at = append_kv_hex(out, sizeof(out), at, "pstate=", pstate);
    at = append_str(out, sizeof(out), at, "arch=aarch64\n");
    at = append_str(out, sizeof(out), at, "native_engine_sha256=" INFINITY_NATIVE_ENGINE_SHA "\n");

    if (at > sizeof(out)) at = sizeof(out);

    /* Do not depend on a descriptor opened during startup: other native
     * initialization is allowed to close descriptors it does not own.
     * Open the precomputed app-private path only after the fatal signal has
     * reached this handler, then replace the slot atomically enough for the
     * next process to preserve it. openat/write/fsync/close are direct syscalls
     * here and do not allocate or touch JNI. */
    int record_fd = (int)syscall(__NR_openat, AT_FDCWD, g_crash_path,
                                 O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
    if (record_fd >= 0) {
      (void)syscall(__NR_write, record_fd, out, at);
      (void)syscall(__NR_fsync, record_fd);
      (void)syscall(__NR_close, record_fd);
    }
  }

  forward_original_signal(sig, tid, info, opaque);
}

static uintptr_t action_address(const struct sigaction* action)
{
  if (!action) return 0;
  if ((action->sa_flags & SA_SIGINFO) != 0)
    return (uintptr_t)action->sa_sigaction;
  return (uintptr_t)action->sa_handler;
}

static int action_is_ours(const struct sigaction* action)
{
  return action_address(action) == (uintptr_t)crash_handler;
}

static void native_breadcrumb(const char* state, uintptr_t address)
{
  char path[PATH_MAX];
  char line[512];
  struct timespec ts;
  uint64_t timestamp_ms = 0;
  int n;
  int fd;

  if (g_diag_dir[0] == '\0' || !state) return;
  if (clock_gettime(CLOCK_REALTIME, &ts) == 0)
    timestamp_ms = (uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u;

  n = snprintf(path, sizeof(path), "%s/lifecycle-breadcrumbs.jsonl", g_diag_dir);
  if (n <= 0 || (size_t)n >= sizeof(path)) return;

  n = snprintf(line, sizeof(line),
               "{\"schema\":2,\"timestamp_ms\":%llu,\"pid\":%d,"
               "\"event\":\"native.sigsegv.%s.0x%llx\"}\n",
               (unsigned long long)timestamp_ms, (int)getpid(), state,
               (unsigned long long)address);
  if (n <= 0) return;
  if ((size_t)n > sizeof(line)) n = (int)sizeof(line);

  fd = open(path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600);
  if (fd < 0) return;
  (void)write(fd, line, (size_t)n);
  (void)close(fd);
}

static void rearm_sigsegv_if_needed(void)
{
  int idx = signal_index(SIGSEGV);
  struct sigaction current;
  struct sigaction action;
  uintptr_t previous_address;

  if (idx < 0) return;
  if (sigaction(SIGSEGV, NULL, &current) != 0) {
    native_breadcrumb("query_failed", 0);
    return;
  }

  previous_address = action_address(&current);
  if (action_is_ours(&current)) {
    native_breadcrumb("owner_self", previous_address);
    return;
  }

  g_previous[idx] = current;
  action.sa_sigaction = crash_handler;
  sigemptyset(&action.sa_mask);
  action.sa_flags = SA_SIGINFO | SA_ONSTACK;
  if (sigaction(SIGSEGV, &action, NULL) == 0)
    native_breadcrumb("rearmed_from", previous_address);
  else
    native_breadcrumb("rearm_failed", previous_address);
}

static void* sigsegv_monitor(void* ignored)
{
  (void)ignored;
  /* Bounded three-minute ownership watch. Kodi/ART are free to finish late
   * native initialization; if another user-level SIGSEGV handler replaces
   * ours, preserve it as the chain target and put our recorder back on top. */
  for (int i = 0; i < 36; ++i) {
    struct timespec wait = { 5, 0 };
    while (nanosleep(&wait, &wait) != 0 && errno == EINTR) {}
    rearm_sigsegv_if_needed();
  }
  native_breadcrumb("monitor_complete", 0);
  return NULL;
}

static void copy_maps(const char* diag_dir)
{
  char output_path[PATH_MAX];
  char buffer[8192];
  int in_fd = -1, out_fd = -1;
  pid_t pid = getpid();
  int n = 0;

  /* snprintf is used only during library construction, never from the signal handler. */
  n = snprintf(output_path, sizeof(output_path), "%s/native-maps-%d.txt", diag_dir, (int)pid);
  if (n <= 0 || (size_t)n >= sizeof(output_path)) return;

  in_fd = open("/proc/self/maps", O_RDONLY | O_CLOEXEC);
  if (in_fd < 0) return;
  out_fd = open(output_path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
  if (out_fd < 0) { close(in_fd); return; }

  for (;;) {
    ssize_t got = read(in_fd, buffer, sizeof(buffer));
    if (got <= 0) break;
    ssize_t off = 0;
    while (off < got) {
      ssize_t wrote = write(out_fd, buffer + off, (size_t)(got - off));
      if (wrote <= 0) break;
      off += wrote;
    }
    if (off < got) break;
  }
  close(out_fd);
  close(in_fd);
}

static int infinity_owned_process(void)
{
  static const char expected[] = "com.projectinfinity.kodi:kodi";
  char name[128];
  int fd = open("/proc/self/cmdline", O_RDONLY | O_CLOEXEC);
  if (fd < 0) return 0;
  ssize_t size = read(fd, name, sizeof(name));
  (void)close(fd);
  if (size < (ssize_t)sizeof(expected)) return 0;
  for (size_t i = 0; i < sizeof(expected); ++i)
    if (name[i] != expected[i]) return 0;
  return 1;
}

__attribute__((constructor))
static void infinity_crash_recorder_install(void)
{
#if !defined(__aarch64__)
  return;
#else
  if (!infinity_owned_process()) return;
  char diag_dir[PATH_MAX];
  char crash_path[PATH_MAX];
  uid_t uid = getuid();
  unsigned int user_id = (unsigned int)(uid / 100000u);
  size_t i;

  int n = snprintf(diag_dir, sizeof(diag_dir),
                   "/data/user/%u/com.projectinfinity.kodi/files/%s",
                   user_id, INFINITY_DIAG_DIR_NAME);
  if (n <= 0 || (size_t)n >= sizeof(diag_dir)) return;
  (void)mkdir(diag_dir, 0700);

  n = snprintf(crash_path, sizeof(crash_path), "%s/native-crash-last.txt", diag_dir);
  if (n <= 0 || (size_t)n >= sizeof(crash_path)) return;

  /* Persist only the path at startup. Never keep crash evidence dependent on
   * a descriptor that later native initialization could close. */
  (void)snprintf(g_diag_dir, sizeof(g_diag_dir), "%s", diag_dir);
  (void)snprintf(g_crash_path, sizeof(g_crash_path), "%s", crash_path);
  {
    int placeholder_fd = open(g_crash_path, O_WRONLY | O_CREAT | O_CLOEXEC, 0600);
    if (placeholder_fd >= 0) close(placeholder_fd);
  }

  copy_maps(diag_dir);

  stack_t stack;
  stack.ss_sp = g_altstack_mem;
  stack.ss_size = sizeof(g_altstack_mem);
  stack.ss_flags = 0;
  (void)sigaltstack(&stack, NULL);

  for (i = 0; i < sizeof(g_signals) / sizeof(g_signals[0]); ++i) {
    struct sigaction action;
    action.sa_sigaction = crash_handler;
    sigemptyset(&action.sa_mask);
    action.sa_flags = SA_SIGINFO | SA_ONSTACK;
    if (sigaction(g_signals[i], &action, &g_previous[i]) != 0) {
      /* Best effort: a failed signal registration must never stop Infinity. */
      g_previous[i].sa_handler = SIG_DFL;
      sigemptyset(&g_previous[i].sa_mask);
      g_previous[i].sa_flags = 0;
    }
  }

  native_breadcrumb("installed", action_address(&g_previous[signal_index(SIGSEGV)]));
  {
    pthread_t monitor;
    if (pthread_create(&monitor, NULL, sigsegv_monitor, NULL) == 0)
      (void)pthread_detach(monitor);
    else
      native_breadcrumb("monitor_start_failed", 0);
  }
#endif
}
