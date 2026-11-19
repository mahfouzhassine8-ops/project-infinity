# Selected capture tooling checks

Scope: local synthetic files only. Verify exact-key selection, identity alias
handling, failure fingerprint comparison, checkpoint offsets in the selected
report, and rejection of duplicate store members. Verify that private strings
from paths, route secrets, media identifiers, titles, and unrelated ZIP
members are absent. Verify that the log filter retains both trace formats and
drops arbitrary log content. No application startup, device operation, native
rebuild, APK packaging or signing is selected.

**Passed.** The reader selected the same synthetic movie from a plain JSON
file and an existing ZIP, and correctly distinguished canonical, unique alias,
and ambiguous state. A matched failure was shown only as an equality result.
Private strings and unselected data were absent. The original inputs were
unchanged, and a duplicate matching ZIP member or absent movie was rejected.
The log filter retained both trace formats with their PID and TID and rejected
other tags, malformed prefixes, URI-like add-on strings and extra fields.

The host result recorded at `301a6cd0` remains the result for the native
diagnostic overlay. It was not rerun.
