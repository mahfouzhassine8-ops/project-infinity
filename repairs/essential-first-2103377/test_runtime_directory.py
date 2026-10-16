#!/usr/bin/env python3
"""Compile actual CPosixDirectory::Create with the production write ledger.

The native CI passes its staged Kodi source. Local negative/corrected controls
can apply the production delta to the SHA-pinned original PosixDirectory.cpp.
Only the unrelated Kodi class/URL declarations are host peers; mkdir, stat,
descriptor identity, leases and authorization execute real production code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import apply_runtime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIGNATURE = 'bool CPosixDirectory::Create(const std::string& path)'


def function(text):
    start = text.index(SIGNATURE)
    opening = text.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


CODE = r'''
#include "platform/android/activity/InfinityProtectedWrites.h"
#include <cassert>
#include <iostream>
#include <sys/syscall.h>
namespace InfinityAndroidCheckpoint { bool IsPersistingOnThisThread() { return false; } }
class CPosixDirectory { public: static bool Create(const std::string& path); };
static int mkdirCalls = 0;
static int lastMkdirError = 0;
static std::string failedSync;
extern "C" int mkdir(const char* path, mode_t mode) noexcept {
  ++mkdirCalls;
  const auto result = static_cast<int>(syscall(SYS_mkdir, path, mode));
  lastMkdirError = result ? errno : 0;
  return result;
}
extern "C" int fsync(int fd) {
  char target[PATH_MAX]{};
  const auto descriptor = "/proc/self/fd/" + std::to_string(fd);
  const auto length = ::readlink(descriptor.c_str(), target, sizeof(target)-1);
  if (length > 0 && !failedSync.empty() &&
      std::string(target, static_cast<size_t>(length)) == failedSync)
  { errno = EIO; return -1; }
  return static_cast<int>(syscall(SYS_fsync, fd));
}
// ACTUAL_PRODUCTION_CREATE
namespace Ledger = InfinityScriptPersistence;
static bool tracked(const std::string& path) {
  auto& s = Ledger::Get(); std::lock_guard<std::mutex> lock(s.mutex);
  return s.protection.paths.count(path) && s.protection.writerPaths[37].count(path);
}
int main(int argc, char** argv) {
  assert(argc == 4);
  const std::string mode = argv[1], root = argv[2];
  const bool unfixed = std::string(argv[3]) == "unfixed";
  const auto profile = root+"/profile", cache = root+"/cache";
  const auto created = profile+"/created";
  Ledger::protectedWriteOwner = 37;
  if (mode == "existing-unwritten") {
    // /proc exists and cannot provide file fsync. This tests the operation,
    // not a production path/filesystem exemption. A real mkdir is interposed
    // only to observe its actual syscall result, never to fake success.
    assert(!CPosixDirectory::Create("/proc"));
    if (unfixed) assert(mkdirCalls == 1 && lastMkdirError == EEXIST && tracked("/proc"));
    else assert(mkdirCalls == 0 && !tracked("/proc"));
  } else if (mode == "failed-real-create") {
    assert(!CPosixDirectory::Create("/proc/self/infinity-protected-missing/directory"));
    assert(mkdirCalls > 0);
    assert(tracked("/proc/self/infinity-protected-missing/directory"));
  } else if (mode != "sealed-create") {
    assert(CPosixDirectory::Create(created));
    assert(tracked(created));
    struct stat st{}; assert(::stat(created.c_str(), &st) == 0 && S_ISDIR(st.st_mode));
    if (mode == "created-fsync-failure" || mode == "created-then-existing") failedSync = created;
    if (mode == "parent-fsync-failure") failedSync = profile;
    if (mode == "created-then-existing") {
      assert(!CPosixDirectory::Create(created));
      assert(tracked(created)); // An existing-directory query cannot erase a prior real write.
    }
  }
  assert(Ledger::BeginWriteProtection(81, {profile}, {cache}));
  assert(Ledger::CloseParticipantWrites(81));
  const bool expected = mode == "created-durable" || mode == "sealed-create" ||
                        (mode == "existing-unwritten" && !unfixed);
  const bool sealed = Ledger::SealEssentialWrites(81);
  assert(sealed == expected);
  assert(Ledger::EssentialWritesAuthorized(81) == expected);
  if (mode == "sealed-create") {
    assert(!CPosixDirectory::Create(created));
    struct stat st{}; assert(::stat(created.c_str(), &st) != 0 && errno == ENOENT);
    assert(mkdirCalls == 0); // Rejected at the real admission boundary.
    assert(Ledger::EssentialWritesAuthorized(81));
  }
  const auto proof = Ledger::EssentialWrites();
  std::cout << "case=" << mode << "; mkdir_calls=" << mkdirCalls
            << "; mkdir_errno=" << lastMkdirError << "; sealed=" << sealed
            << "; authorized=" << Ledger::EssentialWritesAuthorized(81) << '\n';
  for (const auto& blocker : proof.blockers) std::cout << blocker << '\n';
}
'''


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--runtime', type=Path)
    source.add_argument('--locked-source', type=Path)
    parser.add_argument('--expect-unfixed', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.runtime:
        text = (args.runtime/apply_runtime.DIRECTORY).read_text()
    else:
        text = args.locked_source.read_text()
        assert hashlib.sha256(text.encode()).hexdigest() == apply_runtime.PINS[apply_runtime.DIRECTORY]
        text = apply_runtime.directory(text)
    actual = function(text)
    includes = [HERE/'runtime/xbmc', ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc']
    cases = ['existing-unwritten', 'created-durable', 'created-fsync-failure',
             'parent-fsync-failure', 'created-then-existing', 'failed-real-create', 'sealed-create']
    with tempfile.TemporaryDirectory(prefix='infinity-native-directory-') as tmp:
        folder = Path(tmp)
        source = folder/'test.cpp'; binary = folder/'test'
        source.write_text(CODE.replace('// ACTUAL_PRODUCTION_CREATE', actual))
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                        '-DTARGET_ANDROID', *['-I'+str(p) for p in includes],
                        str(source), '-o', str(binary)], check=True)
        results = []
        for case in cases:
            root = folder/case
            (root/'profile').mkdir(parents=True); (root/'cache').mkdir()
            result = subprocess.run([str(binary), case, str(root), 'unfixed' if args.expect_unfixed else 'corrected'],
                                    capture_output=True, text=True, timeout=10)
            results.append(dict(case=case, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
            print(case, result.returncode, result.stdout, result.stderr, flush=True)
    report = dict(scope='actual patched CPosixDirectory::Create and production write ledger; host filesystem',
                  expected_unfixed=args.expect_unfixed, production_function_sha256=hashlib.sha256(actual.encode()).hexdigest(),
                  results=results, all_passed=all(row['exit_code'] == 0 for row in results),
                  android_process_death_verified=False, physical_fold_accepted=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    if not report['all_passed']: raise SystemExit(1)


if __name__ == '__main__':
    main()
