"""QA transport for the reviewed platform-root observer; no app installation."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

PACKAGE = "com.projectinfinity.kodi"
REMOTE_JAR = "/data/local/tmp/CobraImmediateHierarchy.jar"
CLASSPATH = "/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:" + REMOTE_JAR
MAX_ACTION_AGE_SECONDS = 3.5


class MissingHierarchy(RuntimeError):
    """Explicit missing/changed current root; never a successful app observation."""


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class ImmediateObserver:
    def __init__(self, jar, receipt, out):
        self.jar, self.receipt_path, self.out = Path(jar), Path(receipt), Path(out)
        self.receipt = json.loads(self.receipt_path.read_text())
        self.expected = self.receipt["QA_JAR_sha256"]
        assert sha256(self.jar) == self.expected, "Compiled QA JAR differs from its receipt"
        assert self.receipt["inspected_DEX_classes"] == [
            "Lqa/CobraImmediateHierarchy$ReadinessSignal;", "Lqa/CobraImmediateHierarchy$RootReadiness;",
            "Lqa/CobraImmediateHierarchy;"], "Only the QA main and two named readiness helpers are allowed"
        assert self.receipt["android_jar_sha256"] == "6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad"
        assert self.receipt["D8_jar_sha256"] == "305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5"
        self.out.mkdir(parents=True, exist_ok=False)
        self.prepared = False
        self.last = None
        self.notice_sequence = 0
        self.nonce = time.monotonic_ns()

    def command(self, name, arguments):
        started = time.monotonic()
        record = {"command": arguments}
        try:
            result = subprocess.run(arguments, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            decode = lambda value: value.decode(errors="replace") if isinstance(value, bytes) else value or ""
            record.update(exit_code=None, stdout=decode(error.stdout), stderr=decode(error.stderr), timed_out=True)
            raise
        else:
            record.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
            return result
        finally:
            record["host_elapsed_seconds"] = round(time.monotonic() - started, 6)
            (self.out / (name + "-command.json")).write_text(json.dumps(record, indent=2) + "\n")

    def checked(self, name, arguments):
        result = self.command(name, arguments)
        assert result.returncode == 0, "QA command failed (%d): %s" % (result.returncode, result.stderr[-1500:])
        return result.stdout

    def launch(self, arguments):
        # No BOOTCLASSPATH assignment, permission flag, legacy runner or APK.
        return ["adb", "shell", "ANDROID_DATA=/data/local/tmp", "CLASSPATH=" + CLASSPATH,
                "/system/bin/app_process", "/system/bin", "qa.CobraImmediateHierarchy", *arguments]

    def shared_metadata(self, metadata):
        assert metadata["QA_JAR_sha256"] == self.expected, "Device QA JAR differs"
        assert metadata["application_classpath"] == CLASSPATH, "Unreviewed runtime classpath"
        assert metadata["platform_surface"] == "VERIFIED_PUBLIC_REFLECTION_SURFACE_NO_ACCESS_EXEMPTIONS"
        assert len(metadata["actual_public_methods"]) == 7, "Incomplete platform reflection preflight"
        assert set(metadata["OS_JAR_sha256"]) == {"/system/framework/android.test.runner.jar", "/system/framework/uiautomator.jar"}
        assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in metadata["OS_JAR_sha256"].values())
        assert re.fullmatch(r"[0-9a-f]{64}", metadata["OS_uiautomator_script_sha256"])
        assert metadata["OS_script_classpath_line"] == "CLASSPATH=/system/framework/android.test.runner.jar:${base}/framework/uiautomator.jar"

    def prepare(self):
        assert not self.prepared, "One explicit device preflight required"
        self.checked("push", ["adb", "push", str(self.jar), REMOTE_JAR])
        observed = self.checked("device-jar-hash", ["adb", "shell", "sha256sum", REMOTE_JAR]).split()
        assert observed and observed[0] == self.expected, "Pushed JAR bytes changed"
        remote = "/data/local/tmp/CobraImmediateHierarchy-preflight.json"
        result = self.command("preflight", self.launch(["--preflight", remote, self.expected]))
        assert result.returncode == 0, "Actual platform preflight failed: " + result.stderr[-1500:]
        raw = self.checked("preflight-read", ["adb", "shell", "cat", remote])
        metadata = json.loads(raw)
        self.shared_metadata(metadata)
        assert metadata["status"] == "PREFLIGHT_PASS" and metadata["exit_code"] == 0
        (self.out / "PLATFORM-PREFLIGHT.json").write_text(raw)
        script = self.checked("OS-script-read", ["adb", "shell", "cat", "/system/bin/uiautomator"])
        assert hashlib.sha256(script.encode()).hexdigest() == metadata["OS_uiautomator_script_sha256"], "OS script changed after preflight"
        (self.out / "OS-UIAUTOMATOR.sh").write_text(script)
        self.prepared = True

    def capture(self, name, remote, *, known_notice=False):
        assert self.prepared, "Actual OS/JAR preflight must pass before observation"
        assert re.fullmatch(r"[A-Za-z0-9_-]+", name), "Unexpected observation name"
        assert re.fullmatch(r"/sdcard/cobra-cards-baseline-[0-9]+-[0-9]+\.xml", remote), "Fresh unique path required"
        metadata_path = remote[:-4] + ".json"
        started = time.monotonic()
        arguments = ["--dump", remote, metadata_path, self.expected]
        if known_notice:
            arguments.append("--known-notice-root")
        result = self.command(name + "-capture", self.launch(arguments))
        raw_metadata = self.checked(name + "-metadata-read", ["adb", "shell", "cat", metadata_path])
        (self.out / (name + "-native.json")).write_text(raw_metadata)
        metadata = json.loads(raw_metadata)
        assert result.returncode in (0, 3) and metadata.get("status") != "ERROR", "Platform observer failed: %s; native stderr=%s" % (metadata.get("error", metadata.get("status")), result.stderr[-1500:])
        self.shared_metadata(metadata)
        assert metadata["root_readiness_budget_ms"] == 2000 and metadata["root_query_ceiling"] == 16
        queries = metadata["root_queries"]
        assert 1 <= len(queries) <= 16 and [query["attempt"] for query in queries] == list(range(1, len(queries) + 1))
        assert all(query["query_started_uptime_ms"] <= query["query_finished_uptime_ms"] for query in queries)
        if result.returncode == 3 and metadata.get("status") == "ROOT_MISSING" and metadata.get("exit_code") == 3:
            assert metadata.get("reason") in {"NULL_CURRENT_ACTIVE_ROOT", "CURRENT_ACTIVE_WINDOW_CHANGED_DURING_DUMP"}
            if metadata["reason"] == "NULL_CURRENT_ACTIVE_ROOT":
                assert metadata["root_readiness_outcome"] in {"BUDGET_EXHAUSTED", "QUERY_CEILING"} and not any(query["available"] for query in queries)
            absent = self.command(name + "-missing-check", ["adb", "shell", "test", "-s", remote])
            assert absent.returncode == 1 and not absent.stdout.strip() and not absent.stderr.strip(), "Missing-root result retained XML or transport failed"
            self.last = None
            raise MissingHierarchy("%s; native stderr=%r; metadata=%s" % (metadata["reason"], result.stderr, metadata_path))
        assert result.returncode == 0 and metadata.get("status") == "ROOT_CAPTURED" and metadata.get("exit_code") == 0, "Platform observer failed: " + result.stderr[-1500:]
        assert metadata["active_window_revalidated"] is True
        assert metadata["root_readiness_outcome"] == "CURRENT_ROOT_AVAILABLE" and metadata["root_readiness_elapsed_ms"] < 2000
        assert metadata["root_package"] in ({PACKAGE, "android"} if known_notice else {PACKAGE}), "Unexpected active package"
        assert type(metadata["window_id"]) is int and metadata["window_id"] >= 0
        box = metadata["root_bounds"]; display = metadata["display_size"]
        assert len(box) == 4 and all(type(value) is int for value in box) and box[2] > box[0] and box[3] > box[1]
        assert len(display) == 2 and all(type(value) is int and value > 0 for value in display)
        assert box[0] < display[0] and box[1] < display[1] and box[2] > 0 and box[3] > 0
        assert metadata["known_notice_root_allowed"] is known_notice
        stamp = [metadata[key] for key in ("started_uptime_ms", "root_acquire_started_uptime_ms", "root_acquired_uptime_ms", "dump_completed_uptime_ms", "finished_uptime_ms")]
        assert all(type(value) is int and value >= 0 for value in stamp) and stamp == sorted(stamp), "Invalid native chronology"
        present = self.command(name + "-nonempty-check", ["adb", "shell", "test", "-s", remote])
        assert present.returncode == 0, "Fresh nonempty XML required"
        raw = self.checked(name + "-XML-read", ["adb", "shell", "cat", remote])
        assert hashlib.sha256(raw.encode()).hexdigest() == metadata["XML_sha256"] and len(raw.encode()) == metadata["XML_bytes"], "Native XML bytes changed"
        tree = ET.fromstring(raw); root = tree.find("node")
        assert tree.tag == "hierarchy" and root is not None and root.get("package") == metadata["root_package"]
        assert int(tree.get("rotation")) == metadata["rotation"]
        self.last = {"started": started, "metadata": metadata, "XML": raw}
        return raw, metadata, started

    def guard_age(self, started):
        assert 0 <= time.monotonic() - started < MAX_ACTION_AGE_SECONDS, "Current observation exceeded unchanged3.5second action-age guard"

    def notice_capture(self, name):
        self.notice_sequence += 1
        remote = "/sdcard/cobra-cards-baseline-%d-%03d.xml" % (self.nonce, self.notice_sequence)
        raw, metadata, started = self.capture("notice-%03d-%s" % (self.notice_sequence, name), remote, known_notice=True)
        return raw

    def guard_notice_press(self, notice):
        assert self.last is not None
        self.guard_age(self.last["started"])
        left, top, right, bottom = self.last["metadata"]["root_bounds"]
        width, height = self.last["metadata"]["display_size"]
        x, y = notice["coordinate"]
        assert max(0, left) <= x < min(width, right) and max(0, top) <= y < min(height, bottom), "Notice target lies outside current active root/display"
