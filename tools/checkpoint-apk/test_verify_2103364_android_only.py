#!/usr/bin/env python3
"""Regression checks for the Android-only 2103364 preservation comparator."""
import io
import unittest
import zipfile
from unittest.mock import patch
import verify_2103364_android_only as v

def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return zipfile.ZipFile(io.BytesIO(output.getvalue()))

class ComparatorTests(unittest.TestCase):
    def setUp(self):
        self.before = {
            "AndroidManifest.xml": b"before",
            "classes.dex": b"classes",
            "lib/arm64-v8a/libkodi.so": b"engine",
            "assets/infinity/checkpoint-controller-20.zip": b"scripts",
            "assets/skin.infinity.diggz/addon.xml": b"skin",
        }
        self.after = dict(self.before)
        self.after["AndroidManifest.xml"] = b"after"
        self.after["classes.dex"] = b"new classes"

    def compare(self):
        with archive(self.before) as a, archive(self.after) as b, patch.object(
            v, "dex_contract", return_value=({"jni"}, {"Lcom/projectinfinity/kodi/Main;"})
        ):
            return v.compare(a, b)

    def test_allows_only_android_code(self):
        self.assertEqual(self.compare()["baseline_version"], 2103364)

    def test_rejects_native_drift(self):
        self.after["lib/arm64-v8a/libkodi.so"] = b"bad"
        with self.assertRaises(RuntimeError):
            self.compare()

    def test_rejects_script_drift(self):
        self.after["assets/infinity/checkpoint-controller-20.zip"] = b"changed"
        with self.assertRaises(RuntimeError):
            self.compare()

    def test_rejects_skin_drift(self):
        self.after["assets/skin.infinity.diggz/addon.xml"] = b"changed"
        with self.assertRaises(RuntimeError):
            self.compare()

    def test_rejects_new_payload(self):
        self.after["assets/unknown"] = b"new"
        with self.assertRaises(RuntimeError):
            self.compare()

if __name__ == "__main__":
    unittest.main(verbosity=2)
