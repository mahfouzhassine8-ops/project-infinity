"""Correction 9 only: preserve the original fatal context for Android diagnostics.

Staging is not ARM64/Android acceptance. The signed recorder's executable bytes
must match the historical source producer after reversing its engine-SHA field.
No Kodi engine, shutdown policy, provider or unrelated process is modified.
"""
import base64
import gzip
import hashlib
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT.parent / 'native-crash-forensics-2103250/infinity_crash_recorder.c.gz.b64'
SOURCE_SHA = 'b314c9f715d5cc6a30dcc34cf85268860d0a4cb66d830588fe3ee99e6c77c7a7'
RECORDER_SHA = 'bc7aab86fc97844e02e25c96fc73f269bc85f5f8ce5528e132a78841aa130bca'
HISTORICAL_RECORDER_SHA = '19f017612d9447503ef8957d2ad82266631150c98454359789bdf6f547f4b3df'
OLD_ENGINE = 'db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
ENGINE = '704834f42e49a2eea0a36ad41b5f79345f5e4108dcd339213899ea3c6ff045a0'

HELPER = '''static void crash_handler(int sig, siginfo_t* info, void* opaque);

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

'''

OWNER = '''static int infinity_owned_process(void)
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

'''

CHANGES = [
    ('static void crash_handler(int sig, siginfo_t* info, void* opaque)\n{',
     HELPER + 'static void crash_handler(int sig, siginfo_t* info, void* opaque)\n{'),
    ('  restore_and_reraise(sig, tid);\n}\n\nstatic uintptr_t action_address',
     '  forward_original_signal(sig, tid, info, opaque);\n}\n\nstatic uintptr_t action_address'),
    ('__attribute__((constructor))\nstatic void infinity_crash_recorder_install',
     OWNER + '__attribute__((constructor))\nstatic void infinity_crash_recorder_install'),
    ('#else\n  char diag_dir[PATH_MAX];',
     '#else\n  if (!infinity_owned_process()) return;\n  char diag_dir[PATH_MAX];'),
    ('#define INFINITY_NATIVE_ENGINE_SHA "' + OLD_ENGINE + '"',
     '#define INFINITY_NATIVE_ENGINE_SHA "' + ENGINE + '"'),
]


def original_source():
    value = gzip.decompress(base64.b64decode(SOURCE.read_bytes()))
    if hashlib.sha256(value).hexdigest() != SOURCE_SHA:
        raise ValueError('Unknown original recorder source')
    return value


def verify_signed_recorder(value):
    if hashlib.sha256(value).hexdigest() != RECORDER_SHA:
        raise ValueError('Unknown signed recorder')
    field = b'native_engine_sha256=' + ENGINE.encode() + b'\n'
    if value.count(field) != 1:
        raise ValueError('Unknown recorder identity field')
    restored = value.replace(field, b'native_engine_sha256=' + OLD_ENGINE.encode() + b'\n', 1)
    if hashlib.sha256(restored).hexdigest() != HISTORICAL_RECORDER_SHA:
        raise ValueError('Original executable changed beyond approved identity field')


def transform(value):
    if hashlib.sha256(value).hexdigest() != SOURCE_SHA:
        raise ValueError('Unknown original recorder source')
    result = value
    for before, after in CHANGES:
        if result.count(before.encode()) != 1:
            raise ValueError('Ambiguous recorder boundary')
        result = result.replace(before.encode(), after.encode(), 1)
    restored = result
    for before, after in reversed(CHANGES):
        restored = restored.replace(after.encode(), before.encode(), 1)
    if restored != value:
        raise ValueError('Unrelated recorder change')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(transform(original_source()))
