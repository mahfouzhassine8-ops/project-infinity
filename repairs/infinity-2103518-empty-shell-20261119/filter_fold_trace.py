"""Retain only the signed diagnostic events from root-free ADB threadtime logs."""
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "infinity-2103514-targeted-20261118"))
from filter_continue_trace import decision

LINE = re.compile(r"(\d\d-\d\d \d\d:\d\d:\d\d\.\d{3,6})\s+(\d+)\s+(\d+)\s+[A-Z]\s+"
                  r"(Kodi|InfinityPersistenceMutex)\s*:\s?(.*)")
STARTUP = re.compile(
    r"InfinityStartupTrace stage=(?:gil\.(?:wait|acquired)|"
    r"interpreter\.(?:create|returned|created|failed|main_state_missing|thread_state_failed)|"
    r"bytecode\.(?:enter|returned|exception|cancelled_before_entry)|"
    r"execution\.finished|gate\.checkpoint_closed|trace\.overflow)"
    r" request=\d+ invoker=-?\d+ tid=\d+ us=\d+ value=-?\d+ flags=\d+ tracked=\d+"
    r"(?: addon=(?:[A-Za-z0-9._-]{1,127}))?")
MUTEX = re.compile(r"phase=(?:observer_(?:start|end)|observer_start_failed result=\d+|"
                   r"waiting ticket=\d+ tid=\d+ site=[123] line=\d+ started_us=\d+ observed_us=\d+"
                   r" wait_us=\d+ owner_ticket=\d+ owner_tid=\d+ owner_site=[0-3] owner_line=\d+ acquired_us=\d+|"
                   r"completed ticket=\d+ tid=\d+ site=[123] line=\d+ started_us=\d+ acquired_us=\d+"
                   r" released_us=\d+ wait_us=\d+|"
                   r"loss wait_slots=\d+ completion_slots=\d+ sample_limit=\d+ log_writes=\d+)")


def filtered_lines(lines):
    for line in lines:
        match = LINE.fullmatch(line.rstrip("\r\n"))
        if not match:
            continue
        stamp, pid, tid, tag, body = match.groups()
        if tag == "Kodi":
            row = decision(body)
            if row is not None:
                yield json.dumps(dict(android_time=stamp, android_pid=int(pid), **row), sort_keys=True)
                continue
            # Kodi can prepend the C++ log context before the trace marker.
            _, found, event = body.partition("InfinityStartupTrace ")
            if not found:
                continue
            body = found + event
            if not STARTUP.fullmatch(body):
                continue
        elif not MUTEX.fullmatch(body):
            continue
        yield " ".join((stamp, pid, tid, tag, body))


def main():
    for line in filtered_lines(sys.stdin):
        print(line, flush=True)


if __name__ == "__main__":
    main()
