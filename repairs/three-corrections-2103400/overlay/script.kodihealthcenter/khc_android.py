"""Best-effort same-UID Android evidence. No root, adb or global log fallback."""
import os
from pathlib import Path
import re
import tempfile

from khc_diagnostics import atomic_json, redact, utc

MAX_OUTPUT = 256 * 1024


def collect_logcat(folder, executable='/system/bin/logcat', runner=None):
    folder = Path(folder)
    result = {'attempted': False, 'status': 'android_logcat_unavailable', 'captured_utc': utc(),
              'same_uid_only': True, 'fatal_stack_confirmed': False,
              'note': 'A buffer may be empty, restricted or contain unrelated earlier records.'}
    if not Path(executable).is_file() or not hasattr(os, 'getuid'):
        return result
    try:
        import subprocess
    except (ImportError, OSError, RuntimeError):
        result['status'] = 'subprocess_unsupported'
        return result
    folder.mkdir(parents=True, exist_ok=True)
    result['attempted'] = True
    command = [executable, '--uid=' + str(os.getuid()), '-b', 'crash', '-d', '-t', '200', '-v', 'threadtime']
    try:
        # Android emulated storage rejects O_TMPFILE with EACCES. TemporaryFile
        # deliberately retries that probe, but the persistence observer must
        # retain every failed write. Allocate real exclusive named files instead;
        # the same observer sees their writes, closes and automatic unlink.
        with tempfile.NamedTemporaryFile(prefix='.khc-logcat-', dir=str(folder)) as output, tempfile.NamedTemporaryFile(prefix='.khc-logcat-', dir=str(folder)) as errors:
            completed = (runner or subprocess.run)(command, stdout=output, stderr=errors, timeout=5, check=False)
            output.seek(0)
            data = output.read(MAX_OUTPUT + 1)
            result['exit_code'] = completed.returncode
            result['truncated'] = len(data) > MAX_OUTPUT
            if completed.returncode:
                result['status'] = 'permission_or_command_unavailable'
            else:
                text = data[:MAX_OUTPUT].decode('utf-8', 'replace')
                actual = [line for line in text.splitlines() if line.strip() and not line.startswith('---------')]
                if actual:
                    clean = redact(text).encode('utf-8')[:MAX_OUTPUT]
                    (folder / 'same-uid-crash-logcat.txt').write_bytes(clean)
                    result.update(status='snapshot_collected_not_diagnosed', bytes=len(clean))
                else:
                    result['status'] = 'no_visible_crash_records'
    except subprocess.TimeoutExpired:
        result['status'] = 'timed_out'
    except (OSError, ValueError, RuntimeError, NotImplementedError) as error:
        result.update(status='collection_unavailable', error_type=type(error).__name__)
    return result
