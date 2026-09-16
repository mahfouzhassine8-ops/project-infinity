"""Optional local Android crash-buffer snapshot, restricted to the app's UID.

No root, adb, new permissions, network, or global log fallback. Android may return
no usable records. This is not a replacement for a native tombstone.
"""
import os
from pathlib import Path
import subprocess
import tempfile

MAX_LOGCAT_BYTES = 256 * 1024


def collect(root, *, executable='/system/bin/logcat', runner=subprocess.run):
    root = Path(root)
    result = {'attempted': False, 'status': 'android_logcat_unavailable',
              'same_uid_only': True, 'usable_trace_confirmed': False}
    if not Path(executable).is_file() or not hasattr(os, 'getuid'):
        return result
    root.mkdir(parents=True, exist_ok=True)
    result['attempted'] = True
    # -t limits the requested line count and implies dump-and-exit. No clearing,
    # no continuous logging, no shell interpolation, no privileged commands.
    command = [executable, '--uid=' + str(os.getuid()), '-b', 'crash', '-d',
               '-t', '200', '-v', 'threadtime']
    try:
        with tempfile.TemporaryFile(dir=str(root)) as output, tempfile.TemporaryFile(dir=str(root)) as errors:
            completed = runner(command, stdout=output, stderr=errors, timeout=5, check=False)
            output.seek(0)
            data = output.read(MAX_LOGCAT_BYTES + 1)
            result['exit_code'] = completed.returncode
            result['truncated'] = len(data) > MAX_LOGCAT_BYTES
            if completed.returncode != 0:
                result['status'] = 'permission_or_command_unavailable'
            elif data.strip():
                path = root / 'same-uid-crash-logcat.txt'
                path.write_bytes(data[:MAX_LOGCAT_BYTES])
                result.update(status='snapshot_collected_not_diagnosed', bytes=path.stat().st_size)
            else:
                result['status'] = 'no_visible_crash_records'
    except subprocess.TimeoutExpired:
        result['status'] = 'timed_out'
    except (OSError, ValueError, RuntimeError) as error:
        result.update(status='collection_error', error_type=type(error).__name__)
    return result
