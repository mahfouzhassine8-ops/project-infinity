"""Real Linux signal regression, not Android debuggerd/ARM64 acceptance."""
import os
from pathlib import Path
import signal
import struct
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

import crash_context_scope as scope

HARNESS = r'''
#include <sys/mman.h>
#include <sys/resource.h>
#include <string.h>
static void* fault_begin;
static void* fault_end;
static void* fault_address;
static int expected_signal;
static int expected_code;
static int queued;
static void previous(int sig, siginfo_t* info, void* opaque) {
  int report[6];
  ucontext_t* uc = (ucontext_t*)opaque;
#if defined(__x86_64__)
  uintptr_t pc = (uintptr_t)uc->uc_mcontext.gregs[REG_RIP];
#elif defined(__aarch64__)
  uintptr_t pc = (uintptr_t)uc->uc_mcontext.pc;
#else
#error Unsupported host signal test architecture
#endif
  report[0] = sig == expected_signal;
  report[1] = info->si_code == expected_code;
  report[2] = queued ? info->si_value.sival_int == 902 : info->si_addr == fault_address;
  report[3] = queued ? 1 : pc >= (uintptr_t)fault_begin && pc < (uintptr_t)fault_end;
  struct sigaction active;
  sigaction(sig, NULL, &active);
  report[4] = !!(active.sa_flags & SA_SIGINFO);
  sigset_t blocked;
  sigprocmask(SIG_BLOCK, NULL, &blocked);
  report[5] = sigismember(&blocked, SIGUSR2);
  (void)write(STDOUT_FILENO, report, sizeof(report));
}
static void legacy(int sig) { (void)write(STDOUT_FILENO, &sig, sizeof(sig)); }
int main(int argc, char** argv) {
  struct rlimit no_core = {0,0}; setrlimit(RLIMIT_CORE, &no_core);
#ifdef CANDIDATE
  if (argc == 2 && !strcmp(argv[1], "owner")) return infinity_owned_process() ? 0 : 33;
#endif
  if (argc < 3) return 90;
  expected_signal = !strcmp(argv[1], "bus") ? SIGBUS : SIGABRT;
  queued = expected_signal == SIGABRT;
  expected_code = queued ? SI_QUEUE : BUS_ADRERR;
  struct sigaction old = {0}, action = {0};
  old.sa_flags = SA_SIGINFO;
  old.sa_sigaction = previous;
  sigemptyset(&old.sa_mask); sigaddset(&old.sa_mask, SIGUSR2);
  if (!strcmp(argv[2], "default")) { old.sa_handler=SIG_DFL; old.sa_flags=0; }
  if (!strcmp(argv[2], "ignore")) { old.sa_handler=SIG_IGN; old.sa_flags=0; }
  if (!strcmp(argv[2], "legacy")) { old.sa_handler=legacy; old.sa_flags=0; }
  if (sigaction(expected_signal, &old, NULL)) return 91;
  action.sa_flags = SA_SIGINFO; action.sa_sigaction = crash_handler;
  sigemptyset(&action.sa_mask);
  if (sigaction(expected_signal, &action, &g_previous[signal_index(expected_signal)])) return 92;
  if (argc > 3) snprintf(g_crash_path, sizeof(g_crash_path), "%s", argv[3]);
  if (queued) { union sigval value; value.sival_int=902; sigqueue(getpid(), SIGABRT, value); }
  else {
    char path[] = "/tmp/infinity-context-test-XXXXXX";
    int fd=mkstemp(path); unlink(path);
    if(fd<0) return 93;
    long size=sysconf(_SC_PAGESIZE);
    if(ftruncate(fd, size)) return 94;
    char* map=mmap(NULL, size*2, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if(map==MAP_FAILED)return 95;
    fault_address=map+size;
    fault_begin=&&fault; fault_end=&&after;
fault:
    (void)*(volatile char*)fault_address;
after:
    return 96;
  }
  return 97;
}
'''


class CrashContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.original = scope.original_source()
        cls.after = scope.transform(cls.original)
        for name, data in [('baseline', cls.original), ('candidate', cls.after)]:
            code = cls.root / (name + '.c')
            code.write_bytes(data + b'\n#include <stdlib.h>\n' + HARNESS.encode())
            command = ['gcc', '-std=gnu11', '-O0', '-fno-omit-frame-pointer', '-pthread',
                       str(code), '-o', str(cls.root / name)]
            if name == 'candidate': command.insert(1, '-DCANDIDATE')
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if result.returncode: raise AssertionError(result.stderr)

    def run_child(self, name, *args, process_name=None):
        path = str(self.root / name)
        return subprocess.run([process_name or path, *args], executable=path,
                              capture_output=True, timeout=4)

    def test_real_sigbus_retains_original_fault_context(self):
        old = self.run_child('baseline', 'bus', 'context')
        new = self.run_child('candidate', 'bus', 'context')
        self.assertEqual(struct.unpack('6i', old.stdout)[:4], (1, 0, 0, 0))
        self.assertEqual(struct.unpack('6i', new.stdout), (1, 1, 1, 1, 1, 1))
        self.assertEqual(new.returncode, -signal.SIGBUS)
        # One report only: no re-entry into the previous handler after it returns.
        self.assertEqual(len(new.stdout), 24)

    def test_queued_abort_payload_survives_and_still_terminates(self):
        old = self.run_child('baseline', 'abort', 'context')
        new = self.run_child('candidate', 'abort', 'context')
        self.assertEqual(struct.unpack('6i', old.stdout)[1:3], (0, 0))
        self.assertEqual(struct.unpack('6i', new.stdout), (1, 1, 1, 1, 1, 1))
        self.assertEqual(new.returncode, -signal.SIGABRT)

    def test_legacy_default_ignore_and_failed_record_preserve_fatal_policy(self):
        for mode in ('legacy', 'default', 'ignore'):
            with self.subTest(mode=mode):
                old = self.run_child('baseline', 'bus', mode)
                new = self.run_child('candidate', 'bus', mode)
                self.assertEqual((new.returncode, new.stdout), (old.returncode, old.stdout))
                self.assertIn(new.returncode, (-signal.SIGBUS, 128 + signal.SIGBUS))
        new = self.run_child('candidate', 'bus', 'context', str(self.root / 'absent' / 'record'))
        self.assertEqual(new.returncode, -signal.SIGBUS)
        self.assertEqual(struct.unpack('6i', new.stdout), (1, 1, 1, 1, 1, 1))

    def test_exact_process_ownership(self):
        for name, expected in [('com.projectinfinity.kodi:kodi', 0),
                               ('com.projectinfinity.kodi', 33),
                               ('com.projectinfinity.kodi:kodi-other', 33),
                               ('unrelated.process', 33)]:
            with self.subTest(process=name):
                self.assertEqual(self.run_child('candidate', 'owner', process_name=name).returncode, expected)

    def test_original_source_and_signed_executable_boundary(self):
        with ZipFile(os.environ['INFINITY_BASELINE_APK']) as z:
            recorder = z.read('lib/arm64-v8a/libinfinitycrash.so')
        scope.verify_signed_recorder(recorder)
        self.assertRaises(ValueError, scope.verify_signed_recorder, recorder + b'!')
        self.assertRaises(ValueError, scope.transform, self.original + b'!')
        restored = self.after
        for before, after in reversed(scope.CHANGES):
            restored = restored.replace(after.encode(), before.encode(), 1)
        self.assertEqual(restored, self.original)
        candidate = scope.ROOT / 'native-overlay/infinity_crash_recorder.c'
        self.assertEqual(candidate.read_bytes(), self.after)


if __name__ == '__main__':
    unittest.main(verbosity=2)
