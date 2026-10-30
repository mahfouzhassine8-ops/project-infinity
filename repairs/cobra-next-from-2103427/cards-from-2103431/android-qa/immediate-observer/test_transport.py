"""Selected host-only observer controls; every device command is mocked."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import immediate_observer as io
import baseline as qa
import android_probe as probe

BUILD = Path("/workspace/cobra-evidence/cards431-immediate-observer-build-v2")
XML = '<hierarchy rotation="0"><node package="com.projectinfinity.kodi" text="Views" clickable="true" enabled="true" bounds="[-5,0][80,90]" /></hierarchy>'


def completed(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class ObserverTransport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.observer = io.ImmediateObserver(BUILD / "CobraImmediateHierarchy.jar", BUILD / "BUILD-RECEIPT.json", self.folder / "observer")
        self.observer.prepared = True
        self.metadata = {
            "QA_JAR_sha256": self.observer.expected, "application_classpath": io.CLASSPATH,
            "platform_surface": "VERIFIED_PUBLIC_REFLECTION_SURFACE_NO_ACCESS_EXEMPTIONS",
            "actual_public_methods": ["source-verified-public-method"] * 7,
            "OS_JAR_sha256": {"/system/framework/android.test.runner.jar": "a" * 64, "/system/framework/uiautomator.jar": "b" * 64},
            "OS_uiautomator_script_sha256": "c" * 64,
            "OS_script_classpath_line": "CLASSPATH=/system/framework/android.test.runner.jar:${base}/framework/uiautomator.jar",
            "status": "ROOT_CAPTURED", "exit_code": 0, "active_window_revalidated": True,
            "root_package": io.PACKAGE, "window_id": 7, "root_bounds": [0, 0, 100, 100],
            "display_size": [100, 100], "known_notice_root_allowed": False, "rotation": 0,
            "started_uptime_ms": 10, "root_acquire_started_uptime_ms": 11,
            "root_acquired_uptime_ms": 12, "dump_completed_uptime_ms": 13, "finished_uptime_ms": 14,
            "XML_sha256": hashlib.sha256(XML.encode()).hexdigest(), "XML_bytes": len(XML.encode()),
        }
        self.path = "/sdcard/cobra-cards-baseline-123-001.xml"

    def response(self, name, arguments):
        if name.endswith("-capture"):
            return completed(self.metadata["exit_code"], stderr="native root diagnostic" if self.metadata["exit_code"] else "")
        if name.endswith("-metadata-read"):
            return completed(stdout=json.dumps(self.metadata))
        if name.endswith("-missing-check"):
            return completed(1)
        if name.endswith("-nonempty-check"):
            return completed()
        if name.endswith("-XML-read"):
            return completed(stdout=XML)
        self.fail("Unexpected command: " + name)

    def capture(self, **kwargs):
        with patch.object(self.observer, "command", side_effect=self.response):
            return self.observer.capture("001-test", self.path, **kwargs)

    def test_success_reads_only_unique_current_xml_and_keeps_native_binding(self):
        raw, metadata, started = self.capture()
        self.assertEqual(XML, raw)
        self.assertEqual(7, metadata["window_id"])
        self.assertEqual(started, self.observer.last["started"])

    def test_preflight_required_before_any_observer_command(self):
        self.observer.prepared = False
        with patch.object(self.observer, "command") as command, self.assertRaisesRegex(AssertionError, "preflight"):
            self.observer.capture("001-test", self.path)
        command.assert_not_called()

    def test_device_preflight_failure_cannot_set_prepared(self):
        self.observer.prepared = False
        responses = [completed(), completed(stdout=self.observer.expected + "  path"), completed(2, stderr="NoSuchMethodException")]
        with patch.object(self.observer, "command", side_effect=responses), self.assertRaisesRegex(AssertionError, "preflight failed.*NoSuchMethodException"):
            self.observer.prepare()
        self.assertFalse(self.observer.prepared)

    def test_pushed_byte_mismatch_stops_before_platform_execution(self):
        self.observer.prepared = False
        with patch.object(self.observer, "command", side_effect=[completed(), completed(stdout="0" * 64)]) as command:
            with self.assertRaisesRegex(AssertionError, "Pushed JAR"):
                self.observer.prepare()
        self.assertEqual(2, command.call_count)

    def test_explicit_null_root_is_optional_miss_only_with_no_retained_xml(self):
        self.metadata.update(status="ROOT_MISSING", exit_code=3, reason="NULL_CURRENT_ACTIVE_ROOT")
        with self.assertRaisesRegex(io.MissingHierarchy, "NULL_CURRENT_ACTIVE_ROOT.*native root diagnostic"):
            self.capture()
        self.assertIsNone(self.observer.last)

    def test_changed_window_is_a_miss_and_not_a_captured_xml_success(self):
        self.metadata.update(status="ROOT_MISSING", exit_code=3, reason="CURRENT_ACTIVE_WINDOW_CHANGED_DURING_DUMP")
        with self.assertRaises(io.MissingHierarchy):
            self.capture()

    def test_missing_platform_method_keeps_exact_native_reason(self):
        self.metadata.update(status="ERROR", exit_code=2, error="java.lang.NoSuchMethodException: exact.method")
        self.metadata.pop("actual_public_methods")
        with self.assertRaisesRegex(AssertionError, "NoSuchMethodException: exact.method"):
            self.capture()

    def test_missing_root_with_transport_error_is_fatal(self):
        self.metadata.update(status="ROOT_MISSING", exit_code=3, reason="NULL_CURRENT_ACTIVE_ROOT")
        original = self.response
        def response(name, arguments):
            return completed(1, stderr="device offline") if name.endswith("-missing-check") else original(name, arguments)
        with patch.object(self.observer, "command", side_effect=response), self.assertRaises(AssertionError):
            self.observer.capture("001-test", self.path)

    def test_wrong_package_window_bounds_or_chronology_is_rejected(self):
        for key, value in [("root_package", "other.application"), ("window_id", -1), ("root_bounds", [0, 0, 0, 1]), ("active_window_revalidated", False), ("root_acquired_uptime_ms", 999)]:
            old = self.metadata[key]
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.metadata[key] = value
                self.capture()
            self.metadata[key] = old

    def test_changed_xml_bytes_rejected(self):
        self.metadata["XML_sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "XML bytes changed"):
            self.capture()

    def test_notice_package_allowance_cannot_leak_into_cards_capture(self):
        self.metadata.update(root_package="android", known_notice_root_allowed=True)
        with self.assertRaises(AssertionError):
            self.capture()

    def test_age_limit_is_strict_and_has_no_clock_conversion(self):
        with patch.object(io.time, "monotonic", return_value=10):
            self.observer.guard_age(6.501)
            with self.assertRaisesRegex(AssertionError, "3.5second"):
                self.observer.guard_age(6.5)

    def test_classpath_inherits_boot_and_never_invokes_legacy_runner(self):
        command = self.observer.launch(["--dump", self.path, self.path[:-4] + ".json", self.observer.expected])
        self.assertIn("CLASSPATH=" + io.CLASSPATH, command)
        self.assertIn("/system/bin/app_process", command)
        self.assertFalse(any(item.startswith("BOOTCLASSPATH=") for item in command))
        self.assertNotIn("runtest", command)

    def test_actual_command_failure_keeps_complete_stdout_stderr(self):
        with patch.object(io.subprocess, "run", return_value=completed(11, "actual out", "actual err")):
            self.observer.command("diagnostic", ["adb", "shell", "example"])
        diagnostic = json.loads((self.observer.out / "diagnostic-command.json").read_text())
        self.assertEqual((11, "actual out", "actual err"), (diagnostic["exit_code"], diagnostic["stdout"], diagnostic["stderr"]))

    def test_fresh_press_is_clipped_to_current_root_and_old_node_rejected(self):
        out = self.folder / "journey"; out.mkdir()
        observation = qa.CardsObservation(out, self.observer)
        with patch.object(self.observer, "capture", return_value=(XML, self.metadata, 8)), patch.object(io.time, "monotonic", return_value=10):
            snap = observation.ui()
            with patch.object(qa, "adb") as adb:
                observation.press(snap.nodes[0], "Views")
            adb.assert_called_once_with("shell", "input", "tap", "40", "45")
            unrelated = qa.Snapshot(XML).nodes[0]
            with self.assertRaisesRegex(AssertionError, "latest current hierarchy"):
                observation.press(unrelated, "old Views")

    def test_expired_press_never_injects_coordinate(self):
        out = self.folder / "journey"; out.mkdir()
        observation = qa.CardsObservation(out, self.observer)
        with patch.object(self.observer, "capture", return_value=(XML, self.metadata, 6.5)), patch.object(io.time, "monotonic", return_value=10):
            snap = observation.ui()
            with patch.object(qa, "adb") as adb, self.assertRaises(AssertionError):
                observation.press(snap.nodes[0], "Views")
            adb.assert_not_called()

    def test_scrolling_clips_container_to_current_root_before_input(self):
        xml = '<hierarchy rotation="0"><node package="com.projectinfinity.kodi" class="android.widget.ScrollView" scrollable="true" bounds="[-40,-20][90,150]" /></hierarchy>'
        out = self.folder / "journey"; out.mkdir()
        observation = qa.CardsObservation(out, self.observer)
        with patch.object(self.observer, "capture", return_value=(xml, self.metadata, 8)), patch.object(io.time, "monotonic", return_value=10), patch.object(qa, "adb") as adb:
            with self.assertRaisesRegex(RuntimeError, "Visible action not observed"):
                observation.tap("absent", sheet_scroll=True, attempts=1)
        adb.assert_called_once_with("shell", "input", "swipe", "45", "70", "45", "30", "350")
        source = (ROOT / "baseline.py").read_text()
        self.assertIn("box = intersect(bounds(observation.grid(snap)), snap.active_bounds)", source)

    def test_known_notice_callback_preserves_exact_guards_and_prepress_age_hook(self):
        xml = '<hierarchy><node package="android" resource-id="android:id/alertTitle" text="Android App Compatibility" /><node package="android" resource-id="android:id/message" text="This app will be run using page size compatible mode. LOAD segment and RELRO segment alignment checks failed. lib/arm64-v8a/libkodi.so" /><node package="android" resource-id="android:id/button2" text="OK" clickable="true" enabled="true" bounds="[10,10][90,90]" /><node package="android" resource-id="android:id/button1" text="Don&apos;t Show Again" /></hierarchy>'
        capture = Mock(side_effect=[xml, xml, XML]); order = []
        with patch.object(probe.subprocess, "run", return_value=completed(stdout=b"\x89PNG\r\n\x1a\n")), patch.object(probe, "adb", side_effect=lambda *args: order.append("input")) as adb:
            result = probe.acknowledge_known_notice_after_launch(
                "Status: ok\nActivity: com.projectinfinity.kodi/.InfinityLiveActivity",
                self.folder / "notice", {"lib/arm64-v8a/libkodi.so"},
                capture_ui=capture, before_notice_press=lambda notice: order.append("age-check"))
        self.assertEqual("KNOWN_NOTICE_ACKNOWLEDGED_ONCE", result["status"])
        self.assertEqual(["age-check", "input"], order)
        self.assertEqual([unittest.mock.call("observed"), unittest.mock.call("fresh-before-OK"), unittest.mock.call("after-OK")], capture.call_args_list)
        adb.assert_called_once_with("shell", "input", "tap", "50", "50")

    def test_unrecognized_android_dialog_remains_fatal_without_press(self):
        xml = '<hierarchy><node package="android" resource-id="android:id/alertTitle" text="Unrecognized dialog" /></hierarchy>'
        with patch.object(probe, "adb") as adb, self.assertRaisesRegex(AssertionError, "Unrecognized Android dialog"):
            probe.acknowledge_known_notice_after_launch(
                "Status: ok\nActivity: com.projectinfinity.kodi/.InfinityLiveActivity",
                self.folder / "notice", set(), capture_ui=lambda name: xml)
        adb.assert_not_called()

    def test_actual_finite_poll_budgets_and_strict_actions_preserved(self):
        out = self.folder / "journey"; out.mkdir()
        observation = qa.CardsObservation(out, self.observer)
        with patch.object(observation, "ui", side_effect=io.MissingHierarchy("missing")) as ui, patch.object(qa.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "Exact Cards"):
                observation.wait_cards()
        self.assertEqual(10, ui.call_count)
        with patch.object(observation, "ui", side_effect=io.MissingHierarchy("missing")) as ui, patch.object(observation, "press") as press:
            with self.assertRaises(io.MissingHierarchy):
                observation.tap("Views")
        self.assertEqual(1, ui.call_count); press.assert_not_called()
        tree = ast.parse((ROOT / "baseline.py").read_text())
        loops = [n for n in ast.walk(tree) if isinstance(n, ast.For) and isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Name) and n.iter.func.id == "range"]
        self.assertTrue(any(ast.dump(n.iter) == ast.dump(ast.parse("range(15)", mode="eval").body) for n in loops))


if __name__ == "__main__":
    unittest.main()
