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
#define INFINITY_NATIVE_ENGINE_SHA "db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375"

static int g_crash_fd = -1;
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
  return append_char(out, cap, at, '
');
}

static size_t append_kv_hex(char* out, size_t cap, size_t at, const char* key, uintptr_t value)
{
  at = append_str(out, cap, at, key);
  at = append_hex(out, cap, at, value);
  return append_char(out, cap, at, '
');
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

static void crash_handler(int sig, siginfo_t* info, void* opaque)
{
  pid_t tid = (pid_t)syscall(__NR_gettid);
  if (g_handling) restore_and_reraise(sig, tid);
  g_handling = 1;

  if (g_crash_fd >= 0) {
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
    at = append_str(out, sizeof(out), at, "arch=aarch64
");
    at = append_str(out, sizeof(out), at, "native_engine_sha256=" INFINITY_NATIVE_ENGINE_SHA "
");

    if (at > sizeof(out)) at = sizeof(out);
    (void)write(g_crash_fd, out, at);
    (void)fsync(g_crash_fd);
  }

  restore_and_reraise(sig, tid);
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

__attribute__((constructor))
static void infinity_crash_recorder_install(void)
{
#if !defined(__aarch64__)
  return;
#else
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
  g_crash_fd = open(crash_path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);

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
      g_previous[i].sa_handler = SIG_DFL;
      sigemptyset(&g_previous[i].sa_mask);
      g_previous[i].sa_flags = 0;
    }
  }
#endif
}
