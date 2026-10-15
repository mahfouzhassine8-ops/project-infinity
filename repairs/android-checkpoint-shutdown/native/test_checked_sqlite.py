#!/usr/bin/env python3
"""Run exact production transaction bodies against the real host SQLite engine."""
import argparse
import ctypes.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import checked_sqlite

HERE = Path(__file__).resolve().parent
SOURCE = None
FUNCTIONS = {
    checked_sqlite.SQLITE: [
        "void SqliteDatabase::start_transaction()",
        "void SqliteDatabase::commit_transaction()",
        "void SqliteDatabase::rollback_transaction()",
    ],
    checked_sqlite.DATABASE: ["bool CDatabase::CommitTransaction()"],
}


def extract_function(source, signature):
    if source.count(signature) != 1:
        raise ValueError("Nonunique production function: " + signature)
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    # These four guarded functions contain no braces in literals/comments.
    while depth:
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
        end += 1
    return source[start:end]


def compile_and_run(files, root):
    functions = []
    for name, signatures in FUNCTIONS.items():
        source = files[name].decode()
        functions.extend(extract_function(source, signature) for signature in signatures)
    template = (HERE / "sqlite_transactions_test.cpp.in").read_text()
    assert template.count("// @PRODUCTION_FUNCTIONS@") == 1
    code = template.replace("// @PRODUCTION_FUNCTIONS@", "\n\n".join(functions))
    cpp, executable = root / "production-transactions.cpp", root / "production-transactions"
    cpp.write_text(code)
    library = ctypes.util.find_library("sqlite3")
    if not library:
        raise RuntimeError("Real SQLite library is required; this test never substitutes SQLite")
    linker = library if Path(library).is_absolute() else "-l:" + library
    subprocess.run([
        "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-Wconversion", "-Wshadow",
        str(cpp), linker, "-o", str(executable),
    ], check=True)
    return subprocess.run([str(executable), str(root)], text=True, capture_output=True, timeout=15)


class CheckedSQLiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SOURCE is None:
            raise RuntimeError("--source-root is mandatory; do not silently skip production verification")
        cls.originals = {name: (SOURCE / name).read_bytes() for name in checked_sqlite.PREIMAGES}
        cls.patched = checked_sqlite.prepare(SOURCE)

    def test_actual_patched_production_functions_against_real_sqlite(self):
        with tempfile.TemporaryDirectory(prefix="checked-sqlite-patched-") as tmp:
            result = compile_and_run(self.patched, Path(tmp))
            print(result.stdout, end="", flush=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.count("PASS "), 9)

    def test_original_production_functions_reproduce_regressions(self):
        with tempfile.TemporaryDirectory(prefix="checked-sqlite-original-") as tmp:
            result = compile_and_run(self.originals, Path(tmp))
            self.assertNotEqual(result.returncode, 0, "Original source unexpectedly passed")
            self.assertIn("PASS ordinary_commit_and_rollback", result.stdout)
            self.assertIn("FAIL busy_commit_retains_transaction_and_retry_persists", result.stdout)
            self.assertIn("FAIL busy_begin_does_not_claim_active_transaction", result.stdout)
            self.assertIn("FAIL rollback_error_preserves_actual_transaction", result.stdout)
            self.assertIn("FAIL missing_or_inactive_connection_rejects", result.stdout)
            print("PASS original 3334 functions reproduce the transaction reporting defects", flush=True)

    def test_preimage_and_output_guards_preserve_parent(self):
        with tempfile.TemporaryDirectory(prefix="checked-sqlite-guards-") as tmp:
            root = Path(tmp)
            source, output = root / "parent", root / "overlay"
            for name, data in self.originals.items():
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            receipt = checked_sqlite.create_overlay(source, output)
            self.assertEqual(set(receipt["postimages"]), set(checked_sqlite.PREIMAGES))
            self.assertFalse(receipt["normal_close_route_activated"])
            self.assertFalse(receipt["safe_to_terminate_implemented"])
            for name, original in self.originals.items():
                self.assertEqual((source / name).read_bytes(), original)
                self.assertEqual((output / name).read_bytes(), self.patched[name])
                with self.assertRaises(ValueError):
                    checked_sqlite.transform(name, self.patched[name])
            with self.assertRaises(ValueError):
                checked_sqlite.create_overlay(source, source)
            with self.assertRaises(ValueError):
                checked_sqlite.create_overlay(source, source / "nested-overlay")
            with self.assertRaises(ValueError):
                checked_sqlite.create_overlay(source, output)
            shutil.rmtree(output)
            (source / checked_sqlite.SQLITE).write_bytes(self.originals[checked_sqlite.SQLITE] + b"\n")
            with self.assertRaises(ValueError):
                checked_sqlite.create_overlay(source, output)
            self.assertFalse(output.exists(), "Mismatch produced a partial overlay")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args, rest = parser.parse_known_args()
    SOURCE = args.source_root.resolve()
    unittest.main(argv=["test_checked_sqlite.py", *rest], verbosity=2)
