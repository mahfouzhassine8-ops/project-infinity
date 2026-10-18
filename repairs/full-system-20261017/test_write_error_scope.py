#!/usr/bin/env python3
"""Host-test real native optional VFS failure proof, with mandatory negatives.

Never compiles/executes a fake coordinator or reports physical Close accepted.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("actual_write_scope",HERE/"write_error_scope_patch.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SOURCES={
 "script":ROOT/"repairs/essential-first-2103377/runtime/xbmc/platform/android/activity/InfinityScriptPersistence.h",
 "writes":HERE/"InfinityProtectedWrites.stagefix.h",
 "bridge":ROOT/"repairs/essential-first-2103377/runtime/xbmc/interfaces/python/InfinityPythonPersistence.h",
 "source":ROOT/"repairs/essential-first-2103377/runtime/xbmc/interfaces/python/InfinityPythonPersistenceSource.h",
}
CASES=(
 "optional", "unscoped", "forged", "wrong-operation", "essential",
 "settings", "pending-essential-txn", "unflushed-essential-buffer",
 "active-essential-operation", "alias-to-essential", "unrelated",
 "mixed-profile-writes",
)

class WriteErrorScopeTests(unittest.TestCase):
    def test_source_patch_is_scoped_and_has_exact_anchors(self):
        after={}
        for kind,path in SOURCES.items():
            old=path.read_text()
            new=module.PATCHES[kind](old)
            self.assertNotEqual(old,new)
            after[kind]=new
        script=after["script"]
        self.assertIn('const std::string& verifiedWriteTarget={}',script)
        self.assertNotIn('reason=="vfs_write_exception" ||',script.split('inline bool AdvisoryFailureReason',1)[1].split('inline void AddBlockerLocked',1)[0])
        writes=after["writes"]
        self.assertIn('live.thread != std::this_thread::get_id()',writes)
        self.assertIn('!p.participants.count(blocker.writerId)',writes)
        self.assertIn('OptionalPathLocked(p, blocker.verifiedWriteTarget)',writes)
        self.assertIn('allWriterPathsOptional && targetWasInventoried',writes)
        bridge=after["bridge"]
        self.assertIn('VerifiedVfsWriteFailureTarget',bridge)
        self.assertIn('PyArg_ParseTuple(args,"s|sz"',bridge)
        py=after["source"]
        self.assertIn("target=self._infinity_path",py)
        self.assertNotIn("self.fail('vfs_write_exception')",py)

    def test_compile_real_native_paths_and_all_negative_cases(self):
        with tempfile.TemporaryDirectory(prefix="infinity-vfs-regressions-") as temp:
            temp=Path(temp)
            for kind,name in [
                ("script","InfinityScriptPersistence.h"),
                ("writes","InfinityProtectedWrites.h"),
            ]:
                (temp/name).write_text(module.PATCHES[kind](SOURCES[kind].read_text()))
            binary=temp/"protection"
            subprocess.run([
               "g++","-std=c++17","-pthread","-Wall","-Wextra","-Werror",
               "-I",str(temp),
               str(HERE/"test_native_scoped_vfs_error.cpp"),
               "-o",str(binary)
            ],check=True,capture_output=True,text=True,timeout=60)
            for name in CASES:
                with self.subTest(name=name):
                    result=subprocess.run([str(binary),name],capture_output=True,
                                          text=True,timeout=25)
                    self.assertEqual(result.returncode,0,
                                     result.stdout+"\n"+result.stderr)
                    self.assertIn("PASS "+name,result.stdout)

if __name__=="__main__":
    unittest.main(verbosity=2)
