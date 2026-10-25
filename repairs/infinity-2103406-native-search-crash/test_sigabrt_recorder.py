#!/usr/bin/env python3
"""Build-independent safety gates for the 2103406 native recorder delta."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("recorder_patch",ROOT/"sigabrt_tombstone_forwarding_fix.py")
MODULE=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=MODULE
SPEC.loader.exec_module(MODULE)
ORIGINAL=ROOT.parent/"infinity-2103402-final/native-overlay/infinity_crash_recorder.c"

class SignalRecorderChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=ORIGINAL.read_bytes()
        cls.after=MODULE.apply(cls.before)
    def test_exact_signed_baseline_source(self):
        self.assertEqual(MODULE.git_blob_sha1(self.before),MODULE.ORIGINAL_GIT_BLOB_SHA1)
    def test_one_reversible_signal_registration_edit(self):
        orig=MODULE.BEFORE.encode()
        replaced=MODULE.AFTER.encode()
        self.assertEqual(self.before.count(orig),1)
        self.assertEqual(self.after.count(replaced),1)
        self.assertEqual(self.after.replace(replaced,orig,1),self.before)
    def test_android_abort_not_intercepted_anymore(self):
        line=self.after.split(b"static const int g_signals[]",1)[1].split(b";",1)[0]
        self.assertNotIn(b"SIGABRT",line)
        for retained in (b"SIGSEGV",b"SIGBUS",b"SIGILL",b"SIGFPE"):
            self.assertIn(retained,line)
        self.assertIn(b"sigaction(g_signals[i], &action, &g_previous[i])",self.after)
        # No extra direct SIGABRT handler registration may exist.
        self.assertNotIn(b"sigaction(SIGABRT",self.after)
    def test_original_health_diagnostics_unchanged(self):
        for token in (b"native-crash-last.txt",b"native-maps-%d.txt",
                      b"lifecycle-breadcrumbs.jsonl",b"fault_address=",
                      b"native_engine_sha256=",b"native.sigsegv."):
            self.assertIn(token,self.after)
    def test_compiled_host_signal_table(self):
        # Compile one TU including exactly the patched C. The constructor
        # refuses to run outside the Infinity Android application process;
        # main inspects g_signals without installing signal handlers.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            c_file=root/"recorder.c"
            c_file.write_bytes(self.after)
            harness=root/"test.c"
            harness.write_text(
                '#include "recorder.c"\n'
                'int main(void) {\n'
                '  if (signal_index(SIGABRT) != -1) return 11;\n'
                '  if (signal_index(SIGSEGV) < 0) return 12;\n'
                '  if (signal_index(SIGBUS) < 0) return 13;\n'
                '  if (signal_index(SIGILL) < 0) return 14;\n'
                '  if (signal_index(SIGFPE) < 0) return 15;\n'
                '  return 0;\n'
                '}\n',encoding="utf-8")
            cc=os.environ.get("HOST_CC","cc")
            subprocess.run([cc,"-std=gnu11","-O2","-pthread",str(harness),"-o",str(root/"test")],check=True)
            subprocess.run([str(root/"test")],check=True)
    def test_rejects_wrong_or_modified_source(self):
        with self.assertRaisesRegex(RuntimeError,"audited baseline"):
            MODULE.apply(self.before+b"\n")
        with self.assertRaisesRegex(RuntimeError,"audited baseline"):
            MODULE.apply(self.before.replace(MODULE.BEFORE.encode(),b"other"))
if __name__ == "__main__":
    unittest.main(verbosity=2)
