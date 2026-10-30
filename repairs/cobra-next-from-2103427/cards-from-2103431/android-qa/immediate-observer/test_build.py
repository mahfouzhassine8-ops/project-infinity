"""Selected host-only builder controls; does not compile or run an observer."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("immediate_observer_builder", HERE / "build.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def dex_with_descriptor(descriptor):
    # Minimal table fixture for the descriptor reader only, never runnable DEX.
    data = descriptor.encode("ascii")
    raw = bytearray(152 + 1 + len(data) + 1)
    raw[:8] = b"dex\n035\0"
    struct.pack_into("<III", raw, 32, len(raw), 112, 0x12345678)
    struct.pack_into("<II", raw, 56, 1, 112)
    struct.pack_into("<II", raw, 64, 1, 116)
    struct.pack_into("<II", raw, 96, 1, 120)
    struct.pack_into("<I", raw, 112, 152)
    raw[152] = len(data)
    raw[153:153 + len(data)] = data
    return bytes(raw)


class BuildControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.android = self.root / "android.jar"
        self.d8 = self.root / "d8.jar"
        self.source = self.root / "CobraImmediateHierarchy.java"
        self.android.write_bytes(b"mock Android SDK")
        self.d8.write_bytes(b"mock D8")
        self.source.write_text("package qa; public final class CobraImmediateHierarchy {}")

    def test_wrong_actual_sdk_pin_fails_before_output_or_compilation(self):
        out = self.root / "out"
        with patch.object(builder.subprocess, "run") as run:
            with self.assertRaisesRegex(AssertionError, "Pinned official Android34"):
                builder.build(self.android, self.d8, out)
        run.assert_not_called()
        self.assertFalse(out.exists())

    def test_wrong_d8_pin_fails_before_source_is_trusted(self):
        with patch.object(builder, "ANDROID_SHA256", builder.digest(self.android)):
            with self.assertRaisesRegex(AssertionError, "Pinned official SDK35"):
                builder.verify_inputs(self.android, self.d8, self.source)

    def test_forbidden_idle_or_permission_method_reflection_fails_closed(self):
        for method in ("waitForIdle", "injectInputEvent", "adoptShellPermissionIdentity", "setHiddenApiExemptions"):
            with self.subTest(method=method):
                self.source.write_text('package qa; public final class CobraImmediateHierarchy { void f(){ c.getMethod("' + method + '"); }}')
                with patch.object(builder, "ANDROID_SHA256", builder.digest(self.android)), patch.object(builder, "D8_SHA256", builder.digest(self.d8)):
                    with self.assertRaisesRegex(AssertionError, "Forbidden observer API"):
                        builder.verify_inputs(self.android, self.d8, self.source)

    def test_actual_class_definition_reader_distinguishes_own_and_foreign(self):
        self.assertEqual([builder.OWN_DESCRIPTOR], builder.dex_descriptors(dex_with_descriptor(builder.OWN_DESCRIPTOR)))
        foreign = builder.dex_descriptors(dex_with_descriptor("Landroid/app/UiAutomation;"))
        self.assertNotEqual([builder.OWN_DESCRIPTOR], foreign)
        with self.assertRaisesRegex(AssertionError, "DEX header"):
            builder.dex_descriptors(b"not a dex")
        with self.assertRaisesRegex(AssertionError, "Truncated DEX table"):
            raw = bytearray(dex_with_descriptor(builder.OWN_DESCRIPTOR))
            struct.pack_into("<II", raw, 96, 2, 120)
            builder.dex_descriptors(bytes(raw))

    def test_transport_jar_is_deterministic_and_contains_only_supplied_dex(self):
        a, b = self.root / "a.jar", self.root / "b.jar"
        members = {"classes.dex": b"explicit QA DEX bytes"}
        builder.write_jar(a, members)
        builder.write_jar(b, members)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with zipfile.ZipFile(a) as archive:
            self.assertEqual(["classes.dex"], archive.namelist())
            self.assertEqual((1980, 1, 1, 0, 0, 0), archive.getinfo("classes.dex").date_time)


if __name__ == "__main__":
    unittest.main()
