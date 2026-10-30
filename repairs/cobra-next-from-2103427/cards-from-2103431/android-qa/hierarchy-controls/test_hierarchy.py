"""Focused host-only controls for the Cards QA observer; all ADB is mocked."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "baseline.py"
SPEC = importlib.util.spec_from_file_location("cards_baseline_qa_under_test", SOURCE)
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)
XML = '<hierarchy><node package="com.projectinfinity.kodi" text="Cards QA 00001, programme" bounds="[0,0][100,100]" /></hierarchy>'


def completed(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class HierarchyControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)
        self.observation = qa.CardsObservation(self.out)

    def test_code_zero_without_xml_records_failure_and_never_cats(self):
        with patch.object(qa.subprocess, "run", side_effect=[completed(stdout="ERROR: null root"), completed(1)]), patch.object(qa, "adb") as adb:
            with self.assertRaisesRegex(qa.MissingHierarchy, "No fresh nonempty hierarchy"):
                self.observation.ui("transition")
        adb.assert_not_called()
        saved = json.loads((self.out / "001-transition-dump.json").read_text())
        self.assertEqual(0, saved["exit_code"])
        self.assertEqual("ERROR: null root", saved["stdout"])
        self.assertEqual(1, saved["nonempty_check_exit_code"])
        self.assertEqual("NO_FRESH_NONEMPTY_XML", self.observation.events[0]["reason"])

    def test_failed_dump_command_remains_fatal_with_original_stderr(self):
        with patch.object(qa.subprocess, "run", return_value=completed(23, "stdout", "actual transport error")) as run, patch.object(qa, "adb") as adb:
            with self.assertRaisesRegex(RuntimeError, "failed \\(23\\).*actual transport error") as error:
                self.observation.ui("failed")
        self.assertNotIsInstance(error.exception, qa.MissingHierarchy)
        self.assertEqual(1, run.call_count)
        adb.assert_not_called()
        saved = json.loads((self.out / "001-failed-dump.json").read_text())
        self.assertEqual((23, "stdout", "actual transport error"), (saved["exit_code"], saved["stdout"], saved["stderr"]))

    def test_valid_fresh_xml_only_is_read_and_parsed(self):
        commands = []
        def run(command, **kwargs):
            commands.append(command)
            return completed(stdout="UI hierarchy dumped" if "dump" in command else "")
        with patch.object(qa.subprocess, "run", side_effect=run), patch.object(qa, "adb", return_value=XML) as adb:
            snap = self.observation.ui("valid")
        remote = commands[0][-1]
        self.assertEqual(commands[1], ["adb", "shell", "test", "-s", remote])
        adb.assert_called_once_with("shell", "cat", remote)
        self.assertEqual(["Cards QA 00001, programme"], snap.labels())
        self.assertEqual(XML, (self.out / "001-valid.xml").read_text())

    def test_file_check_transport_error_is_fatal_not_an_optional_miss(self):
        with patch.object(qa.subprocess, "run", side_effect=[completed(), completed(1, stderr="device offline")]), patch.object(qa, "adb") as adb:
            with self.assertRaisesRegex(RuntimeError, "file check failed.*device offline") as error:
                self.observation.ui("offline")
        self.assertNotIsInstance(error.exception, qa.MissingHierarchy)
        adb.assert_not_called()

    def test_missing_second_dump_cannot_reuse_first_xml(self):
        with patch.object(qa.subprocess, "run", side_effect=[completed(), completed(), completed(), completed(1)]) as run, patch.object(qa, "adb", return_value=XML) as adb:
            self.observation.ui("first")
            with self.assertRaises(qa.MissingHierarchy):
                self.observation.ui("second")
        self.assertNotEqual(run.call_args_list[0].args[0][-1], run.call_args_list[2].args[0][-1])
        self.assertEqual(1, adb.call_count)
        self.assertFalse((self.out / "002-second.xml").exists())

    def test_ten_cards_poll_misses_exhaust_existing_budget_without_success(self):
        with patch.object(self.observation, "ui", side_effect=qa.MissingHierarchy("missing")) as ui, patch.object(qa.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "Exact Cards"):
                self.observation.wait_cards()
        self.assertEqual(10, ui.call_count)
        self.assertEqual([unittest.mock.call(.5)] * 9, sleep.call_args_list)

    def test_fifteen_source_poll_misses_exhaust_existing_actual_loop(self):
        # Execute the actual selected loop AST, rather than a duplicate model.
        tree = ast.parse(SOURCE.read_text())
        run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
        loop = next(n for n in ast.walk(run) if isinstance(n, ast.For) and isinstance(n.iter, ast.Call) and isinstance(n.iter.func, ast.Name) and n.iter.func.id == "range" and n.iter.args and isinstance(n.iter.args[0], ast.Constant) and n.iter.args[0].value == 15)
        ui = Mock(side_effect=qa.MissingHierarchy("missing"))
        self.observation.ui = ui
        with patch.object(qa.time, "sleep") as sleep, patch.object(qa, "adb") as adb:
            with self.assertRaisesRegex(RuntimeError, "Imported fixture inventory"):
                exec(compile(ast.Module(body=[loop], type_ignores=[]), str(SOURCE), "exec"), {"observation": self.observation, "MissingHierarchy": qa.MissingHierarchy, "time": qa.time, "adb": qa.adb})
        self.assertEqual(15, ui.call_count)
        self.assertEqual([unittest.mock.call(.5)] * 14, sleep.call_args_list)
        adb.assert_not_called()

    def test_cards_poll_miss_then_valid_state_requires_real_strict_guard(self):
        snap = qa.Snapshot(XML)
        with patch.object(self.observation, "ui", side_effect=[qa.MissingHierarchy("missing"), snap]) as ui, patch.object(self.observation, "cards_ready", return_value=True) as ready, patch.object(qa.time, "sleep"):
            self.assertIs(snap, self.observation.wait_cards())
        self.assertEqual(2, ui.call_count)
        ready.assert_called_once_with(snap)

    def test_action_path_does_not_convert_a_missing_dump_to_success(self):
        with patch.object(self.observation, "ui", side_effect=qa.MissingHierarchy("missing")), patch.object(self.observation, "press") as press:
            with self.assertRaises(qa.MissingHierarchy):
                self.observation.tap("TEST & SAVE")
        press.assert_not_called()

    def test_terminal_screenshot_is_independent_of_terminal_hierarchy(self):
        tree = ast.parse(SOURCE.read_text())
        run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
        final = next(n.finalbody for n in run.body if isinstance(n, ast.Try) and n.finalbody)
        captures = [n for n in final if isinstance(n, ast.Try) and any(isinstance(c, ast.Attribute) and c.attr in ("ui", "screenshot") for c in ast.walk(n))]
        self.assertEqual(2, len(captures))
        report = {}
        with patch.object(self.observation, "ui", side_effect=qa.MissingHierarchy("missing")), patch.object(self.observation, "screenshot") as screenshot:
            exec(compile(ast.Module(body=captures, type_ignores=[]), str(SOURCE), "exec"), {"observation": self.observation, "report": report})
        screenshot.assert_called_once_with("terminal")
        self.assertEqual(["terminal hierarchy: missing"], report["diagnostic_errors"])


if __name__ == "__main__":
    unittest.main()
