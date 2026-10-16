#!/usr/bin/env python3
"""Negative control: actual JVM buffered output against the production ledger.

This is not Android device acceptance and never authorizes APK delivery. It
records whether ordinary Java output can change a native-sealed essential file.
No protection flag, fake write receipt, Python hook or second ledger is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
CPP = r'''
#include "InfinityProtectedWrites.h"
#include <cassert>
#include <cstdlib>
#include <string>

// JNI's unused environment/class pointers and unsigned-byte boolean ABI.
// No Java VM internals or test hooks are installed in the application.
extern "C" unsigned char Java_BufferBoundary_seed(void*, void*) {
  const std::string path = std::string(std::getenv("INFINITY_JAVA_BOUNDARY_ROOT")) + "/profile/state";
  InfinityScriptPersistence::ProtectedOperation write(-1, {path}, "native_seed");
  if (!write) return 0;
  const int fd = ::open(path.c_str(), O_CREAT | O_WRONLY | O_TRUNC | O_CLOEXEC, 0600);
  if (fd < 0) return 0;
  const bool saved = ::write(fd, "verified", 8) == 8 && ::fsync(fd) == 0;
  return ::close(fd) == 0 && saved;
}
extern "C" unsigned char Java_BufferBoundary_seal(void*, void*) {
  const std::string root = std::getenv("INFINITY_JAVA_BOUNDARY_ROOT");
  return InfinityScriptPersistence::BeginWriteProtection(29, {root + "/profile"}, {root + "/cache"}) &&
      InfinityScriptPersistence::CloseParticipantWrites(29) &&
      InfinityScriptPersistence::SealEssentialWrites(29) &&
      InfinityScriptPersistence::EssentialWritesAuthorized(29);
}
extern "C" unsigned char Java_BufferBoundary_authorized(void*, void*) {
  return InfinityScriptPersistence::EssentialWritesAuthorized(29);
}
'''
JAVA = r'''
import java.io.BufferedOutputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class BufferBoundary {
  static native boolean seed();
  static native boolean seal();
  static native boolean authorized();
  public static void main(String[] args) throws Exception {
    System.load(args[0]);
    if (!seed()) throw new AssertionError("Actual native seed save failed");
    Path state = Path.of(System.getenv("INFINITY_JAVA_BOUNDARY_ROOT"), "profile", "state");
    try (FileOutputStream raw = new FileOutputStream(state.toFile(), true);
         BufferedOutputStream buffer = new BufferedOutputStream(raw)) {
      buffer.write("-pending-java".getBytes(StandardCharsets.UTF_8));
      if (!Files.readString(state).equals("verified"))
        throw new AssertionError("Buffered bytes reached disk before the test seal");
      boolean accepted = seal();
      buffer.flush();
      raw.getFD().sync();
      boolean changed = Files.readString(state).equals("verified-pending-java");
      boolean stillAccepted = authorized();
      System.out.println("{\"native_authorized_before_java_flush\":" + accepted +
          ",\"actual_protected_bytes_changed\":" + changed +
          ",\"native_authorized_after_java_flush\":" + stillAccepted + "}");
      if (!accepted || !changed || !stillAccepted)
        throw new AssertionError("Expected unresolved Java boundary was not reproduced; inspect before updating evidence");
    }
  }
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    runtime = HERE/'runtime/xbmc/platform/android/activity'
    with tempfile.TemporaryDirectory(prefix='infinity-java-boundary-') as temporary:
        root = Path(temporary)
        for name in ('profile', 'cache'):
            (root/name).mkdir()
        (root/'boundary.cpp').write_text(CPP)
        (root/'BufferBoundary.java').write_text(JAVA)
        library = root/'libboundary.so'
        subprocess.run(['g++', '-std=c++17', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-pthread', '-I'+str(runtime), str(root/'boundary.cpp'), '-o', str(library)], check=True)
        subprocess.run(['java', 'com.sun.tools.javac.Main', '-d', str(root),
                        str(root/'BufferBoundary.java')], check=True)
        result = subprocess.run(['java', '-cp', str(root), 'BufferBoundary', str(library)],
                                env=dict(os.environ, INFINITY_JAVA_BOUNDARY_ROOT=str(root)),
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise RuntimeError(result.stdout+result.stderr)
        observed = json.loads(result.stdout)
        report = dict(scope='production native ledger in actual host JVM with real buffered file writes; not Android process evidence',
                      negative_control_reproduced=True, observation=observed,
                      production_header_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                                for p in (runtime/'InfinityProtectedWrites.h', runtime/'InfinityScriptPersistence.h')},
                      android_process_death_verified=False, apk_deliverable=False,
                      required_correction='Join actual Android Java write admission, buffered output and preference durability to the existing checkpoint before whole-package exit.')
        args.out.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
