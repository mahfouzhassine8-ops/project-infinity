"""Print only the fixed decision fields from a private Kodi/logcat stream."""
import json
import re
import sys

prefix = 'INFINITY_SAVED_NAVIGATION '
code = re.compile(r'[a-z][a-z0-9_]{0,63}')
for line in sys.stdin:
    _, matched, raw = line.partition(prefix)
    if not matched or len(raw) > 1024:
        continue
    try:
        row = json.loads(raw)
    except ValueError:
        continue
    if not isinstance(row, dict) or set(row) != {
            'schema', 'stage', 'epoch_ms', 'monotonic_ms', 'boundary', 'outcome'
    } or row['schema'] != 1 or row['stage'] != 'continue_navigation':
        continue
    if (type(row['epoch_ms']) is not int or type(row['monotonic_ms']) not in (int, float) or
            not all(isinstance(row[key], str) and code.fullmatch(row[key]) for key in ('boundary', 'outcome'))):
        continue
    print(json.dumps(row, sort_keys=True), flush=True)
